---
id: dns-retry-pattern
title: "Padrão de retry para resolução DNS"
tags: [dns, retry, resilience, polly]
scope: "src/**/Dns*/**"
priority: high
kind: reference
---

# Padrão de retry para DNS

Em resolvers DNS internos, usar política de retry com backoff exponencial alinhada ao cliente HTTP do serviço.

- Preferir bibliotecas de resiliência já adotadas no microserviço (ex.: Polly em .NET).
- Não bloquear o thread de consumo: sempre `async`/`await` nos caminhos quentes.
- Registrar falhas com correlação (`CorrelationId`) para diagnóstico.

## Anti-padrões

- Retry infinito sem circuit breaker.
- Logs com dados pessoais ou domínios completos em claro quando a política de privacidade proíbe.
