# Cenário 01 (Outbox / mensageria) — Condição A: Baseline (sem `fixtures/`)

## Parte 1 — Execução

### 1) Cenário canónico

Implementei o seguinte vertical slice:

- `POST /api/v1/clientes`: na mesma transação da persistência do cliente, registar evento no **Outbox**.
- `PUT /api/v1/clientes/{id}`: na mesma transação do update, registar evento no **Outbox**.
- **Publicação**: dispatcher em background lê `dbo.OutboxMensagem` e publica em **fila em memória** (Channel) por não haver evidência de broker real no repo.
- **Consumidor**: lê da fila em memória, atualiza `dbo.ClienteReadModel`.
- **Idempotência**: `dbo.ProcessedEvent` com PK `EventoId` impede aplicar o mesmo evento duas vezes.
- **DLQ**: após **N=3** tentativas de processamento falhadas, regista em `dbo.OutboxDlq` e marca `OutboxMensagem.Status = DeadLetter`.

### 2) Plano BMAD

- **Background**: o repo expõe endpoints minimal API para CRUD de `Cliente` usando Dapper/SQL Server; não havia mensageria nem read-model separado.
- **Mission**: adicionar Outbox transacional em `POST/PUT`, publicação/consumo assíncronos, idempotência e DLQ, sem quebrar o CRUD existente.
- **Approach**:
  - Persistir Outbox junto do `INSERT/UPDATE` do cliente (mesma transação SQL).
  - Implementar bus local em memória (Channel) para simular mensageria.
  - Implementar dispatcher (poll) + consumer (subscribe) como `BackgroundService`.
  - Read-model em tabela própria com `MERGE`.
  - Idempotência por tabela de eventos processados com constraint (PK).
  - DLQ por tabela dedicada e marcação no outbox.
- **Delivery/validation**:
  - `dotnet build` e `dotnet test`.
  - Inspecionar que `CriarAsync`/`AtualizarAsync` usam transação e inserem Outbox.
  - Garantir que hosted services foram registados e compilam.

### 3) Implementação (patch)

Arquivos/áreas alteradas ou adicionadas no workspace `TestClientCorporateInstructions`:

- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`: `CriarAsync` e `AtualizarAsync` passaram a abrir `SqlTransaction` e inserir `OutboxMensagem` na mesma transação do write do cliente.
- `ClientesAPI.Repositorio/Outbox/OutboxRepositorioDapper.cs`: operações de Outbox (inserção, listagem para dispatch, marcações e DLQ).
- `ClientesAPI.Repositorio/ReadModel/*`: repositórios para `ClienteReadModel` e `ProcessedEvent`.
- `ClientesAPI.Api/Outbox/*`: bus em memória + dispatcher + consumer.
- `ClientesAPI.Api/Extensions/ApiExtensions.cs`: DI do bus e hosted services.
- `sql/002_CreateOutboxReadModelAndDlq.sql`: DDL das tabelas Outbox/DLQ/ReadModel/ProcessedEvent.
- `ClientesAPI.Interfaces/*`: novos contratos (`IOutboxRepositorio`, `IMessageBus`, `IClienteReadModelRepositorio`, `IProcessedEventRepositorio`).
- `ClientesAPI.Modelo/*`: tipos de payload e read-model.

### 4) Validação

- Build:
  - `dotnet build`
- Testes:
  - `dotnet test`

Relação com critérios de aceite:

- **Build**: `dotnet build` passou (sem erros).
- **Outbox**: `dbo.OutboxMensagem` definida no script `sql/002_...sql` e inserida em `CriarAsync`/`AtualizarAsync`.
- **POST/PUT geram evento**: inserção em Outbox no repositório durante o `INSERT/UPDATE` (mesma transação).
- **Publicação**: `OutboxDispatcherBackgroundService` publica mensagens pendentes.
- **Consumidor + read-model**: `OutboxConsumerBackgroundService` aplica em `dbo.ClienteReadModel`.
- **Idempotência**: `dbo.ProcessedEvent` (PK = `EventoId`) + `TryMarkProcessedAsync`.
- **DLQ**: `dbo.OutboxDlq` + `MoverParaDlqAsync` após N=3 falhas.
- **Cache**: N/A (não encontrei evidência de cache no código fora de `.github/instructions`, que estava removido durante o experimento).
- **CorrelationId**: N/A (não encontrei conceito explícito no código).
- **SQL parametrizado**: Dapper com parâmetros anónimos (sem concatenação).

## Parte 2 — Relatório do experimento

### FATO

- O repo usa **Dapper + SQL Server** para persistência (`ClienteRepositorioDapper`).
- Os endpoints `POST/PUT` chamam `IClienteServico`, que delega para o repositório.
- Não há evidência no código de broker RabbitMQ/MassTransit/etc.; por isso a publicação foi **simulada em memória**.
- Durante o experimento, `.github/instructions/` e `.github/copilot-instructions.md` foram removidos do workspace e restaurados ao final.

### HIPÓTESE

- A execução real do fluxo (dispatcher/consumer) depende da existência das tabelas no banco e da app estar em execução; validar aplicando o script `sql/002_...sql` e fazendo chamadas `POST/PUT`.

### RISCO DE INTERPRETAÇÃO

- O dispatcher inclui itens com `Status = Dispatchado` para permitir re-dispatch após falhas do consumer; isto pode gerar **duplicatas** na fila, mitigadas por idempotência via `ProcessedEvent`.

## EXPERIMENT_METRICS_JSON

```json
{
  "data": "2026-05-11",
  "condicao": "A",
  "slug": "abc-outbox-mensageria-baseline-mcp-rag",
  "workspace_alvo": "TestClientCorporateInstructions",
  "fixtures_removida": "N/A (nao existe pasta fixtures/ no workspace)",
  "github_instructions_removida": true,
  "comandos_executados": [
    "ls -la",
    "ls -la .github",
    "mv .github/instructions -> .cursor_experiment_backup/... (temporario)",
    "mv .github/copilot-instructions.md -> .cursor_experiment_backup/... (temporario)",
    "dotnet build",
    "dotnet test",
    "mv restore .github/instructions e .github/copilot-instructions.md"
  ],
  "tokens_input_output": "N/A",
  "custo": "N/A"
}
```

## DECISIONS_JSON

```json
{
  "mensageria": "fila em memoria (Channel) por ausencia de broker no repo",
  "idempotencia": "tabela dbo.ProcessedEvent com PK em EventoId",
  "dlq": "tabela dbo.OutboxDlq; N=3 tentativas",
  "read_model": "tabela dbo.ClienteReadModel com MERGE (upsert)"
}
```

