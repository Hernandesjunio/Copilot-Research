# C — Interfaces e contratos

`Protocol`s Python propostos para destravar a evolução desacoplada descrita em [`analise-arquitetural.md`](analise-arquitetural.md) §5–§6 e [`A-design-alvo.md`](A-design-alvo.md). Apresentam-se **apenas os contratos**, não as implementações (estas entram nos PRs concretos de cada refatoração em [`B-refatoracoes.md`](B-refatoracoes.md)).

Preferiu-se `typing.Protocol` (duck typing estrutural) em vez de ABCs concretas para:

1. **Testabilidade** — qualquer dupla passa como implementação se expuser os métodos certos.
2. **Baixa fricção de migração** — o código atual pode ser adaptado para satisfazer o `Protocol` sem herança.
3. **Sem dependências** — `typing.Protocol` é stdlib desde Python 3.8.

Todas as interfaces propostas devem viver em um novo módulo `corporate_instructions_mcp/ranking.py`, importável sem side-effects.

---

## 1. Tipos de apoio

```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ExpansionTerm:
    """Um termo da query já expandido, com peso e proveniência."""
    term: str           # termo normalizado (NFKD + lowercase)
    weight: float       # peso relativo; 1.0 = direto, <1.0 = relacionado
    source: str         # "query" | "alias:<doc_id>" | "domain:<name>" | "global"
    canonical: str | None = None  # grupo canônico no vocabulário, se aplicável


@dataclass(frozen=True)
class ExpansionResult:
    """Resultado completo de uma expansão; preserva provenance para explicabilidade."""
    terms: dict[str, ExpansionTerm]             # chave = termo já normalizado
    truncated: tuple[str, ...] = ()             # termos descartados pelo limite
    activated_domains: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SearchContext:
    """Contexto de uma chamada de busca."""
    raw_query: str
    tokens: tuple[str, ...]
    tag_filter: frozenset[str] | None
    domains_hint: frozenset[str] = frozenset()   # opcional, vindo do consumidor
    debug: bool = False


@dataclass(frozen=True)
class VocabularyGroup:
    """Um grupo de sinónimos: um canônico + aliases."""
    canonical: str
    aliases: tuple[str, ...]
    domain: str | None = None
    scope: str | None = None            # restringe em que docs o grupo se aplica


@dataclass(frozen=True)
class VocabularyBundle:
    """Coleção de vocabulários disponíveis após carregamento."""
    global_groups: tuple[VocabularyGroup, ...]
    domain_groups: Mapping[str, tuple[VocabularyGroup, ...]]  # domain -> groups
    # Meta para observabilidade / explain
    sources: Mapping[str, str]    # domain_or_"global" -> filesystem path


@dataclass
class ScoreTrace:
    """Decomposição do score, preenchida quando ctx.debug é True."""
    lexical: float = 0.0
    metadata: float = 0.0
    semantic: float | None = None
    per_term: dict[str, float] = field(default_factory=dict)   # term -> contrib
    per_field: dict[str, float] = field(default_factory=dict)  # title/tags/body
    provenance: dict[str, str] = field(default_factory=dict)   # term -> source
```

**Notas de desenho:**

- `ExpansionResult.terms` é `dict[str, ExpansionTerm]`, não `dict[str, float]`, para preservar proveniência no modo `explain` sem duplicar estruturas.
- `SearchContext` é imutável (dataclass frozen) — tornou-se explícito e pesquisável nos logs.
- `VocabularyGroup.scope` prepara para aliases per-documento sem inflar outro tipo.
- `ScoreTrace` não é parte obrigatória do score: a `Protocol` devolve `float` e, opcionalmente, o ranker implementa `score_with_trace` para `debug=True`. Isto evita penalizar o caminho quente com custo de tracing.

---

## 2. `VocabularyProvider`

Fornece o vocabulário à aplicação. Invocado uma vez por `build_index` (ou sempre que o provider for recarregado).

```python
@runtime_checkable
class VocabularyProvider(Protocol):
    """Carrega vocabulário para expansão de query.

    Implementações previstas:
      - YamlVocabularyProvider: lê INSTRUCTIONS_ROOT/_vocabulary/*.yaml
      - StaticVocabularyProvider: fallback para o dicionário hard-coded atual
      - CompositeVocabularyProvider: combina múltiplos providers com precedência
    """

    def load(self) -> VocabularyBundle: ...

    def version(self) -> str:
        """Identificador estável usado para invalidação de caches.

        Para YAML, pode ser o hash dos ficheiros.
        Para static, uma constante.
        """
        ...
```

