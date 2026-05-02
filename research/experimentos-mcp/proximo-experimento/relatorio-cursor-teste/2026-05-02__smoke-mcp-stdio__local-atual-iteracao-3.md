# Smoke test MCP stdio — local atual (iteração 3)

## Objetivo

Executar uma terceira iteração do smoke test MCP stdio contra a versão local atual do `corporate_instructions_mcp`, preservando as queries-base das rodadas anteriores e adicionando probes específicos para os itens `M16`, `M17`, `M18` e `M22`.

## Configuração da rodada

- Data: `2026-05-02`
- Tipo: `MCP stdio`
- Servidor executado: `python -m corporate_instructions_mcp`
- Diretório de execução: `c:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `c:\_projeto\Copilot-Research\fixtures\instructions`
- Telemetria: `CORPORATE_INSTRUCTIONS_TELEMETRY=minimal`
- Validação operacional: `stdio` real; não houve execução headless ponta a ponta de agente

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
- `fallback_suggestions`: 1 sugestão

### `observabilidade correlation tracing`

- `microservice-opentelemetry-correlation-and-health`
- `microservice-saga-process-manager-and-compensation`
- `microservice-clean-architecture-guardrails`
- `search_confidence: 1.0`
- `fallback_suggestions: []`

## Probes de alto esforço

### `M16` — `resolve_instruction_context`

#### Query `retry DNS polly`

- `selected_ids`:
  - `dns-retry-pattern`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
- `normative_ids`:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
- `supporting_ids`:
  - `dns-retry-pattern`
- `section_focus`: `polly`

Leitura:

- a tool deixou de ser apenas um empacotamento de `search` + `batch`
- agora há seleção explícita, separação entre baseline normativo e referência de apoio, e foco de seção para reduzir atrito no consumo imediato

#### Query `mensageria outbox`

- `selected_ids`:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-data-access-and-sql-security`
  - `microservice-saga-process-manager-and-compensation`
- `normative_ids`:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-data-access-and-sql-security`
- `supporting_ids`:
  - `microservice-saga-process-manager-and-compensation`
- `section_focus`: `mensageria`

Leitura:

- a composição já devolve um pacote mais acionável para implementação de outbox/mensageria
- a distinção entre policy e reference ficou observável no contrato

### `M17` — `get_normative_checklist`

#### Cenário `mensageria_outbox`

- `total_items: 5`
- `required_items: 3`
- `recommended_items: 2`
- `required_items_covered: 3`
- `implementation_readiness: ready`
- itens:
  - `transactional_outbox`
  - `idempotent_consumers`
  - `retry_and_dead_letter`
  - `traceability`
  - `delivery_tests`

#### Cenário `security_baseline`

- `total_items: 4`
- `required_items: 2`
- `recommended_items: 2`
- `required_items_covered: 2`
- `implementation_readiness: ready`
- itens:
  - `secret_handling`
  - `jwt_validation`
  - `resource_scope_audit`
  - `error_leakage`

Leitura:

- o checklist agora vem estruturado por cenário, com `requirement_level`, `support_ids`, `evidence_ids`, `verification` e leitura de prontidão
- para consumo por cliente/agente, isso reduz bastante a lacuna entre “documentos relevantes” e “o que preciso implementar/verificar”

### `M18` — `detect_instruction_conflicts`

#### `dns-retry-pattern` vs `microservice-resilience-polly-timeouts-and-circuit-breaker`

- `potential_conflict: true`
- `severity: low`
- `relationship_reason: scope_overlap_with_precedence`
- `winner_id: microservice-resilience-polly-timeouts-and-circuit-breaker`
- precedência explicada por:
  - `scope`: mesmo escopo
  - `kind`: `policy` vence `reference`
  - `priority`: empate em `high`
- `agent_guidance`: usar a policy como baseline normativo e o DNS retry como apoio

#### `microservice-auth-jwt-bearer-and-authorization` vs `microservice-authorization-resource-scope-and-audit`

- `potential_conflict: true`
- `severity: medium`
- `relationship_reason: same_scope_same_kind`
- sem vencedor automático por:
  - mesmo `scope`
  - mesmo `kind`
  - mesma `priority`
- `agent_guidance`: combinar ambos e escalar para instructions locais se surgir ambiguidade concreta

Leitura:

- a resposta ficou claramente mais útil para cliente/agente do que uma mera lista de ids
- o contrato agora distingue melhor “há precedência clara” vs “não há vencedor automático”

### `M22` — painel de qualidade por release

Relatório gerado a partir da telemetria desta própria rodada:

- `events_total: 18`
- `total_completed_calls: 16`
- `search_completed_calls: 8`
- `tool_failure_rate: 0.0`
- `retry_rate: 0.0625`
- `zero_result_rate: 0.0`
- `low_confidence_rate: 0.0`
- `avg_search_confidence: 0.8347`
- `warnings: []`

Breakdown por tool:

- `search_instructions`: `8` calls, `retry_rate: 0.125`, `avg_latency_ms: 44.75`
- `resolve_instruction_context`: `2` calls, `avg_latency_ms: 42.0`
- `get_normative_checklist`: `2` calls, `avg_latency_ms: 13.0`
- `detect_instruction_conflicts`: `2` calls, `avg_latency_ms: 0.5`

Leitura:

- a telemetria passou a refletir também as tools compostas, não só `search`/`batch`
- o script do painel agora produz saída mais útil para release, com `summary`, `counts`, `rates`, `search_quality`, `tool_breakdown`, `warnings` e suporte a comparação com baseline

## Leitura inicial

Esta terceira iteração preservou integralmente o comportamento das queries-base e, ao mesmo tempo, tornou os itens de alto valor/alto esforço observáveis no contrato real:

- `M16` agora entrega contexto consolidado e acionável
- `M17` virou checklist de implementação com evidências e lacunas
- `M18` passou a devolver relação, severidade, precedência e guidance
- `M22` ganhou consolidação de telemetria útil para governança de release

## Limitação

Continua sendo um smoke test MCP stdio real, não uma execução ponta a ponta do agente CLI.
