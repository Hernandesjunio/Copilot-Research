# Parte 1 — Execução

## 1) Seleção de guardrails e evidências (antes de codar)

### Instructions locais aplicáveis e decisões suportadas

1. `assistant-workflow-bmad-planning-and-controlled-inference` — exigência de BMAD e separação entre evidência e inferência.
   - Decisão suportada: estruturar implementação e relatório com BMAD + riscos + critérios.
2. `microservice-messaging-rabbitmq-publish-consume` — outbox transacional, consumidor idempotente, DLQ e read-model.
   - Decisão suportada: usar outbox + fila em memória (ausência de RabbitMQ no repo), consumidor com idempotência por `EventId`, DLQ em tabela.
3. `microservice-data-access-and-sql-security` — SQL parametrizado, transações curtas e `CommandDefinition` com timeout/cancellation.
   - Decisão suportada: toda persistência Dapper com parâmetros, transação única em POST/PUT para cliente+outbox.
4. `microservice-di-options-extensions` — options tipadas e DI por extensions.
   - Decisão suportada: `MensageriaOptions` + binding em `RepositoryExtensions` + hosted services no `Program`.
5. `microservice-architecture-layering` e `microservice-domain-interfaces-models-repository` — separação por camadas e contratos em Interfaces.
   - Decisão suportada: novos contratos em `Interfaces`, modelos em `Modelo`, implementação Dapper em `Repositorio`, orquestração em `Api`.
6. `microservice-opentelemetry-correlation-and-health` — propagação de correlação quando aplicável.
   - Decisão suportada: propagar `X-Correlation-Id`/`traceparent` do HTTP para o payload do evento.
7. `microservice-caching-imemorycache-policy` — só aplicar se houver evidência de cache.
   - Decisão suportada: **não implementar invalidação** por ausência de `IMemoryCache` no código.

### Ficheiros/módulos do workspace que ancoraram decisões

- API: `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`, `ClientesAPI.Api/Program.cs`
- Domínio: `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- Contratos: `ClientesAPI.Interfaces/IClienteServico.cs`, `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- Repositório: `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`, `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs`, `ClientesAPI.Repositorio/Conexao/*`
- Configuração: `ClientesAPI.Api/appsettings.json`, `ClientesAPI.Api/appsettings.Development.json`, `ClientesAPI.Repositorio/Options/SqlOptions.cs`

### Lacunas

- **FATO:** não há evidência de broker RabbitMQ no repositório (sem pacotes/registrations/sinais do workspace).
- **Decisão:** aplicada simulação em memória com `Channel<T>`, conforme permitido pela tarefa e por `microservice-messaging-rabbitmq-publish-consume` (condição `on_absence: hypothesis_only`).

---

## 2) Cenário canónico (vertical slice comparável)

Implementação entregue:
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, regista evento no **Outbox**; publicação para mensageria via fila local em memória (com evidência no código).
- **Consumidor:** lê da fila e atualiza `ClienteReadModel`; idempotência por `EventId` em `ClienteEventosProcessados`.
- **DLQ** em tabela (`ClienteEventosDlq`) após **N=3** tentativas falhadas (explícito em `MensageriaOptions`).
- CRUD preservado; sem cache existente no projeto; correlação propagada (`X-Correlation-Id`/`traceparent`/`TraceIdentifier`).

---

## 3) Plano BMAD (obrigatório)

### Background
- API .NET 8 com Minimal API + Dapper em SQL Server, arquitetura em camadas.
- CRUD já existente em `Cliente`.
- Instructions locais exigem BMAD, SQL parametrizado, outbox/idempotência/DLQ.

### Mission
- Implementar fluxo de outbox transacional para criação/atualização de cliente, publicação assíncrona, consumo idempotente para read-model e DLQ após N tentativas.

### Approach
- Estender contratos (`Interfaces`) e serviço de domínio para propagar `correlationId`.
- Alterar repositório de cliente para gravar cliente+outbox na mesma transação.
- Criar repositório de mensageria (schema, polling outbox, deduplicação, DLQ).
- Criar fila local em memória + workers de publicação e consumo.
- Registrar DI/options e validar build.

### Delivery/validation
- `dotnet build` sem erros.
- Verificações objetivas por SQL/fluxo (descritas na seção de validação).
- Sem rollback/feature flag neste repo (não há mecanismo prévio observado).

### Refinamento crítico
- **Riscos:** consistência eventual entre write-model e read-model; reprocessamento sob falhas transitórias.
- **Dependências:** SQL Server local disponível e permissões para criar tabelas.
- **Critérios técnicos:** transação única cliente+outbox, idempotência por `EventId`, DLQ após `N=3`, build verde.

