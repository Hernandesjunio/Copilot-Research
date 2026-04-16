# Experimento: Análise comparativa — instructions locais vs MCP (STDIO) vs baseline

- **Data:** 2026-04-12
- **Autor:** —
- **Objetivo:** Avaliar criticamente três abordagens de contextualização para o planejamento do endpoint `PUT /api/v1/clientes/{id}` (A: instructions locais; B: MCP via STDIO; C: baseline sem corpus estruturado), com foco em centralização de conhecimento, escalabilidade e viabilidade corporativa.

## Artefatos (anexos)

| Artefato | Modelo | Descrição |
|---|---|---|
| [`criterios-de-comparacao.md`](criterios-de-comparacao.md) | — | Rubrica compartilhada (11 critérios, escala 0–10); mantida na **raiz** desta pasta para reutilização por experimentos relacionados. |
| [`artefatos/analise-comparativa.md`](artefatos/analise-comparativa.md) | Opus 4.6 | Análise consolidada completa (correções metodológicas, tabelas, limitações, recomendação arquitetural). |
| [`artefatos/hipoteses/hipotese1.md`](artefatos/hipoteses/hipotese1.md) | GPT 5.4 | Ensaio **A** — apenas `.github/copilot-instructions.md` e `.github/instructions/*`. |
| [`artefatos/hipoteses/hipotese2.md`](artefatos/hipoteses/hipotese2.md) | GPT 5.4 | Ensaio **B** — MCP como mecanismo principal de contexto. |
| [`artefatos/hipoteses/hipotese3.md`](artefatos/hipoteses/hipotese3.md) | GPT 5.4 | Ensaio **C** — baseline sem instructions nem MCP. |

## Setup

- **IDE / extensão Copilot:** pesquisa com assistentes no ecossistema Cursor / Copilot Chat / outras LLMs citadas nos artefatos.
- **Modelo:** hipóteses A/B/C geradas com **GPT 5.4**; análise comparativa final (síntese e crítica metodológica) com **Opus 4.6**. Execuções em threads separadas conforme [`artefatos/analise-comparativa.md`](artefatos/analise-comparativa.md).
- **`INSTRUCTIONS_ROOT` ou corpus usado:** `.github\instructions` no repositório do experimento, **deliberadamente** igual para A e B (controle de variável de conteúdo). Baseline C sem corpus estruturado.
- **Tools MCP invocadas (cenário B):** `search_instructions`, `list_instructions_index`, `get_instruction` (MVP com ~3 de ~13 tools planeadas).

## Procedimento

1. **Controle:** cada condição (A, B, C) em **thread separada, partindo do zero**, sem contaminação sequencial.
2. **Metodologia staged:** planejamento (BMAD / plano técnico) **antes** de codificação; escopo deste registro é **qualidade de plano**, não de código gerado.
3. **Tarefa:** planejar implementação de `PUT /api/v1/clientes/{id}` (substituição total) no mesmo codebase de referência (camadas Api/Dominio/Repositorio, Dapper, contratos OpenFinance, etc.).
4. Detalhes de prompts, instruções citadas e planos completos estão nas três hipóteses e na análise consolidada.

## Resultado

- **Entregável:** documento de análise comparativa + três registros de ensaio (hipóteses) com planos estruturados; ver [`artefatos/analise-comparativa.md`](artefatos/analise-comparativa.md).
- **O que funcionou bem:** A e B produziram planos de alta qualidade e equivalentes para o caso; B adiciona busca determinística via tools; C documentou lacunas do baseline como controle.
- **O que falhou ou gerou retrabalho:** baseline (C) exigiu reprompt e suposições; próxima etapa declarada nos artefatos é medir **código gerado** e tarefas mais complexas.

## Conclusões e próximos passos

- **Corpus / MCP:** equivalência A ≈ B em planejamento valida o MVP com 3 tools; investir nas tools restantes e em experimentos de geração de código e multi-repo.
- **Governança em escala:** recomendação híbrida — MCP STDIO como autoridade para padrões transversais; instructions locais só para contexto específico do repositório; `copilot-instructions.md` como entrypoint leve.
- **Decisão:** **iterar** — adotar direção MCP + corpus central para centralização; manter baseline apenas como referência metodológica; próximos ensaios conforme secção «O que fica para próximos experimentos» na análise consolidada.
