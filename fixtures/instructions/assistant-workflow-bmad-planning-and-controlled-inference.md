---
id: assistant-workflow-bmad-planning-and-controlled-inference
title: "Fluxo de assistência — BMAD/spec-driven, refinamento e inferência controlada"
tags: [assistant, planning, bmad, spec-driven, governance, inference, legacy, confidence]
scope: "**/*"
priority: high
kind: policy
owner: platform-architecture
last_reviewed: 2026-05-03
status: active
---

# Objetivo

Impor um fluxo mínimo de planejamento e revisão para trabalhos assistidos por IA neste repositório, reduzindo invenção de requisitos, ambiguidade e inconsistência com o corpus de instructions, especialmente em legados ou más práticas pré-existentes.

Quando houver **cenário canônico** ou **spec já fornecida**, a IA deve operar em modo **spec-driven**: primeiro compreender e refinar a spec, depois planejar a implementação, e só ao final consolidar avaliação/métricas.

## TL;DR

- Antes de implementar mudanças relevantes, produzir **plano BMAD simplificado obrigatório**: **B**ackground, **M**ission/goal, **A**pproach, **D**elivery/validation.
- Quando o usuário já forneceu **spec**, **ticket canônico** ou **cenário fixo**, não reabrir o domínio por conveniência: refinar limites, lacunas e critérios de aceite antes de propor código.
- Sempre executar **refinamento técnico** do plano: riscos, impacto arquitetural/operacional, dependências, critérios de aceite técnico e alternativas rejeitadas.
- Em dúvida sobre requisitos, contratos externos ou comportamento legado: **parar e solicitar esclarecimento em nova interação** em vez de supor.
- Inferência em legado só é permitida quando explicitamente rotulada como **hipótese** com impacto e passos de validação.
- Conteúdo normativo adicional do corpus deve seguir `instruction-authoring-standard`.

## BMAD simplificado (obrigatório)

1. **Background**: contexto, restrições, arquivos/serviços tocados, instruções aplicáveis.
2. **Mission**: resultado observável e critérios de pronto.
3. **Approach**: passos técnicos, alternativas consideradas, decisões de trade-off.
4. **Delivery**: como validar (testes, checks manuais), rollback/feature flag, observabilidade afetada.

## Quando existir spec ou cenário canônico

- Preservar o **problema de negócio** já fornecido; não trocar o cenário por outro "mais conveniente" sem pedir confirmação.
- Separar explicitamente:
  - o que já veio fixado pela spec;
  - o que foi inferido a partir do repo/corpus;
  - o que continua bloqueado por falta de evidência.
- Refinar a spec em termos de:
  - fluxo principal;
  - fluxos de falha e compensação;
  - infraestrutura permitida vs opcional;
  - critérios de aceite observáveis.
- Em cenários multipasso, preferir uma formulação curta e auditável do tipo:
  - passos principais;
  - compensações;
  - estados principais;
  - timeout/retry/idempotência;
  - como validar.
- Não misturar **execução técnica** com **julgamento experimental** no mesmo bloco principal; primeiro entregar spec refinada + BMAD + validação, e só depois consolidar métricas/parecer.

## Refinamento crítico (obrigatório após o BMAD)

