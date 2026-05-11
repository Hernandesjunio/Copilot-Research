# 2026-05-11 — abc-outbox-mensageria-baseline-mcp-rag — Condição B (MCP)

## Parte 1 — Execução (obrigatório)

### 1) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice:
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação em memória/fila local conforme evidência no código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite e evidência no repositório.

### 2) Plano BMAD (obrigatório)

#### Background
- A condição B exige uso de MCP `corporate-instructions` (tools `corporate_instructions_*`) para recuperar guardrails e citar `instruction_id` no relatório.

- Repo alvo: `C:/Users/herna/source/repos/TestClientCorporateInstructions` (API .NET 8, minimal endpoints, Dapper + SQL Server).
- Evidência: não há broker RabbitMQ no repo; foi implementada **simulação em memória** para publicação/consumo.

- Guardrails MCP aplicados (instruction_id):
  - `microservice-messaging-rabbitmq-publish-consume` (outbox transacional, ack após efeito durável, DLQ, idempotência, contrato versionado)
  - `microservice-data-access-and-sql-security` (parametrização SQL, transações curtas, sem I/O externo dentro de transação)
  - `assistant-workflow-bmad-planning-and-controlled-inference` (BMAD/spec-driven e separar FATO/HIPÓTESE/RISCO)

#### Mission
- Implementar vertical slice (Outbox + publicação + consumidor + read-model + idempotência + DLQ) no repo `TestClientCorporateInstructions`, preservando CRUD e validando build/testes.

#### Approach
- Recuperar guardrails via MCP (buscar → ler batch → ancorar decisões).
- Implementar persistência do evento Outbox **na mesma transação** do `INSERT`/`UPDATE` do cliente (Dapper + `SqlTransaction`).
- Implementar publicação/consumo com **fila em memória** (`Channel<T>`), conforme ausência de broker no repo.
- Implementar consumidor que materializa `ClienteReadModel`, com idempotência por `MessageId` usando tabela `ProcessedMessage`.
- Implementar DLQ após N=3 tentativas explícitas (publicação e consumo convergem para `OutboxDeadLetter`).
- Validar com `dotnet build` e testes aplicáveis.

#### Delivery/validation
- Entregar patch no repo e rodar build/testes.

### 3) Implementação (patch)
#### Patch aplicado (alto nível)
- **Outbox transacional**: `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs` agora cria `OutboxEvent` junto com `INSERT/UPDATE` do cliente, na mesma transação.
- **Outbox storage**: `ClientesAPI.Repositorio/Outbox/OutboxRepositoryDapper.cs`.
- **Read model idempotente**: `ClientesAPI.Repositorio/ReadModel/ClienteReadModelRepositoryDapper.cs` com tabela `ProcessedMessage` (dedupe) e `ClienteReadModel` (projeção).
- **Mensageria simulada**: `ClientesAPI.Api/Outbox/InMemoryEventBus.cs` com `Channel<T>`.
- **Publisher/Consumer workers**: `ClientesAPI.Api/Outbox/OutboxPublisherBackgroundService.cs` e `ClientesAPI.Api/Outbox/OutboxConsumerBackgroundService.cs`.
- **SQL**: `sql/002_CreateOutboxAndReadModel.sql` cria `OutboxEvent`, `OutboxDeadLetter`, `ProcessedMessage`, `ClienteReadModel`.

### 4) Validação
- Build: `dotnet build ClientesAPI.sln` (OK).
- Testes: `dotnet test ClientesAPI.Api.Tests/ClientesAPI.Api.Tests.csproj` (OK).
- Observação: warnings `NU1603` pré-existentes por versão de `Swashbuckle.AspNetCore` resolvida por aproximação.

## Parte 2 — Relatório do experimento (obrigatório)

### Resumo
- **Status**: CONCLUÍDO

### FATO
- MCP foi consultado e retornou policies usadas na decisão (ver seção “Guardrails MCP aplicados” e “MCP” abaixo).
- O repo alvo é .NET 8 com Dapper/SQL Server; não há evidência de RabbitMQ/MassTransit/EasyNetQ.
- `POST /clientes` e `PUT /clientes/{id}` já existiam e foram preservados; a geração do outbox ocorre no repositório.
- Outbox é persistido na mesma transação (`SqlTransaction`) do `INSERT/UPDATE` do cliente.
- Há idempotência na projeção do read-model via tabela `ProcessedMessage` (chave `MessageId`).
- DLQ existe via tabela `OutboxDeadLetter` e N=3 está explícito no código.

