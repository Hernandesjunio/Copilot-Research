# Arquitetura MCP para projetos .NET corporativos

## Metadados
- **ID:** PROMPT-20260403-002
- **Data:** 2026-04-03
- **Contexto:** Copilot Chat no Visual Studio, modo agente (ou equivalente)
- **Objetivo:** Obter uma proposta de arquitetura MCP alinhada ao funcionamento do assistente, cobrindo tools, I/O, contexto, composição e três níveis de maturidade (MVP → avançado)
- **Hipótese (opcional):** —

## Prompt (cole exatamente o que enviar ao Copilot)

```
Com base no seu funcionamento, proponha uma arquitetura de MCP para suportar implementações em projetos .NET corporativos.

Inclua:

1) Tipos de tools recomendadas
2) Quando cada tool deve ser usada
3) Formato ideal de entrada e saída
4) Como evitar excesso de contexto
5) Estratégia de composição entre tools

Depois proponha:

- arquitetura mínima (MVP)
- arquitetura intermediária
- arquitetura avançada

Finalize com uma tabela:

tool | objetivo | valor | risco | prioridade
```

## Notas pós-envio
- Comportamento observado (opcional, preencher depois)
