---
id: microservice-opentelemetry-correlation-and-health
title: "Observabilidade — OpenTelemetry, correlação, logs e health checks"
tags: [microservice, observability, opentelemetry, tracing, metrics, logging, health]
scope: "**/*.cs"
priority: high
kind: policy
---

# Objetivo

Prescrever instrumentação com OpenTelemetry, propagação de contexto de trace, logs estruturados correlacionados e health checks (`live`/`ready`) alinhados a operação de microservices .NET em produção.

## TL;DR

- Habilitar tracing para ASP.NET Core, `HttpClient` e provedores relevantes (SQL, filas) conforme dependências do serviço.
- Propagar `traceparent`/`tracestate` em chamadas HTTP saída e consumo/produção de mensagens quando suportado.
- Logs estruturados com `TraceId`/`SpanId`/`CorrelationId` (quando aplicável); **nunca** colocar PII, segredos ou tokens em atributos de span ou logs.
- `/health/live` e `/health/ready` separados; readiness inclui dependências críticas com timeout curto.

## OpenTelemetry — regras

- Usar nomes de span estáveis e de baixa cardinalidade; evitar URLs completas com IDs como nomes de span.
- Atributos: preferir chaves semânticas conhecidas (`http.method`, `db.system`, `messaging.system`); valores de negócio só quando cardinalidade controlada (ex.: `tenant_id` se enumerável).
- Exportadores configuráveis por ambiente; amostragem consciente (head-based ou tail quando disponível) para custo.

## Correlação

- Aceitar cabeçalhos de trace W3C de entrada; gerar raiz quando ausente.
- Propagar o mesmo `Activity` para operações assíncronas iniciadas no mesmo request, respeitando `CancellationToken`.

## Snippet

```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter());

builder.Services.AddHealthChecks()
    .AddCheck<SqlReadyHealthCheck>("sql", tags: new[] { "ready" });

app.MapHealthChecks("/health/live", new HealthCheckOptions { Predicate = _ => false });
app.MapHealthChecks("/health/ready", new HealthCheckOptions { Predicate = r => r.Tags.Contains("ready") });
```

## Pode ser feito

- Criar spans manuais para trechos de negócio críticos (ex.: “processar_pagamento”) com início/fim explícitos.
- Registrar métricas de latência/contadores por dependência com labels limitadas.

## Não pode ser feito

- Criar labels/tags com IDs ilimitados (userId como tag em alta cardinalidade).
- Depender de log não estruturado como única fonte de diagnóstico em produção.
- Marcar serviço como `ready` quando dependência obrigatória está indisponível.
