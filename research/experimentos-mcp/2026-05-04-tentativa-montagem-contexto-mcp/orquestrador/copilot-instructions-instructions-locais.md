# Instruções locais (cenário: `.github/instructions`)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Não inventar**: sem evidência no código ou nas instructions locais, rotule como **HIPÓTESE** e descreva como validar.

## Fonte de guardrails (instructions locais)

- Use como fonte principal de padrões e políticas os ficheiros em `.github/instructions/`.
- Se o projeto do experimento não tiver `.github/instructions/`, declare **lacuna** e não substitua por políticas inventadas.

### Entrypoints do corpus (caminhos relativos a `.github/copilot-instructions.md`)

No layout do experimento, este guardrail deve corresponder a `.github/copilot-instructions.md` e o corpus a copiar para `.github/instructions/` deve espelhar [`fixtures/instructions/`](../../../../fixtures/instructions/).

Importante: os caminhos abaixo são **caminhos esperados no repositório-alvo do experimento** (onde existe `.github/`), não neste repositório de pesquisa. Por isso, eles são listados como **caminhos (não links)**:

- `./.github/instructions/artifact-encoding-line-endings-and-unicode.md`
- `./.github/instructions/assistant-workflow-bmad-planning-and-controlled-inference.md`
- `./.github/instructions/example-coding-style.md`
- `./.github/instructions/example-dns-retry.md`
- `./.github/instructions/example-security-baseline.md`
- `./.github/instructions/instruction-authoring-standard.md`
- `./.github/instructions/microservice-api-collection-resources-pagination-filters.md`
- `./.github/instructions/microservice-api-error-catalog-baseline.md`
- `./.github/instructions/microservice-api-openfinance-patterns.md`
- `./.github/instructions/microservice-api-validation-and-error-contracts.md`
- `./.github/instructions/microservice-architecture-layering.md`
- `./.github/instructions/microservice-auth-jwt-bearer-and-authorization.md`
- `./.github/instructions/microservice-authorization-resource-scope-and-audit.md`
- `./.github/instructions/microservice-caching-imemorycache-policy.md`
- `./.github/instructions/microservice-clean-architecture-guardrails.md`
- `./.github/instructions/microservice-configuration-production-readiness.md`
- `./.github/instructions/microservice-data-access-and-sql-security.md`
- `./.github/instructions/microservice-design-principles-solid-performance-types.md`
- `./.github/instructions/microservice-di-options-extensions.md`
- `./.github/instructions/microservice-domain-interfaces-models-repository.md`
- `./.github/instructions/microservice-integration-httpclientfactory-contracts.md`
- `./.github/instructions/microservice-messaging-rabbitmq-publish-consume.md`
- `./.github/instructions/microservice-opentelemetry-correlation-and-health.md`
- `./.github/instructions/microservice-resilience-polly-timeouts-and-circuit-breaker.md`
- `./.github/instructions/microservice-rest-http-semantics-and-status-codes.md`
- `./.github/instructions/microservice-saga-process-manager-and-compensation.md`
- `./.github/instructions/microservice-testing-strategy-unit-integration-contract.md`

## Fluxo mínimo (para reduzir variação)

Use BMAD antes de codar:
- Background
- Mission
- Approach
- Delivery/validation

Se houver dúvida de convenção (status codes, validação, erros, resiliência, cache, mensageria), procure uma instruction específica e cite o ficheiro usado.
