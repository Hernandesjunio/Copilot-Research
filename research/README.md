# Research — metodologia, análises e experimentos

Esta área agrega **notas, análises e experimentos** que **não** constituem o corpus canônico servido pelo MCP. O objetivo documental é manter **rastreabilidade** entre pergunta de pesquisa, **desenho metodológico**, **artefatos brutos** (ensaíos, prompts) e **síntese crítica**, distinguindo o que é **evidência empírica** do que é **argumento arquitetural** ou **projeção de escala**.

Para o guia de produto/execução (BMAD) e critérios de aceite por épico, ver [`../planning/bmad/README.md`](../planning/bmad/README.md).

---

## 1. Visão geral

A linha de pesquisa investiga como **estender o GitHub Copilot** com um **MCP customizado** orientado a **recuperação de instruções normativas** (Markdown com frontmatter), reduzindo a necessidade de replicar grandes volumes de `.github/instructions` em cada repositório. O repositório combina:

- **Artefatos de engenharia** (servidor MCP em Python, transporte **STDIO**, tools read-only).
- **Arquitetura de informação** do corpus (classificação sempre-ativa vs on-demand; metadados para auditoria e busca).
- **Estudos documentais** (papel de custom instructions, prompt files e MCP segundo documentação consolidada nas análises).
- **Experimentação** registrada sob templates, incluindo **comparação com baseline** e **síntese** por modelo distinto dos ensaios quando aplicável.

---

## 2. Objetivo metodológico

Produzir conhecimento **acionável** e **auditável** sobre:

1. **Centralização e governança** de contexto estável (policies, padrões transversais) sem perder **previsibilidade** no fluxo de desenvolvimento assistido por IA.
2. **Trade-offs** entre instruções nativas, fixture/corpus e MCP (incluindo transporte, operação e superfície de manutenção).
3. **Critérios de decisão** para investimento incremental (por exemplo, lógica de MVP baseada em equivalência de resultados em um caso-base antes de expandir tools).

O repositório **não** alega neutralidade absoluta do pesquisador: onde houver **auditoria reflexiva** dos argumentos, ela aparece explicitamente nos relatórios de síntese.

---

## 3. Classificação da pesquisa (somente com base em evidências documentadas)

| Rótulo | Justificativa breve no repositório |
|--------|-------------------------------------|
| **Pesquisa aplicada** | Orienta decisões de arquitetura de uso do Copilot em organizações com muitos repositórios; entrega MVP e playbooks. |
| **Avaliação arquitetural** | Documentos comparativos STDIO/HTTP/híbrido; modelo de distribuição central com cache local. |
| **Prototipação de software** | Servidor MCP com tools de leitura e índice em memória; critérios de aceite em épicos. |
| **Estudo comparativo com controle** | Condições A/B/C com baseline sem corpus estruturado; variáveis de conteúdo e de sessão explicitadas nos artefatos do experimento 2026-04-12; extensão 2026-04-16 para vertical slice com duas sínteses (iterações) e rubrica compartilhada. |
| **Experimento empírico documentado** | Registros datados em `experimentos-mcp/` com setup, procedimento e anexos. |
| **Ciclo iterativo** | Análises e experimentos encadeiam achados, limitações e próximos passos; decisões de iteração aparecem em análises datadas. |

**Não classificar sem evidência adicional:** ensaio clínico randomizado, medição estatística amostral formal, ou validação em produção com telemetria — não constam como métodos concluídos nos artefatos principais consolidados aqui.

---

## 4. Metodologias utilizadas (inventário operacional)

### 4.1 Planejamento e governança de conteúdo (BMAD / EPICs)

- **EPIC-01 — Inventário e governança:** classificação **sempre-ativa** vs **on-demand**, hierarquia de conflito (nativas locais prevalecem), contrato de **frontmatter** (`id`, `title`, `tags`, `scope`, `priority`, `kind`).
- **EPIC-02 — MVP do servidor MCP:** `stdio`, tools de descoberta/busca/leitura em lote (`list_instructions_index`, `search_instructions`, `get_instructions_batch`), testes de fumaça.
- **EPIC-03 — Rollout multi-repo:** opções de distribuição do corpus (clone central, submodule, package, env), checklist de onboarding, piloto em poucos repositórios.
- **EPIC-04 — Protocolo de experimentos (E1–E5):** métricas propostas para qualidade percebida, invocação de tools, ruído de `max_results`, embeddings futuros e conflitos entre camadas.

