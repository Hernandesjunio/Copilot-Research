# EPIC-09 I-04 - observability/readiness cross-domain coverage (controlled pass)

## Escopo executado

- Foco exclusivo em `I-04`: cobertura semantica entre observabilidade, readiness/configuracao e consultas tecnicas adjacentes.
- Guardrails respeitados:
  - sem alteracao de contratos publicos;
  - sem alteracao de corpus/frontmatter;
  - sem alteracao de algoritmo de ranking;
  - sem alteracao de `context_resolver.py` para tuning amplo.
- Mudancas implementadas:
  - `mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`:
    - adicao de pontes focais para `T06/T08/T16/T18/T20/T21` (`traceparent`, `correlation`, `metricas`, `banco`, `transacao`, `queries`, `segredos`, `logs`, `problemdetails`, `claims`);
  - `mcp-instructions-server/corporate_instructions_mcp/indexing.py`:
    - espelho dos mesmos ajustes em `DEFAULT_SYNONYMS` com comentarios de rastreabilidade por caso;
  - `mcp-instructions-server/tests/test_epic09_i04_cross_domain_coverage.py`:
    - 6 testes focais de falha/comportamento esperado para `I-04`.

## Fase 0 - baseline congelado

- `pytest -q` pre-pass: `149 passed, 1 skipped`.
- Rebaseline operacional anterior da suite de 24: `8/24`.
- Fail set alvo de `I-04`: `T06`, `T07`, `T08`, `T11`, `T16`, `T18`, `T20`, `T21`.

## Fase 1 - fail-first (antes da correcao)

Execucao:

- `pytest -q tests/test_epic09_i04_cross_domain_coverage.py`

Resultado:

- `6 failed` (falhando exatamente nos gaps esperados de `I-04`).

## Fase 2 - implementacao minima em sinonimos

Resultado da execucao focal apos ajuste:

- `pytest -q tests/test_epic09_i04_cross_domain_coverage.py`
- `6 passed`.

Efeitos observados em casos-alvo (consulta -> `selected_ids`):

- `T06`: passou a incluir `microservice-opentelemetry-correlation-and-health`.
- `T08`: passou a incluir `microservice-data-access-and-sql-security`.
- `T20`: passou a incluir `microservice-configuration-production-readiness`.
- `T16`: passou a incluir `microservice-api-error-catalog-baseline`.
- `T18`: passou a incluir `microservice-api-error-catalog-baseline`.
- `T21`: `microservice-configuration-production-readiness` melhorou ranking (aprox. `#20 -> #8` em busca com top estendido), mas ainda fora de `selected_ids` no corte padrao de 7.

## Fase 3 - nao regressao automatizada

Executado:

- `pytest -q tests/test_epic09_i02_meta_governance.py` -> `3 passed`;
- `pytest -q tests/smoke_test.py` -> `32 passed`;
- `pytest -q tests/integration_mcp_stdio_test.py` -> `6 passed`;
- `pytest -q` -> `155 passed, 1 skipped`.

## Fase 4 - reexecucao da suite de 24 via MCP stdio

Protocolo executado em cada caso:

- `get_context_triggers`
- `resolve_instruction_context`
- `get_instructions_batch`
- `validate_applicability`

Critero de aprovacao aplicado (mesmo da suite):

- todos `primary_ids` presentes em `selected_ids`;
- pelo menos um `supporting_id` presente;
- nenhum `nao priorizar` no top-2.

Placar:

- pos-`I-04`: `9/24`.
- aprovados: `T05`, `T14`, `T15`, `T16`, `T17`, `T19`, `T22`, `T23`, `T24`.
- reprovados: `T01`, `T02`, `T03`, `T04`, `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`, `T18`, `T20`, `T21`.

Comparativo:

- baseline historico: `7/24`;
- baseline pos-`I-01`: `8/24`;
- baseline pos-`I-04` (este pass): `9/24`.

## Leitura do gate

- Houve ganho liquido (`+1` no placar agregado) e ganhos claros de cobertura semantica em casos de `I-04` (especialmente `T06`, `T08`, `T16`, `T18`, `T20`).
- Persistem falhas de supporting IDs e ranking de corte em parte dos casos `I-04` (principalmente `T21` e supporting de `T06/T08/T20`).

Decisao registrada:

- **`I-04` parcial/insuficiente** para destravar materialmente a suite.
