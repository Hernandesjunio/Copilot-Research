# Testes basicos para montagem de contexto (fixtures)

Objetivo: validar se as tools de contexto MCP estao selecionando as instructions corretas a partir de perguntas em linguagem natural.

Corpus alvo: `fixtures/instructions`.

## Como avaliar cada teste

- Entrada: prompt de usuario (evidence opcional).
- Saida esperada: IDs que devem aparecer em `resolve_instruction_context.selected_ids`.
- Validacao minima:
  - os `primary_ids` devem aparecer entre os primeiros IDs retornados;
  - `get_instructions_batch` deve trazer os mesmos IDs;
  - quando uma instruction exigir `workspace_evidence_required: true` e nao houver evidencia, aceitar `hypothesis_only` em `validate_applicability`;
  - nao priorizar IDs claramente fora do tema da pergunta.

---

## Suite (24 testes)

### T01 - Estrutura de projeto (baseline)
- **Entrada**: "me mostre como o projeto deve ser estruturado"
- **Saida esperada (primary_ids)**:
  - `microservice-architecture-layering`
  - `microservice-clean-architecture-guardrails`
  - `microservice-domain-interfaces-models-repository`
- **Saida esperada (supporting_ids)**:
  - `microservice-design-principles-solid-performance-types`
  - `microservice-di-options-extensions`
- **Nao priorizar**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-messaging-rabbitmq-publish-consume`

### T02 - Estrutura por camadas + DI
- **Entrada**: "qual a forma correta de separar Api, Dominio, Interfaces e Repositorio com DI?"
- **Saida esperada (primary_ids)**:
  - `microservice-architecture-layering`
  - `microservice-domain-interfaces-models-repository`
  - `microservice-di-options-extensions`
- **Saida esperada (supporting_ids)**:
  - `microservice-clean-architecture-guardrails`

### T03 - Clean Architecture em microservico
- **Entrada**: "como aplicar clean architecture sem acoplar dominio a infraestrutura?"
- **Saida esperada (primary_ids)**:
  - `microservice-clean-architecture-guardrails`
  - `microservice-architecture-layering`
  - `microservice-domain-interfaces-models-repository`
- **Saida esperada (supporting_ids)**:
  - `microservice-design-principles-solid-performance-types`

### T04 - Convencoes de extensoes e options
- **Entrada**: "como organizar AddApiExtensions, AddDomainExtensions e configuracoes por options?"
- **Saida esperada (primary_ids)**:
  - `microservice-di-options-extensions`
  - `microservice-configuration-production-readiness`
  - `microservice-architecture-layering`
- **Saida esperada (supporting_ids)**:
  - `microservice-clean-architecture-guardrails`

### T05 - Observabilidade (baseline)
- **Entrada**: "me informe como que a observabilidade deve ser implementada"
- **Saida esperada (primary_ids)**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-configuration-production-readiness`
- **Saida esperada (supporting_ids)**:
  - `microservice-api-openfinance-patterns`
  - `microservice-clean-architecture-guardrails`
- **Nao priorizar**:
  - `microservice-api-collection-resources-pagination-filters`

### T06 - Tracing e correlacao
- **Entrada**: "como propagar traceparent e correlation id entre API e chamadas externas?"
- **Saida esperada (primary_ids)**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-integration-httpclientfactory-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`

### T07 - Health checks live/ready
- **Entrada**: "como separar /health/live de /health/ready em servico .NET?"
- **Saida esperada (primary_ids)**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-configuration-production-readiness`
- **Saida esperada (supporting_ids)**:
  - `microservice-di-options-extensions`

### T08 - Metricas de dependencia externa
- **Entrada**: "quais metricas e spans devo coletar para dependencias HTTP e banco?"
- **Saida esperada (primary_ids)**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-data-access-and-sql-security`
  - `microservice-integration-httpclientfactory-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`

### T09 - Integracao externa (baseline)
- **Entrada**: "como fazer integração externa"
- **Saida esperada (primary_ids)**:
  - `microservice-integration-httpclientfactory-contracts`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-di-options-extensions`
- **Saida esperada (supporting_ids)**:
  - `microservice-testing-strategy-unit-integration-contract`
  - `microservice-configuration-production-readiness`

### T10 - HttpClientFactory com typed client
- **Entrada**: "qual padrao para typed client com IHttpClientFactory e mapping de DTO externo?"
- **Saida esperada (primary_ids)**:
  - `microservice-integration-httpclientfactory-contracts`
  - `microservice-domain-interfaces-models-repository`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`

### T11 - Retry e circuit breaker
- **Entrada**: "como configurar retry com backoff e circuit breaker para API de pagamentos?"
- **Saida esperada (primary_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-opentelemetry-correlation-and-health`

