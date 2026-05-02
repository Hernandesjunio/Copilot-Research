# Prompt — síntese comparativa pós-execução (A/B/C)

## Proveniência

No experimento [`2026-04-16-analise-comparativa-instructions-mcp-vertical-slice`](../2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/), **não foi encontrado** um ficheiro de prompt versionado para gerar `analise-comparativa-iteracao-*.md`. As sínteses estão atribuídas no frontmatter a **Opus 4.6 (Cursor Agent)**; os ficheiros em `Prompts/` desse ensaio servem à **execução** dos cenários (MCP, instructions locais, baseline), não à meta-análise.

Este documento **reconstrói** o protocolo a partir da estrutura de [`analise-comparativa-iteracao-3.md`](../2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-3.md) para permitir reprodutibilidade em novos experimentos.

---

## Como usar

1. Preencha os placeholders `{{...}}` na secção **Prompt (copiar para o agente)** abaixo (ou injete como mensagem de sistema + anexos).
2. Anexe ou indique caminhos para: a **rubrica**, os **três relatórios** por cenário (ex.: `hipotese1.md` … `hipotese3.md`), e opcionalmente a **análise anterior** para deltas entre iterações.
3. Peça saída em Markdown com frontmatter YAML no topo, tal como no exemplo de referência.

**Rubrica de referência** (11 critérios, escala 0–10): normalmente [`2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md`](../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md).

---

## Prompt (copiar para o agente)

Atua como **avaliador técnico independente**: rigoroso, baseado em evidências dos artefatos fornecidos, sem inventar execuções que não estejam documentadas.

### Entradas obrigatórias

- **Rubrica:** `{{CAMINHO_OU_RESUMO_RUBRICA}}` — aplica os **11 critérios** na escala **0–10** definida nesse documento (incluindo regra de **critério 8 invertido** — maior nota = pior risco de drift — e fórmulas de agregação se estiverem definidas).
- **Experimento:** nome `{{NOME_EXPERIMENTO}}`, data `{{DATA}}`, escopo da tarefa canónica `{{ESCOPO_TAREFA}}`.
- **Modelo que executou os cenários:** `{{MODELO_EXECUCAO}}`.
- **Modelo que produz esta síntese (opcional):** `{{MODELO_ANALISE}}`.

**Cenários (ajustar rótulos e caminhos conforme o desenho experimental):**

| Cenário | Artefato (relatório pós-execução) | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|
| **A** — `{{ROTULO_A}}` | `{{ARTEFATO_A}}` | `{{INSTR_A}}` | `{{FONTE_A}}` |
| **B** — `{{ROTULO_B}}` | `{{ARTEFATO_B}}` | `{{INSTR_B}}` | `{{FONTE_B}}` |
| **C** — `{{ROTULO_C}}` | `{{ARTEFATO_C}}` | `{{INSTR_C}}` | `{{FONTE_C}}` |

**Iteração (se aplicável):** número `{{ITERACAO}}`; comparar com `{{ANALISE_ANTERIOR_PATH}}` para colunas **Δ** e secção “diferença-chave”. Se for a primeira síntese, omitir deltas iterativos ou marcar N/A.

**Ajustes desta volta (lista):** `{{LISTA_AJUSTES_METODOLOGICOS_OU_TOOLS}}`

### Tarefa

1. Lê os **três artefatos** de cenário e extrai apenas **métricas e afirmações que constem no texto** (incluindo `EXPERIMENT_METRICS_JSON`, `DECISIONS_JSON`, contagens de tools, FATO/HIPÓTESE/RISCO quando existirem).
2. Para **cada um dos 11 critérios** da rubrica, atribui uma **nota 0–10 por cenário** e uma **justificativa** ancorada em evidências citadas (IDs de instructions, ficheiros, números de tool calls, etc.).
3. Quando houver análise anterior, calcula **Δ** por critério e síntese qualitativa da evolução (o que fechou gaps, o que permanece).
4. Produz o documento na **estrutura obrigatória** abaixo.