### 4.2 Análises técnicas datadas (`research/analises/`)

**Índice com entrada por ficheiro e descrição breve:** [`analises/README.md`](analises/README.md). As linhas temáticas abaixo resumem a linha do tempo; detalhes e links estáveis estão no índice.

- **2026-04-07** — Template “thin” vs variante alternativa; inconsistências I1–I7 e decisão de **iterar** até uma fonte canónica.
- **2026-04-09** — Duas análises complementares: **estratégias MCP** (substituir/complementar `.github/instructions`) e **distribuição central + cache local + STDIO** (plano frio vs plano quente).
- **2026-04-11** — Auditoria técnica crítica da estratégia Copilot + MCP no âmbito deste repositório.
- **2026-04-12** — Tools versus prompts/resources no corpus `corporate-instructions` (substituibilidade 1:1, híbridos, roadmap).
- **2026-04-16** — **Pitch** curto e **defesa arquitetural** alinhados (MCP STDIO, tools, limites do estágio); ver entradas datadas no índice.

### 4.3 Experimentação (`research/experimentos-mcp/`)

- **Template padrão:** [`experimentos-mcp/_template-experimento.md`](experimentos-mcp/_template-experimento.md) padroniza data, setup (IDE, modelo, `INSTRUCTIONS_ROOT`, tools), procedimento, resultado e decisão.
- **Experimento 2026-04-05** — Avaliação do MCP em projeto **.NET 8** real; discussão de evolução de tools, comportamento agêntico e pressões de **janela de contexto**.
- **Experimento 2026-04-12** — Comparação **A/B/C** para planejamento de endpoint REST específico; **threads isoladas**; **corpus idêntico** entre A e B por configuração deliberada; síntese crítica com **matriz de critérios** e **limitações** explícitas (incluindo o que **não** foi testado empiricamente, como operação em 100+ repositórios reais). Rubrica operacional na raiz da pasta: [`experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md`](experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md).
- **Experimento 2026-04-16** — Mesmo desenho **A/B/C** aplicado a um **vertical slice** (`PUT`/`GET` `/clientes/{id}`): **plano + implementação + validação**; **duas sínteses** (`analise-comparativa-iteracao-1.md`, `analise-comparativa-iteracao-2.md`) com **reexecução isolada** do cenário MCP na segunda volta; registo em [`experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/notas.md`](experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/notas.md).

### 4.4 Papel de múltiplos modelos e decomposição de viés

Quando o registo assim declara, os **ensaios** e a **síntese** podem usar **modelos distintos** (funções epistémicas diferentes). Isso não substitui repetição estatística, mas documenta uma escolha metodológica de **separação entre produção bruta e consolidação**.

### 4.5 Explorações de longo prazo (`research/sugestoes-futura/`)

Materiais **não canónicos** e de maior volatilidade (por exemplo, desdobramentos BMAD ou context builder) — úteis para ideação, sem status de decisão ou de aceite do planejamento BMAD.

---

## 5. Metodologia por fases (fluxo típico no repositório)

1. **Caracterização do problema** — custos de replicação e drift; limites de instruções nativas volumosas.
2. **Fundamentação arquitetural** — comparação de transportes e padrões híbridos; papel de tools/resources/prompts.
3. **Definição de contratos** — frontmatter, política de conflito entre camadas, template “thin”.
4. **Implementação mínima** — MVP MCP read-only; corpus de fixtures para validação local.
5. **Experimento** — condições comparáveis, controles de sessão e de conteúdo; prompts e anexos versionados.
6. **Síntese e auditoria** — trade-offs, matriz de critérios, revisão explícita de argumentos, limitações e próximos passos.
7. **Extensão de escala** — playbooks e arquiteturas prescritivas; **medições adicionais** quando o protocolo E1–E5 for executado e arquivado com o mesmo rigor do template.

---

## 6. Critérios de avaliação (observados vs planejados)

### 6.1 Critérios já usados em sínteses comparativas (ex.: experimentos 2026-04-12 e 2026-04-16)

