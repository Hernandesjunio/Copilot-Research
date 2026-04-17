---
id: microservice-configuration-production-readiness
title: "Configuração e operação — options, fail-fast, feature flags e deploy"
tags: [microservice, configuration, options, feature-flags, production, deployment]
scope: "**/*.cs"
priority: medium
kind: policy
workspace_evidence_required: true
workspace_signals: [IConfiguration, IOptions, IHostApplicationLifetime, AddFeatureManagement, IFeatureManager]
on_absence: hypothesis_only
---

# Objetivo

Complementar o registro de DI com regras de configuração segura, validação no startup, feature flags, governança de variáveis de ambiente e comportamento em produção, incluindo readiness e compatibilidade retroatória.

## TL;DR

- `IOptions` com `ValidateDataAnnotations` + `ValidateOnStart` para falhar cedo quando config obrigatória estiver ausente ou inválida.
- Feature flags para liberar comportamento novo sem deploy arriscado; flags temporárias devem ter dono e data de remoção.
- Separar config não secreta (appsettings) de segredos (KeyVault/variáveis de pipeline); nunca commitar segredos.
- Defaults seguros: em dúvida, modo mais restritivo (ex.: feature desligada, limite menor de página).

## Ambientes

- `Development` pode relaxar certas checagens; `Production` deve manter validações estritas e logs sem dados sensíveis.
- Variáveis de ambiente nomeadas com prefixo do serviço (`MYMS_`) para evitar colisão em hosts compartilhados.

## Snippet

```csharp
services.AddOptions<DownstreamApiOptions>()
    .Bind(configuration.GetSection("Downstream:Contas"))
    .Validate(o => !string.IsNullOrWhiteSpace(o.BaseUrl), "BaseUrl obrigatória")
    .ValidateOnStart();
```

## Pode ser feito

- Expor toggles via `Microsoft.FeatureManagement` ou provedor corporativo equivalente.
- Registrar versão do assembly e commit hash em `/health` ou endpoint interno de build info (sem dados sensíveis).

## Não pode ser feito

- Silenciar falhas de configuração com `try/catch` no startup.
- Depender de ordem implícita de variáveis não documentada.
- Alterar semântica de config existente sem bump de versão ou período de convivência.