**Contratos adicionais (não expressos no tipo, documentar):**

- `load()` **não** deve levantar em caso de vocabulário vazio (apenas se YAML for inválido e nenhum fallback existir).
- `load()` deve aplicar os limites defensivos (200 grupos × 30 aliases × 256 KiB por ficheiro).
- Chamadas repetidas a `load()` devolvem **a mesma** bundle (imutabilidade após carga).

---

## 3. `QueryExpansionProvider`

Recebe tokens normalizados da query e devolve o `ExpansionResult` com proveniência.

```python
@runtime_checkable
class QueryExpansionProvider(Protocol):
    """Expande tokens da query em termos relacionados."""

    def expand(
        self,
        ctx: SearchContext,
        vocabulary: VocabularyBundle,
        *,
        max_related_per_token: int = 8,
    ) -> ExpansionResult: ...
```

**Contratos adicionais:**

- `expand` **deve** preservar os tokens originais em `result.terms` com `weight=1.0` e `source="query"`.
- Sinónimos de aliases locais de documento **não** entram aqui (são tratados no ranker, porque dependem do documento atual). `QueryExpansionProvider` só lida com vocabulário global + de domínio.
- `ExpansionResult.activated_domains` deve refletir os domínios cujas groups foram usados.
- Truncamento **deve** popular `ExpansionResult.truncated` (nunca silencioso).

**Implementações previstas:**

- `DictQueryExpansionProvider` (Fase 1): port direto do comportamento atual.
- `DomainAwareExpansionProvider` (Fase 2): aplica regra de ativação por domínio (§5 da análise principal).

---

## 4. `LexicalRanker`

Calcula o score lexical de um documento dada uma expansão.

```python
@runtime_checkable
class LexicalRanker(Protocol):
    """Pontua um documento contra uma expansão de query."""

    name: str   # identificador estável, aparece em explain e logs

    def score(
        self,
        rec: "InstructionRecord",
        expansion: ExpansionResult,
        ctx: SearchContext,
    ) -> float: ...

    def score_with_trace(
        self,
        rec: "InstructionRecord",
        expansion: ExpansionResult,
        ctx: SearchContext,
    ) -> tuple[float, ScoreTrace]:
        """Default pode ser implementado via score(), mas subclasses podem otimizar."""
        ...
```

**Contratos adicionais:**