### HIPÓTESE
- Não foi possível validar comportamento end-to-end em runtime (API rodando + SQL com as novas tabelas criadas), pois o experimento exigia build/testes e não inclui ambiente DB provisionado aqui.
- **Como validar**: executar `sql/002_CreateOutboxAndReadModel.sql` no mesmo database da app e exercitar `POST/PUT`, observando `dbo.OutboxEvent`, `dbo.ClienteReadModel` e `dbo.OutboxDeadLetter`.

### RISCO DE INTERPRETAÇÃO
- A implementação usa “mensageria em memória” para cumprir o requisito na ausência de broker no repo; isso não cobre semânticas reais de ack/nack do RabbitMQ, embora preserve as decisões principais (outbox, idempotência, DLQ).

### MCP
- **mcp_tools_chamadas**: 2
- **tools usadas**:
  - `search_instructions` query=`mensageria outbox idempotência DLQ retry`
  - `get_instructions_batch` ids=`microservice-messaging-rabbitmq-publish-consume,microservice-resilience-polly-timeouts-and-circuit-breaker,microservice-data-access-and-sql-security,assistant-workflow-bmad-planning-and-controlled-inference,microservice-opentelemetry-correlation-and-health`
- **instruction_id citados e usados em decisões**:
  - `microservice-messaging-rabbitmq-publish-consume`: outbox transacional, idempotência, DLQ, contrato versionado
  - `microservice-data-access-and-sql-security`: transação curta; sem I/O externo dentro da transação; SQL parametrizado
  - `assistant-workflow-bmad-planning-and-controlled-inference`: BMAD/spec-driven, explicitar FATO/HIPÓTESE/RISCO

### Métricas (N/A quando não disponível)
- **inicio_iso**: 2026-05-11T09:05:00-03:00
- **fim_iso**: 2026-05-11T09:30:00-03:00
- **duracao_ms**: N/A
- **tempos_por_etapa_ms**:
  - leitura: N/A
  - decisao: N/A
  - implementacao: N/A
  - validacao: N/A
  - relatorio: N/A
- **arquivos_lidos_qtd**: N/A
- **arquivos_tocados_qtd**: N/A
- **comandos_executados**:
  - `dotnet build ClientesAPI.sln`
  - `dotnet test ClientesAPI.Api.Tests/ClientesAPI.Api.Tests.csproj -v minimal`
- **tokens_input/output**: N/A
- **custo**: N/A
- **reprompts_qtd**: 0

```text
EXPERIMENT_METRICS_JSON
{"status":"completed","condition":"B","slug":"abc-outbox-mensageria-baseline-mcp-rag","date":"2026-05-11","mcp_tools_chamadas":2,"mcp_instruction_ids":["microservice-messaging-rabbitmq-publish-consume","microservice-resilience-polly-timeouts-and-circuit-breaker","microservice-data-access-and-sql-security","assistant-workflow-bmad-planning-and-controlled-inference","microservice-opentelemetry-correlation-and-health"],"repo_execucao":"TestClientCorporateInstructions"}
```

```text
DECISIONS_JSON
{"decisions":[{"decision":"Mensageria será simulada em memória (Channel<T>) por ausência de evidência de broker no repo.","anchored_in":["microservice-messaging-rabbitmq-publish-consume"],"evidence":"Sem referências a RabbitMQ.Client/MassTransit/EasyNetQ no workspace do repo alvo."},{"decision":"Outbox persistido na mesma transação do INSERT/UPDATE do cliente (SqlTransaction).","anchored_in":["microservice-messaging-rabbitmq-publish-consume","microservice-data-access-and-sql-security"],"evidence":"Alteração em ClienteRepositorioDapper para usar SqlTransaction e persistir OutboxEvent."},{"decision":"Idempotência no consumidor via tabela ProcessedMessage com PK MessageId.","anchored_in":["microservice-messaging-rabbitmq-publish-consume"],"evidence":"ProcessedMessage inserida antes do MERGE do read-model; conflito implica noop."},{"decision":"DLQ após N=3 tentativas explícitas no publisher e consumer.","anchored_in":["microservice-messaging-rabbitmq-publish-consume"],"evidence":"Constantes PublishMaxAttempts=3 e ConsumeMaxAttempts=3 e persistência em OutboxDeadLetter."}]}
```

