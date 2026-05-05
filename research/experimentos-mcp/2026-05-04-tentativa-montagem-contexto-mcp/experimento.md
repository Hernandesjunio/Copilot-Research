Protocolo v3 — Experimento Comparativo com Cenários Complexos
0) Introdução e Contexto
Você evoluiu do CRUD simples (PUT/GET /clientes/{id}) para cenários que demandam:

Orquestração entre múltiplos serviços (mensageria, integrações externas),
Consistência eventual (padrões de saga, outbox, compensação),
Resiliência real (circuit breaker, retry, timeout, fallback),
Observabilidade distribuída (correlation IDs, tracing).
Este documento descreve 4 cenários complexos organizados por nível de complexidade, cada um com:

Descrição técnica do problema,
Ticket canônico para reprodutibilidade,
BMAD esperado (background, missão, approach, delivery),
Critérios de aceite objetivos,
Riscos e dependências explícitos,
Métricas a medir (tokens, latência, aderência, consistência),
Instruções MCP que devem ser consultadas (validação de escopo).
1) Cenário Complexo 1: Integração com Mensageria para Consistência Eventual
1.1 Descrição técnica
Problema real: Quando um cliente é criado ou atualizado, eventos precisam ser propagados para sistema de notificações, atualização de índices de busca, replicação em read-models etc. Sem orquestração correta, pode haver inconsistência entre serviços, perda de eventos ou replicação duplicada.

Padrão esperado: Usar padrão Outbox ou Inbox com mensageria (RabbitMQ, Azure Service Bus, MassTransit) para garantir consistência eventual com idempotência.

1.2 Ticket canônico
Code
Título: Implementar publicação de eventos de cliente via mensageria com garantia de entrega

Descrição:
Quando um cliente é criado (POST /clientes) ou atualizado (PUT /clientes/{id}):
1. Persistir o evento em uma tabela Outbox local (mesma transação de INSERT/UPDATE).
2. Publicar o evento para um tópico/fila de mensageria (RabbitMQ ou simulado).
3. Implementar consumidor que lê eventos do tópico e atualiza modelo de leitura (ClienteReadModel).
4. Garantir idempotência: mesmo evento publicado 2x não gera duplicação na read-model.
5. Implementar DLQ (Dead Letter Queue) para eventos que falharem após N retries.

Restrições:
- Não deve quebrar o CRUD existente (GET, PUT, POST, DELETE).
- Cache em GET deve ser invalidado após publicação (ou usar TTL curto se mensageria falhar).
- Build deve passar; testes de integração ideais (se repo permitir).

Cenários esperados:
- Cliente criado com sucesso → evento publicado e consumido.
- Cliente atualizado com sucesso → evento publicado e consumido (idempotência testada).
- Falha ao publicar → evento fica em Outbox; sistema de retry tira da fila.
- Consumidor falha 1x, sucesso 2x → DLQ vazio, read-model atualizado.
1.3 Palco BMAD esperado
Background
FATO: API ClientesAPI já possui CRUD funcional (POST, GET, PUT, DELETE).
FATO: não há mensageria configurada no projeto (sem RabbitMQ, Azure Service Bus, MassTransit).
FATO: não há tabela Outbox ou padrão de consistência eventual.
HIPÓTESE: o repositório SQL permite transações e adicionar tabela Outbox.
Mission
Introduzir padrão Outbox + mensageria para publicar eventos de cliente, garantindo entrega e idempotência na read-model.

Approach
Criar tabela ClienteEventosOutbox (Id, TipoEvento, Payload, CriadoEm, Processado).
Em ClienteServico: após INSERT/UPDATE bem-sucedido, adicionar evento ao Outbox na mesma transação.
Registrar interface IClienteEventPublisher e implementação que tenta publicar; se falhar, deixa em Outbox.
Criar consumidor via IMessageConsumer que lê ClienteCriado e ClienteAtualizado, atualiza ClienteReadModel.
Implementar IdempotencyKey ou hash do evento para evitar replicação.
Adicionar DLQ: eventos falhados após 3 retries vão para ClienteEventosDLQ.
Delivery/validation
Build sem erros.
Teste manual: criar cliente → verificar Outbox → consumidor executa → read-model atualizado.
Teste de idempotência: publicar mesmo evento 2x → read-model com 1 registro, não 2.
Teste de DLQ: consumidor falha 3x → evento vai para DLQ.
1.4 Instruções MCP esperadas
O modelo deve consultar (via search_instructions + get_instructions_batch):

