# EPIC-07 — Qualidade de ranking de busca e integridade do corpus

## Objetivo

Corrigir as causas raiz de baixa precisão na recuperação de instrução por `resolve_instruction_context` e `search_instructions`, identificadas em auditoria técnica realizada em 2026-05-04 após execução da suíte de 24 testes de montagem de contexto com corpus `fixtures/instructions`.

**Resultado**: suíte de 24 testes aprovada com ≥ 21/24, sem regressão em nenhum teste existente.

## Contexto do problema

A auditoria original da suíte `testes-basicos-montagem-contexto-mcp.md` registrou baseline de **5/24 aprovados**. Uma reexecução real via MCP `stdio`, no mesmo dia e com o estado atual do workspace/fixture, registrou **7/24 aprovados**.

As duas leituras convergem em um ponto: a suíte continua muito abaixo do critério de aceitação e o problema principal permanece sendo de **qualidade de ranking/seleção**, não de disponibilidade do servidor MCP.

A auditoria técnica identificou 7 problemas, classificados em três grupos:

1. **Mecanismo de scoring** (P1, P2): stopwords portuguesas ausentes inflacionam scores de documentos irrelevantes via conectivos de alta frequência.
2. **Dicionário de sinônimos** (P4, P5, P7): lacunas e caminhos de expansão cruzada introduzem documentos fora do tema.
3. **Integridade de dados do corpus** (P3): ID declarado no frontmatter diverge do nome do arquivo em uma fixture.

Após a reexecução real, `I-01` e `I-02` continuam fortemente sustentadas; `I-04` permanece parcialmente sustentada; `I-03`, `I-06` e `I-07` devem ser **revalidadas** contra o estado atual da fixture antes de qualquer implementação.

## Princípio de implementação

> **Toda mudança deve ser estritamente aditiva ou conservadora.**
> Nenhum teste existente (smoke, context_triggers, epic05, integration) deve regredir.
> Cada issue tem: teste de falha que reproduz o bug **antes** da correção, e teste de comportamento esperado **após** a correção.

---

## Issues e classificação

| ID | Problema | Categoria | Severidade | Status auditoria |
|---|---|---|---|---|
| I-01 | Stopwords PT ausentes: `como`, `deve`, `ser`, `que`, `me`, `quando`, `qual` inflacionam qualquer query natural PT | Implementação | **Crítica** | Confirmado no código e reforçado na reexecução |
| I-02 | `bmad` e `instruction-authoring-standard` aparecem sistematicamente no top de queries técnicas por scope global + priority alto + efeito I-01 | Design | **Crítica** | Confirmado no código e reforçado na reexecução |
| I-03 | `example-security-baseline.md` declara `id: security-baseline-secrets` no frontmatter — ID esperado não existe no índice | Integridade de dados | **Crítica** | Revalidar no estado atual da fixture |
| I-04 | `configuration-production-readiness` suprimido em queries de observabilidade, health checks e SQL — ausência de sinônimos cruzados | Design (sinônimos) | **Alta** | Parcialmente confirmado; escopo atual mais estreito |
| I-05 | `dns-retry-pattern` aparece em queries de resiliência HTTP/Polly via expansão bidirecional `resiliencia→retry←dns` | Implementação (sinônimos) | **Média** | Confirmado no código; não reproduzido na reexecução |
| I-06 | Queries compostas multi-tema não garantem representação de todos os domínios no top-5 — pool dominado por I-01 | Implementação (seleção) | **Alta** | Revalidar após nova rodada; T24 atual passou |
| I-07 | `api-openfinance-patterns` ausente em queries de paginação/coleções — `paginacao`/`colecoes` sem caminho de expansão | Design (sinônimos) | **Média** | Revalidar no estado atual da fixture |

---

## Artefatos principais

### Código do servidor MCP
- `mcp-instructions-server/corporate_instructions_mcp/indexing.py` — `STOPWORDS`, `DEFAULT_SYNONYMS`, `score_record_breakdown`
- `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py` — `build_resolved_context`
- `mcp-instructions-server/tests/smoke_test.py` — testes de regressão existentes

