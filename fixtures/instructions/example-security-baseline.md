---
id: example-security-baseline
title: "Linha de base de segurança — segredos e dados sensíveis"
tags: [security, secrets, compliance]
scope: "**/*"
priority: high
kind: policy
owner: "<!-- TODO -->"
last_reviewed: 2026-05-10
status: active
---

# Objetivo

Evitar vazamento de segredos e exposição de dados sensíveis em código e telemetria.

## TL;DR

# Segredos e dados sensíveis

- Nunca commitar tokens, senhas ou connection strings; usar cofre ou variáveis de pipeline.
- Não ecoar valores de cabeçalhos de autorização em logs.
- Rotacionar credenciais quando houver suspeita de vazamento.

## Critérios verificáveis

<!-- TODO: adicionar critérios verificáveis (ex.: o que é considerado "segredo" e como validar em PR/CI/logs) -->

## Pode ser feito

<!-- TODO: listar ações permitidas e recomendadas de forma verificável -->

## Não pode ser feito

<!-- TODO: listar violações explícitas (ex.: commits com segredos, logs com Authorization) -->

## Anti-exemplos

<!-- TODO: inserir 1-2 anti-exemplos curtos (sem segredos reais) -->

Esta instrução em formato **policy** no corpus reforça o tema; o repositório de serviço deve ainda ter **regra nativa** curta equivalente (sempre presente no contexto).
