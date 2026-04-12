---
id: assistant-workflow-bmad-planning-and-controlled-inference
title: "Fluxo de assistência — BMAD obrigatório, refinamento e inferência controlada"
tags: [assistant, planning, bmad, governance, inference, legacy]
scope: "**/*"
priority: high
kind: policy
---

# Objetivo

Impor um fluxo mínimo de planejamento e revisão para trabalhos assistidos por IA neste repositório, reduzindo invenção de requisitos, ambiguidade e inconsistência com o corpus de instructions, especialmente em legados ou más práticas pré-existentes.

## TL;DR

- Antes de implementar mudanças relevantes, produzir **plano BMAD simplificado obrigatório**: **B**ackground, **M**ission/goal, **A**pproach, **D**elivery/validation.
- Sempre executar **refinamento técnico** do plano: riscos, impacto arquitetural/operacional, dependências, critérios de aceite técnico e alternativas rejeitadas.
- Em dúvida sobre requisitos, contratos externos ou comportamento legado: **parar e solicitar esclarecimento em nova interação** em vez de supor.
- Inferência em legado só é permitida quando explicitamente rotulada como **hipótese** com impacto e passos de validação.

## BMAD simplificado (obrigatório)

1. **Background**: contexto, restrições, arquivos/serviços tocados, instruções aplicáveis.
2. **Mission**: resultado observável e critérios de pronto.
3. **Approach**: passos técnicos, alternativas consideradas, decisões de trade-off.
4. **Delivery**: como validar (testes, checks manuais), rollback/feature flag, observabilidade afetada.

## Refinamento crítico (obrigatório após o BMAD)

- Liste **riscos** (segurança, consistência, performance, compatibilidade).
- Liste **dependências** (outros times, filas, contratos, migrações).
- Defina **critérios de aceite técnico** mensuráveis (ex.: latência p95, ausência de PII em logs, testes adicionados).

## Snippet (template textual)

```
BMAD
- Background: ...
- Mission: ...
- Approach: ...
- Delivery/validation: ...

Refinamento
- Riscos: ...
- Dependências: ...
- Critérios de aceite técnico: ...
```

## Pode ser feito

- Agrupar itens altamente coesos na mesma mudança quando reduzir fragmentação artificial, mantendo PR revisável.
- Documentar “decisão tomada pelo assistente” apenas quando inevitável, com rastreabilidade no PR.

## Não pode ser feito

- Implementar comportamento não solicitado “por conveniência”.
- Contradizer instructions do corpus sem registro explícito de exceção aprovada.
- Apresentar suposição como fato sem rotular como hipótese.
