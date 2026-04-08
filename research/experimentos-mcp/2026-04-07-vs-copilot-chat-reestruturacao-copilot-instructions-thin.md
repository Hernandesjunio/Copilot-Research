# Experimento: Reestruturação de `copilot-instructions.thin.md` (Copilot Chat no Visual Studio)

- **Data:** 2026-04-07
- **Autor:** (a preencher)
- **Objetivo:** Comparar o template atual do repositório com a recomendação obtida no VS (Copilot Chat), identificar inconsistências e registrar insights acionáveis para o projeto.

## Setup

- IDE / extensão Copilot: Visual Studio + Copilot Chat
- Modelo (se souber): (a preencher)
- `INSTRUCTIONS_ROOT` ou corpus usado: `templates/copilot-instructions.thin.md` (referência); rascunho em `research/rascunho.md`
- Tools MCP invocadas (ex.: `search_instructions`, `get_instruction`): não aplicável ao experimento de redação do template; contexto: MCP `corporate-instructions`

## Procedimento

1. Solicitar ou obter recomendação de reestruturação do arquivo de instruções locais (camada mínima), com foco em tokens, MCP e reuso em muitos repositórios.
2. Confrontar o artefato recomendado (bloco em `research/rascunho.md`) com `templates/copilot-instructions.thin.md`.
3. Validar coerência interna da matriz de análise anexa ao rascunho versus o estado do repositório.

## Resultado

### Entregável

- Notas estruturadas abaixo (inconsistências + insights). O texto fonte da recomendação permanece em `research/rascunho.md`.

### Inconsistências identificadas

| # | Tema | `copilot-instructions.thin.md` (repo) | Recomendação no rascunho | Nota |
|---|------|----------------------------------------|---------------------------|------|
| I1 | Placeholders | `(descrição do projeto)` / `(stack completa)` | `{{DESCRIÇÃO_DO_SERVIÇO}}` / `{{STACK}}` | Dois estilos de template; o rascunho alinha com a matriz (3.2) e escala melhor em geradores. |
| I2 | Gatilho MCP — escopo textual | Lista explícita: arquitetura, convenções, **segurança**, resiliência, ADRs, **exemplos de domínio**, catálogo de erros | Lista mais curta: arquitetura, convenções, resiliência, ADRs, catálogo de erros (omite segurança e exemplos de domínio) | Pode ser compressão intencional; **risco**: modelo associar menos ao MCP em tópicos de segurança ou domínio se a intenção era manter paridade. |
| I3 | Orquestração MCP | Passos numerados com nomes de tools: `search_instructions`, `get_instruction`, `compose_context` | Frase genérica: “use as tools do MCP `corporate-instructions`” | A matriz do rascunho (2.3, 3.4–3.5) descreve esta versão genérica como desejável; **o arquivo thin do repo ainda está na variante explícita** — desalinhamento real, não só de redação. |
| I4 | Coerência matriz vs. repositório | — | A matriz marca vários pontos como “✅ na versão atual” no sentido da recomendação comprimida | Quem lê só `thin.md` não vê essa “versão atual” da matriz; a documentação do experimento precisa deixar claro **qual** arquivo é a fonte da verdade (thin vs. copilot-instructions gerado por repo). |
| I5 | Placeholder e queries MCP | Matriz 2.1: placeholders “impedem” queries até preenchimento | Recomendação continua usando `{{...}}` | A tensão não é placeholder vs. texto livre, e sim **vazio vs. preenchido**: a recomendação correta é “obrigatório preencher antes de usar”, não eliminar marcadores. |
| I6 | Formatação do artefato | Markdown estável | No rascunho: `###Análise` sem espaço; bloco fenced mistura nome de ficheiro com conteúdo | Corrige-se na limpeza do rascunho se for promover a nota a documento oficial. |
| I7 | Contagem de linhas / “ótimo” | 28 linhas (inclui 4 passos MCP) | ~22 linhas no corpo recomendado | Delta explicado pela lista explícita de tools; decisão de produto: tokens vs. orientação explícita ao modelo. |

### O que funcionou bem (no experimento)

- A matriz no rascunho organiza bem dimensões: tokens, MCP, template, clareza, infra externa.
- Destaque útil: **hierarquia “regras locais > MCP”** e **investimento em descriptions das tools no servidor** como alavanca quando o template fica genérico.
- Alertas de infra (índice vazio, descriptions pendentes) são acionáveis e independentes do texto do thin.

### O que falhou ou gerou retrabalho

- Dois “estados” do template (repo vs. recomendação) sem decisão explícita no Git: risco de PRs divergirem.
- A omissão de termos no gatilho MCP (I2) exige confirmação de intenção; não é óbvio só pela tabela.

## Conclusões e próximos passos

### Insights para o projeto

1. **Explícito vs. genérico (MCP):** O thin atual maximiza **descoberta pelo texto** (nomes de tools e fluxo); a recomendação maximiza **manutenção em escala** e empurra detalhes para o MCP server. Escolha explícita: ou atualizar o thin para o estilo genérico **e** reforçar descriptions/listagem no servidor, ou manter passos explícitos no thin e aceitar tokens + edits em massa se as tools mudarem.
2. **Placeholders:** Padronizar um estilo (`{{ }}` vs. parênteses) nos templates oficiais e documentar “preencher antes do commit” alinha matriz 2.1 com o uso real.
3. **Paridade semântica:** Se “segurança” e “exemplos de domínio” saírem do primeiro parágrafo do MCP, garantir o mesmo peso noutro sítio (ex.: regra fixa no topo, ou description da tool `search_instructions`).
4. **Rascunho vs. canonical:** Tratar `research/rascunho.md` como notas até ser incorporado a um experimento datado ou ao README/templates; evitar duas “verdades” sem README linkando “fonte atual do thin”.
5. **Infra MCP (5.1–5.2):** Prioridade alta desacoplada do texto: popular índice e enriquecer descriptions — compatível com template genérico.

### Alterações propostas ao corpus / template / servidor

- **Template:** Decidir adotar versão genérica MCP (rascunho) ou manter lista de tools no `thin.md`; se adotar genérico, atualizar `templates/copilot-instructions.thin.md` e o README que o referencia.
- **Servidor MCP:** Plano de descriptions ricas nas tools; validar `compose_context` e demais nomes contra o pacote real em `mcp-instructions-server`.
- **Documentação:** Uma linha no template ou no repositório de templates: “Marcadores obrigatórios: preencher Descrição e Stack antes de usar.”

### Decisão: adotar / iterar / descartar (e porquê)

- **Iterar:** A recomendação do Chat é coerente com a estratégia “menos tokens + MCP como fonte de verdade das tools”, mas o repositório ainda reflete a estratégia anterior (passos explícitos). Fechar decisão e alinhar um único arquivo canónico evita inconsistência I3/I4.
