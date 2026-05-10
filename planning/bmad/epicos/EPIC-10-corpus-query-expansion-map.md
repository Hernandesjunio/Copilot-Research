# EPIC-10 — Corpus Query Expansion Map (implementação da ADR-002)

## Objetivo

Implementar o **Corpus Query Expansion Map** conforme especificado na ADR-002: substituir o
mecanismo de expansão de queries atual (dicionário plano, bidirecional e com fallback silencioso)
por uma camada modular, tipada, unidirecional e observável, integrada ao mecanismo de busca
existente sem alterá-lo.

**Resultado esperado**:
- Suíte de 24 casos mantém ou melhora o baseline pós-EPIC-09 (≥ 8/24).
- Critérios de validação da ADR-002 (seção 5) todos atendidos.
- `pytest -q` permanece verde com zero regressões ao longo de todas as fases.

---

## Contexto consolidado

Estado confirmado antes deste epic:

- **Mecanismo atual**: `DEFAULT_SYNONYMS` hardcoded em `indexing.py` (fallback silencioso
  invisível ao operador) + `synonyms.yaml` bundled junto ao pacote (flat list, carregado
  na inicialização como módulo-level global).
- **Lookup**: `_build_expansion_lookup()` constrói lookup **bidirecional** — `mensageria →
  rabbitmq` gera automaticamente `rabbitmq → mensageria`, criando expansão cruzada indevida
  entre domínios.
- **Pesos**: todos os termos expandidos recebem `weight=0.5`, sem distinção entre alias
  (quase equivalente) e termo fraco (sinal baixo).
- **Rastreabilidade**: nenhuma; não é possível saber qual expansão foi aplicada e por quê.
- **Fallback**: se `synonyms.yaml` ausente ou com erro de parse, `DEFAULT_SYNONYMS` é usado
  silenciosamente — comportamento invisível ao operador.
- **Corpus signature**: `pytest -q` no estado pré-epic: todos os testes existentes verdes.

Problemas documentados na ADR-002 (seção 1) que este epic resolve:

| Problema | Causa | Solução |
|---|---|---|
| Expansão cruzada indevida | Lookup bidirecional | Lookup unidirecional (canônico → expandidos) |
| Sem distinção de intensidade | Peso único 0.5 | Pesos por tipo: alias 0.9, strong 0.7, weak 0.3 |
| Ambiguidade de termos | Sem contexto de path | Campo `contexts` no schema (V2) |
| Fallback silencioso | DEFAULT_SYNONYMS como backup | Desabilitar expansão se mapa ausente |
| Sem rastreabilidade | Nenhum diagnóstico | `ExpansionDiagnostic` com source + tipo |

---

## Princípio de implementação

> **TDD estrito: RED → implementação mínima → GREEN, sub-issue por sub-issue.**
> Uma variável por vez. Zero regressões permitidas.

Guardrails invioláveis:

- Não alterar assinaturas públicas das tools (`search_instructions`, `resolve_instruction_context`,
  `get_instructions_batch`, `get_context_triggers`, `validate_applicability`).
- Não alterar o algoritmo de scoring em `score_record_breakdown`.
- Não introduzir BM25 ou busca vetorial.
- Não alterar o protocolo stdio.
- Não alterar corpus/frontmatter das fixtures (`fixtures/instructions/*.md`).
- Não alterar critérios da suíte de 24 casos.
- Não introduzir expansão transitiva (multi-hop).
- Não implementar merge global/local de mapas.
- Campo `contexts` do schema: parseado e armazenado no tipo Python, mas **não aplicado em
  scoring nesta versão** (reservado para V2). Incluir apenas para garantir compatibilidade
  futura do schema.

---

## Escopo

### Em escopo

- Novo módulo `mcp-instructions-server/corporate_instructions_mcp/expansion.py` com:
  - Tipos: `ContextRule`, `ExpansionEntry`, `ExpansionDomain`, `ExpansionMap`, `ExpansionDiagnostic`.
  - Funções: `parse_domain_file()`, `load_corpus_expansion_map()`,
    `build_unidirectional_lookup()`, `expand_query_weighted()`.
  - Constantes: `ALIAS_WEIGHT`, `STRONG_WEIGHT`, `WEAK_WEIGHT`.
- Modificações em `indexing.py`:
  - Remover `DEFAULT_SYNONYMS`, `_load_expansion_map_from_file()`, `_build_expansion_lookup()`,
    módulo-level `QUERY_EXPANSION_MAP` e `_EXPANSION_LOOKUP`.
  - Adicionar parâmetro opcional `expansion_map` em `expand_query_with_metadata()`.
  - Quando `expansion_map is None`, expansão é desabilitada (apenas tokens do usuário com
    peso 1.0).
- Criação dos arquivos YAML por domínio em
  `fixtures/instructions/metadata/corpus-query-expansion-map/`.
- Remoção do arquivo `synonyms.yaml` bundled junto ao pacote
  (`corporate_instructions_mcp/synonyms.yaml`).
- Arquivo de testes: `mcp-instructions-server/tests/test_epic10_corpus_query_expansion_map.py`.

### Fora de escopo

- Reescrever algoritmo de scoring.
- BM25 / busca vetorial.
- Expansão transitiva (multi-hop).
- Merge global/local de mapas.
- Context-based scoring por path de documento (V2).
- Atualização do corpus real de produção (`INSTRUCTIONS_ROOT` em produção).

---

## Artefatos principais

### Novos

- `mcp-instructions-server/corporate_instructions_mcp/expansion.py`
- `mcp-instructions-server/tests/test_epic10_corpus_query_expansion_map.py`
- `fixtures/instructions/metadata/corpus-query-expansion-map/messaging.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/observability.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/architecture.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/persistence.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/resilience.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/api.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/security.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/caching.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/validation.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/configuration.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/dns.yaml`
- `fixtures/instructions/metadata/corpus-query-expansion-map/integration.yaml`

### Modificados

- `mcp-instructions-server/corporate_instructions_mcp/indexing.py`

### Removidos

- `mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`

### Não alterados

- `context_resolver.py`, `server.py`, `paths.py`, `config.py`, `telemetry.py`,
  `applicability.py`, `search_contract.py`
- Todos os `fixtures/instructions/*.md`

---

## Fases de execução sequencial

```
Fase 0  → Congelar baseline (pytest verde confirmado)
Fase 1  → S-01: tipos e schema (RED → implementar → GREEN)
Fase 2  → S-02: loader corpus-aware (RED → implementar → GREEN)
Fase 3  → S-03: lookup unidirecional ponderado (RED → implementar → GREEN)
Fase 4  → S-04: integração expand_query_with_metadata (RED → implementar → GREEN)
Fase 5  → S-05: domain YAML files para fixture corpus (RED → criar arquivos → GREEN)
Fase 6  → S-06: remover DEFAULT_SYNONYMS e synonyms.yaml bundled (RED → remover → GREEN)
Fase 7  → S-07: validação de regressão e critérios ADR-002
```

---

## Fase 0 — Congelar baseline

Antes de qualquer edição:

- [ ] Executar `pytest -q` e confirmar zero falhas.
- [ ] Registrar o número exato de testes passando.
- [ ] Confirmar que `indexing.py` contém: `DEFAULT_SYNONYMS`, `_load_expansion_map_from_file`,
      `_build_expansion_lookup`, `QUERY_EXPANSION_MAP`, `_EXPANSION_LOOKUP`.
- [ ] Confirmar que `synonyms.yaml` existe em `corporate_instructions_mcp/synonyms.yaml`.

---

## S-01 — Schema, tipos e parser de arquivo de domínio

### Background

Definir os tipos Python que representam o schema YAML por domínio e a função que faz o parse
de um dict (resultado de `yaml.safe_load`) para esses tipos. O schema YAML esperado por domínio:

```yaml
# Exemplo: fixtures/instructions/metadata/corpus-query-expansion-map/messaging.yaml
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases:
      - messaging
    strong_terms:
      - rabbitmq
      - publish
      - consume
    weak_terms:
      - outbox
    contexts: []        # reservado para V2 — parseado mas não usado em scoring
```

Tipos a definir em `expansion.py`:

```python
@dataclass(frozen=True)
class ContextRule:
    path_pattern: str       # glob pattern (e.g. "**/dns*.md") — V2, não usado em scoring
    extra_terms: list[str]  # termos adicionais quando path_pattern corresponder

@dataclass(frozen=True)
class ExpansionEntry:
    canonical: str              # termo canônico (chave unidirecional)
    aliases: list[str]          # peso ALIAS_WEIGHT (0.9)
    strong_terms: list[str]     # peso STRONG_WEIGHT (0.7)
    weak_terms: list[str]       # peso WEAK_WEIGHT (0.3)
    contexts: list[ContextRule] # V2, não usado em scoring neste epic

@dataclass(frozen=True)
class ExpansionDomain:
    domain: str
    version: str
    source_file: str
    entries: list[ExpansionEntry]
```

Constantes de peso:

```python
ALIAS_WEIGHT: float = 0.9
STRONG_WEIGHT: float = 0.7
WEAK_WEIGHT: float = 0.3
```

Função pública:

```python
def parse_domain_file(raw: dict, source: str) -> ExpansionDomain | None:
    """Faz parse de um dict (output de yaml.safe_load) para ExpansionDomain.

    Retorna None (com log de warning) se:
      - `raw` não é dict
      - campo 'domain' ausente ou vazio
      - campo 'entries' ausente ou não é lista

    Comportamento tolerante:
      - Campos desconhecidos no nível superior ou na entrada são ignorados.
      - Entradas sem 'canonical' são ignoradas (com log de warning por entrada).
      - Campos 'aliases', 'strong_terms', 'weak_terms', 'contexts' ausentes → lista vazia.
      - Todos os tokens (canonical + listas) são normalizados com _normalize_token().
      - version ausente → "1" como default.
    """
```

### Testes RED — S-01

**Estado RED**: todos os testes abaixo falham com `ModuleNotFoundError: No module named
'corporate_instructions_mcp.expansion'` porque o módulo ainda não existe.

