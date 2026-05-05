# Smoke test MCP stdio — local atual (cenários 2, 3 e 4)

## Objetivo

Executar uma rodada de smoke test MCP stdio contra a versão local atual do `corporate_instructions_mcp`, focada nos cenários:

- `cenario-02-cep-viacep`
- `cenario-03-auth-jwt`
- `cenario-04-saga-onboarding`

Além da validação MCP, foi feita uma verificação rápida da base atual do projeto antes da rodada.

## Configuração da rodada

- Data: `2026-05-02`
- Tipo: `MCP stdio`
- Servidor executado: `python -m corporate_instructions_mcp`
- Diretório de execução: `c:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `c:\_projeto\Copilot-Research\fixtures\instructions`
- Telemetria: `CORPORATE_INSTRUCTIONS_TELEMETRY=minimal`
- Validação operacional: MCP stdio real; não agente ponta a ponta

## Sanidade do projeto

Antes do smoke test:

- `pytest -q`
- resultado: `64 passed, 1 skipped`

Leitura:

- a base atual estava estável antes da rodada específica dos cenários 2, 3 e 4

## Tools expostas

- `detect_instruction_conflicts`
- `get_instructions_batch`
- `get_normative_checklist`
- `list_instructions_index`
- `resolve_instruction_context`
- `search_instructions`

## Sinais agregados da rodada

Relatório de qualidade derivado da telemetria desta execução:

- `total_completed_calls: 31`
- `search_completed_calls: 18`
- `tool_failure_rate: 0.0`
- `retry_rate: 0.0`
- `zero_result_rate: 0.0`
- `low_confidence_rate: 0.0`
- `avg_search_confidence: 0.983417`
- `warnings: []`

Leitura:

- a rodada foi estável
- não houve falhas de tool nem casos de busca com zero resultado

## Cenário 2 — CEP / ViaCEP

### Search

Queries principais e top-3:

- `httpclient timeout retry circuit breaker`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `dns-retry-pattern`
  - `microservice-integration-httpclientfactory-contracts`
- `cache ttl imemorycache`
  - `microservice-caching-imemorycache-policy`
  - `microservice-messaging-rabbitmq-publish-consume`
  - `instruction-authoring-standard`
- `api validation problem details 400 422`
  - `microservice-api-validation-and-error-contracts`
  - `microservice-api-error-catalog-baseline`
  - `microservice-rest-http-semantics-and-status-codes`
- `observability correlation tracing health`
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-clean-architecture-guardrails`
  - `microservice-saga-process-manager-and-compensation`

### Tools compostas

`resolve_instruction_context` para `httpclient timeout retry circuit breaker`:

- `selected_ids`:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
  - `dns-retry-pattern`
- `normative_ids`:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
- `supporting_ids`:
  - `dns-retry-pattern`
- `section_focus`: `breaker`

`get_normative_checklist` para `api_http_contract`:

- `total_items: 4`
- `required_items: 2`
- `implementation_readiness: ready`
- itens:
  - `status_code_semantics`
  - `problem_details`
  - `auth_responses`
  - `collection_contracts`

`detect_instruction_conflicts` entre:

- `microservice-api-validation-and-error-contracts`
- `microservice-rest-http-semantics-and-status-codes`

Resultado:

- `potential_conflict: true`
- `severity: medium`
- sem vencedor automático
- guidance: combinar ambos e escalar para instructions locais se a aplicação concreta continuar ambígua

### Leitura

- o cenário continua bem ancorado em guardrails transversais
- a versão atual reduz fricção na composição entre HTTP, resiliência e contrato de erro
- a principal lacuna continua de domínio: não há guidance específico para ViaCEP, modelagem de endereço ou estado pendente

## Cenário 3 — Auth / JWT

### Search

Queries principais e top-3:

