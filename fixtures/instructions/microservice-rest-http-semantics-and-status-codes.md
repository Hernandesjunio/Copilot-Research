---
id: microservice-rest-http-semantics-and-status-codes
title: "REST — verbos HTTP, semântica de resposta e códigos de status"
tags: [microservice, api, rest, http, status-codes, idempotency]
scope: "**/Api/**/*.cs"
priority: high
kind: policy
---

# Objetivo

Prescrever semântica REST consistente para microservices .NET: uso correto de verbos, códigos de status previsíveis e regras mínimas de idempotência e consistência de rotas, alinhadas ao envelope/contrato público do produto (ex.: Open Finance quando aplicável).

## TL;DR

- `GET` e `DELETE` devem ser idempotentes no efeito observável do recurso; `POST` cria; `PUT` substitui; `PATCH` aplica alteração parcial documentada.
- Escolher **um** código principal por cenário; evitar “200 genérico” para erro de negócio ou validação.
- Quando o produto exigir envelope (ex.: Open Finance), o corpo HTTP ainda segue o padrão do produto; códigos de status continuam semânticos HTTP.
- Rotas versionadas (`/v1/...`) e substantivos no plural para coleções, salvo exceção documentada do domínio.

## Regras por verbo

- `GET`
  - Retorna representação do recurso ou coleção; não altera estado do servidor.
  - `200` com payload; `204` apenas quando a ausência de corpo for contratada explicitamente.
- `POST`
  - Cria recurso ou dispara operação de processamento; não usar para substituição total de recurso existente.
  - `201` com `Location` quando criar recurso endereçável; `202` quando aceitar trabalho assíncrono com rastreio.
- `PUT`
  - Substituição total do recurso endereçado; rejeitar se invariantes não puderem ser satisfeitas (`409`/`412` conforme regra abaixo).
- `PATCH`
  - Mudança parcial com contrato explícito (JSON Patch/Merge Patch ou DTO de patch documentado); não misturar semântica de `PUT`.
- `DELETE`
  - Remoção lógica ou física conforme política do domínio; `204` quando não houver corpo; `202` se exclusão for assíncrona.

## Mapeamento mínimo de status (referência)

| Situação | Status | Notas |
| --- | --- | --- |
| Sucesso com corpo | `200` | Leituras e operações síncronas concluídas. |
| Criação concluída | `201` | Incluir `Location` quando fizer sentido. |
| Aceito para processamento | `202` | Corpo deve permitir acompanhar estado (URL, id, etc.). |
| Sucesso sem corpo | `204` | Evitar corpo vazio com `200`. |
| Validação de entrada inválida | `400` | Detalhes em `ProblemDetails`/padrão do produto. |
| Não autenticado | `401` | Não confundir com “sem permissão”. |
| Autenticado, sem permissão | `403` | |
| Recurso inexistente | `404` | Também para IDs inexistentes quando não for vazamento de enumeração. |
| Conflito de estado/regra | `409` | Ex.: duplicidade, violação de invariante persistível. |
| Pré-condição (ETag/version) falhou | `412` | Quando usar concorrência otimista na API. |
| `Content-Type`/formato não suportado | `415` | |
| Regra de negócio violada (domínio) | `422` | Ver instruction de erros; não usar para erro de sintaxe JSON. |
| Limite de taxa | `429` | Com `Retry-After` quando possível. |
| Falha interna inesperada | `500` | Sem detalhes internos no payload. |
| Bad gateway / dependência indisponível | `502`/`503`/`504` | Com critério operacional; preferir timeouts explícitos no cliente. |

## Snippet

```csharp
// Exemplo: operação assíncrona aceita, sem bloquear o cliente
app.MapPost("/v1/relatorios", async (GerarRelatorioRequisicao req, IGerarRelatorioServico svc, CancellationToken ct) =>
{
    var id = await svc.EnfileirarAsync(req, ct);
    return Results.Accepted($"/v1/relatorios/{id}", new { id });
});
```

## Pode ser feito

- Declarar idempotência de `POST` específicos via chave de idempotência (`Idempotency-Key`) quando o domínio exigir deduplicação.
- Expor cabeçalhos de correlação (`traceparent`, `X-Correlation-Id`) conforme política de observabilidade.
- Documentar semântica de erros junto ao OpenAPI/Minimal API metadata.

## Não pode ser feito

- Usar `GET` com efeitos colaterais de escrita.
- Retornar `200` com payload de erro para falha de negócio ou validação.
- Acoplar nomes de colunas/tabelas ou stack traces em respostas públicas.