### Regras

- Não confundir **prompt de execução** com **esta síntese**; não uses como evidência o que não apareça nos relatórios anexos.
- Para o critério **drift** (invertido), na **média simples** usa `(10 − nota)` apenas para esse critério, **se** a rubrica assim o definir.
- **Agregação:** inclui **média simples** dos 11 critérios (com normalização do drift conforme rubrica) **e**, se a rubrica definir pesos, **média ponderada** com tabela de contribuições por critério.
- Inclui **quadro consolidado** (todos os critérios × cenários) e **métricas auxiliares** (tool calls, reprompts, duração, FATOs vs HIPÓTESE+RISCO, etc.) **só com dados presentes** nos artefatos; caso falte um dado, `N/A` e nota de método.
- Fecha com **limitações do experimento**, **conclusão** (veredicto por objetivo se fizer sentido), **principal evidência**, **principal limitação**, **próximos passos sugeridos**.

### Estrutura obrigatória do Markdown de saída

O ficheiro deve começar por **frontmatter YAML** com, no mínimo:

```yaml
titulo: "{{TITULO_ANALISE}}"
data: "{{DATA}}"
modelo_analise: "{{MODELO_ANALISE}}"
modelo_execucao: "{{MODELO_EXECUCAO}}"
rubrica: "{{CAMINHO_RUBRICA}}"
escopo: "{{ESCOPO_TAREFA}}"
iteracao: {{ITERACAO}}
delta_vs: "{{ANALISE_ANTERIOR_PATH_OU_VAZIO}}"
ajustes_aplicados:
  - "{{ITEM}}"
```

Seguido de corpo com secções **nesta ordem** (adaptar títulos se a rubrica usar outros nomes, mantendo a ordem lógica):

1. Título H1 alinhado ao `titulo` do frontmatter.
2. Bloco curto **Contexto** (o que mudou nesta iteração vs anteriores, em 1–3 parágrafos).
3. **Identificação dos cenários** (tabela A/B/C).
4. **Diferença-chave desta iteração** (vs anterior), se aplicável; senão omitir ou uma linha “primeira síntese”.
5. **Avaliação por critério (0–10)** — para cada critério 1…11:
   - subtítulo `### N) Nome do critério`
   - tabela `| Cenário | Nota | Δ | Justificativa |` (Δ opcional)
   - subsecções **Evidências** e **Evolução** quando útil.
6. **Quadro consolidado** (matriz critérios × cenários; incluir colunas de referência anterior se fizer sentido).
7. **Agregação** — Opção média simples; Opção média ponderada (explicitar pesos da rubrica).
8. **Métricas auxiliares** (tabela única; observações numeradas se houver contradições aparentes nos números).
9. **Evolução do gap** entre abordagens (ex.: qualidade 1–4 vs estrutural 5–8), se a rubrica o suportar.
10. **Evolução ao longo das iterações** (tabela critério × v1/v2/…), apenas se existirem múltiplas sínteses.
11. **Validação das metas pendentes** (metas explícitas de iterações anteriores, se houver).
12. **Observações cruzadas** (onde A supera B, empates, lideranças).
13. **Limitações do experimento**.
14. **Conclusão** — veredicto/recomendação, evidência principal, limitação principal, próximos passos.

### Saída

Entrega **apenas** o Markdown completo (frontmatter + corpo), pronto a gravar como `analise-comparativa-iteracao-{{ITERACAO}}.md` na pasta do experimento.

---

## Relação com outros templates

- **Execução** dos ensaios (ticket + BMAD + relatório por cenário): [`../templates/prompt-experimento-comparativo.md`](../templates/prompt-experimento-comparativo.md).
- **Síntese** (este ficheiro): aplica-se **depois** de existirem os três relatórios por cenário.
