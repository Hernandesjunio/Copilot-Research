# Instruções locais (cenário: `.github/instructions`)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Não inventar**: sem evidência no código ou nas instructions locais, rotule como **HIPÓTESE** e descreva como validar.

## Fonte de guardrails (instructions locais)

- Use como fonte principal de padrões e políticas os ficheiros em `.github/instructions/`.
- Se o projeto do experimento não tiver `.github/instructions/`, declare **lacuna** e não substitua por políticas inventadas.

### Entrypoints do corpus (caminhos relativos a `.github/copilot-instructions.md`)

No layout do experimento, este guardrail deve corresponder a `.github/copilot-instructions.md` e o corpus a copiar para `.github/instructions/` deve espelhar [`fixtures/instructions/`](../../../../fixtures/instructions/). Os links abaixo apontam para cada ficheiro sob `instructions/` (resolução correta quando o entrypoint está na pasta `.github/`).

- [Artefactos — encoding, fim de linha e Unicode](.github/instructions/artifact-encoding-line-endings-and-unicode.md)
- [Fluxo de assistência — BMAD obrigatório, refinamento e inferência controlada](.github/instructions/assistant-workflow-bmad-planning-and-controlled-inference.md)
- [Estilo C# — async e nomenclatura](.github/instructions/example-coding-style.md)
- [Padrão de retry para resolução DNS](.github/instructions/example-dns-retry.md)
- [Linha de base — segredos e dados sensíveis](.github/instructions/example-security-baseline.md)
- [Corpus — padrão de autoria de instructions](.github/instructions/instruction-authoring-standard.md)
- [API — coleções, paginação, filtros, ordenação e compatibilidade](.github/instructions/microservice-api-collection-resources-pagination-filters.md)
- [API — catálogo base de erros HTTP e referências](.github/instructions/microservice-api-error-catalog-baseline.md)
- [Microservice API — envelope de resposta, erros globais e documentação](.github/instructions/microservice-api-openfinance-patterns.md)
- [API — validação de entrada, 400 vs 422 e contrato de erros](.github/instructions/microservice-api-validation-and-error-contracts.md)
- [Microservice .NET — arquitetura por camadas](.github/instructions/microservice-architecture-layering.md)
- [Auth — JWT Bearer, validação de token e autorização por claims](.github/instructions/microservice-auth-jwt-bearer-and-authorization.md)
- [Autorização — âmbito de recurso, propriedade e auditoria](.github/instructions/microservice-authorization-resource-scope-and-audit.md)
- [Cache — IMemoryCache, chaves, TTL e invalidação](.github/instructions/microservice-caching-imemorycache-policy.md)
- [Guardrails de Clean Architecture para microservices](.github/instructions/microservice-clean-architecture-guardrails.md)
- [Configuração e operação — options, fail-fast, feature flags e deploy](.github/instructions/microservice-configuration-production-readiness.md)
- [Dados — acesso seguro, parametrização, transações e timeouts](.github/instructions/microservice-data-access-and-sql-security.md)
- [Design — SOLID, coesão, generics e performance de tipos](.github/instructions/microservice-design-principles-solid-performance-types.md)
- [DI e configurações — Options e extension methods](.github/instructions/microservice-di-options-extensions.md)
- [Dominio, Interfaces, Modelo e Repositorio — contrato e implementação](.github/instructions/microservice-domain-interfaces-models-repository.md)
- [Integrações HTTP — HttpClientFactory, contratos externos e tolerância](.github/instructions/microservice-integration-httpclientfactory-contracts.md)
- [Mensageria — RabbitMQ, contratos, idempotência e dead letter](.github/instructions/microservice-messaging-rabbitmq-publish-consume.md)
- [Observabilidade — OpenTelemetry, correlação, logs e health checks](.github/instructions/microservice-opentelemetry-correlation-and-health.md)
- [Resiliência — timeout, retry com backoff, jitter e circuit breaker](.github/instructions/microservice-resilience-polly-timeouts-and-circuit-breaker.md)
- [REST — verbos HTTP, semântica de resposta e códigos de status](.github/instructions/microservice-rest-http-semantics-and-status-codes.md)
- [Consistência eventual — Saga / Process Manager, compensações e orquestração](.github/instructions/microservice-saga-process-manager-and-compensation.md)
- [Testes — unidade, integração, contrato e cenários negativos](.github/instructions/microservice-testing-strategy-unit-integration-contract.md)

## Fluxo mínimo (para reduzir variação)

Use BMAD antes de codar:
- Background
- Mission
- Approach
- Delivery/validation

Se houver dúvida de convenção (status codes, validação, erros, resiliência, cache, mensageria), procure uma instruction específica e cite o ficheiro usado.