microservice-architecture-layering — manter separação entre API, domínio e infra.
microservice-domain-interfaces-models-repository — onde vive a lógica de Outbox.
microservice-messaging-patterns-outbox-inbox (se existir) — padrão de consistência eventual.
microservice-idempotency-keys-deduplication (se existir) — como garantir idempotência.
microservice-resilience-polly-timeouts-and-circuit-breaker — retry e circuit breaker no publicador.
microservice-data-access-and-sql-security — SQL seguro para Outbox.
microservice-observability-correlation-ids — rastreamento de eventos end-to-end.
Lacuna esperada: se o corpus não contiver padrão de Outbox/Inbox, o modelo pode inventar (risco 4).

1.5 Critérios de aceite objetivos
Critério	Descrição	Pass/Fail
Build	dotnet build sem erros	✓ Pass
Outbox criada	Tabela com Id, TipoEvento, Payload, CriadoEm, Processado	✓ Pass
POST cria evento	Criar cliente → evento em Outbox	✓ Pass
PUT cria evento	Atualizar cliente → evento em Outbox	✓ Pass
Read-model atualizada	Consumidor lê evento → ClienteReadModel tem o cliente	✓ Pass
Idempotência	Publicar evento 2x → read-model com 1 registro	✓ Pass
DLQ funciona	Consumidor falha 3x → evento em DLQ	✓ Pass
Cache invalidado	Após PUT + publicação, GET reflete mudanças	✓ Pass
Correlação	Evento carrega CorrelationId do request HTTP	✓ Pass
Segurança	SQL parametrizado, sem injection	✓ Pass
1.6 Riscos e dependências
Risco	Probabilidade	Impacto	Mitigação
Repo não tem suporte a mensageria	Alta	Alto	Usar simulação in-memory ou RabbitMQ containerizado.
Sem tabela Outbox → modelo inventa	Média	Médio	Instruction sobre Outbox ou criar tabela antes do experimento.
Transações não isolam Outbox	Baixa	Alto	Usar transaction scope adequado; validar com testes.
DLQ infinito (sem dead-letter handling)	Baixa	Médio	Limite de retries explícito no consumidor.
1.7 Métricas a medir
Tool calls: quantas chamadas MCP para descobrir padrão de Outbox/Inbox?
Instructions consultadas: 6+ esperado (arquitetura, interfaces, mensageria, idempotência, resiliência, observabilidade).
Tokens input: estimativa de quanto contexto foi necessário.
Aderência: patch reflete exatamente o que as instructions sugeriram?
Consistência: modelo não inventou Outbox custom; usou padrão conhecido?
Tempo de implementação: quanto tempo (wall-clock) levou planejamento + implementação?
2) Cenário Complexo 2: Integração com Serviço Externo (Consulta CEP via ViaCEP/Correios)
2.1 Descrição técnica
Problema real: Ao criar/atualizar cliente, validar CEP consultando um serviço externo. O serviço pode estar lento, offline ou retornar erros. A solução deve ser resiliente (retry, timeout, circuit breaker, fallback).

Padrão esperado: HttpClientFactory com Polly para políticas de resiliência; possível cache do resultado de lookup.

2.2 Ticket canônico
Code
Título: Implementar validação de CEP com integração resiliente ao ViaCEP/Correios

Descrição:
Ao criar ou atualizar cliente com CEP:
1. Validar formato do CEP (8 dígitos, sem máscara).
2. Consultar ViaCEP (ou mock) para obter endereço (logradouro, bairro, cidade, estado).
3. Armazenar endereço completo ou erro de validação.
4. Implementar resiliência:
   - Timeout de 3s por chamada.
   - Retry com backoff exponencial (1s, 2s, 4s) para erros transientes (5xx, timeout).
   - Circuit breaker: após 5 falhas, bloquear chamadas por 30s.
   - Fallback: se circuit aberto, permitir cliente sem validação externa (marcar como "pendente validação").
5. Cache resultado de lookup por 24h (ou TTL configurável).
6. Registrar observabilidade: latência, sucesso/falha, circuit breaker ativo.

