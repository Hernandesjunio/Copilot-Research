# Experimento — Avaliação do MCP para planejamento do endpoint `PUT /api/v1/clientes/{id}`

**Data/hora:** 2026-04-12 15:27:07  
**Objetivo do experimento:** avaliar o MCP customizado como mecanismo principal de contexto para planejar a implementação de um endpoint de atualização completa de cliente, com foco em arquitetura, centralização de conhecimento, extensibilidade do Copilot e viabilidade corporativa em escala.

---

## 0. Planejamento técnico da implementação

### BMAD

- **Background:**
  - O repositório está estruturado em camadas `Api`, `Dominio`, `Interfaces`, `Modelo` e `Repositorio`, o que converge com `microservice-architecture-layering` e `microservice-domain-interfaces-models-repository`.
  - O endpoint atual está em `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`, com operações `GET /api/v1/clientes/` e `POST /api/v1/clientes/`.
  - O contrato público hoje usa `OpenFinanceResponse<T>` em `ClientesAPI.Api/Responses/OpenFinanceResponse.cs`.
  - O tratamento global de falhas existe em `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`, porém ainda cobre poucos tipos de erro e o endpoint atual repete `try/catch`, o que conflita com `microservice-api-openfinance-patterns` e `microservice-api-validation-and-error-contracts`.
  - O domínio atual está em `ClientesAPI.Dominio/Servicos/ClienteServico.cs`, com validações simples e delegação para `IClienteRepositorio`.
  - A persistência usa Dapper em `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`, com `CommandDefinition`, `CancellationToken` e timeout por `SqlOptions`, alinhado a `microservice-data-access-and-sql-security`.
  - O contexto normativo principal veio do MCP, especialmente dos ids: `assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-rest-http-semantics-and-status-codes`, `microservice-api-validation-and-error-contracts`, `microservice-api-openfinance-patterns`, `microservice-clean-architecture-guardrails`, `microservice-data-access-and-sql-security`, `microservice-opentelemetry-correlation-and-health` e `microservice-testing-strategy-unit-integration-contract`.

- **Mission:**
  - Planejar a implementação de um endpoint de substituição total do cliente por `PUT /api/v1/clientes/{id}`.
  - O plano deve respeitar separação por camadas, SOLID, semântica REST correta, tratamento centralizado de erros, tolerância a falhas e observabilidade mínima.
  - Critério de pronto do plano: existir desenho de fluxo completo cobrindo contrato HTTP, DTOs, domínio, persistência, tratamento de falhas, resiliência operacional e testes.

- **Approach:**
  1. Definir `PUT` como **substituição total** do recurso endereçado, conforme `microservice-rest-http-semantics-and-status-codes`.
  2. Introduzir DTO dedicado de atualização completa, evitando ambiguidade entre criação e substituição.
  3. Estender `IClienteServico` e `IClienteRepositorio` com métodos assíncronos usando `CancellationToken`.
  4. Implementar a orquestração no domínio, incluindo validações de negócio e verificação de existência do cliente.
  5. Implementar atualização no repositório com SQL parametrizado, timeout explícito e retorno do estado persistido.
  6. Expor `MapPut("/{id:guid}", AtualizarCliente)` na camada `Api`, mantendo o envelope `OpenFinanceResponse<T>`.
  7. Remover do novo endpoint o padrão de `try/catch` de fluxo normal e delegar o mapeamento de falhas ao middleware global.
  8. Evoluir o middleware para diferenciar `400`, `404`, `409`, `412`, `422`, `408` e `500`, conforme política adotada.
  9. Cobrir o fluxo com testes unitários, integração e contrato.

- **Delivery/validation:**
  - Validar semanticamente o endpoint com os seguintes cenários: sucesso, cliente inexistente, payload inválido, violação de regra de negócio, cancelamento/timeout e conflito de concorrência se adotado.
  - Validar que nenhuma regra de negócio fique no endpoint e que o repositório permaneça parametrizado e desacoplado do contrato HTTP.
  - Validar observabilidade mínima: correlação por `TraceId`, logs estruturados sem PII e readiness preservada.
  - Como é apenas adição de endpoint, rollback é simples por reversão do deploy. Se houver publicação antecipada de contrato, considerar feature flag de exposição.

### Refinamento crítico

