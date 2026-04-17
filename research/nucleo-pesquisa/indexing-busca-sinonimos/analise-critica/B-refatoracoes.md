# B — Lista de refatorações concretas

Lista detalhada e priorizada das refatorações sobre [`indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) e, quando necessário, sobre o consumidor [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py).

Cada item declara: **objetivo**, **impacto**, **esforço relativo**, **pontos de código**, **dependências** e **teste associado**. Nenhum código é aplicado aqui — este documento é o plano.

Convenções:
- **Esforço**: S (≤ 0.5 dia), M (1–2 dias), L (> 2 dias).
- **Impacto**: correção | governança | qualidade-de-ranking | explicabilidade | observabilidade.
- **Fase**: 1 (inegociável), 2 (estatístico/domínios), 3 (semântico opcional).

---

## Fase 1 — Correção e desacoplamento

### R-1. Substituir `blob.count(t)` por casamento com fronteira de palavra

- **Fase:** 1. **Esforço:** S. **Impacto:** correção.
- **Objetivo:** eliminar falsos positivos de substring (ex.: "get" casando "getter", "target").
- **Pontos de código:** [`score_record`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) linha 211 (`c = blob.count(t)`).
- **Alteração:** pré-compilar `re.compile(rf"\b{re.escape(t)}\b")`, cachear em módulo por termo expandido. Substituir `blob.count(t)` por `len(pattern.findall(blob))`.
- **Atenção:** preservar case-insensitive via lowercasing do blob (já é feito em `search_blob`).
- **Dependências:** nenhuma.
- **Teste associado:** `test_word_boundary_avoids_substring_false_positive` — documento com `body="The getter pattern..."` e query `"get"` não deve ativar contribuição `blob.count`-equivalente após a refatoração.
- **Risco de regressão:** casos onde o corpus atual dependia do substring em termos como `"get" in "getter"`. Cobrir via golden queries (**R-10**) antes de mergear.

### R-2. Normalização simétrica (NFKD + lowercase) entre query e blob

- **Fase:** 1. **Esforço:** S. **Impacto:** correção.
- **Objetivo:** eliminar a assimetria observada em §2 (L-4): query sem acento não casa diretamente corpo com acento pelo `blob.count`.
- **Pontos de código:** `tokenize_query` (linha 151), `_normalize_token` (linha 171), `search_blob` (linha 41), `score_record` (linhas 207–218).
- **Alteração:**
  - Criar `_normalize_text(text: str) -> str` aplicando NFKD + strip de diacríticos + lowercase (generalização de `_normalize_token`).
  - `search_blob` passa a devolver texto normalizado; ou `score_record` normaliza explicitamente.
  - Tokens da query são normalizados antes do casamento (já são lowercased; falta remover diacríticos).
- **Dependências:** **R-1** (para aplicar junto).
- **Teste associado:** `test_accent_normalization_symmetric` — documento com `body="persistência em SQL"`, query `"persistencia"` casa diretamente no blob (score direto, não apenas via sinónimo).

### R-3. Tag matching por igualdade normalizada

- **Fase:** 1. **Esforço:** S. **Impacto:** correção.
- **Objetivo:** remover `t in tag` que faz substring em tags (ex.: `"test" in "latest"`).
- **Pontos de código:** `score_record` linhas 216–218.
- **Alteração:**
  ```
  tags_n = {_normalize_text(tag).replace("_", "-") for tag in rec.tags}
  for term, weight in terms.items():
      if _normalize_text(term).replace("_", "-") in tags_n:
          score += weight * 2.0
  ```
  (Normalização de hífen/underscore evita falsos negativos em tags como `data_access` vs `data-access`.)
- **Dependências:** nenhuma.
- **Teste associado:** `test_tag_match_is_exact_not_substring` — documento com tag `"latest"` + query `"test"` não ganha boost de tag.

### R-4. Title matching com fronteira de palavra

- **Fase:** 1. **Esforço:** S. **Impacto:** correção.
- **Objetivo:** `t in title_l` (linha 214) sofre o mesmo problema de substring do corpo, com peso mais alto (×3).
- **Alteração:** usar `pattern.search(title_n)` (pattern já cacheado em **R-1**).
- **Dependências:** **R-1**, **R-2**.
- **Teste associado:** parte do `test_word_boundary_avoids_substring_false_positive`.

### R-5. Extrair `SYNONYMS` para `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`

- **Fase:** 1. **Esforço:** M. **Impacto:** governança.
- **Objetivo:** desacoplar vocabulário do código. Permitir PR editorial separado, revisão de domínio por equipa.
- **Pontos de código:** `SYNONYMS` (linhas 157–168), `_build_synonym_lookup` (linha 177), `_SYNONYM_LOOKUP` (linha 190).
- **Alteração:**
  - Novo ficheiro `corporate_instructions_mcp/vocabulary.py` com classes `YamlVocabularyProvider`, `StaticVocabularyProvider` (fallback) implementando `VocabularyProvider` (ver [`C-interfaces.md`](C-interfaces.md)).
  - `build_index` aceita parâmetro opcional `vocabulary_provider`; se ausente, tenta `root / "_vocabulary" / "global.yaml"`, senão cai no `StaticVocabularyProvider` com warning `log.warning("fallback_static_vocabulary reason=yaml_missing")`.
  - Schema valida: `version`, `groups[].canonical`, `groups[].aliases`, `metadata.domain`. Rejeita se exceder 200 grupos × 30 aliases.
- **Dependências:** **R-9** (interfaces).
- **Teste associado:**
  - `test_yaml_vocabulary_loads_groups`.
  - `test_yaml_vocabulary_rejects_over_limit`.
  - `test_falls_back_to_static_when_yaml_missing` (com monkeypatch).

### R-6. `QueryExpansionProvider` injetado

- **Fase:** 1. **Esforço:** M. **Impacto:** governança + explicabilidade.
- **Objetivo:** expansão deixa de ser função livre, passa a objeto com estado (vocabulários carregados) e contrato explícito.
- **Pontos de código:** `expand_query_with_synonyms` (linhas 193–201).
- **Alteração:**
  - Função livre permanece, implementada em cima de um `DictQueryExpansionProvider` default. Consumidor (`server.py`) cria o provider no `_ensure_index` e passa ao ranker.
  - Resultado passa a ser `ExpansionResult` em vez de `dict[str, float]`: inclui origem de cada termo (provenance) para explicabilidade.
- **Dependências:** **R-5**, **R-9**.
- **Teste associado:** `test_expansion_provider_preserves_existing_behavior` (paridade com versão funcional atual quando vocabulário é o antigo).

### R-7. Parametrizar e logar truncamento de sinónimos

- **Fase:** 1. **Esforço:** S. **Impacto:** observabilidade.
- **Objetivo:** eliminar o `[:5]` cego (§1.4, observação 2 e 4).
- **Pontos de código:** linha 199.
- **Alteração:**
  - Novo parâmetro `max_related_per_token: int = 8` configurável no provider.
  - Quando `len(related) > max_related_per_token`, emitir `log.debug("synonym_truncated token=%s kept=%s dropped=%s", ...)`.
  - Preservar ordenação estável, mas mudar de alfabética para: primeiro aliases do mesmo grupo, depois cross-group (quando houver).
- **Dependências:** **R-6**.
- **Teste associado:** `test_synonym_truncation_is_logged` com `caplog`; `test_default_related_limit_is_eight`.

### R-8. Suportar `aliases:` no frontmatter

- **Fase:** 1. **Esforço:** M. **Impacto:** governança + qualidade-de-ranking.
- **Objetivo:** mover curadoria lexical para o **autor do documento**, democratizando a evolução do vocabulário e evitando vazamento entre domínios.
- **Pontos de código:** `InstructionRecord` (linhas 26–42), `_parse_markdown` (linhas 50–100), `build_index` (linhas 103–148).
- **Alteração:**
  - `InstructionRecord` ganha `aliases: list[str] = field(default_factory=list)`.
  - `_parse_markdown` extrai `meta.get("aliases") or []`, normaliza para lista de strings lowercased + NFKD.
  - `search_blob` passa a incluir os aliases: `f"{title}\n{' '.join(tags + aliases)}\n{body}"` — estes matches contam como match direto **apenas para o doc que os declara**, não expandem globalmente.
  - Peso no ranker: match em alias contribui com boost ×2 (como tag exata), evitando inflação.
- **Dependências:** **R-3** (normalização de tag serve também para aliases).
- **Teste associado:**
  - `test_frontmatter_aliases_are_indexed_per_doc`.
  - `test_aliases_do_not_leak_across_docs` — alias declarado no doc A não melhora score do doc B.

### R-9. `Protocol`s: `QueryExpansionProvider`, `LexicalRanker`, `VocabularyProvider`

- **Fase:** 1. **Esforço:** S (só definição; implementações concretas = 0 custo extra, são wrappers do existente). **Impacto:** governança + qualidade-de-ranking.
- **Objetivo:** criar contratos para as substituições de Fase 2 e 3 serem drop-in.
- **Pontos de código:** novo módulo `corporate_instructions_mcp/ranking.py`.
- **Alteração:** ver definição em [`C-interfaces.md`](C-interfaces.md).
- **Dependências:** nenhuma.
- **Teste associado:** `test_protocols_are_runtime_checkable` (usa `typing.runtime_checkable`).

### R-10. Golden queries

- **Fase:** 1. **Esforço:** M. **Impacto:** qualidade-de-ranking.
- **Objetivo:** proteger contra regressão em queries conhecidas durante qualquer refatoração do ranker.
- **Pontos de código:** novo `tests/search_goldens.yaml` + `tests/test_search_goldens.py`.
- **Conteúdo mínimo (usando fixture atual):**
  ```yaml
  # tests/search_goldens.yaml
  version: 1
  cases:
    - id: dns-retry
      query: "dns retry"
      expected_top_ids:
        - dns-retry-pattern
    - id: persistencia-sql
      query: "persistência SQL"
      expected_top_ids:
        - microservice-data-access-and-sql-security
    - id: rabbitmq-publish
      query: "rabbitmq publish"
      expected_top_ids:
        - microservice-messaging-rabbitmq-publish-consume
    - id: clean-architecture
      query: "clean architecture guardrails"
      expected_top_ids:
        - microservice-clean-architecture-guardrails
        - microservice-architecture-layering
    - id: polly-resilience
      query: "polly retry circuit breaker"
      expected_top_ids:
        - microservice-resilience-polly-timeouts-and-circuit-breaker
    - id: jwt-auth
      query: "jwt bearer authorization"
      expected_top_ids:
        - microservice-auth-jwt-bearer-and-authorization
    - id: openfinance
      query: "open finance patterns"
      expected_top_ids:
        - microservice-api-openfinance-patterns
    - id: pt-en-mapping
      query: "mensageria consumo"
      expected_top_ids:
        - microservice-messaging-rabbitmq-publish-consume
    - id: empty-no-match
      query: "xyznonexistentterm"
      expected_top_ids: []
  ```
- **Teste associado:** `test_golden_queries` parametrizado — para cada caso, falha se `expected_top_ids` não estão contidos nos primeiros `len(expected_top_ids) + 2` resultados.
- **Política:** mudanças no YAML exigem nota de justificativa no PR.

---

## Fase 2 — Ranking estatístico e partição por domínio

### R-11. Índice invertido

- **Fase:** 2. **Esforço:** M. **Impacto:** qualidade-de-ranking.
- **Objetivo:** viabilizar BM25 com custo linear na query, não no corpus, e permitir estatísticas (`df`, `avgdl`).
- **Pontos de código:** `build_index` (linhas 103–148).
- **Alteração:** devolver `IndexBundle` em vez de `dict[str, InstructionRecord]` (ver [`A-design-alvo.md`](A-design-alvo.md)).
- **Retrocompat:** adaptar `server.py` (`_index: IndexBundle | None`) mantendo ID-lookup em `bundle.records`.

### R-12. `BM25Ranker` implementando `LexicalRanker`

- **Fase:** 2. **Esforço:** M. **Impacto:** qualidade-de-ranking.
- **Objetivo:** substituir heurística aditiva por fórmula com fundamento.
- **Alteração:**
  - BM25-F com pesos por campo (`title=3.0`, `tags=2.0`, `body=1.0` como ponto de partida; calibráveis por golden queries).
  - `k1=1.2`, `b=0.75` defaults.
  - Selecionável por variável `INSTRUCTIONS_RANKER=bm25 | word-boundary`. Default na introdução: `word-boundary`; depois de validado por goldens em corpus real: `bm25`.
- **Dependências:** **R-11**.
- **Teste associado:** `test_bm25_prefers_denser_shorter_doc` (documento curto com alta densidade do termo deve ranquear acima de documento longo com muitas ocorrências mas baixa densidade).

### R-13. `DomainVocabularyProvider` com ativação condicional

- **Fase:** 2. **Esforço:** M. **Impacto:** governança.
- **Objetivo:** resolver estruturalmente o FIX ≠ RabbitMQ.
- **Alteração:** `DomainVocabularyProvider` lê todos os `_vocabulary/<d>.yaml` com `metadata.domain != null`. Calcula `ctx.domains` a partir de:
  1. `tag_filter` interseção com `metadata.activation_tags` de cada domínio.
  2. Tokens da query aparecendo como `canonical` em algum vocabulário de domínio.
- **Dependências:** **R-5**, **R-6**.
- **Teste associado:** `test_domain_vocab_does_not_leak_across_domains` (criar dois vocabulários `messaging-rabbitmq.yaml` e `messaging-fix.yaml`; query `rabbitmq` não traz documentos FIX; query `fix` não traz documentos RabbitMQ).

### R-14. Modo `explain`

- **Fase:** 2. **Esforço:** S. **Impacto:** explicabilidade + observabilidade.
- **Objetivo:** expor a decomposição do score.
- **Alteração:**
  - `LexicalRanker.score` devolve `ScoreTrace` opcionalmente.
  - `search_instructions` aceita `debug: bool = False`; se `True`, inclui campo `explain` no JSON (ver [`A-design-alvo.md`](A-design-alvo.md) §"Contrato de saída").
- **Dependências:** **R-12**.
- **Teste associado:** `test_explain_trace_shape`.

---

## Fase 3 — Opcional, medida

### R-15. `SemanticReranker` como pós-processamento

- **Fase:** 3. **Esforço:** L. **Impacto:** qualidade-de-ranking (recall semântico).
- **Gatilho:** >20% das queries reais sem match satisfatório no top-5 após Fases 1+2, e não endereçáveis via `aliases` em tempo razoável.
- **Alteração:**
  - `SemanticReranker` opera sobre top-N (N=30) da BM25.
  - Embeddings locais (ex.: `fastembed` com `multilingual-e5-small`, ~90 MB).
  - Flag `enable_semantic_rerank` default **off**; quando off, paridade perfeita com Fase 2.
  - Cache de embeddings de documentos invalidado por `content_hash`.
- **Teste associado:**
  - `test_semantic_rerank_disabled_by_default` (paridade com BM25).
  - `test_semantic_rerank_only_reorders_top_n` (não introduz documentos novos além dos já candidatos).

---

## Sequência recomendada de merges

Cada linha é um PR independente com teste próprio:

1. **PR-1** (F1): R-9 (`Protocol`s, sem consumo ainda) + testes de forma.
2. **PR-2** (F1): R-1, R-2, R-4 (correção lexical; goldens inicialmente via vocabulário atual).
3. **PR-3** (F1): R-3 (tag igualdade normalizada).
4. **PR-4** (F1): R-10 (goldens), **bloqueia merges futuros sem atualizar YAML**.
5. **PR-5** (F1): R-5 + R-6 + R-7 (YAML externo, provider injetado, limite parametrizado). Fallback garante compatibilidade.
6. **PR-6** (F1): R-8 (`aliases:` no frontmatter). Migrar fixtures seletivamente para demonstrar uso (ex.: RabbitMQ doc ganha `aliases: [amqp, broker, iconnection]`).
7. Gate de métrica — executar goldens em corpus real; decidir entrar em Fase 2.
8. **PR-7** (F2): R-11 + R-12 com flag `INSTRUCTIONS_RANKER`.
9. **PR-8** (F2): R-13.
10. **PR-9** (F2): R-14.
11. Gate de métrica — decidir Fase 3.
12. **PR-10** (F3): R-15, atrás de flag off-by-default.

## O que **explicitamente não é refatoração** agora

- Substituir `yaml.safe_load` por outro loader.
- Introduzir cache de disco para o índice (invalidation via hash é suficiente para o corpus atual).
- Mudar `rglob("*.md")` por `watchdog` / notificação de filesystem.
- Tornar `build_index` assíncrono.
- Expor APIs REST/HTTP (fora do âmbito desta análise; ver [`docs/ROADMAP-TRANSPORT-HTTP.md`](../../../../mcp-instructions-server/docs/ROADMAP-TRANSPORT-HTTP.md)).