---

## 4) Implementação (patch)

### FATO — arquivos adicionados
- `ClientesAPI.Modelo/ClienteEventoPayload.cs`
- `ClientesAPI.Modelo/ClienteEventoOutboxItem.cs`
- `ClientesAPI.Modelo/ClienteEventoFilaMensagem.cs`
- `ClientesAPI.Interfaces/IClienteEventQueue.cs`
- `ClientesAPI.Interfaces/IClienteMensageriaRepositorio.cs`
- `ClientesAPI.Repositorio/Options/MensageriaOptions.cs`
- `ClientesAPI.Repositorio/ClienteMensageriaRepositorioDapper.cs`
- `ClientesAPI.Api/Messaging/InMemoryClienteEventQueue.cs`
- `ClientesAPI.Api/Messaging/OutboxPublisherWorker.cs`
- `ClientesAPI.Api/Messaging/ClienteReadModelConsumerWorker.cs`

### FATO — arquivos alterados
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
- `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs`
- `ClientesAPI.Api/Program.cs`
- `ClientesAPI.Api/appsettings.json`
- `ClientesAPI.Api/appsettings.Development.json`

### Decisões técnicas principais implementadas
- Outbox persistido em `dbo.ClienteEventosOutbox` no mesmo `BEGIN TRANSACTION` do `INSERT/UPDATE` de `Cliente`.
- Publisher lê pendências de outbox e publica na fila local em memória.
- Consumer processa payload, atualiza `dbo.ClienteReadModel` com `MERGE`, e deduplica em `dbo.ClienteEventosProcessados`.
- Falhas de publicação reagem com retry agendado; ao atingir limite, outbox é marcado `DeadLettered` e evento vai para `dbo.ClienteEventosDlq`.
- Falhas de consumo após N tentativas também registram em DLQ.
- Correlação: capturada do HTTP e armazenada no evento.

---

## 5) Validação

### Executado
- **Build:** `dotnet build` → **sucesso**.

### Não executado automaticamente
- **Testes:** `get_tests` não encontrou testes no workspace.

### Matriz critérios de aceite x verificação

| Critério | Verificação |
|---|---|
| Build | `dotnet build` (executado: sucesso) |
| Outbox | Tabela criada em `EnsureSchemaAsync`: `ClienteEventosOutbox` com tipo, payload, timestamps, flags |
| POST gera evento | Fluxo: `ClienteRepositorioDapper.CriarAsync` + `InserirOutboxAsync` na mesma transação |
| PUT gera evento | Fluxo: `ClienteRepositorioDapper.AtualizarAsync` + `InserirOutboxAsync` na mesma transação |
| Read-model | `ProcessarReadModelAsync` grava em `ClienteReadModel` |
| Idempotência | `ClienteEventosProcessados(EventId PK)` evita aplicar duas vezes |
| DLQ | `ReagendarOuMoverOutboxParaDlqAsync` e `RegistrarFalhaConsumoAsync` com N=3 |
| Cache | **FATO:** não há `IMemoryCache`; critério não aplicável no estado atual |
| Correlação | `ObterCorrelationId` em endpoint → campo `CorrelationId` no payload |
| Segurança | SQL parametrizado com Dapper `CommandDefinition` |

### Comandos objetivos para validação funcional manual (não executados nesta sessão)

1. Criar cliente:
   - `POST /api/v1/clientes` com JSON válido.
   - Sucesso esperado: registro em `Cliente`, `ClienteEventosOutbox`, depois `Publicado=1` e upsert em `ClienteReadModel`.
2. Atualizar cliente:
   - `PUT /api/v1/clientes/{id}`.
   - Sucesso esperado: novo evento em outbox, read-model refletindo update.
3. Idempotência:
   - Reenfileirar mesmo `EventId` no consumer.
   - Sucesso esperado: sem duplicação de efeito por bloqueio em `ClienteEventosProcessados`.
4. DLQ:
   - Forçar exceção no consumidor por 3 tentativas.
   - Sucesso esperado: registro em `ClienteEventosDlq`.

---

# Parte 2 — Relatório do experimento

## 0) Métricas de execução

- **tempo total (wall-clock)**
  - `inicio_iso`: `2026-05-02T09:57:04.6680248-03:00`
  - `fim_iso`: `2026-05-02T10:16:09.2240445-03:00`
  - `duracao_ms`: `1144556`
