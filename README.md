# Copilot — governança, pesquisa e MCP

Repositório da iniciativa de **uso disciplinado do GitHub Copilot** com **instructions nativas mínimas**, **corpus servido via MCP** e registo de **prompts, respostas e experimentos**.

## Por onde começar

| Área | Descrição | Documentos |
|------|-----------|------------|
| Governança local | Política de camadas (nativo vs MCP), checklists e convenções de chat | [`copilot-comportamento/README.md`](copilot-comportamento/README.md) |
| Template por repo | Instructions “finas” para colar em cada repositório de aplicação | [`templates/copilot-instructions.thin.md`](templates/copilot-instructions.thin.md) |
| Planeamento | Épicos BMAD (inventário, servidor MCP, rollout, protocolo de experimentos) | [`planning/bmad/`](planning/bmad/) |
| Perguntas de pesquisa | Prompts datados usados para explorar temas (MCP, agente, arquitetura) | [`prompts/`](prompts/) |
| Respostas | Respostas alinhadas a cada prompt em `prompts/` | [`responses/`](responses/) |
| Pesquisa e ensaios | Índice de research e relatórios em `experimentos-mcp/` | [`research/README.md`](research/README.md) |
| Corpus de exemplo | Markdown de instructions para testar o servidor localmente | [`fixtures/instructions/`](fixtures/instructions/) |
| Servidor MCP | Implementação read-only (stdio, três tools) | [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md) |

## Documentos de apoio (links diretos)

- [Política de camadas](copilot-comportamento/politica-camadas.md) · [Convenções de prompts](copilot-comportamento/convenções-prompts.md) · [Checklist novo repo](copilot-comportamento/checklist-novo-repo.md)
- [EPIC-01 — inventário e governança](planning/bmad/EPIC-01-inventory-governance.md) · [EPIC-02 — servidor MCP](planning/bmad/EPIC-02-mcp-server.md)
- [Template de experimento](research/experimentos-mcp/_template-experimento.md)

## Desenvolvimento do servidor MCP

Ver secção “Instalação” e “Corpus de exemplo” em [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md). No VS Code, testes pytest estão configurados em [`.vscode/settings.json`](.vscode/settings.json).
