# Comparativo — cenário 2 (CEP / ViaCEP) após tuning

## Escopo

Comparação entre duas leituras do mesmo cenário `CEP / ViaCEP` sobre a versão local atual do `corporate_instructions_mcp`:

- **Antes**: leitura já registrada nos relatórios de `2026-05-02`
- **Depois**: nova rodada MCP stdio real após ajuste de ranking/sinónimos para `CEP` / `ViaCEP`

Esta comparação mede **comportamento MCP/orquestração real**. Não valida agente Copilot ponta a ponta sobre uma API .NET real, porque este repositório não é o serviço alvo do cenário.

## Configuração da rodada pós-tuning

- Servidor: `python -m corporate_instructions_mcp`
- Diretório: `c:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `c:\_projeto\Copilot-Research\fixtures\instructions`
- Transporte: MCP `stdio`
- Telemetria: `CORPORATE_INSTRUCTIONS_TELEMETRY=minimal`

## Resumo executivo

O tuning melhorou de forma visível o cenário `CEP / ViaCEP` no eixo de **recuperação de bundle útil**:

- a query combinada passou a devolver no top-3 um pacote mais coerente para o caso:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-caching-imemorycache-policy`
  - `microservice-integration-httpclientfactory-contracts`
- a query de validação passou a trazer explicitamente `microservice-api-validation-and-error-contracts` no top-2
- o ruído por substring curta (`cep` a casar em termos irrelevantes) caiu

Ainda assim, o caso **não virou excelente** porque a lacuna principal continua a ser de **domínio**, não de infraestrutura MCP:

- continua sem existir instruction específica para `ViaCEP`
- continua sem guidance específica para modelagem de endereço
- continua sem guidance explícita para o estado “validação pendente”

## Antes vs depois

| Ponto | Antes | Depois | Leitura |
|---|---|---|---|
| Busca de resiliência/HTTP | já boa | continua boa | manteve anchor forte |
| Busca combinada para o cenário | dependia de decompor em várias queries | top-3 já traz resiliência + cache + integração | melhora real |
| Busca de validação | validação aparecia, mas menos acoplada ao cenário combinado | `api-validation-and-error-contracts` aparece no top-2 da query de validação | melhora real |
| `resolve_instruction_context` | útil em queries de infraestrutura | útil também para query de validação do cenário | melhora parcial |
| Ruído lexical | maior para termos curtos/genéricos | menor | melhora real |
| Domínio ViaCEP | fraco | fraco | sem mudança estrutural |

## Evidência observada

### Query combinada

Query:

- `cep viacep retry timeout cache`

Top-5 após tuning:

1. `microservice-resilience-polly-timeouts-and-circuit-breaker`
2. `microservice-caching-imemorycache-policy`
3. `microservice-integration-httpclientfactory-contracts`
4. `dns-retry-pattern`
5. `microservice-messaging-rabbitmq-publish-consume`

Leitura:

- o top-3 ficou melhor alinhado ao vertical slice do cenário
- ainda existe ruído no top-5 (`microservice-messaging-rabbitmq-publish-consume`)

### Query de validação mais específica

Query:

- `cep formato 8 digitos viacep 422 400 cache timeout retry`

Top-5 após tuning:

1. `microservice-resilience-polly-timeouts-and-circuit-breaker`
2. `microservice-api-validation-and-error-contracts`
3. `microservice-caching-imemorycache-policy`
4. `microservice-integration-httpclientfactory-contracts`
5. `dns-retry-pattern`

Leitura:

- esta foi a melhoria mais importante da rodada
- o cenário passou a recuperar com mais clareza o trio:
  - resiliência
  - contrato/validação HTTP
  - cache

### `resolve_instruction_context`

Para a query combinada:

- `normative_ids`:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-caching-imemorycache-policy`
  - `microservice-integration-httpclientfactory-contracts`
  - `microservice-messaging-rabbitmq-publish-consume`
- `supporting_ids`:
  - `dns-retry-pattern`

Para a query de validação:

- `normative_ids`:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-api-validation-and-error-contracts`
  - `microservice-caching-imemorycache-policy`
  - `microservice-integration-httpclientfactory-contracts`
- `supporting_ids`:
  - `dns-retry-pattern`

Leitura:

- o `resolve_instruction_context` ficou melhor quando a query já explicita validação/contrato
- para query mais ampla, ainda há um candidato normativo lateral demais (`messaging`)

### Checklist e conflitos

Mantiveram-se úteis:

- `get_normative_checklist(scenario="api_http_contract")`
  - `implementation_readiness: ready`
  - `required_items_covered: 2/2`
- `detect_instruction_conflicts(...)`
  - continua a indicar que `microservice-api-validation-and-error-contracts` e `microservice-rest-http-semantics-and-status-codes` devem ser **combinados**

Leitura:

- o ganho não está só na busca; o pacote operacional do MCP continua superior para consumo por agente/cliente

## Nota revista

### Nota anterior

- **6/10**

### Nota após tuning

- **7/10**

## Justificativa da nota

Subiu porque:

- o bundle técnico central do cenário agora aparece com menos esforço manual
- a validação HTTP passou a entrar com mais clareza quando a query explicita o problema
- houve redução observável do ruído lexical

Não subiu mais porque:

- ainda falta domínio específico para `ViaCEP`
- ainda falta guidance para shape de endereço e estado “pendente”
- `resolve_instruction_context` ainda pode puxar um normativo lateral em query ampla

## Veredicto

O tuning **melhorou de forma real** o cenário `CEP / ViaCEP`, mas a melhoria foi de **7/10**, não de excelência. O gargalo principal deixou de ser só ranking e continua a ser o **gap entre guardrail transversal e conhecimento de domínio específico**.

Em termos práticos:

- **sim**, a nota sobe
- **não**, ainda não chega ao nível de `Auth/JWT`
- o melhor uso para este cenário continua a ser:
  - múltiplas queries focadas
  - `resolve_instruction_context` com query mais explícita
  - checklist/conflitos como suporte, não como substituto de domínio
