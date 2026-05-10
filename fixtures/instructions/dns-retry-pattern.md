---
id: dns-retry-pattern
title: "Padrão de retry para resolução DNS"
tags: [dns, resilience, polly]
scope: "**/*.cs"
priority: high
kind: reference
owner: platform-architecture
last_reviewed: 2026-05-04
status: active
---

# Objetivo

Definir um padrão consistente e seguro de retry para falhas transitórias de resolução DNS em serviços.

## TL;DR

- Usar backoff exponencial com jitter e limites (sem retry infinito).
- Preferir a biblioteca de resiliência já adotada no serviço (ex.: Polly em .NET).
- Manter caminhos quentes não-bloqueantes (`async`/`await`) e registrar falhas com correlação.

## Padrão de retry para DNS

Em resolvers DNS internos, usar política de retry com backoff exponencial alinhada ao cliente HTTP do serviço.

- Preferir bibliotecas de resiliência já adotadas no microserviço (ex.: Polly em .NET).
- Não bloquear o thread de consumo: sempre `async`/`await` nos caminhos quentes.
- Registrar falhas com correlação (`CorrelationId`) para diagnóstico.

## Anti-exemplos

- Retry infinito sem escalonamento por domínio/falha DNS.
- Logs com dados pessoais ou domínios completos em claro quando a política de privacidade proíbe.
