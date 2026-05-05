# Comparativo — smoke test MCP stdio

## Escopo

Comparação entre duas rodadas do mesmo smoke test MCP stdio, ambas apontando para o mesmo corpus:

- **A**: instância global antiga
- **B**: versão local atual com as melhorias implementadas

## Resumo executivo

O protocolo básico MCP permaneceu estável nas duas rodadas, mas a versão atual ampliou claramente o valor do contrato entregue ao cliente. A versão antiga funciona como catálogo/search lexical simples. A versão atual acrescenta diagnósticos, versionamento do corpus e tools compostas úteis para orquestração.

## Quadro comparativo

| Dimensão | Global antigo | Local atual | Leitura |
|---|---|---|---|
| Tools expostas | 3 | 6 | Houve expansão do contrato sem perder as tools originais |
| `search_instructions` | retorno básico | retorno com `diagnostics` | Busca ficou mais explicável |
| `get_instructions_batch` | batch simples | batch com `corpus_version` e parâmetros novos | Mais rastreabilidade e foco |
| Tool composta | não | sim | Menor fricção para cliente/agente |
| Checklist por cenário | não | sim | Ajuda completude normativa |
| Conflitos/precedência | não | sim | Ajuda consistência entre instruções |

## Tools observadas

### Global antigo

- `get_instructions_batch`
- `list_instructions_index`
- `search_instructions`

### Local atual

- `detect_instruction_conflicts`
- `get_instructions_batch`
- `get_normative_checklist`
- `list_instructions_index`
- `resolve_instruction_context`
- `search_instructions`

## Diferenças de ranking observadas

### `mensageria outbox`

Top-3 permaneceu equivalente entre as duas versões:

1. `microservice-messaging-rabbitmq-publish-consume`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-data-access-and-sql-security`

Leitura: não houve regressão aparente no caso mais diretamente ligado ao cenário.

### `idempotencia eventos`

- **Antigo**: terceiro resultado `microservice-auth-jwt-bearer-and-authorization`
- **Atual**: terceiro resultado `microservice-rest-http-semantics-and-status-codes`

Leitura: houve mudança de desempate/ranking intermediário; o top-2 principal permaneceu estável.

### `resiliencia retry timeout`

- **Antigo**: terceiro resultado `microservice-data-access-and-sql-security`
- **Atual**: terceiro resultado `microservice-integration-httpclientfactory-contracts`

Leitura: o atual parece mais coerente com o domínio de integração/resiliência do que um documento de data access.

### `sql seguranca persistencia`

- **Antigo**:
  - `microservice-data-access-and-sql-security`
  - `microservice-domain-interfaces-models-repository`
  - `security-baseline-secrets`
- **Atual**:
  - `microservice-data-access-and-sql-security`
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`

Leitura: aqui a melhoria não é claramente superior no top-3; a busca atual puxou mais fortemente documentos de segurança/autorização. Isso é útil como sinal para revisão de tuning da consulta ou dos pesos de expansão nesse tema.

### `observabilidade correlation tracing`

Top-3 permaneceu equivalente entre as duas versões:

1. `microservice-opentelemetry-correlation-and-health`
2. `microservice-saga-process-manager-and-compensation`
3. `microservice-clean-architecture-guardrails`

Leitura: estabilidade preservada no domínio de observabilidade.

## Diagnósticos novos observáveis

Somente na versão atual:

- `search_confidence`
- `top_score_gap_1_2`
- `top3_scores`
- termos casados do utilizador
- termos vindos só de expansão
- `fallback_suggestions`

Leitura: isso não muda apenas o ranking; muda a capacidade do cliente/agente de saber quando confiar ou refinar a busca.

## Ferramentas compostas novas

### `resolve_instruction_context`

Valor observado:

- faz seleção de IDs
- agrega `search` + `batch`
- reduz a necessidade de orquestração manual do lado do cliente

### `get_normative_checklist`

Valor observado:

- retorna checklist por cenário
- no caso `mensageria_outbox`, devolveu `2` itens e nenhum faltante

### `detect_instruction_conflicts`

Valor observado:

- já oferece checagem explícita de conflitos/precedência
- detectou `2` conflitos no conjunto testado

## Conclusão

### Ganho evidente

A versão local atual mostrou ganho claro de **contrato**, **explicabilidade** e **orquestração**, mesmo num smoke test curto. O MCP deixa de ser apenas um ponto de busca/batch e passa a expor primitives mais úteis para um agente.

### Ganho parcialmente validado

No ranking puro, os resultados ficaram mistos:

- estabilidade ou melhora em `mensageria outbox`, `resiliencia retry timeout` e `observabilidade correlation tracing`
- mudança discutível em `sql seguranca persistencia`

### Veredicto prático

Pelo que foi possível observar via MCP stdio real, a implementação nova **surtiu efeito esperado no contrato e na ergonomia de consumo**. Já a validação de “efeito esperado no comportamento final da IA” ainda ficou **parcial**, porque faltou a rodada ponta a ponta com agente real usando essas tools em uma tarefa completa.

## Próximo passo recomendado

Quando houver um modo viável de execução de agente ponta a ponta neste ambiente, repetir exatamente estes cenários com:

- mesma tarefa
- mesmo corpus
- versão antiga vs atual
- captura do uso efetivo das novas tools compostas

Isso permitiria validar não só a capacidade do MCP, mas também se o agente realmente converte o contrato expandido em melhor comportamento final.