### Corpus / fixtures
- `fixtures/instructions/example-security-baseline.md` — revalidar se ainda existe divergência entre slug do arquivo e `id` do frontmatter
- `fixtures/instructions/assistant-workflow-bmad-planning-and-controlled-inference.md` — scope global
- `fixtures/instructions/instruction-authoring-standard.md` — scope quase global

### Especificação de testes
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md` — suíte de 24 testes

---

## Roadmap sequencial

As issues são independentes entre si, mas I-01 deve ser corrigida **antes** de I-02 e I-06, pois é a causa raiz que amplifica ambas.

### Fase 0 — Baseline e invariante de não-regressão

Antes de qualquer mudança:

- [ ] Executar `pytest -q` no servidor (todos os testes existentes verdes).
- [ ] Registrar explicitamente os dois baselines conhecidos da suíte de 24 testes:
  - auditoria inicial: `5/24`
  - reexecução real via MCP `stdio` em 2026-05-04: `7/24`
- [ ] Fixar o registro de IDs conhecidos do índice (fixture: 27 documentos, lista conhecida).
- [ ] Revalidar `I-03`, `I-06` e `I-07` contra o estado atual da fixture antes de implementar correções específicas desses itens.

---

### I-01 — Stopwords portuguesas ausentes

**Background:** `indexing.py` linha 33-65 define `STOPWORDS` com conectivos ingleses mas omite os portugueses equivalentes. `como`, `deve`, `ser`, `que`, `me`, `quando`, `qual`, `quais` pontuam em todos os documentos do corpus via body score, tornando o ranking não-discriminativo para queries em português natural.

**Evidência direta:**
```
query "me mostre como o projeto deve ser estruturado" → matched_user_terms por documento:
  assistant-workflow-bmad  → ['como', 'deve', 'ser']         → score 9.8
  rabbitmq                 → ['como', 'deve', 'projeto', 'ser'] → score 9.7
  architecture-layering    → ['como', 'deve', 'projeto', 'ser'] → score 8.7
```
O ranking é determinado por quantidade de conectivos no body, não por relevância temática.

**Entregas (aditivas — apenas ampliação do conjunto existente):**

- [ ] Adicionar ao `STOPWORDS` em `indexing.py`: `como`, `deve`, `ser`, `que`, `me`, `mostre`, `quando`, `qual`, `quais`, `fazer`, `usar`, `implementar`, `configurar`, `retornar`, `tratar`.
- [ ] Verificar que nenhum desses tokens é chave de sinônimo ou usado em lógica de negócio fora de scoring.
- [ ] Executar todos os testes existentes e confirmar zero regressões.

**Critério de aceite:**
- `como`, `deve`, `ser`, `que`, `me`, `quando`, `qual` presentes em `STOPWORDS`.
- `score_record_breakdown` para `microservice-messaging-rabbitmq-publish-consume` com query `"como deve ser"` retorna `score_body_blob == 0.0`.
- Todos os testes existentes continuam verdes.

**Novos testes obrigatórios:**

```python
# FALHA (reproduz o bug — deve falhar ANTES da correção):
def test_FAIL_stopwords_pt_missing_como_deve_ser():
    from corporate_instructions_mcp.indexing import STOPWORDS
    missing = [w for w in ["como", "deve", "ser", "que", "me", "quando", "qual", "quais"] if w not in STOPWORDS]
    assert missing == [], f"Stopwords PT ausentes: {missing}"

def test_FAIL_common_pt_words_score_nonzero_in_unrelated_doc():
    """'como deve ser' não deve gerar body score em documento de mensageria."""
    from corporate_instructions_mcp.indexing import tokenize_query, expand_query_with_metadata, score_record_breakdown
    from corporate_instructions_mcp.server import _ensure_index
    idx, _ = _ensure_index()
    tokens = tokenize_query("como deve ser")
    info = expand_query_with_metadata(tokens)
    bd = score_record_breakdown(idx["microservice-messaging-rabbitmq-publish-consume"], tokens, None, info)
    assert bd.score_body_blob == 0.0

# COMPORTAMENTO ESPERADO (deve passar APÓS a correção):
def test_EXPECT_stopwords_pt_filter_connectives():
    from corporate_instructions_mcp.indexing import STOPWORDS
    for word in ["como", "deve", "ser", "que", "me", "quando", "qual", "quais"]:
        assert word in STOPWORDS, f"'{word}' deve estar em STOPWORDS"
