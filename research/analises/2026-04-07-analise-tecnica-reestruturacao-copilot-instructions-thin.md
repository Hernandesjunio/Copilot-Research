# Análise Técnica: Reestruturação de `copilot-instructions.thin.md` (Copilot Chat no Visual Studio)

## 1. Objetivo do documento

Este documento registra uma **revisão comparativa** entre o template mínimo versionado no repositório (`templates/copilot-instructions.thin.md`) e uma **recomendação de reestruturação** obtida via Copilot Chat no Visual Studio (detalhes da variante na secção 2). O objetivo é:

- explicitar **inconsistências** entre as duas variantes (placeholders, gatilhos MCP, orquestração, coerência com a matriz anexa ao rascunho, formatação e trade-off tokens versus orientação explícita ao modelo);
- consolidar **insights acionáveis** para alinhar estratégia de template fino, servidor MCP `corporate-instructions` e documentação do projeto;
- deixar claro **qual variante** deve ser tratada como canónica até decisão formal, evitando duas “fontes da verdade” sem README ou política que ligue o fluxo.

A análise **não** substitui decisão de produto: ela organiza evidências e trade-offs para fechar escolha entre **orquestração explícita no thin** (nomes de tools e passos) e **orquestração genérica** (delegação ao servidor e às descriptions das tools).

---

## 2. Contexto consolidado

O cenário considera **instruções nativas mínimas por repositório** (“thin”) combinadas com recuperação de contexto via **MCP** orientado a tools (`corporate-instructions`). O template fino funciona como camada sempre presente no prompt do Copilot; o MCP complementa com busca e obtenção de instruções governadas fora do repo do microsserviço.

Nesta revisão:

- **IDE / extensão:** Visual Studio com Copilot Chat;
- **Modelo utilizado na conversa:** não registado (opcional preencher);
- **Corpus de referência:** `templates/copilot-instructions.thin.md` no repositório; texto recomendado pelo Chat e matriz de análise estão **reproduzidos neste documento** (secções 2–5) para o comparativo;
- **Tools MCP:** não foram invocadas durante a redação da recomendação; o contexto conceitual é o servidor MCP `corporate-instructions` descrito no restante da pesquisa do repositório.

---

## 3. Artefatos e premissas

1. O arquivo **`templates/copilot-instructions.thin.md`** representa a política atual versionada no Git (lista explícita de passos com nomes de tools, placeholders em estilo parênteses, etc.).
2. A **variante recomendada pelo Copilot Chat** (corpo e matriz transcritos nas secções seguintes) agrega recomendação comprimida e uma **matriz** (dimensões: tokens, MCP, template, clareza, infra externa) que classifica pontos relativamente a uma “versão atual” no sentido da recomendação — não necessariamente alinhada ao `thin.md` do repo.
3. A premissa implícita da recomendação comprimida é **menos tokens no thin** e **maior peso** nas descriptions e no comportamento do servidor MCP.

---

## 4. Metodologia de comparativo

1. Obter do Copilot Chat uma proposta de reestruturação do ficheiro de instruções locais, com foco em tokens, MCP e reuso em muitos repositórios.
2. Confrontar o artefato recomendado (corpo e matriz neste documento) com `templates/copilot-instructions.thin.md`.
3. Validar coerência interna da matriz face ao estado real do repositório (qual ficheiro é canónico, o que a matriz chama de “versão atual”).

---

## 5. Achados: inconsistências entre repositório e recomendação

| #   | Tema                             | `copilot-instructions.thin.md` (repo)                                                                                  | Recomendação no rascunho                                                                                                | Nota                                                                                                                                                                                                 |
| --- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| I1  | Placeholders                     | `(descrição do projeto)` / `(stack completa)`                                                                          | `{{DESCRIÇÃO_DO_SERVIÇO}}` / `{{STACK}}`                                                                                | Dois estilos de template; o rascunho alinha com a matriz (3.2) e escala melhor em geradores.                                                                                                         |
| I2  | Gatilho MCP — escopo textual     | Lista explícita: arquitetura, convenções, **segurança**, resiliência, ADRs, **exemplos de domínio**, catálogo de erros | Lista mais curta: arquitetura, convenções, resiliência, ADRs, catálogo de erros (omite segurança e exemplos de domínio) | Pode ser compressão intencional; **risco**: modelo associar menos ao MCP em tópicos de segurança ou domínio se a intenção era manter paridade.                                                       |
| I3  | Orquestração MCP                 | Passos numerados com nomes de tools: `search_instructions`, `get_instructions_batch` (na época: `get_instruction`), `compose_context`                       | Frase genérica: “use as tools do MCP `corporate-instructions`”                                                          | A matriz do rascunho (2.3, 3.4–3.5) descreve esta versão genérica como desejável; **o arquivo thin do repo ainda está na variante explícita** — desalinhamento real, não só de redação.              |
| I4  | Coerência matriz vs. repositório | —                                                                                                                      | A matriz marca vários pontos como “✅ na versão atual” no sentido da recomendação comprimida                             | Quem lê só `thin.md` não vê essa “versão atual” da matriz; a documentação precisa deixar claro **qual** arquivo é a fonte da verdade (thin vs. instruções geradas por repo).                           |
| I5  | Placeholder e queries MCP        | Matriz 2.1: placeholders “impedem” queries até preenchimento                                                           | Recomendação continua usando `{{...}}`                                                                                  | A tensão não é placeholder vs. texto livre, e sim **vazio vs. preenchido**: a recomendação correta é “obrigatório preencher antes de usar”, não eliminar marcadores.                                 |
| I6  | Formatação do artefato           | Markdown estável                                                                                                       | No rascunho: `###Análise` sem espaço; bloco fenced mistura nome de ficheiro com conteúdo                                | Corrige-se na limpeza do rascunho se for promover a nota a documento oficial.                                                                                                                        |
| I7  | Contagem de linhas / “ótimo”     | 28 linhas (inclui 4 passos MCP)                                                                                        | ~22 linhas no corpo recomendado                                                                                         | Delta explicado pela lista explícita de tools; decisão de produto: tokens vs. orientação explícita ao modelo.                                                                                        |

