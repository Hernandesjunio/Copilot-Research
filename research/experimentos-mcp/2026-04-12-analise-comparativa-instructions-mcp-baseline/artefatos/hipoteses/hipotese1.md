# Experimento — Avaliação de instructions locais para planejamento de endpoint `PUT /api/v1/clientes/{id}`

**Data/hora:** 2026-04-12 15:22:09  
**Escopo do experimento:** uso exclusivo de contexto local em `.github/copilot-instructions.md` e `.github/instructions/*` para planejar um novo endpoint de atualização completa de cliente e avaliar a sustentabilidade dessa abordagem em escala organizacional.

---

## 0. Planejamento técnico da implementação

### BMAD

- **Background:**
  - O repositório já está organizado em camadas `Api`, `Dominio`, `Interfaces`, `Modelo` e `Repositorio`, aderente a `microservice-architecture-layering` e `microservice-domain-interfaces-models-repository`.
  - Há endpoints Minimal API em `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`, com operações atuais de `GET` e `POST`.
  - O contrato público usa envelope `OpenFinanceResponse<T>` em `ClientesAPI.Api/Responses/OpenFinanceResponse.cs`.
  - O tratamento global de exceções existe em `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`, mas hoje o endpoint ainda repete `try/catch` local, o que conflita com `microservice-api-openfinance-patterns`.
  - O domínio está concentrado em `ClientesAPI.Dominio/Servicos/ClienteServico.cs` e o acesso a dados em `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs` com Dapper e timeout configurável.
  - Instruções mais relevantes usadas no plano: `assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-rest-http-semantics-and-status-codes`, `microservice-api-validation-and-error-contracts`, `microservice-api-openfinance-patterns`, `microservice-data-access-and-sql-security`, `microservice-clean-architecture-guardrails`, `microservice-di-options-extensions`, `microservice-testing-strategy-unit-integration-contract`, `microservice-opentelemetry-correlation-and-health`.

- **Mission:**
  - Planejar um endpoint de **substituição total** de cliente por `PUT /api/v1/clientes/{id}`.
  - O endpoint deve respeitar separação de camadas, SOLID, timeout/cancelamento, tratamento consistente de falhas e contrato HTTP adequado.
  - Critério de pronto: existir fluxo completo de atualização com validação de entrada, validação de domínio, persistência parametrizada, mapeamento de erros consistente e testes unitários/integrados/contratuais cobrindo cenários positivos e negativos.

- **Approach:**
  1. Definir o contrato de `PUT` como **substituição total** do recurso endereçado.
  2. Introduzir DTO dedicado para atualização completa, sem reutilizar cegamente o DTO de criação se isso tornar a semântica ambígua.
  3. Estender interface de serviço e repositório com método assíncrono e `CancellationToken`.
  4. Implementar regra de negócio no domínio: validar payload, garantir existência do cliente e aplicar regras de atualização.
  5. Implementar atualização no repositório com SQL parametrizado, timeout explícito e sem concatenação dinâmica.
  6. Expor endpoint na camada `Api` usando o envelope já existente, removendo tratamento duplicado de exceção do handler e delegando o fluxo excepcional ao middleware global.
  7. Evoluir o middleware global para mapear `400`, `404`, `409` e `422` de forma centralizada.
  8. Validar com testes de unidade, integração e contrato.
  9. Opcional/recomendado: preparar concorrência otimista para evitar lost update se o domínio exigir consistência forte.

- **Delivery/validation:**
  - Validar por testes unitários do serviço, testes de integração do repositório Dapper e testes HTTP do endpoint.
  - Validar respostas: `200` no sucesso, `400` para contrato inválido, `404` para cliente inexistente, `422` ou `409` para regra de negócio/conflito, `408` para timeout exposto contratualmente e `500` para falha inesperada.
  - Validar observabilidade mínima: logs estruturados sem PII sensível, correlação por request e readiness preservada.
  - Rollback: por ser adição de endpoint, rollback é simples via reversão do deploy; não requer feature flag se o contrato não for publicado antes da validação.

### Refinamento crítico