Restrições:
- Não quebrar CRUD existente.
- Não fazer chamada síncrona bloqueante se puder ser assíncrono.
- Validação de CEP deve ser dentro de transação para consistência.

Cenários esperados:
- CEP válido → endereço retornado e armazenado.
- ViaCEP timeout → retry → sucesso.
- ViaCEP fora do ar (5 falhas) → circuit breaker abre → fallback aplicado.
- Mesmo CEP consultado 2x com 1h intervalo → segundo vem de cache.
2.3 Palco BMAD esperado
Background
FATO: API possui CRUD de clientes.
FATO: não há integração externa no código atual.
FATO: não há HttpClientFactory configurado (ou existe mas sem policies).
HIPÓTESE: ViaCEP é público e sem autenticação; tolerância a latência.
Mission
Adicionar validação de CEP com resiliência, cache e observabilidade.

Approach
Registrar HttpClientFactory com named client viaCepClient.
Aplicar policies Polly: timeout 3s, retry exponencial, circuit breaker 5/30s.
Criar interface ICepValidator e implementação ViaCepValidator.
Em ClienteServico.CriarClienteAsync e AtualizarClienteAsync: chamar ValidarCepAsync antes de persistir.
Armazenar resultado em coluna EnderecoCompleto (json serialized com logradouro, bairro, cidade, estado).
Se falha transiente (circuit aberto ou timeout sem sucesso): permitir cliente mas marcar EnderecoValidadoEm = null.
Cache em IMemoryCache com chave cep:{zipcode} e TTL 24h.
Adicionar health check para circuit breaker de ViaCEP.
Delivery/validation
Build sem erros.
Teste: criar cliente com CEP válido → endereço armazenado.
Teste: simular timeout → retry → sucesso.
Teste: simular 5 falhas → circuit aberto → fallback.
Teste: mesmo CEP 2x → segundo de cache.
2.4 Instruções MCP esperadas
microservice-architecture-layering — camadas (API → Domínio → Gateway/Services → Http).
microservice-integration-httpclientfactory-contracts — como registrar HttpClient.
microservice-resilience-polly-timeouts-and-circuit-breaker — políticas Polly.
microservice-api-validation-and-error-contracts — validação de CEP e mapeamento de erro 400/422.
microservice-caching-imemorycache-policy — cache de resultado.
microservice-data-access-and-sql-security — armazenar endereço completo de forma segura (json).
microservice-observability-correlation-ids — rastrear chamadas a ViaCEP com correlation ID.
microservice-api-error-catalog-baseline — mapeamento de erros (ex: CEP não encontrado → 404, timeout → 408).
2.5 Critérios de aceite objetivos
Critério	Descrição	Pass/Fail
Build	dotnet build sem erros	✓ Pass
HttpClientFactory	Named client viaCepClient registrado com policies	✓ Pass
Validação básica	CEP sem formato válido → erro 400	✓ Pass
Consulta ViaCEP	CEP válido → consulta ViaCEP → endereço armazenado	✓ Pass
Timeout	Simular timeout → retry → sucesso	✓ Pass
Circuit Breaker	5 falhas → circuit aberto → fallback (cliente criado sem endereço)	✓ Pass
Cache	Mesmo CEP 2x → segundo de cache (não faz chamada HTTP)	✓ Pass
Correlation ID	Requisição HTTP carrega X-Correlation-Id; passado para ViaCEP	✓ Pass
Health Check	GET /health reporta status de circuit breaker	✓ Pass
Error handling	CEP não encontrado (404 do ViaCEP) → mapeado para 422 da API	✓ Pass
2.6 Riscos e dependências
Risco	Probabilidade	Impacto	Mitigação
ViaCEP offline durante experimento	Média	Alto	Usar mock HttpClient ou fixture com respostas pré-gravadas.
Sem HttpClientFactory no repo	Baixa	Médio	Instruction clara sobre setup; adicionar antes do experimento.
Modelo inventa policy própria sem Polly	Média	Médio	Instruction específica sobre Polly (retry, circuit breaker).
Serialização de JSON para endereço é ineficiente	Baixa	Baixo	Usar JsonColumn ou coluna varchar + validação.
2.7 Métricas a medir
Tool calls: quantas chamadas para descobrir HttpClientFactory + Polly?
Instructions consultadas: 7+ esperado.
Aderência: modelo usou Polly ou inventou retry custom?
Consistência: nível de rigor em política de retry e circuit breaker (5 falhas? 3s timeout? está aligned)?
Tempo: planejamento + implementação.
3) Cenário Complexo 3: Refactor Cross-Cutting — Implementar Autenticação/Autorização Distribuída
3.1 Descrição técnica
Problema real: A API atualmente não diferencia usuários. Necessário introduzir autenticação (JWT/OAuth) e autorização (role-based ou claims-based) sem quebrar fluxo existente. Refactor exige mudança em múltiplas camadas: middleware, controllers, serviços, queries.