```

---

### I-02 — `bmad` e `instruction-authoring-standard` como ruído sistêmico

**Background:** `assistant-workflow-bmad-planning-and-controlled-inference` tem `scope:"**/*"` e `priority:high`. `instruction-authoring-standard` tem `scope:"**/*.md"` e `priority:medium`. Combinado com I-01, qualquer query PT gera hits via conectivos em seus bodies longos, colocando-os no top de queries de arquitetura, segurança e integração. São documentos de meta-governance do corpus — não são instruções técnicas de domínio.

**Dependência:** I-01 deve ser corrigida primeiro. Após I-01, avaliar se ainda há contaminação residual e agir conforme abaixo.

**Opções de correção (escolher após medir impacto pós-I-01):**

- [ ] **Opção A**: restringir `scope` do `bmad` para `"**/*.md"` (alinhado com sua natureza de instrução de workflow, não de artefato técnico).
- [ ] **Opção B**: adicionar tag `meta-governance` e filtrar documentos com essa tag do pool de busca técnica (requer mudança em `search_instructions`).
- [ ] **Opção C**: introduzir campo `exclude_from_search: true` no frontmatter para documentos de meta-governance, respeitado pelo indexador.

A opção escolhida deve ser documentada no frontmatter dos arquivos afetados como `last_reviewed` atualizado.

**Critério de aceite:**
- `resolve_instruction_context("como o projeto deve ser estruturado", max_results=7)` não retorna `assistant-workflow-bmad-planning-and-controlled-inference` nem `instruction-authoring-standard` entre os 3 primeiros.
- Todos os testes existentes continuam verdes (incluindo `test_list_instructions_index_count` que verifica contagem ≥ 3).

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção):
def test_FAIL_architecture_query_bmad_not_in_top3():
    from corporate_instructions_mcp.server import search_instructions
    data = json.loads(search_instructions(query="como o projeto deve ser estruturado", max_results=7))
    top3 = [r["id"] for r in data["results"][:3]]
    assert "assistant-workflow-bmad-planning-and-controlled-inference" not in top3, \
        f"bmad no top-3 de query de arquitetura: {top3}"

def test_FAIL_resolve_context_architecture_excludes_meta_governance():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("como separar Api, Dominio, Interfaces e Repositorio", max_results=7))
    found = {"assistant-workflow-bmad-planning-and-controlled-inference", "instruction-authoring-standard"} & set(data["selected_ids"])
    assert not found, f"Meta-governance em query de arquitetura: {found}"

# COMPORTAMENTO ESPERADO (após a correção):
def test_EXPECT_architecture_query_top3_are_architecture_docs():
    from corporate_instructions_mcp.server import search_instructions
    data = json.loads(search_instructions(query="como o projeto deve ser estruturado", max_results=7))
    top3 = [r["id"] for r in data["results"][:3]]
    arch_ids = {"microservice-architecture-layering", "microservice-clean-architecture-guardrails", "microservice-domain-interfaces-models-repository"}
    assert len(arch_ids & set(top3)) >= 2, f"Menos de 2 IDs de arquitetura no top-3: {top3}"
```

---

### I-03 — ID mismatch no frontmatter do fixture `example-security-baseline.md`

**Background:** Na auditoria original, o arquivo `fixtures/instructions/example-security-baseline.md` declarava no frontmatter `id: security-baseline-secrets`. O indexador usa o campo `id` do frontmatter como chave do índice (`indexing.py` linha 255). Logo, o ID `example-security-baseline` não existiria no índice e `get_instructions_batch(ids="example-security-baseline")` retornaria `found_count: 0`.

**Revalidação 2026-05-04:** a reexecução real da suíte retornou `example-security-baseline` normalmente em `selected_ids` e no `get_instructions_batch`. Portanto, este item não deve ser implementado sem revalidar primeiro o estado atual da fixture e dos testes de smoke.

**Nota:** `security-baseline-secrets` foi o ID real observado na auditoria original. O estado atual do workspace pode já ter divergido desse baseline.

**Entregas (somente se a revalidação reproduzir o problema):**