```python
# === ARQUIVO: mcp-instructions-server/tests/test_epic10_corpus_query_expansion_map.py ===
# Seção: S-01 — Schema e tipos

def test_FAIL_S01_module_expansion_importable() -> None:
    """Módulo expansion.py deve existir e ser importável.

    Input:  import do módulo corporate_instructions_mcp.expansion
    Output: nenhuma exceção levantada
    RED:    falha com ModuleNotFoundError
    GREEN:  importa sem erro
    """
    from corporate_instructions_mcp import expansion  # noqa: F401


def test_FAIL_S01_weight_constants_values() -> None:
    """Constantes de peso devem ter os valores exatos definidos na ADR-002.

    Input:
      import de ALIAS_WEIGHT, STRONG_WEIGHT, WEAK_WEIGHT de expansion

    Output (esperado após GREEN):
      ALIAS_WEIGHT  == 0.9   (alias: quase equivalente ao canonical)
      STRONG_WEIGHT == 0.7   (strong_terms: forte sinal semântico)
      WEAK_WEIGHT   == 0.3   (weak_terms: sinal fraco, contexto-dependente)

    RED:  ModuleNotFoundError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import ALIAS_WEIGHT, STRONG_WEIGHT, WEAK_WEIGHT
    assert ALIAS_WEIGHT == 0.9, f"ALIAS_WEIGHT esperado 0.9, obtido {ALIAS_WEIGHT}"
    assert STRONG_WEIGHT == 0.7, f"STRONG_WEIGHT esperado 0.7, obtido {STRONG_WEIGHT}"
    assert WEAK_WEIGHT == 0.3, f"WEAK_WEIGHT esperado 0.3, obtido {WEAK_WEIGHT}"


def test_FAIL_S01_parse_domain_file_valid_full_entry() -> None:
    """parse_domain_file aceita YAML válido com todos os campos preenchidos.

    Input:
      raw = {
          "domain":   "messaging",
          "version":  "1",
          "entries":  [
              {
                  "canonical":    "mensageria",
                  "aliases":      ["messaging"],
                  "strong_terms": ["rabbitmq", "publish", "consume"],
                  "weak_terms":   ["outbox"],
                  "contexts":     []
              }
          ]
      }
      source = "messaging.yaml"

    Output esperado:
      result                           is not None
      result.domain                    == "messaging"
      result.version                   == "1"
      result.source_file               == "messaging.yaml"
      len(result.entries)              == 1
      result.entries[0].canonical      == "mensageria"
      result.entries[0].aliases        == ["messaging"]
      result.entries[0].strong_terms   == ["rabbitmq", "publish", "consume"]
      result.entries[0].weak_terms     == ["outbox"]
      result.entries[0].contexts       == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "aliases": ["messaging"],
                "strong_terms": ["rabbitmq", "publish", "consume"],
                "weak_terms": ["outbox"],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    assert result.domain == "messaging"
    assert result.version == "1"
    assert result.source_file == "messaging.yaml"
    assert len(result.entries) == 1

    entry = result.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["messaging"]
    assert entry.strong_terms == ["rabbitmq", "publish", "consume"]
    assert entry.weak_terms == ["outbox"]
    assert entry.contexts == []


def test_FAIL_S01_parse_domain_file_normalizes_tokens() -> None:
    """parse_domain_file normaliza todos os tokens: lowercase, sem acento, underscore→hífen.

    Input:
      canonical com maiúscula e acento: "Mensageria"
      alias com maiúscula:             "RabbitMQ"
      strong_term com underscore:      "publish_subscribe"
      weak_term com acento:            "publicação"

    Output esperado:
      entry.canonical     == "mensageria"          (lowercase + sem acento)
      entry.aliases       == ["rabbitmq"]           (lowercase)
      entry.strong_terms  == ["publish-subscribe"]  (underscore → hífen via _normalize_token)
      entry.weak_terms    == ["publicacao"]          (sem acento)

    Nota: _normalize_token() de indexing.py realiza NFKD + remoção de combining chars +
          lowercase + strip. O underscore é convertido em hífen por esse normalizador.

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "messaging",
        "version": "1",
        "entries": [
            {
                "canonical": "Mensageria",
                "aliases": ["RabbitMQ"],
                "strong_terms": ["publish_subscribe"],
                "weak_terms": ["publicação"],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="messaging.yaml")

    assert result is not None
    entry = result.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["rabbitmq"]
    assert entry.strong_terms == ["publish-subscribe"]
    assert entry.weak_terms == ["publicacao"]


def test_FAIL_S01_parse_domain_file_missing_domain_returns_none() -> None:
    """parse_domain_file retorna None quando campo 'domain' está ausente.

    Input:
      raw = {
          "version": "1",
          "entries": [{"canonical": "mensageria", "aliases": [], "strong_terms": [],
                        "weak_terms": [], "contexts": []}]
      }
      source = "bad.yaml"

    Output esperado:
      result is None

    Justificativa: sem 'domain', não há como registrar a origem semântica da entrada;
    descartar é mais seguro do que aceitar.

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "version": "1",
        "entries": [
            {
                "canonical": "mensageria",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "contexts": [],
            }
        ],
    }
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_missing_entries_returns_none() -> None:
    """parse_domain_file retorna None quando campo 'entries' está ausente.

    Input:
      raw = {"domain": "messaging", "version": "1"}
      source = "bad.yaml"

    Output esperado:
      result is None

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {"domain": "messaging", "version": "1"}
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_empty_domain_string_returns_none() -> None:
    """parse_domain_file retorna None quando 'domain' é string vazia.

    Input:
      raw = {"domain": "", "version": "1", "entries": []}
      source = "bad.yaml"

    Output esperado:
      result is None

    RED:  ModuleNotFoundError
    GREEN: assert result is None passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {"domain": "", "version": "1", "entries": []}
    result = parse_domain_file(raw, source="bad.yaml")
    assert result is None


def test_FAIL_S01_parse_domain_file_entry_without_canonical_is_skipped() -> None:
    """parse_domain_file ignora entradas sem 'canonical', mantém as válidas.

    Input:
      entries com 2 entradas:
        - entrada 1: sem campo 'canonical' (apenas aliases, strong_terms, etc.)
        - entrada 2: canonical='cache', aliases=['caching'], strong_terms=['ttl'],
                     weak_terms=[], contexts=[]

    Output esperado:
      result is not None
      len(result.entries) == 1          (entrada 1 foi ignorada)
      result.entries[0].canonical == "cache"
      result.entries[0].aliases   == ["caching"]
      result.entries[0].strong_terms == ["ttl"]
      result.entries[0].weak_terms   == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "version": "1",
        "entries": [
            {
                # sem 'canonical'
                "aliases": ["caching"],
                "strong_terms": ["imemorycache"],
                "weak_terms": [],
                "contexts": [],
            },
            {
                "canonical": "cache",
                "aliases": ["caching"],
                "strong_terms": ["ttl"],
                "weak_terms": [],
                "contexts": [],
            },
        ],
    }
    result = parse_domain_file(raw, source="caching.yaml")

    assert result is not None
    assert len(result.entries) == 1
    assert result.entries[0].canonical == "cache"
    assert result.entries[0].aliases == ["caching"]
    assert result.entries[0].strong_terms == ["ttl"]
    assert result.entries[0].weak_terms == []


def test_FAIL_S01_parse_domain_file_unknown_fields_ignored() -> None:
    """parse_domain_file ignora campos desconhecidos (schema extensível).

    Input:
      raw com campo desconhecido 'future_field' no nível superior
      entrada com campo desconhecido 'extra_metadata'

    Output esperado:
      Nenhuma exceção
      result is not None
      result.entries[0].canonical == "cache"

    RED:  ModuleNotFoundError
    GREEN: nenhuma exceção + asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "version": "1",
        "future_field": "ignored at top level",
        "entries": [
            {
                "canonical": "cache",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "contexts": [],
                "extra_metadata": "ignored at entry level",
            }
        ],
    }
    result = parse_domain_file(raw, source="caching.yaml")

    assert result is not None
    assert result.entries[0].canonical == "cache"


def test_FAIL_S01_parse_domain_file_optional_fields_default_to_empty_list() -> None:
    """parse_domain_file trata aliases/strong_terms/weak_terms/contexts ausentes como [].

    Input:
      entrada com somente 'canonical', sem os demais campos opcionais

    Output esperado:
      entry.aliases      == []
      entry.strong_terms == []
      entry.weak_terms   == []
      entry.contexts     == []

    RED:  ModuleNotFoundError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "minimal",
        "version": "1",
        "entries": [{"canonical": "cache"}],
    }
    result = parse_domain_file(raw, source="minimal.yaml")

    assert result is not None
    entry = result.entries[0]
    assert entry.aliases == []
    assert entry.strong_terms == []
    assert entry.weak_terms == []
    assert entry.contexts == []


def test_FAIL_S01_parse_domain_file_version_defaults_to_one() -> None:
    """parse_domain_file usa '1' como version default quando campo ausente.

    Input:
      raw sem campo 'version'

    Output esperado:
      result.version == "1"

    RED:  ModuleNotFoundError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "caching",
        "entries": [{"canonical": "cache"}],
    }
    result = parse_domain_file(raw, source="no-version.yaml")

    assert result is not None
    assert result.version == "1"


def test_FAIL_S01_parse_domain_file_context_rule_fields() -> None:
    """parse_domain_file faz parse do campo 'contexts' em ContextRule objects.

    Input:
      entry com contexts contendo um ContextRule:
        path_pattern: "**/dns*.md"
        extra_terms:  ["nameserver", "resolver"]

    Output esperado:
      entry.contexts[0].path_pattern == "**/dns*.md"
      entry.contexts[0].extra_terms  == ["nameserver", "resolver"]

    Nota: ContextRule é parseado mas NÃO usado em scoring nesta versão (V2).

    RED:  ModuleNotFoundError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = {
        "domain": "dns",
        "version": "1",
        "entries": [
            {
                "canonical": "ttl",
                "aliases": [],
                "strong_terms": [],
                "weak_terms": [],
                "contexts": [
                    {
                        "path_pattern": "**/dns*.md",
                        "extra_terms": ["nameserver", "resolver"],
                    }
                ],
            }
        ],
    }
    result = parse_domain_file(raw, source="dns.yaml")

    assert result is not None
    entry = result.entries[0]
    assert len(entry.contexts) == 1
    assert entry.contexts[0].path_pattern == "**/dns*.md"
    assert entry.contexts[0].extra_terms == ["nameserver", "resolver"]
```

### Implementação S-01

Criar `mcp-instructions-server/corporate_instructions_mcp/expansion.py` com:
- [ ] Dataclasses: `ContextRule`, `ExpansionEntry`, `ExpansionDomain`.
- [ ] Constantes: `ALIAS_WEIGHT = 0.9`, `STRONG_WEIGHT = 0.7`, `WEAK_WEIGHT = 0.3`.
- [ ] Função `parse_domain_file(raw: dict, source: str) -> ExpansionDomain | None`.
- [ ] Usar `_normalize_token` de `indexing.py` para normalizar todos os tokens.
- [ ] `log.warning()` em cada caso de retorno None ou entrada ignorada.

### Critérios de aceite — S-01

- [ ] Todos os `test_FAIL_S01_*` passam.
- [ ] `pytest -q` permanece verde (zero regressões nos testes existentes).

---

## S-02 — Loader corpus-aware

### Background

O mapa de expansão deve ser carregado a partir do corpus ativo (`INSTRUCTIONS_ROOT`), não
do pacote Python. O diretório esperado é `INSTRUCTIONS_ROOT/metadata/corpus-query-expansion-map/`.
O loader lê todos os arquivos `.yaml` do diretório, faz o parse de cada um e consolida em
um `ExpansionMap`.

