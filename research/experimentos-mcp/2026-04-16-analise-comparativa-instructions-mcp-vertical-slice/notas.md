# Experimento: Análise comparativa — vertical slice (plano + implementação + validação)

- **Data:** 2026-04-16
- **Autor:** —
- **Objetivo:** Estender o desenho A/B/C do experimento de 2026-04-12 para um **vertical slice** (`PUT` e `GET` `/clientes/{id}`), cobrindo **planejamento BMAD**, **implementação** e **validação**, com **duas iterações** de síntese sobre o cenário MCP: (1) diagnóstico inicial frente a instructions locais e baseline; (2) reavaliação após melhorias dirigidas aos critérios 2 e 4 da rubrica compartilhada.

## Relação com o experimento 2026-04-12 (baseline de comparação)

- O **baseline documental** de A/B/C (planejamento de endpoint isolado) permanece em [`../2026-04-12-analise-comparativa-instructions-mcp-baseline/`](../2026-04-12-analise-comparativa-instructions-mcp-baseline/).
- A **rubrica de comparação** (11 critérios, escala 0–10) está versionada na pasta desse experimento, na raiz: [`../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md`](../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md). Este registo reutiliza essa rubrica para manter **comparabilidade** entre execuções.

## Sínteses comparativas (iterações)

| Artefato | Modelo | Descrição |
|---|---|---|
| [`analise-comparativa-iteracao-1.md`](analise-comparativa-iteracao-1.md) | Opus 4.6 (Cursor Agent) | Primeira síntese após execução A/B/C no vertical slice; matriz de critérios, evidências e leitura do desempenho relativo do MCP. |
| [`analise-comparativa-iteracao-2.md`](analise-comparativa-iteracao-2.md) | Opus 4.6 (Cursor Agent) | Segunda síntese após ajustes de prompt e tools MCP documentados em [`artefatos/plano-bmad-melhoria-mcp-criterios-2-4.md`](artefatos/plano-bmad-melhoria-mcp-criterios-2-4.md); **re-execução isolada** do cenário A (MCP); B e C mantidos para isolar o efeito das melhorias. |

## Artefatos (ensaíos e anexos)

| Artefato | Modelo | Descrição |
|---|---|---|
| [`artefatos/hipotese1.md`](artefatos/hipotese1.md) | GPT 5.4 | Cenário **A — MCP** (atualizado na segunda iteração conforme plano de melhoria). |
| [`artefatos/hipotese2.md`](artefatos/hipotese2.md) | GPT 5.4 | Cenário **B — Instructions locais**. |
| [`artefatos/hipotese3.md`](artefatos/hipotese3.md) | GPT 5.4 | Cenário **C — Baseline**. |
| [`artefatos/plano-bmad-melhoria-mcp-criterios-2-4.md`](artefatos/plano-bmad-melhoria-mcp-criterios-2-4.md) | — | Plano de melhoria entre iteração 1 e 2 (MCP). |
| [`Prompts/prompt-com-mcp.md`](Prompts/prompt-com-mcp.md) | — | Prompt do cenário MCP (referenciado no orquestrador). |
| [`Prompts/prompt-com-instrucoes-locais.md`](Prompts/prompt-com-instrucoes-locais.md) | — | Prompt com instructions locais. |
| [`Prompts/prompt-sem-mcp-e-instructions.md`](Prompts/prompt-sem-mcp-e-instructions.md) | — | Prompt baseline. |
| [`orquestrador/copilot-instructions.md`](orquestrador/copilot-instructions.md) | — | Entrypoint neutro com caminhos para os três `copilot-instructions-*.md` de cenário. |

## Setup

- **IDE / extensão Copilot:** pesquisa com assistentes no ecossistema Cursor / Copilot Chat / outras LLMs citadas nos artefatos.
- **Modelo:** ensaios A/B/C com **GPT 5.4**; sínteses comparativas com **Opus 4.6 (Cursor Agent)**.
- **`INSTRUCTIONS_ROOT` ou corpus usado:** alinhado ao controlo do experimento anterior (corpus deliberadamente comparável entre A e B onde aplicável).
- **Tools MCP (cenário A):** evolução documentada entre iterações (inclui reforço de índice, batch read e parâmetros de busca conforme `plano-bmad-melhoria-mcp-criterios-2-4.md` e `analise-comparativa-iteracao-2.md`).

## Procedimento

1. **Controle:** cada condição em **thread separada**, partindo do zero, sem contaminação sequencial.
2. **Metodologia staged:** BMAD / plano técnico antes de implementação; em seguida implementação e validação do vertical slice.
3. **Tarefa canónica:** `PUT /clientes/{id}` (substituição total) e `GET /clientes/{id}` no codebase de referência das hipóteses.
4. **Iteração 2:** aplicar melhorias MCP; repetir apenas o cenário **A**; atualizar síntese (`analise-comparativa-iteracao-2.md`).

## Resultado

- **Entregáveis:** duas sínteses comparativas versionadas, plano de melhoria MCP, três ensaios (com nota de qual cenário foi reexecutado na segunda volta) e prompts/orquestrador para reprodutibilidade documental.
- **O que funcionou bem:** encadeamento explícito **diagnóstico → plano de melhoria → reavaliação** com variável isolada (reexecução de A).
- **O que permanece como limitação:** generalização além deste slice e bateria estatística de repetições; ver secções de limitações nas duas sínteses.

## Conclusões e próximos passos

- Consolidar aprendizados das duas iterações nas decisões de roadmap do servidor MCP e dos prompts de orquestração.
- Repetir o protocolo em tarefas de maior superfície (multi-arquivo, testes automatizados como gate) quando o EPIC-04 tiver sessões métricas arquivadas.