- Score `0.0` ⇒ documento **não** entra no resultado (convenção preservada do `score_record` atual em [`indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) linha 205–206 e consumidor em [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py) linha 202).
- `LexicalRanker` recebe **o registro completo** incluindo `aliases` (campo novo em `InstructionRecord` via **R-8**). O ranker decide como ponderar match em alias local.
- Scores **não** são normalizados entre rankers (i.e., scores `WordBoundaryCountRanker` e `BM25FieldedRanker` não são diretamente comparáveis). O campo `relevance` no JSON de saída deve continuar a normalizar para `[0,1]` via `round(min(1.0, score / divisor), 4)` com `divisor` dependente do ranker.

**Implementações previstas:**

- `WordBoundaryCountRanker` (Fase 1): versão corrigida do atual `score_record`, com `\b` e normalização simétrica. `name = "word-boundary-v1"`.
- `BM25FieldedRanker` (Fase 2): `name = "bm25f-v1"`, parâmetros `k1`, `b`, `field_weights` configuráveis.

---

## 5. `MetadataBooster`

Encapsula boosts que não dependem do texto (prioridade, kind, scope).

```python
@runtime_checkable
class MetadataBooster(Protocol):
    """Pontuação adicional a partir de metadados estruturados do registro."""

    def boost(
        self,
        rec: "InstructionRecord",
        ctx: SearchContext,
    ) -> float: ...

    def boost_with_trace(
        self,
        rec: "InstructionRecord",
        ctx: SearchContext,
    ) -> tuple[float, dict[str, float]]:
        """Devolve (total, {component -> value}) para explain."""
        ...
```

**Implementação padrão (Fase 1):**

- `PriorityMetadataBooster`: replica exatamente `0.5 * PRIORITY_RANK.get(rec.priority, 0)` da linha 219 de `indexing.py`.
- Evolui em Fase 2 para incorporar `scope`/`kind` quando houver casos de uso concretos.

---

## 6. `SearchIndex` — envelope operacional

Agrupa os componentes num único objeto com o qual `server.py` interage.

```python
@dataclass(frozen=True)
class SearchIndex:
    records: Mapping[str, "InstructionRecord"]
    vocabulary: VocabularyBundle
    expansion: QueryExpansionProvider
    lexical: LexicalRanker
    metadata_booster: MetadataBooster
    # Fase 2:
    # inverted: Mapping[str, tuple[Posting, ...]] | None = None
    # stats: CorpusStats | None = None

    def search(
        self,
        query: str,
        tag_filter: frozenset[str] | None,
        max_results: int,
        debug: bool = False,
    ) -> "SearchResponse": ...
```

`SearchResponse` substitui o dicionário JSON atual por um tipo tipado; a tool continua a serializar para JSON na saída. A definição completa fica a cargo do PR que implementa a Fase 2; em Fase 1 o `server.py` pode continuar a montar JSON diretamente consumindo os componentes individuais.

---

## 7. `SemanticReranker` — Fase 3, opcional

Nunca é obrigatório. A presença de uma interface permite integração limpa se e quando a métrica justificar.

```python
@runtime_checkable
class SemanticReranker(Protocol):
    """Reordena top-N resultados lexicais por similaridade semântica."""

    enabled: bool
    name: str

    def rerank(
        self,
        candidates: Sequence[tuple[float, "InstructionRecord"]],
        ctx: SearchContext,
    ) -> Sequence[tuple[float, "InstructionRecord"]]:
        """Retorna a MESMA sequência de records, possivelmente com scores ajustados.

        INVARIANTE: len(output) <= len(candidates) e output ⊂ candidates (por id).
        Não pode introduzir documentos que não estavam no top-N lexical.
        """
        ...
```

A invariante "não pode introduzir documentos" é crucial: embeddings como **recall** tornam a busca não-auditável e cara; como **re-ranker** do top-N (N=30) preservam recall lexical e apenas refinam ordem.

---

## 8. Integração em `build_index` e `server.py`

Assinatura recomendada (Fase 1):

```python
# corporate_instructions_mcp/indexing.py

def build_index(
    root: Path,
    *,
    vocabulary_provider: VocabularyProvider | None = None,
    expansion_provider: QueryExpansionProvider | None = None,
    lexical_ranker: LexicalRanker | None = None,
    metadata_booster: MetadataBooster | None = None,
) -> SearchIndex:
    """Backwards-compatible: sem kwargs, usa defaults que reproduzem o comportamento atual."""
    ...
```

`server.py` deixa de importar `score_record`, `tokenize_query`, etc. diretamente — passa a fazer `index.search(query, ...)`. A retrocompatibilidade é mantida durante a transição mantendo as funções livres como wrappers finos sobre `DictQueryExpansionProvider` e `WordBoundaryCountRanker`.

---

## 9. Testes de conformidade das interfaces

Recomendação mínima para cada PR que adicione uma implementação:

```python
# tests/test_protocols.py (ilustrativo)

def test_word_boundary_ranker_satisfies_lexical_protocol():
    ranker = WordBoundaryCountRanker()
    assert isinstance(ranker, LexicalRanker)   # via runtime_checkable
    # plus: chamada funcional mínima contra um InstructionRecord sintético

def test_yaml_vocabulary_satisfies_vocabulary_protocol(tmp_path):
    (tmp_path / "global.yaml").write_text("version: 1\ngroups: []\n")
    provider = YamlVocabularyProvider(tmp_path)
    assert isinstance(provider, VocabularyProvider)
    bundle = provider.load()
    assert bundle.global_groups == ()
```

---

## 10. O que **não** entra nestas interfaces

- **Cache de queries**: é decisão de `server.py`, não do ranker. Manter fora.
- **Persistência do índice**: fora de escopo (índice em memória).
- **I/O de HTTP**: fora de escopo desta análise (ver [`docs/ROADMAP-TRANSPORT-HTTP.md`](../../../../mcp-instructions-server/docs/ROADMAP-TRANSPORT-HTTP.md)).
- **Autenticação/autorização**: fora de escopo.
- **LLM-driven query rewriting**: explicitamente rejeitado em §8.7 da análise principal.
