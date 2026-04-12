# Experimento — Baseline sem contexto estruturado para endpoint de atualização completa de cliente

**Data/hora:** 2026-04-12 15:43:29  
**Modelo:** GPT 5.4  
**Título inferido:** `experimento-baseline-endpoint-atualizacao-cliente`

---

## Escopo do experimento

Avaliação feita **sem usar `.github/instructions` e sem usar MCP**, considerando apenas o código disponível no workspace e conhecimento geral de engenharia de software.

---

## Contexto observado no código

O repositório expõe uma API em camadas com projetos `Api`, `Dominio`, `Interfaces`, `Modelo` e `Repositorio`.

Estado atual identificado:

- existe `GET /api/v1/clientes/`
- existe `POST /api/v1/clientes/`
- não existe endpoint de atualização completa
- a API usa `Minimal API`
- o repositório usa `Dapper` com `SQL Server`
- há middleware global para exceções com envelope `OpenFinanceResponse`
- não há projeto de testes visível
- não há mecanismo explícito de concorrência otimista, versionamento ou `ETag`
- não há catálogo visível de erros de domínio

---

## Planejamento de implementação do novo endpoint

### Objetivo funcional inferido

Adicionar um endpoint idempotente de atualização completa do cliente, provavelmente em `PUT /api/v1/clientes/{id}`.

### Premissas assumidas

Sem fonte de verdade centralizada, fui obrigado a assumir que:

1. `PUT` é o verbo correto para atualização completa.
2. `Nome` e `Email` continuam sendo os únicos campos atualizáveis.
3. a resposta deve continuar usando `OpenFinanceResponse<T>`.
4. atualização de cliente inexistente deve retornar `404`.
5. a semântica de atualização deve preservar `Id` e `DataCriacao`.
6. não existe requisito de auditoria, versionamento, evento de domínio ou integração externa.

Essas premissas são razoáveis, mas são **suposições**, não regras confirmadas.

### Estratégia técnica recomendada

#### 1. Contrato HTTP

Adicionar em `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs` um `MapPut("/{id:guid}", AtualizarCliente)` com:

- `200 OK` para sucesso
- `400 BadRequest` para payload inválido ou `Guid.Empty`
- `404 NotFound` para cliente inexistente
- `408 RequestTimeout` para cancelamento/timeout
- `500 InternalServerError` para falhas não tratadas

#### 2. DTO de entrada

Há duas opções:

- **mais rápida:** reutilizar `ClienteRequisicao`
- **mais correta para evolução:** criar `ClienteAtualizacaoRequisicao`

Para um planejamento rigoroso, a segunda opção é melhor. Reutilizar o DTO de criação acopla criação e atualização sem saber se as regras de negócio são idênticas.

#### 3. Contrato de serviço

Expandir `IClienteServico` com algo como:

- `Task<ClienteResposta> AtualizarClienteAsync(Guid id, ClienteAtualizacaoRequisicao requisicao, CancellationToken cancellationToken)`

Responsabilidades esperadas no serviço:

- validar `id`
- validar obrigatoriedade de `Nome` e `Email`
- validar formato mínimo de `Email`
- garantir semântica de atualização completa
- traduzir ausência do registro para exceção específica de domínio

#### 4. Contrato de repositório

Expandir `IClienteRepositorio` com operação específica de atualização, por exemplo:

- `Task<ClienteResposta?> AtualizarAsync(Guid id, ClienteAtualizacaoRequisicao requisicao, CancellationToken cancellationToken)`

Retornar `null` em caso de não encontrado é suficiente para a camada de domínio decidir se lança exceção específica.

#### 5. Implementação no repositório

Em `ClienteRepositorioDapper`:

- usar um único `UPDATE ... OUTPUT INSERTED...`
- preservar `DataCriacao`
- usar `CommandDefinition` com `commandTimeout` e `cancellationToken`
- evitar múltiplas consultas desnecessárias

Exemplo de comportamento esperado:

- se atualizar 1 linha, retornar o registro atualizado
- se atualizar 0 linhas, retornar `null`

#### 6. Tratamento de exceções

O código atual mistura `try/catch` local nos handlers com middleware global. Isso já é um sinal de desenho inconsistente.

Para o novo endpoint, o melhor plano é:

- evitar `catch` redundante no handler
- concentrar o mapeamento HTTP no middleware global
- criar exceção específica para recurso não encontrado, por exemplo `ClienteNaoEncontradoException`
- mapear essa exceção para `404`
- mapear `ArgumentException` para `400`

Sem isso, o endpoint nasce com o mesmo problema já visível nos handlers atuais: tratamento parcial, duplicado e pouco previsível.

#### 7. Resiliência e tolerância a falhas

Aplicável com base no código atual:

- propagar `CancellationToken` do endpoint até o banco
- manter timeout configurável via `SqlOptions`
- registrar logs estruturados para falhas de banco e cliente não encontrado
- manter resposta padronizada no envelope existente

Limite importante: **não recomendo retry automático cego para operação de escrita** neste baseline.

Motivo:

- não há contexto sobre política organizacional de retry
- não há mecanismo de concorrência otimista
- não há idempotency key
- retry em escrita pode mascarar defeitos ou produzir comportamento ambíguo em cenários reais

#### 8. Testes mínimos necessários

Mesmo sendo só planejamento, a ausência de testes no workspace é uma lacuna séria. O mínimo necessário seria:

