# Simulação básica v2 — cenários via MCP STDIO

## Objetivo

Validar os 4 cenários com o fluxo completo da implementação atual (P0/P1/P2), corrigindo os problemas da v1:
- gatilhos por cenário (sem viés global);
- evidence gate formal com `validate_applicability`;
- consolidação operacional com `build_compliance_matrix`.

## Fluxo executado (STDIO real)

1. `corporate_instructions_get_context_triggers`
2. `corporate_instructions_resolve_instruction_context`
3. `corporate_instructions_get_instructions_batch`
4. `corporate_instructions_validate_applicability`
5. `corporate_instructions_build_compliance_matrix`

Corpus: `C:\_projeto\Copilot-Research\fixtures\instructions`

---

## Cenário — Preciso saber quais são as regras para implementar observabilidade

**Entrada (resumo):**
- query: `observabilidade opentelemetry correlation health checks tracing metrics`
- target_artifact.path: `Api/Endpoints/ClienteEndpoints.cs`
- workspace_evidence: `["OpenTelemetry", "AddOpenTelemetry"]`

**Saída — get_context_triggers:**
- scenario_id: `plan-crosscutting-async-migration`
- recommended_execution_mode: `stop_and_request_human_input`
- stop_required: `True`
- stop_reasons: `["new_infrastructure_without_evidence"]`

**Saída — resolve_instruction_context:**
- selected_ids: `["microservice-opentelemetry-correlation-and-health", "microservice-clean-architecture-guardrails", "microservice-saga-process-manager-and-compensation", "assistant-workflow-bmad-planning-and-controlled-inference", "microservice-rest-http-semantics-and-status-codes"]`
- implementation_brief: Normative baseline: `microservice-opentelemetry-correlation-and-health`, `microservice-clean-architecture-guardrails`, `assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-rest-http-semantics-and-status-codes`. Supporting references: `microservice-saga-process-manager-and-compensation`.
- gaps: `["Some selected policies require workspace evidence before being asserted strongly: microservice-opentelemetry-correlation-and-health, microservice-saga-process-manager-and-compensation."]`

**Saída — get_instructions_batch (resumo):**
- `microservice-opentelemetry-correlation-and-health` (policy, priority=high, evidence_required=True)
- `microservice-clean-architecture-guardrails` (policy, priority=high, evidence_required=False)
- `microservice-saga-process-manager-and-compensation` (reference, priority=high, evidence_required=True)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy, priority=high, evidence_required=False)
- `microservice-rest-http-semantics-and-status-codes` (policy, priority=high, evidence_required=False)

**Saída — validate_applicability:**
- `microservice-opentelemetry-correlation-and-health` -> `applicable` | reason: Found positive workspace signals with no explicit contradictory evidence.
- `microservice-clean-architecture-guardrails` -> `applicable` | reason: Instruction is in scope and does not require workspace evidence.
- `microservice-saga-process-manager-and-compensation` -> `hypothesis_only` | reason: Reference can inform analysis, but is not enforceable as strong policy.
- `assistant-workflow-bmad-planning-and-controlled-inference` -> `applicable` | reason: Instruction is in scope and does not require workspace evidence.
- `microservice-rest-http-semantics-and-status-codes` -> `non_applicable` | reason: Artifact path is out of declared scope.
- summary.by_applicability: `{"applicable": 3, "blocked_by_missing_evidence": 0, "hypothesis_only": 1, "non_applicable": 1}`

**Saída — build_compliance_matrix:**
- `microservice-opentelemetry-correlation-and-health` -> status `conformant` | decision `applicable`
- `microservice-clean-architecture-guardrails` -> status `conformant` | decision `applicable`
- `microservice-saga-process-manager-and-compensation` -> status `not_enforceable` | decision `hypothesis_only`
- `assistant-workflow-bmad-planning-and-controlled-inference` -> status `conformant` | decision `applicable`
- `microservice-rest-http-semantics-and-status-codes` -> status `not_applicable` | decision `non_applicable`
- summary: `{"conformant": 3, "partial_conformance": 0, "non_conformance": 0, "not_enforceable": 1, "not_applicable": 1, "insufficient_evidence": 0}`

**Decisão simulada:**
- Se `stop_required=true`, pedir input humano antes de impor stack/contrato novo.
- `not_enforceable`/`hypothesis_only` mantém recomendação como hipótese guiada.
- `conformant`/`partial_conformance` indica estado operacional após observações fornecidas.

