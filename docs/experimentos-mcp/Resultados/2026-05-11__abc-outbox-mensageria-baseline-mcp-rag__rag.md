# 2026-05-11 — abc-outbox-mensageria-baseline-mcp-rag — Condição C (RAG geral)

## Parte 1 — Execução (obrigatório)

### 1) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice:
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação em memória/fila local conforme evidência no código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite e evidência no repositório.

### 2) Plano BMAD (obrigatório)

#### Background
- Repo alvo: `C:/Users/herna/source/repos/TestClientCorporateInstructions` (API .NET 8, minimal endpoints, Dapper + SQL Server).
- Nesta condição, foi usado RAG geral do codebase; **MCP não foi usado**.
- Evidência no repo: não há broker configurado no workspace; foi implementada **simulação em memória** para publicação/consumo.

#### Mission
- Implementar vertical slice (Outbox + publicação + consumidor + read-model + idempotência + DLQ) no repo `TestClientCorporateInstructions`, preservando CRUD e validando build/testes.

#### Approach
- Persistir evento no outbox **na mesma transação** do `INSERT`/`UPDATE` do cliente (Dapper + `IDbTransaction`).
- Publicação/consumo com **fila em memória** (`Channel<T>`), já que não há evidência de broker no repo.
- Consumidor materializa `ClienteReadModel` com **idempotência** via tabela `ProcessedEvent` (PK `EventId`).
- DLQ implementada via tabela `DeadLetterEvent` após **N=3** tentativas (explícito no consumidor/outbox).
- Validar com `dotnet build` e `dotnet test`.

#### Delivery/validation
- Entregar patch no repo e rodar build/testes do solution.

### 3) Implementação (patch)
#### Patch aplicado (alto nível)
- **Outbox transacional**: `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs` grava `dbo.OutboxEvent` junto com `INSERT/UPDATE` do cliente, na mesma transação.
- **Outbox storage**: `ClientesAPI.Repositorio/Outbox/OutboxRepositoryDapper.cs` (poll de pendentes, marcar publicado, registrar falhas e mover para DLQ).
- **Read model idempotente**: `ClientesAPI.Repositorio/ReadModel/ClienteReadModelRepositoryDapper.cs` aplica evento ao `dbo.ClienteReadModel` com dedupe em `dbo.ProcessedEvent`.
- **Mensageria simulada**: `ClientesAPI.Api/Outbox/InMemoryEventBus.cs` usando `Channel<T>`.
- **Publisher/Consumer workers**: `ClientesAPI.Api/Outbox/OutboxPublisherBackgroundService.cs` e `ClientesAPI.Api/Outbox/OutboxConsumerBackgroundService.cs`.
- **SQL**: `sql/002_CreateOutboxAndReadModel.sql` cria `OutboxEvent`, `ClienteReadModel`, `ProcessedEvent` e `DeadLetterEvent`.

### 4) Validação
- Build: `dotnet build` (OK).
- Testes: `dotnet test` (OK; saída no ambiente não detalhou testes executados).
- Observação: warnings `NU1603` pré-existentes sobre `Swashbuckle.AspNetCore` resolvido por aproximação.

## Parte 2 — Relatório do experimento (obrigatório)

### Resumo
- **Status**: CONCLUÍDO

### FATO
- O repo alvo é .NET 8 com Dapper/SQL Server (`ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`, `DbConnectionFactory`).
- Não há evidência no codebase de broker RabbitMQ/MassTransit/EasyNetQ; a mensageria foi implementada como **simulação em memória**.
- `POST /clientes` e `PUT /clientes/{id}` já existiam e foram preservados; a persistência do outbox ocorre no repositório.
- O evento do outbox é persistido na mesma transação do `INSERT/UPDATE` do cliente (`BeginTransaction` no repositório).
- Há idempotência na projeção do read-model via tabela `dbo.ProcessedEvent` (chave `EventId`).
- DLQ existe via tabela `dbo.DeadLetterEvent` e **N=3** está explícito no consumidor + persistência de falhas no outbox.

### HIPÓTESE
- Não foi possível validar o comportamento end-to-end em runtime (API rodando + SQL com as novas tabelas), pois não há garantia de ambiente de DB provisionado no experimento.
- **Como validar**: executar `sql/002_CreateOutboxAndReadModel.sql` no mesmo database da app e exercitar `POST/PUT`, observando `dbo.OutboxEvent`, `dbo.ClienteReadModel`, `dbo.ProcessedEvent` e `dbo.DeadLetterEvent`.

### RISCO DE INTERPRETAÇÃO
- A solicitação do operador menciona “experimento A”, mas os artefatos fornecidos para execução foram de **condição C** (orquestrador/prompt C). Este relatório registra a execução como **C** (RAG geral), conforme o prompt usado.
- A simulação em memória não cobre semânticas reais de ack/nack de um broker, embora mantenha as decisões principais (outbox transacional, idempotência, DLQ).

### Métricas (N/A quando não disponível)
- **inicio_iso**: 2026-05-11T09:40:00-03:00
- **fim_iso**: 2026-05-11T09:55:00-03:00
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
  - `dotnet build`
  - `dotnet test`
- **tokens_input/output**: N/A
- **custo**: N/A
- **reprompts_qtd**: 1

```text
EXPERIMENT_METRICS_JSON
{"status":"completed","condition":"C","slug":"abc-outbox-mensageria-baseline-mcp-rag","date":"2026-05-11","repo_execucao":"TestClientCorporateInstructions","mcp_used":false,"validation":{"dotnet_build":true,"dotnet_test":true}}
```

```text
DECISIONS_JSON
{"decisions":[{"decision":"Mensageria simulada em memória (Channel<T>) por ausência de evidência de broker no repo.","anchored_in":[],"evidence":"Não há referências a bibliotecas/infra de RabbitMQ/MassTransit/EasyNetQ no codebase alvo; apenas Dapper + SQL."},{"decision":"Outbox persistido na mesma transação do INSERT/UPDATE do cliente (BeginTransaction no repositório).","anchored_in":[],"evidence":"Alterações em ClienteRepositorioDapper para abrir transação, executar INSERT/UPDATE e inserir OutboxEvent antes do commit."},{"decision":"Idempotência no consumidor via tabela ProcessedEvent com PK EventId.","anchored_in":[],"evidence":"Read-model aplica evento somente quando registra EventId em ProcessedEvent."},{"decision":"DLQ após N=3 tentativas explícitas via DeadLetterEvent e atualização do status do OutboxEvent.","anchored_in":[],"evidence":"Consumer chama RecordFailureAsync(maxAttempts=3) que incrementa Attempts e move para DeadLetterEvent ao atingir limite."}]}
```