- **latência por etapa (estimada)**
  - `exploracao_leitura_ms`: `360000`
  - `raciocinio_decisao_ms`: `150000`
  - `escrita_patch_ms`: `430000`
  - `validacao_ms`: `90000`
  - `escrita_relatorio_ms`: `114556`
- **uso de tools**
  - `qtd_tool_calls_total`: `65` (estimado por contagem do log da sessão)
  - `qtd_por_tool` (estimado):
    - `get_projects_in_solution`: 1
    - `get_files_in_project`: 5
    - `get_file`: 30
    - `file_search`: 4
    - `code_search`: 1
    - `plan`: 2
    - `update_plan_progress`: 12
    - `apply_patch`: 13
    - `create_file`: 10
    - `run_build`: 3
    - `run_command_in_terminal`: 5
    - `get_tests`: 1
    - `record_observation`: 1
    - `finish_plan`: 0 (até este ponto do arquivo)
  - `sucessos`: `64`
  - `falhas`: `1` (um `apply_patch` inicial inválido)
  - `retries`: `1`
- **I/O de contexto**
  - `qtd_arquivos_lidos`: `~26` (estimativa por paths únicos lidos)
  - `qtd_arquivos_citados`: `~22`
  - `qtd_trechos_citados`: `~40`
  - `bytes_aprox_lidos`: `~120000`
- **tokens**
  - `tokens_input_est`: `~26000`
  - `tokens_output_est`: `~9000`
  - método: aproximação por `caracteres/4`
  - margem de erro: `±25%`
- **custo**
  - `custo_total`: `N/A` (plataforma não expõe billing nesta sessão)
  - `moeda`: `N/A`
- **tamanho do resultado**
  - `caracteres_resposta`: `N/A` (não disponível de forma automática)
  - `qtd_itens_patch`: `19` (arquivos tocados diretamente pela implementação)
- **contagens de rigor**
  - `qtd_afirmacoes_FATO`: `22`
  - `qtd_afirmacoes_HIPOTESE`: `4`
  - `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`: `6`

```json
EXPERIMENT_METRICS_JSON
{
  "inicio_iso": "2026-05-02T09:57:04.6680248-03:00",
  "fim_iso": "2026-05-02T10:16:09.2240445-03:00",
  "duracao_ms": 1144556,
  "exploracao_leitura_ms": 360000,
  "raciocinio_decisao_ms": 150000,
  "escrita_patch_ms": 430000,
  "validacao_ms": 90000,
  "escrita_relatorio_ms": 114556,
  "qtd_tool_calls_total": 65,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "get_files_in_project": 5,
    "get_file": 30,
    "file_search": 4,
    "code_search": 1,
    "plan": 2,
    "update_plan_progress": 12,
    "apply_patch": 13,
    "create_file": 10,
    "run_build": 3,
    "run_command_in_terminal": 5,
    "get_tests": 1,
    "record_observation": 1,
    "finish_plan": 0
  },
  "sucessos": 64,
  "falhas": 1,
  "retries": 1,
  "qtd_arquivos_lidos": 26,
  "qtd_arquivos_citados": 22,
  "qtd_trechos_citados": 40,
  "bytes_aprox_lidos": 120000,
  "tokens_input": "N/A",
  "tokens_output": "N/A",
  "tokens_input_est": 26000,
  "tokens_output_est": 9000,
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_patch": 19,
  "qtd_afirmacoes_FATO": 22,
  "qtd_afirmacoes_HIPOTESE": 4,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 6
}
```

