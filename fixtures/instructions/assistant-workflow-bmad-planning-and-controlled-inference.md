---
id: assistant-workflow-bmad-planning-and-controlled-inference
title: "Fluxo de assistência — BMAD obrigatório, refinamento e inferência controlada"
tags: [assistant, planning, bmad, governance, inference, legacy, confidence]
scope: "**/*"
priority: high
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Impor um fluxo mínimo de planejamento e revisão para trabalhos assistidos por IA neste repositório, reduzindo invenção de requisitos, ambiguidade e inconsistência com o corpus de instructions, especialmente em legados ou más práticas pré-existentes.

## TL;DR

- Antes de implementar mudanças relevantes, produzir **plano BMAD simplificado obrigatório**: **B**ackground, **M**ission/goal, **A**pproach, **D**elivery/validation.
- Sempre executar **refinamento técnico** do plano: riscos, impacto arquitetural/operacional, dependências, critérios de aceite técnico e alternativas rejeitadas.
- Em dúvida sobre requisitos, contratos externos ou comportamento legado: **parar e solicitar esclarecimento em nova interação** em vez de supor.
- Inferência em legado só é permitida quando explicitamente rotulada como **hipótese** com impacto e passos de validação.
- Conteúdo normativo adicional do corpus deve seguir `instruction-authoring-standard`.

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

## Checklist de qualidade do plano BMAD

- [ ] **Background** cita ficheiros ou módulos concretos e instructions aplicáveis (`id`).
- [ ] **Mission** tem critério de pronto verificável (teste, endpoint, métrica).
- [ ] **Approach** lista passos ordenados e **alternativas** consideradas ou explícita “não há alternativa razoável”.
- [ ] **Delivery** inclui validação (automática ou manual) e impacto em observabilidade/rollback quando relevante.
- [ ] **Refinamento** cobre pelo menos um risco e uma dependência externa quando existirem.

## Quando a IA deve explicitar incerteza

- Requisito, SLA ou contrato externo **não** está no código nem nas instructions recuperadas.
- Há **várias** políticas HTTP ou de produto plausíveis (ex.: `404` vs `403` em mascaramento) sem texto nativo no repositório.
- O legado sugere um comportamento mas o teste ou o comentário é ambíguo: apresentar **2–3 opções** com trade-offs e recomendar validação humana.
- Nunca apresentar escolha de política organizacional como facto; usar formulações do tipo “se a política for X, então Y”.

## Anti-exemplos

- Plano com **Approach** longo mas **Delivery** vazio (“implementar e testar” sem dizer como).
- Misturar **hipótese** e facto na mesma frase sem etiqueta (`Hipótese: …`).
- Ignorar instructions `kind: policy` do corpus sob o argumento de “preferência de estilo” sem exceção documentada.
- BMAD sem **Refinamento** quando a mudança toca segurança, persistência ou contrato público.

## Pode ser feito

- Agrupar itens altamente coesos na mesma mudança quando reduzir fragmentação artificial, mantendo PR revisável.
- Documentar “decisão tomada pelo assistente” apenas quando inevitável, com rastreabilidade no PR.

## Não pode ser feito

- Implementar comportamento não solicitado “por conveniência”.
- Contradizer instructions do corpus sem registro explícito de exceção aprovada.
- Apresentar suposição como fato sem rotular como hipótese.

## Impacto esperado na resposta da IA

- Planos e respostas priorizam **rastreabilidade** (ficheiros, `id` de instructions, critérios de aceite).
- Lacunas normativas são **nomeadas** em vez de preenchidas silenciosamente com política inventada.

## Confiança (níveis práticos)

| Nível | Condição | Comportamento |
| --- | --- | --- |
| Alta | Há `kind: policy` no corpus cobrindo a decisão | Aplicar a regra; citar o `id`. |
| Média | Apenas `reference` ou padrão forte no código | Seguir o padrão; mencionar que não é policy explícita. |
| Baixa | Sem corpus nem evidência no repo | Declarar lacuna; hipóteses numeradas ou pedido de input humano. |
