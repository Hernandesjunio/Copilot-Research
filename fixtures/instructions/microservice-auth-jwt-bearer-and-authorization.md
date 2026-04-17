---
id: microservice-auth-jwt-bearer-and-authorization
title: "Auth — JWT Bearer, validação de token e autorização por claims"
tags: [microservice, security, auth, authentication, authorization, jwt, bearer, claims]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals: [AddAuthentication, JwtBearerDefaults, AddJwtBearer, Microsoft.AspNetCore.Authentication.JwtBearer, AuthorizationPolicy, AddAuthorization]
on_absence: hypothesis_only
---

# Objetivo

Padronizar autenticação e autorização em APIs/microservices .NET com **JWT Bearer**, evitando validações incompletas, logs inseguros e decisões de autorização acopladas ao transporte.

## TL;DR

- Validar token com **issuer**, **audience**, **signature**, **lifetime** e **clock skew** explícitos.
- **Não** confiar em claims não validadas; mapear claims relevantes para um modelo interno (`UserContext`) e usar políticas/requirements.
- **Nunca** logar tokens (header `Authorization`) nem claims sensíveis; mascarar IDs quando necessário.
- Responder com semântica HTTP consistente: `401` quando não autenticado, `403` quando autenticado mas sem permissão.

## Critérios (decisão rápida)

| Situação | Resposta | Regra |
| --- | --- | --- |
| Sem token / token inválido | `401 Unauthorized` | Incluir `WWW-Authenticate: Bearer` quando aplicável |
| Token válido, mas sem permissão | `403 Forbidden` | Não “vazar” detalhes de autorização (motivo específico) |
| Recurso inexistente vs falta de permissão | `404` **ou** `403` | Definir política por API; se usar `404` para evitar enumeração, aplicar de forma consistente |

## Regras obrigatórias

### Validação do JWT

- Configurar validação com parâmetros explícitos (issuer/audience/signing key).
- `ValidateLifetime = true` e tolerância de relógio (`ClockSkew`) **baixa e justificada**.
- Não desabilitar validações (“funciona em dev”) sem decisão de segurança formal.

### Autorização (policies)

- Preferir `AddAuthorization(options => ...)` com **policies nomeadas** e/ou `IAuthorizationHandler` para regras não triviais.
- Evitar regras de autorização escondidas em controllers/handlers sem cobertura de teste.
- Regras por claims devem ser **defensivas**: claim ausente = negar.

### Logging e observabilidade

- Logar apenas metadados seguros (ex.: `sub`/`userId` normalizado) e correlação (`TraceId`), nunca o token.
- Quando precisar depurar auth, capturar eventos técnicos (falha de validação, issuer inesperado, audience incorreta), sem registrar payload do token.

## Snippet (mínimo ilustrativo)

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateIssuerSigningKey = true,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromMinutes(1),
            // IssuerSigningKey / ValidIssuer / ValidAudience vindos de configuração segura
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("require:scope:write", p =>
        p.RequireClaim("scope", "write"));
});
```

## Pode ser feito

- Usar `RequireAuthorization("policy")` por endpoint e consolidar regras em policies.
- Criar mapeamento para `UserContext` e isolar acesso a claims em um único ponto.
- Usar testes de autorização (unitário para handlers/requirements + testes de integração para rotas críticas).

## Não pode ser feito

- Aceitar token sem validar **issuer/audience/signature/lifetime**.
- Tratar qualquer claim como “fonte de verdade” sem validação do token.
- Logar `Authorization` header, token inteiro, ou claims sensíveis em spans/logs.
- Retornar `200` com corpo de erro “não autorizado”; usar `401`/`403`.

