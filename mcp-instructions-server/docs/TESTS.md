# Suíte de testes — Corporate Instructions MCP

Este documento descreve os testes automatizados em `tests/`, o que cada um valida e que pressupostos têm sobre o corpus.

## Como executar

Na pasta `mcp-instructions-server/`:

```bash
pip install -e ".[dev]"
pytest
```

Com verbosidade e só smoke: `pytest tests/smoke_test.py -v`. Integração STDIO (subprocess + cliente MCP): `pytest tests/integration_mcp_stdio_test.py -v`. Telemetria NDJSON: `pytest tests/test_telemetry_ndjson.py -v`.

Para gravar o catálogo `tools/list` em JSON (útil quando um IDE mostra tools nas definições mas o chat nega): `python scripts/print_mcp_tools_list.py` (defina `INSTRUCTIONS_ROOT` como no IDE).

**Bateria manual / semi-automatizada (expansão de query, 3 tools):** plano em [`MCP-QUERY-EXPANSION-MANUAL-TEST-PLAN.md`](MCP-QUERY-EXPANSION-MANUAL-TEST-PLAN.md); script `python scripts/run_query_expansion_manual_battery.py` (tabela Markdown no stdout; opções `--json`, `--strict`).

### Telemetria estruturada (`CORPORATE_INSTRUCTIONS_TELEMETRY`)

Com `minimal` ou `full`, o servidor escreve linhas **NDJSON** em **stderr** (por exemplo `server_start`, `index_rebuilt`, eventos `*.completed` por tool). Guia prático (ver, gravar em ficheiro, filtrar, IDE): [`HOW-TO-TELEMETRY-LOGS.md`](HOW-TO-TELEMETRY-LOGS.md). Não misture stderr com stdout (protocolo MCP).

## Corpus usado

- **Smoke e maior parte dos testes:** `INSTRUCTIONS_ROOT` aponta para [`../../fixtures/instructions`](../../fixtures/instructions) (relativamente a `mcp-instructions-server/`). Vários testes assumem IDs concretos desse fixture (ex.: `dns-retry-pattern`, `microservice-data-access-and-sql-security`).
- **Integração MCP:** por omissão usa o mesmo fixture; se definir `INSTRUCTIONS_ROOT` no ambiente para outro diretório, alguns asserts condicionais deixam de aplicar-se (ou o teste é ignorado).

## Ficheiros de teste

| Ficheiro | Tipo | Âmbito |
|----------|------|--------|
| [`tests/smoke_test.py`](../tests/smoke_test.py) | Smoke | Importação directa do módulo `corporate_instructions_mcp.server`; sem subprocess. |
| [`tests/integration_mcp_stdio_test.py`](../tests/integration_mcp_stdio_test.py) | Integração | Processo real `python -m corporate_instructions_mcp` com JSON-RPC sobre stdio. |
| [`tests/test_context_triggers.py`](../tests/test_context_triggers.py) | Unitário | Contrato e motor determinístico da tool `get_context_triggers` (cenários, invariantes e erros). |
| [`tests/test_indexing.py`](../tests/test_indexing.py) | Unitário | Funções puras e `build_index` em directórios temporários. |
| [`tests/test_paths.py`](../tests/test_paths.py) | Unitário | Validação de caminhos e segurança. |
| [`tests/test_server_frontmatter.py`](../tests/test_server_frontmatter.py) | Unitário | Normalização JSON de frontmatter (`date`, `datetime`, `Decimal`, listas aninhadas). |
| [`tests/test_telemetry_ndjson.py`](../tests/test_telemetry_ndjson.py) | Unitário | Eventos NDJSON em stderr (`CORPORATE_INSTRUCTIONS_TELEMETRY`) sem subprocess MCP. |
| [`tests/test_epic05_tools.py`](../tests/test_epic05_tools.py) | Unitário/aceite | Aceite de P0 (`validate_applicability` + `build_compliance_matrix`) com 17 cenários obrigatórios. |
| [`tests/test_corpus_expansion_map_merged.py`](../tests/test_corpus_expansion_map_merged.py) | Unitário | Mapa `metadata/corpus-query-expansion-map/*.yaml` mesclado (schema ADR-002, ausência de `.yml` legado, spot-checks de expansão). |

---

## `smoke_test.py`

Executa as tools com `INSTRUCTIONS_ROOT` no fixture; reinicia o índice em memória entre testes.