Padrão esperado: Middleware de autenticação, policy-based authorization, injeção de ClaimsPrincipal em serviços.

3.2 Ticket canônico
Code
Título: Refactor para autenticação JWT com autorização por role

Descrição:
Introduzir autenticação JWT em todos os endpoints de cliente, com autorização por role:
1. Implementar middleware de validação de JWT (verificar token, claims).
2. Adicionar atributo [Authorize(Roles = "Admin,ClienteManager")] em endpoints de criação/atualização/deleção.
3. Em `ClienteServico`: recuperar `userId` do ClaimsPrincipal (Current User).
4. Adicionar coluna `CriadoPor` (Guid) e `UltimoAtualizadoPor` (Guid) na tabela Cliente.
5. Adicionar rota `GET /clientes/meus` que retorna só clientes do usuário autenticado (se role permitir).
6. Implementar `ClientePermissionHandler` que verifica: usuário só pode editar seus próprios clientes ou é Admin.
7. Auditar: registrar quem criou, atualizou, deletou cliente (tabela `ClienteAuditLog` opcional).

Restrições:
- Não quebrar GET /clientes (lista global se Admin; seus clientes se ClienteManager).
- Token JWT pode ser simulado ou usar AspNetCore.Identity (conforme disponível).
- Sem alterar contrato HTTP (status codes, envelope de resposta).

Cenários esperados:
- Sem token → 401 Unauthorized.
- Com token inválido → 401.
- Com token válido mas role insuficiente → 403 Forbidden.
- Admin vê todos os clientes.
- ClienteManager vê só seus clientes.
- ClienteManager tenta editar cliente de outro usuário → 403.
- Auditoria registra quem fez cada mudança.
3.3 Palco BMAD esperado
Background
FATO: API não possui autenticação; é open access.
FATO: não há integração com Identity provider.
HIPÓTESE: pode usar AspNetCore.Identity ou JWT local simulado.
Mission
Refactor para autenticação JWT e autorização por role, sem quebrar contrato HTTP.

