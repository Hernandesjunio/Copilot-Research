# EPIC-08 — Stopwords PT first pass e rebaseline da suite de contexto

## Objetivo

Executar a primeira correcao incremental derivada do `EPIC-07`: tratar apenas `I-01` (stopwords portuguesas ausentes no scoring textual), reexecutar a suite de 24 testes de montagem de contexto e medir o delta antes de qualquer intervencao em `I-02+`.

**Resultado esperado**: `STOPWORDS` ampliado de forma conservadora, regressao zero na suite existente do servidor e novo baseline medido para decidir se `I-02` ainda precisa de correcao dedicada.

## Contexto do problema

O `EPIC-07` consolidou duas rodadas da suite `testes-basicos-montagem-contexto-mcp.md`:

- baseline inicial: `5/24`
- reexecucao real via MCP `stdio`: `7/24`

Nas duas leituras, `I-01` permaneceu como a causa-raiz mais provavel:

- queries tecnicas em portugues natural continuam puxando documentos fora do tema;
- o ruido aparece em multiplos dominios, o que sugere problema transversal de scoring;
- `I-02` e parte dos demais issues podem estar sendo amplificados por esse efeito.

Por isso, o proximo passo mais seguro nao e atacar varias hipoteses em paralelo, e sim **isolar a variavel principal**:

1. corrigir apenas `I-01`;
2. repetir testes automatizados;
3. repetir a suite de 24 casos;
4. medir o quanto do problema restante continua explicado por `I-02+`.

## Principio de implementacao

> **Uma unica variavel por vez.**
> Este epic altera apenas o conjunto de `STOPWORDS` e os testes associados a essa mudanca.
> Nao deve introduzir mudancas em `DEFAULT_SYNONYMS`, corpus, algoritmo de selecao ou contrato das tools.

Guardrails:

- nenhuma mudanca em `DEFAULT_SYNONYMS`;
- nenhuma mudanca em `context_resolver.py`;
- nenhuma mudanca em fixtures, salvo se descoberta alguma quebra objetiva que impeça a execucao da suite;
- toda evidencia de melhora deve vir de reexecucao da suite e nao apenas de inspeccao manual.

---

## Escopo

### Em escopo

- ampliar `STOPWORDS` em `mcp-instructions-server/corporate_instructions_mcp/indexing.py`;
- adicionar testes de falha/comportamento esperado para `I-01`;
- reexecutar `pytest -q`;
- reexecutar a suite de 24 testes via MCP `stdio`;
- registrar novo baseline e leitura comparativa contra `5/24` e `7/24`.

### Fora de escopo

- corrigir `I-02`, `I-04`, `I-05`, `I-06` ou `I-07`;
- alterar ranking por sinonimos;
- mexer em frontmatter do corpus;
- redesenhar o contrato das tools;
- mudar criterios de aprovacao da suite de 24 testes.

---

## Artefatos principais

### Codigo do servidor MCP

- `mcp-instructions-server/corporate_instructions_mcp/indexing.py` — `STOPWORDS`, `tokenize_query`, `score_record_breakdown`
- `mcp-instructions-server/corporate_instructions_mcp/server.py` — `search_instructions`, `resolve_instruction_context`

### Testes

- `mcp-instructions-server/tests/smoke_test.py`
- `mcp-instructions-server/tests/integration_mcp_stdio_test.py`
- novo teste focal para `I-01` no pacote de testes do servidor

### Evidencia e planejamento

- `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__execucao-real-e-analise-epic-07.md`

---

## Hipotese operacional

Se `STOPWORDS` passar a absorver conectivos PT de alta frequencia, entao:

- o body score de documentos irrelevantes deve cair;
- queries de arquitetura em portugues natural devem parar de privilegiar mensageria, observabilidade e docs meta por simples coincidencia lexical;
- parte dos fails de `T01`, `T03`, `T04`, `T12`, `T20` e `T21` deve melhorar sem qualquer tuning adicional.

Se isso nao acontecer, a leitura muda de:

- "`I-01` e causa-raiz dominante"

para:

- "`I-01` era apenas amplificador parcial, e `I-02`/`I-04` passam a ser os proximos candidatos operacionais".

---

## Roadmap sequencial

### Fase 0 — Congelar baseline e invariantes

Antes de editar:

- [ ] Confirmar `pytest -q` verde no estado atual.
- [ ] Registrar que o baseline operacional mais recente da suite de 24 testes e `7/24`.
- [ ] Fixar os casos mais sensiveis para leitura pos-correcao:
  - `T01`
  - `T03`
  - `T04`
  - `T12`
  - `T20`
  - `T21`

### Fase 1 — Testes de falha para `I-01`

Adicionar testes que reproduzam o problema antes da correcao:

- [ ] verificar que palavras como `como`, `deve`, `ser`, `que`, `me`, `quando`, `qual`, `quais` fazem parte de `STOPWORDS`;
- [ ] verificar que `"como deve ser"` nao gera body score positivo em documento de mensageria;
- [ ] verificar que uma query de arquitetura simples deixa de depender de conectivos para ranquear documentos.

### Fase 2 — Implementacao minima em `STOPWORDS`