| Teste | O que valida |
|-------|----------------|
| `test_list_instructions_index_count` | Resposta JSON com `status/index_health/warnings/errors`, `count`, `by_tag`, e presença mínima de IDs conhecidos (incl. `dns-retry-pattern`, `example-security-baseline`, `csharp-async-style`). |
| `test_search_instructions_finds_dns` | Busca por texto encontra `dns-retry-pattern` no topo e devolve `composed_context`. |
| `test_search_results_have_related_ids_shape` | Cada resultado de busca inclui `related_ids` (lista de strings), sem o próprio `id`. |
| `test_search_dns_top_result_related_ids_include_resilience_policy` | Para o hit DNS, `related_ids` contém `microservice-resilience-polly-timeouts-and-circuit-breaker` (partilha de tags com a policy Polly). |
| `test_search_persistencia_sql_data_access_related_ids_include_dapper_neighbor` | Para `microservice-data-access-and-sql-security`, `related_ids` inclui `microservice-domain-interfaces-models-repository` (overlap forte de tags). |
| `test_search_instructions_default_max_results_is_ten` | Sem `max_results`, a lista tem exactamente 10 entradas para a query `microservice` (corpus com >10 matches). |
| `test_search_instructions_max_results_clamped_to_twenty` | `max_results=100` é limitado a 20 resultados. |
| `test_search_instructions_max_results_one` | `max_results=1` devolve uma linha. |
| `test_get_instructions_batch_single_document` | Batch com um único ID devolve conteúdo esperado (ex.: menção a Polly). |
| `test_get_instructions_batch_includes_frontmatter_with_extra_keys` | Cada item inclui `frontmatter` com chaves extra do YAML (ex.: `owner`, `last_reviewed` como ISO). |
| `test_get_instructions_batch_frontmatter_round_trips_json` | `frontmatter` é serializável em JSON após `json.loads` do payload da tool. |
| `test_search_tags_only` | Query vazia com `tags=security` filtra e inclui `example-security-baseline`. |
| `test_search_instructions_invalid_max_results_uses_default` | `max_results` inválido cai no default e ainda devolve resultados. |
| `test_search_instructions_persistencia_sql_returns_data_access` | Expansão por sinónimos / domínio: `persistência SQL` ranqueia `microservice-data-access-and-sql-security`. |
| `test_search_instructions_multi_query_consolidated_output` | Modo `queries` devolve saída consolidada estável (`top_policies`, `top_references`, `coverage_gaps`). |
| `test_get_instructions_batch_returns_multiple_documents` | Vários IDs separados por vírgula; `found_count` e `missing_ids` coerentes. |
| `test_get_instructions_batch_errors` | `ids` vazio → erro JSON; ID inexistente → `missing_ids` e `found_count` zero. |
| `test_instructions_root_not_dir_raises` | `INSTRUCTIONS_ROOT` inexistente → payload com `status=error`, `ok=false` e `error_code=INDEX_LOAD_FAILED`. |
| `test_list_instructions_index_status_partial_when_warnings_present` | Quando há ficheiro ignorado por tamanho, `status=partial` e `warnings` é preenchido. |
| `test_resolve_instruction_context_exposes_p1_evidence_fields` | Campos P1 aditivos (`selection_rationale`, `pending_evidence`, `required_workspace_signals`, `next_repo_evidence_actions`). |

---

## `integration_mcp_stdio_test.py`

Valida o mesmo comportamento através do **transporte MCP real** (stdio), útil para regressões na serialização de argumentos, FastMCP e cliente.

| Teste | O que valida |
|-------|----------------|
| `test_mcp_stdio_list_search_get_instruction` | `list_tools` expõe pelo menos as tools base (`get_context_triggers`, `list_instructions_index`, `search_instructions`, `get_instructions_batch`, `validate_applicability`, `build_compliance_matrix`); valida também `list_instructions_index`, `search_instructions` (DNS) e `get_instructions_batch` com conteúdo não vazio. Com corpus alternativo, relaxa asserts que dependem de IDs fixos. |
| `test_mcp_stdio_search_default_max_persistencia_sql_and_related_ids` | **Só com o fixture por omissão** (caso contrário `skip`): `search_instructions` sem `max_results` para `microservice` → 10 resultados; `persistência SQL` inclui `microservice-data-access-and-sql-security` e `composed_context` não vazio; busca DNS com `related_ids` e policy Polly listada. |
| `test_mcp_stdio_get_context_triggers_contract_output` | Chama `get_context_triggers` via stdio com payload JSON, valida `schema_version`, `scenario`, `strategy` (`plan_only`) e `batch_required=true` para cenário transversal. |
| `test_mcp_stdio_composite_tools_expose_actionable_outputs` | `resolve_instruction_context` com campos P1 + chamadas reais a `validate_applicability` e `build_compliance_matrix` via stdio. |

## `test_context_triggers.py`

Suite unitária da nova tool de orquestração, escrita em ciclo TDD Red/Green/Refactor.