Approach
Adicionar middleware JwtAuthenticationMiddleware ou usar AddAuthentication("Bearer").
Registrar IAuthorizationHandler para verificar propriedade de cliente.
Adicionar atributo [Authorize] em endpoints POST/PUT/DELETE.
Em ClienteServico: injetar IHttpContextAccessor ou ICurrentUserService para obter userId.
Adicionar colunas CriadoPor e UltimoAtualizadoPor.
Implementar query GetClientesByUserAsync (usuário vê só seus; Admin vê todos).
Implementar ClienteAuditLog: registrar operação, ator, timestamp.
Adicionar endpoint /clientes/meus para listar clientes do usuário.
Delivery/validation
Build sem erros.
Teste: GET /clientes sem token → 401.
Teste: GET /clientes com token Admin → lista todos.
Teste: GET /clientes com token ClienteManager → lista só seus.
Teste: POST com token ClienteManager → sucesso, criado com CriadoPor = userId.
Teste: PUT cliente de outro usuário com token ClienteManager → 403.
Teste: DELETE cliente próprio → sucesso, registrado em AuditLog.
3.4 Instruções MCP esperadas
microservice-architecture-layering — onde vive autorização (policy? handler?).
microservice-domain-interfaces-models-repository — como passar userId entre camadas.
microservice-api-validation-and-error-contracts — 401, 403 vs 400.
microservice-api-error-catalog-baseline — mapeamento de erros de autenticação.
microservice-security-baseline-secrets — onde armazenar chave JWT.
microservice-observability-correlation-ids — rastrear ações por usuário + correlation ID.
microservice-testing-strategy-unit-integration-contract (se existir) — como testar autorização.
Lacuna esperada: instruções específicas de AspNetCore.Identity ou JWT local podem não existir; modelo pode inventar.
3.5 Critérios de aceite objetivos
Critério	Descrição	Pass/Fail
Build	dotnet build sem erros	✓ Pass
Auth middleware	GET /clientes sem token → 401	✓ Pass
Admin vê todos	GET /clientes com token Admin → 200 com N clientes	✓ Pass
User vê seus	GET /clientes com token ClienteManager → 200 com seus clientes	✓ Pass
Create registra criador	POST /clientes com token → cliente.CriadoPor = userId	✓ Pass
Update reclusa	PUT cliente alheio com ClienteManager → 403	✓ Pass
Admin pode editar alheio	PUT cliente alheio com token Admin → 200	✓ Pass
Audit log	DELETE cliente → registro em AuditLog com ator + timestamp	✓ Pass
GET /clientes/meus	Endpoint existe, retorna clientes do user	✓ Pass
Contrato HTTP	Envelope de resposta inalterado (OpenFinanceResponse)	✓ Pass
3.6 Riscos e dependências
Risco	Probabilidade	Impacto	Mitigação
Sem Identity provider disponível	Alta	Médio	Usar JWT local com claims simuladas para teste.
Modelo inventa autorização custom sem pattern conhecido	Média	Alto	Instruction específica sobre resource-based ou policy-based auth.
Quebra contrato HTTP de clientes existentes	Baixa	Alto	Manter envelope OpenFinanceResponse; só adicionar 401/403.
Coluna CriadoPor vira null para clientes existentes	Médio	Médio	Migration script que popula com Guid.Empty ou usuário de sistema.
3.7 Métricas a medir
Tool calls: quantas para descobrir pattern de autenticação/autorização?
Instructions consultadas: 7+ esperado; lacuna em AspNetCore.Identity/JWT?
Aderência: modelo usou padrão conhecido (policy-based) ou inventou custom?
Completude: modelo implementou auditoria?
Consistência: nível de rigor em 403 vs 401.
Tempo: refactor de cross-cutting é sempre demorado.
4) Cenário Complexo 4: Saga Distribuída — Criar Cliente + Submeter Formulário + Notificar
4.1 Descrição técnica
Problema real: Workflow que envolve múltiplos serviços:

ClienteService: criar cliente.
FormularioService: criar formulário inicial (associado ao cliente).
NotificacaoService: enviar email de boas-vindas.
Se qualquer etapa falha, deve haver compensação (rollback). Sem orquestração correta, fica cliente criado mas sem formulário, ou formulário criado mas sem notificação.

Padrão esperado: Saga orquestrada (via mensageria) com steps e compensations, ou Saga coreografada (cada serviço publica eventos).

4.2 Ticket canônico
Code
Título: Implementar saga distribuída para onboarding de cliente

Descrição:
Ao chamar POST /clientes/onboarding:
1. Criar cliente (ClienteService).
2. Criar formulário inicial e associar ao cliente (FormularioService - chamada HTTP síncrona ou via fila).
3. Enviar email de boas-vindas (NotificacaoService - via fila).
4. Se qualquer etapa falha → compensar passos anteriores.

Exemplo de fluxo:
  Step 1: CreateCliente → sucesso → CorrelationId = UUID
  Step 2: CreateFormulario(clienteId) → falha → Compensar: DeleteCliente
  Result: Cliente não criado, formulário não criado, email não enviado.

Restrições:
- Sem Saga framework externo (NServiceBus/MassTransit/Temporal); usar padrão manual.
- Usar tabela SagaState para registrar progresso.
- Implementar timeout: se saga não completar em 30s, abortar e compensar.
- Idempotência em todos os compensations.

Cenários esperados:
- Happy path: create cliente + formulário + email → sucesso.
- Falha em Step 2: delete cliente (compensation).
- Falha em Step 3: delete cliente + formulário (compensations em ordem reversa).
- Retry automático de Step 2 após 5s → sucesso.
- Timeout após 30s → abortar + compensar.
4.3 Palco BMAD esperado
Background
FATO: ClienteService (seu atual microserviço).
FATO: FormularioService e NotificacaoService são externos (simulados).
FATO: não há orquestração de saga.
HIPÓTESE: há mensageria disponível ou pode usar HTTP síncrono com fallback.
Mission
Implementar onboarding de cliente como saga distribuída com compensations.