Aplicar apenas ampliacao conservadora de stopwords PT em `indexing.py`.

Lista inicial candidata:

- [ ] `como`
- [ ] `deve`
- [ ] `ser`
- [ ] `que`
- [ ] `me`
- [ ] `mostre`
- [ ] `quando`
- [ ] `qual`
- [ ] `quais`
- [ ] `fazer`
- [ ] `usar`
- [ ] `implementar`
- [ ] `configurar`
- [ ] `retornar`
- [ ] `tratar`

Validacoes obrigatorias:

- [ ] nenhum desses tokens e chave essencial de sinonimo que precise permanecer ativa para discovery;
- [ ] a mudanca nao reduz casos explicitamente esperados em queries curtas do smoke.

### Fase 3 — Nao-regressao automatizada

Depois da mudanca:

- [ ] executar `pytest -q`;
- [ ] executar testes de smoke/integracao relevantes se houver qualquer sinal de regressao contextual;
- [ ] confirmar zero regressao em:
  - `test_search_instructions_finds_dns`
  - `test_search_persistencia_sql_returns_data_access`
  - `test_resolve_instruction_context_exposes_p1_evidence_fields`

### Fase 4 — Reexecucao da suite de 24 testes

Repetir o protocolo real via MCP `stdio`:

- [ ] `get_context_triggers`
- [ ] `resolve_instruction_context`
- [ ] `get_instructions_batch`
- [ ] `validate_applicability`

Medicoes obrigatorias:

- [ ] placar total atualizado da suite;
- [ ] comparativo `5/24` vs `7/24` vs pos-`I-01`;
- [ ] leitura por grupo de falhas remanescentes;
- [ ] verificacao explicita de ruido residual de `assistant-workflow-bmad-planning-and-controlled-inference` e `instruction-authoring-standard`.

### Fase 5 — Gate de decisao para o proximo passo

Com o novo baseline em maos:

- [ ] se o ganho for material, priorizar `I-02` apenas se o ruido meta-governance continuar relevante;
- [ ] se o ganho for pequeno, registrar que `I-01` era insuficiente sozinha e promover `I-02` a proximo alvo imediato;
- [ ] nao iniciar tuning de sinonimos sem esse gate documental.

---

## Critérios de aceite

- [ ] `STOPWORDS` inclui o conjunto PT aprovado para este first pass.
- [ ] o teste focal `"como deve ser"` confirma `score_body_blob == 0.0` para documento irrelevante.
- [ ] `pytest -q` passa sem regressao.
- [ ] a suite de 24 testes e reexecutada integralmente via MCP `stdio`.
- [ ] o novo baseline e documentado em relatorio proprio.
- [ ] o resultado pos-`I-01` nao fica abaixo de `7/24`.
- [ ] o epic termina com decisao explicita: "`I-02` ainda necessaria" ou "`I-01` insuficiente; escalar para proximo alvo".

## Novos testes obrigatorios

```python
# FALHA (deve falhar antes da correcao):
def test_FAIL_stopwords_pt_missing_como_deve_ser():
    from corporate_instructions_mcp.indexing import STOPWORDS
    missing = [w for w in ["como", "deve", "ser", "que", "me", "quando", "qual", "quais"] if w not in STOPWORDS]
    assert missing == [], f"Stopwords PT ausentes: {missing}"

def test_FAIL_common_pt_words_score_nonzero_in_unrelated_doc():
    from corporate_instructions_mcp.indexing import tokenize_query, expand_query_with_metadata, score_record_breakdown
    from corporate_instructions_mcp.server import _ensure_index
    idx, _ = _ensure_index()
    tokens = tokenize_query("como deve ser")
    info = expand_query_with_metadata(tokens)
    bd = score_record_breakdown(idx["microservice-messaging-rabbitmq-publish-consume"], tokens, None, info)
    assert bd.score_body_blob == 0.0

# COMPORTAMENTO ESPERADO:
def test_EXPECT_architecture_query_reduces_off_topic_noise():
    from corporate_instructions_mcp.server import resolve_instruction_context
    data = json.loads(resolve_instruction_context("me mostre como o projeto deve ser estruturado", max_results=7))
    top5 = data["selected_ids"][:5]
    assert "microservice-architecture-layering" in top5
    assert "microservice-clean-architecture-guardrails" in top5
```

## Criterios de leitura do rebaseline

Sinais de melhora forte:

- `T01` deixa de priorizar observabilidade/mensageria no topo;
- `T03` e `T04` reduzem contaminacao indireta;
- o numero total de aprovados sobe de forma clara sobre `7/24`.

Sinais de melhora parcial:

- o placar sobe pouco, mas o ruido transversal cai;
- `I-02` aparece de forma mais limpa como proximo gargalo.

Sinais de fracasso da hipotese:

- o placar nao melhora;
- os mesmos casos continuam desviando para topicos fora do tema;
- a contaminacao por meta-governance permanece praticamente identica.

---

## Referências

- `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__execucao-real-e-analise-epic-07.md`
- `mcp-instructions-server/corporate_instructions_mcp/indexing.py`
- `mcp-instructions-server/tests/smoke_test.py`
