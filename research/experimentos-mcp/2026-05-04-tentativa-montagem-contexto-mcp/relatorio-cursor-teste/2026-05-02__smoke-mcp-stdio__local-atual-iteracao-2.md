# Smoke test MCP stdio — local atual (iteração 2)

## Objetivo

Executar uma nova iteração do smoke test MCP stdio contra a versão local atual do `corporate_instructions_mcp`, preservando as queries anteriores para comparabilidade e adicionando probes específicos para os refinamentos em `M7`, `M8`, `M9`, `M12`, `M13` e `M20`.

## Configuração da rodada

- Data: `2026-05-02`
- Tipo: `MCP stdio`
- Servidor executado: `python -m corporate_instructions_mcp`
- Diretório de execução: `c:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `c:\_projeto\Copilot-Research\fixtures\instructions`
- Query mode: `search_instructions` com `include_diagnostics=true`

## Tools expostas

- `detect_instruction_conflicts`
- `get_instructions_batch`
- `get_normative_checklist`
- `list_instructions_index`
- `resolve_instruction_context`
- `search_instructions`

## Queries base reaplicadas

### `mensageria outbox`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-data-access-and-sql-security`
- `search_confidence: 0.7967`
- `fallback_suggestions: []`

### `idempotencia eventos`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-rest-http-semantics-and-status-codes`
- `search_confidence: 0.775`
- `fallback_suggestions: []`

### `resiliencia retry timeout`

- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `dns-retry-pattern`
- `microservice-integration-httpclientfactory-contracts`
- `search_confidence: 1.0`
- `fallback_suggestions: []`

### `sql seguranca persistencia`

- `microservice-data-access-and-sql-security`
- `microservice-auth-jwt-bearer-and-authorization`
- `microservice-authorization-resource-scope-and-audit`
- `search_confidence: 0.7075`
- `fallback_suggestions`: 1 sugestão de ambiguidade de top scores

### `observabilidade correlation tracing`

- `microservice-opentelemetry-correlation-and-health`
- `microservice-saga-process-manager-and-compensation`
- `microservice-clean-architecture-guardrails`
- `search_confidence: 1.0`
- `fallback_suggestions: []`

## Probes adicionais desta iteração

### `qvwxzplm`

- `result_count: 0`
- `note`: `No matches; refine query or use list_instructions_index.`
- `fallback_suggestions`:
  - ampliar `max_results`
  - tentar recorte por tags

Leitura:

- o bug de score positivo apenas por `priority` não se manifestou
- o servidor agora entrega um fluxo útil para `zero_results`

### `"problem details"`

- `microservice-api-validation-and-error-contracts`
- `microservice-api-error-catalog-baseline`
- `microservice-api-openfinance-patterns`
- `search_confidence: 0.895`

Leitura:

- o boost por frase exata está a puxar documentos coerentes com o termo composto

### `.NET 8 net8 v2`

- `microservice-api-validation-and-error-contracts`
- `microservice-api-openfinance-patterns`
- `microservice-rest-http-semantics-and-status-codes`
- `matched_user_terms` observados no diagnóstico:
  - `2`
  - `8`
  - `net`
  - `v2`

Leitura:

- a tokenização passou a preservar variantes úteis de versão, mas este smoke test ainda não prova, sozinho, que o ranking final para queries de versão já está ideal em corpus real

## Batch por seções

### Batch `retry`

IDs solicitados:

- `dns-retry-pattern`
- `microservice-resilience-polly-timeouts-and-circuit-breaker`

Resultado:

- `found_count: 2`
- `dns-retry-pattern`
  - `section_match_count: 2`
  - `included_headings`:
    - `Padrão de retry para DNS`
    - `Padrão de retry para DNS > Anti-padrões`
- `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `section_match_count: 4`
  - `included_headings`:
    - `Objetivo > TL;DR`
    - `Objetivo > Política de retry`
    - `Objetivo > Snippet`
    - `Objetivo > Não pode ser feito`

### Batch `problem`

ID solicitado:

- `microservice-rest-http-semantics-and-status-codes`

Resultado:

- `found_count: 1`
- `section_match_count: 2`
- `included_headings`:
  - `Objetivo`
  - `Objetivo > Mapeamento mínimo de status (referência)`

Leitura:

- o batch agora já devolve evidência observável de quais seções foram escolhidas

## Tool composta

### `resolve_instruction_context`

- selecionou:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-data-access-and-sql-security`
- retornou `search` + `batch`
- `corpus_version`: `53abc71415375f5282c7c0def68caa191ed95011f31b4c9cc98889b50c08de71`

## Leitura inicial

Esta segunda iteração manteve estabilidade nas queries-base e evidenciou comportamentos novos que não estavam explicitamente testados antes: fallback em `zero_results`, sinalização de ambiguidade de ranking e batch retornando metadados de seções incluídas.

## Limitação

Continua sendo um smoke test MCP stdio, não uma execução completa de agente ponta a ponta.
