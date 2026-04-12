# Research

Notas e experimentos que **não** são conteúdo canônico do corpus MCP.

| Pasta | Finalidade |
|-------|------------|
| [`experimentos-mcp/`](experimentos-mcp/) | Registro de experimentos com Copilot + servidor MCP (prompts, setup, conclusões). |

## Análises

- [`analises/2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md`](analises/2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md) — comparativo entre `templates/copilot-instructions.thin.md` e recomendação do Copilot Chat (`research/rascunho.md`); inconsistências I1–I7 e implicações para MCP genérico vs. explícito.
- [`analises/2026-04-09-analise-tecnica-mcp-copilot.md`](analises/2026-04-09-analise-tecnica-mcp-copilot.md) — análise comparativa (STDIO vs HTTP vs híbrido; tools/resources/prompts).
- [`analises/2026-04-09-distribuicao-central-cache-local-stdio.md`](analises/2026-04-09-distribuicao-central-cache-local-stdio.md) — desenho prescritivo do modelo híbrido: **distribuição central** do corpus + **cache local** + retrieval via **MCP STDIO**.

Documentação de produto e planejamento: [`../planning/bmad/README.md`](../planning/bmad/README.md).