- [ ] Corrigir frontmatter de `fixtures/instructions/example-security-baseline.md`: alterar `id: security-baseline-secrets` para `id: example-security-baseline`.
- [ ] Atualizar `title` se necessário para refletir o tema de baseline geral de segurança (não apenas segredos).
- [ ] Verificar se algum teste existente usa `security-baseline-secrets` como ID direto e atualizar para `example-security-baseline` se a semântica for a mesma. Se forem documentos conceitualmente distintos, criar dois arquivos separados.
- [ ] Adicionar teste de invariante de corpus (filename slug == frontmatter id) para prevenir regressão futura.

**Critério de aceite:**
- `get_instructions_batch(ids="example-security-baseline")` retorna `found_count: 1`.
- `get_instructions_batch(ids="security-baseline-secrets")` retorna `found_count: 0` (ou 1 se o documento for separado).
- Teste de invariante de corpus passa.

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção):
def test_FAIL_example_security_baseline_id_matches_filename():
    from corporate_instructions_mcp.server import _ensure_index
    idx, _ = _ensure_index()
    assert "example-security-baseline" in idx, \
        "ID 'example-security-baseline' não existe no índice — frontmatter declara id diferente do nome do arquivo"

# COMPORTAMENTO ESPERADO (após a correção):
def test_EXPECT_example_security_baseline_retrievable():
    from corporate_instructions_mcp.server import get_instructions_batch
    data = json.loads(get_instructions_batch(ids="example-security-baseline"))
    assert data["found_count"] == 1
    assert data["instructions"][0]["id"] == "example-security-baseline"

# INVARIANTE DE CORPUS (novo — deve sempre passar após a correção):
def test_INVARIANT_corpus_filename_ids_match_frontmatter_ids():
    """Para todo arquivo do corpus, o id do frontmatter deve coincidir com o slug do nome do arquivo."""
    from pathlib import Path
    from corporate_instructions_mcp.server import _ensure_index
    from corporate_instructions_mcp.indexing import _slug_from_path
    idx, _ = _ensure_index()
    mismatches = [
        f"arquivo={rec.rel_path}  id_frontmatter={rec_id}  slug_esperado={_slug_from_path(Path(rec.rel_path))}"
        for rec_id, rec in idx.items()
        if rec_id != _slug_from_path(Path(rec.rel_path))
    ]
    assert not mismatches, "Frontmatter id diverge do nome de arquivo:\n" + "\n".join(mismatches)
```

---

### I-04 — `configuration-production-readiness` suprimido em queries de observabilidade e health

**Background:** Nenhum sinônimo conecta os tokens de query de T05/T07 (`observabilidade`, `health`, `live`, `ready`) ao documento `microservice-configuration-production-readiness` (tags: `[configuration, options, feature-flags, production, deployment]`). Adicionalmente, o documento tem `priority:medium` enquanto concorrentes com `priority:high` e muitos hits em I-01 dominam o ranking.

**Entregas (aditivas no dicionário de sinônimos):**

- [ ] Adicionar ao cluster `"observabilidade"` em `DEFAULT_SYNONYMS`: `"production"`, `"deployment"`, `"readiness"`.
- [ ] Adicionar ao cluster `"configuracao"` em `DEFAULT_SYNONYMS`: `"health"`, `"ready"`, `"live"`.
- [ ] OU adicionar novo cluster: `"producao": ["production", "readiness", "health", "deployment", "live", "ready", "fail-fast"]`.
- [ ] Verificar que as adições não criam caminhos de expansão indesejados (ex: `health` não deve direcionar para documentos de segurança não relacionados).
- [ ] Avaliar se `microservice-configuration-production-readiness` deve ter `priority:high` dado que health checks e production readiness são críticos — documentar decisão.

**Critério de aceite:**
- `resolve_instruction_context("me informe como a observabilidade deve ser implementada", max_results=7)` inclui `microservice-configuration-production-readiness`.
- `resolve_instruction_context("como separar /health/live de /health/ready em servico .NET", max_results=7)` inclui `microservice-configuration-production-readiness`.
- Todos os testes existentes continuam verdes.

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção):
def test_FAIL_observability_query_missing_configuration_readiness():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("me informe como a observabilidade deve ser implementada", max_results=7))
    assert "microservice-configuration-production-readiness" in data["selected_ids"], \
        f"configuration-production-readiness ausente. selected={data['selected_ids']}"

def test_FAIL_health_check_query_missing_configuration_readiness():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("como separar /health/live de /health/ready em servico .NET", max_results=7))
    assert "microservice-configuration-production-readiness" in data["selected_ids"], \
        f"configuration-production-readiness ausente. selected={data['selected_ids']}"

def test_FAIL_synonym_health_does_not_reach_configuration():
    from corporate_instructions_mcp.indexing import _SYNONYM_LOOKUP
    health_exp = set(_SYNONYM_LOOKUP.get("health", []))
    obs_exp = set(_SYNONYM_LOOKUP.get("observabilidade", []))
    target = {"configuration", "production", "readiness", "deployment"}
    assert (health_exp | obs_exp) & target, \
        f"Nenhuma expansão de 'health'/{health_exp} ou 'observabilidade'/{obs_exp} alcança {target}"

# COMPORTAMENTO ESPERADO (após a correção):
def test_EXPECT_observability_query_surfaces_configuration_readiness():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("me informe como a observabilidade deve ser implementada", max_results=7))
    assert "microservice-configuration-production-readiness" in data["selected_ids"]
    assert "microservice-opentelemetry-correlation-and-health" in data["selected_ids"]
```

