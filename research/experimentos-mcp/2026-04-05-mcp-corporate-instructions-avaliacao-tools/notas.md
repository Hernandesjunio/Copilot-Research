# Experimento: MCP corporate-instructions — avaliação e evolução de tools

- **Data:** 2026-04-05
- **Autor:** —
- **Objetivo:** Validar o servidor MCP `corporate-instructions` em um projeto .NET 8 real (ClientesAPI), com corpus em `fixtures/instructions`, e produzir uma avaliação sobre **tools adicionais** que melhorem a integração com o Copilot; documentar **impacto agêntico** das propostas, **métrica de janela de contexto** via `copilot-instructions.md`, e o padrão **pseudo-hook orchestrator**.

## Relatório principal (síntese única)

| Artefato | Descrição |
|---|---|
| [`2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`](2026-04-05-mcp-corporate-instructions-avaliacao-tools.md) | Registro completo: setup, três experimentos (tools, agêntico, janela de contexto), seis tools recomendadas, matrizes e conclusões. |

## Artefatos e anexos

| Artefato | Descrição |
|---|---|
| [`Prompts/perguntas-registro-experimento.md`](Prompts/perguntas-registro-experimento.md) | Perguntas que estruturaram os três experimentos no registro. |
| [`orquestrador/copilot-instructions.md`](orquestrador/copilot-instructions.md) | Entrypoint com ligações aos exemplos de orquestração. |
| [`orquestrador/copilot-instructions-exemplo-pseudo-hook.md`](orquestrador/copilot-instructions-exemplo-pseudo-hook.md) | Exemplo mínimo de `copilot-instructions.md` como pseudo-hook (orquestração de tools). |
| [`artefatos/`](artefatos/) | Reservado para anexos futuros (diagramas, exports de índice MCP, etc.). |

## Setup (resumo)

- **Ambiente:** Visual Studio Community 2026; .NET 8; projeto ClientesAPI (TestClientCorporateInstructions).
- **MCP:** `corporate-instructions` (stdio); tools usadas na época: `list_instructions_index`, `search_instructions`, `get_instruction`.

Detalhes e exemplos de `.mcp.json` estão no relatório principal.

## Procedimento (resumo)

Três experimentos no mesmo contexto: (1) avaliação de tools adicionais; (2) dimensão “agêntico”; (3) feedback de janela de contexto e `copilot-instructions.md`.

## Resultado e conclusões

Ver o relatório principal; inclui roadmap por fases para novas tools e o papel do orchestrator por repositório.
