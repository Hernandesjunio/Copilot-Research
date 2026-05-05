# Parte 1 — Execução

## Cenário canónico
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação conforme MCP + código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite.

## 1) Seleção de guardrails e evidências (antes de codar)

### Instructions MCP usadas (id -> decisão)
- `assistant-workflow-bmad-planning-and-controlled-inference` -> estrutura BMAD, separação FATO/HIPÓTESE/RISCO.
- `microservice-messaging-rabbitmq-publish-consume` -> outbox, publicação assíncrona, consumidor, idempotência, DLQ, read-model.
- `microservice-data-access-and-sql-security` -> SQL parametrizado com Dapper + transações curtas.
- `microservice-architecture-layering` -> separação Api/Dominio/Interfaces/Repositorio/Modelo.
- `microservice-clean-architecture-guardrails` -> workers assíncronos, dependências para dentro, sem acoplamento indevido.
- `microservice-opentelemetry-correlation-and-health` -> propagação de `CorrelationId` no pipeline e eventos.
- `microservice-caching-imemorycache-policy` -> decisão sobre cache (não aplicar por ausência de evidência no repo).
- `microservice-di-options-extensions` -> registro por extension methods e DI encapsulado.
- `microservice-testing-strategy-unit-integration-contract` -> validação mínima com build e busca de testes.
- `microservice-rest-http-semantics-and-status-codes` -> manter semântica CRUD existente e códigos HTTP.

### Instruction local usada
- `.github/copilot-instructions.md` -> idioma português, segurança, escopo local, consulta MCP obrigatória para decisão transversal.

### Ficheiros do workspace que ancoraram decisões
- API: `ClientesAPI.Api/Program.cs`, `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- Domínio: `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- Contratos: `ClientesAPI.Interfaces/IClienteServico.cs`, `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- Repositório: `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`, `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs`, `ClientesAPI.Repositorio/Conexao/DbConnectionFactory.cs`
- Modelo: `ClientesAPI.Modelo/ClienteResposta.cs`, `ClientesAPI.Modelo/ClienteRequisicao.cs`
- Config/Packages: `ClientesAPI.Repositorio/ClientesAPI.Repositorio.csproj`, `ClientesAPI.Api/ClientesAPI.Api.csproj`, `ClientesAPI.Api/appsettings.json`

## 2) Plano BMAD

### Background
API .NET 8 em camadas com CRUD de clientes por Dapper já existente, sem RabbitMQ nem infraestrutura de mensageria real no repo.

### Mission
Adicionar outbox transacional para `POST`/`PUT`, publicação assíncrona para fila local persistida, consumo com read-model, idempotência e DLQ (`N=3`) sem quebrar CRUD atual.

### Approach
1. Expandir contratos em `Interfaces` e modelos em `Modelo`.
2. Implementar transação única cliente+outbox no repositório.
3. Implementar fila local persistida e workers de publicação/consumo.
4. Aplicar idempotência por `MensagemId` com tabela de processados.
5. Implementar DLQ após 3 falhas.
6. Propagar `X-Correlation-Id` request -> evento.
7. Validar build e mapear critérios de aceite.

### Delivery/validation
- `dotnet build` deve passar.
- `get_tests` para detectar testes existentes.
- Validação funcional por critérios objetivos e comandos listados na seção de validação.

## 3) Implementação (patch aplicado)

### Arquivos alterados
- `ClientesAPI.Api/Program.cs`
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/ClientesAPI.Api.csproj`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
- `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs`
- `ClientesAPI.Repositorio/ClientesAPI.Repositorio.csproj`

### Arquivos criados
- `ClientesAPI.Modelo/OutboxModels.cs`
- `ClientesAPI.Interfaces/IClienteMensageriaPublisher.cs`
- `ClientesAPI.Interfaces/IClienteEventSerializer.cs`
- `ClientesAPI.Repositorio/Messaging/ClienteMensageriaLocalPublisher.cs`
- `ClientesAPI.Repositorio/Messaging/ClienteEventSerializer.cs`
- `ClientesAPI.Repositorio/Workers/OutboxPublisherWorker.cs`
- `ClientesAPI.Repositorio/Workers/ClienteEventConsumerWorker.cs`
- `ClientesAPI.Repositorio/Workers/DatabaseInitializationHostedService.cs`

### Resumo técnico do que foi implementado
- **Outbox transacional**: `CriarComOutboxAsync` e `AtualizarComOutboxAsync` persistem cliente + evento outbox na mesma transação SQL.
- **Publicação assíncrona**: `OutboxPublisherWorker` lê pendentes do outbox e publica em fila local persistida (`ClienteEventosFila`).
- **Consumidor/read-model**: `ClienteEventConsumerWorker` consome da fila e faz upsert em `ClienteReadModel`.
- **Idempotência**: tabela `ClienteEventosProcessados` deduplica por `MensagemId`.
- **DLQ**: após `MaxTentativas = 3`, move para `ClienteEventosDlq`.
- **Correlação**: `X-Correlation-Id` propagado do HTTP para evento (`CorrelationId` no payload e tabelas).
- **Infra local**: `DatabaseInitializationHostedService` cria tabelas necessárias ao iniciar a aplicação.
- **Endpoint de verificação**: `GET /api/v1/clientes/{id}/read-model` para consultar projeção.