---

## Cenário — Como que os projetos são estruturados

**Entrada (resumo):**
- query: `estrutura de projeto arquitetura em camadas clean architecture`
- target_artifact.path: `Api/Endpoints/ClienteEndpoints.cs`
- workspace_evidence: `[]`

**Saída — get_context_triggers:**
- scenario_id: `plan-crosscutting-async-migration`
- recommended_execution_mode: `plan_only`
- stop_required: `False`
- stop_reasons: `[]`

**Saída — resolve_instruction_context:**
- selected_ids: `["microservice-architecture-layering", "microservice-clean-architecture-guardrails", "microservice-design-principles-solid-performance-types", "assistant-workflow-bmad-planning-and-controlled-inference", "microservice-messaging-rabbitmq-publish-consume"]`
- implementation_brief: Normative baseline: `microservice-clean-architecture-guardrails`, `assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-messaging-rabbitmq-publish-consume`. Supporting references: `microservice-architecture-layering`, `microservice-design-principles-solid-performance-types`.
- gaps: `["Some selected policies require workspace evidence before being asserted strongly: microservice-messaging-rabbitmq-publish-consume."]`

**Saída — get_instructions_batch (resumo):**
- `microservice-architecture-layering` (reference, priority=high, evidence_required=False)
- `microservice-clean-architecture-guardrails` (policy, priority=high, evidence_required=False)
- `microservice-design-principles-solid-performance-types` (reference, priority=medium, evidence_required=False)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy, priority=high, evidence_required=False)
- `microservice-messaging-rabbitmq-publish-consume` (policy, priority=high, evidence_required=True)

**Saída — validate_applicability:**
- `microservice-architecture-layering` -> `hypothesis_only` | reason: Reference can inform analysis, but is not enforceable as strong policy.
- `microservice-clean-architecture-guardrails` -> `applicable` | reason: Instruction is in scope and does not require workspace evidence.
- `microservice-design-principles-solid-performance-types` -> `hypothesis_only` | reason: Reference can inform analysis, but is not enforceable as strong policy.
- `assistant-workflow-bmad-planning-and-controlled-inference` -> `applicable` | reason: Instruction is in scope and does not require workspace evidence.
- `microservice-messaging-rabbitmq-publish-consume` -> `hypothesis_only` | reason: No sufficient positive signal found; using instruction on_absence behavior.
- summary.by_applicability: `{"applicable": 2, "blocked_by_missing_evidence": 0, "hypothesis_only": 3, "non_applicable": 0}`

**Saída — build_compliance_matrix:**
- `microservice-architecture-layering` -> status `not_enforceable` | decision `hypothesis_only`
- `microservice-clean-architecture-guardrails` -> status `conformant` | decision `applicable`
- `microservice-design-principles-solid-performance-types` -> status `not_enforceable` | decision `hypothesis_only`
- `assistant-workflow-bmad-planning-and-controlled-inference` -> status `conformant` | decision `applicable`
- `microservice-messaging-rabbitmq-publish-consume` -> status `not_enforceable` | decision `hypothesis_only`
- summary: `{"conformant": 2, "partial_conformance": 0, "non_conformance": 0, "not_enforceable": 3, "not_applicable": 0, "insufficient_evidence": 0}`

**Decisão simulada:**
- Se `stop_required=true`, pedir input humano antes de impor stack/contrato novo.
- `not_enforceable`/`hypothesis_only` mantém recomendação como hipótese guiada.
- `conformant`/`partial_conformance` indica estado operacional após observações fornecidas.

---

## Cenário — Como que eu consigo fazer integrações externas

**Entrada (resumo):**
- query: `integrações externas httpclientfactory contracts resiliencia`
- target_artifact.path: `Api/Endpoints/ClienteEndpoints.cs`
- workspace_evidence: `["IHttpClientFactory", "AddHttpClient", {"value": "Polly", "evidence_type": "positive"}]`

**Saída — get_context_triggers:**
- scenario_id: `plan-crosscutting-async-migration`
- recommended_execution_mode: `stop_and_request_human_input`
- stop_required: `True`
- stop_reasons: `["new_infrastructure_without_evidence", "external_integration_without_evidence"]`

