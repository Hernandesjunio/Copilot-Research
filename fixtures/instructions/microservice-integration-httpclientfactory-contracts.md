---
id: microservice-integration-httpclientfactory-contracts
title: "Integrações HTTP — HttpClientFactory, contratos externos e tolerância"
tags: [microservice, httpclient, integration, resilience, serialization, contracts]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals: [IHttpClientFactory, AddHttpClient, HttpClient, HttpRequestMessage]
on_absence: hypothesis_only
---

# Objetivo

Padronizar clientes HTTP nomeados/typed com `IHttpClientFactory`, políticas por dependência, contratos externos (`RequisicaoIntegracao`/`RespostaRequisicaoIntegracao`) e tolerância a mudanças sem acoplar o domínio ao transporte.

## TL;DR

- Um `HttpClient` nomeado por bounded context de integração (`contas-api`, `pagamentos-api`).
- Mapear resposta externa para modelos internos na camada de infraestrutura/gateway; **não** propagar DTO externo ao `Dominio`.
- Timeouts, retries e circuit breaker aplicados por política (ver instruction de resiliência).
- Headers comuns (`Authorization`, `Accept`, `Idempotency-Key`, `traceparent`) centralizados no delegating handler quando repetidos.

## Serialização e erros

- `System.Text.Json` com `PropertyNamingPolicy` explícita alinhada ao provedor.
- Erros HTTP mapeados para exceções técnicas internas com contexto mínimo seguro; conversão para `ProblemDetails` ocorre na `Api`.

## Snippet

```csharp
builder.Services.AddHttpClient<IContasApiGateway, ContasApiGateway>((sp, client) =>
{
    var opt = sp.GetRequiredService<IOptions<ContasApiOptions>>().Value;
    client.BaseAddress = new Uri(opt.BaseUrl);
    client.DefaultRequestHeaders.Accept.ParseAdd("application/json");
});
```

## Pode ser feito

- Implementar anti-corruption layer (ACL) com tradução explícita de códigos/erros do fornecedor.
- Versionar endpoints externos em configuração (`/v2` do fornecedor) independentemente da versão pública do microserviço.

## Não pode ser feito

- `new HttpClient()` descartável em hot path.
- Ignorar `CancellationToken` em chamadas de integração.
- Logar payloads completos de integração em produção sem política de mascaramento.
