# EPIC-09 (preparacao) — Analise de falhas remanescentes e correcao cirurgica de I-02

## Contexto de entrada

- baseline pos-EPIC-08: `8/24`
- casos reprovados: `T01`, `T02`, `T03`, `T04`, `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`, `T16`, `T18`, `T20`, `T21`

## Classificacao caso a caso (estado pre-correcao de I-02)

| Caso | Sintoma | Documento esperado | Documento retornado | Causa provavel | Evidencia |
|---|---|---|---|---|---|
| T01 | Arquitetura contaminada por observabilidade/mensageria no topo | `microservice-domain-interfaces-models-repository` no bundle primario | Topo com `microservice-opentelemetry-correlation-and-health` + `microservice-messaging-rabbitmq-publish-consume` | resíduo de `I-01` | query natural ainda puxa docs transversais sem sinal meta-governance |
| T02 | Query de camadas+DI traz API validation no topo e perde DI options | `microservice-di-options-extensions` | Top-4 com `microservice-api-validation-and-error-contracts` e `microservice-api-openfinance-patterns` | resíduo de `I-01` | falha sem documento meta no top; sintoma de discriminacao lexical ainda fraca |
| T03 | Supporting de arquitetura ausente com meta doc no pool | supporting `microservice-design-principles-solid-performance-types` | `assistant-workflow-bmad-planning-and-controlled-inference` em posicao 5 | `I-02` | documento meta entra em query tecnica de arquitetura |
| T04 | Supporting de clean architecture ausente; authoring aparece no pool | supporting `microservice-clean-architecture-guardrails` | `instruction-authoring-standard` em posicao 7 | inconclusivo | ha ruido meta, mas nao no topo; falha principal e ausencia de supporting esperado |
| T06 | Tracing/correlation roteia para docs de API/error | `microservice-opentelemetry-correlation-and-health` | Top-4 dominado por docs API (`openfinance`, `rest`, `error-catalog`) | `I-04` | lacuna de conectividade observabilidade/integracao |
| T07 | Supporting de DI ausente em health query | supporting `microservice-di-options-extensions` | bundle com docs de arquitetura e meta em posicao 5 | `I-04` | caso de health/readiness sem apoio esperado de DI |
| T08 | Query de metricas HTTP+banco nao traz data-access | `microservice-data-access-and-sql-security` | Top-4 sem data-access; foco em `rest` e `api-error` | `I-04` | cluster observabilidade/dependencias nao alcança SQL como esperado |
| T09 | Integracao externa sem DI options no primario | `microservice-di-options-extensions` | Top-4 com `testing`, `domain`, `architecture` | inconclusivo | sem ruído meta no topo; lacuna parece semantica de cobertura |
| T10 | Doc meta authoring vence indevidamente query tecnica de HttpClientFactory | `microservice-domain-interfaces-models-repository` (primario) | `instruction-authoring-standard` em posicao 2 | `I-02` | meta doc com termos genericos (`client`, `padrao`) supera documento tecnico especifico |
| T11 | Supporting de observabilidade ausente em retry/circuit breaker | supporting `microservice-opentelemetry-correlation-and-health` | Top-4 sem observabilidade | `I-04` | cobertura parcial entre resiliencia e observabilidade |
| T12 | POST idempotencia/timeout sem API validation/error catalog | `microservice-api-validation-and-error-contracts` + supporting de erro | top com resiliencia/rest/saga e meta em posicao 6 | resíduo de `I-01` | query natural ainda favorece docs adjacentes e genericos |
| T13 | Meta workflow sobe para topo em query RabbitMQ | supporting inclui `opentelemetry/testing`; saga deve aparecer antes de meta | `assistant-workflow-bmad...` em posicao 2 (e saga em 3 no resolved) | `I-02` | no search bruto saga estava acima; no resolved meta foi promovido |
| T16 | ProblemDetails sem API error catalog no primario | `microservice-api-error-catalog-baseline` | Top-4 com validation/openfinance/collection/readiness | `I-04` | lacuna de conexao entre contracts e catalogo de erro |
| T18 | Supporting de API error catalog ausente em JWT baseline | supporting `microservice-api-error-catalog-baseline` | top com auth/authorization e docs API adjacentes | `I-04` | cobertura parcial no cluster auth/erro |
| T20 | Segredos/logs nao traz readiness no primario | `microservice-configuration-production-readiness` | top com data-access/opentelemetry/domain/security | `I-04` | readiness ainda subrepresentada em queries security/logging |
| T21 | SQL seguro sem readiness; com authoring no pool | `microservice-configuration-production-readiness` | top com data-access/resilience/domain; `instruction-authoring-standard` em posicao 6 | `I-04` | falha principal e conectividade SQL→readiness; meta aparece como amplificador |

## Evidencia especifica de I-02

### Testes de falha criados antes da correcao

Arquivo: `mcp-instructions-server/tests/test_epic09_i02_meta_governance.py`

1. `test_FAIL_meta_governance_doc_should_not_beat_specific_technical_doc_for_httpclient_query`
2. `test_FAIL_meta_policy_promotion_should_not_outrank_saga_reference_for_rabbitmq_query`
3. `test_FAIL_meta_governance_docs_should_not_be_marked_as_normative_for_technical_query`

Execucao pre-correcao:

- `pytest -q tests/test_epic09_i02_meta_governance.py` -> `3 failed`

## Correcao aplicada (escopo I-02)

Arquivo alterado: `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`

- classificador leve de documento meta/governance por tags/ID;
- deteccao de query tecnica vs query meta-governance;
- em query tecnica:
  - evita promover documento meta como `ensure_normative_policy`;
  - adia docs meta no preenchimento de candidatos;
  - trata docs meta como `supporting` (nao `normative`) no `actionable_context`.

## Validacao pos-correcao

- `pytest -q tests/test_epic09_i02_meta_governance.py` -> `3 passed`
- `pytest -q` -> `149 passed, 1 skipped`
- suite 24 casos (stdio) -> `8/24` (mesmo placar), com reducao do ruido meta no topo em `T10` e `T13`.

## Conclusao operacional

- `I-02` estava confirmado por evidencia direta e foi mitigado nos cenarios alvo.
- O placar agregado nao subiu nesta iteracao, indicando que o gargalo remanescente dominante da suite permanece em `I-04`/lacunas de cobertura semantica entre dominios tecnicos.