**Saída — resolve_instruction_context:**
- selected_ids: `["microservice-integration-httpclientfactory-contracts", "microservice-resilience-polly-timeouts-and-circuit-breaker", "microservice-saga-process-manager-and-compensation", "microservice-di-options-extensions", "microservice-testing-strategy-unit-integration-contract"]`
- implementation_brief: Normative baseline: `microservice-integration-httpclientfactory-contracts`, `microservice-resilience-polly-timeouts-and-circuit-breaker`, `microservice-di-options-extensions`, `microservice-testing-strategy-unit-integration-contract`. Supporting references: `microservice-saga-process-manager-and-compensation`.
- gaps: `["Some selected policies require workspace evidence before being asserted strongly: microservice-di-options-extensions, microservice-integration-httpclientfactory-contracts, microservice-resilience-polly-timeouts-and-circuit-breaker, microservice-saga-process-manager-and-compensation."]`

**Saída — get_instructions_batch (resumo):**
- `microservice-integration-httpclientfactory-contracts` (policy, priority=high, evidence_required=True)
- `microservice-resilience-polly-timeouts-and-circuit-breaker` (policy, priority=high, evidence_required=True)
- `microservice-saga-process-manager-and-compensation` (reference, priority=high, evidence_required=True)
- `microservice-di-options-extensions` (policy, priority=medium, evidence_required=True)
- `microservice-testing-strategy-unit-integration-contract` (policy, priority=medium, evidence_required=False)

**Saída — validate_applicability:**
- `microservice-integration-httpclientfactory-contracts` -> `applicable` | reason: Found positive workspace signals with no explicit contradictory evidence.
- `microservice-resilience-polly-timeouts-and-circuit-breaker` -> `applicable` | reason: Found positive workspace signals with no explicit contradictory evidence.
- `microservice-saga-process-manager-and-compensation` -> `hypothesis_only` | reason: Reference can inform analysis, but is not enforceable as strong policy.
- `microservice-di-options-extensions` -> `hypothesis_only` | reason: No sufficient positive signal found; using instruction on_absence behavior.
- `microservice-testing-strategy-unit-integration-contract` -> `non_applicable` | reason: Artifact path is out of declared scope.
- summary.by_applicability: `{"applicable": 2, "blocked_by_missing_evidence": 0, "hypothesis_only": 2, "non_applicable": 1}`

**Saída — build_compliance_matrix:**
- `microservice-integration-httpclientfactory-contracts` -> status `partial_conformance` | decision `applicable`
- `microservice-resilience-polly-timeouts-and-circuit-breaker` -> status `partial_conformance` | decision `applicable`
- `microservice-saga-process-manager-and-compensation` -> status `not_enforceable` | decision `hypothesis_only`
- `microservice-di-options-extensions` -> status `not_enforceable` | decision `hypothesis_only`
- `microservice-testing-strategy-unit-integration-contract` -> status `not_applicable` | decision `non_applicable`
- summary: `{"conformant": 0, "partial_conformance": 2, "non_conformance": 0, "not_enforceable": 2, "not_applicable": 1, "insufficient_evidence": 0}`

**Decisão simulada:**
- Se `stop_required=true`, pedir input humano antes de impor stack/contrato novo.
- `not_enforceable`/`hypothesis_only` mantém recomendação como hipótese guiada.
- `conformant`/`partial_conformance` indica estado operacional após observações fornecidas.

---

## Cenário — Como funciona o mecanismo de mensageria padrão RabbitMQ ou Azure ServiceBus

**Entrada (resumo):**
- query: `mensageria rabbitmq azure servicebus publish consume outbox`
- target_artifact.path: `Api/Endpoints/ClienteEndpoints.cs`
- workspace_evidence: `["RabbitMQ", "IBus", {"value": "MassTransit", "evidence_type": "negative"}]`

**Saída — get_context_triggers:**
- scenario_id: `plan-crosscutting-async-migration`
- recommended_execution_mode: `stop_and_request_human_input`
- stop_required: `True`
- stop_reasons: `["new_infrastructure_without_evidence", "external_integration_without_evidence"]`