---

### I-05 — `dns-retry-pattern` como ruído em queries de resiliência HTTP/Polly

**Background:** O `DEFAULT_SYNONYMS` tem `"dns": [..., "retry"]` e `"resiliencia": ["polly", "retry", ...]`. A função `_build_synonym_lookup` cria o reverse lookup, gerando `"retry" → [..., "dns"]`. Portanto, qualquer query com `"resiliencia"` expande para `"retry"`, que por sua vez pontua `dns-retry-pattern` (tags: `[dns, retry, resilience, polly]`). Com `priority:high` e `kind:reference`, o documento entra no pool de resiliência HTTP mesmo sendo específico para DNS.

**Entregas:**

- [ ] Remover `"retry"` do cluster `"dns"` em `DEFAULT_SYNONYMS` — DNS retry é um padrão específico, não um sinônimo genérico de retry.
- [ ] OU adicionar `dns-retry-pattern` ao `_LOW_SIGNAL_REFERENCE_TERMS` como documento de escopo restrito, reduzindo seu peso no pool geral.
- [ ] OU adicionar `scope: "**/*DnsClient*.cs,**/*Dns*.cs"` ao frontmatter de `dns-retry-pattern` para restringir sua aplicabilidade.
- [ ] Verificar que `dns-retry-pattern` ainda aparece corretamente em queries sobre DNS (`"retry DNS polly"` deve continuar funcionando — `test_search_instructions_finds_dns` não deve regredir).

**Critério de aceite:**
- `search_instructions("como configurar retry com backoff e circuit breaker para API de pagamentos", max_results=7)` não inclui `dns-retry-pattern`.
- `search_instructions("retry DNS polly", max_results=3)` ainda retorna `dns-retry-pattern` como resultado #1 (sem regressão de `test_search_instructions_finds_dns`).

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção):
def test_FAIL_dns_retry_appears_in_polly_circuit_breaker_query():
    from corporate_instructions_mcp.server import search_instructions
    data = json.loads(search_instructions("como configurar retry com backoff e circuit breaker para API de pagamentos", max_results=7))
    ids = [r["id"] for r in data["results"]]
    assert "dns-retry-pattern" not in ids, f"dns-retry-pattern em query de circuit breaker Polly: {ids}"

def test_FAIL_resiliencia_synonym_retry_cross_contaminates_dns():
    from corporate_instructions_mcp.indexing import expand_query_with_metadata, tokenize_query, _SYNONYM_LOOKUP
    from corporate_instructions_mcp.server import _ensure_index
    tokens = tokenize_query("resiliencia polly circuit breaker")
    info = expand_query_with_metadata(tokens)
    assert "retry" in info.weights and info.weights["retry"] == 0.5
    idx, _ = _ensure_index()
    assert "retry" in idx["dns-retry-pattern"].tags  # confirma o caminho de contaminação