- **Riscos:**
  - **Semântico:** implementar `PUT` como patch disfarçado.
  - **Arquitetural:** perpetuar o anti-padrão atual de `try/catch` por endpoint.
  - **Consistência:** sobrescrita concorrente sem controle de versão.
  - **Operacional:** timeout de banco tratado de modo genérico, sem taxonomia clara entre cancelamento, timeout e falha interna.
  - **Privacidade:** logs de erro podem expor email se o middleware evoluir sem critérios de masking.

- **Dependências:**
  - Definição funcional de quais campos de `Cliente` são realmente mutáveis.
  - Decisão do time sobre concorrência otimista: sem versão, com `rowversion`, ou com `ETag`/`If-Match` na API.
  - Confirmação se existe regra de unicidade para `Email`.
  - Definição se o produto quer `409` ou `422` para determinadas rejeições de domínio persistente.

- **Critérios de aceite técnico:**
  - Novo endpoint documentado e versionado em `ClienteEndpoints`.
  - Fluxo fim a fim com `CancellationToken` em todas as camadas novas.
  - Middleware global responsável pelo mapeamento de falhas; sem `try/catch` de negócio no handler.
  - SQL de atualização 100% parametrizado e com `CommandTimeout` explícito.
  - Testes cobrindo positivos e negativos relevantes.
  - Sem exposição de PII em logs, spans ou payloads de erro.

- **Alternativas rejeitadas:**
  1. **Reutilizar `ClienteRequisicao` para `POST` e `PUT` sem distinção semântica.** Rejeitada por conflitar com a policy de `PUT` vs `PATCH` e por esconder intenção.
  2. **Implementar validação de negócio diretamente no endpoint.** Rejeitada por violar separação de camadas.
  3. **Aplicar retry automático no comando SQL de update.** Rejeitada por risco de mascarar escrita não idempotente sob falhas ambíguas.

---

## 0.1. Plano de implementação por camada

### Camada `Api`

**Arquivos-alvo prováveis:**
- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`

**Mudanças planejadas:**
1. Adicionar `group.MapPut("/{id:guid}", AtualizarCliente)`.
2. Documentar o endpoint com `.WithName`, `.WithSummary`, `.WithDescription`, `.Accepts<T>()` e `.Produces<T>()`.
3. Retornar `200 OK` com `OpenFinanceResponse<ClienteResposta>` no sucesso.
4. Declarar contratos de erro coerentes com a policy:
   - `400` para input inválido/malformado.
   - `404` para `id` inexistente.
   - `409` para conflito persistente ou duplicidade.
   - `412` se a API adotar pré-condição com `ETag`/versão.
   - `422` para regra de negócio com payload válido.
   - `408` para cancelamento/timeout mapeado contratualmente.
   - `500` para falha inesperada.
5. Não repetir `try/catch` no novo handler; delegar exceções ao middleware.
6. Opcional, mas recomendado: alinhar também os handlers existentes para reduzir drift comportamental.

### Camada `Modelo`

**Arquivos-alvo prováveis:**
- novo DTO em `ClientesAPI.Modelo`

**Mudanças planejadas:**
1. Criar `AtualizarClienteRequisicao`.
2. Modelar apenas campos substituíveis do recurso, mantendo `Id` e `DataCriacao` como geridos pelo servidor.
3. Se houver concorrência otimista por payload, incluir campo de versão; se for por header, manter o DTO limpo.

### Camada `Interfaces`

**Arquivos-alvo prováveis:**
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`

**Mudanças planejadas:**
1. Adicionar no serviço:
   - `Task<ClienteResposta> AtualizarClienteAsync(Guid id, AtualizarClienteRequisicao requisicao, CancellationToken cancellationToken);`
2. Adicionar no repositório:
   - `Task<ClienteResposta?> ObterPorIdAsync(Guid id, CancellationToken cancellationToken);`
   - `Task<ClienteResposta> AtualizarAsync(Guid id, AtualizarClienteRequisicao requisicao, CancellationToken cancellationToken);`
3. Se houver concorrência otimista, expor contrato específico para versão/precondição sem contaminar o endpoint com detalhe de banco.

### Camada `Dominio`

**Arquivos-alvo prováveis:**
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- novas exceções de domínio em `ClientesAPI.Dominio`

