---
id: microservice-clean-architecture-guardrails
title: "Guardrails de Clean Architecture para microservices"
tags: [microservice, clean-architecture, observability, resilience, security, testing]
scope: "**/*.cs"
priority: high
kind: policy
---

# Objetivo

Estabelecer guardrails técnicos para garantir que microservices crescam com qualidade arquitetural, segurança e operação previsível em produção.

## TL;DR

- Dependências sempre apontam para dentro (infra depende de domínio/interfaces).
- Contratos externos estáveis, versionados e backward compatible quando possível.
- Observabilidade e resiliência são requisitos de projeto, não itens opcionais.
- Segurança e testes mínimos são obrigatórios antes de promover para produção.

## Snippet

```csharp
services.AddHealthChecks()
    .AddCheck<SqlHealthCheck>("sql")
    .AddCheck<StorageHealthCheck>("table-storage");

services.AddOpenTelemetry()
    .WithTracing(builder => builder
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation());
```

## Pode ser feito

- Implementar health checks (`/health/live`, `/health/ready`) e métricas.
- Aplicar timeout, retry com backoff e circuit breaker em integrações críticas.
- Usar idempotência em operações de escrita expostas externamente.
- Definir contratos com versionamento claro e documentação pública.
- Criar testes unitários (domínio), integração (repositório) e contrato (API).

## Não pode ser feito

- Fazer chamadas síncronas bloqueantes em fluxo I/O-bound.
- Ignorar `CancellationToken` em operações de acesso externo.
- Publicar logs com dados sensíveis (PII, segredos, token, credenciais).
- Acoplar regras de negócio a detalhes de transporte (HTTP, fila, banco).
- Liberar deploy sem trilha mínima de observabilidade e cobertura crítica.