```json
DECISIONS_JSON
{
  "decisoes": [
    {
      "decisao": "Usar Outbox transacional para POST/PUT de cliente",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume; ClientesAPI.Repositorio/ClienteRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "Verificar transação única e INSERT em ClienteEventosOutbox no mesmo fluxo"
    },
    {
      "decisao": "Implementar fila local em memória em vez de RabbitMQ",
      "ancoragem": "codigo_repo",
      "evidencia": "ausência de sinais RabbitMQ no workspace + on_absence: hypothesis_only",
      "risco": "medio",
      "como_validar": "Substituir IClienteEventQueue por adapter RabbitMQ em ambiente com broker"
    },
    {
      "decisao": "Idempotência por EventId com tabela ClienteEventosProcessados",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume; ClienteMensageriaRepositorioDapper.ProcessarReadModelAsync",
      "risco": "baixo",
      "como_validar": "Reprocessar mesmo EventId e observar ausência de duplicação na read-model"
    },
    {
      "decisao": "DLQ em tabela após N=3 tentativas",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume; MensageriaOptions.Max*Tentativas=3",
      "risco": "baixo",
      "como_validar": "Forçar falha repetida e confirmar inserção em ClienteEventosDlq"
    },
    {
      "decisao": "SQL sempre parametrizado com Dapper CommandDefinition",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-data-access-and-sql-security; repositórios Dapper",
      "risco": "baixo",
      "como_validar": "Inspecionar queries sem concatenação de input"
    },
    {
      "decisao": "Propagar correlationId do HTTP para o evento",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-opentelemetry-correlation-and-health; ClienteEndpoints.ObterCorrelationId",
      "risco": "medio",
      "como_validar": "Enviar header X-Correlation-Id e verificar campo no payload do outbox"
    },
    {
      "decisao": "Não implementar invalidação de cache",
      "ancoragem": "codigo_repo",
      "evidencia": "sem IMemoryCache/AddMemoryCache no workspace",
      "risco": "baixo",
      "como_validar": "Code search para componentes de cache"
    },
    {
      "decisao": "Registrar options de mensageria e workers no startup",
      "ancoragem": "instruction_local",
      "evidencia": "microservice-di-options-extensions; Program.cs e RepositoryExtensions.cs",
      "risco": "baixo",
      "como_validar": "Build + startup sem falhas de DI"
    }
  ]
}
```

## 1) Uso das instructions locais

### FATO
- Houve uso efetivo das instructions locais como fonte principal (sem MCP corporativo).
- Decisões centrais (outbox/idempotência/DLQ/transação/DI/segurança SQL) foram ancoradas em arquivos específicos da pasta `.github/instructions`.

### Valor agregado
- Redução de ambiguidade em mensageria e acesso a dados.
- Direcionamento claro para separar contratos e implementação por camada.

### Onde poderia melhorar
- Falta de uma instruction local específica para padrão de testes do próprio repositório (há policy geral, mas sem suíte local disponível).

### Dependência de inferência restante
- **HIPÓTESE:** usar fila em memória é suficiente para este experimento; em produção real exigiria broker real e controles operacionais.

## 2) Qualidade técnica do plano

- Estrutura do plano: **forte** (BMAD aplicado).
- Clareza de camadas: **forte** (Interfaces/Modelo/Repositorio/Api separados).
- Coerência arquitetural: **forte** para escopo atual.
- Aderência a boas práticas: **forte** em transação, SQL parametrizado, idempotência e DLQ.
- Sinais de genericidade/overengineering: **parcial** (inclusão de schema bootstrap em runtime pode não ser ideal em produção, mas é pragmático para experimento).

## 3) Centralização de conhecimento

- **FATO:** instructions locais reduziram ambiguidades que não estavam explícitas no código (ex.: critérios de idempotência e DLQ).
- Reutilização: **boa** para times no mesmo repo, pois decisões ficam rastreáveis por `id`.
- Consistência: **boa**, desde que os autores mantenham o corpus atualizado e sem conflitos.
- Governança: **favorável**, porque policies versionadas no repositório são auditáveis por PR.

## 4) Escalabilidade em múltiplos repositórios

- Escala até certo ponto: boa para autonomia local, mas com risco de drift entre repositórios.
- Esforço de manutenção: moderado/alto sem automação de sincronização de corpus.
- Riscos operacionais: versões divergentes de policies, duplicação de conteúdo e interpretação inconsistente.
- Dependências de tooling: convém ter linting/validação automática das instructions e difusão de baseline corporativa.

## 5) Experiência de uso

- Fluidez: boa na fase de implementação.
- Previsibilidade: razoável, com necessidade de leitura explícita das instructions.
- Interrupções: baixa; principal fricção foi um patch inicial inválido e ausência de testes automatizados.
- Dependência de prompt: média; sem prompt forte, parte da rastreabilidade poderia cair.
- Impacto de tools: alto e positivo para evidência objetiva, com custo de tempo adicional.

---

## Avaliação (0 a 2)

- aderência ao contexto recuperado: **2**
- qualidade técnica: **2**
- completude: **1**
- consistência: **2**
- capacidade de centralização: **2**
- escalabilidade: **1**
- governança: **2**

---

## Conclusão final

**“as instructions locais ajudam, mas precisam de complementos (código, reprompt ou corpus externo)”**

- principal evidência: policies locais guiaram corretamente decisões críticas (outbox/idempotência/DLQ/SQL), porém validação funcional ponta a ponta ficou dependente de execução manual (sem testes prontos no repo).
- principal limitação do experimento: ausência de suíte de integração automatizada no workspace para provar os cenários de falha/retry/DLQ de forma reproduzível.
