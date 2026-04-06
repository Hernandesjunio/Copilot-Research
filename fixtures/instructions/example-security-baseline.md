---
id: security-baseline-secrets
title: "Linha de base — segredos e dados sensíveis"
tags: [security, secrets, compliance]
priority: high
kind: policy
---

# Segredos e dados sensíveis

- Nunca commitar tokens, passwords ou connection strings; usar cofre ou variáveis de pipeline.
- Não ecoar valores de cabeçalhos de autorização em logs.
- Rotacionar credenciais quando houver suspeita de vazamento.

Esta instrução em formato **policy** no corpus reforça o tema; o repositório de serviço deve ainda ter **regra nativa** curta equivalente (sempre presente no contexto).