**Saída — resolve_instruction_context:**
- selected_ids: `["microservice-messaging-rabbitmq-publish-consume", "assistant-workflow-bmad-planning-and-controlled-inference", "microservice-saga-process-manager-and-compensation", "microservice-data-access-and-sql-security", "instruction-authoring-standard"]`
- implementation_brief: Normative baseline: `microservice-messaging-rabbitmq-publish-consume`, `assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-data-access-and-sql-security`, `instruction-authoring-standard`. Supporting references: `microservice-saga-process-manager-and-compensation`.
- gaps: `["Some selected policies require workspace evidence before being asserted strongly: microservice-data-access-and-sql-security, microservice-messaging-rabbitmq-publish-consume, microservice-saga-process-manager-and-compensation."]`

**Saída — get_instructions_batch (resumo):**
- `microservice-messaging-rabbitmq-publish-consume` (policy, priority=high, evidence_required=True)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy, priority=high, evidence_required=False)
- `microservice-saga-process-manager-and-compensation` (reference, priority=high, evidence_required=True)
- `microservice-data-access-and-sql-security` (policy, priority=high, evidence_required=True)
- `instruction-authoring-standard` (policy, priority=medium, evidence_required=False)

**Saída — validate_applicability:**
- `microservice-messaging-rabbitmq-publish-consume` -> `hypothesis_only` | reason: Evidence is mixed (positive and blocking), so enforcement remains conservative.
- `assistant-workflow-bmad-planning-and-controlled-inference` -> `applicable` | reason: Instruction is in scope and does not require workspace evidence.
- `microservice-saga-process-manager-and-compensation` -> `hypothesis_only` | reason: Reference can inform analysis, but is not enforceable as strong policy.
- `microservice-data-access-and-sql-security` -> `hypothesis_only` | reason: No sufficient positive signal found; using instruction on_absence behavior.
- `instruction-authoring-standard` -> `non_applicable` | reason: Artifact path is out of declared scope.
- summary.by_applicability: `{"applicable": 1, "blocked_by_missing_evidence": 0, "hypothesis_only": 3, "non_applicable": 1}`

**Saída — build_compliance_matrix:**
- `microservice-messaging-rabbitmq-publish-consume` -> status `not_enforceable` | decision `hypothesis_only`
- `assistant-workflow-bmad-planning-and-controlled-inference` -> status `partial_conformance` | decision `applicable`
- `microservice-saga-process-manager-and-compensation` -> status `not_enforceable` | decision `hypothesis_only`
- `microservice-data-access-and-sql-security` -> status `not_enforceable` | decision `hypothesis_only`
- `instruction-authoring-standard` -> status `not_applicable` | decision `non_applicable`
- summary: `{"conformant": 0, "partial_conformance": 1, "non_conformance": 0, "not_enforceable": 3, "not_applicable": 1, "insufficient_evidence": 0}`

**Decisão simulada:**
- Se `stop_required=true`, pedir input humano antes de impor stack/contrato novo.
- `not_enforceable`/`hypothesis_only` mantém recomendação como hipótese guiada.
- `conformant`/`partial_conformance` indica estado operacional após observações fornecidas.

---

## Problemas da v1 e correções aplicadas na v2

1. Evidence gate apenas descritivo -> corrigido com chamada real de `validate_applicability`.
2. Compliance sem estado formal -> corrigido com `build_compliance_matrix`.
3. Gatilhos enviesados para todos os cenários -> corrigido com payload específico por cenário em `get_context_triggers`.
4. Falta de trilha de entrada/saída -> corrigido com seção explícita de input/output por tool em cada cenário.

## Etapas sugeridas para ajustes de unit tests e smoke tests

- Unit tests (`tests/test_epic05_tools.py`):
  - adicionar casos de `validate_applicability` com evidência mista (`positive` + `negative`) para garantir `hypothesis_only`.
  - adicionar casos com múltiplos ids e verificação de `summary.by_applicability`.
  - adicionar matrix com observações por múltiplas instructions e assert de agregação de `summary`.
- Smoke tests (`tests/smoke_test.py`):
  - criar cenário multi-tool encadeado (`resolve` -> `batch` -> `validate_applicability` -> `build_compliance_matrix`).
  - validar explicitamente que cenário sem policy específica (ex.: Azure ServiceBus) não força stack por inferência.
- Integração STDIO (`tests/integration_mcp_stdio_test.py`):
  - ampliar cobertura para pelo menos um caso `stop_required=false` e outro `stop_required=true` com payloads distintos.
  - validar contratos mínimos de saída (chaves obrigatórias) para `validate_applicability` e `build_compliance_matrix`.
