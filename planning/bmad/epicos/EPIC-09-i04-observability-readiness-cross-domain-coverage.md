# EPIC-09 - I-04 observability/readiness cross-domain coverage (controlled pass)

## Objetivo

Executar a proxima iteracao controlada apos EPIC-08 e mitigacao de I-02, atacando apenas `I-04`: lacunas de cobertura semantica entre observabilidade, readiness/configuracao e consultas tecnicas adjacentes (integracao, SQL, seguranca, erro de API).

**Resultado esperado**: reduzir falhas atribuidas a `I-04` na suite de 24 casos, mantendo zero regressao no servidor e sem tuning generico fora do escopo.

## Contexto consolidado

Estado confirmado antes deste epic:

- `pytest -q`: `149 passed, 1 skipped`
- suite 24 casos via MCP stdio: `8/24`
- baseline anterior (pos-EPIC-08): `8/24`
- `I-02` foi mitigado em cenarios focais (meta/governance deixou de dominar topo em casos criticos), mas o placar agregado nao subiu.

Leitura atual das falhas:

- falhas com predominio de `I-04`: `T06`, `T07`, `T08`, `T11`, `T16`, `T18`, `T20`, `T21`
- falhas com resíduo de `I-01`: `T01`, `T02`, `T12`
- falhas inconclusivas/parcialmente fora do foco principal: `T03`, `T04`, `T09`, `T10`, `T13`

Hipotese operacional:

- o maior gargalo atual nao e mais ruído meta-governance no topo;
- o principal bloqueio e conectividade semantica insuficiente entre dominios tecnicos que deveriam co-aparecer (ex.: observabilidade + data access; SQL + readiness; auth + error catalog; segredos + readiness).

## Principio de implementacao

> Uma variavel por vez.
> Este epic altera somente a cobertura semantica de `I-04`, priorizando ajustes minimos e verificaveis.

Guardrails:

- nao alterar `STOPWORDS` (exceto bug objetivo comprovado);
- nao alterar contratos publicos das tools;
- nao alterar corpus/frontmatter;
- nao alterar criterios da suite de 24;
- nao fazer tuning amplo de sinonimos sem ligacao direta com casos falhos de `I-04`;
- nao reescrever algoritmo de ranking.

---

## Escopo

### Em escopo

- ajustes pontuais em `DEFAULT_SYNONYMS` em `mcp-instructions-server/corporate_instructions_mcp/indexing.py`, estritamente ligados aos casos falhos de `I-04`;
- novos testes de falha e comportamento esperado para `I-04`;
- reexecucao de `pytest -q`;
- reexecucao da suite de 24 casos via MCP stdio;
- rebaseline comparativo (`7/24` -> `8/24` -> pos-`I-04`).

### Fora de escopo

- voltar a mexer em `I-01` ou `I-02` sem evidencia nova;
- tuning generico em clusters nao relacionados aos casos alvo;
- alteracoes de `context_resolver.py` fora de bugs diretamente ligados ao escopo;
- alteracoes estruturais de scoring/ranking.

---

## Artefatos principais

### Codigo

- `mcp-instructions-server/corporate_instructions_mcp/indexing.py` (`DEFAULT_SYNONYMS`, expansao de termos)

### Testes

- novo arquivo focal: `mcp-instructions-server/tests/test_epic09_i04_cross_domain_coverage.py`
- regressao obrigatoria:
  - `mcp-instructions-server/tests/test_epic09_i02_meta_governance.py`
  - `mcp-instructions-server/tests/smoke_test.py`
  - `mcp-instructions-server/tests/integration_mcp_stdio_test.py`

### Evidencias

- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__rebaseline-epic-08-i01-stopwords.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__epic-09-i02__analise-falhas-e-correcao-targeted.md`

---

## Casos alvo de I-04

Prioridade P1:

- `T06` tracing/correlation entre API e chamadas externas
- `T08` metricas/spans para HTTP + banco
- `T20` segredos/logging com readiness de producao
- `T21` SQL seguro com timeout/transacao e readiness

Prioridade P2:

- `T07` health live/ready com supporting de DI
- `T11` retry/circuit breaker com supporting de observabilidade
- `T16` ProblemDetails com error catalog
- `T18` JWT/auth com supporting de error catalog

---

## Roadmap sequencial

### Fase 0 - congelar baseline

Antes de editar:

- [ ] confirmar `pytest -q` verde;
- [ ] confirmar baseline da suite em `8/24`;
- [ ] registrar lista de falhas alvo de `I-04`: `T06`, `T07`, `T08`, `T11`, `T16`, `T18`, `T20`, `T21`.

### Fase 1 - testes de falha (antes da correcao)

Criar testes que falhem no estado atual, com evidencia explicita do gap:

- [ ] query tecnica de tracing/integracao nao pode perder `microservice-opentelemetry-correlation-and-health`;
- [ ] query de metricas/spans + banco deve incluir `microservice-data-access-and-sql-security`;
- [ ] query SQL segura com timeout/transacao deve incluir `microservice-configuration-production-readiness`;
- [ ] query de segredos/logs deve incluir `microservice-configuration-production-readiness`;
- [ ] query ProblemDetails deve incluir `microservice-api-error-catalog-baseline` no bundle;
- [ ] query JWT baseline deve incluir `microservice-api-error-catalog-baseline` como supporting.

### Fase 2 - implementacao minima em sinonimos (I-04)

Aplicar apenas ajustes pontuais, orientados por testes de falha:

- [ ] adicionar/ajustar chaves de sinonimos para aproximar observabilidade de tracing/metricas/dependencias;
- [ ] reforcar ponte SQL/transacao/timeout para readiness/configuracao;
- [ ] reforcar ponte auth/problemdetails para error catalog quando a intencao da query exigir contrato de erro;
- [ ] manter comentado no codigo o por que de cada ajuste (ligacao direta com casos da suite).

### Fase 3 - nao regressao automatizada

- [ ] executar `pytest -q`;
- [ ] garantir verdes os testes de `I-02` (meta-governance) para evitar regressao de foco;
- [ ] confirmar regressoes criticas continuam verdes (DNS, persistencia SQL, resolve context evidence fields).

### Fase 4 - reexecucao da suite de 24 casos (MCP stdio)

- [ ] reexecutar protocolo real com `get_context_triggers`, `resolve_instruction_context`, `get_instructions_batch`, `validate_applicability`;
- [ ] gerar placar atualizado;
- [ ] comparar `7/24` vs `8/24` vs pos-`I-04`;
- [ ] registrar leitura por grupo (melhorou I-04? sobrou I-01 residual? surgiram novos desvios?).

### Fase 5 - gate de decisao

- [ ] se houver ganho material em casos `I-04`, consolidar pass e planejar proximo foco;
- [ ] se ganho for marginal, registrar `I-04` parcialmente insuficiente e promover proxima hipotese residual;
- [ ] nao abrir nova frente sem registrar evidencias do gate.

---

## Criterios de aceite

- [ ] testes de falha de `I-04` falham antes da correcao e passam apos a correcao;
- [ ] `pytest -q` permanece verde (zero regressao);
- [ ] suite de 24 casos reexecutada integralmente via MCP stdio;
- [ ] baseline pos-`I-04` nao fica abaixo de `8/24`;
- [ ] pelo menos 2 casos do grupo P1 de `I-04` melhoram (`T06`, `T08`, `T20`, `T21`);
- [ ] resultado final documenta explicitamente: "`I-04` suficiente" ou "`I-04` parcial/insuficiente".

---

## Testes obrigatorios (modelo inicial)

```python
def test_FAIL_tracing_query_should_include_observability_doc():
    ...

def test_FAIL_http_and_db_metrics_query_should_include_data_access_doc():
    ...

def test_FAIL_sql_timeout_transaction_query_should_include_production_readiness():
    ...

def test_FAIL_secrets_and_logs_query_should_include_production_readiness():
    ...

def test_FAIL_problemdetails_query_should_include_error_catalog():
    ...
```

---

## Criterios de leitura do rebaseline

Sinais fortes de melhora:

- `T06` e `T08` deixam de priorizar bundles de API generica e passam a incluir observabilidade/data-access esperados;
- `T20` e `T21` passam a incluir `microservice-configuration-production-readiness`;
- `T16` e/ou `T18` passam a incluir `microservice-api-error-catalog-baseline`.

Sinais de melhora parcial:

- alguns casos `I-04` melhoram, mas o placar sobe pouco;
- falta de supporting IDs continua como principal motivo de fail.

Sinais de hipotese insuficiente:

- placar permanece estagnado em `8/24`;
- mesmos casos `I-04` continuam com lacunas praticamente identicas;
- sem ganho liquido nos casos P1.

