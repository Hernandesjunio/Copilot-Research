# MCP altamente eficiente em uso de contexto

## Metadados
- **ID:** PROMPT-20260403-002
- **Data:** 2026-04-03
- **Contexto:** Copilot Chat (design de servidor MCP / integração)
- **Objetivo:** Obter orientação prática sobre formatos de contexto, reação a ruído e heurísticas de busca para implementar um MCP que minimize desperdício de tokens e maximize relevância
- **Hipótese (opcional):** Respostas ancoradas em como você consome contexto na prática, não em teoria genérica de RAG

## Prompt (cole exatamente o que enviar ao Copilot)

```
Quero projetar um MCP altamente eficiente em uso de contexto.

Responda pensando em implementação real de código (contratos de tools, payloads, estratégias de retrieval), não em explicações teóricas genéricas.

1) Qual formato de contexto você utiliza melhor?
   - chunks pequenos
   - documentos completos
   - resumos estruturados
   - evidências com metadados

Para cada opção, diga quando vale a pena e qual o principal risco de custo ou perda de precisão.

2) Como você reage a:
   - excesso de contexto
   - contexto irrelevante
   - contexto redundante

Seja explícito sobre o efeito prático (ex.: dilui atenção, ignora trechos, repete erros).

3) Quais heurísticas são ideais para:
   - decidir buscar mais contexto
   - parar de buscar
   - evitar repetição entre chamadas
   - priorizar trechos relevantes

Sugira critérios que eu possa codificar (limites, sinais, ordem de prioridade).

4) Você trabalha melhor com:
   - tools especializadas (uma por domínio ou tipo de dado)
   - tool genérica de busca
   - combinação das duas

Explique como estruturar isso no servidor MCP para reduzir chamadas inúteis e payloads grandes sem perder capacidade de resposta.

Feche com uma lista curta de anti-patterns concretos a evitar na implementação.
```

## Notas pós-envio
- Comportamento observado (opcional, preencher depois)