| Teste | O que valida |
|-------|----------------|
| `test_catalog_contains_required_sections` | Catálogo canónico carregável com secções obrigatórias de roteamento/evidence/stop. |
| `test_build_context_triggers_plan_cross_cutting_shape` | Output principal para cenário `plan_only` transversal com shape e campos críticos do contrato. |
| `test_tool_sequence_ordered_and_contains_only_read_tools_for_plan_only` | Ordem determinística da sequência e ausência de tools de execução em pedidos de plano. |
| `test_mentions_current_file_prepends_get_currentfile` | Regra de precedência para `mentions_current_file=true`. |
| `test_public_contract_without_workspace_signals_forces_human_stop` | Stop rule para risco de contrato público sem evidência local. |
| `test_mentions_new_infrastructure_without_workspace_signals_sets_fallback` | Fallback de não introduzir stack por inferência e stop rule para infraestrutura nova sem evidência. |
| `test_invalid_schema_version_raises_contract_error` | Rejeição de versão de contrato inválida com código de erro explícito. |
| `test_conflicting_plan_only_flags_raise_contract_error` | Rejeição de conflito `wants_only_plan=true` com modo de execução incompatível. |
| `test_missing_required_section_raises_contract_error` | Rejeição de payload incompleto (`INVALID_REQUEST_PAYLOAD`). |

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

## `test_server_frontmatter.py`

Testa `_json_safe_frontmatter` sem corpus (datas e decimais YAML → valores JSON-safe).

| Teste | O que valida |
|-------|----------------|
| `test_json_safe_frontmatter_converts_date_and_nested` | `date` em raiz e aninhado → strings ISO. |
| `test_json_safe_frontmatter_datetime_and_decimal` | `datetime` e `Decimal` convertidos. |
| `test_json_safe_frontmatter_lists` | Listas com `date` dentro. |
| `test_json_safe_frontmatter_empty` | Dicionário vazio. |

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

## `test_epic05_tools.py`

Aceite obrigatório de P0 (secção 16.1 da especificação), sem subprocess:

| Teste | O que valida |
|-------|----------------|
| `test_validate_applicability_scope_no_match_returns_non_applicable` | `scope` fora do artefacto → `non_applicable`. |
| `test_validate_applicability_policy_in_scope_without_workspace_requirement_returns_applicable` | policy sem evidence gate em escopo → `applicable`. |
| `test_validate_applicability_policy_with_sufficient_evidence_returns_applicable` | evidência positiva suficiente → `applicable`. |
| `test_validate_applicability_policy_on_absence_hypothesis_only` | `on_absence=hypothesis_only` aplicado quando faltam sinais. |
| `test_validate_applicability_policy_without_on_absence_defaults_blocked` | sem `on_absence` e sem sinais suficientes → `blocked_by_missing_evidence`. |
| `test_validate_applicability_reference_in_scope_returns_hypothesis_only` | `kind=reference` em escopo → `hypothesis_only`. |
| `test_validate_applicability_accepts_simple_string_evidence` | contrato backward-compatible para evidência em lista de strings. |
| `test_validate_applicability_accepts_structured_evidence` | contrato com objetos ricos (`value`, `path`, `symbol`, `source`, `evidence_type`). |
| `test_validate_applicability_accepts_negative_evidence` | evidência negativa tratada de forma conservadora (sem forçar não conformidade). |
| `test_validate_applicability_normalizes_windows_path` | normalização de path Windows (`\`) no matching de `scope`. |
| `test_build_compliance_matrix_non_applicable_maps_not_applicable` | mapeamento `non_applicable -> not_applicable`. |
| `test_build_compliance_matrix_hypothesis_only_maps_not_enforceable` | mapeamento `hypothesis_only -> not_enforceable`. |
| `test_build_compliance_matrix_blocked_maps_not_enforceable` | mapeamento `blocked_by_missing_evidence -> not_enforceable`. |
| `test_build_compliance_matrix_applicable_positive_maps_conformant` | `applicable + positive` -> `conformant`. |
| `test_build_compliance_matrix_applicable_positive_and_gap_maps_partial` | `applicable + positive + gap` -> `partial_conformance`. |
| `test_build_compliance_matrix_applicable_deviation_maps_non_conformance` | `applicable + deviation` -> `non_conformance`. |
| `test_build_compliance_matrix_applicable_without_observation_maps_insufficient_evidence` | `applicable` sem observação suficiente -> `insufficient_evidence`. |

---

## Validação real por agente (STDIO)

Além do `pytest`, existe uma verificação de consumo real no script:

- [`scripts/run_epic05_stdio_real_check.py`](../scripts/run_epic05_stdio_real_check.py)

O script sobe `python -m corporate_instructions_mcp`, chama as tools por cliente MCP real e valida saída esperada para P0/P1/P2.

Plano detalhado para repetir em outros contextos: [`STDIO-REAL-TEST-PLAN.md`](STDIO-REAL-TEST-PLAN.md).

## O que não é coberto por estes testes

- Comportamento do assistente ou qualidade do plano de código (avaliação humana / rubrica).
- Transporte HTTP ou autenticação (roadmap futuro).
- Performance ou carga em corpus muito maior que o fixture.

Para alterações nas tools ou no índice, execute `pytest` completo e, se possível, os testes de integração stdio.
