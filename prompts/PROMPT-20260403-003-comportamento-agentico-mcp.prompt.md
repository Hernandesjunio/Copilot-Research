# Comportamento mais agêntico com MCP

## Metadados
- **ID:** PROMPT-20260403-003
- **Data:** 2026-04-03
- **Contexto:** Copilot Chat no Visual Studio, modo agente (e integração MCP)
- **Objetivo:** Entender se e como MCP pode induzir comportamento mais agêntico (iteração, detecção de lacunas, interrupção para busca) e qual fluxo ideal análise → contexto → refinamento → implementação
- **Hipótese (opcional):** MCP amplia ferramentas e dados, mas o grau de “agência” continua limitado pelo modelo e pelo orquestrador do agente

## Prompt (cole exatamente o que enviar ao Copilot)

```
Quero entender se consigo induzir um comportamento mais agêntico usando MCP (Model Context Protocol).

Sem expor informação interna sensível, explique com base no seu comportamento funcional no modo agente:

1) Se você consegue iterar chamadas de tools ao longo da resolução de uma tarefa (várias rodadas de tool use antes de concluir).

2) Se você detecta lacunas de contexto durante a execução (ex.: falta de spec, arquivo ausente, ambiente desconhecido) e como isso se manifesta na prática.

3) Se você consegue interromper ou pausar uma linha de solução para buscar mais informação (via MCP ou outras tools) antes de continuar implementando.

4) Qual seria um fluxo ideal entre:
   - análise
   - busca de contexto
   - refinamento
   - implementação

   Indique como essas fases se relacionam e se podem se repetir ou sobrepor.

5) Quais limitações impedem um comportamento totalmente agêntico (mesmo com MCP bem configurado).

Se possível, descreva um fluxo ideal passo a passo para uma implementação real de feature ou correção (do pedido inicial ao código entregue), incluindo onde MCP ajuda e onde o gargalo não é o protocolo.
```

## Notas pós-envio
- Resposta arquivada em `responses/PROMPT-20260403-003-comportamento-agentico-mcp.response.md` (2026-04-03).
- Comportamento observado (opcional, preencher depois)
