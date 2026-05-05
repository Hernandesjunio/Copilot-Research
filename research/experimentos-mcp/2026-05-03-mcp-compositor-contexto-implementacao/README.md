# Experimento — MCP como compositor de contexto

Este experimento foi desenhado para validar o MCP `corporate-instructions` como **compositor de contexto** para implementação, com foco em um único cenário e sem comparação A/B/C nesta etapa.

## Objetivo

Verificar se uma execução em fases, apoiada por MCP e sem exigir que o dev conheça nomes de tools, melhora:

- a composição de contexto antes do patch;
- a qualidade e o foco da implementação;
- a rastreabilidade entre contexto, decisão, patch e validação.

## Como usar

Siga o guia operacional em [`experiment-guide.md`](experiment-guide.md).

Esse guia contém:

- pré-requisitos;
- ordem exata de execução;
- modelo recomendado por etapa;
- prompts numerados;
- convenção de artefatos e resultados;
- procedimento de coleta de métricas.

## Estrutura

```text
2026-05-03-mcp-compositor-contexto-implementacao/
├── README.md
├── experiment-guide.md
├── prompts/
│   ├── 01-composicao-contexto-mcp.md
│   ├── 02-plano-bmad-mcp.md
│   ├── 03-implementacao-mcp.md
│   └── 04-validacao-relatorio-mcp.md
├── templates/
│   ├── contexto-composition-template.md
│   └── relatorio-final-template.md
├── artefatos/
│   └── .gitkeep
└── resultados/
    └── .gitkeep
```

## Escopo atual

- Cenário alvo: outbox/mensageria para consistência eventual.
- Condição experimental: MCP only.
- Foco: composição de contexto e execução profissional em fases.

## Leitura recomendada

- Guia operacional: [`experiment-guide.md`](experiment-guide.md)
- Prompt 1: [`prompts/01-composicao-contexto-mcp.md`](prompts/01-composicao-contexto-mcp.md)
- Prompt 2: [`prompts/02-plano-bmad-mcp.md`](prompts/02-plano-bmad-mcp.md)
- Prompt 3: [`prompts/03-implementacao-mcp.md`](prompts/03-implementacao-mcp.md)
- Prompt 4: [`prompts/04-validacao-relatorio-mcp.md`](prompts/04-validacao-relatorio-mcp.md)
