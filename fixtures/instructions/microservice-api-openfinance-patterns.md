---
id: microservice-api-openfinance-patterns
title: "Microservice API — Open Finance, erros globais e docs"
tags: [microservice, api, openfinance, minimal-api, xmldocs, error-handling]
scope: "**/Api/**/*.cs"
priority: high
kind: policy
---

# Objetivo

Padronizar a camada `Api` para expor endpoints consistentes, documentados e resilientes, com resposta no padrão Open Finance e tratamento global de erros.

## TL;DR

- Todos os endpoints devem ser documentados com XML docs.
- Respostas devem seguir o envelope/padrão Open Finance definido pelo domínio.
- Exceções devem ser tratadas em middleware/filtro global reutilizável.
- Preferir Minimal API com organização por extensions e endpoints por feature.

## Snippet

```csharp
/// <summary>
/// Consulta recursos financeiros por identificador.
/// </summary>
/// <param name="id">Identificador do recurso.</param>
/// <returns>Resposta padronizada Open Finance.</returns>
app.MapGet("/v1/recursos/{id}", async (string id, IConsultaServico servico, CancellationToken ct) =>
{
    var resultado = await servico.ConsultarAsync(id, ct);
    return Results.Ok(OpenFinanceResponse.Success(resultado));
})
.WithName("ConsultarRecurso")
.WithSummary("Consulta recurso financeiro")
.WithDescription("Retorna dados no padrão Open Finance.");
```

## Pode ser feito

- Centralizar `ProblemDetails` e mapeamento de exceções de negócio/técnicas.
- Versionar endpoints (`/v1`, `/v2`) quando contrato mudar.
- Usar validação de entrada antes de chamar domínio.
- Padronizar correlação (`traceId`/`correlationId`) em logs e resposta de erro.

## Não pode ser feito

- Capturar exceção em cada endpoint repetindo código de tratamento.
- Retornar payload fora do padrão Open Finance definido para o produto.
- Expor stack trace, connection string ou detalhes internos em erro de API.
- Publicar endpoint sem documentação mínima (XML docs e metadados de rota).
