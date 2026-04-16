# Suíte de testes — Corporate Instructions MCP

Este documento descreve os testes automatizados em `tests/`, o que cada um valida e que pressupostos têm sobre o corpus.

## Como executar

Na pasta `mcp-instructions-server/`:

```bash
pip install -e ".[dev]"
pytest
```

Com verbosidade e só smoke: `pytest tests/smoke_test.py -v`. Integração STDIO (subprocess + cliente MCP): `pytest tests/integration_mcp_stdio_test.py -v`.

## Corpus usado

- **Smoke e maior parte dos testes:** `INSTRUCTIONS_ROOT` aponta para [`../../fixtures/instructions`](../../fixtures/instructions) (relativamente a `mcp-instructions-server/`). Vários testes assumem IDs concretos desse fixture (ex.: `dns-retry-pattern`, `microservice-data-access-and-sql-security`).
- **Integração MCP:** por omissão usa o mesmo fixture; se definir `INSTRUCTIONS_ROOT` no ambiente para outro diretório, alguns asserts condicionais deixam de aplicar-se (ou o teste é ignorado).

## Ficheiros de teste

| Ficheiro | Tipo | Âmbito |
|----------|------|--------|
| [`tests/smoke_test.py`](../tests/smoke_test.py) | Smoke | Importação directa do módulo `corporate_instructions_mcp.server`; sem subprocess. |
| [`tests/integration_mcp_stdio_test.py`](../tests/integration_mcp_stdio_test.py) | Integração | Processo real `python -m corporate_instructions_mcp` com JSON-RPC sobre stdio. |
| [`tests/test_indexing.py`](../tests/test_indexing.py) | Unitário | Funções puras e `build_index` em directórios temporários. |
| [`tests/test_paths.py`](../tests/test_paths.py) | Unitário | Validação de caminhos e segurança. |

---

## `smoke_test.py`

Executa as tools com `INSTRUCTIONS_ROOT` no fixture; reinicia o índice em memória entre testes.

| Teste | O que valida |
|-------|----------------|
| `test_list_instructions_index_count` | Resposta JSON com `count`, `by_tag`, e presença mínima de IDs conhecidos (incl. `dns-retry-pattern`, `security-baseline-secrets`, `csharp-async-style`). |
| `test_search_instructions_finds_dns` | Busca por texto encontra `dns-retry-pattern` no topo e devolve `composed_context`. |
| `test_search_results_have_related_ids_shape` | Cada resultado de busca inclui `related_ids` (lista de strings), sem o próprio `id`. |
| `test_search_dns_top_result_related_ids_include_resilience_policy` | Para o hit DNS, `related_ids` contém `microservice-resilience-polly-timeouts-and-circuit-breaker` (partilha de tags com a policy Polly). |
| `test_search_persistencia_sql_data_access_related_ids_include_dapper_neighbor` | Para `microservice-data-access-and-sql-security`, `related_ids` inclui `microservice-domain-interfaces-models-repository` (overlap forte de tags). |
| `test_search_instructions_default_max_results_is_ten` | Sem `max_results`, a lista tem exactamente 10 entradas para a query `microservice` (corpus com >10 matches). |
| `test_search_instructions_max_results_clamped_to_twenty` | `max_results=100` é limitado a 20 resultados. |
| `test_search_instructions_max_results_one` | `max_results=1` devolve uma linha. |
| `test_get_instructions_batch_single_document` | Batch com um único ID devolve conteúdo esperado (ex.: menção a Polly). |
| `test_search_tags_only` | Query vazia com `tags=security` filtra e inclui `security-baseline-secrets`. |
| `test_search_instructions_invalid_max_results_uses_default` | `max_results` inválido cai no default e ainda devolve resultados. |
| `test_search_instructions_persistencia_sql_returns_data_access` | Expansão por sinónimos / domínio: `persistência SQL` ranqueia `microservice-data-access-and-sql-security`. |
| `test_get_instructions_batch_returns_multiple_documents` | Vários IDs separados por vírgula; `found_count` e `missing_ids` coerentes. |
| `test_get_instructions_batch_errors` | `ids` vazio → erro JSON; ID inexistente → `missing_ids` e `found_count` zero. |
| `test_instructions_root_not_dir_raises` | `INSTRUCTIONS_ROOT` inexistente → `RuntimeError` ao chamar a tool (fail-fast). |