Approach
Criar tabela OnboardingSagaState (SagaId, ClienteId, Step, Status, CreatedAt, CompletedAt).
Implementar IOnboardingSagaOrchestrator com steps:
Step1_CreateCliente,
Step2_CreateFormulario,
Step3_SendEmail.
Cada step tem seu compensation (Compensate_DeleteCliente, etc).
Usar IClienteRepository, IFormularioHttpClient, INotificacaoPublisher.
Registrar cada step na OnboardingSagaState; se qualquer falha, executar compensations em ordem reversa.
Implementar timeout em 30s (cancelation token).
Implementar idempotency key em cada chamada para evitar duplicação se retry.
Delivery/validation
Build sem erros.
Teste happy path: POST /clientes/onboarding → cliente criado + saga completa.
Teste falha em Step 2: simular erro no FormularioService → compensar → cliente não criado.
Teste timeout: simular delay infinito → abort + compensate.
Teste retry: Step 2 falha 1x, sucesso 2x → saga completa.
4.4 Instruções MCP esperadas
microservice-architecture-layering — sagaOrchestrator em que camada?
microservice-domain-interfaces-models-repository — SagaState, interfaces de gateway.
microservice-messaging-patterns-outbox-inbox (ou similiar) — publicar eventos de saga.
microservice-idempotency-keys-deduplication — garantir idempotência em compensations.
microservice-resilience-polly-timeouts-and-circuit-breaker — timeout de saga.
microservice-data-access-and-sql-security — armazenar SagaState.
microservice-observability-correlation-ids — rastrear saga com CorrelationId.
microservice-testing-strategy-unit-integration-contract — como testar saga (se existir).
Lacuna esperada: instrução específica de padrão de saga (orquestrada vs coreografada).
4.5 Critérios de aceite objetivos
Critério	Descrição	Pass/Fail
Build	dotnet build sem erros	✓ Pass
SagaState criada	Tabela com SagaId, ClienteId, Step, Status	✓ Pass
Happy path	POST /onboarding → cliente + formulário + email	✓ Pass
Failure in Step 2	FormularioService erro → cliente deletado (compensate)	✓ Pass
Failure in Step 3	NotificacaoService erro → cliente + formulário deletados	✓ Pass
Timeout	Saga > 30s → abort + compensate	✓ Pass
Retry	Step 2 falha 1x → retry 5s → sucesso	✓ Pass
Idempotency	Mesma saga executada 2x → resultado idêntico, sem duplicação	✓ Pass
Correlation	SagaId == CorrelationId propagado em eventos/logs	✓ Pass
Rollback order	Compensations em ordem reversa (Step3 → Step2 → Step1)	✓ Pass
4.6 Riscos e dependências
Risco	Probabilidade	Impacto	Mitigação
Sem FormularioService/NotificacaoService implementados	Alta	Alto	Usar mocks HTTP ou publicadores de eventos simulados.
Modelo inventa saga pattern custom	Média	Médio	Instruction clara sobre saga orquestrada vs coreografada.
Sem mecanismo de timeout	Média	Médio	Usar CancellationToken com TimeoutAfter.
Compensations não são idempotentes	Baixa	Alto	Revisar cada compensation; usar idempotency key.
4.7 Métricas a medir
Tool calls: quantas para descobrir padrão de saga?
Instructions consultadas: 8+ esperado; lacuna em saga orquestrada/coreografada?
Aderência: modelo seguiu padrão esperado ou inventou custom?
Completude: todos os compensations foram implementados?
Consistência: nível de rigor em idempotência e timeout.
Tempo: saga é complexa; esperado > 2h.
5) Protocolo de Execução (para todos os 4 cenários)
5.1 Setup comum
Para cada cenário complexo:

