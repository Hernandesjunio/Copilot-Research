# Smoke test MCP stdio — local atual

## Objetivo

Executar um smoke test real via MCP stdio contra a versão local atual do `corporate_instructions_mcp`, usando o mesmo corpus e as mesmas queries da rodada baseline.

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

## Queries executadas

### `mensageria outbox`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-data-access-and-sql-security`
- `search_confidence: 0.7967`

### `idempotencia eventos`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-rest-http-semantics-and-status-codes`
- `search_confidence: 0.775`

### `resiliencia retry timeout`

- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `dns-retry-pattern`
- `microservice-integration-httpclientfactory-contracts`
- `search_confidence: 1.0`

### `sql seguranca persistencia`

- `microservice-data-access-and-sql-security`
- `microservice-auth-jwt-bearer-and-authorization`
- `microservice-authorization-resource-scope-and-audit`
- `search_confidence: 0.7075`

### `observabilidade correlation tracing`

- `microservice-opentelemetry-correlation-and-health`
- `microservice-saga-process-manager-and-compensation`
- `microservice-clean-architecture-guardrails`
- `search_confidence: 1.0`

## Batch executado

IDs solicitados:

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `dns-retry-pattern`

Resultado:

- `found_count: 4`
- `missing_ids: []`
- `corpus_version: 53abc71415375f5282c7c0def68caa191ed95011f31b4c9cc98889b50c08de71`

## Tools compostas exercitadas

### `resolve_instruction_context`

- selecionou:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-data-access-and-sql-security`
- retornou bloco com `search` e `batch`

### `get_normative_checklist`

- cenário: `mensageria_outbox`
- itens retornados: `2`
- itens faltantes: `[]`

### `detect_instruction_conflicts`

- IDs verificados:
  - `microservice-messaging-rabbitmq-publish-consume`
  - `microservice-saga-process-manager-and-compensation`
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
- conflitos detectados: `2`

## Leitura inicial

A versão atual respondeu normalmente no protocolo MCP stdio, preservando as tools originais e expondo novas tools compostas. O comportamento observável ficou mais rico: diagnósticos de busca, evidência de versão de corpus, checklist normativa e detecção de conflitos já aparecem como contrato utilizável pelo cliente.

## Limitação

Esta rodada continua sendo um smoke test via MCP stdio e não uma execução completa de agente ponta a ponta, porque o CLI headless do agente não está disponível neste ambiente.
