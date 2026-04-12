---
id: microservice-api-openfinance-patterns
title: "Microservice API — envelope de resposta, erros globais e documentação"
tags: [microservice, api, response-envelope, rfc7807, minimal-api, xmldocs, error-handling, openfinance]
scope: "**/Api/**/*.cs"
priority: high
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Padronizar a camada `Api` para expor endpoints consistentes, documentados e resilientes, com **tratamento global de erros** e resposta alinhada ao **contrato público** da organização (corpo JSON direto, `ProblemDetails`/RFC 7807 ou envelope tipado).

## TL;DR

- Todos os endpoints devem ser documentados com XML docs.
- Respostas de sucesso e erro seguem **um** modelo acordado por produto ou plataforma (envelope tipado **ou** `ProblemDetails`, sem misturar semânticas conflituosas no mesmo status).
- Exceções devem ser tratadas em middleware/filtro global reutilizável.
- Preferir Minimal API com organização por extensions e endpoints por feature.
- O identificador `microservice-api-openfinance-patterns` mantém compatibilidade com índices existentes; o conteúdo aplica-se a qualquer perfil de envelope, não só Open Finance.

## Perfis de resposta (escolher um por serviço ou rota)

| Perfil | Quando usar | Erros |
| --- | --- | --- |
| **RFC 7807** (`ProblemDetails`) | APIs internas ou públicas sem envelope corporativo | `Results.Problem` / middleware de mapeamento |
| **Envelope tipado** | Organização exige payload uniforme (`success`, `data`, `errors`, etc.) | Middleware traduz exceções para o mesmo esquema |
| **Misto documentado** | Sucesso com envelope, erro com `ProblemDetails` | Documentar no OpenAPI e deixar explícito na review |

## Snippet (perfil envelope — exemplo genérico)

```csharp
/// <summary>
/// Obtém um recurso por identificador.
/// </summary>
/// <param name="id">Identificador do recurso.</param>
/// <returns>Payload no envelope acordado para o serviço.</returns>
app.MapGet("/v1/recursos/{id}", async (string id, IConsultaServico servico, CancellationToken ct) =>
{
    var resultado = await servico.ConsultarAsync(id, ct);
    return Results.Ok(ApiEnvelope.Success(resultado));
})
.WithName("ConsultarRecurso")
.WithSummary("Consulta recurso")
.WithDescription("Retorna dados no contrato público do serviço.");
```

## Snippet (exemplo histórico Open Finance)

Quando o produto mandar tipos como `OpenFinanceResponse<T>`, o padrão de endpoint permanece o mesmo: sucesso traduzido para o envelope, erros pelo pipeline global.

```csharp
return Results.Ok(OpenFinanceResponse.Success(resultado));
```

## Pode ser feito

- Centralizar `ProblemDetails` e mapeamento de exceções de negócio/técnicas.
- Versionar endpoints (`/v1`, `/v2`) quando contrato mudar.
- Usar validação de entrada antes de chamar domínio.
- Padronizar correlação (`traceId`/`correlationId`) em logs e resposta de erro.

## Não pode ser feito

- Capturar exceção em cada endpoint repetindo código de tratamento.
- Retornar payload de sucesso ou erro **fora** do contrato público definido para aquele serviço.
- Expor stack trace, connection string ou detalhes internos em erro de API.
- Publicar endpoint sem documentação mínima (XML docs e metadados de rota).

## Anti-exemplos

- Sucesso com envelope corporativo e erro com JSON anónimo sem `type`/`title`, sem decisão documentada.
- Duas classes de envelope diferentes na mesma versão de API sem namespace ou caminho que separe contextos.

## Impacto esperado na resposta da IA

- Ao gerar endpoints, aplicar o perfil que o repositório já usa; se houver apenas exemplos Open Finance no código, **generalizar** o padrão (envelope + middleware) em vez de copiar nomes de tipos inexistentes noutro repo.