- `jwt bearer authorization claims 401 403`
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-api-validation-and-error-contracts`
- `resource scope ownership audit authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-saga-process-manager-and-compensation`
- `api validation error contracts 401 403 404`
  - `microservice-rest-http-semantics-and-status-codes`
  - `microservice-api-validation-and-error-contracts`
  - `microservice-api-error-catalog-baseline`
- `security secrets compliance`
  - `microservice-auth-jwt-bearer-and-authorization`
  - `security-baseline-secrets`
  - `microservice-authorization-resource-scope-and-audit`

### Tools compostas

`resolve_instruction_context` para `jwt bearer authorization claims 401 403`:

- `selected_ids`:
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-api-validation-and-error-contracts`
- `normative_ids`: os 3 selecionados
- `supporting_ids`: nenhum
- `section_focus`: `authorization`

`get_normative_checklist` para `security_baseline`:

- `total_items: 4`
- `required_items: 2`
- `implementation_readiness: ready`
- itens:
  - `secret_handling`
  - `jwt_validation`
  - `resource_scope_audit`
  - `error_leakage`

`detect_instruction_conflicts` entre:

- `microservice-auth-jwt-bearer-and-authorization`
- `microservice-authorization-resource-scope-and-audit`

Resultado:

- `potential_conflict: true`
- `severity: medium`
- sem vencedor automático
- guidance: combinar ambos e escalar para instructions locais se houver ambiguidade concreta

### Leitura

- este segue a ser o cenário mais forte para o corpus atual
- a versão atual melhora bastante a capacidade de consumo imediato do conjunto JWT + ownership + contrato HTTP
- a principal lacuna continua local ao produto: nomes de role, contratos exatos de listagem e schema de auditoria

## Cenário 4 — Saga onboarding

### Search

Queries principais e top-3:

- `saga outbox idempotencia mensageria`
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-data-access-and-sql-security`
- `retry timeout circuit breaker polly`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `dns-retry-pattern`
  - `microservice-integration-httpclientfactory-contracts`
- `sql transactions data access consistency`
  - `microservice-data-access-and-sql-security`
  - `microservice-domain-interfaces-models-repository`
  - `microservice-di-options-extensions`
- `observability correlation tracing`
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-clean-architecture-guardrails`
  - `microservice-messaging-rabbitmq-publish-consume`

### Tools compostas

`resolve_instruction_context` para `saga outbox idempotencia mensageria`:

- `selected_ids`:
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-data-access-and-sql-security`
- `normative_ids`:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-data-access-and-sql-security`
- `supporting_ids`:
  - `microservice-saga-process-manager-and-compensation`
- `section_focus`: `mensageria`

`get_normative_checklist` para `mensageria_outbox`:

- `total_items: 5`
- `required_items: 3`
- `implementation_readiness: ready`
- itens:
  - `transactional_outbox`
  - `idempotent_consumers`
  - `retry_and_dead_letter`
  - `traceability`
  - `delivery_tests`

`detect_instruction_conflicts` entre:

- `microservice-saga-process-manager-and-compensation`
- `microservice-messaging-rabbitmq-publish-consume`

Resultado:

- `potential_conflict: true`
- `severity: low`
- `winner_id: microservice-messaging-rabbitmq-publish-consume`
- precedência por `kind`: `policy` vence `reference`

### Leitura

- o cenário ficou bem suportado no desenho transversal de saga/outbox/idempotência
- a nova tool de conflito ajuda a não tratar a reference de saga como baseline normativo
- ainda faltam detalhes de domínio concreto, como shape do `OnboardingSagaState`, contrato das integrações externas e recorte exato das compensações

## Conclusão

A versão local atual comportou-se bem nos três cenários:

- nenhum sinal de instabilidade no smoke
- boa cobertura transversal em `CEP/ViaCEP`
- cobertura forte em `Auth/JWT`
- boa cobertura arquitetural em `Saga onboarding`

O valor novo não apareceu só no ranking, mas no contrato utilizável:

- `resolve_instruction_context` reduz orquestração manual
- `get_normative_checklist` transforma corpus em checklist acionável
- `detect_instruction_conflicts` melhora precedência e consistência

## Limitação

Esta validação continua sendo via MCP stdio real. Ainda não é uma execução ponta a ponta de agente usando esses cenários num repositório-alvo de implementação.
