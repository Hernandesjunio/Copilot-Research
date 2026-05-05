# Comparativo — smoke test MCP stdio

## Escopo

Comparação entre:

- **Iteração 2**: rodada após reforço dos itens médios (`M7`, `M8`, `M9`, `M12`, `M13`, `M20`)
- **Iteração 3**: rodada após evolução dos itens de alto valor/alto esforço (`M16`, `M17`, `M18`, `M22`)

Ambas apontando para o mesmo corpus de fixtures.

## Resumo executivo

As queries-base permaneceram estáveis na iteração 3, sem regressão observável no top-3 dos cenários principais. O ganho desta rodada não apareceu em “mudar ranking bruto”, e sim em transformar as tools compostas e o painel de qualidade em artefatos muito mais úteis para consumo operacional.

## Quadro comparativo

| Dimensão | Iteração 2 | Iteração 3 | Leitura |
|---|---|---|---|
| Queries-base | estáveis | estáveis | Comparabilidade mantida |
| `resolve_instruction_context` | retorna `search` + `batch` | retorna `selection`, `criteria`, `evidence_bundle` e `actionable_context` | Ganho claro de acionabilidade |
| Seleção de contexto | top ids sem critério explícito | separa `normative_ids` e `supporting_ids`, com `section_focus` | Menos atrito entre `search` e `batch` |
| `get_normative_checklist` | itens simples com existência no índice | cenário estruturado, `requirement_level`, `support_ids`, `evidence_ids`, `verification`, prontidão | Ganho forte de utilidade para implementação |
| `detect_instruction_conflicts` | conflito básico por `scope/kind` | `relationships`, severidade, precedência por `scope/kind/priority`, guidance para agente | Ganho forte de explicabilidade |
| Telemetria de tools compostas | praticamente ausente no painel | refletida no quality report | `M22` ficou mais real |
| `build_quality_report.py` | métricas básicas | `summary`, `counts`, `rates`, `search_quality`, `tool_breakdown`, `warnings`, baseline opcional | Ganho claro de governança |

## Estabilidade das queries-base

### `mensageria outbox`

Top-3 permaneceu igual à iteração 2:

1. `microservice-messaging-rabbitmq-publish-consume`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-data-access-and-sql-security`

### `idempotencia eventos`

Top-3 permaneceu igual à iteração 2:

1. `microservice-messaging-rabbitmq-publish-consume`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-rest-http-semantics-and-status-codes`

### `resiliencia retry timeout`

Top-3 permaneceu igual à iteração 2:

1. `microservice-resilience-polly-timeouts-and-circuit-breaker`
2. `dns-retry-pattern`
3. `microservice-integration-httpclientfactory-contracts`

### `sql seguranca persistencia`

Top-3 permaneceu igual à iteração 2:

1. `microservice-data-access-and-sql-security`
2. `microservice-auth-jwt-bearer-and-authorization`
3. `microservice-authorization-resource-scope-and-audit`

Leitura:

- o caso continua com gap de score curto no topo, tal como já ocorria
- a diferença é que a iteração 3 melhora fortemente o que o cliente faz depois da busca, via `resolve_instruction_context` e `detect_instruction_conflicts`

### `observabilidade correlation tracing`

Top-3 permaneceu igual à iteração 2:

1. `microservice-opentelemetry-correlation-and-health`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-clean-architecture-guardrails`

## Ganhos novos da iteração 3

### `M16` saiu do modo “wrapper”

Na iteração 2, `resolve_instruction_context` era essencialmente um encadeamento conveniente de `search` + `batch`.

Na iteração 3, a resposta passou a explicitar:

- critério de seleção
- `section_focus`
- distinção entre `normative_ids` e `supporting_ids`
- `evidence_bundle`
- `implementation_brief`
- próximos passos e gaps

Leitura:

- isso reduz bastante o número de passos que o cliente/agente precisa inferir sozinho

### `M17` virou checklist de implementação, não só de indexação

Na iteração 2, não havia evidência de checklist normativo estruturado por cenário.

Na iteração 3, `get_normative_checklist` passou a devolver:

- meta do cenário
- itens required/recommended
- `support_ids`
- `evidence_ids`
- `verification`
- `implementation_readiness`

Leitura:

- houve salto de completude para consumo prático em cenários como `mensageria_outbox` e `security_baseline`

### `M18` passou a explicar precedência de forma operacional

Na iteração 2, a detecção de conflitos ainda era superficial.

Na iteração 3, a tool passou a devolver:

- `relationships`
- `potential_conflict`
- severidade
- razão da relação
- precedência por `scope`, `kind` e `priority`
- guidance textual para cliente/agente

Leitura:

- no caso `dns-retry-pattern` vs `microservice-resilience-polly-timeouts-and-circuit-breaker`, a precedência ficou clara: a `policy` vence a `reference`
- no caso auth vs resource scope, a tool deixa claro que não existe desempate automático e recomenda combinação + escalonamento para instruções locais

### `M22` deixou de ser só taxa agregada

Na iteração 2, o quality report era útil, mas ainda muito enxuto.

Na iteração 3, o relatório passa a consolidar:

- `summary`
- `counts`
- `rates`
- `search_quality`
- `tool_breakdown`
- `warnings`
- suporte a baseline opcional

Sinais observados na própria rodada:

- `tool_failure_rate: 0.0`
- `retry_rate: 0.0625`
- `zero_result_rate: 0.0`
- `low_confidence_rate: 0.0`
- tools compostas já aparecem no breakdown

Leitura:

- o painel ficou mais útil para governança contínua por release

## Conclusão

A iteração 3 manteve a estabilidade das buscas-base e entregou o principal valor esperado para os itens de alto esforço:

- contexto resolvido de forma mais acionável
- checklist normativo orientado a implementação
- conflito/precedência com leitura operacional
- painel de qualidade mais governável

## Veredicto prático

Se a pergunta for “a iteração 3 melhorou materialmente `M16`, `M17`, `M18` e `M22` sem regredir o comportamento observado na iteração 2?”, a resposta é **sim**.

Se a pergunta for “o ranking puro das queries-base mudou muito?”, a resposta continua sendo **não**, e isso aqui é mais sinal de estabilidade do que de regressão.