# COMPORTAMENTO ESPERADO (após a correção):
def test_EXPECT_httpclientfactory_query_excludes_dns_retry():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("qual padrao para typed client com IHttpClientFactory e mapping de DTO externo", max_results=7))
    assert "dns-retry-pattern" not in data["selected_ids"], \
        f"dns-retry-pattern em query de IHttpClientFactory: {data['selected_ids']}"

# REGRESSÃO OBRIGATÓRIA (deve continuar passando):
def test_REGRESSION_dns_query_still_finds_dns_retry_pattern():
    from corporate_instructions_mcp.server import search_instructions
    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"][0]["id"] == "dns-retry-pattern"
```

---

### I-06 — Queries compostas multi-tema sem diversidade no top-5

**Background:** `build_resolved_context` em `context_resolver.py` seleciona candidatos por score ranqueado dentro de um pool de `max(max_results*2, 6)` documentos. Com I-01 distorcendo os scores, documentos de alto body-score por conectivos podem dominar o pool e expulsar documentos temáticos relevantes.

**Revalidação 2026-05-04:** na rodada real mais recente, `T24` passou e os três temas esperados apareceram no top-5. Portanto, este item deve permanecer como hipótese condicional, não como falha confirmada no estado atual.

**Dependência:** I-01 deve ser corrigida primeiro. Avaliar se o problema persiste após I-01 antes de implementar mudança no algoritmo de seleção.

**Entregas (se necessário após I-01):**

- [ ] Medir resultado da suíte T24 após I-01. Se `architecture-layering` subir para top-5, I-06 está resolvida por transitividade.
- [ ] Se ainda falhar: introduzir **diversity slot** em `build_resolved_context` — ao selecionar, garantir que ao menos um ID por cluster temático detectado seja incluído no top-5.
- [ ] Alternativa mais simples: se a query contém ≥ 3 termos de domínios distintos (detectáveis por tag de cada candidato), ampliar `pool_size` para `max_results * 3` antes de rankear.
- [ ] Qualquer mudança deve ser validada com teste de regressão em `test_resolve_instruction_context_cep_viacep_surfaces_normative_bundle`.

**Critério de aceite (condicional a I-01 e à revalidação):**
- T24: `resolve_instruction_context("quero estruturar o projeto, instrumentar observabilidade e integrar API externa com resiliencia", max_results=7)` inclui os 3 IDs primários nos top-5.
- Nenhum teste existente regride.

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção — validar se ainda falha após I-01):
def test_FAIL_composite_query_all_three_themes_in_top5():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context(
        "quero estruturar o projeto, instrumentar observabilidade e integrar API externa com resiliencia",
        max_results=7
    ))
    top5 = data["selected_ids"][:5]
    required = {
        "microservice-architecture-layering",
        "microservice-opentelemetry-correlation-and-health",
        "microservice-integration-httpclientfactory-contracts",
    }
    missing = required - set(top5)
    assert not missing, f"Temas ausentes do top-5: {missing}. top5={top5}"

# COMPORTAMENTO ESPERADO:
def test_EXPECT_integration_query_surfaces_resilience_and_di():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("como fazer integracao externa", max_results=7))
    selected = data["selected_ids"]
    assert "microservice-integration-httpclientfactory-contracts" in selected
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in selected
```

---

### I-07 — `api-openfinance-patterns` ausente em queries de paginação/coleções

**Background:** Os tokens `paginacao` e `colecoes` não têm entradas explícitas no `DEFAULT_SYNONYMS`, logo a expansão para termos relacionados a `openfinance`, `envelope` ou contratos de API de coleção depende de caminhos indiretos.

**Revalidação 2026-05-04:** na rodada real mais recente, `T17` passou e `microservice-api-openfinance-patterns` apareceu em `selected_ids`. Portanto, este item deve ser revalidado antes de qualquer mudança no dicionário de sinônimos.

**Entregas (aditivas no dicionário de sinônimos):**

- [ ] Adicionar chave `"paginacao"` ao `DEFAULT_SYNONYMS` com valores `["pagination", "filtering", "ordering", "collection", "envelope"]`.
- [ ] Adicionar chave `"colecoes"` ao `DEFAULT_SYNONYMS` com valores `["collection", "pagination", "filtering", "api-collection"]`.
- [ ] OU adicionar `"paginacao"` e `"colecoes"` como termos dentro do cluster `"api"` existente.
- [ ] Verificar que a expansão não arrasta documentos de mensageria/cache para queries de coleções.