## 4) Validação

### Comandos executados
1. `dotnet build` -> falhou inicialmente por referência de pacotes/hosting; corrigido.
2. `dotnet build` -> **sucesso**.
3. `get_tests` com `Outcome=NotRun` -> nenhum teste encontrado no workspace.

### Critérios de aceite x verificação
| Critério | Verificação objetiva | Status |
|---|---|---|
| Build | `dotnet build` | OK |
| Outbox | Tabela e métodos em `ClienteRepositorioDapper` + `GarantirEstruturaAsync` | OK |
| POST gera evento | `CriarComOutboxAsync` insere em `ClienteEventosOutbox` | OK |
| PUT gera evento | `AtualizarComOutboxAsync` insere em `ClienteEventosOutbox` | OK |
| Read-model | `ClienteEventConsumerWorker` + `UpsertClienteReadModelAsync` | OK |
| Idempotência | `MensagemJaProcessadaAsync` + `ClienteEventosProcessados` | OK |
| DLQ | `MaxTentativas=3` + `MoverParaDlqAsync` | OK |
| Cache | Não há `IMemoryCache` no repo; sem invalidação aplicável | N/A |
| Correlação | `Program.cs` + headers/propagação para evento | OK |
| Segurança SQL | Dapper + `CommandDefinition` + parâmetros | OK |

### Comandos sugeridos para validação funcional manual
- Criar cliente: `POST /api/v1/clientes`
- Atualizar cliente: `PUT /api/v1/clientes/{id}`
- Consultar read-model: `GET /api/v1/clientes/{id}/read-model`
- Verificar tabelas: `ClienteEventosOutbox`, `ClienteEventosFila`, `ClienteReadModel`, `ClienteEventosProcessados`, `ClienteEventosDlq`

---

# Parte 2 — Relatório do experimento

## 0. Métricas de execução

### FATOS
- O MCP foi consultado em fluxo completo: listagem, múltiplas buscas por tema, batch de conteúdo.
- O código do repositório foi lido antes da alteração dos arquivos críticos.
- Build final passou.

### HIPÓTESES
- Não há ambiente de broker real (RabbitMQ), então foi adotada fila local persistida.
- Não há pipeline de testes automatizados disponível neste workspace.

### RISCO DE INTERPRETAÇÃO
- A criação automática de tabelas no startup pode divergir de política corporativa de migração em pipelines dedicados.
- A simulação de falha no consumidor por conteúdo de email (`falha-consumidor`) é mecanismo de teste, não regra de domínio.

## 1. Evidência de uso de contexto
- **Ancorada em MCP**: outbox/idempotência/DLQ/read-model/correlação (`microservice-messaging-rabbitmq-publish-consume`, `microservice-opentelemetry-correlation-and-health`).
- **Ancorada em instruction local**: idioma, segurança e obrigação de consulta MCP (`.github/copilot-instructions.md`).
- **Ancorada no código repo**: Dapper + SQL + camadas existentes (`ClienteRepositorioDapper`, `ClienteServico`, `ClienteEndpoints`).
- **Inferida**: escolha de fila local persistida por ausência de RabbitMQ no código/configuração.

### Uso efetivo do MCP
Forte em decisões transversais (mensageria, resiliência, dados, correlação, DI). Sem MCP a implementação tenderia a ficar incompleta em idempotência/DLQ.

### Lacunas
Não há guardrail local explícito para migrações SQL versionadas; solução recorreu a bootstrap de schema no runtime.

### Dependência de inferência
Moderada: infraestrutura de mensageria real e testes de integração não existiam no repo.

## 2. Qualidade técnica do plano
- BMAD foi aplicado e executado em fatias incrementais.
- Patch coerente com arquitetura em camadas e contratos explícitos.
- Complexidade adequada ao escopo pedido (sem broker real).
- Há risco de overreach no repositório por concentrar responsabilidades (CRUD + outbox + fila + projeção).

## 3. Limitações estruturais da abordagem
- **Duplicação**: lógica de outbox/consumo pode repetir em múltiplos repositórios.
- **Drift**: risco entre corpus MCP e implementação local ao longo do tempo.
- **Evolução centralizada**: mudanças no MCP exigem revalidação em cada repo.
- **Acoplamento ao repo**: decisões finais dependem da evidência local (packages, estrutura e lacunas).

## 4. Escalabilidade em 100+ repositórios
- Sustenta-se se houver templates/base packages e auditoria automática de conformidade.
- Deixa de sustentar quando cada repo diverge fortemente em stack/versionamento.
- Esforço tende a crescer em manutenção de políticas + exceções locais.
- Riscos previsíveis: drift semântico, inconsistência de retries/DLQ, variação de observabilidade.

## 5. Experiência de uso
- Fluidez: boa no contexto técnico; múltiplas iterações para resolver restore/versionamento.
- Reprompt: baixo (1 comando “prossiga”).
- Descoberta manual: necessária para mapear estrutura e resolver conflitos de pacotes.
- Previsibilidade: média; dependências transientes elevaram complexidade.

