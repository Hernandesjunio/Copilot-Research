---
id: microservice-di-options-extensions
title: "DI e configurações — Options e extension methods"
tags: [microservice, dotnet, dependency-injection, ioptions, configuration]
scope: "**/*.cs"
priority: medium
kind: policy
---

# Objetivo

Padronizar registro de dependências e leitura de configuração para microservices .NET usando `IOptions`, `IOptionsSnapshot` e extension methods por módulo.

## TL;DR

- Configuração tipada com classes de options e validação em startup.
- `IOptionsSnapshot` para dados que mudam por request/escopo.
- Registro de DI encapsulado em extensions por contexto.
- Evitar configuração e registrations "soltos" no `Program.cs`.

## Snippet

```csharp
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddRepositoryExtensions(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddOptions<SqlOptions>()
            .Bind(configuration.GetSection("Sql"))
            .ValidateDataAnnotations()
            .ValidateOnStart();

        services.AddScoped<IContaRepositorio, ContaRepositorioDapper>();
        services.AddScoped<IExtratoTableRepository, ExtratoTableRepository>();
        return services;
    }
}
```

## Pode ser feito

- Separar extensões por módulo (`AddApi`, `AddDomain`, `AddRepository`, `AddObservability`).
- Validar options com DataAnnotations e validações customizadas.
- Injetar `IOptions<T>` para singleton e `IOptionsSnapshot<T>` para scoped/transient.
- Usar `IHttpClientFactory` com políticas de resiliência para integrações externas.

## Não pode ser feito

- Ler configuração com chave mágica repetida em vários pontos.
- Instanciar classe concreta manualmente quando DI poderia resolver.
- Espalhar registrations em vários arquivos sem padrão de extensão.
- Usar `IOptionsSnapshot<T>` em singleton (lifetime incompatível).