---

## `integration_mcp_stdio_test.py`

Valida o mesmo comportamento através do **transporte MCP real** (stdio), útil para regressões na serialização de argumentos, FastMCP e cliente.

| Teste | O que valida |
|-------|----------------|
| `test_mcp_stdio_list_search_get_instruction` | `list_tools` expõe exactamente as três tools; `list_instructions_index` com `by_tag`; `search_instructions` (DNS); `get_instructions_batch` com conteúdo não vazio. Com corpus alternativo, relaxa asserts que dependem de IDs fixos. |
| `test_mcp_stdio_search_default_max_persistencia_sql_and_related_ids` | **Só com o fixture por omissão** (caso contrário `skip`): `search_instructions` sem `max_results` para `microservice` → 10 resultados; `persistência SQL` inclui `microservice-data-access-and-sql-security` e `composed_context` não vazio; busca DNS com `related_ids` e policy Polly listada. |

---

## `test_indexing.py`

Testa `indexing.py` sem arrancar o servidor MCP.

| Teste | O que valida |
|-------|----------------|
| `test_tokenize_query_drops_short_and_splits` | `tokenize_query` ignora tokens demasiado curtos e separa palavras. |
| `test_summarize_body_truncates` | `summarize_body` respeita limite e sufixo `...`. |
| `test_excerpt_around_match_prefers_token_hit` | `excerpt_around_match` centra o excerto num match. |
| `test_score_record_respects_tag_filter` | Com filtro de tags, registos fora do filtro têm score zero. |
| `test_expand_query_with_synonyms_handles_accents` | Sinónimos e pesos (ex.: `persistência` → SQL/dapper a 0,5). |
| `test_score_record_boosts_related_domain_terms` | Match directo no corpo pontua mais que match só via sinónimo. |
| `test_build_index_duplicate_id_raises` | Dois ficheiros com o mesmo `id` no frontmatter → erro. |
| `test_build_index_missing_dir_returns_empty` | Directório inexistente → índice vazio. |
| `test_build_index_skips_huge_file` | Ficheiros acima do limite de bytes são ignorados. |
| `test_build_index_skips_symlink_escape` | Symlink para fora da raiz é ignorado (pode ser `skip` no Windows se criar symlink falhar). |
| `test_build_index_skips_huge_frontmatter` | Frontmatter YAML gigante é tratado como vazio e o corpo mantém-se. |
| `test_yaml_non_dict_frontmatter_treated_as_empty` | Frontmatter que não é mapeamento → metadados vazios; id derivado do ficheiro. |

---

## `test_paths.py`

| Teste | O que valida |
|-------|----------------|
| `test_require_existing_dir_ok` | `require_existing_dir` resolve um directório existente. |
| `test_require_existing_dir_empty_raises` | String vazia ou só espaços → `ValueError`. |
| `test_require_existing_dir_missing_raises` | Caminho inexistente → `ValueError`. |
| `test_instruction_path_needle_is_safe` | Rejeita caminhos absolutos, `..` e sequências inseguras. |
| `test_is_path_under_root` | Ficheiro dentro da raiz é aceite. |

---

## O que não é coberto por estes testes

- Comportamento do assistente ou qualidade do plano de código (avaliação humana / rubrica).
- Transporte HTTP ou autenticação (roadmap futuro).
- Performance ou carga em corpus muito maior que o fixture.

Para alterações nas tools ou no índice, execute `pytest` completo e, se possível, os testes de integração stdio.