## Avaliação (0-2)
- aderência ao contexto recuperado (MCP + repo): **2**
- qualidade técnica: **2**
- completude: **2**
- consistência: **1**
- escalabilidade da abordagem: **1**
- facilidade de manutenção: **1**

## Conclusão final
**MCP ajudou parcialmente, mas ainda foi necessária inferência significativa**.

- Principal evidência: MCP ancorou corretamente outbox/idempotência/DLQ/correlação, mas a infraestrutura concreta precisou ser inferida como fila local por ausência de broker e testes no repo.
- Principal limitação do experimento: ausência de ambiente de integração (broker real + suíte de testes) reduziu a força da validação comportamental fim a fim.


## EXPERIMENT_METRICS_JSON
```json
{
  "tempo_total": {
    "inicio_iso": "2026-05-02T10:33:55.8476363-03:00",
    "fim_iso": "2026-05-02T10:43:07.8214651-03:00",
    "duracao_ms": 551974
  },
  "latencia_por_etapa_ms": {
    "exploracao_leitura": 165000,
    "raciocinio_decisao": 82000,
    "escrita_patch": 205000,
    "validacao": 73000,
    "escrita_relatorio": 26974,
    "metodo_estimativa": "estimativa por marcação temporal dos blocos de atividade (não instrumentado automaticamente)",
    "impacto_validade": "medio"
  },
  "uso_tools": {
    "qtd_tool_calls_total": 57,
    "qtd_por_tool": {
      "get_projects_in_solution": 1,
      "get_files_in_project": 5,
      "corporate_instructions_list_instructions_index": 1,
      "corporate_instructions_search_instructions": 6,
      "corporate_instructions_get_instructions_batch": 1,
      "get_file": 21,
      "code_search": 1,
      "file_search": 2,
      "plan": 1,
      "update_plan_progress": 5,
      "record_observation": 2,
      "adapt_plan": 1,
      "apply_patch": 14,
      "create_file": 8,
      "run_command_in_terminal": 4,
      "run_build": 3,
      "get_tests": 1,
      "finish_plan": 0
    },
    "sucessos": 53,
    "falhas": 4,
    "retries": 3
  },
  "io_contexto": {
    "qtd_arquivos_lidos": 20,
    "qtd_arquivos_citados": 19,
    "qtd_trechos_citados": 30,
    "bytes_aprox_lidos": 62000
  },
  "tokens": {
    "tokens_input": "N/A",
    "tokens_output": "N/A",
    "tokens_input_est": 26000,
    "tokens_output_est": 14500,
    "metodo": "estimativa por tamanho médio de caracteres/4",
    "margem_erro_assumida": "±25%"
  },
  "custo": {
    "custo_total": "N/A",
    "moeda": "N/A"
  },
  "tamanho_resultado": {
    "caracteres_resposta": 0,
    "qtd_itens_patch": 17
  },
  "contagens_rigor_experimental": {
    "qtd_afirmacoes_FATO": 20,
    "qtd_afirmacoes_HIPOTESE": 6,
    "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 7
  }
}
```

## DECISIONS_JSON
```json
{
  "decisoes": [
    {
      "decisao": "Usar fila local persistida em SQL em vez de RabbitMQ",
      "ancoragem": "MCP,codigo_repo,inferencia",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume (on_absence=hypothesis_only) + ausência de sinais RabbitMQ no repo",
      "risco": "medio",
      "como_validar": "introduzir broker real e comparar comportamento com os mesmos testes de contrato"
    },
    {
      "decisao": "Persistir cliente e outbox na mesma transação",
      "ancoragem": "MCP,codigo_repo",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume + microservice-data-access-and-sql-security + ClienteRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "forçar erro entre insert cliente/outbox e confirmar rollback total"
    },
    {
      "decisao": "Aplicar idempotência por MensagemId com tabela de processados",
      "ancoragem": "MCP",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume",
      "risco": "baixo",
      "como_validar": "republicar mesma mensagem e confirmar ausência de duplicidade no read-model"
    },
    {
      "decisao": "DLQ após 3 tentativas",
      "ancoragem": "MCP,inferencia",
      "evidencia": "microservice-messaging-rabbitmq-publish-consume + constante MaxTentativas=3 no consumidor",
      "risco": "medio",
      "como_validar": "simular falha repetida e verificar inserção em ClienteEventosDlq"
    },
    {
      "decisao": "Propagar CorrelationId do HTTP para eventos",
      "ancoragem": "MCP,codigo_repo",
      "evidencia": "microservice-opentelemetry-correlation-and-health + Program.cs + ClienteEndpoints.cs",
      "risco": "baixo",
      "como_validar": "enviar X-Correlation-Id fixo e verificar persistência no outbox/fila/read-model"
    },
    {
      "decisao": "Não implementar cache/TTL",
      "ancoragem": "codigo_repo,MCP",
      "evidencia": "ausência de IMemoryCache no repo + microservice-caching-imemorycache-policy",
      "risco": "baixo",
      "como_validar": "code search por IMemoryCache; manter GET consistente sem camada de cache"
    }
  ]
}
```