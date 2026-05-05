# Simulação básica — cenários via MCP STDIO

## Escopo do teste

- Fonte de instrução local lida: `planning/plano-visual-studio-copilot-chat/copilot-instructions.md`.
- Corpus utilizado no MCP STDIO: `fixtures/instructions` (corpus real informado).
- Fluxo aplicado em cada cenário:
  1. `corporate_instructions_get_context_triggers`
  2. `corporate_instructions_resolve_instruction_context`
  3. `corporate_instructions_get_instructions_batch` (ids selecionados)
- Este documento é apenas simulação de consumo de instruções (sem implementação de código).

## Resultado transversal observado

- Em todos os cenários, `get_context_triggers` retornou:
  - `scenario_id = plan-crosscutting-async-migration`
  - `execution_mode = stop_and_request_human_input`
  - `stop_required = true`
  - `stop_reasons = [external_integration_without_evidence]`
- Leitura compatível com as stop rules locais: sem evidência de integração/infra no repo, o agente deve pedir confirmação humana antes de impor stack.

---

## Cenário 1 — Regras para implementar observabilidade

**Pergunta:** "Preciso saber quais são as regras para implementar observabilidade"

**Policies/references selecionadas (top):**
- `microservice-opentelemetry-correlation-and-health` (policy)
- `microservice-clean-architecture-guardrails` (policy)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy)
- `microservice-rest-http-semantics-and-status-codes` (policy)
- `microservice-saga-process-manager-and-compensation` (reference)

**Síntese de regras recuperadas:**
- Instrumentar tracing com OpenTelemetry para ASP.NET Core e dependências.
- Propagar contexto (`traceparent`/`tracestate`) em chamadas e fluxos assíncronos suportados.
- Logs estruturados com correlação (`TraceId`/`SpanId`), sem PII/segredos.
- Separar health checks de liveness/readiness com dependências críticas no readiness.
- Tratar observabilidade e resiliência como requisito arquitetural, não opcional.

**Evidence gate relevante:**
- `workspace_evidence_required=true` em `microservice-opentelemetry-correlation-and-health`.
- `workspace_signals`: `OpenTelemetry`, `AddOpenTelemetry`, `ActivitySource`, `Meter`, `TracerProvider`, `MapHealthChecks`.
- `on_absence=hypothesis_only` no frontmatter.

**Lacuna detectada:**
- Necessidade de evidência no repo para enforcement forte da policy de observabilidade.

---

## Cenário 2 — Estrutura dos projetos

**Pergunta:** "Como que os projetos são estruturados"

**Policies/references selecionadas (top):**
- `microservice-architecture-layering` (reference)
- `microservice-clean-architecture-guardrails` (policy)
- `microservice-design-principles-solid-performance-types` (reference)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy)
- `microservice-messaging-rabbitmq-publish-consume` (policy)

**Síntese de regras recuperadas:**
- Estrutura recomendada por camadas: `Api`, `Dominio`, `Interfaces`, `Modelo`, `Repositorio`.
- Dependências sempre apontando para dentro (guardrail de Clean Architecture).
- Contratos externos estáveis e segregação de responsabilidades por camada.
- Aplicação pragmática de SOLID, evitando abstração especulativa.
- Planejamento BMAD/spec-driven antes de mudanças relevantes.

**Evidence gate relevante:**
- Parte de arquitetura é `reference`; serve como guia.
- Foi selecionada policy de mensageria com evidence gate (`workspace_evidence_required=true`), mas sem evidência local não deve virar imposição.

**Lacuna detectada:**
- Estrutura detalhada real do repo precisa ser confirmada por leitura factual do código/solução.

---

## Cenário 3 — Como fazer integrações externas

**Pergunta:** "Como que eu consigo fazer integrações externas"

**Policies/references selecionadas (top):**
- `microservice-integration-httpclientfactory-contracts` (policy)
- `microservice-resilience-polly-timeouts-and-circuit-breaker` (policy)
- `microservice-di-options-extensions` (policy)
- `microservice-testing-strategy-unit-integration-contract` (policy)
- `microservice-saga-process-manager-and-compensation` (reference)

**Síntese de regras recuperadas:**
- Usar `IHttpClientFactory` (clientes nomeados/typed) para integrações HTTP.
- Isolar DTO externo na infraestrutura; não vazar para domínio.
- Configurar timeout, retry com backoff/jitter e circuit breaker com critérios claros.
- Centralizar headers/correlação de forma padronizada.
- Definir testes mínimos de unidade, integração e contrato para integrações críticas.

**Evidence gate relevante:**
- `workspace_evidence_required=true` para policies principais de integração/resiliência/DI.
- `on_absence=hypothesis_only` para essas policies.

**Lacuna detectada:**
- Sem sinais concretos de stack de integração no repo, a recomendação deve permanecer hipótese guiada, não imposição.

---

## Cenário 4 — Mensageria padrão RabbitMQ ou Azure ServiceBus

**Pergunta:** "Como funciona o mecanismo de mensageria padrão RabbitMQ ou Azure ServiceBus"

**Policies/references selecionadas (top):**
- `microservice-messaging-rabbitmq-publish-consume` (policy)
- `microservice-saga-process-manager-and-compensation` (reference)
- `microservice-data-access-and-sql-security` (policy, suporte para outbox/consistência)
- `assistant-workflow-bmad-planning-and-controlled-inference` (policy)

**Síntese de regras recuperadas:**
- Contratos de mensagem versionados e compatibilidade explícita.
- `ack` só após processamento idempotente persistido; `nack/requeue` apenas em transitório.
- Uso de DLQ para poison messages e controle de reentrega.
- Propagação de correlação/trace em metadados de mensagem.
- Outbox para publicação acoplada a persistência e consistência eventual.

**Evidence gate relevante:**
- Policy principal de mensageria exige sinais (`RabbitMQ`, `RabbitMQ.Client`, `MassTransit`, `IBus`, etc.).
- `on_absence=hypothesis_only`.

**Lacuna detectada (importante):**
- No corpus atual, a policy específica retornada é de **RabbitMQ**.
- Não houve policy específica de **Azure ServiceBus** nos resultados selecionados.
- Pelo protocolo local, não se deve assumir ServiceBus por inferência sem evidência/policy correspondente.

---

## Conclusão da simulação

- O MCP STDIO respondeu conforme o protocolo local: contexto primeiro, evidence gate e stop rule para integração sem evidência.
- As respostas normativas para os 4 cenários foram recuperadas e sintetizadas com base em batch lido.
- Principais hipóteses/lacunas ficaram explícitas, especialmente para:
  - enforcement de policies com `workspace_evidence_required=true`;
  - ausência de policy específica para Azure ServiceBus no resultado atual.
