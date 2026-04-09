# Copilot Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Repositório da iniciativa de **uso disciplinado do GitHub Copilot** com **instruções nativas mínimas**, **corpus servido via MCP** e registro de **prompts, respostas e experimentos** de pesquisa.

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Comece por aqui (navegação rápida)](#comece-por-aqui-navegação-rápida)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Documentos de apoio](#documentos-de-apoio-links-diretos)
- [Desenvolvimento do servidor MCP](#desenvolvimento-do-servidor-mcp)
- [Licença e autoria](#licença-e-autoria)

## Sobre o projeto

Este projeto organiza **governança**, **planejamento BMAD** (plano de execução entregue e épicos por tema) e **pesquisa aplicada** ao ecossistema Copilot: políticas de camadas (nativo versus MCP), templates reutilizáveis por repositório, prompts datados, respostas alinhadas e um servidor MCP read-only para servir um corpus de instruções de forma controlada.

**Objetivos principais**

- Reduzir instruções nativas ao essencial e mover contexto estável para MCP.
- Documentar decisões, experimentos e convenções de forma rastreável.
- Disponibilizar um servidor MCP de exemplo (`mcp-instructions-server`) com ferramentas read-only.

## Comece por aqui (navegação rápida)

Se você está chegando agora (ou quer se localizar rápido), siga este mapa. A ideia é sempre saber **o que será tratado** em cada área e para onde ir em seguida.

- **Como o Copilot deve se comportar (políticas/checklists)**: índice em [`copilot-comportamento/README.md`](copilot-comportamento/README.md).  
  Use quando estiver definindo “regras do jogo”: camadas (nativo vs MCP), precedência, como orquestrar MCP, e checklists de adoção.
- **Template mínimo para colar em cada repo de serviço (thin)**: [`templates/copilot-instructions.thin.md`](templates/copilot-instructions.thin.md).  
  Use quando for criar/adotar um repositório e precisar da camada nativa mínima.
- **Pesquisa aplicada e experimentos (não-canônico)**: índice em [`research/README.md`](research/README.md) e, para execuções, [`research/experimentos-mcp/README.md`](research/experimentos-mcp/README.md).  
  Use quando quiser ver “o que já foi testado”, setup, resultados e próximos passos.
- **Planejamento/roadmap (BMAD)**: índice em [`planning/bmad/README.md`](planning/bmad/README.md).  
  Use quando quiser entender critérios de aceite, épicos e o plano de execução do modelo híbrido.
- **Servidor MCP (como instalar/rodar e quais tools existem)**: [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md).  
  Use quando for configurar o MCP no IDE ou entender as tools disponíveis.

Leituras recomendadas (para contexto mais “arquitetural”):

- [`research/analises/2026-04-09-analise-tecnica-mcp-copilot.md`](research/analises/2026-04-09-analise-tecnica-mcp-copilot.md) — análise técnica comparativa (STDIO vs HTTP vs híbrido, tools/resources/prompts).

## Estrutura do repositório

| Área | Descrição | Documentos |
|------|-----------|------------|
| Governança local | Política de camadas (nativo vs MCP), checklists e convenções de chat | [`copilot-comportamento/README.md`](copilot-comportamento/README.md) |
| Template por repo | Instruções “finas” para colar em cada repositório de aplicação | [`templates/copilot-instructions.thin.md`](templates/copilot-instructions.thin.md) |
| Planejamento BMAD | Índice, [plano de execução](planning/bmad/execucao/plano-execucao-bmad.md) e [épicos](planning/bmad/epicos/) (inventário, servidor MCP, rollout, experimentos) | [`planning/bmad/README.md`](planning/bmad/README.md) |
| Perguntas de pesquisa | Prompts datados usados para explorar temas (MCP, agente, arquitetura) | [`prompts/`](prompts/) |
| Respostas | Respostas alinhadas a cada prompt em `prompts/` | [`responses/`](responses/) |
| Pesquisa e experimentos | Índice de research e relatórios em `experimentos-mcp/` | [`research/README.md`](research/README.md) |
| Corpus de exemplo | Markdown de instruções para testar o servidor localmente | [`fixtures/instructions/`](fixtures/instructions/) |
| Servidor MCP | Implementação read-only (stdio, três tools) | [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md) |

## Documentos de apoio (links diretos)

- [Política de camadas](copilot-comportamento/politica-camadas.md) · [Convenções de prompts](copilot-comportamento/convenções-prompts.md) · [Checklist novo repo](copilot-comportamento/checklist-novo-repo.md)
- [Plano de execução BMAD (modelo híbrido nativas + MCP)](planning/bmad/execucao/plano-execucao-bmad.md)
- [EPIC-01 — inventário e governança](planning/bmad/epicos/EPIC-01-inventory-governance.md) · [EPIC-02 — servidor MCP](planning/bmad/epicos/EPIC-02-mcp-server.md)
- [Template de experimento](research/experimentos-mcp/_template-experimento.md)

## Desenvolvimento do servidor MCP

Consulte as seções **Instalação** e **Corpus de exemplo** em [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md). No VS Code, os testes pytest estão configurados em [`.vscode/settings.json`](.vscode/settings.json).

## Licença e autoria

O código e a documentação neste repositório são disponibilizados sob a [**licença MIT**](LICENSE): pode **usar**, **modificar** e **distribuir** o material, inclusive em projetos comerciais, desde que **mantenha o aviso de copyright e o texto da licença** nas cópias ou trabalhos derivados — o que preserva a **referência à autoria** original.

**Copyright © 2026 [Hernandes Junio de Assis](https://github.com/Hernandesjunio).** Os direitos autorais permanecem com o autor; a licença MIT não transfere a titularidade, apenas concede as permissões acima nas condições indicadas.
