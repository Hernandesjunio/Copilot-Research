---
id: microservice-rest-http-semantics-and-status-codes
title: "REST — verbos HTTP, semântica de resposta e códigos de status"
tags: [microservice, api, rest, http, status-codes, idempotency, 404, put, patch]
scope: "**/Api/**/*.cs"
priority: high
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Prescrever semântica REST consistente para microservices .NET: uso correto de verbos, códigos de status previsíveis e regras mínimas de idempotência e consistência de rotas, alinhadas ao **contrato público** (corpo JSON, envelope ou `ProblemDetails` conforme política organizacional do produto).

## TL;DR

- `GET` e `DELETE` devem ser idempotentes no efeito observável do recurso; `POST` cria; `PUT` substitui; `PATCH` aplica alteração parcial documentada.
- Escolher **um** código principal por cenário; evitar “200 genérico” para erro de negócio ou validação.
- Quando existir **envelope de resposta** definido pela organização, o corpo HTTP segue esse contrato; os **códigos de status** permanecem semanticamente HTTP.
- Rotas versionadas (`/v1/...`) e substantivos no plural para coleções, salvo exceção documentada do domínio.
- Catálogo de referência cruzada: `microservice-api-error-catalog-baseline`.

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

## DTOs e contratos de atualização (`PUT` vs `PATCH`)

- **`PUT`**: contrato de **substituição total** do recurso endereçado; o DTO deve refletir o recurso completo (campos obrigatórios e defaults documentados). Não usar um único DTO “tudo opcional” como substituto de substituição total sem documentação explícita.
- **`PATCH`**: alteração **parcial** com contrato explícito (JSON Patch, merge patch documentado ou DTO de patch dedicado). Campos omitidos não devem ser interpretados como “apagar dado” salvo semântica documentada.
- **Anti-padrão**: reutilizar o mesmo tipo de requisição para `PUT` e `PATCH` com semânticas diferentes sem nomes, rotas ou documentação OpenAPI que deixem isso óbvio para o consumidor.

## Recurso inexistente (`404`, `204`) por operação

| Operação | Identificador na URI inexistente | Resposta predefinida | Notas |
| --- | --- | --- | --- |
| `GET` coleção/item | sim | `404` | Salvo política explícita de mascaramento (ex.: `403`/`204` em listagens vazias — documentar). |
| `PUT` | sim | `404` | Não há recurso para substituir. |
| `PATCH` | sim | `404` | Idem. |
| `DELETE` | sim | `404` **ou** `204` | Escolher **uma** política por API e documentar: `404` = “só apaga se existir”; `204` idempotente = “garantir ausência” sem distinguir existência prévia. |
| `POST` sub-recurso | pai inexistente | `404` | Típico quando o recurso pai define o namespace. |

Erros de negócio (“não pode cancelar neste estado”) não são substitutos de `404`; mapear para `409`/`422` conforme `microservice-api-validation-and-error-contracts`.

## Representação interna até à fronteira `Api`

- O `Dominio` pode expressar ausência com `null`, tipo `Option`, `Result` com ramo “não encontrado” ou exceção de domínio **tipada** — o importante é **um padrão por serviço** e mapeamento **centralizado** (middleware/filtro) para o status HTTP e o envelope de erro acordados.
- A camada `Api` traduz o resultado do caso de uso para status e corpo; evita-se lógica duplicada de “se null então 404” espalhada por cada endpoint.

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

## Anti-exemplos

- `PATCH` com corpo parcial que na prática substitui o recurso inteiro sem contrato (comportamento de `PUT` disfarçado).
- `DELETE` que retorna `200` com corpo `{"deleted": false}` em vez de usar `404`/`204` conforme política.
- `GET /{id}` que retorna `200` com corpo vazio ou lista vazia quando o **id** não existe, misturando “não encontrado” com “encontrado sem dados”.

## Pode ser feito

- Declarar idempotência de `POST` específicos via chave de idempotência (`Idempotency-Key`) quando o domínio exigir deduplicação.
- Expor cabeçalhos de correlação (`traceparent`, `X-Correlation-Id`) conforme política de observabilidade.
- Documentar semântica de erros junto ao OpenAPI/Minimal API metadata.

## Não pode ser feito

- Usar `GET` com efeitos colaterais de escrita.
- Retornar `200` com payload de erro para falha de negócio ou validação.
- Acoplar nomes de colunas/tabelas ou stack traces em respostas públicas.

## Impacto esperado na resposta da IA

- Escolher verbo e status com base nas tabelas desta instruction; quando a política de `DELETE` (`404` vs `204`) não estiver definida no repositório, **propor as duas opções** e pedir decisão em vez de assumir.

## Quando explicitar incerteza

- Mascaramento de existência (`403` vs `404`), `DELETE` idempotente e contratos legais do produto: seguir instructions nativas do repo; se ausentes, declarar inferência e risco de enumeração.