```python
@dataclass(frozen=True)
class ExpansionMap:
    domains: list[ExpansionDomain]
    disabled: bool   # True se nenhum domínio válido foi carregado

def load_corpus_expansion_map(corpus_root: Path) -> ExpansionMap:
    """Lê todos os *.yaml em corpus_root/metadata/corpus-query-expansion-map/.

    Comportamento:
      - Se o diretório não existir: retorna ExpansionMap(domains=[], disabled=True).
      - Se o diretório existir mas vazio: retorna ExpansionMap(domains=[], disabled=True).
      - Se um arquivo tiver erro de parse YAML: loga warning, pula o arquivo, continua.
      - Se um arquivo retornar None em parse_domain_file: loga warning, pula, continua.
      - Se ao menos um arquivo for carregado com sucesso: disabled=False.
      - Se todos os arquivos falharem: disabled=True.
      - NUNCA lança exceção (incluindo OSError/PermissionError): loga, retorna disabled.
    """
```

### Testes RED — S-02

**Estado RED**: falham com `ImportError` (função não existe no módulo ainda não completo).

```python
# === Seção: S-02 — Loader corpus-aware ===

def test_FAIL_S02_load_from_nonexistent_directory_returns_disabled() -> None:
    """load_corpus_expansion_map retorna ExpansionMap disabled quando dir não existe.

    Input:
      corpus_root = Path("/tmp/nonexistent_corpus_xyz_12345")
      (garante-se que não existe via tmp aleatório)

    Output esperado:
      result.disabled == True
      result.domains  == []

    Justificativa: corpus sem mapa de expansão → expansão desabilitada,
    não fallback silencioso (ADR-002, seção 2).

    RED:  ImportError ou AttributeError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    with tempfile.TemporaryDirectory() as tmp:
        nonexistent = Path(tmp) / "nonexistent_subdir"
        result = load_corpus_expansion_map(nonexistent)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_from_empty_map_directory_returns_disabled() -> None:
    """load_corpus_expansion_map retorna disabled quando metadata/corpus-query-expansion-map/ existe mas vazio.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/   ← diretório vazio (nenhum .yaml)

    Output esperado:
      result.disabled == True
      result.domains  == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_single_valid_file() -> None:
    """load_corpus_expansion_map carrega um arquivo YAML válido com sucesso.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            messaging.yaml    ← conteúdo abaixo

    Conteúdo de messaging.yaml:
      domain: messaging
      version: "1"
      entries:
        - canonical: mensageria
          aliases:      [messaging]
          strong_terms: [rabbitmq, publish, consume]
          weak_terms:   [outbox]
          contexts:     []

    Output esperado:
      result.disabled        == False
      len(result.domains)    == 1
      result.domains[0].domain           == "messaging"
      result.domains[0].source_file      == "messaging.yaml"
      len(result.domains[0].entries)     == 1
      result.domains[0].entries[0].canonical     == "mensageria"
      result.domains[0].entries[0].aliases       == ["messaging"]
      result.domains[0].entries[0].strong_terms  == ["rabbitmq", "publish", "consume"]
      result.domains[0].entries[0].weak_terms    == ["outbox"]

    RED:  ImportError
    GREEN: todos os asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    yaml_content = """\
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases:
      - messaging
    strong_terms:
      - rabbitmq
      - publish
      - consume
    weak_terms:
      - outbox
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "messaging.yaml").write_text(yaml_content, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 1
    domain = result.domains[0]
    assert domain.domain == "messaging"
    assert domain.source_file == "messaging.yaml"
    assert len(domain.entries) == 1
    entry = domain.entries[0]
    assert entry.canonical == "mensageria"
    assert entry.aliases == ["messaging"]
    assert entry.strong_terms == ["rabbitmq", "publish", "consume"]
    assert entry.weak_terms == ["outbox"]


def test_FAIL_S02_load_multiple_valid_files() -> None:
    """load_corpus_expansion_map carrega múltiplos arquivos YAML e consolida.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            messaging.yaml    ← domain: messaging, 1 entry
            caching.yaml      ← domain: caching,   1 entry

    Output esperado:
      result.disabled        == False
      len(result.domains)    == 2
      {d.domain for d in result.domains} == {"messaging", "caching"}

    Nota: a ordem dos domínios pode variar (sorted() por filename garantirá ordem estável
    se implementado, mas o teste só verifica o conjunto).

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    messaging_yaml = """\
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases: [messaging]
    strong_terms: [rabbitmq]
    weak_terms: []
    contexts: []
"""
    caching_yaml = """\
domain: caching
version: "1"
entries:
  - canonical: cache
    aliases: [caching]
    strong_terms: [imemorycache, ttl]
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "messaging.yaml").write_text(messaging_yaml, encoding="utf-8")
        (map_dir / "caching.yaml").write_text(caching_yaml, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 2
    domains_names = {d.domain for d in result.domains}
    assert domains_names == {"messaging", "caching"}


def test_FAIL_S02_invalid_yaml_syntax_skipped_valid_loaded() -> None:
    """Arquivo com YAML inválido é ignorado; arquivos válidos são carregados.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            bad.yaml       ← YAML sintaticamente inválido
            caching.yaml   ← YAML válido

    Output esperado:
      result.disabled        == False   (ao menos um arquivo válido)
      len(result.domains)    == 1       (somente caching carregado)
      result.domains[0].domain == "caching"

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    bad_yaml = "domain: [unclosed bracket\n  invalid: yaml: :\n"
    caching_yaml = """\
domain: caching
version: "1"
entries:
  - canonical: cache
    aliases: []
    strong_terms: [ttl]
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "bad.yaml").write_text(bad_yaml, encoding="utf-8")
        (map_dir / "caching.yaml").write_text(caching_yaml, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is False
    assert len(result.domains) == 1
    assert result.domains[0].domain == "caching"


def test_FAIL_S02_all_files_invalid_returns_disabled() -> None:
    """Se todos os arquivos falharem no parse, retorna disabled=True.

    Setup:
      corpus_root/
        metadata/
          corpus-query-expansion-map/
            bad1.yaml   ← YAML inválido
            bad2.yaml   ← YAML sem campo 'domain' (parse_domain_file retorna None)

    Output esperado:
      result.disabled     == True
      result.domains      == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    bad1 = "::invalid yaml::"
    bad2 = """\
version: "1"
entries:
  - canonical: cache
    aliases: []
    strong_terms: []
    weak_terms: []
    contexts: []
"""
    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "bad1.yaml").write_text(bad1, encoding="utf-8")
        (map_dir / "bad2.yaml").write_text(bad2, encoding="utf-8")

        result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []


def test_FAIL_S02_load_does_not_raise_on_os_error() -> None:
    """load_corpus_expansion_map não lança exceção em caso de erro de OS/permissão.

    Estratégia: criar arquivo com conteúdo que cause erro de leitura simulado através de
    monkeypatching de yaml.safe_load para lançar OSError.

    Input:
      corpus_root existente com um arquivo .yaml válido
      yaml.safe_load mockado para lançar OSError("permission denied")

    Output esperado:
      Nenhuma exceção levantada
      result.disabled == True
      result.domains  == []

    RED:  ImportError
    GREEN: asserts passam
    """
    import tempfile
    from pathlib import Path
    from unittest.mock import patch
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    yaml_content = "domain: caching\nversion: '1'\nentries: []\n"

    with tempfile.TemporaryDirectory() as tmp:
        corpus_root = Path(tmp)
        map_dir = corpus_root / "metadata" / "corpus-query-expansion-map"
        map_dir.mkdir(parents=True)
        (map_dir / "caching.yaml").write_text(yaml_content, encoding="utf-8")

        with patch("yaml.safe_load", side_effect=OSError("permission denied")):
            result = load_corpus_expansion_map(corpus_root)

    assert result.disabled is True
    assert result.domains == []
```

### Implementação S-02

Adicionar a `expansion.py`:
- [ ] Dataclass `ExpansionMap(domains: list[ExpansionDomain], disabled: bool)`.
- [ ] Função `load_corpus_expansion_map(corpus_root: Path) -> ExpansionMap`.
- [ ] Diretório de busca: `corpus_root / "metadata" / "corpus-query-expansion-map"`.
- [ ] Iterar sobre `*.yaml` em ordem sorted (estabilidade).
- [ ] Para cada arquivo: `yaml.safe_load()` dentro de try/except amplo; chamar
  `parse_domain_file()`; ignorar None; acumular domínios válidos.
- [ ] Retornar `ExpansionMap(domains=valid_domains, disabled=len(valid_domains) == 0)`.

### Critérios de aceite — S-02

- [ ] Todos os `test_FAIL_S02_*` passam.
- [ ] `pytest -q` permanece verde.

---

## S-03 — Lookup unidirecional ponderado

### Background

A partir de um `ExpansionMap`, construir um lookup que mapeia cada canonical term para uma
lista de `(term, weight)` pares — **unidirecional**: apenas `canonical → [expanded terms]`,
NUNCA `expanded_term → [canonical, others]`.

```python
def build_unidirectional_lookup(
    expansion_map: ExpansionMap,
) -> dict[str, list[tuple[str, float]]]:
    """Retorna dict canonical → [(term, weight), ...].

    Regras:
      - Chave: somente termos que aparecem como 'canonical' em alguma ExpansionEntry.
      - Valor: lista de (term, weight) para aliases (ALIAS_WEIGHT), strong_terms
               (STRONG_WEIGHT), weak_terms (WEAK_WEIGHT).
      - Se um mesmo canonical aparece em múltiplos domínios: as listas são concatenadas
        (sem duplicatas de term; em caso de duplicata, mantém o maior peso).
      - O canonical em si NÃO aparece na lista de expansão (não é auto-expandido).
      - Termos que aparecem somente como expanded (nunca como canonical) NÃO têm entrada
        no lookup.
    """
```

### Testes RED — S-03