- **Riscos:**
  - **Semântico:** `PUT` mal implementado como atualização parcial disfarçada.
  - **Contrato:** reutilizar `ClienteRequisicao` pode confundir criação vs substituição total.
  - **Consistência:** sem controle de concorrência, duas atualizações simultâneas podem sobrescrever dados.
  - **Operacional:** tratamento de exceção hoje está parcialmente espalhado nos endpoints, favorecendo drift de comportamento.
  - **Segurança/privacidade:** logs ou payloads de erro podem expor email ou detalhes internos se o middleware crescer sem cuidado.

- **Dependências:**
  - Definição funcional do contrato de `PUT`: quais campos são realmente substituíveis.
  - Confirmação sobre política de concorrência: sem versão/ETag ou com versão/ETag.
  - Eventual alinhamento com consumidores caso o recurso público exija semântica específica de atualização.

- **Critérios de aceite técnico:**
  - Endpoint `PUT /api/v1/clientes/{id}` documentado em Minimal API.
  - Nenhuma regra de negócio implementada diretamente no endpoint.
  - SQL 100% parametrizado e com `CommandTimeout` explícito.
  - Todos os métodos novos assíncronos com `CancellationToken`.
  - Middleware global responsável pelo mapeamento de erro; endpoint sem `try/catch` de fluxo normal.
  - Testes cobrindo pelo menos: sucesso, `id` inexistente, payload inválido, timeout/cancelamento e conflito de concorrência se adotado.

---

## 0.1. Plano de implementação por camada

### Camada `Api`

**Arquivos prováveis:**
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`

**Mudanças planejadas:**
1. Adicionar `group.MapPut("/{id:guid}", AtualizarCliente)`.
2. Documentar o endpoint com `.WithName`, `.WithSummary`, `.WithDescription`, `.Accepts<T>()` e `.Produces<T>()` coerentes.
3. Usar `200 OK` com `OpenFinanceResponse<ClienteResposta>` no sucesso.
4. Não capturar exceções de regra de negócio no endpoint; delegar ao middleware.
5. Manter validações de contrato mínimas na borda:
   - `id` inválido/binding quebrado -> `400`
   - corpo ausente/malformado -> `400`
6. Centralizar no middleware o mapeamento de exceções tipadas:
   - `ArgumentException` -> `400`
   - `ClienteNaoEncontradoException` (ou equivalente) -> `404`
   - `BusinessRuleException` -> `422`
   - `ConcurrencyException`/`InvalidOperationException` específica -> `409`
   - `OperationCanceledException`/`TimeoutException` -> `408`
   - fallback -> `500`

**Observação crítica:** o código atual em `ClienteEndpoints.cs` ainda viola o padrão de tratamento global ao capturar exceções localmente. Para o novo endpoint, o ideal é corrigir o padrão e, se possível, alinhar também os existentes.

### Camada `Modelo`

**Arquivos prováveis:**
- novo DTO em `ClientesAPI.Modelo`

**Mudanças planejadas:**
1. Criar `AtualizarClienteRequisicao` para o `PUT`.
2. Recomendar que o DTO represente a **visão substituível do recurso**, não necessariamente toda a resposta pública.
3. Campos recomendados inicialmente:
   - `Nome`
   - `Email`
4. Não expor `DataCriacao` como campo atualizável.

**Lacuna com inferência controlada:** as instructions definem a semântica de `PUT`, mas não definem explicitamente quais campos do recurso `Cliente` são mutáveis. Há 3 opções viáveis:
1. **Recomendada:** `PUT` substitui apenas os campos mutáveis (`Nome`, `Email`) e preserva campos gerenciados pelo servidor (`Id`, `DataCriacao`).
2. `PUT` recebe um DTO mais completo com campo de versão para concorrência otimista.
3. `PUT` recebe a representação pública inteira e ignora campos imutáveis, desde que isso seja documentado com clareza.  

Sem definição do domínio, a opção 1 é a inferência mais segura.

### Camada `Interfaces`

**Arquivos prováveis:**
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`

**Mudanças planejadas:**
1. Adicionar no serviço:
   - `Task<ClienteResposta> AtualizarClienteAsync(Guid id, AtualizarClienteRequisicao requisicao, CancellationToken cancellationToken);`
2. Adicionar no repositório:
   - método para obter por `id` se ainda não existir contrato explícito;
   - método para atualizar cliente.
3. Manter interfaces pequenas e específicas, sem generalização prematura.

### Camada `Dominio`

**Arquivos prováveis:**
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- possivelmente novas exceções de domínio em `ClientesAPI.Dominio`

