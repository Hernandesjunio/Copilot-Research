# Experimento — cenários complexos (MCP vs instructions locais vs baseline)

> **STATUS: INVALIDADO / ARQUIVADO (tentativa de 2026-05-04).**
>
> Esta pasta foi criada inicialmente como “próximo experimento” e depois **renomeada** para refletir o status real: **`2026-05-04-tentativa-montagem-contexto-mcp`**.
> Ela virou um **arquivo de tentativa**: a montagem completa de contexto não atingiu o critério de aceite (chegou a ~9/24 na melhor leitura), e a causa principal foi atribuída ao **resultado de recuperação/ranking do MCP**, não à orquestração (`copilot-instructions-mcp.md`) em si.
>
> Decisão registrada em:
> - `research/analises/2026-05-05-redirecionamento-mcp-instruction-retrieval-v1.md`
> - `research/nucleo-pesquisa/instruction-retrieval-v1/plano_mcp_instruction_retrieval_v1.md`

Este diretório contém a **especificação** (`experimento.md`), os **orquestradores** reutilizáveis no GitHub Copilot para Visual Studio e os **prompts** autocontidos por cenário.

## Onde está cada coisa

| Conteúdo | Localização |
|----------|-------------|
| Especificação longa, métricas e protocolo (referência) | [`experimento.md`](experimento.md) |
| Orquestradores A/B/C (copiar ou referenciar no Copilot) | [`orquestrador/`](orquestrador/) |
| Três prompts por cenário (tarefa completa no corpo do ficheiro) | [`Prompts/README.md`](Prompts/README.md) |

## Condições experimentais

| Letra | Significado | Orquestrador |
|-------|-------------|--------------|
| **A** | MCP `corporate-instructions` | `orquestrador/copilot-instructions-mcp.md` |
| **B** | `.github/instructions/` (sem MCP) | `orquestrador/copilot-instructions-instructions-locais.md` |
| **C** | Baseline (sem MCP nem instructions locais) | `orquestrador/copilot-instructions-baseline.md` |

**Procedimento:** uma combinação **(cenário 1–4) × (A|B|C)** por sessão/thread. No Visual Studio, configurar as instruções do Copilot para o ficheiro de orquestrador correspondente à condição; depois colar o prompt do ficheiro certo em `Prompts/cenario-0X-*/`.

## Pastas de cenário (prompts)

- `Prompts/cenario-01-outbox-mensageria/`
- `Prompts/cenario-02-cep-viacep/`
- `Prompts/cenario-03-auth-jwt/`
- `Prompts/cenario-04-saga-onboarding/`

Cada uma contém `prompt-com-mcp.md`, `prompt-com-instrucoes-locais.md`, `prompt-sem-mcp-e-instructions.md`.

## Nota sobre os relatórios (origem das execuções)

- `relatorio-cursor-teste/2026-05-02__*.md`: relatórios gerados via **Cursor** (smoke/comparativos).
- `relatorio-cursor-teste/2026-05-04__*.md`: análises e rebaselines derivados de execuções e leituras realizadas no **GitHub Copilot do Visual Studio** (incluindo auditorias e épicos 07–09).

Esta distinção existe para evitar a leitura equivocada de que todos os relatórios vieram do mesmo agente/IDE/modelo.
