# Convenções de prompts (Copilot + MCP)

Frases e fluxos reutilizáveis. Ajuste nomes de servidor e de tools ao que tiver no `.mcp.json`.

## Antes de um design ou refatoração grande

1. Peça uma busca ao corpus primeiro, com contexto concreto:

   > Use o MCP **corporate-instructions**: chame `search_instructions` com a query: «[tecnologia ou domínio] + [preocupação, ex.: handlers REST, idempotência, DI]». Resuma os `id` mais relevantes antes de propor código.

2. Se precisar do texto completo de um documento:

   > Para o `id` **[id-devolvido]**, chame `get_instruction` e aplique só o que for compatível com as instructions nativas deste repo.

## Ao implementar um endpoint ou feature vertical

> Siga as instructions nativas deste repositório. Para padrões organizacionais, consulte o MCP: `search_instructions` com «[ex.: Open Finance, repository pattern]»; se necessário, `get_instruction` pelo `id` escolhido. Não contradiga políticas locais.

## Quando o modelo não invocou o MCP

> Obrigatório: invoque as tools `search_instructions` (e `get_instruction` se precisar) antes de continuar; a tarefa depende do corpus corporativo.

## Checklist rápido em um único prompt

- Contexto do serviço (stack, boundaries).
- Objeto da tarefa (arquivos ou área).
- Pedido explícito: buscar no MCP com query X; depois implementar alinhado ao nativo.

## Registro

Experimentos que mudem corpus ou fluxo devem ser documentados em [`../research/experimentos-mcp/`](../research/experimentos-mcp/) (copiar [`_template-experimento.md`](../research/experimentos-mcp/_template-experimento.md)).