**Mudanças planejadas:**
1. Implementar `AtualizarClienteAsync` no serviço.
2. Validar obrigatoriedade de `Nome` e `Email`.
3. Garantir existência do cliente antes de atualizar.
4. Lançar exceções tipadas para `não encontrado`, `regra de negócio` e `conflito`, em vez de usar apenas `ArgumentException`.
5. Se existir unicidade de email, decidir o mapeamento:
   - **Opção 1 (recomendada):** duplicidade persistente -> `409`.
   - **Opção 2:** regra de domínio mais ampla -> `422`.
   - **Opção 3:** pré-condição com versão -> `412` para concorrência e `409` para duplicidade.

### Camada `Repositorio`

**Arquivos-alvo prováveis:**
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`

**Mudanças planejadas:**
1. Adicionar busca por `id` com query parametrizada.
2. Adicionar comando `UPDATE` parametrizado usando `CommandDefinition` com timeout explícito.
3. Retornar o estado persistido após atualização.
4. Preservar `DataCriacao`.
5. Se concorrência otimista for adotada, incluir predicado de versão no `WHERE`.

**Estratégia SQL recomendada:**
- `UPDATE dbo.Cliente SET Nome = @Nome, Email = @Email WHERE Id = @Id;`
- seguido de `SELECT` do estado atualizado ou uso de `OUTPUT INSERTED...`.

**Práticas de tolerância a falhas aplicáveis:**
- timeout explícito;
- cancelamento cooperativo;
- transação curta apenas se houver mais de um passo atômico;
- sem retry automático de escrita por padrão.

### Observabilidade e operação

**Mudanças recomendadas:**
1. Incluir log estruturado no middleware com `TraceId` e categoria estável.
2. Não logar payload completo do cliente.
3. Medir latência e taxa de falhas do endpoint.
4. Se o serviço evoluir para OpenTelemetry completo, incluir instrumentação de ASP.NET Core e SQL.

### Testes

**Plano mínimo:**
- **Unitário (`Dominio`)**
  - atualiza cliente existente;
  - rejeita `Nome` vazio;
  - rejeita `Email` vazio;
  - retorna erro de não encontrado;
  - retorna erro de conflito quando aplicável.
- **Integração (`Repositorio`)**
  - `ObterPorIdAsync` retorna cliente existente;
  - `AtualizarAsync` persiste corretamente;
  - timeout/cancelamento é respeitado;
  - concorrência otimista é respeitada, se adotada.
- **Contrato/API**
  - `PUT` retorna `200` com envelope esperado;
  - `404` para `id` inexistente;
  - `400` para payload inválido;
  - `409`/`412`/`422` conforme regra escolhida;
  - `408` para timeout/cancelamento mapeado.

---

## 0.2. Lacunas com inferência controlada

Há falta de informação decisiva em pontos funcionais. Seguem opções com recomendação explícita:

### A. Contrato do DTO de `PUT`

1. **Recomendada:** criar `AtualizarClienteRequisicao` com `Nome` e `Email`, preservando campos geridos pelo servidor.  
2. Reutilizar `ClienteRequisicao` por simplicidade, desde que o time aceite ambiguidade semântica controlada.  
3. Criar DTO completo com versão (`Version`/`RowVersion`) para já suportar concorrência otimista.  

**Recomendação:** opção 1, com possível evolução para opção 3.

### B. Estratégia de concorrência

1. **Recomendada para cenário corporativo:** adotar concorrência otimista com versão/`ETag`, retornando `412` em pré-condição falhada.  
2. Adotar `409` com detecção de conflito no repositório, sem `ETag` exposto na API.  
3. Operar em last-write-wins sem controle explícito.  

**Recomendação:** opção 1 em produção; opção 2 como etapa intermediária; opção 3 não é recomendada.

### C. Classificação de erro para email duplicado

1. **Mais provável:** `409`, por conflito persistente com estado atual.  
2. `422`, se o produto tratar toda rejeição de domínio sob a mesma semântica.  
3. `400`, se a regra for tratada como validação estrita de contrato.  

**Recomendação:** opção 1.

---

## 1. Uso do MCP

### Evidências de uso efetivo das tools

Houve uso real e relevante do MCP, não apenas menção superficial:

1. Foi consultado o índice central de instructions para identificar corpus disponível e seus `ids`.
2. Foi feita busca temática por arquitetura, `PUT`, validação, resiliência, domínio, repositório e observabilidade.
3. Foram recuperadas instructions completas para decisões normativas, incluindo:
   - `assistant-workflow-bmad-planning-and-controlled-inference`
   - `microservice-rest-http-semantics-and-status-codes`
   - `microservice-api-validation-and-error-contracts`
   - `microservice-api-openfinance-patterns`
   - `microservice-architecture-layering`
   - `microservice-data-access-and-sql-security`
   - `microservice-clean-architecture-guardrails`
   - `microservice-opentelemetry-correlation-and-health`
   - `microservice-testing-strategy-unit-integration-contract`
4. O plano foi confrontado com o código real do repositório, especialmente `ClienteEndpoints`, `ClienteServico`, `IClienteServico`, `IClienteRepositorio`, `ClienteRepositorioDapper` e o middleware global.

### Onde o MCP agregou valor real

1. **Semântica REST consistente:** o MCP reduziu ambiguidade sobre `PUT`, `404`, `409`, `412` e `422`.
2. **Padronização transversal:** as regras de camadas, tratamento global de erro, contratos e testes vieram de um corpus unificado, não de memória implícita do assistente.
3. **Governança técnica:** o uso de `ids` específicos gerou rastreabilidade da decisão arquitetural.
4. **Resiliência pragmática:** o MCP evitou overengineering, deixando claro que retry automático não é adequado para escrita em SQL sem garantias adicionais.
5. **Observabilidade:** trouxe requisitos não triviais para logs, correlação e readiness, que dificilmente surgiriam apenas do contexto local mínimo.

### Onde poderia ter sido melhor utilizado

1. O corpus cobre muito bem arquitetura e políticas técnicas, mas não trouxe ADRs ou regras funcionais do domínio `Cliente`.
2. Faltou uma instruction central específica para persistência de escrita em banco relacional com taxonomia de exceções de update/concurrency, em vez de depender de adaptação de policies mais amplas.
3. O experimento teria ainda mais valor se o MCP também oferecesse catálogo organizacional de exceções de domínio, convenções de nomenclatura de DTOs e guideline de versionamento concorrente.

---

## 2. Qualidade técnica do plano

### Estruturação

O plano seguiu BMAD de forma explícita, o que fortalece rastreabilidade e evita resposta puramente opinativa. Houve também refinamento com riscos, dependências, critérios de aceite e alternativas rejeitadas.

### Organização em camadas

A decomposição ficou aderente ao repositório e ao corpus:
- `Api` para contrato HTTP e documentação;
- `Dominio` para regras e orquestração;
- `Interfaces` para contratos assíncronos;
- `Modelo` para DTOs;
- `Repositorio` para persistência parametrizada.

### Aderência a boas práticas

Pontos fortes:
- respeito à semântica correta de `PUT`;
- uso de DTO dedicado;
- `CancellationToken` fim a fim;
- tratamento global de falhas;
- SQL parametrizado;
- separação entre validação de contrato e regra de negócio;
- abordagem crítica para concorrência e observabilidade.

Pontos de atenção:
- o plano ainda depende de decisões funcionais não presentes no MCP nem no código;
- a resiliência aplicada ao caso é mais operacional do que transacional, porque o corpus de Polly é mais forte para HTTP do que para escrita SQL.

---

## 3. Centralização de conhecimento

### O MCP permite evitar duplicação entre repositórios?

Sim, em boa medida. Para arquitetura, contrato HTTP, validação, observabilidade, testes e governança de resposta, o MCP reduz a necessidade de repetir os mesmos guidelines em 100+ repositórios.

### O conhecimento parece reutilizável?

Sim. O corpus usado é majoritariamente transversal e independente do domínio específico. As instructions consultadas se aplicam a múltiplos microservices .NET sem grande adaptação.

### Há indícios de consistência transversal?

Sim. O uso de `ids` e policies centralizadas sugere consistência entre repositórios, especialmente para:
- semântica REST;
- tratamento de erros;
- arquitetura por camadas;
- observabilidade;
- estratégia de testes.

### Avaliação crítica

O MCP centraliza bem o **como implementar**. Já o **o que o produto quer** continua fora dele. Isso significa que ele funciona muito bem como fonte central de padrões técnicos, mas não substitui catálogos de domínio, ADRs de produto e contratos funcionais versionados.

---

## 4. Limitações da abordagem

### Dependência de chamadas de tool

A abordagem depende fortemente da disponibilidade e qualidade das tools. Sem busca, índice e fetch de instructions, a experiência degrada para uma resposta genérica.

### Latência

Cada busca e cada recuperação adiciona custo de tempo. Em cenários corporativos com corpus amplo, isso pode tornar o fluxo mais lento do que instruções locais simples.

### Possíveis gargalos

1. Índice central desatualizado.
2. Corpus excessivamente amplo sem curadoria semântica.
3. Overfetch de instructions pouco relevantes.
4. Dependência operacional do serviço MCP como ponto crítico de suporte ao assistente.

### Complexidade operacional

Governar um MCP corporativo exige:
- ciclo de publicação/versionamento de instructions;
- ownership claro por domínio técnico;
- revisão de impacto transversal;
- observabilidade do próprio MCP;
- política de compatibilidade para não quebrar automações e experiências existentes.

---

## 5. Escalabilidade (100+ repositórios)

### O MCP se comporta bem como fonte única de verdade?

Parcialmente. Para padrões técnicos compartilhados, sim. Para decisões de domínio, não necessariamente.

### Facilidade de evolução centralizada

Alta. Uma nova policy de API, resiliência ou observabilidade pode beneficiar todos os repositórios sem replicação manual de arquivos locais.

### Governança de conhecimento

O MCP favorece governança melhor do que instructions espalhadas, porque:
- há ponto central de atualização;
- a rastreabilidade por `id` é objetiva;
- revisões podem ocorrer em um único local;
- auditoria de aderência tende a ser mais simples.

### Avaliação crítica em escala

Em 100+ repositórios, o MCP é forte para reduzir drift técnico e inconsistência de padrões. Porém, ele ainda precisa de complementos para governar:
- decisões de domínio por vertical;
- exceptions processuais aprovadas;
- versionamento e depreciação de guidelines;
- descoberta contextual sem excesso de latência.

---

## 6. Experiência de uso

### Fluidez

Boa, desde que o fluxo seja guiado por busca no corpus e leitura do código real. O uso do MCP como primeira fonte de verdade ajudou a estruturar a resposta rapidamente.

### Interrupções no fluxo

Existem interrupções naturais pelo número de chamadas necessárias para:
- descobrir instructions relevantes;
- recuperar texto completo;
- cruzar com o código do repositório.

### Dependência de prompt

Ainda há dependência relevante do prompt. O usuário precisou explicitar que o MCP deveria ser priorizado. Sem essa instrução, o assistente poderia recorrer mais ao contexto local ou a heurísticas genéricas.

### Avaliação crítica

A experiência é melhor que a de instructions locais isoladas quando o tema exige coerência arquitetural. Ainda assim, ela não é totalmente invisível: há custo cognitivo e operacional para orquestrar contexto distribuído entre código real e corpus central.

---

## Avaliação (0 a 10)

| Critério | Nota | Justificativa resumida |
| --- | ---: | --- |
| aderência ao contexto | 9 | O plano foi ancorado no código real e no corpus central do MCP. |
| qualidade técnica | 9 | Semântica REST, camadas, erros, resiliência e testes foram tratados com boa profundidade. |
| completude | 8 | Está completo para planejamento técnico, mas depende de definições funcionais ausentes. |
| consistência | 9 | Há coerência entre policies centrais e o desenho por camadas do repositório. |
| capacidade de centralização | 9 | O MCP mostrou boa aptidão para concentrar padrões transversais reutilizáveis. |
| escalabilidade | 8 | Escala bem em governança técnica, mas sofre com latência, curadoria e cobertura de domínio. |
| governança | 9 | Uso de corpus versionável e rastreável por `id` fortalece a governança. |

---

## Conclusão final

**MCP ajuda, mas precisa de complementos**

### Fundamentação resumida

Como solução arquitetural corporativa, o MCP demonstrou valor real para centralizar conhecimento técnico reutilizável e consistente entre múltiplos repositórios. Ele é especialmente forte para padrões transversais, boas práticas, contratos HTTP, observabilidade, testes e guardrails arquiteturais.

Por outro lado, ele não elimina a necessidade de outras camadas de conhecimento, como:
- decisões de domínio e produto;
- ADRs específicos por contexto;
- catálogos funcionais versionados;
- políticas operacionais específicas de times/plataformas.

Em cenário corporativo real, o MCP é uma peça forte da estratégia de centralização, mas não deve ser a única.
