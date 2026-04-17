---
id: microservice-resilience-polly-timeouts-and-circuit-breaker
title: "Resiliência — timeout, retry com backoff, jitter e circuit breaker"
tags: [microservice, resilience, polly, httpclient, timeout, retry, circuit-breaker]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals: [Polly, AddPolicyHandler, IAsyncPolicy, HttpPolicyExtensions, AddResilienceHandler]
on_absence: hypothesis_only
---

# Objetivo

Definir políticas de resiliência para dependências remotas (HTTP e similares) em microservices .NET, evitando tempestade de retries, amplificação de falha e mascaramento de erros não idempotentes.

## TL;DR

- Sempre definir **timeout** explícito por dependência; timeout global do host não substitui política por cliente.
- Retry apenas para falhas **transientes** e idempotentes (ou com idempotência de negócio garantida); usar backoff exponencial com **jitter**.
- Circuit breaker abre após limiar configurado; half-open com probes limitados.
- Não aplicar retry cego em `POST` sem chave de idempotência ou contrato deduplicável.

## Política de retry

- Condições típicas: `HttpRequestException`, timeouts, `5xx` selecionados, `429` **somente** se respeitar `Retry-After` ou política explícita.
- Limitar tentativas (ex.: 2–3); registrar cada retentativa em log estruturado com contagem e `DependencyName`.
- Introduzir jitter uniforme para evitar sincronização de clientes.

## Circuit breaker

- Abrir quando taxa de falha ultrapassar limiar em janela configurável.
- Quando aberto, falhar rápido e sinalizar degradação (`503` na API somente se política de produto permitir).

## Snippet

```csharp
var retry = HttpPolicyExtensions
    .HandleTransientHttpError()
    .OrResult(r => r.StatusCode == HttpStatusCode.TooManyRequests)
    .WaitAndRetryAsync(3, attempt => TimeSpan.FromMilliseconds(100 * Math.Pow(2, attempt))
        + TimeSpan.FromMilliseconds(Random.Shared.Next(0, 50)));

var breaker = HttpPolicyExtensions
    .HandleTransientHttpError()
    .CircuitBreakerAsync(handledEventsAllowedBeforeBreaking: 5, durationOfBreak: TimeSpan.FromSeconds(30));

builder.Services.AddHttpClient<IContasApiClient, ContasApiClient>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Integrations:Contas:BaseUrl"]!);
    c.Timeout = TimeSpan.FromSeconds(10);
}).AddPolicyHandler(retry).AddPolicyHandler(breaker);
```

## Pode ser feito

- Combinar bulkhead por dependência quando houver risco de esgotar pool de threads/socket.
- Parametrizar políticas via `IOptions` por ambiente.

## Não pode ser feito

- Retry infinito ou sem circuit breaker.
- Retentar `4xx` de contrato (exceto `408`/`429` com política explícita).
- Bloquear thread com `.Result` / `.Wait()` em caminhos ASP.NET Core.