```python
# === Seção: S-03 — Lookup unidirecional ponderado ===

def _make_expansion_map_from_raw(domains_raw: list[dict], sources: list[str]):
    """Helper: cria ExpansionMap diretamente de dicts (para isolar S-03 de S-02)."""
    from corporate_instructions_mcp.expansion import parse_domain_file, ExpansionMap
    domains = []
    for raw, src in zip(domains_raw, sources):
        d = parse_domain_file(raw, source=src)
        if d is not None:
            domains.append(d)
    return ExpansionMap(domains=domains, disabled=len(domains) == 0)


def test_FAIL_S03_canonical_expands_to_typed_terms() -> None:
    """build_unidirectional_lookup mapeia canonical → [(term, weight)] corretamente.

    Input:
      ExpansionMap com um domínio 'messaging', uma entry:
        canonical:    "mensageria"
        aliases:      ["messaging"]
        strong_terms: ["rabbitmq", "publish"]
        weak_terms:   ["outbox"]
        contexts:     []

    Output esperado (lookup["mensageria"]):
      Contém (peso exato):
        ("messaging", 0.9)   ← alias
        ("rabbitmq",  0.7)   ← strong_term
        ("publish",   0.7)   ← strong_term
        ("outbox",    0.3)   ← weak_term

    Ordem: não garantida; verificar como conjunto de pares.

    RED:  ImportError ou AttributeError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "mensageria" in lookup
    pairs = set(lookup["mensageria"])
    assert ("messaging", 0.9) in pairs
    assert ("rabbitmq", 0.7) in pairs
    assert ("publish", 0.7) in pairs
    assert ("outbox", 0.3) in pairs


def test_FAIL_S03_non_canonical_term_has_no_entry() -> None:
    """Termos expanded (não-canonical) NÃO aparecem como chave no lookup.

    Este é o comportamento central da ADR-002: lookup UNIDIRECIONAL.

    Input (mesmo do teste anterior):
      canonical:    "mensageria"
      aliases:      ["messaging"]
      strong_terms: ["rabbitmq", "publish"]
      weak_terms:   ["outbox"]

    Output esperado:
      "rabbitmq" NOT in lookup     ← só mensageria é canonical
      "messaging" NOT in lookup
      "publish" NOT in lookup
      "outbox" NOT in lookup

    Contraste com comportamento ATUAL (bidirecional) que seria:
      "rabbitmq" IN lookup (gerado por _build_expansion_lookup)

    RED:  ImportError ou AttributeError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "rabbitmq" not in lookup, (
        "rabbitmq é termo expandido, não canonical — NÃO deve aparecer como chave no lookup unidirecional"
    )
    assert "messaging" not in lookup
    assert "publish" not in lookup
    assert "outbox" not in lookup


def test_FAIL_S03_same_canonical_across_two_domains_merges_with_max_weight() -> None:
    """Mesmo canonical em dois domínios: expansões concatenadas, duplicata mantém maior peso.

    Input:
      Domínio 'observability':
        canonical: "observabilidade"
        strong_terms: ["opentelemetry", "health"]
        weak_terms:   ["deployment"]

      Domínio 'configuration':
        canonical: "observabilidade"   ← mesmo canonical em outro domínio
        strong_terms: ["production"]
        weak_terms:   ["health"]       ← 'health' reaparece como weak

    Output esperado para lookup["observabilidade"]:
      ("opentelemetry", 0.7)   ← strong em observability
      ("health",        0.7)   ← aparece como strong (0.7) e weak (0.3) → mantém 0.7
      ("deployment",    0.3)   ← weak em observability
      ("production",    0.7)   ← strong em configuration

    RED:  ImportError ou AttributeError
    GREEN: todos os asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "observability",
                "version": "1",
                "entries": [
                    {
                        "canonical": "observabilidade",
                        "aliases": [],
                        "strong_terms": ["opentelemetry", "health"],
                        "weak_terms": ["deployment"],
                        "contexts": [],
                    }
                ],
            },
            {
                "domain": "configuration",
                "version": "1",
                "entries": [
                    {
                        "canonical": "observabilidade",
                        "aliases": [],
                        "strong_terms": ["production"],
                        "weak_terms": ["health"],
                        "contexts": [],
                    }
                ],
            },
        ],
        ["observability.yaml", "configuration.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    pairs = dict(lookup["observabilidade"])  # {term: weight}
    assert pairs.get("opentelemetry") == pytest.approx(0.7)
    assert pairs.get("health") == pytest.approx(0.7)   # max(0.7, 0.3) = 0.7
    assert pairs.get("deployment") == pytest.approx(0.3)
    assert pairs.get("production") == pytest.approx(0.7)


def test_FAIL_S03_disabled_map_returns_empty_lookup() -> None:
    """ExpansionMap com disabled=True gera lookup vazio.

    Input:
      ExpansionMap(domains=[], disabled=True)

    Output esperado:
      lookup == {}

    RED:  ImportError
    GREEN: assert passa
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, ExpansionMap

    expansion_map = ExpansionMap(domains=[], disabled=True)
    lookup = build_unidirectional_lookup(expansion_map)

    assert lookup == {}


def test_FAIL_S03_canonical_not_self_expanding() -> None:
    """O canonical em si NÃO aparece como expansão de si mesmo.

    Input:
      canonical: "cache"
      aliases:      ["caching"]
      strong_terms: ["ttl"]
      weak_terms:   []

    Output esperado:
      lookup["cache"] não contém ("cache", qualquer_peso)
      lookup["cache"] contém ("caching", 0.9)
      lookup["cache"] contém ("ttl", 0.7)

    RED:  ImportError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "caching",
                "version": "1",
                "entries": [
                    {
                        "canonical": "cache",
                        "aliases": ["caching"],
                        "strong_terms": ["ttl"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["caching.yaml"],
    )

    lookup = build_unidirectional_lookup(expansion_map)

    assert "cache" in lookup
    terms_in_lookup = {term for term, _ in lookup["cache"]}
    assert "cache" not in terms_in_lookup, (
        "O canonical 'cache' não deve aparecer como expansão de si mesmo"
    )
    assert "caching" in terms_in_lookup
    assert "ttl" in terms_in_lookup
```

### Implementação S-03

Adicionar a `expansion.py`:
- [ ] Função `build_unidirectional_lookup(expansion_map: ExpansionMap) -> dict[str, list[tuple[str, float]]]`.
- [ ] Iterar sobre todos os `entry` de todos os `domain` em `expansion_map.domains`.
- [ ] Para cada entry: acumular `(term, weight)` em `accumulator[entry.canonical]`.
  - aliases → `ALIAS_WEIGHT`
  - strong_terms → `STRONG_WEIGHT`
  - weak_terms → `WEAK_WEIGHT`
- [ ] Em caso de duplicata de term: manter `max(existing_weight, new_weight)`.
- [ ] Nunca adicionar o canonical em si à lista.
- [ ] Se `expansion_map.disabled`: retornar `{}`.

### Critérios de aceite — S-03

- [ ] Todos os `test_FAIL_S03_*` passam.
- [ ] `pytest -q` permanece verde.

---

## S-04 — Integração com `expand_query_with_metadata()` e diagnóstico

### Background

Modificar `expand_query_with_metadata()` em `indexing.py` para aceitar um `ExpansionMap`
opcional e usar o novo lookup ponderado unidirecional. Adicionar `ExpansionDiagnostic` ao
`ExpandedQueryInfo` para rastreabilidade.

Mudança na assinatura (interna, não é tool pública):

```python
# ANTES:
def expand_query_with_metadata(tokens: list[str]) -> ExpandedQueryInfo:
    ...

# DEPOIS:
def expand_query_with_metadata(
    tokens: list[str],
    expansion_map: "ExpansionMap | None" = None,
) -> ExpandedQueryInfo:
    ...
```

Adicionar ao `ExpandedQueryInfo`:

```python
@dataclass(frozen=True)
class ExpandedQueryInfo:
    weights: dict[str, float]
    user_tokens: list[str]
    expansion_added_terms: list[str]
    expansion_truncated: bool
    expansion_count: int
    diagnostics: list["ExpansionDiagnostic"]   # NOVO campo
    expansion_disabled: bool                    # NOVO campo — True se map is None ou disabled
```

`ExpansionDiagnostic` (definir em `expansion.py`):

```python
@dataclass(frozen=True)
class ExpansionDiagnostic:
    canonical: str        # token do usuário que disparou a expansão
    term: str             # termo adicionado
    relation: str         # "alias" | "strong" | "weak"
    weight: float         # peso aplicado (0.9 / 0.7 / 0.3)
    source_domain: str    # domain do arquivo que forneceu a entry
    source_file: str      # nome do arquivo (ex: "messaging.yaml")
```

Comportamento quando `expansion_map is None` ou `expansion_map.disabled is True`:
- `weights` contém somente user tokens com peso 1.0.
- `expansion_added_terms == []`.
- `expansion_count == 0`.
- `expansion_truncated == False`.
- `diagnostics == []`.
- `expansion_disabled == True`.

### Testes RED — S-04

