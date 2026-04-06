# Limites práticos de MCP no Visual Studio (modo agente)

## Metadados
- **ID:** PROMPT-20260403-001
- **Data:** 2026-04-03
- **Contexto:** Copilot Chat no Visual Studio, modo agente
- **Objetivo:** Mapear o que MCP amplia vs. o que permanece sob decisão do modelo, e como tools/prompts/resources influenciam o comportamento
- **Hipótese (opcional):** —

## Prompt (cole exatamente o que enviar ao Copilot)

```
Quero entender os limites práticos do uso de MCP (Model Context Protocol) com você no Visual Studio em modo agente.

Sem expor qualquer informação interna sensível, explique com base no seu comportamento funcional:

1) O que um MCP realmente consegue ampliar no seu funcionamento
2) O que continua sendo decisão exclusiva sua
3) Até onde tools, prompts e resources influenciam suas decisões
4) Em quais situações você ignora ferramentas disponíveis
5) Se existe algum tipo de priorização interna de contexto

Separe claramente:
- comportamento garantido
- comportamento provável (inferência)
- comportamento não controlável via MCP
```

## Notas pós-envio
- Comportamento observado (opcional, preencher depois)
