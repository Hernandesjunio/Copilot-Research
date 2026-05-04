# Parte 1 — Execução

## 1) Seleção de guardrails e evidências (antes de codar)

### Instructions MCP selecionadas

| Instruction ID | kind | Decisão suportada | Evidência no repo | Status de aplicação |
|---|---|---|---|---|
| `microservice-saga-process-manager-and-compensation` | reference | saga manual, estado durável, compensações, timeout global, retry por passo, idempotência | ausência de `MassTransit`, `Saga`, `IBus`, `BackgroundService`; presença de API síncrona + Dapper | aplicada como guia, não como imposição total |
| `microservice-data-access-and-sql-security` | policy | persistência SQL parametrizada com Dapper e `CommandDefinition` | `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`, `DbConnectionFactory.cs` | aplicada |
| `microservice-rest-http-semantics-and-status-codes` | policy | `POST` para operação de processamento; códigos `201/400/408/503/500` | `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs` | aplicada com ressalva de contrato |
| `microservice-api-validation-and-error-contracts` | policy | `400` para entrada inválida e erro seguro no envelope existente | `OpenFinanceResponse.cs`, `ExceptionHandlingMiddleware.cs` | aplicada parcialmente |
| `microservice-clean-architecture-guardrails` | policy | separação por camadas, `CancellationToken`, evitar acoplamento de domínio ao transporte | estrutura `Api/Dominio/Interfaces/Repositorio` | aplicada |
| `microservice-di-options-extensions` | policy | `OnboardingOptions` tipado e DI por extension methods | `RepositoryExtensions.cs` | aplicada |
| `microservice-testing-strategy-unit-integration-contract` | policy | expectativa de testes/negativos | nenhum projeto de teste encontrado | não aplicada por ausência de base |
| `microservice-opentelemetry-correlation-and-health` | policy | correlação | ausência de `OpenTelemetry`/`ActivitySource`/health checks | não imposta; apenas inspiração mínima |
| `microservice-integration-httpclientfactory-contracts` | policy | decidir não introduzir `HttpClientFactory` sem evidência | ausência de `AddHttpClient` | usada para conter inferência |
| `.github/copilot-instructions.md` | instruction_local | responder em português, não assumir infra sem evidência, usar MCP antes de editar, declarar FATO/HIPÓTESE | arquivo local lido | aplicada |

### Módulos/ficheiros que ancoraram decisões

- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs` — padrão de rotas e envelope HTTP.
- `ClientesAPI.Api/Program.cs` — composição da aplicação mínima.
- `ClientesAPI.Dominio/Extensions/DomainExtensions.cs` — registro de serviços de domínio.
- `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs` — padrão de options + DI.
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs` — padrão Dapper parametrizado.
- `ClientesAPI.Api/appsettings.json` — configuração existente e inclusão de `Onboarding`.
- `ClientesAPI.Modelo/OnboardingSagaState.cs` — estado persistido essencial.
- `ClientesAPI.Dominio/Servicos/OnboardingSagaServico.cs` — orquestração manual implementada.
- `ClientesAPI.Repositorio/OnboardingSagaRepositorioDapper.cs` — store SQL da saga.
- `ClientesAPI.Repositorio/FormularioOnboardingGatewaySimulado.cs` — integração simulada com falha transitória/permanente.
- `ClientesAPI.Repositorio/NotificacaoOnboardingGatewaySimulado.cs` — notificação simulada idempotente.

### Nota crítica sobre uso de MCP

Foi seguido fluxo tool-first: índice → múltiplas buscas → batch → cruzamento com código.

**Crítica:** houve overfetch moderado. A instruction local sugeria até 6 IDs finais, mas foram lidos 10 IDs. Benefício: separou policies aplicáveis de policies com `workspace_evidence_required=true` sem sinais no repo. Custo: aumentou leitura e ruído; parte do corpus lido acabou servindo mais para conter inferência do que para dirigir código.

## 2) Cenário canónico

Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- Fluxo onboarding **3 passos** + **estado persistido** + **timeout global** + **retry** explícitos.
- **Compensações** idempotentes na ordem inversa; falhas por etapa cobertas pelos cenários esperados.
- **Sem** framework de saga externo obrigatório; **CorrelationId**/`SagaId` conforme projeto.

## 3) Plano BMAD