```python
# === Seção: S-04 — Integração expand_query_with_metadata ===

def test_FAIL_S04_expand_with_none_map_disables_expansion() -> None:
    """expand_query_with_metadata com expansion_map=None retorna só user tokens.

    Input:
      tokens = ["mensageria", "rabbitmq"]
      expansion_map = None

    Output esperado:
      info.expansion_disabled == True
      info.expansion_added_terms == []
      info.expansion_count == 0
      info.weights == {"mensageria": 1.0, "rabbitmq": 1.0}
        (apenas user tokens com peso 1.0; nenhum termo adicionado por expansão)
      info.diagnostics == []

    RED:  TypeError (parâmetro expansion_map não aceito ainda)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    tokens = ["mensageria", "rabbitmq"]
    info = expand_query_with_metadata(tokens, expansion_map=None)

    assert info.expansion_disabled is True
    assert info.expansion_added_terms == []
    assert info.expansion_count == 0
    assert info.diagnostics == []
    assert info.weights.get("mensageria") == pytest.approx(1.0)
    assert info.weights.get("rabbitmq") == pytest.approx(1.0)
    # Nenhum outro termo com peso < 1.0 deve aparecer
    for term, w in info.weights.items():
        assert w == pytest.approx(1.0), (
            f"Com expansion_map=None, '{term}' não deveria ter peso {w} (esperado 1.0)"
        )


def test_FAIL_S04_expand_with_disabled_map_disables_expansion() -> None:
    """expand_query_with_metadata com ExpansionMap(disabled=True) retorna só user tokens.

    Input:
      tokens = ["observabilidade"]
      expansion_map = ExpansionMap(domains=[], disabled=True)

    Output esperado:
      info.expansion_disabled == True
      info.expansion_added_terms == []
      "observabilidade" in info.weights com peso 1.0
      Nenhum termo expandido presente em info.weights

    RED:  ImportError / TypeError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata
    from corporate_instructions_mcp.expansion import ExpansionMap

    disabled_map = ExpansionMap(domains=[], disabled=True)
    tokens = ["observabilidade"]
    info = expand_query_with_metadata(tokens, expansion_map=disabled_map)

    assert info.expansion_disabled is True
    assert info.weights.get("observabilidade") == pytest.approx(1.0)
    assert info.expansion_added_terms == []


def test_FAIL_S04_expand_with_valid_map_applies_typed_weights() -> None:
    """expand_query_with_metadata usa pesos tipados do novo mapa.

    Setup:
      ExpansionMap com um domínio 'messaging':
        canonical: "mensageria"
        aliases:      ["messaging"]
        strong_terms: ["rabbitmq", "publish"]
        weak_terms:   ["outbox"]

    Input:
      tokens = ["mensageria"]
      expansion_map = (mapa acima)

    Output esperado:
      info.expansion_disabled == False
      info.weights["mensageria"] == 1.0    ← user token
      info.weights["messaging"]  == 0.9   ← alias
      info.weights["rabbitmq"]   == 0.7   ← strong_term
      info.weights["publish"]    == 0.7   ← strong_term
      info.weights["outbox"]     == 0.3   ← weak_term
      "rabbitmq" in info.expansion_added_terms
      "outbox" in info.expansion_added_terms

    RED:  ImportError / TypeError / AssertionError (pesos errados no sistema atual)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq", "publish"],
                        "weak_terms": ["outbox"],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["mensageria"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert info.expansion_disabled is False
    assert info.weights.get("mensageria") == pytest.approx(1.0)
    assert info.weights.get("messaging") == pytest.approx(0.9)
    assert info.weights.get("rabbitmq") == pytest.approx(0.7)
    assert info.weights.get("publish") == pytest.approx(0.7)
    assert info.weights.get("outbox") == pytest.approx(0.3)

    assert "rabbitmq" in info.expansion_added_terms
    assert "outbox" in info.expansion_added_terms


def test_FAIL_S04_expand_diagnostics_populated() -> None:
    """expand_query_with_metadata popula diagnostics quando mapa válido.

    Setup:
      ExpansionMap com um domínio 'messaging' (source_file="messaging.yaml"):
        canonical: "mensageria"
        aliases:   ["messaging"]   ← deve gerar um ExpansionDiagnostic

    Input:
      tokens = ["mensageria"]

    Output esperado:
      len(info.diagnostics) >= 1
      info.diagnostics tem um item onde:
        diagnostic.canonical     == "mensageria"
        diagnostic.term          == "messaging"
        diagnostic.relation      == "alias"
        diagnostic.weight        == 0.9
        diagnostic.source_domain == "messaging"
        diagnostic.source_file   == "messaging.yaml"

    RED:  ImportError / AttributeError (campo diagnostics não existe)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": ["messaging"],
                        "strong_terms": ["rabbitmq"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["mensageria"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert len(info.diagnostics) >= 1

    alias_diag = next(
        (d for d in info.diagnostics if d.term == "messaging"),
        None,
    )
    assert alias_diag is not None, "Diagnóstico para alias 'messaging' não encontrado"
    assert alias_diag.canonical == "mensageria"
    assert alias_diag.relation == "alias"
    assert alias_diag.weight == pytest.approx(0.9)
    assert alias_diag.source_domain == "messaging"
    assert alias_diag.source_file == "messaging.yaml"


def test_FAIL_S04_expand_unidirectional_no_cross_contamination() -> None:
    """Com o novo mapa, 'rabbitmq' como token de usuário NÃO expande para 'mensageria'.

    Este é o teste central da ADR-002: sem expansão cruzada indevida.

    Setup:
      ExpansionMap com 'mensageria' como canonical → strong: rabbitmq
      (rabbitmq NÃO é canonical, portanto não tem expansão)

    Input:
      tokens = ["rabbitmq"]

    Output esperado:
      info.expansion_disabled == False   (mapa está ativo)
      info.expansion_added_terms == []   (rabbitmq não tem expansão no lookup)
      "mensageria" NOT in info.weights   (não houve expansão cruzada)

    Contraste com comportamento ATUAL (bidirecional):
      "mensageria" ESTARIA em info.weights via _EXPANSION_LOOKUP["rabbitmq"]

    RED:  AssertionError (sistema atual é bidirecional) ou ImportError
    GREEN: asserts passam (sistema novo é unidirecional)
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    expansion_map = _make_expansion_map_from_raw(
        [
            {
                "domain": "messaging",
                "version": "1",
                "entries": [
                    {
                        "canonical": "mensageria",
                        "aliases": [],
                        "strong_terms": ["rabbitmq"],
                        "weak_terms": [],
                        "contexts": [],
                    }
                ],
            }
        ],
        ["messaging.yaml"],
    )

    tokens = ["rabbitmq"]
    info = expand_query_with_metadata(tokens, expansion_map=expansion_map)

    assert info.expansion_disabled is False
    assert info.expansion_added_terms == [], (
        f"'rabbitmq' não é canonical, não deve ter expansão. "
        f"Termos adicionados: {info.expansion_added_terms}"
    )
    assert "mensageria" not in info.weights, (
        "Expansão cruzada indevida: 'rabbitmq' expandiu para 'mensageria' "
        "(ADR-002 exige lookup unidirecional)"
    )


def test_FAIL_S04_expand_query_without_explicit_map_parameter_backward_compat() -> None:
    """expand_query_with_metadata sem parâmetro expansion_map continua funcionando.

    Garante retrocompatibilidade da assinatura. Quando chamada sem o novo parâmetro,
    o comportamento deve ser equivalente a expansion_map=None (expansão desabilitada).

    Input:
      tokens = ["cache"]
      (sem parâmetro expansion_map — chamada legada)

    Output esperado:
      Nenhuma exceção
      info.expansion_disabled == True
      info.weights.get("cache") == 1.0

    RED:  pode passar ou falhar dependendo do estado de refatoração
    GREEN: asserts passam com nova implementação
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata

    tokens = ["cache"]
    info = expand_query_with_metadata(tokens)  # sem expansion_map

    assert info.expansion_disabled is True
    assert info.weights.get("cache") == pytest.approx(1.0)
```

### Implementação S-04

Modificações em `indexing.py`:

- [ ] Remover módulo-level: `QUERY_EXPANSION_MAP`, `_EXPANSION_LOOKUP`,
      `_load_expansion_map_from_file()`, `_build_expansion_lookup()`.
- [ ] Remover `DEFAULT_SYNONYMS` (ou comentar com marcação `# REMOVED: ver ADR-002 / EPIC-10`).
- [ ] Importar `ExpansionMap, build_unidirectional_lookup, ExpansionDiagnostic` de `expansion.py`.
- [ ] Adicionar `expansion_disabled: bool` e `diagnostics: list[ExpansionDiagnostic]` ao
      `ExpandedQueryInfo`.
- [ ] Modificar `expand_query_with_metadata(tokens, expansion_map=None)`:
  - Se `expansion_map is None` ou `expansion_map.disabled`: retornar `ExpandedQueryInfo`
    com apenas user tokens em `weights` (peso 1.0), `expansion_disabled=True`,
    `diagnostics=[]`.
  - Caso contrário: chamar `build_unidirectional_lookup(expansion_map)`, aplicar pesos
    tipados, gerar `ExpansionDiagnostic` por cada expansão.
- [ ] Atualizar todos os pontos internos que chamam `expand_query_with_metadata()` para
  continuar funcionando (server.py usa expansão via `_ensure_index()` — atualizar para
  passar o mapa carregado junto com o índice).

**Mudança em `server.py` necessária para passar o mapa:**

O `_ensure_index()` atual retorna `(idx, sig)`. Após a mudança, deve retornar `(idx, sig, expansion_map)`.
Isso é uma mudança interna e não altera contratos de tools.

### Critérios de aceite — S-04

- [ ] Todos os `test_FAIL_S04_*` passam.
- [ ] `pytest -q` permanece verde.

---

## S-05 — Domain YAML files para o fixture corpus

### Background

Criar os arquivos YAML por domínio em `fixtures/instructions/metadata/corpus-query-expansion-map/`.
Cada arquivo define as relações semânticas para os documentos do corpus de fixture. As relações
devem ser **unidirecionais** e tipadas conforme o novo schema.

**Contrato geral dos arquivos**:

- Cada relação é estritamente unidirecional: se `mensageria → rabbitmq` existe, NÃO criar
  `rabbitmq → mensageria`.
- `aliases` reservado para termos genuinamente equivalentes (mesma intensidade semântica).
- `strong_terms`: documentos que devem aparecer quando o canonical é consultado.
- `weak_terms`: documentos auxiliares, sinal contextual fraco.
- `dns.yaml` isolado: `retry` NÃO é strong/weak term de `dns` (previne cruzamento com resiliência).

**Arquivos a criar** (contendo ao menos os mappings das queries afetadas pela suíte de 24 casos):

`messaging.yaml`:

```yaml
domain: messaging
version: "1"
entries:
  - canonical: mensageria
    aliases:
      - messaging
    strong_terms:
      - rabbitmq
      - publish
      - consume
    weak_terms:
      - outbox
    contexts: []
```

`observability.yaml`:

```yaml
domain: observability
version: "1"
entries:
  - canonical: observabilidade
    aliases:
      - observability
    strong_terms:
      - opentelemetry
      - tracing
      - health
    weak_terms:
      - production
      - deployment
    contexts: []
  - canonical: metricas
    aliases:
      - metrics
    strong_terms:
      - spans
      - tracing
      - opentelemetry
    weak_terms:
      - observability
    contexts: []
  - canonical: traceparent
    aliases: []
    strong_terms:
      - tracing
      - correlation
      - opentelemetry
    weak_terms:
      - httpclient
    contexts: []
  - canonical: correlation
    aliases: []
    strong_terms:
      - tracing
      - opentelemetry
    weak_terms:
      - health
    contexts: []
  - canonical: healthcheck
    aliases: []
    strong_terms:
      - health
      - live
      - ready
      - readiness
    weak_terms:
      - production
    contexts: []
  - canonical: logs
    aliases:
      - logging
    strong_terms:
      - observability
    weak_terms:
      - readiness
      - production
    contexts: []
```

`architecture.yaml`:

```yaml
domain: architecture
version: "1"
entries:
  - canonical: arquitetura
    aliases:
      - architecture
    strong_terms:
      - layering
      - clean-architecture
      - solid
    weak_terms:
      - dotnet
    contexts: []
  - canonical: dominio
    aliases:
      - domain
    strong_terms:
      - repository
      - interfaces
      - models
    weak_terms:
      - table-storage
    contexts: []
  - canonical: estruturar
    aliases: []
    strong_terms:
      - arquitetura
      - layering
      - camadas
    weak_terms:
      - dominio
    contexts: []
```

`persistence.yaml`:

```yaml
domain: persistence
version: "1"
entries:
  - canonical: persistencia
    aliases: []
    strong_terms:
      - dapper
      - sql
      - repositorio
      - data-access
    weak_terms:
      - efcore
    contexts: []
  - canonical: banco
    aliases: []
    strong_terms:
      - sql
      - dapper
      - efcore
    weak_terms:
      - transactions
    contexts: []
  - canonical: transacao
    aliases:
      - transactions
    strong_terms:
      - configuracao
      - configuration
    weak_terms:
      - readiness
      - producao
    contexts: []
  - canonical: queries
    aliases: []
    strong_terms:
      - sql
      - transactions
    weak_terms:
      - configuration
      - production
    contexts: []
```

`resilience.yaml`:

```yaml
domain: resilience
version: "1"
entries:
  - canonical: resiliencia
    aliases:
      - resilience
    strong_terms:
      - polly
      - circuit-breaker
      - timeout
    weak_terms:
      - tolerancia
    contexts: []
```

**Nota sobre `retry`**: NÃO incluir `retry` como strong/weak de `resiliencia` — `retry` é
um termo ambíguo que pode contaminar `dns-retry-pattern`. O `circuit-breaker` e `polly`
são suficientemente discriminativos.