A definição operacional da rubrica (escalas, evidências, pesos sugeridos) está em [`experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md`](experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md). Os critérios incluem, entre outros: qualidade de **plano** (estrutura BMAD), **centralização**, **escalabilidade projetada**, **governança** (metadados e hash), **risco de drift**, **DX/fluidez**, **dependência de reprompt**, **previsibilidade**, **latência** no perfil STDIO, **maturidade do MVP**, **viabilidade corporativa** percebida, e **mecanismo de descoberta** (busca determinística vs navegação de arquivos).

### 6.2 Critérios planejados no protocolo E1–E5 (EPIC-04)

Incluem métricas como notas por dimensão, contagem aproximada de tokens em nativas, frequência de invocação de tools, sensibilidade a `max_results`, deteção de conflitos entre nativa e MCP em PRs piloto, e (futuro) comparação fulltext vs embeddings.

**Estado de evidência:** a existência do protocolo é documental; a **execução sistemática** de E1–E5 deve ser tratada como **hipótese de trabalho** até que sessões preenchidas e commits referenciados existam por cada ID.

---

## 7. Limitações (declaradas ou decorrentes dos desenhos)

- **Escopo “plano antes de código”** em experimentos específicos: equivalência observada entre mecanismos **não** implica automaticamente equivalência em **qualidade de código** ou em **refatoração multi-arquivo** sem novos desenhos.
- **Escala 100+ repositórios:** há argumentação e modelos operacionais; **teste empírico multi-repo** é explicitamente listado como pendência na síntese do experimento 2026-04-12.
- **Variabilidade de modelo e de IDE:** resultados podem variar com o cliente Copilot, versão da extensão e modelo; o repositório mitiga parcialmente com **controles de sessão** e **declaração de modelos**, mas não substitui bateria grande de repetições.
- **Corpus gerado por pipeline assistido:** reprodutibilidade do *prompt estruturado* não elimina decisões de curadoria humana (o próprio relatório de síntese admite decisões de framing).

---

## 8. Lacunas e próximos refinamentos metodológicos

1. **Formalizar e arquivar execuções E1–E5** com o template de sessão do EPIC-04, referenciando commits e hashes de versão do servidor quando métricas dependerem de defaults.
2. **Definir protocolo empírico multi-repo** (amostra de repositórios, tarefas padronizadas, janela temporal, critérios de sucesso observáveis).
3. **Operacionalizar avaliação de código gerado** (testes automatizados, revisão cega, ou rubrica de defeitos) e vincular ao mesmo template de experimento.
4. **Registo de variabilidade inter-modelo** no mesmo papel (por exemplo, repetir síntese com segundo modelo) quando a decisão depender de qualidade linguística frágil.
5. **Trilha explícita Spaces / prompt files** se esses mecanismos forem critérios de decisão independentes do MCP (hoje aparecem com força maior na camada de análise documental do que na camada empírica comparativa principal).

---

## 9. Índice de pastas e artefatos

| Caminho | Conteúdo |
|---------|----------|
| [`analises/README.md`](analises/README.md) | Índice das análises técnicas datadas (uma linha por ficheiro + descrição). |
| [`experimentos-mcp/`](experimentos-mcp/) | README de convenções, template, pastas ou arquivos por data com `notas.md` e anexos. |
| [`sugestoes-futura/`](sugestoes-futura/) | Explorações e notas de longo prazo (sem status de decisão formal). |

## 10. Como citar internamente

Para **análises técnicas** sob `analises/`, use o índice em [`analises/README.md`](analises/README.md) para identificar o ficheiro certo antes de citar `caminho + data`.

Prefira citar **caminho + data + revisão** quando existir no artefato (por exemplo, `experimentos-mcp/2026-04-12-…/artefatos/analise-comparativa.md`, revisão R1, e `experimentos-mcp/2026-04-12-…/criterios-de-comparacao.md` para a rubrica). Para o follow-up de vertical slice, cite `experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-1.md` ou `…-iteracao-2.md` conforme a síntese relevante. Para hipóteses brutas vs síntese, preserve a distinção de **papel** (ensaio vs consolidação) indicada em `notas.md` do experimento correspondente.