### T12 - Timeout e idempotencia em POST
- **Entrada**: "posso aplicar retry em POST? como tratar idempotencia e timeout?"
- **Saida esperada (primary_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
  - `microservice-api-validation-and-error-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-api-error-catalog-baseline`

### T13 - Mensageria RabbitMQ
- **Entrada**: "como padronizar publish/consume com rabbitmq, dlq e idempotencia?"
- **Saida esperada (primary_ids)**:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-saga-process-manager-and-compensation`
- **Saida esperada (supporting_ids)**:
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-testing-strategy-unit-integration-contract`

### T14 - Saga e compensacao
- **Entrada**: "quando usar saga/process manager e como modelar compensacoes?"
- **Saida esperada (primary_ids)**:
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-messaging-rabbitmq-publish-consume`
- **Saida esperada (supporting_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-opentelemetry-correlation-and-health`

### T15 - Validacao 400 vs 422
- **Entrada**: "quando retornar 400 e quando retornar 422 em validacao de entrada?"
- **Saida esperada (primary_ids)**:
  - `microservice-api-validation-and-error-contracts`
  - `microservice-api-error-catalog-baseline`
  - `microservice-rest-http-semantics-and-status-codes`
- **Saida esperada (supporting_ids)**:
  - `microservice-api-openfinance-patterns`

### T16 - Contrato de erro e ProblemDetails
- **Entrada**: "como padronizar ProblemDetails sem try/catch duplicado nos endpoints?"
- **Saida esperada (primary_ids)**:
  - `microservice-api-validation-and-error-contracts`
  - `microservice-api-openfinance-patterns`
  - `microservice-api-error-catalog-baseline`
- **Saida esperada (supporting_ids)**:
  - `microservice-rest-http-semantics-and-status-codes`

### T17 - API de colecoes
- **Entrada**: "como implementar paginacao, filtro e ordenacao em colecoes sem quebrar contrato?"
- **Saida esperada (primary_ids)**:
  - `microservice-api-collection-resources-pagination-filters`
  - `microservice-rest-http-semantics-and-status-codes`
  - `microservice-api-openfinance-patterns`
- **Saida esperada (supporting_ids)**:
  - `microservice-api-validation-and-error-contracts`

### T18 - Autenticacao JWT
- **Entrada**: "qual baseline para autenticação JWT bearer e claims authorization?"
- **Saida esperada (primary_ids)**:
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `example-security-baseline`
- **Saida esperada (supporting_ids)**:
  - `microservice-api-error-catalog-baseline`

### T19 - Autorizacao por ownership
- **Entrada**: "como validar escopo de recurso e registrar auditoria de autorizacao?"
- **Saida esperada (primary_ids)**:
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-auth-jwt-bearer-and-authorization`
- **Saida esperada (supporting_ids)**:
  - `example-security-baseline`
  - `microservice-opentelemetry-correlation-and-health`

### T20 - Segredos e dados sensiveis
- **Entrada**: "como tratar segredos e evitar vazamento em logs e repositorio?"
- **Saida esperada (primary_ids)**:
  - `example-security-baseline`
  - `microservice-configuration-production-readiness`
  - `microservice-opentelemetry-correlation-and-health`
- **Saida esperada (supporting_ids)**:
  - `artifact-encoding-line-endings-and-unicode`

### T21 - Acesso a dados seguro
- **Entrada**: "qual padrao para queries SQL seguras com timeout e transacao?"
- **Saida esperada (primary_ids)**:
  - `microservice-data-access-and-sql-security`
  - `microservice-configuration-production-readiness`
- **Saida esperada (supporting_ids)**:
  - `microservice-domain-interfaces-models-repository`
  - `microservice-testing-strategy-unit-integration-contract`

### T22 - Estrategia de testes
- **Entrada**: "como montar estrategia de testes unitario, integracao e contrato para microservico?"
- **Saida esperada (primary_ids)**:
  - `microservice-testing-strategy-unit-integration-contract`
  - `microservice-api-validation-and-error-contracts`
  - `microservice-integration-httpclientfactory-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-messaging-rabbitmq-publish-consume`

### T23 - Cache em leitura
- **Entrada**: "quando usar imemorycache, ttl e invalidacao em API de consulta?"
- **Saida esperada (primary_ids)**:
  - `microservice-caching-imemorycache-policy`
  - `microservice-api-collection-resources-pagination-filters`
- **Saida esperada (supporting_ids)**:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-configuration-production-readiness`

### T24 - Pergunta hibrida (arquitetura + observabilidade + integracao)
- **Entrada**: "quero estruturar o projeto, instrumentar observabilidade e integrar API externa com resiliencia"
- **Saida esperada (primary_ids)**:
  - `microservice-architecture-layering`
  - `microservice-opentelemetry-correlation-and-health`
  - `microservice-integration-httpclientfactory-contracts`
- **Saida esperada (supporting_ids)**:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-clean-architecture-guardrails`
  - `microservice-di-options-extensions`
- **Regra de ouro**:
  - os 3 temas devem aparecer no top-5 de `selected_ids`;
  - se vier apenas 1 tema dominante, considerar roteamento insuficiente.

---

## Modelo de saida esperado por teste (template)

Use este formato para registrar execucao real e comparar com o esperado:

```json
{
  "test_id": "TXX",
  "input": "pergunta do usuario",
  "tool_outputs": {
    "get_context_triggers": {
      "scenario_id": "<valor>",
      "recommended_execution_mode": "<valor>",
      "stop_required": true,
      "stop_reasons": ["..."]
    },
    "resolve_instruction_context": {
      "selected_ids": ["id1", "id2", "id3", "id4", "id5"],
      "gaps": ["..."]
    },
    "get_instructions_batch": {
      "ids_returned": ["id1", "id2", "id3", "id4", "id5"]
    },
    "validate_applicability": {
      "by_instruction": [
        { "id": "id1", "decision": "applicable|hypothesis_only|non_applicable|blocked_by_missing_evidence" }
      ]
    }
  },
  "assertions": {
    "contains_all_primary_ids": true,
    "contains_at_least_one_supporting_id": true,
    "does_not_prioritize_unrelated_ids": true
  },
  "final_result": "pass|fail"
}
```

## Criterio de aprovacao da suite

- **Passa** se pelo menos 21/24 testes cumprirem:
  - 100% dos `primary_ids` presentes em `selected_ids`;
  - pelo menos 1 `supporting_id` presente;
  - nenhum ID explicitamente "nao priorizar" entre os 2 primeiros.
- **Falha** se houver vies sistematico:
  - observabilidade roteando para API/colecoes;
  - arquitetura roteando para mensageria/seguranca sem gatilho textual;
  - integracao externa sem trazer `httpclientfactory` + `resilience`.