**Critério de aceite:**
- `resolve_instruction_context("como implementar paginacao, filtro e ordenacao em colecoes sem quebrar contrato", max_results=7)` inclui `microservice-api-openfinance-patterns`.
- `resolve_instruction_context("quando usar imemorycache, ttl e invalidacao em API de consulta", max_results=7)` não piora (T23 deve manter seus primary_ids).

**Novos testes obrigatórios:**

```python
# FALHA (antes da correção):
def test_FAIL_pagination_query_missing_openfinance():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context(
        "como implementar paginacao, filtro e ordenacao em colecoes sem quebrar contrato",
        max_results=7
    ))
    assert "microservice-api-openfinance-patterns" in data["selected_ids"], \
        f"api-openfinance-patterns ausente em query de coleções. selected={data['selected_ids']}"

def test_FAIL_synonym_paginacao_has_no_expansion():
    from corporate_instructions_mcp.indexing import _SYNONYM_LOOKUP
    exp = set(_SYNONYM_LOOKUP.get("paginacao", []))
    assert exp & {"pagination", "filtering", "collection", "envelope"}, \
        f"'paginacao' sem expansão útil. expansões={exp}"

# COMPORTAMENTO ESPERADO (após a correção):
def test_EXPECT_collection_query_surfaces_openfinance_and_rest():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context(
        "como implementar paginacao, filtro e ordenacao em colecoes sem quebrar contrato",
        max_results=7
    ))
    assert "microservice-api-collection-resources-pagination-filters" in data["selected_ids"]
    assert "microservice-api-openfinance-patterns" in data["selected_ids"]

# REGRESSÃO OBRIGATÓRIA:
def test_REGRESSION_cache_query_T23_still_surfaces_cache_policy():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context(
        "quando usar imemorycache, ttl e invalidacao em API de consulta",
        max_results=7
    ))
    assert "microservice-caching-imemorycache-policy" in data["selected_ids"]
```

---

## Critérios de aceite do épico

- [ ] `pytest -q` no servidor passa com zero regressões após cada issue implementada isoladamente.
- [ ] Suíte de 24 testes (`testes-basicos-montagem-contexto-mcp.md`) aprovada com ≥ 21/24.
- [ ] I-01 implementada e validada antes de I-02 e I-06 (dependência explícita).
- [ ] I-03, I-06 e I-07 só avançam para implementação após revalidação explícita no estado atual da fixture.
- [ ] Se I-03 for confirmada na revalidação, implementar sem quebrar testes existentes que ainda referenciem `security-baseline-secrets` (verificar e atualizar se necessário).
- [ ] Para cada issue: teste de falha executa e falha **antes** da correção; teste de comportamento esperado passa **após** a correção.
- [ ] Nenhum dos testes de regressão listados (`test_search_instructions_finds_dns`, `test_resolve_instruction_context_cep_viacep_surfaces_normative_bundle`, `test_search_persistencia_sql_returns_data_access`) regride.
- [ ] Mudanças em `DEFAULT_SYNONYMS` são documentadas com comentário inline explicando a intenção de cada cluster novo ou modificado.

## Fora de escopo deste épico

- Reescrita do algoritmo de ranking (mudança apenas no conjunto de stopwords e no dicionário de sinônimos).
- Embedding/semântica vetorial (abordagem BM25 textual é mantida).
- Alteração de qualquer tool do servidor além do dicionário de sinônimos e stopwords em `indexing.py`.
- Mudanças no protocolo stdio ou no contrato de entrada/saída das tools.
- Atualização do corpus real de produção (`INSTRUCTIONS_ROOT` em produção) — escopo restrito a `fixtures/instructions`.

## Referências

- Auditoria técnica: conversa de 2026-05-04 (suíte 24 testes + análise de causa raiz)
- Reexecução real via MCP `stdio`: `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__execucao-real-e-analise-epic-07.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`
- `mcp-instructions-server/corporate_instructions_mcp/indexing.py`
- `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`
- `mcp-instructions-server/tests/smoke_test.py`
- EPIC-05: Evidence gate e compliance matrix
- EPIC-06: Gap analysis de uso real com agente