`api.yaml`:

```yaml
domain: api
version: "1"
entries:
  - canonical: api
    aliases: []
    strong_terms:
      - problem-details
      - rfc7807
      - pagination
    weak_terms:
      - minimal-api
      - filtering
    contexts: []
  - canonical: paginacao
    aliases:
      - pagination
    strong_terms:
      - filtering
      - ordering
      - collection
    weak_terms:
      - envelope
    contexts: []
  - canonical: colecoes
    aliases:
      - collection
    strong_terms:
      - pagination
      - filtering
      - ordering
    weak_terms:
      - api-collection
    contexts: []
  - canonical: problemdetails
    aliases:
      - problem-details
    strong_terms:
      - rfc7807
      - error-catalog
      - errors
    weak_terms:
      - status-codes
    contexts: []
```

`security.yaml`:

```yaml
domain: security
version: "1"
entries:
  - canonical: seguranca
    aliases:
      - security
    strong_terms:
      - secrets
      - jwt
      - authentication
    weak_terms:
      - authorization
    contexts: []
  - canonical: segredos
    aliases:
      - secrets
    strong_terms:
      - security
      - logging
    weak_terms:
      - readiness
      - configuration
    contexts: []
  - canonical: claims
    aliases: []
    strong_terms:
      - jwt
      - authorization
    weak_terms:
      - error-catalog
    contexts: []
```

`caching.yaml`:

```yaml
domain: caching
version: "1"
entries:
  - canonical: cache
    aliases:
      - caching
    strong_terms:
      - imemorycache
      - idistributedcache
      - ttl
    weak_terms:
      - invalidation
    contexts: []
```

`validation.yaml`:

```yaml
domain: validation
version: "1"
entries:
  - canonical: validacao
    aliases:
      - validation
    strong_terms:
      - error-contracts
      - problem-details
    weak_terms:
      - "400"
      - "422"
    contexts: []
```

`configuration.yaml`:

```yaml
domain: configuration
version: "1"
entries:
  - canonical: configuracao
    aliases:
      - configuration
    strong_terms:
      - options
      - ioptions
      - feature-flags
    weak_terms:
      - deployment
    contexts: []
```

`dns.yaml`:

```yaml
domain: dns
version: "1"
entries:
  - canonical: dns
    aliases: []
    strong_terms:
      - nameserver
      - resolver
      - lookup
    weak_terms:
      - network
      - ttl
    contexts: []
```

**Nota crítica**: `retry` foi removido de `dns` para evitar a contaminação cruzada documentada
na ADR-002. `ttl` aparece como `weak_term` (sinal fraco, contextual).

`integration.yaml`:

```yaml
domain: integration
version: "1"
entries:
  - canonical: integracao
    aliases:
      - integration
    strong_terms:
      - httpclient
      - contracts
      - serialization
    weak_terms:
      - resilience
    contexts: []
  - canonical: saga
    aliases: []
    strong_terms:
      - orchestration
      - process-manager
      - consistency
    weak_terms:
      - idempotency
      - compensation
    contexts: []
```

### Testes RED — S-05

```python
# === Seção: S-05 — Domain YAML files no fixture corpus ===
# Setup: os testes assumem que INSTRUCTIONS_ROOT aponta para fixtures/instructions/

import os
from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent.parent.parent / "fixtures" / "instructions"
MAP_DIR = FIXTURES_ROOT / "metadata" / "corpus-query-expansion-map"


def test_FAIL_S05_map_directory_exists() -> None:
    """Diretório metadata/corpus-query-expansion-map/ deve existir no fixture corpus.

    Input:  filesystem — fixtures/instructions/metadata/corpus-query-expansion-map/
    Output: diretório existe e é um diretório (não arquivo)

    RED:  AssertionError (diretório não existe antes da criação dos arquivos)
    GREEN: assert passa
    """
    assert MAP_DIR.exists(), f"Diretório não existe: {MAP_DIR}"
    assert MAP_DIR.is_dir(), f"Caminho existe mas não é diretório: {MAP_DIR}"


def test_FAIL_S05_required_domain_files_present() -> None:
    """Todos os arquivos de domínio obrigatórios devem estar presentes.

    Input:  filesystem listing de MAP_DIR
    Output: cada filename da lista abaixo existe como arquivo .yaml

    Arquivos obrigatórios:
      messaging.yaml, observability.yaml, architecture.yaml, persistence.yaml,
      resilience.yaml, api.yaml, security.yaml, caching.yaml, validation.yaml,
      configuration.yaml, dns.yaml, integration.yaml

    RED:  AssertionError (arquivos não existem)
    GREEN: asserts passam
    """
    required = [
        "messaging.yaml",
        "observability.yaml",
        "architecture.yaml",
        "persistence.yaml",
        "resilience.yaml",
        "api.yaml",
        "security.yaml",
        "caching.yaml",
        "validation.yaml",
        "configuration.yaml",
        "dns.yaml",
        "integration.yaml",
    ]
    for filename in required:
        path = MAP_DIR / filename
        assert path.exists(), f"Arquivo de domínio ausente: {path}"
        assert path.is_file(), f"Caminho existe mas não é arquivo: {path}"


def test_FAIL_S05_messaging_yaml_mensageria_entry() -> None:
    """messaging.yaml contém entry 'mensageria' com strong_terms incluindo 'rabbitmq'.

    Input:  leitura e parse de fixtures/instructions/metadata/corpus-query-expansion-map/messaging.yaml
    Output:
      domain == "messaging"
      entry com canonical == "mensageria" existe
      entry.strong_terms contém "rabbitmq"
      entry.strong_terms contém "publish"
      entry.strong_terms contém "consume"
      entry.weak_terms contém "outbox"
      "rabbitmq" NÃO é canonical no arquivo (unidirectionality)

    RED:  FileNotFoundError ou AssertionError
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "messaging.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="messaging.yaml")

    assert domain is not None
    assert domain.domain == "messaging"

    mensageria_entry = next(
        (e for e in domain.entries if e.canonical == "mensageria"), None
    )
    assert mensageria_entry is not None, "Entry 'mensageria' não encontrada em messaging.yaml"
    assert "rabbitmq" in mensageria_entry.strong_terms
    assert "publish" in mensageria_entry.strong_terms
    assert "consume" in mensageria_entry.strong_terms
    assert "outbox" in mensageria_entry.weak_terms

    # Verificar unidirectionality: rabbitmq NÃO é canonical
    canonicals = {e.canonical for e in domain.entries}
    assert "rabbitmq" not in canonicals, (
        "'rabbitmq' não deve ser canonical em messaging.yaml (unidirecional: mensageria→rabbitmq)"
    )


def test_FAIL_S05_dns_yaml_retry_not_in_strong_or_weak_terms() -> None:
    """dns.yaml NÃO deve ter 'retry' como strong_term nem weak_term.

    Esta é a correção central do problema I-05 (EPIC-07): evitar que 'resiliencia → retry'
    contamine 'dns-retry-pattern' via expansão cruzada.

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/dns.yaml
    Output:
      Para toda entry do domínio dns:
        'retry' NOT in entry.strong_terms
        'retry' NOT in entry.weak_terms
        'retry' NOT in entry.aliases

    RED:  FileNotFoundError ou AssertionError (se retry estiver presente)
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "dns.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="dns.yaml")

    assert domain is not None
    for entry in domain.entries:
        assert "retry" not in entry.strong_terms, (
            f"'retry' está em strong_terms de '{entry.canonical}' em dns.yaml — "
            f"isto causaria expansão cruzada indevida com resiliencia"
        )
        assert "retry" not in entry.weak_terms, (
            f"'retry' está em weak_terms de '{entry.canonical}' em dns.yaml"
        )
        assert "retry" not in entry.aliases, (
            f"'retry' está em aliases de '{entry.canonical}' em dns.yaml"
        )


def test_FAIL_S05_resilience_yaml_retry_not_as_canonical() -> None:
    """resilience.yaml: 'retry' NÃO é canonical (evita geração de expansão bidirecional via retry).

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/resilience.yaml
    Output:
      'retry' NOT in {e.canonical for e in domain.entries}

    Justificativa: 'retry' como canonical geraria um lookup entry própria que poderia
    reconectar indiretamente com dns. A cobertura de retry vem via 'polly' e 'circuit-breaker'
    como strong_terms de 'resiliencia'.

    RED:  FileNotFoundError ou AssertionError
    GREEN: assert passa
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "resilience.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="resilience.yaml")

    assert domain is not None
    canonicals = {e.canonical for e in domain.entries}
    assert "retry" not in canonicals, (
        "'retry' não deve ser canonical em resilience.yaml — "
        "use 'polly' e 'circuit-breaker' como strong_terms de 'resiliencia'"
    )


def test_FAIL_S05_observability_yaml_observabilidade_entry() -> None:
    """observability.yaml contém entry 'observabilidade' com opentelemetry e health.

    Input:  leitura de fixtures/instructions/metadata/corpus-query-expansion-map/observability.yaml
    Output:
      domain == "observability"
      entry com canonical == "observabilidade" existe
      entry.strong_terms contém "opentelemetry"
      entry.strong_terms contém "health"

    RED:  FileNotFoundError ou AssertionError
    GREEN: asserts passam
    """
    import yaml
    from corporate_instructions_mcp.expansion import parse_domain_file

    raw = yaml.safe_load((MAP_DIR / "observability.yaml").read_text(encoding="utf-8"))
    domain = parse_domain_file(raw, source="observability.yaml")

    assert domain is not None
    assert domain.domain == "observability"

    obs_entry = next(
        (e for e in domain.entries if e.canonical == "observabilidade"), None
    )
    assert obs_entry is not None, "Entry 'observabilidade' não encontrada em observability.yaml"
    assert "opentelemetry" in obs_entry.strong_terms
    assert "health" in obs_entry.strong_terms


def test_FAIL_S05_load_corpus_expansion_map_from_fixtures() -> None:
    """load_corpus_expansion_map carrega todos os domínios do fixture corpus com sucesso.

    Input:  FIXTURES_ROOT = fixtures/instructions/
    Output:
      result.disabled == False
      len(result.domains) >= 10   (ao menos 10 domínios carregados)
      {d.domain for d in result.domains} contém:
        "messaging", "observability", "architecture", "persistence",
        "resilience", "api", "security", "caching", "validation",
        "configuration", "dns", "integration"

    RED:  ImportError / FileNotFoundError / AssertionError
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    result = load_corpus_expansion_map(FIXTURES_ROOT)

    assert result.disabled is False, (
        f"ExpansionMap retornou disabled=True. Verifique que os arquivos YAML existem em {MAP_DIR}"
    )
    assert len(result.domains) >= 10, (
        f"Esperado ao menos 10 domínios, obtido {len(result.domains)}: "
        f"{[d.domain for d in result.domains]}"
    )

    expected_domains = {
        "messaging", "observability", "architecture", "persistence",
        "resilience", "api", "security", "caching", "validation",
        "configuration", "dns", "integration",
    }
    loaded_domains = {d.domain for d in result.domains}
    missing = expected_domains - loaded_domains
    assert not missing, f"Domínios ausentes no mapa carregado: {missing}"
```