**Mudanças planejadas:**
1. Implementar `AtualizarClienteAsync` no serviço de domínio.
2. Validar regras básicas:
   - `Nome` obrigatório
   - `Email` obrigatório
   - formato consistente se essa regra for tratada como contrato ou domínio
3. Garantir existência antes de atualizar.
4. Lançar exceções tipadas em vez de depender de `ArgumentException` genérica para tudo.
5. Se houver política de unicidade para email, validar e retornar conflito (`409`) ou regra de negócio (`422`) conforme definição funcional.

**Recomendação arquitetural:** criar exceções específicas de domínio melhora clareza e reduz acoplamento do contrato HTTP ao tipo genérico de exceção.

### Camada `Repositorio`

**Arquivos prováveis:**
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`

**Mudanças planejadas:**
1. Adicionar query de busca por `id` caso necessária ao fluxo.
2. Adicionar comando `UPDATE` parametrizado com `CommandDefinition` e `CancellationToken`.
3. Preservar `DataCriacao` e retornar o estado persistido após atualização.
4. Se adotada concorrência otimista, incluir coluna de versão ou predicado adicional no `WHERE`.
5. Manter timeout explícito usando `SqlOptions.CommandTimeoutSeconds`.

**Pseudoestratégia SQL recomendada:**
- `UPDATE dbo.Cliente SET Nome = @Nome, Email = @Email WHERE Id = @Id;`
- seguido de `SELECT` do registro atualizado, ou `OUTPUT INSERTED...` se suportado no padrão local.

**Tolerância a falhas aplicável aqui:**
- timeout explícito;
- cancelamento cooperativo;
- transação curta apenas se houver múltiplos passos que precisem atomicidade;
- nada de retry cego em comando de escrita sem garantias claras, para evitar duplicidade ou sobrescrita indevida.

### DI e configuração

**Arquivos prováveis:**
- sem grandes mudanças além de manter os registrations existentes em extensions.

**Mudanças planejadas:**
1. Manter o padrão atual de `AddDomainExtensions` e `AddRepositoryExtensions`.
2. Não registrar concretos diretamente em `Program.cs`.
3. Se concorrência otimista ou feature correlata exigir novas options, adicionar classe tipada validada em startup.

### Resiliência e tolerância a falhas

**Aplicação pragmática ao caso:**
- Para este endpoint, o principal vetor de falha é banco SQL, não integração HTTP externa.
- Portanto, a aplicação mais relevante das instructions de resiliência é:
  - `CancellationToken` fim a fim;
  - timeout explícito de comando SQL;
  - falha rápida e mapeamento consistente de exceções;
  - evitar retry automático em `PUT` de escrita no banco sem idempotência/concor­rência controlada.
- Se no futuro o fluxo de atualização chamar serviço externo de validação cadastral, aí sim aplicar `HttpClientFactory` + timeout + retry com jitter + circuit breaker, conforme `microservice-resilience-polly-timeouts-and-circuit-breaker`.

### Observabilidade

**Mudanças recomendadas:**
1. Log estruturado no middleware e/ou serviço, sem registrar payload completo do cliente.
2. Correlação por `TraceId` nos erros.
3. Medir taxa de falha do endpoint e latência de atualização.
4. Não incluir email como atributo de alta cardinalidade em spans/logs.

### Testes

**Plano mínimo:**
- **Unitário (`Dominio`)**
  - atualiza cliente existente com sucesso;
  - rejeita nome vazio;
  - rejeita email vazio;
  - retorna exceção de não encontrado.
- **Integração (`Repositorio`)**
  - `UPDATE` persiste nome/email corretamente;
  - timeout/cancelamento respeitado;
  - conflito de concorrência, se implementado.
- **Contrato/API**
  - `PUT` retorna `200` e envelope esperado;
  - `404` para `id` inexistente;
  - `400` para payload inválido;
  - `422`/`409` para rejeições de domínio;
  - `408` quando a operação é cancelada/estoura timeout contratual.

---

## 1. Uso de contexto

### Sinais de uso efetivo das instructions locais

Há sinais concretos de uso real do contexto local, não apenas inferência genérica:

1. **Semântica de `PUT` como substituição total** veio diretamente de `microservice-rest-http-semantics-and-status-codes`.
2. **Separação por camadas** foi orientada por `microservice-architecture-layering` e `microservice-domain-interfaces-models-repository`.
3. **Tratamento centralizado de exceções** foi derivado de `microservice-api-openfinance-patterns` e confrontado com a implementação atual que ainda repete `try/catch` em endpoint.
4. **Uso de `CancellationToken`, SQL parametrizado e timeout** veio de `microservice-data-access-and-sql-security` e `microservice-clean-architecture-guardrails`.
5. **Estrutura BMAD** foi aplicada por exigência explícita de `assistant-workflow-bmad-planning-and-controlled-inference`.
6. **DI por extension methods e options tipadas** veio de `microservice-di-options-extensions`.
7. **Testes por tipo** foram orientados por `microservice-testing-strategy-unit-integration-contract`.
8. **Envelope de resposta** foi ancorado no próprio código do repositório e confirmado pela policy `microservice-api-openfinance-patterns`.

### Lacunas mesmo com instructions presentes

Sim, houve lacunas importantes:

1. As instructions definem arquitetura e políticas, mas **não definem o contrato funcional do recurso `Cliente`**.
2. Não está definido se `Email` deve ser único, se pode ser alterado, se existe auditoria, soft delete ou concorrência otimista.
3. Não há policy local explícita para **conflito de concorrência** no domínio atual.
4. O conjunto de instructions é forte em **como implementar**, mas mais fraco em **decisões de produto/negócio**.

### Dependência de inferência vs uso real de contexto

A resposta dependeu de ambos, mas com pesos diferentes:

- **Uso real de contexto:** alto para arquitetura, contrato HTTP, validação, DI, SQL, resiliência e testes.
- **Inferência:** moderada para regras de mutabilidade do recurso, estratégia de concorrência e taxonomia de exceções de domínio.

Avaliação: a base local foi suficiente para um **bom plano técnico**, mas insuficiente para fechar detalhes de contrato sem hipóteses controladas.

---

## 2. Qualidade técnica do plano

### Estrutura BMAD

A estrutura BMAD foi atendida de forma explícita:
- `Background` com arquivos e instructions aplicáveis;
- `Mission` com resultado observável;
- `Approach` com passos técnicos e trade-offs;
- `Delivery/validation` com estratégia de validação.

Também houve refinamento crítico com riscos, dependências e critérios de aceite, aderente ao workflow local.

### Clareza de camadas

A separação ficou clara:
- `Api`: contrato HTTP, metadata, resposta e delegação;
- `Dominio`: validação de negócio e orquestração;
- `Interfaces`: contratos assíncronos;
- `Modelo`: DTO de entrada/saída;
- `Repositorio`: persistência Dapper e SQL parametrizado.

Isso está alinhado ao desenho atual do repositório e às instructions.

### Uso de boas práticas (.NET, SOLID, resiliência)

Pontos positivos:
- respeito a `CancellationToken`;
- interfaces pequenas;
- DI por extensions;
- mapeamento centralizado de erro;
- SQL parametrizado com timeout;
- testes por pirâmide de responsabilidade;
- recomendação pragmática de não aplicar retry cego em escrita.

Ponto crítico:
- a instruction de resiliência tem foco forte em HTTP/Polly, mas o caso real é update em SQL. Logo, a aderência existe, porém por adaptação indireta, não por cobertura específica do cenário.

---

## 3. Limitações estruturais dessa abordagem

### Problemas de duplicação entre repositórios

Em 100+ repositórios, replicar `.github/instructions` localmente tende a criar:
- múltiplas cópias do mesmo guideline;
- revisões assíncronas;
- repositórios em versões diferentes da mesma norma;
- custo alto para auditoria de aderência.

### Risco de divergência entre instructions

O risco é alto. Mesmo com nomes iguais, dois repositórios podem carregar:
- textos ligeiramente diferentes;
- prioridades diferentes;
- exemplos defasados;
- interpretações conflitantes do mesmo status code ou padrão arquitetural.

Esse drift tende a aparecer primeiro em temas transversais: erro HTTP, observabilidade, resiliência, segurança e testes.

### Dificuldade de evolução centralizada

Sem um mecanismo central de versionamento e distribuição, a evolução depende de:
- abrir PR em massa;
- sincronizar revisões em dezenas de times;
- validar impacto de compatibilidade textual e operacional;
- aceitar janelas longas de inconsistência organizacional.

### Acoplamento ao repositório

O modelo é fortemente acoplado ao repositório porque o conhecimento normativo passa a morar junto com o código. Isso ajuda a contextualização local, mas piora:
- governança central;
- consistência transversal;
- descoberta da versão correta da regra;
- comparação entre serviços.

---

## 4. Escalabilidade (100+ repositórios)

### Essa abordagem se sustenta?

**Sozinha, não de forma saudável.** Ela se sustenta bem em poucos repositórios ou em domínios muito autônomos, mas como fonte única de verdade para 100+ repositórios tende a degradar rapidamente.

### Esforço de manutenção esperado

O esforço é **alto** e cumulativo:
- manutenção de conteúdo duplicado;
- revisão de drift;
- PRs sincronizados;
- reconciliação de exceções locais;
- treinamento para garantir que os entrypoints apontem para as instruções certas.

Se cada ajuste transversal exigir tocar 100 repositórios, o custo operacional cresce de forma desproporcional.

### Riscos operacionais

1. **Drift silencioso:** times copiam e adaptam sem governança.
2. **Falsa sensação de centralização:** parece padronizado, mas o padrão real diverge entre repositórios.
3. **Inconsistência de onboarding:** engenheiros novos veem regras diferentes conforme o repo.
4. **Regressão de políticas críticas:** segurança, logging, erro HTTP e observabilidade podem ficar defasados em parte da frota.
5. **Dificuldade de auditoria:** comprovar qual regra estava vigente em toda a organização vira tarefa cara.

---

## 5. Experiência de uso

### Fluidez

A fluidez local é boa para o agente quando:
- o entrypoint está claro;
- as instructions estão bem nomeadas;
- o repositório já segue a arquitetura descrita.

Neste experimento, isso ajudou bastante.

### Necessidade de reprompt

Para arquitetura e padrões técnicos, a necessidade de reprompt foi baixa.  
Para decisões de produto/contrato, ainda seria necessário reprompt humano, porque as instructions não substituem requisitos funcionais.

### Dependência de contexto manual

A dependência continua alta em dois níveis:
1. alguém precisa manter o entrypoint e as instruções locais corretas;
2. alguém precisa garantir que o conteúdo local esteja atualizado em relação ao padrão organizacional.

Ou seja, há boa usabilidade local, mas com forte custo de curadoria manual.

---

## Avaliação (0 a 10)

| Critério | Nota | Justificativa resumida |
| --- | ---: | --- |
| aderência ao contexto | 9 | O plano usou claramente as instructions locais e o padrão real do repositório. |
| qualidade técnica | 8 | Plano sólido, com camadas, contrato HTTP e testes; perdeu 2 pontos por depender de inferências funcionais inevitáveis. |
| completude | 8 | Cobriu endpoint, domínio, repositório, erros, resiliência, observabilidade e testes. |
| consistência | 8 | A linha arquitetural ficou consistente, embora o repositório atual já apresente pequenas divergências do guideline. |
| escalabilidade da abordagem | 4 | Funciona localmente, mas o modelo degrada bastante em 100+ repositórios. |
| facilidade de manutenção | 3 | Como fonte única de verdade distribuída, o custo de manter coerência é alto. |

---

## Conclusão final

**instructions locais funcionam, mas não escalam bem**

### Fundamentação da conclusão

Como mecanismo de **contextualização local**, a abordagem é boa. Ela melhora aderência arquitetural, reduz respostas genéricas e aproxima o plano do padrão do repositório.

Como **fonte única de verdade organizacional**, ela é fraca em escala porque:
- distribui o conhecimento em cópias;
- aumenta risco de drift;
- dificulta governança central;
- torna manutenção transversal cara;
- mistura padrão organizacional com contexto local do repositório.

### Leitura arquitetural final

A melhor leitura organizacional não é abolir instructions locais, e sim reposicioná-las:

- **bom uso:** contexto local, exceções do serviço, particularidades do domínio e entrypoints de navegação;
- **mau uso:** depender delas como autoridade única para padrões corporativos transversais em 100+ repositórios.

### Recomendação objetiva

Modelo mais sustentável:
1. **base central versionada** para policies organizacionais;
2. **instructions locais enxutas** apenas para contexto específico do repositório;
3. **referência/espelhamento controlado**, não cópia livre;
4. **mecanismo de atualização e auditoria** para evitar drift.

Esse arranjo preserva relevância local sem sacrificar governança em escala.