- Liste **riscos** (segurança, consistência, performance, compatibilidade).
- Liste **dependências** (outros times, filas, contratos, migrações).
- Defina **critérios de aceite técnico** mensuráveis (ex.: latência p95, ausência de PII em logs, testes adicionados).
- Liste também **decisões bloqueadas**: pontos que não podem ser fechados sem evidência adicional do repo, contrato ou usuário.

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
- Decisões bloqueadas: ...
```

## Template curto para cenário canônico

```
Spec refinada
- Fluxo principal: passo 1 -> passo 2 -> passo 3
- Compensações: falha em 2 => compensa 1; falha em 3 => compensa 2 e 1
- Estados principais: ...
- Infra permitida: ...
- Infra opcional se houver evidência no repo: ...
- Critérios de aceite: happy path, falha intermediária, falha final, retry, timeout, idempotência
```

## Checklist de qualidade do plano BMAD

- [ ] **Background** cita ficheiros ou módulos concretos e instructions aplicáveis (`id`).
- [ ] **Mission** tem critério de pronto verificável (teste, endpoint, métrica).
- [ ] **Approach** lista passos ordenados e **alternativas** consideradas ou explícita “não há alternativa razoável”.
- [ ] **Delivery** inclui validação (automática ou manual) e impacto em observabilidade/rollback quando relevante.
- [ ] **Refinamento** cobre pelo menos um risco e uma dependência externa quando existirem.
- [ ] Quando houver spec fixa, o plano deixa claro o que está **fixado**, o que é **hipótese** e o que está **bloqueado**.
- [ ] O cenário não foi ampliado com mensageria, outbox, workers ou contratos públicos novos sem evidência suficiente.

## Quando a IA deve explicitar incerteza

- Requisito, SLA ou contrato externo **não** está no código nem nas instructions recuperadas.
- Há **várias** políticas HTTP ou de produto plausíveis (ex.: `404` vs `403` em mascaramento) sem texto nativo no repositório.
- O legado sugere um comportamento mas o teste ou o comentário é ambíguo: apresentar **2–3 opções** com trade-offs e recomendar validação humana.
- Nunca apresentar escolha de política organizacional como facto; usar formulações do tipo “se a política for X, então Y”.
- A spec pede SAGA, mensageria, outbox, timeout, retry ou observabilidade, mas o repo não mostra sinais suficientes de stack ou contrato para implementar isso com segurança.

## Anti-exemplos

- Plano com **Approach** longo mas **Delivery** vazio (“implementar e testar” sem dizer como).
- Misturar **hipótese** e facto na mesma frase sem etiqueta (`Hipótese: …`).
- Ignorar instructions `kind: policy` do corpus sob o argumento de “preferência de estilo” sem exceção documentada.
- BMAD sem **Refinamento** quando a mudança toca segurança, persistência ou contrato público.
- Reescrever a spec do usuário para caber em uma solução preferida do assistente.
- Misturar no mesmo artefato principal a entrega de engenharia e o score/parecer experimental da rodada.

## Pode ser feito

- Agrupar itens altamente coesos na mesma mudança quando reduzir fragmentação artificial, mantendo PR revisável.
- Documentar “decisão tomada pelo assistente” apenas quando inevitável, com rastreabilidade no PR.
- Em cenário canônico já fixado, propor a **menor** arquitetura capaz de satisfazer a spec e os guardrails observáveis.

## Não pode ser feito

- Implementar comportamento não solicitado “por conveniência”.
- Contradizer instructions do corpus sem registro explícito de exceção aprovada.
- Apresentar suposição como fato sem rotular como hipótese.
- Tratar mensageria, outbox, workers ou integrações externas como obrigatórios apenas porque o tema "combina" com SAGA.

## Impacto esperado na resposta da IA

- Planos e respostas priorizam **rastreabilidade** (ficheiros, `id` de instructions, critérios de aceite).
- Lacunas normativas são **nomeadas** em vez de preenchidas silenciosamente com política inventada.
- A execução tende a ficar mais próxima de um fluxo de desenvolvimento real: spec/refino -> BMAD -> implementação -> validação -> métricas.

## Confiança (níveis práticos)

| Nível | Condição | Comportamento |
| --- | --- | --- |
| Alta | Há `kind: policy` no corpus cobrindo a decisão | Aplicar a regra; citar o `id`. |
| Média | Apenas `reference` ou padrão forte no código | Seguir o padrão; mencionar que não é policy explícita. |
| Baixa | Sem corpus nem evidência no repo | Declarar lacuna; hipóteses numeradas ou pedido de input humano. |