Preparar tickets canônicos acima como artefatos separados (cenario-1-ticket.md, cenario-2-ticket.md, etc.).
Criar 3 condições experimentais (A = MCP, B = Instructions locais, C = Baseline).
Para cada condição:
Thread separada (sem contaminação).
Instrução de orquestração apropriada (ex.: copilot-instructions-mcp.md para A).
Executar com GPT 5.4 ou modelo equivalent.
Medir:
Tool calls (qtd, sucesso/falha, retries).
Instructions consultadas (qtd, quais IDs).
Tempo wall-clock por etapa (exploração, plano, implementação, validação).
Tokens input/output (estimado ou real se disponível).
Aderência (patch reflete contexto recuperado?).
Consistência (modelo não inventou padrão custom?).
Completude (todos os critérios de aceite cobertos?).
5.2 Artefatos por cenário
Para cada cenário (1, 2, 3, 4), organizar como:

Code
research/experimentos-mcp/2026-04-16-analise-complexa-mensageria-cep-auth-saga/
├── tickets/
│   ├── cenario-1-outbox-mensageria-ticket.md
│   ├── cenario-2-cep-viacao-ticket.md
│   ├── cenario-3-autenticacao-refactor-ticket.md
│   └── cenario-4-saga-distribuida-ticket.md
├── orquestrador/
│   ├── copilot-instructions.md (neutro)
│   ├── copilot-instructions-mcp.md
│   ├── copilot-instructions-instructions-locais.md
│   └── copilot-instructions-baseline.md
├── artefatos/
│   ├── cenario-1/
│   │   ├── hipotese-a-mcp.md (resultado de execução)
│   │   ├── hipotese-b-instructions.md
│   │   └── hipotese-c-baseline.md
│   ├── cenario-2/
│   │   ├── hipotese-a-mcp.md
│   │   ├── hipotese-b-instructions.md
│   │   └── hipotese-c-baseline.md
│   ├── cenario-3/
│   │   ├── hipotese-a-mcp.md
│   │   ├── hipotese-b-instructions.md
│   │   └── hipotese-c-baseline.md
│   └── cenario-4/
│       ├── hipotese-a-mcp.md
│       ├── hipotese-b-instructions.md
│       └── hipotese-c-baseline.md
├── planos-de-melhoria/
│   ├── plano-bmad-melhorias-cenarios-complexos-v1.md
│   └── (se necessário, após primeira iteração)
├── analises-comparativas/
│   ├── analise-cenario-1.md (MCP vs Instructions vs Baseline)
│   ├── analise-cenario-2.md
│   ├── analise-cenario-3.md
│   ├── analise-cenario-4.md
│   └── analise-integrada-todos-cenarios.md (síntese final)
├── README.md (índice e links)
└── notas.md (observações e evoluções entre iterações)
5.3 Rubrica de avaliação (estendida para complexidade)
Critério	Peso	Escala	Observação
Qualidade do plano BMAD	15%	0-10	Background claro, mission bem definida, approach com passos explícitos.
Aderência ao contexto	15%	0-10	Quantas instructions foram consultadas? Quantas cidades? Overlap com padrão conhecido?
Completude	12%	0-10	Todos os critérios de aceite foram implementados?
Consistência interna	12%	0-10	Padrão não inventado? Sem contradição entre componentes?
Tratamento de resiliência	10%	0-10	Retry, timeout, circuit breaker implementados? Conservadorismo respeitado?
Observabilidade	10%	0-10	Correlation IDs, logs, métricas registradas?
Escalabilidade projetada	10%	0-10	Soluções sustentáveis em multi-repo? DDD/Clean Architecture respeitados?
Segurança	10%	0-10	SQL injection evitado? Secrets não expostos? Autorização robusta?
DX	6%	0-10	Fluidez? Zero falhas de tool? Previsibilidade?
Tempo de execução	?	N/A	Apenas métrica (não entra na agregação; reportado separadamente).
Nota agregada: média ponderada dos 9 critérios (0-10).

6) Como usar este documento
6.1 Antes de executar
Baixar e revisar cada ticket canônico (seções 1.2, 2.2, 3.2, 4.2).
Revisar critérios de aceite específicos (seções 1.5, 2.5, 3.5, 4.5).
Listar instruções MCP esperadas (seções 1.4, 2.4, 3.4, 4.4).
Identificar lacunas no corpus — há instruction para Outbox/Inbox? JWT? Saga?
Completar corpus antes do experimento se lacuna crítica.
6.2 Durante execução (protocolo)
Para cada cenário (1-4), para cada condição (A, B, C):