- teste unitário do serviço para validação de `id`, `Nome` e `Email`
- teste unitário para `cliente não encontrado`
- teste de integração do endpoint `PUT`
- teste de integração do repositório validando `UPDATE` e `404`
- teste de timeout/cancelamento

Sem isso, a alteração ficaria tecnicamente frágil.

### Arquivos provavelmente impactados

- `ClientesAPI.Api/Endpoints/ClienteEndpoints.cs`
- `ClientesAPI.Api/Extensions/ExceptionHandlingMiddleware.cs`
- `ClientesAPI.Interfaces/IClienteServico.cs`
- `ClientesAPI.Interfaces/IClienteRepositorio.cs`
- `ClientesAPI.Dominio/Servicos/ClienteServico.cs`
- `ClientesAPI.Repositorio/ClienteRepositorioDapper.cs`
- `ClientesAPI.Modelo/ClienteRequisicao.cs` **ou** novo `ClientesAPI.Modelo/ClienteAtualizacaoRequisicao.cs`
- possivelmente nova exceção de domínio em local ainda indefinido

---

## Relatório do experimento

### 1. Uso de contexto

#### Limitações encontradas

- não há fonte central de padrões arquiteturais
- não há convenção explícita para modelagem de `PUT` vs `PATCH`
- não há diretriz confirmada para erros funcionais (`404`, `409`, `422`)
- não há definição de observabilidade, correlação, logging ou telemetria
- não há política visível de resiliência para escrita em banco
- não há contrato explícito sobre concorrência, auditoria ou versionamento
- não há projeto de testes servindo como especificação executável

#### Dependência de suposições

Alta.

O planejamento dependeu de inferências sobre:

- semântica do endpoint
- formato do payload
- tratamento de não encontrado
- nível aceitável de validação
- comportamento esperado em falhas transitórias
- fronteira entre domínio e infraestrutura

Sem contexto estruturado, qualquer uma dessas inferências pode estar errada.

### 2. Qualidade técnica

#### Partes bem resolvidas

- a arquitetura em camadas existente dá uma base mínima para distribuir responsabilidades
- o uso de interfaces facilita extensão de serviço e repositório
- o middleware global já cria um ponto central para padronizar erros
- o uso de `CancellationToken` já existe e favorece tolerância a falhas
- o repositório com `Dapper` e `CommandDefinition` permite implementar `UPDATE` de forma objetiva

#### Partes genéricas

- escolha do verbo HTTP foi inferida, não confirmada
- decisão entre reaproveitar ou criar DTO de atualização continua especulativa
- tratamento de resiliência ficou necessariamente conservador e genérico
- proposta de exceções de domínio é técnica, mas não ancorada em convenção do time
- estratégia de testes é correta em termos gerais, mas não alinhada a stack de testes do repositório

### 3. Lacunas

#### O que faltou para melhorar

- convenção oficial de desenho de endpoint
- catálogo de erros e status HTTP por tipo de falha
- regra formal para DTOs de comando e resposta
- padrão organizacional para logs, tracing e correlação
- política explícita de retry, circuit breaker e timeout
- requisitos de concorrência otimista
- padrão de testes aceito pela equipe
- definição clara de onde exceções de domínio devem viver

#### Que tipo de contexto ajudaria

- ADR de arquitetura da API
- convenções de contratos REST
- guideline de resiliência para operações de escrita
- convenção de nomenclatura e organização de exceções
- exemplos internos de endpoints equivalentes
- padrão corporativo de observabilidade
- decisão explícita sobre reaproveitamento ou separação de DTOs

### 4. Impacto organizacional

#### Risco em ambiente com múltiplos repositórios

Alto.

Sem fonte de verdade centralizada, cada repositório tende a derivar soluções próprias para:

- tratamento de erro
- nomenclatura de DTOs
- regras de atualização
- políticas de retry
- semântica de `404`, `409` e `422`
- padrões de teste

O resultado previsível é fragmentação técnica.

#### Consistência entre equipes

Baixa.

Duas equipes diferentes, com o mesmo pedido, provavelmente entregariam endpoints semanticamente diferentes mesmo usando a mesma stack.

### 5. Experiência do desenvolvedor

#### Necessidade de reprompt

Alta.

Para sair do genérico, eu precisaria reprompt sobre:

- contrato exato do endpoint
- regras de validação
- política de resiliência
- semântica de erro
- padrão de testes
- logging e observabilidade

#### Esforço manual

Alto.

Sem contexto estruturado, o esforço migra da implementação para descoberta manual, comparação entre arquivos e tomada de decisão defensiva.

---

## Avaliação

> Escala geral: `0` = muito ruim / `10` = muito bom.  
> Exceção: em **risco de erro**, `10` = risco muito alto.

| Critério | Nota | Avaliação crítica |
|---|---:|---|
| qualidade técnica | 5 | O plano é tecnicamente plausível, mas inevitavelmente conservador e incompleto. |
| completude | 4 | Falta contexto decisivo para fechar contrato, resiliência e testes com segurança. |
| consistência | 3 | Há alta chance de outra execução produzir decisões diferentes. |
| risco de erro | 8 | Muitas decisões centrais foram inferidas, não confirmadas. |
| previsibilidade | 3 | O resultado depende demais de interpretação local do código. |

---

## Conclusão final

**baseline é insuficiente para desenvolvimento real**

Motivo: o código disponível permite montar um plano viável, mas não permite garantir aderência consistente a padrões de arquitetura, resiliência, tratamento de erro e evolução entre equipes. Em tarefa real, isso não é uma limitação marginal. É um fator estrutural de erro.
