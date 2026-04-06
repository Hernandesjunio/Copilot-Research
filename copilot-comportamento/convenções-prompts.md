# Convenções de prompts (Copilot + MCP)

Frases e fluxos reutilizáveis. Ajuste nomes de servidor e de tools ao que tiveres no `.mcp.json`.

## Antes de desenho ou refactor grande

1. Peça uma busca ao corpus primeiro, com contexto concreto:

   > Usa o MCP **corporate-instructions**: chama `search_instructions` com a query: «[tecnologia ou domínio] + [preocupação, ex.: handlers REST, idempotência, DI]». Resume os `id` mais relevantes antes de propor código.

2. Se precisares do texto completo de um documento:

   > Para o `id` **[id-devolvido]**, chama `get_instruction` e aplica só o que for compatível com as instructions nativas deste repo.

## Ao implementar um endpoint ou feature vertical

> Segue as instructions nativas deste repositório. Para padrões organizacionais, consulta o MCP: `search_instructions` com «[ex.: Open Finance, repository pattern]»; se necessário, `get_instruction` pelo `id` escolhido. Não contradigas políticas locais.

## Quando o modelo não invocou o MCP

> Obrigatório: invoca tu as tools `search_instructions` (e `get_instruction` se precisares) antes de continuar; a tarefa depende do corpus corporativo.

## Checklist rápido num único prompt

- Contexto do serviço (stack, boundaries).
- Objeto da tarefa (ficheiros ou área).
- Pedido explícito: buscar no MCP com query X; depois implementar alinhado ao nativo.

## Registo

Ensaios que mudem corpus ou fluxo devem ser documentados em [`../research/experimentos-mcp/`](../research/experimentos-mcp/) (copiar [`_template-experimento.md`](../research/experimentos-mcp/_template-experimento.md)).