### Background
- O repositório já expunha CRUD de clientes em Minimal API.
- A persistência existente usa SQL Server + Dapper.
- Não havia evidência de framework de saga, mensageria, `HttpClientFactory`, OpenTelemetry ou suíte de testes.

### Mission
- Implementar uma saga manual de onboarding com 3 passos, estado durável, timeout, retry e compensações reversas idempotentes.

### Approach
- Reusar a arquitetura existente por camadas.
- Persistir estado em tabela própria (`OnboardingSagaState`) via Dapper.
- Simular formulário e notificação in-process, sem inventar URLs ou filas reais.
- Expor `POST /api/v1/clientes/onboarding` com `Idempotency-Key` obrigatório.
- Propagar `CorrelationId`/`SagaId` por headers e log scope, sem introduzir observabilidade nova sem evidência.

### Delivery/validation
- Criar contratos e options.
- Implementar store SQL da saga e gateways simulados.
- Implementar o orquestrador manual com retry/timeout/compensação.
- Expor endpoint.
- Validar com build e descoberta de testes; descrever comandos de validação funcional não executados.

## 4) Implementação (patch)

### Resumo do patch

**Criados**
- `ClientesAPI.Modelo/OnboardingOptions.cs`
- `ClientesAPI.Modelo/OnboardingSagaConstantes.cs`
- `ClientesAPI.Modelo/OnboardingSagaState.cs`
- `ClientesAPI.Modelo/OnboardingSagaResposta.cs`
- `ClientesAPI.Modelo/FormularioInicialResposta.cs`
- `ClientesAPI.Modelo/OnboardingDependencyException.cs`
- `ClientesAPI.Modelo/OnboardingSagaExecutionException.cs`
- `ClientesAPI.Interfaces/IOnboardingSagaServico.cs`
- `ClientesAPI.Interfaces/IOnboardingSagaRepositorio.cs`
- `ClientesAPI.Interfaces/IFormularioOnboardingGateway.cs`
- `ClientesAPI.Interfaces/INotificacaoOnboardingGateway.cs`
- `ClientesAPI.Repositorio/OnboardingSagaRepositorioDapper.cs`
- `ClientesAPI.Repositorio/FormularioOnboardingGatewaySimulado.cs`
- `ClientesAPI.Repositorio/NotificacaoOnboardingGatewaySimulado.cs`
- `ClientesAPI.Dominio/Servicos/OnboardingSagaServico.cs`

