# Prompts do experimento — cenários complexos

Cada pasta `cenario-0X-*` contém **três** ficheiros para a mesma tarefa, diferindo só na **condição experimental**:

| Ficheiro | Condição | Copilot / VS |
|----------|----------|----------------|
| `prompt-com-mcp.md` | **A** — MCP `corporate-instructions` | Apontar instruções do projeto para `orquestrador/copilot-instructions-mcp.md` (e MCP ativo). |
| `prompt-com-instrucoes-locais.md` | **B** — `.github/instructions/` | Apontar para `orquestrador/copilot-instructions-instructions-locais.md`. |
| `prompt-sem-mcp-e-instructions.md` | **C** — Baseline | Apontar para `orquestrador/copilot-instructions-baseline.md`. |

**Regra:** uma combinação **cenário × (A|B|C)** por sessão/thread, sem contaminação.

O **corpo da tarefa** está **inteiro** dentro de cada prompt (não depende de outros ficheiros para descrever o ticket). Registe métricas de execução conforme o protocolo do experimento (tempo, tool calls, critérios de aceite).

**Convenção de pastas**

- `cenario-01-outbox-mensageria`
- `cenario-02-cep-viacep`
- `cenario-03-auth-jwt`
- `cenario-04-saga-onboarding`