### Implementação S-05

- [ ] Criar `fixtures/instructions/metadata/corpus-query-expansion-map/` (diretório).
- [ ] Criar cada arquivo `.yaml` conforme schema especificado acima.
- [ ] Confirmar que `build_index()` em `indexing.py` continua ignorando o diretório
  `metadata/` (já existente no código, linha: `if metadata_root.exists() and path.is_relative_to(metadata_root): continue`).

### Critérios de aceite — S-05

- [ ] Todos os `test_FAIL_S05_*` passam.
- [ ] `pytest -q` permanece verde.
- [ ] `build_index(FIXTURES_ROOT)` não carrega nenhum arquivo de `metadata/` como documento.

---

## S-06 — Remover DEFAULT_SYNONYMS e synonyms.yaml bundled

### Background

Após S-04 (integração de `expand_query_with_metadata` com o novo mapa) e S-05 (domain YAML
files criados), remover o mecanismo de fallback silencioso:

1. `DEFAULT_SYNONYMS` em `indexing.py` — remover (não comentar, remover).
2. `synonyms.yaml` em `corporate_instructions_mcp/synonyms.yaml` — remover o arquivo.
3. `_load_expansion_map_from_file()` e `_build_expansion_lookup()` — já removidos em S-04;
   confirmar que não restam referências.

### Testes RED — S-06

```python
# === Seção: S-06 — Remoção de DEFAULT_SYNONYMS e synonyms.yaml bundled ===

def test_FAIL_S06_default_synonyms_not_in_indexing() -> None:
    """DEFAULT_SYNONYMS não deve existir em indexing.py após a remoção.

    Verifica que o módulo indexing não exporta mais DEFAULT_SYNONYMS.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, 'DEFAULT_SYNONYMS')` == False

    RED:  AssertionError (DEFAULT_SYNONYMS ainda existe no módulo atual)
    GREEN: assert passa após remoção
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "DEFAULT_SYNONYMS"), (
        "DEFAULT_SYNONYMS ainda existe em indexing.py — deve ser removido conforme ADR-002"
    )


def test_FAIL_S06_load_expansion_map_from_file_not_in_indexing() -> None:
    """_load_expansion_map_from_file não deve existir em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_load_expansion_map_from_file')` == False

    RED:  AssertionError (função ainda existe)
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_load_expansion_map_from_file"), (
        "_load_expansion_map_from_file ainda existe em indexing.py — deve ser removido"
    )


def test_FAIL_S06_build_expansion_lookup_not_in_indexing() -> None:
    """_build_expansion_lookup não deve existir em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_build_expansion_lookup')` == False

    RED:  AssertionError
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_build_expansion_lookup"), (
        "_build_expansion_lookup ainda existe em indexing.py — deve ser removido"
    )


def test_FAIL_S06_query_expansion_map_not_module_level() -> None:
    """QUERY_EXPANSION_MAP não deve existir como módulo-level em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, 'QUERY_EXPANSION_MAP')` == False

    RED:  AssertionError (ainda existe como global)
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "QUERY_EXPANSION_MAP"), (
        "QUERY_EXPANSION_MAP ainda existe em indexing.py como módulo-level global"
    )


def test_FAIL_S06_expansion_lookup_not_module_level() -> None:
    """_EXPANSION_LOOKUP não deve existir como módulo-level em indexing.py.

    Input:  import do módulo indexing
    Output: `hasattr(indexing, '_EXPANSION_LOOKUP')` == False

    RED:  AssertionError
    GREEN: assert passa
    """
    from corporate_instructions_mcp import indexing
    assert not hasattr(indexing, "_EXPANSION_LOOKUP"), (
        "_EXPANSION_LOOKUP ainda existe em indexing.py"
    )


def test_FAIL_S06_synonyms_yaml_not_in_package_directory() -> None:
    """synonyms.yaml bundled não deve existir dentro do pacote Python após remoção.

    Input:  filesystem — corporate_instructions_mcp/synonyms.yaml
    Output: arquivo NÃO existe

    RED:  AssertionError (arquivo ainda existe antes da remoção)
    GREEN: assert passa
    """
    from pathlib import Path
    import corporate_instructions_mcp
    package_dir = Path(corporate_instructions_mcp.__file__).parent
    bundled_synonyms = package_dir / "synonyms.yaml"
    assert not bundled_synonyms.exists(), (
        f"synonyms.yaml bundled ainda existe em {bundled_synonyms} — deve ser removido conforme ADR-002"
    )
```

### Implementação S-06

- [ ] Remover `DEFAULT_SYNONYMS` de `indexing.py`.
- [ ] Remover `_load_expansion_map_from_file()` de `indexing.py`.
- [ ] Remover `_build_expansion_lookup()` de `indexing.py`.
- [ ] Remover `QUERY_EXPANSION_MAP = ...` (módulo-level) de `indexing.py`.
- [ ] Remover `_EXPANSION_LOOKUP = ...` (módulo-level) de `indexing.py`.
- [ ] Deletar `mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`.
- [ ] Confirmar que nenhum outro arquivo Python importa `DEFAULT_SYNONYMS` ou
  `_EXPANSION_LOOKUP` diretamente.

### Critérios de aceite — S-06

- [ ] Todos os `test_FAIL_S06_*` passam.
- [ ] `pytest -q` permanece verde.

---

## S-07 — Validação de regressão e critérios da ADR-002

### Background

Verificar que:
1. Todos os testes de regressão existentes continuam passando.
2. Os 4 critérios de validação da ADR-002 (seção 5) são atendidos com o fixture corpus.
3. A expansão via corpus fixture melhora ou mantém o baseline da suíte de 24 casos.

### Testes de regressão obrigatórios — S-07

Estes testes já existem nos arquivos de teste existentes. Confirmar que CONTINUAM passando:

```
test_search_instructions_finds_dns                            (smoke_test.py)
test_resolve_instruction_context_cep_viacep_surfaces_normative_bundle
test_search_persistencia_sql_returns_data_access
```

### Testes RED — S-07 (critérios ADR-002)

```python
# === Seção: S-07 — Validação dos critérios ADR-002 ===
# Estes testes usam o servidor completo com o fixture corpus.
# Requerem que S-04 e S-05 estejam implementados (expansion_map carregado em _ensure_index).

def test_FAIL_S07_adr002_criterion1_recall_improves_for_zero_result_queries() -> None:
    """ADR-002 critério 1: recall de ao menos 3 queries previamente sem resultado melhora.

    As queries abaixo devem retornar ao menos 1 resultado relevante via expansão.
    Em estado sem expansão (antes desta implementação ou com map disabled), retornam 0
    ou resultados irrelevantes.

    Queries testadas e resultado mínimo esperado:

    Query 1: "healthcheck live ready producao"
      Resultado mínimo: "microservice-configuration-production-readiness" em selected_ids
      Justificativa: 'healthcheck' → strong: live, ready, readiness; 'producao' → via
        'transacao' ou 'logs' que têm 'production' como strong/weak.

    Query 2: "mensageria publicação assincrona"
      Resultado mínimo: "microservice-messaging-rabbitmq-publish-consume" em selected_ids
      Justificativa: 'mensageria' → strong: rabbitmq, publish, consume.

    Query 3: "resiliencia circuito e tolerancia"
      Resultado mínimo: "microservice-resilience-polly-timeouts-and-circuit-breaker" em selected_ids
      Justificativa: 'resiliencia' → strong: polly, circuit-breaker, timeout.

    Input:  server tools com fixture corpus + expansion_map ativo
    Output: para cada query, o resultado mínimo está em selected_ids

    RED:  AssertionError (sem expansão tipada, queries falham em recuperar o doc correto)
    GREEN: asserts passam
    """
    import json
    from corporate_instructions_mcp.server import resolve_instruction_context

    # Query 1: healthcheck → production-readiness
    data1 = json.loads(resolve_instruction_context(
        "healthcheck live ready producao", max_results=7
    ))
    assert "microservice-configuration-production-readiness" in data1["selected_ids"], (
        f"ADR-002 critério 1, query 1: 'microservice-configuration-production-readiness' ausente. "
        f"selected_ids={data1['selected_ids']}"
    )

    # Query 2: mensageria → rabbitmq
    data2 = json.loads(resolve_instruction_context(
        "mensageria publicacao assincrona", max_results=7
    ))
    assert "microservice-messaging-rabbitmq-publish-consume" in data2["selected_ids"], (
        f"ADR-002 critério 1, query 2: 'microservice-messaging-rabbitmq-publish-consume' ausente. "
        f"selected_ids={data2['selected_ids']}"
    )

    # Query 3: resiliencia → polly
    data3 = json.loads(resolve_instruction_context(
        "resiliencia circuito tolerancia", max_results=7
    ))
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in data3["selected_ids"], (
        f"ADR-002 critério 1, query 3: 'microservice-resilience-polly-timeouts-and-circuit-breaker' ausente. "
        f"selected_ids={data3['selected_ids']}"
    )


def test_FAIL_S07_adr002_criterion2_precision_not_degraded_single_domain() -> None:
    """ADR-002 critério 2: precisão (top-1 correto) não piora em queries de domínio único.

    Queries de domínio único (sem contexto ambíguo) devem ter seu documento principal
    como primeiro resultado, mesmo com expansão ativa.

    Query 1: "rabbitmq publish consume outbox"
      top-1 esperado: "microservice-messaging-rabbitmq-publish-consume"
      (termo rabbitmq aparece no título, tags e body — deve dominar)

    Query 2: "polly retry circuit breaker timeout"
      top-1 esperado: "microservice-resilience-polly-timeouts-and-circuit-breaker"

    Query 3: "imemorycache idistributedcache ttl invalidation"
      top-1 esperado: "microservice-caching-imemorycache-policy"

    Input:  server tools com fixture corpus + expansion_map ativo
    Output:
      query 1: results[0]["id"] == "microservice-messaging-rabbitmq-publish-consume"
      query 2: results[0]["id"] == "microservice-resilience-polly-timeouts-and-circuit-breaker"
      query 3: results[0]["id"] == "microservice-caching-imemorycache-policy"

    RED:  AssertionError se expansão introduz ruído que derruba o top-1
    GREEN: asserts passam
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    # Query 1: rabbitmq direto → deve ser top-1
    data1 = json.loads(search_instructions(
        query="rabbitmq publish consume outbox", max_results=5
    ))
    top1_id_1 = data1["results"][0]["id"]
    assert top1_id_1 == "microservice-messaging-rabbitmq-publish-consume", (
        f"ADR-002 critério 2, query 1: top-1 esperado 'microservice-messaging-rabbitmq-publish-consume', "
        f"obtido '{top1_id_1}'. Expansão pode estar introduzindo ruído."
    )

    # Query 2: polly direto
    data2 = json.loads(search_instructions(
        query="polly retry circuit breaker timeout", max_results=5
    ))
    top1_id_2 = data2["results"][0]["id"]
    assert top1_id_2 == "microservice-resilience-polly-timeouts-and-circuit-breaker", (
        f"ADR-002 critério 2, query 2: top-1 esperado 'microservice-resilience-polly-timeouts-and-circuit-breaker', "
        f"obtido '{top1_id_2}'"
    )

    # Query 3: imemorycache direto
    data3 = json.loads(search_instructions(
        query="imemorycache idistributedcache ttl invalidation", max_results=5
    ))
    top1_id_3 = data3["results"][0]["id"]
    assert top1_id_3 == "microservice-caching-imemorycache-policy", (
        f"ADR-002 critério 2, query 3: top-1 esperado 'microservice-caching-imemorycache-policy', "
        f"obtido '{top1_id_3}'"
    )


