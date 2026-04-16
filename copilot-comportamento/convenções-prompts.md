# Convenções de prompts (Copilot + MCP)

Frases e fluxos reutilizáveis. Ajuste nomes de servidor e de tools ao que tiver no `.mcp.json`.

## Antes de um design ou refatoração grande

1. Peça uma busca ao corpus primeiro, com contexto concreto:

   > Use o MCP **corporate-instructions**: chame `search_instructions` com a query: «[tecnologia ou domínio] + [preocupação, ex.: handlers REST, idempotência, DI]». Resuma os `id` mais relevantes antes de propor código.

2. Se precisar do texto completo de um documento:

   > Para o(s) `id` **[id-devolvido(s)]**, chame `get_instructions_batch` e aplique só o que for compatível com as instructions nativas deste repo.

## Ao implementar um endpoint ou feature vertical

> Siga as instructions nativas deste repositório. Para padrões organizacionais, consulte o MCP: `search_instructions` com «[ex.: Open Finance, repository pattern]»; se necessário, `get_instructions_batch` com os `id` escolhidos. Não contradiga políticas locais.

## Quando o modelo não invocou o MCP

> Obrigatório: invoque as tools `search_instructions` e `get_instructions_batch` antes de continuar; a tarefa depende do corpus corporativo.

## Baseline sem corpus (controlo na pesquisa)

Na síntese **2026-04-12** ([`artefatos/analise-comparativa.md`](../research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/artefatos/analise-comparativa.md)), o cenário **C** (sem instructions estruturadas nem MCP) aparece com **DX mais baixa**, **dependência maior de reprompt** e lista explícita de temas que exigiriam **intervenção humana** frente a A/B com corpus.

Use este quadro para pedir ao modelo que reconheça lacunas quando não houver MCP/instructions: “liste suposições e o que falta confirmar antes de decidir”.

## MCP vs instructions locais (mecanismo, não só “qual é melhor”)

- **2026-04-12** (mesmo `analise-comparativa.md`): a diferença estrutural entre A e B é o **mecanismo de acesso** (leitura de ficheiros locais vs busca determinística via tools), com impacto projetado em corpus grande.
- **2026-04-16** iteração 1 ([`analise-comparativa-iteracao-1.md`](../research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-1.md)): no slice documentado, o cenário com instructions locais teve **mais tool calls** e **mais ficheiros citados** que o MCP na primeira volta; na iteração 2 o MCP foi ajustado (prompt + tools) e a síntese compara métricas — conclusões são **condicionadas** a modelo e cliente indicados nos artefatos (ver [`research/README.md`](../research/README.md), limitações).

## Checklist rápido em um único prompt

- Contexto do serviço (stack, boundaries).
- Objeto da tarefa (arquivos ou área).
- Pedido explícito: buscar no MCP com query X; depois implementar alinhado ao nativo.

## Registro

Experimentos que mudem corpus ou fluxo devem ser documentados em [`../research/experimentos-mcp/`](../research/experimentos-mcp/) (copiar [`_template-experimento.md`](../research/experimentos-mcp/_template-experimento.md)).
