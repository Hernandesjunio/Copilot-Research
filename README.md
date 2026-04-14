# Copilot Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Apresentação

[![Assista à apresentação do projeto](https://img.youtube.com/vi/abE2CV6SE98/maxresdefault.jpg)](https://youtu.be/abE2CV6SE98)

Repositório de **pesquisa aplicada** sobre extensão do **GitHub Copilot** via **Model Context Protocol (MCP)** customizado, com foco em **centralização de contexto**, **governança de corpus** e **redução de duplicação** de `.github/instructions` em cenários com **muitos repositórios**.

## Problema e objetivo

Arquivos em `.github/instructions` e instruções nativas ajudam o contexto **local**, mas tendem a **escalar mal** quando o mesmo conhecimento precisa existir em dezenas ou centenas de repositórios: **duplicação**, **drift**, custo de manutenção e ausência de **fonte única de verdade**. Este repositório documenta uma linha de trabalho que combina **instruções nativas mínimas (“thin”)**, um **corpus normativo** e um **servidor MCP read-only em STDIO** para recuperação sob demanda, além de **experimentos** e **análises** rastreáveis.

## Research Methodology

Esta iniciativa combina métodos complementares (detalhamento metodológico, critérios, limitações e rastreabilidade de artefatos em [`research/README.md`](research/README.md)):

- **Planejamento orientado a épicos (BMAD)** — decompõe inventário, MVP do servidor MCP, rollout multi-repo e protocolos de experimentação com critérios de aceite.
- **Análise arquitetural comparativa** — confronta transportes e modos de exposição MCP (STDIO, HTTP, híbrido; tools, resources, prompts) com trade-offs explícitos.
- **Prototipação de MVP** — implementa MCP `stdio` com conjunto inicial de tools de leitura/indexação sobre `INSTRUCTIONS_ROOT`.
- **Experimentação comparativa com baseline** — registra condições paralelas (instruções locais, MCP, ausência de corpus estruturado) com controles explícitos de contaminação e de conteúdo.
- **Encadeamento em fases (staged)** — separa evidência sobre **planejamento** de evidência futura sobre **código gerado**, evitando extrapolação fora do escopo medido.
- **Consolidação crítica e limitações declaradas** — documenta o que foi provado, o que é projeção arquitetural e quais medições ainda faltam.

## Onde está cada coisa

| Área | Caminho |
|------|---------|
| Políticas de uso do Copilot (camadas, checklists) | [`copilot-comportamento/README.md`](copilot-comportamento/README.md) |
| Template de instruções nativas mínimas | [`templates/copilot-instructions.thin.md`](templates/copilot-instructions.thin.md) |
| **Metodologia, análises e experimentos** | [`research/README.md`](research/README.md) |
| Registro de experimentos MCP | [`research/experimentos-mcp/README.md`](research/experimentos-mcp/README.md) |
| Planejamento BMAD (execução + épicos) | [`planning/bmad/README.md`](planning/bmad/README.md) |
| Perguntas de pesquisa (prompts datados) | [`prompts/`](prompts/) |
| Respostas alinhadas aos prompts | [`responses/`](responses/) |
| Servidor MCP (instalação, tools) | [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md) |
| Corpus de exemplo | [`fixtures/instructions/`](fixtures/instructions/) |

Leitura complementar (visão arquitetural MCP × Copilot): [`research/analises/2026-04-09-analise-tecnica-mcp-copilot.md`](research/analises/2026-04-09-analise-tecnica-mcp-copilot.md).

## Desenvolvimento do servidor MCP

Instalação, configuração no IDE e smoke tests: [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md). Configuração de testes no workspace: [`.vscode/settings.json`](.vscode/settings.json).

## Segurança

Reporte de vulnerabilidades e modelo de ameaça (incluindo o servidor MCP): [SECURITY.md](SECURITY.md).

## Licença e autoria

O código e a documentação neste repositório são disponibilizados sob a [**licença MIT**](LICENSE): pode **usar**, **modificar** e **distribuir** o material, inclusive em projetos comerciais, desde que **mantenha o aviso de copyright e o texto da licença** nas cópias ou trabalhos derivados — o que preserva a **referência à autoria** original.

**Copyright © 2026 [Hernandes Junio de Assis](https://github.com/Hernandesjunio).** Os direitos autorais permanecem com o autor; a licença MIT não transfere a titularidade, apenas concede as permissões acima nas condições indicadas.