def test_FAIL_S07_adr002_criterion3_no_cross_domain_contamination() -> None:
    """ADR-002 critério 3: termos contextuais NÃO aparecem em resultados sem contexto do domínio.

    Cenário principal: 'mensageria' expande para 'rabbitmq', mas uma query sem nenhum
    termo de mensageria NÃO deve trazer 'microservice-messaging-rabbitmq-publish-consume'
    via expansão cruzada.

    Query: "polly retry circuit breaker"
      'rabbitmq' não está no lookup de 'resiliencia' → messaging doc não deve aparecer
      'dns-retry-pattern' não deve aparecer (retry isolado de dns)

    Expected top-5 NOT to contain:
      "microservice-messaging-rabbitmq-publish-consume"
      "dns-retry-pattern"

    Input:  server tools com fixture corpus + expansion_map ativo
    Output:
      "microservice-messaging-rabbitmq-publish-consume" NOT in top-5 ids
      "dns-retry-pattern" NOT in top-5 ids

    RED:  AssertionError se expansão bidirecional ainda estiver ativa
    GREEN: asserts passam (lookup unidirecional)
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(
        query="polly retry circuit breaker", max_results=7
    ))
    top5_ids = [r["id"] for r in data["results"][:5]]

    assert "microservice-messaging-rabbitmq-publish-consume" not in top5_ids, (
        f"ADR-002 critério 3: 'mensageria/rabbitmq' contaminou query de resiliência. "
        f"top-5={top5_ids}"
    )
    assert "dns-retry-pattern" not in top5_ids, (
        f"ADR-002 critério 3: 'dns-retry-pattern' apareceu em query de polly/circuit-breaker. "
        f"top-5={top5_ids} — 'retry' não deve ser strong_term de resilience nem de dns"
    )


def test_FAIL_S07_adr002_criterion4_diagnostics_reproducible() -> None:
    """ADR-002 critério 4: diagnóstico reproduz exatamente o comportamento observado.

    Executa a mesma query duas vezes; os diagnósticos devem ser idênticos (determinísticos).

    Query: "observabilidade health opentelemetry"

    Para cada execução:
      - info.diagnostics deve ter ao menos um ExpansionDiagnostic
      - diagnostics[0] da execução 1 == diagnostics[0] da execução 2
        (mesmo canonical, term, relation, weight, source_domain, source_file)

    Input:
      tokens = tokenize_query("observabilidade health opentelemetry")
      expansion_map = load_corpus_expansion_map(FIXTURES_ROOT)

    Output:
      Duas chamadas a expand_query_with_metadata(tokens, expansion_map) retornam
      diagnostics com o mesmo conteúdo.

    RED:  ImportError / AttributeError (campo diagnostics não existe)
    GREEN: asserts passam
    """
    from corporate_instructions_mcp.indexing import expand_query_with_metadata, tokenize_query
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    map1 = load_corpus_expansion_map(FIXTURES_ROOT)
    tokens = tokenize_query("observabilidade health opentelemetry")

    info1 = expand_query_with_metadata(tokens, expansion_map=map1)
    info2 = expand_query_with_metadata(tokens, expansion_map=map1)

    assert len(info1.diagnostics) > 0, "Nenhum diagnóstico gerado — mapa pode estar disabled"
    assert len(info1.diagnostics) == len(info2.diagnostics), (
        f"Diagnósticos não-determinísticos: run1={len(info1.diagnostics)}, run2={len(info2.diagnostics)}"
    )

    for i, (d1, d2) in enumerate(zip(info1.diagnostics, info2.diagnostics)):
        assert d1.canonical == d2.canonical, f"diagnostic[{i}].canonical diferente"
        assert d1.term == d2.term, f"diagnostic[{i}].term diferente"
        assert d1.relation == d2.relation, f"diagnostic[{i}].relation diferente"
        assert d1.weight == pytest.approx(d2.weight), f"diagnostic[{i}].weight diferente"
        assert d1.source_domain == d2.source_domain, f"diagnostic[{i}].source_domain diferente"
        assert d1.source_file == d2.source_file, f"diagnostic[{i}].source_file diferente"


def test_REGRESSION_S07_dns_query_still_finds_dns_retry_pattern() -> None:
    """REGRESSÃO: query de DNS ainda deve encontrar dns-retry-pattern como top-1.

    Este teste DEVE SEMPRE PASSAR (não é RED/GREEN — é invariante de regressão).

    Input:
      query = "retry DNS polly"
      max_results = 3

    Output esperado:
      results[0]["id"] == "dns-retry-pattern"

    Justificativa: dns-retry-pattern permanece findable via tokens diretos de DNS
    (não via expansão cruzada de resiliência).
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"][0]["id"] == "dns-retry-pattern", (
        f"REGRESSÃO: 'dns-retry-pattern' deixou de ser top-1 para query 'retry DNS polly'. "
        f"results={[r['id'] for r in data['results']]}"
    )


def test_REGRESSION_S07_cep_viacep_bundle_intact() -> None:
    """REGRESSÃO: bundle de CEP/ViaCEP continua funcionando após as mudanças.

    Input:
      context query = "buscar endereço por CEP usando ViaCEP com retry e cache"
      max_results = 7

    Output esperado:
      selected_ids contém ao menos 3 dos seguintes:
        "microservice-integration-httpclientfactory-contracts"
        "microservice-resilience-polly-timeouts-and-circuit-breaker"
        "microservice-caching-imemorycache-policy"
        "microservice-api-validation-and-error-contracts"
    """
    import json
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(
        "buscar endereco por CEP usando ViaCEP com retry e cache",
        max_results=7,
    ))
    expected = {
        "microservice-integration-httpclientfactory-contracts",
        "microservice-resilience-polly-timeouts-and-circuit-breaker",
        "microservice-caching-imemorycache-policy",
        "microservice-api-validation-and-error-contracts",
    }
    found = expected & set(data["selected_ids"])
    assert len(found) >= 3, (
        f"REGRESSÃO: bundle CEP/ViaCEP incompleto. "
        f"Encontrados: {found}. "
        f"selected_ids={data['selected_ids']}"
    )


def test_REGRESSION_S07_persistencia_sql_returns_data_access() -> None:
    """REGRESSÃO: query de persistência SQL retorna data-access doc.

    Input:
      query = "persistencia sql dapper repositorio"
      max_results = 5

    Output esperado:
      results[0]["id"] == "microservice-data-access-and-sql-security"
    """
    import json
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(
        query="persistencia sql dapper repositorio", max_results=5
    ))
    assert data["results"][0]["id"] == "microservice-data-access-and-sql-security", (
        f"REGRESSÃO: top-1 para query de persistência SQL mudou. "
        f"results={[r['id'] for r in data['results']]}"
    )
```

### Implementação S-07

- [ ] Verificar que `_ensure_index()` em `server.py` carrega o `ExpansionMap` via
  `load_corpus_expansion_map(INSTRUCTIONS_ROOT)` e passa para `expand_query_with_metadata()`.
- [ ] Verificar que o cache de índice (`_cached_index`) inclui o `ExpansionMap` no tuple
  (ou invalida o cache quando o mapa muda).
- [ ] Executar `pytest -q` completo; registrar resultado.
- [ ] Executar suíte de 24 casos via MCP stdio; registrar placar.

### Critérios de aceite — S-07

- [ ] `test_FAIL_S07_adr002_criterion1_*` passa.
- [ ] `test_FAIL_S07_adr002_criterion2_*` passa.
- [ ] `test_FAIL_S07_adr002_criterion3_*` passa.
- [ ] `test_FAIL_S07_adr002_criterion4_*` passa.
- [ ] Todos os `test_REGRESSION_S07_*` passam.
- [ ] `pytest -q` completo: zero regressões.
- [ ] Suíte de 24 casos: placar ≥ 8/24 (baseline pós-EPIC-09 mantido ou melhorado).

---

## Critérios de aceite do épico

- [ ] Módulo `expansion.py` criado com todos os tipos, constantes e funções especificados.
- [ ] `DEFAULT_SYNONYMS` removido de `indexing.py` (sem fallback silencioso).
- [ ] `synonyms.yaml` bundled removido do pacote.
- [ ] `expand_query_with_metadata()` usa lookup unidirecional ponderado.
- [ ] Expansão desabilitada quando mapa ausente/inválido (sem exceção, sem fallback).
- [ ] 12 arquivos YAML de domínio criados em `fixtures/instructions/metadata/corpus-query-expansion-map/`.
- [ ] Todos os testes `test_FAIL_*` falham em estado RED e passam em estado GREEN.
- [ ] Todos os testes `test_REGRESSION_*` passam do início ao fim (nunca regridem).
- [ ] `pytest -q` verde com zero falhas ao final de todas as fases.
- [ ] Suíte de 24 casos: placar ≥ 8/24 (mantido ou melhorado).
- [ ] Para cada sub-issue: evidência explícita de RED (falha antes) e GREEN (passa após).

---

## Fora de escopo deste épico

- Reescrita do algoritmo de scoring.
- BM25 ou busca vetorial.
- Expansão transitiva (multi-hop).
- Context-based scoring por path de documento (ContextRule parseado mas não aplicado).
- Global/local merge de mapas.
- Alterações em contratos de tools (`search_instructions`, `resolve_instruction_context`, etc.).
- Atualização do corpus real de produção.

---

## Referências

- ADR-002: `planning/adr/ADR-002-corpus-query-expansion-map.md`
- EPIC-07: `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
- EPIC-09: `planning/bmad/epicos/EPIC-09-i04-observability-readiness-cross-domain-coverage.md`
- Análise do dicionário de sinônimos: `research/nucleo-pesquisa/analise-tools/analise-dicionario-sinonimos.md`
- Código atual: `mcp-instructions-server/corporate_instructions_mcp/indexing.py`
- Corpus de fixture: `fixtures/instructions/`
