# Smoke test MCP stdio — global antigo

## Objetivo

Executar um smoke test real via MCP stdio contra a instância global antiga do `corporate_instructions_mcp`, usando o mesmo corpus do projeto e chamadas MCP reais (`tools/list`, `search_instructions`, `get_instructions_batch`).

## Configuração da rodada

- Data: `2026-05-02`
- Tipo: `MCP stdio`
- Servidor executado: `python -m corporate_instructions_mcp`
- Diretório de execução: `c:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `c:\_projeto\Copilot-Research\fixtures\instructions`
- Isolamento da versão antiga: `git stash` temporário em `mcp-instructions-server/`, seguido de `git stash pop`

## Tools expostas

- `get_instructions_batch`
- `list_instructions_index`
- `search_instructions`

## Queries executadas

### `mensageria outbox`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-data-access-and-sql-security`

### `idempotencia eventos`

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-auth-jwt-bearer-and-authorization`

### `resiliencia retry timeout`

- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `dns-retry-pattern`
- `microservice-data-access-and-sql-security`

### `sql seguranca persistencia`

- `microservice-data-access-and-sql-security`
- `microservice-domain-interfaces-models-repository`
- `security-baseline-secrets`

### `observabilidade correlation tracing`

- `microservice-opentelemetry-correlation-and-health`
- `microservice-saga-process-manager-and-compensation`
- `microservice-clean-architecture-guardrails`

## Batch executado

IDs solicitados:

- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-saga-process-manager-and-compensation`
- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `dns-retry-pattern`

Resultado:

- `found_count: 4`
- `missing_ids: []`
- todos os IDs retornaram com sucesso

## Leitura inicial

O servidor antigo respondeu normalmente no protocolo MCP stdio e recuperou documentos coerentes com o cenário de outbox/mensageria. Nesta rodada, o catálogo observado tem apenas as três tools originais, sem evidência de contracts expandidos ou tools compostas novas.

## Limitação

Esta rodada foi um smoke test de tool behavior via stdio, não uma execução completa de agente ponta a ponta, porque o CLI headless do agente não está disponível neste ambiente.
