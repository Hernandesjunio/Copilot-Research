# Prompt 02 — Plano BMAD orientado pelo contexto composto

## Modelo recomendado

`GPT 5.4`

Alternativo: `Sonnet 4.6`

## Objetivo da etapa

Transformar o contexto composto na etapa 1 em um plano BMAD mínimo, executável e controlado.

## Instruções de uso

1. Abra uma nova thread.
2. Cole o artefato gerado na etapa 1.
3. Cole o prompt abaixo.
4. Não peça implementação nesta etapa.

## Prompt

```md
Quero que você produza apenas o plano BMAD para a implementação do cenário de outbox/mensageria no repositório atual.

Use como entrada obrigatória o artefato de composição de contexto fornecido nesta conversa.

Nesta etapa:
- não escreva patch;
- não reabra escopo do experimento;
- não produza relatório final;
- não crie endpoints técnicos extras apenas para facilitar demonstração.

O plano deve ser derivado do contexto composto já levantado.
Se houver lacuna crítica não resolvida, ela deve virar bloqueio explícito ou fallback controlado, nunca inferência silenciosa.

Sua saída deve ter exatamente estas seções:

## 1. Background
Resuma apenas fatos relevantes do repo e do contexto MCP.

## 2. Mission
Defina o objetivo técnico mínimo desta implementação.

## 3. Approach
Liste os passos de implementação em ordem.
Cada passo deve informar:
- objetivo;
- camada ou área impactada;
- dependência de contexto MCP;
- risco.

## 4. Delivery/validation
Liste:
- build esperado;
- testes ou validações objetivas;
- critérios de aceite que serão cobertos;
- o que ficará como validação manual, se necessário.

## 5. Decisões permitidas
Liste as decisões que o implementador pode tomar sem nova confirmação humana.

## 6. Decisões bloqueadas
Liste decisões que não devem ser tomadas por inferência.

## 7. Escopo mínimo
Explique qual é a menor mudança coerente para cumprir o cenário.

## 8. Guardrails da implementação
Registre regras claras para a próxima etapa, incluindo:
- evitar overengineering;
- respeitar evidência do repo;
- usar MCP como suporte de decisão, não como justificativa para inventar infraestrutura ausente.

Restrições:
- responda em português;
- seja específico;
- use BMAD curto e auditável;
- explicite FATO, HIPÓTESE e RISCO DE INTERPRETAÇÃO quando necessário.
```

## Saída esperada

Salvar o resultado em:

`artefatos/YYYY-MM-DD__plano-bmad.md`
