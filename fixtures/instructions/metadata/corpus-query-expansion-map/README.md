# Corpus Query Expansion Map

Mapa modular de expansão de query (ADR-002). Cada ficheiro `*.yaml` declara **um** `domain` e uma lista `entries` com `canonical`, `aliases`, `strong_terms`, `weak_terms`, `contexts` (opcional) e `applies_to` (opcional).

## Ficheiros (fixture)

| Ficheiro | Conteúdo (resumo) |
|----------|-------------------|
| `api.yaml` | REST, paginação, ProblemDetails, catálogos de erro, semântica HTTP |
| `architecture.yaml` | Camadas, DDD, SOLID, guardrails |
| `caching.yaml` | Cache em memória, DI de cache |
| `configuration.yaml` | Options, feature flags |
| `core.yaml` | Transversal: encoding, EOL, UTF-8 |
| `dns.yaml` | Resolução DNS, retry (sem token `retry` solto no domínio `dns` além de `dns-retry` em alias) |
| `dotnet.yaml` | C#, testes, DI, options |
| `governance.yaml` | BMAD, meta-governação |
| `integration.yaml` | HttpClient, integração, sagas |
| `messaging.yaml` | Filas, RabbitMQ, sagas, contextos activáveis |
| `observability.yaml` | OpenTelemetry, health, métricas |
| `persistence.yaml` | SQL, Dapper, EF, transacções |
| `resilience.yaml` | Polly, circuit breaker, timeouts |
| `security.yaml` | JWT, segredos, âmbito de recursos |
| `validation.yaml` | Validação, códigos HTTP 400/422 |

Ficheiros legado `*.yml` (schema antigo com `namespace` + `terms`) foram **mesclados** nestes `*.yaml` e removidos.

## Loader

O servidor carrega **apenas** `metadata/corpus-query-expansion-map/*.yaml` (ordenados). Se o directório estiver vazio, a expansão fica desactivada.

## `contexts`

Lista de regras com `activation_terms`, `applies_to` (globs) e `terms` — ver `mcp-instructions-server/corporate_instructions_mcp/expansion.py` (`ContextRule`).