Thread separada — evitar contaminação.
Copiar ticket canônico no início do artefato.
Executar plano BMAD explicitamente (antes de implementação).
Implementar patch conforme plano.
Validar objetivamente (build, critérios de aceite).
Registrar métricas (tool calls, instructions, tempo, aderência).
Produzir relatório (Parte 1 = execução; Parte 2 = análise técnica).
6.3 Após cada cenário
Síntese comparativa (MCP vs Instructions vs Baseline).
Identificar lacunas de contexto (corpus).
Se MCP perdeu: planejar melhorias de tools/prompt.
Re-executar o cenário apenas no MCP com melhorias (isolando efeito).
6.4 Após os 4 cenários
Análise integrada — padrões cross-cutting.
Evolução de critérios — como métricas mudaram de cenário 1 para 4?
Viabilidade corporativa — MCP sustenta em todos os 4 cenários?
Roadmap de corpus — quais instruções críticas ainda faltam?
Decisões de arquitetura — MCP continua sendo o melhor caminho?
7) Métricas Consolidadas (template para cada experimento)
JSON
{
  "experimento": "cenario-X-nome",
  "data_inicio": "2026-04-17T10:00:00Z",
  "data_fim": "2026-04-17T12:30:00Z",
  "duracao_ms": 9000000,
  "cenario": "A|B|C",
  
  "metricas_tool": {
    "qtd_tool_calls_total": 45,
    "qtd_por_tool": {
      "list_instructions_index": 1,
      "search_instructions": 8,
      "get_instructions_batch": 5,
      "get_file": 30,
      "apply_patch": 7,
      "run_command_in_terminal": 2
    },
    "sucessos": 45,
    "falhas": 0,
    "retries": 0
  },
  
  "metricas_contexto": {
    "qtd_arquivos_lidos": 22,
    "qtd_arquivos_citados": 14,
    "qtd_trechos_citados": 28,
    "bytes_aprox_lidos": 58000,
    "qtd_instructions_consultadas": 9,
    "instruction_ids": [
      "microservice-architecture-layering",
      "microservice-messaging-patterns-outbox-inbox",
      "microservice-idempotency-keys-deduplication",
      "..."
    ]
  },
  
  "metricas_tokens": {
    "tokens_input_est": 24000,
    "tokens_output_est": 8500,
    "metodo_estimativa": "caracteres/4 + margem ±30%",
    "custo_est_usd": null
  },
  
  "metricas_tempo": {
    "exploracao_ms": 420000,
    "raciocinio_decisao_ms": 180000,
    "escrita_plano_ms": 240000,
    "implementacao_ms": 1800000,
    "validacao_ms": 300000,
    "relatorio_ms": 360000
  },
  
  "metricas_qualidade": {
    "qtd_afirmacoes_FATO": 18,
    "qtd_afirmacoes_HIPOTESE": 5,
    "qtd_afirmacoes_RISCO": 6,
    "ratio_FATO_vs_HIPOTESE": 3.6
  },
  
  "avaliacoes_rubrica": {
    "qualidade_plano": 8,
    "aderencia_contexto": 9,
    "completude": 7,
    "consistencia_interna": 7,
    "tratamento_resiliencia": 8,
    "observabilidade": 7,
    "escalabilidade": 8,
    "seguranca": 8,
    "dx": 8,
    "nota_agregada": 7.9
  },
  
  "conclusoes": "MCP demonstrou capacidade de descobrir e aplicar padrões complexos de mensageria. Gap: corpus não tinha instrução específica de saga orquestrada vs coreografada; modelo inventou padrão. Recomendação: adicionar instrução sobre saga patterns antes de próxima iteração."
}
8) Próximas ações recomendadas
Completar corpus com instruções faltantes:

microservice-messaging-patterns-outbox-inbox (cenário 1).
microservice-resilience-polly-timeouts-and-circuit-breaker (cenário 2, 3).
microservice-security-baseline-secrets + microservice-authorization-policy-based (cenário 3).
microservice-saga-patterns-orchestrated-choreographed (cenário 4).
Executar cenários em sequência (1 → 2 → 3 → 4), documentando melhorias de corpus entre cada.

Medir impacto de corpus — antes vs depois de adicionar instruções específicas.

Testar com múltiplos modelos — GPT 5.4, Claude 3.5, outros — para validar robustez.

Validação em múltiplos repositórios — não só seu projeto de clientes; testar em 2-3 repos alheios.