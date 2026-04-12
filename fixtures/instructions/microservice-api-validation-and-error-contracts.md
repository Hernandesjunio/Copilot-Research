---
id: microservice-api-validation-and-error-contracts
title: "API — validação de entrada, 400 vs 422 e contrato de erros"
tags: [microservice, api, validation, problem-details, errors, 400, 422]
scope: "**/Api/**/*.cs"
priority: high
kind: policy
---

# Objetivo

Definir regras objetivas para validação de entrada e tratamento uniforme de falhas na camada `Api`, incluindo quando retornar `400` versus `422`, integração com `ProblemDetails` e alinhamento ao tratamento global já prescrito para o produto.

## TL;DR

- `400`: entrada malformada, tipos incorretos, campos obrigatórios ausentes, regras de formato/sintaxe da requisição.
- `422`: entrada **sintaticamente válida**, mas rejeitada por **regra de negócio** ou invariante de domínio que não é “campo inválido” trivial.
- Exceções de domínio mapeadas de forma centralizada (middleware/filtro); endpoints não repetem `try/catch` para fluxo normal.
- Payload de erro segue `ProblemDetails` (RFC 7807) **ou** envelope do produto (ex.: Open Finance) que encapsule o mesmo conteúdo semântico, nunca ambos conflitantes.

## Critérios de decisão

### Quando retornar `400`

- JSON inválido ou incompatível com o contrato declarado.
- Falhas de model binding que impedem interpretar a requisição.
- Violações de validação de **forma** (tamanho máximo, regex, intervalo permitido pelo contrato de API) antes de invocar o domínio, quando a equipe classificar isso como “contrato de entrada” e não como regra de negócio.

### Quando retornar `422`

- Domínio rejeita operação com requisição bem formada (ex.: limite excedido, estado do recurso impede ação, combinação de campos permitida pelo schema mas ilegal no negócio).
- Regras que exigem conhecimento de agregado/persistência para avaliar (ex.: “conta encerrada não pode receber crédito”).

### Quando **não** usar `422`

- Autenticação/autorização: usar `401`/`403`.
- Recurso não encontrado por identificador: `404` (salvo política explícita de mascaramento).
- Conflito de concorrência/versionamento: preferir `409` ou `412` conforme contrato.

## Snippet

```csharp
// Validação de entrada na Api (formato/contrato) -> 400 com ProblemDetails
if (string.IsNullOrWhiteSpace(req.ContaId))
    return Results.Problem(title: "Requisição inválida", detail: "contaId é obrigatório.", status: StatusCodes.Status400BadRequest);

// Domínio rejeita negócio com payload bem formado -> mapear para 422 no exception handler global
public sealed class BusinessRuleException : Exception
{
    public string Code { get; }
    public BusinessRuleException(string code, string message) : base(message) => Code = code;
}
```

## Pode ser feito

- Padronizar `type`/`title`/`detail`/`instance` e um campo `code` interno estável para telemetria.
- Incluir `traceId`/`correlationId` no `extensions` do `ProblemDetails` quando permitido pelo produto.
- Registrar métrica/contador por `code` de erro de negócio (baixa cardinalidade).

## Não pode ser feito

- Expor SQL, mensagens de provedor ou stack trace ao cliente.
- Usar `422` para erro de parsing JSON ou tipo incorreto de propriedade.
- Misturar validação de entrada profunda de domínio no controller; regra complexa permanece no `Dominio`, com exceções de domínio claras.
