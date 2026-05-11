# Prompts — Experimento A/B/C (Outbox/Mensageria)

Este experimento contém **apenas um cenário** e **três condições** (A, B e C).

## Condições

| Ficheiro | Condição | Observação |
|----------|----------|------------|
| `cenario-01-outbox-mensageria/prompt-A-baseline.md` | **A** — baseline sem fixtures | Durante a execução, `fixtures/` deve estar removida do workspace e restaurada ao final. |
| `cenario-01-outbox-mensageria/prompt-B-mcp.md` | **B** — MCP | Usar tools `corporate_instructions_*` para contexto/guardrails e citar IDs no relatório. |
| `cenario-01-outbox-mensageria/prompt-C-rag-geral.md` | **C** — RAG geral | RAG geral no codebase, com `fixtures/` intacta. |

## Regra de contaminação

Execute A, B e C em **threads/sessões separadas**, sem reutilizar texto de uma condição na outra.

