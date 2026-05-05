# Comparativo — smoke test MCP stdio

## Escopo

Comparação entre:

- **Iteração 1**: primeira rodada da versão local atual
- **Iteração 2**: nova rodada após reforço dos itens `M7`, `M8`, `M9`, `M12`, `M13` e `M20`

Ambas apontando para o mesmo corpus.

## Resumo executivo

As queries-base permaneceram estáveis, sem regressão aparente no top-3 dos cenários principais. O ganho da iteração 2 apareceu sobretudo em **observabilidade do contrato**: o servidor agora evidencia melhor o que fazer em `zero_results`, quando o ranking está ambíguo e quais seções foram efetivamente devolvidas no batch.

## Quadro comparativo

| Dimensão | Iteração 1 | Iteração 2 | Leitura |
|---|---|---|---|
| Tools expostas | 6 | 6 | Contrato principal preservado |
| Queries-base | executadas | executadas | Comparabilidade mantida |
| `zero_results` | não testado explicitamente | testado e com fallback útil | Ganho observável |
| Ambiguidade de ranking | sem evidência explícita | fallback acionado em `sql seguranca persistencia` | Ganho observável |
| Batch por seções | uso básico de `section_contains` | retorno com `section_match_count` e `included_headings` validado | Ganho observável |
| Frase exata | não testado explicitamente | `"problem details"` testado com resultado coerente | Cobertura aumentada |
| Tokenização de versão | não testado explicitamente | `.NET 8 net8 v2` exercitado | Cobertura aumentada |

## Estabilidade das queries-base

### `mensageria outbox`

Top-3 permaneceu igual:

1. `microservice-messaging-rabbitmq-publish-consume`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-data-access-and-sql-security`

Leitura:

- estabilidade preservada

### `idempotencia eventos`

Top-3 permaneceu igual à iteração 1:

1. `microservice-messaging-rabbitmq-publish-consume`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-rest-http-semantics-and-status-codes`

Leitura:

- sem regressão aparente

### `resiliencia retry timeout`

Top-3 permaneceu igual à iteração 1:

1. `microservice-resilience-polly-timeouts-and-circuit-breaker`
2. `dns-retry-pattern`
3. `microservice-integration-httpclientfactory-contracts`

Leitura:

- sem regressão aparente

### `sql seguranca persistencia`

Top-3 permaneceu igual à iteração 1:

1. `microservice-data-access-and-sql-security`
2. `microservice-auth-jwt-bearer-and-authorization`
3. `microservice-authorization-resource-scope-and-audit`

Diferença nova:

- a iteração 2 agora expõe uma sugestão de fallback por `ambiguous_top_scores`

Leitura:

- o ranking em si não melhorou neste caso
- mas o contrato agora reconhece explicitamente a ambiguidade e sugere desambiguação por batch

### `observabilidade correlation tracing`

Top-3 permaneceu igual:

1. `microservice-opentelemetry-correlation-and-health`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-clean-architecture-guardrails`

Leitura:

- estabilidade preservada

## Novas evidências da iteração 2

### `zero_results`

Query usada:

- `qvwxzplm`

Resultado:

- `result_count = 0`
- sugestões de fallback presentes

Leitura:

- valida que a correção do bug de score por `priority` sem match lexical surtiu efeito

### Batch por seções com evidência

Novos sinais observados:

- `section_match_count`
- `included_headings`

Leitura:

- o cliente passa a saber não só que houve filtragem por seção, mas exatamente quais blocos foram usados

### Frase exata

Query:

- `"problem details"`

Resultado:

- retornou documentos coerentes do domínio de error contracts / API

Leitura:

- a heurística de frase exata está observável no comportamento do ranking

### Tokenização de versão

Query:

- `.NET 8 net8 v2`

Resultado:

- diagnóstico expôs `2`, `8`, `net`, `v2` como termos reconhecidos

Leitura:

- a tokenização ficou mais robusta para variantes de versão
- o valor do ranking ainda deve ser observado em cenários reais adicionais, mas o mecanismo está ativo

## Conclusão

A iteração 2 não mudou substancialmente os resultados das queries-base, o que é positivo em termos de estabilidade. O ganho principal foi tornar os refinamentos de médio esforço **mais reais e observáveis no contrato**:

- `zero_results` agora é tratado corretamente
- ambiguidade de ranking agora gera fallback explícito
- batch por seções agora devolve evidência concreta do recorte aplicado
- frase exata e tokenização de versão passaram a ter cobertura de smoke test

## Veredicto prático

Se a pergunta for “a nova iteração melhorou a robustez dos itens médios sem regredir o comportamento base?”, a resposta é **sim**.

Se a pergunta for “o ranking bruto melhorou perceptivelmente em todos os domínios?”, a resposta ainda é **não totalmente**; o caso `sql seguranca persistencia` continua sendo o principal candidato a tuning adicional.