---

## 6. O que sustenta a linha recomendada (pontos fortes)

- A matriz no rascunho organiza bem dimensões: tokens, MCP, template, clareza, infra externa.
- Destaque útil: **hierarquia “regras locais > MCP”** e **investimento em descriptions das tools no servidor** como alavanca quando o template fica genérico.
- Alertas de infra (índice vazio, descriptions pendentes) são acionáveis e independentes do texto do thin.

---

## 7. Riscos, tensões e retrabalho

- Dois “estados” do template (repo vs. recomendação) sem decisão explícita no Git: risco de PRs divergirem.
- A omissão de termos no gatilho MCP (I2) exige confirmação de intenção; não é óbvio só pela tabela.

---

## 8. Implicações para template, servidor MCP e documentação

### 8.1 Template (`copilot-instructions.thin.md`)

- Decidir adotar a **versão genérica MCP** (rascunho) ou **manter a lista de tools** no thin; se adotar genérico, atualizar `templates/copilot-instructions.thin.md` e o README que o referencia.
- **Padronizar placeholders** (`{{ }}` vs. parênteses) nos templates oficiais e documentar “preencher antes do commit” para alinhar a matriz 2.1 ao uso real (I5).
- Se “segurança” e “exemplos de domínio” saírem do primeiro parágrafo do MCP no thin comprimido, garantir o **mesmo peso semântico** doutro modo (regra fixa no topo, ou description da tool `search_instructions`, etc.).

### 8.2 Servidor MCP

- Plano de **descriptions ricas** nas tools; validar `compose_context` e demais nomes contra o pacote real em `mcp-instructions-server` (coerência com I3).

### 8.3 Documentação do repositório

- Uma linha no template ou no repositório de templates: “Marcadores obrigatórios: preencher Descrição e Stack antes de usar.”
- Até decisão formal, tratar a variante do Chat como **rascunho de trabalho** já consolidado nesta análise datada; evitar duas verdades sem README a indicar a **fonte atual do thin**.

### 8.4 Infra MCP (matriz 5.1–5.2 no rascunho)

- Prioridade alta desacoplada do texto: popular índice e enriquecer descriptions — compatível com template genérico.

---

## 9. Posicionamento: adotar, iterar ou descartar

**Iterar.** A recomendação do Chat é coerente com a estratégia “menos tokens + MCP como fonte de verdade das tools”, mas o repositório ainda reflete a estratégia anterior (passos explícitos). Fechar decisão e alinhar **um único ficheiro canónico** reduz inconsistências I3/I4.

---

## 10. Síntese final

1. **Explícito vs. genérico (MCP):** O thin atual maximiza **descoberta pelo texto** (nomes de tools e fluxo); a recomendação maximiza **manutenção em escala** e empurra detalhes para o servidor MCP. A escolha deve ser explícita: ou atualizar o thin para o estilo genérico **e** reforçar descriptions/listagem no servidor, ou manter passos explícitos no thin e aceitar tokens e edits em massa quando as tools mudarem.
2. **Placeholders:** Padronizar estilo e política de “obrigatoriamente preenchido antes de uso” alinha matriz e prática.
3. **Paridade semântica:** Não comprimir o gatilho MCP à custa de tópicos críticos sem compensação noutra camada.
4. **Rascunho vs. canónico:** Documentar qual artefato manda até a decisão ser aplicada no Git.

---

## 11. Fontes e referências internas ao repositório

1. `templates/copilot-instructions.thin.md` — template fino versionado.
2. Secções 2–5 deste documento — recomendação do Copilot Chat e matriz de análise usadas no comparativo.
3. `mcp-instructions-server/` — implementação real das tools (validação de nomes e fluxo).
4. Análise arquitetural relacionada (transporte, tools/resources/prompts): [`2026-04-09-analise-tecnica-mcp-copilot.md`](2026-04-09-analise-tecnica-mcp-copilot.md).