**Alterados**
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Program.cs`
- `ClientesAPI.Api/appsettings.json`
- `ClientesAPI.Dominio/Extensions/DomainExtensions.cs`
- `ClientesAPI.Repositorio/Extensions/RepositoryExtensions.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Dominio/ClientesAPI.Dominio.csproj`
- `ClientesAPI.Repositorio/ClientesAPI.Repositorio.csproj`

**Removido**
- `ClientesAPI.Repositorio/OnboardingSchemaInitializer.cs`

### FATO
- O endpoint novo foi exposto em `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs:29-38` e o handler exige `Idempotency-Key` em `:110-115`.
- A correlação é devolvida em headers `X-Correlation-Id` e `X-Saga-Id` em `ClienteEndpoints.cs:128-146`.
- O estado da saga contém `SagaId`, `ClienteId`, `PassoAtual`, `Estado`, tentativas e timestamps em `ClientesAPI.Modelo/OnboardingSagaState.cs:8-34`.
- O orquestrador manual executa cliente → formulário → notificação em `ClientesAPI.Dominio/Servicos/OnboardingSagaServico.cs:101-133`.
- O retry explícito do formulário existe em `OnboardingSagaServico.cs:175-223` com `RetryAttempts` e `RetryDelaySeconds` vindos de `appsettings.json:6-17`.
- As compensações reversas existem em `OnboardingSagaServico.cs:244-279`.
- A persistência durável da saga e das integrações simuladas é criada em SQL por `OnboardingSagaRepositorioDapper.cs:32-78`.
- A criação de cliente foi tornada reentrante por ID determinístico em `ClienteRepositorioDapper.cs:74-84`.

### HIPÓTESE
- A escolha por saga **síncrona no request** foi uma hipótese operacional. O repo não tinha worker/background nem contrato assíncrono prévio.
- O formulário e a notificação foram implementados como **simulados em SQL** por ausência de integração real no código.
- A estratégia de correlação por headers customizados foi uma hipótese mínima, porque não havia evidência de OpenTelemetry ou padrão institucional no repo.

### RISCO DE INTERPRETAÇÃO
- A rota pública `POST /api/v1/clientes/onboarding` não estava previamente acordada no repo. O usuário sugeriu esse formato, mas isso continua sendo contrato novo.
- A inicialização do schema em runtime via `Program.cs` + opção `InitializeSchemaOnStartup` é operacionalmente arriscada e tangencia conflito com policy de dados que desencoraja migração implícita em produção.
- O uso de `503` para falha de dependência e `408` para timeout está razoável, mas não foi validado contra contrato OpenAPI existente do serviço.
- Não houve evidência de padrão oficial do projeto para retorno de saga compensada; foi usado o envelope existente por consistência local, não por prova contratual formal.

## 5) Validação

### Validações executadas

| Verificação | Comando/fonte | Resultado |
|---|---|---|
| Build da solução | `run_build` | **OK** |
| Descoberta de testes | `get_tests` | **Nenhum teste encontrado** |
| Diagnóstico local de arquivos alterados | `get_errors` | **Sem erros finais** |

### Mapeamento dos critérios de aceite

| Critério | Como verificar | Resultado |
|---|---|---|
| Build | `dotnet build` | **Executado: OK** |
| Estado | Ver `OnboardingSagaState.cs` e `OnboardingSagaRepositorioDapper.cs` | **Atendido por inspeção de código** |
| Happy path | Subir API + `POST /api/v1/clientes/onboarding` com defaults | **Não executado automaticamente** |
| Falha etapa 2 | `FormularioPermanentFailure=true`; chamar endpoint; consultar tabelas | **Não executado automaticamente** |
| Falha etapa 3 | `NotificacaoPermanentFailure=true`; chamar endpoint; consultar tabelas | **Não executado automaticamente** |
| Timeout | `FormularioDelayMilliseconds=31000`; chamar endpoint; verificar `408` + compensação | **Não executado automaticamente** |
| Retry | `FormularioTransientFailuresBeforeSuccess=1`, `RetryAttempts=3`; verificar sucesso eventual | **Não executado automaticamente** |
| Idempotência | Repetir o mesmo `Idempotency-Key`; verificar ausência de duplicação | **Não executado automaticamente** |
| Correlação | Ver headers `X-Correlation-Id`/`X-Saga-Id` e log scope | **Atendido por inspeção de código** |

### Comandos exatos para validação funcional manual

#### Happy path
```powershell
$headers = @{ 'Idempotency-Key' = 'exp-happy-001'; 'X-Correlation-Id' = 'corr-happy-001' }
$body = @{ nome = 'Cliente Happy'; email = 'happy@example.com' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:5000/api/v1/clientes/onboarding' -Headers $headers -ContentType 'application/json' -Body $body
```
Critério de sucesso: `201`, `estado=Completa`, `passoAtual=NotificacaoEnviada`.

#### Falha etapa 2 com compensação
Configurar `Onboarding:FormularioPermanentFailure=true`.
```powershell
$headers = @{ 'Idempotency-Key' = 'exp-falha-form-001'; 'X-Correlation-Id' = 'corr-falha-form-001' }
$body = @{ nome = 'Cliente Falha Form'; email = 'falha-form@example.com' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:5000/api/v1/clientes/onboarding' -Headers $headers -ContentType 'application/json' -Body $body
```
Critério de sucesso: resposta de erro; `OnboardingSagaState.Estado=Compensada`; cliente removido.

#### Falha etapa 3 com compensação reversa
Configurar `Onboarding:NotificacaoPermanentFailure=true`.
Critério de sucesso: formulário marcado como excluído e cliente removido.

#### Retry com sucesso eventual
Configurar:
- `Onboarding:FormularioTransientFailuresBeforeSuccess=1`
- `Onboarding:RetryAttempts=3`
- `Onboarding:RetryDelaySeconds=5`

Critério de sucesso: primeira tentativa falha, segunda conclui, estado final `Completa`, `TentativasFormulario >= 2`.

#### Timeout global
Configurar:
- `Onboarding:FormularioDelayMilliseconds=31000`
- `Onboarding:GlobalTimeoutSeconds=30`

Critério de sucesso: retorno `408`, saga compensada, sem cliente órfão.

#### Consulta de evidência no banco
```sql
SELECT * FROM dbo.OnboardingSagaState ORDER BY CriadoEm DESC;
SELECT * FROM dbo.OnboardingFormularioSimulado ORDER BY CriadoEm DESC;
SELECT * FROM dbo.OnboardingNotificacaoSimulada ORDER BY EnviadoEm DESC;
SELECT * FROM dbo.Cliente ORDER BY DataCriacao DESC;
```

---

# Parte 2 — Relatório do experimento

## 0) Métricas de execução

### Observações sobre a qualidade das métricas
- A plataforma não expõe timestamps por tool call, tokens reais nem custo monetário.
- Portanto, tempos finos, custo e caracteres exatos foram marcados como `N/A` ou estimados manualmente.
- As contagens de tools foram estimadas por inspeção da própria sessão e são suficientemente úteis para análise comparativa, mas não têm precisão forense.

### Leitura crítica das métricas
- O fluxo foi pesado em exploração/contexto: muita leitura de corpus e repo antes do patch.
- O uso de MCP foi real, mas com custo de recuperação acima do mínimo local recomendado.
- A validação automática foi fraca: build sem testes e sem execução funcional dos cenários críticos.

## 1) Evidência de uso de contexto

### Decisões ancoradas em instruction MCP
- **Saga manual com compensações e estado durável**: ancorada em `microservice-saga-process-manager-and-compensation`.
- **Retry explícito, timeout e não repetir passos já concluídos**: ancorada em `microservice-saga-process-manager-and-compensation` e `microservice-resilience-polly-timeouts-and-circuit-breaker` como guia conceitual.
- **SQL parametrizado com Dapper**: ancorado em `microservice-data-access-and-sql-security`.
- **Uso de `POST` para processamento e mapeamento de status**: ancorado em `microservice-rest-http-semantics-and-status-codes`.
- **Options tipado e DI via extensions**: ancorado em `microservice-di-options-extensions`.

### Decisões ancoradas em instruction local
- **Não introduzir infra externa real**: ancorada em `.github/copilot-instructions.md`.
- **Diferenciar evidência de inferência**: ancorada em `.github/copilot-instructions.md`.

### Decisões ancoradas no código do repositório
- **Manter Minimal API**: ancorada em `Program.cs` e `ClienteEndpoints.cs`.
- **Manter envelope `OpenFinanceResponse`**: ancorada em `OpenFinanceResponse.cs`.
- **Persistir com Dapper/SQL Server**: ancorada em `ClienteRepositorioDapper.cs` e `DbConnectionFactory.cs`.

### Decisões dependentes de inferência
- **Contrato da nova rota pública**.
- **Estratégia mínima de correlação por headers customizados**.
- **Inicialização opcional do schema em runtime**.
- **Escolha de simulação in-process em vez de fila/HTTP real**.

### Onde houve uso efetivo do corpus MCP
- O corpus foi útil para delimitar o que **não** deveria ser inventado: sem framework de saga, sem mensageria real, sem `HttpClientFactory` sem evidência.
- O corpus também forneceu o desenho base de saga: estado durável, idempotência, compensação reversa, timeout e retry por passo.

### Onde houve lacunas
- O corpus não resolveu o contrato público da rota.
- O corpus não resolveu a política operacional para criação de schema em runtime.
- O corpus não resolveu observabilidade concreta porque faltavam sinais do repo.

## 2) Qualidade técnica do plano

### Avaliação
- **Estruturação do plano (BMAD):** adequada para a complexidade. Houve investigação, desenho, contratos, implementação e validação.
- **Adequação do patch ao plano:** razoável; o patch seguiu o plano macro.
- **Clareza de camadas:** boa. `Api` chama serviço, `Dominio` orquestra, `Repositorio` persiste/simula.
- **Coerência arquitetural:** parcial. A solução respeita a arquitetura existente, mas adiciona responsabilidade operacional sensível (`InitializeSchemaOnStartup`).
- **Nível de complexidade:** adequado ao cenário, mas com fragilidade de validação.
- **Genericidade/overengineering:** moderada. Foram criados muitos artefatos para um repo pequeno; isso melhora legibilidade do fluxo, mas aumenta custo de manutenção.

### Crítica direta
- O desenho técnico é aceitável para experimento, não para produção sem endurecimento operacional.
- O maior problema não é o código da saga em si; é a falta de evidência contratual e de testes automáticos.

## 3) Limitações estruturais da abordagem

### Duplicação entre repositórios
Alta probabilidade. Em 100+ repositórios, esse tipo de saga manual tenderá a ser reimplementado com pequenas variações de nomes, erros e opções.

### Risco de drift entre MCP e código local
Real. O corpus diz para evitar migração implícita em runtime; a solução introduziu inicialização opcional de schema em runtime. Isso já mostra tensão entre guardrail central e pragmatismo local.

### Dificuldade de evolução centralizada do corpus
Média/alta. O corpus ajuda em princípios, mas não substitui contratos locais nem templates executáveis. Em temas como saga, observabilidade e contratos HTTP, a instrução central sozinha não impede deriva.

### Acoplamento do conhecimento ao repositório
Moderado. A implementação ficou fortemente acoplada ao stack local (Minimal API + Dapper + SQL Server). Isso é bom para aderência local, mas ruim para reaproveitamento padronizado sem biblioteca/shared package.

## 4) Escalabilidade em 100+ repositórios

### Sustenta?
Parcialmente.

### Quando sustenta
- Quando o corpus é usado como guardrail de alto nível.
- Quando cada repo já tem padrões locais claros.
- Quando há bibliotecas compartilhadas para itens recorrentes (idempotência, correlation, outbox, saga state).

### Quando deixa de sustentar
- Quando o contrato público é ambíguo.
- Quando o repo não oferece evidência suficiente da stack de integração.
- Quando o corpus exige `workspace_evidence_required=true` e o repo é pobre em sinais.
- Quando se espera que o MCP substitua decisões operacionais concretas.

### Esforço de manutenção esperado
Alto, se a organização não transformar esse conhecimento em componentes reutilizáveis e exemplos canônicos por stack.

### Riscos operacionais previsíveis
- divergência de contratos HTTP;
- divergência de semântica de erro;
- mecanismos diferentes de idempotência entre repos;
- soluções improvisadas para schema/runtime;
- observabilidade inconsistente;
- cobertura de testes desigual.

## 5) Experiência de uso

### Fluidez
Boa na exploração; média na conclusão. O processo foi estável até a fase de fechamento/relato.

### Necessidade de reprompt
Baixa para a implementação; alta para o relatório porque os requisitos de experimento são extensos e prescritivos.

### Dependência de descoberta manual
Alta. O valor da solução dependeu fortemente de ler vários arquivos e várias instructions.

### Previsibilidade do comportamento
Média. O comportamento foi previsível para arquitetura e código; menos previsível para contrato público e métricas, por falta de telemetria da plataforma.

## Avaliação

| Critério | Nota (0-2) | Justificativa |
|---|---:|---|
| aderência ao contexto recuperado (MCP + repo) | 1 | houve uso real de MCP e repo, mas com overfetch e inferência relevante em contrato/observabilidade |
| qualidade técnica | 1 | a saga foi implementada com separação razoável, porém sem testes e com risco operacional no schema |
| completude | 1 | cobre os requisitos em código, mas não comprova cenários críticos por execução automática |
| consistência | 1 | o patch é internamente consistente, porém tensiona uma policy de dados em runtime |
| escalabilidade da abordagem | 1 | viável como guardrail; fraca como mecanismo único de padronização executável |
| facilidade de manutenção | 0 | muitos artefatos para repo pequeno e ausência de biblioteca compartilhada favorecem drift |

## Conclusão final

**MCP ajudou parcialmente, mas ainda foi necessária inferência significativa**

- **Principal evidência:** o corpus foi útil para ancorar a disciplina da saga (estado, timeout, retry, compensação, idempotência), mas não eliminou inferência na definição da rota pública, da correlação concreta e do comportamento operacional de schema.
- **Principal limitação do experimento:** não houve execução funcional automatizada contra banco/API para comprovar happy path, falhas, retry e timeout; a validação ficou concentrada em build + inspeção de código.

## EXPERIMENT_METRICS_JSON
```json
{
  "inicio_iso": null,
  "fim_iso": null,
  "duracao_ms": null,
  "latencia_exploracao_leitura_ms": null,
  "latencia_raciocinio_decisao_ms": null,
  "latencia_escrita_patch_ms": null,
  "latencia_validacao_ms": null,
  "latencia_escrita_relatorio_ms": null,
  "qtd_tool_calls_total": 104,
  "qtd_por_tool": {
    "get_projects_in_solution": 1,
    "corporate_instructions_list_instructions_index": 1,
    "get_files_in_project": 5,
    "corporate_instructions_search_instructions": 5,
    "corporate_instructions_get_instructions_batch": 1,
    "get_file": 44,
    "plan": 1,
    "update_plan_progress": 9,
    "file_search": 2,
    "record_observation": 4,
    "adapt_plan": 2,
    "create_file": 16,
    "get_errors": 4,
    "apply_patch": 5,
    "remove_file": 1,
    "get_tests": 1,
    "run_build": 1,
    "finish_plan": 1
  },
  "sucessos": 99,
  "falhas": 5,
  "retries": 4,
  "qtd_arquivos_lidos": 30,
  "qtd_arquivos_citados": 13,
  "qtd_trechos_citados": 20,
  "bytes_aprox_lidos": null,
  "tokens_input_est": 36000,
  "tokens_output_est": 7000,
  "tokens_metodo_estimativa": "Estimativa heurística por inspeção manual da conversa e dos outputs de tools, usando aproximação chars/4 com margem ampla devido aos resultados extensos de MCP e leitura de ficheiros.",
  "tokens_margem_erro_assumida": "±35%",
  "custo_total": null,
  "moeda": null,
  "caracteres_resposta": null,
  "qtd_itens_patch": 29,
  "qtd_afirmacoes_FATO": 18,
  "qtd_afirmacoes_HIPOTESE": 7,
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": 8
}
```

## DECISIONS_JSON
```json
{
  "decisoes": [
    {
      "decisao": "Implementar saga manual no processo, sem framework externo",
      "ancoragem": "MCP",
      "evidencia": "microservice-saga-process-manager-and-compensation + ausência de sinais de MassTransit/Saga/IBus no repo",
      "risco": "baixo",
      "como_validar": "inspecionar OnboardingSagaServico.cs e confirmar fluxo e compensações"
    },
    {
      "decisao": "Persistir estado da saga em SQL via Dapper",
      "ancoragem": "codigo_repo",
      "evidencia": "ClienteRepositorioDapper.cs; DbConnectionFactory.cs; OnboardingSagaRepositorioDapper.cs",
      "risco": "baixo",
      "como_validar": "executar API com SQL configurado e consultar dbo.OnboardingSagaState"
    },
    {
      "decisao": "Expor POST /api/v1/clientes/onboarding",
      "ancoragem": "inferencia",
      "evidencia": "N/A; usuário sugeriu exemplo de rota e o repo já usa /api/v1/clientes",
      "risco": "alto",
      "como_validar": "confirmar contrato com time dono da API/OpenAPI"
    },
    {
      "decisao": "Usar Idempotency-Key obrigatório e deduplicação por saga/operação",
      "ancoragem": "MCP",
      "evidencia": "microservice-saga-process-manager-and-compensation; microservice-rest-http-semantics-and-status-codes; ClienteEndpoints.cs; ClienteRepositorioDapper.cs",
      "risco": "medio",
      "como_validar": "repetir mesma requisição e verificar ausência de duplicações em Cliente/OnboardingFormularioSimulado/OnboardingNotificacaoSimulada"
    },
    {
      "decisao": "Simular formulário e notificação in-process",
      "ancoragem": "instruction_local",
      "evidencia": ".github/copilot-instructions.md: não assumir serviços/infra sem evidência no repo",
      "risco": "medio",
      "como_validar": "substituir gateways simulados por integrações reais somente quando houver evidência/configuração"
    },
    {
      "decisao": "Retry explícito apenas no passo de formulário",
      "ancoragem": "MCP",
      "evidencia": "microservice-saga-process-manager-and-compensation; OnboardingSagaServico.cs:175-223; appsettings.json:6-17",
      "risco": "baixo",
      "como_validar": "configurar FormularioTransientFailuresBeforeSuccess=1 e verificar sucesso eventual"
    },
    {
      "decisao": "Propagar correlação por X-Correlation-Id e X-Saga-Id",
      "ancoragem": "inferencia",
      "evidencia": "N/A; requisito do usuário + ausência de OpenTelemetry no repo",
      "risco": "medio",
      "como_validar": "confirmar padrão corporativo de correlação e alinhar headers/telemetria"
    },
    {
      "decisao": "Permitir inicialização opcional do schema no startup",
      "ancoragem": "inferencia",
      "evidencia": "Program.cs + appsettings.json",
      "risco": "alto",
      "como_validar": "substituir por migration/pipeline controlado para produção"
    }
  ]
}
```