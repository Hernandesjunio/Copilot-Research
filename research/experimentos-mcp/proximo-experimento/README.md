# Experimento — cenários complexos (MCP vs instructions locais vs baseline)

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
