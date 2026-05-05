# EPIC-08 — Rebaseline da suite de contexto apos first pass de stopwords PT (I-01)

## Escopo executado

- Hipotese controlada: atuar apenas em `I-01` (stopwords PT).
- Guardrails respeitados:
  - sem mudancas em `DEFAULT_SYNONYMS`;
  - sem mudancas em `context_resolver.py`;
  - sem mudancas em ranking, corpus, frontmatter e contratos de tools.
- Mudancas realizadas:
  - `mcp-instructions-server/corporate_instructions_mcp/indexing.py`:
    - adicao de `validar` em `STOPWORDS`;
  - `mcp-instructions-server/tests/test_epic07_search_ranking.py`:
    - novo teste focal de `I-01` para confirmar filtragem de `validar`.

## Fase 0 — baseline real antes da alteracao

### Testes do servidor (`pytest -q`)

- Resultado: `145 passed, 1 skipped`.

### Suite de 24 casos via MCP `stdio`

- Resultado: `7/24`.
- Aprovados:
  - `T05`, `T14`, `T15`, `T17`, `T22`, `T23`, `T24`.
- Reprovados:
  - `T01`, `T02`, `T03`, `T04`, `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`, `T16`, `T18`, `T19`, `T20`, `T21`.

## Classificacao de falhas (estado pre-alteracao)

### Falhas diretamente atribuidas a `I-01`

- `T19`
  - Evidencia operacional: ao ampliar stopwords PT com verbo generico de consulta (`validar`), `T19` deixou de falhar sem qualquer mudanca fora de `STOPWORDS`.

### Falhas potencialmente amplificadas por `I-01` (mas nao resolvidas so com first pass)

- `T01`, `T03`, `T04`, `T12`, `T20`, `T21`.
  - Padrao observado: queries em PT natural ainda geram mistura transversal e lacunas de supporting IDs, mesmo apos reduzir ruido lexical obvio.

### Falhas claramente em `I-02+` (fora de escopo deste epic)

- `T02`, `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T13`, `T16`, `T18`.
  - Padrao dominante: lacunas de conectividade semantica, contaminacao por documentos meta-governance ou ausencia de supporting IDs esperados por design do ranking/sinonimos.

## Fase 1/2 — implementacao minima de `I-01`

- Alteracao aplicada apenas em `STOPWORDS`:
  - token adicionado: `validar`.
- Teste focal adicionado:
  - confirma que `validar` esta em `STOPWORDS`;
  - confirma `score_body_blob == 0.0` em documento irrelevante para query curta de conectivos/verbos comuns.

## Fase 3 — nao-regressao automatizada apos alteracao

- `pytest -q`: `146 passed, 1 skipped`.
- Regressao observada: nenhuma.

## Fase 4 — reexecucao da suite de 24 casos via MCP `stdio`

- Resultado pos-`I-01`: `8/24`.
- Delta vs baseline:
  - baseline historico inicial: `5/24`;
  - baseline operacional anterior: `7/24`;
  - baseline atual pos-`I-01`: `8/24`.
- Novo caso aprovado:
  - `T19` (antes fail, agora pass).
- Casos que permanecem reprovados:
  - `T01`, `T02`, `T03`, `T04`, `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`, `T16`, `T18`, `T20`, `T21`.

## Gate de decisao (EPIC-08)

- Decisao: `I-01` foi parcialmente util, mas insuficiente para mudar materialmente a suite.
- Proximo alvo recomendado: `I-02` (ruido meta-governance e contaminacao estrutural de ranking/sinonimos).

