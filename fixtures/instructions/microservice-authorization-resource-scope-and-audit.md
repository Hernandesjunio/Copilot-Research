---
id: microservice-authorization-resource-scope-and-audit
title: "Autorização — âmbito de recurso, propriedade e auditoria"
tags: [microservice, security, authorization, jwt, claims, ownership, audit, resource-scope]
scope: "**/*.cs"
priority: high
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-18
status: active
workspace_evidence_required: true
workspace_signals: [IAuthorizationHandler, AuthorizationHandlerContext, IAuthorizationRequirement, ResourceAuthorizationRequirement, HttpContext.User]
on_absence: hypothesis_only
---

# Objetivo

Complementar autenticação JWT (`microservice-auth-jwt-bearer-and-authorization`) com **guardrails** para autorização por **âmbito de recurso** (incluindo “recursos do utilizador atual”), **registos de auditoria** e **metadados de rastreio de ator**, sem prescrever nomes de entidades, rotas ou roles de negócio — esses detalhes ficam nas **instructions locais** do repositório (ex.: `.github/instructions/`).

## TL;DR

- **Roles ou claims de permissão global** (ex.: “pode escrever”) **não** substituem, por si só, regras de **quem pode alterar qual instância** de um agregado recurso.
- Modelar **propriedade** ou **responsabilidade** sobre recursos com identificadores de ator estáveis (ex.: `sub`, identificador interno mapeado a partir de claims validadas) e comparar com dados persistidos **no recurso** ou numa política explícita.
- Operações mutáveis que afetem dados sensíveis devem ter **auditoria** reproduzível: quem, quando, o quê (ação), sobre qual recurso — sem gravar tokens nem payloads completos em claro quando a política de dados proibirem.
- Rotas de listagem “**do utilizador atual**” (filtradas pelo ator) e regras exactas de **roles privilegiadas** (bypass de propriedade) são decisão de produto: definir em instructions locais e cobrir com testes.

## Critérios (decisão rápida)

| Situação | Resposta típica | Nota |
| --- | --- | --- |
| Autenticado, sem claim/papel para o âmbito da operação | `403 Forbidden` | Consistente com policy global |
| Autenticado, com papel global, mas recurso pertence a outro ator e a política exige propriedade | `403 Forbidden` | Salvo política local de bypass para role privilegiada |
| Recurso inexistente vs sem permissão | `404` ou `403` | Seguir a **mesma** política em todo o serviço (`microservice-auth-jwt-bearer-and-authorization`) |

## Regras de desenho

### Propriedade de recurso e policies

- Preferir **`IAuthorizationHandler`** com **requirement** que recebe o identificador do recurso (ou o recurso carregado) e compara com o **ator** derivado de `UserContext` / claims validadas.
- Centralizar obtenção do **id de ator** (ex.: método no `UserContext` ou serviço de contexto de pedido); não espalhar parsing de claims em handlers de domínio.
- Quando uma **role ou claim de elevação** permitir ignorar a regra de propriedade (ex.: operações administrativas), isso deve estar explícito na policy e **testado**; não misturar “fallback” implícito em controllers.

### Listagens ao âmbito do ator

- Endpoints que devolvem apenas entidades associadas ao utilizador autenticado devem filtrar por **identificador de ator** (ou mapeamento estável) e usar políticas de autorização alinhadas ao restante API.
- Forma da rota (`/recursos/meus`, query, etc.) e contratos de resposta são **locais ao produto** — o corpus exige apenas consistência e segurança (não vazar dados de outros tenants/atores).

### Auditoria

- Para operações mutáveis relevantes, persistir registo de **auditoria** (tabela dedicada ou stream append-only, conforme stack) com: identificador de recurso, tipo de ação, ator, carimbo temporal e, quando aplicável, correlação (`TraceId`/`CorrelationId` interno, não PII arbitrário).
- **Não** armazenar corpo completo de pedidos com dados pessoais se não for requisito; preferir códigos de ação e identificadores.
- Garantir que a escrita de auditoria falha de forma visível (ou compensada) se o produto exigir trilha forte; não “engolir” falhas silenciosamente em caminhos críticos.

### Metadados `CriadoPor` / `UltimoAtualizadoPor` (ou equivalente)

- Quando o modelo de persistência incluir colunas de rastreio de ator, preenê-las no **serviço de aplicação** ou repositório a partir do contexto autenticado, **após** validação do token.
- Migrações seguras (valores nulos para legado, backfill controlado) são responsabilidade do repositório; não hardcodar semântica de negócio no corpus.

## Snippet (padrão ilustrativo, anónimo)

```csharp
// Requirement genérica: verificar propriedade de recurso para operações mutáveis
public sealed class SameOwnerRequirement : IAuthorizationRequirement { }

// Handler: carregar recurso (ou id) e comparar OwnerUserId com o contexto atual
// Validar sempre claims antes de comparar com colunas persistidas.
```

## Pode ser feito

- Combinar policies de **role** com requirements de **recurso** por endpoint (ex.: `RequireRole` + `Authorize(Policy = "ResourceOwner")`).
- Cobrir handlers de autorização com testes unitários e testes de integração por rota crítica.
- Referenciar `microservice-testing-strategy-unit-integration-contract` para estratégia de testes.

## Não pode ser feito

- Usar email ou nome de exibição como única chave de propriedade sem normalização e validação explícita.
- Expor em respostas ou logs **por que** um `403` ocorreu com detalhes que permitam enumeração de recursos alheios.
- Duplicar validação JWT dentro do domínio puro — manter no perímetro (middleware/policies) e no `UserContext`.

## Ver também

- `microservice-auth-jwt-bearer-and-authorization` — validação JWT e policies base.
- `microservice-api-validation-and-error-contracts` — `401`/`403`/`404` na camada API.
