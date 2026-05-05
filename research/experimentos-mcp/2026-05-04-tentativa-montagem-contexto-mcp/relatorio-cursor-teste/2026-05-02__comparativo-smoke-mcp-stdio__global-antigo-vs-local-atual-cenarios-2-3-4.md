# Comparativo — smoke test MCP stdio

## Escopo

Comparação entre:

- **A**: instância global antiga de `corporate-instructions`
- **B**: versão local atual do projeto

O foco desta comparação são os cenários:

- `cenario-02-cep-viacep`
- `cenario-03-auth-jwt`
- `cenario-04-saga-onboarding`

## Resumo executivo

O projeto atual preservou os sinais fortes que já apareciam no MCP antigo para os três cenários, mas acrescentou um ganho material de contrato e consumo: o cliente deixa de depender só de `search` e `batch` e passa a contar com resolução de contexto, checklist por cenário e leitura explícita de conflitos/precedência.

O efeito varia por cenário:

- em `Auth/JWT`, o ganho foi o mais claro
- em `Saga onboarding`, o ganho foi relevante no desenho e na orquestração
- em `CEP/ViaCEP`, o ganho ficou mais no contrato do MCP do que no domínio, porque o corpus continua genérico para esse caso de negócio

## Quadro comparativo

| Dimensão | Global antigo | Local atual | Leitura |
|---|---|---|---|
| Tools expostas | 3 | 6 | O projeto atual amplia o contrato sem perder compatibilidade |
| `search_instructions` | suficiente para discovery | idem + mais útil quando combinado com tools compostas | Busca continua forte |
| Resolução de contexto | manual no cliente | `resolve_instruction_context` | Menor fricção |
| Checklist por cenário | inexistente | `get_normative_checklist` | Mais completude operacional |
| Conflitos/precedência | implícitos | `detect_instruction_conflicts` | Mais consistência para cliente/agente |
| Estabilidade operacional | boa | boa | Na rodada atual: `tool_failure_rate = 0.0` |

## Cenário 2 — CEP / ViaCEP

### Global antigo

Pontos fortes observados:

- boa recuperação de `HttpClient`, `timeout`, `retry`, `circuit breaker`
- boa recuperação de cache, contrato HTTP e observabilidade

Limitações observadas:

- sem guidance específico para ViaCEP
- sem guidance específico para modelagem de endereço
- sem apoio explícito para “validação pendente” além de inferência do cliente

### Local atual

Pontos fortes observados:

- manteve os mesmos anchors fortes de resiliência e contrato HTTP
- `resolve_instruction_context` agrupou corretamente:
  - `microservice-resilience-polly-timeouts-and-circuit-breaker`
  - `microservice-integration-httpclientfactory-contracts`
  - `dns-retry-pattern`
- `get_normative_checklist` trouxe `api_http_contract` pronto para uso
- `detect_instruction_conflicts` mostrou que `microservice-api-validation-and-error-contracts` e `microservice-rest-http-semantics-and-status-codes` devem ser combinados, não escolhidos cegamente

### Leitura

Houve ganho claro de consumo, mas não de especialização do domínio. O projeto atual ajuda mais a orquestrar os guardrails transversais, porém o caso ViaCEP continua a depender de inferência e de contexto local do produto.

## Cenário 3 — Auth / JWT

### Global antigo

Foi o cenário mais forte da rodada antiga:

- forte recuperação de JWT Bearer
- forte recuperação de ownership / resource-scope
- boa cobertura de `401/403`, contrato HTTP e segredos

Limitações observadas:

- nomes concretos de roles continuam locais
- desenho exato de `/clientes/meus` continua local
- schema de auditoria e colunas ainda dependem do repositório

### Local atual

Pontos fortes observados:

- manteve o mesmo núcleo forte de ranking:
  - `microservice-auth-jwt-bearer-and-authorization`
  - `microservice-authorization-resource-scope-and-audit`
  - `microservice-api-validation-and-error-contracts`
- `resolve_instruction_context` devolveu os três como `normative_ids`, o que é coerente
- `get_normative_checklist` para `security_baseline` consolidou `jwt_validation`, `resource_scope_audit` e `error_leakage`
- `detect_instruction_conflicts` deixou claro que auth e resource-scope não têm vencedor automático; devem ser combinados

### Leitura

Este é o cenário onde a versão local atual mais claramente supera a antiga. O corpus já era forte aqui; com as novas tools, a informação fica muito mais utilizável sem exigir tanta interpretação manual do cliente.

## Cenário 4 — Saga onboarding

### Global antigo

Pontos fortes observados:

- boa recuperação de saga/process manager
- boa recuperação de outbox, idempotência, resiliência, SQL e observabilidade

Limitações observadas:

- saga era mais guidance de referência do que baseline normativo
- `OnboardingSagaState`, timeouts por etapa e shape das compensações ainda dependiam muito do repositório
- escolha entre HTTP, fila ou in-process continuava local

### Local atual

Pontos fortes observados:

- manteve boa recuperação para saga/outbox/idempotência
- `resolve_instruction_context` separou corretamente:
  - baseline normativo: `microservice-messaging-rabbitmq-publish-consume`, `microservice-data-access-and-sql-security`
  - referência de apoio: `microservice-saga-process-manager-and-compensation`
- `get_normative_checklist` para `mensageria_outbox` trouxe checklist acionável
- `detect_instruction_conflicts` mostrou explicitamente que `policy` de mensageria deve prevalecer sobre a `reference` de saga quando houver tensão

### Leitura

O ganho principal aqui foi tornar o desenho mais seguro para consumo por cliente/agente. A antiga já ajudava a encontrar os documentos; a atual ajuda a não tratar a instruction errada como baseline.

## Onde o projeto atual melhorou de forma mais clara

### Contrato do MCP

O salto mais evidente não foi só “achar documentos”, e sim:

- resolver contexto em pacote mais acionável
- estruturar checklist de cenário
- expor conflitos e precedência

### Governança da rodada

Na execução atual dos cenários 2, 3 e 4:

- `31` calls completas
- `18` buscas
- `tool_failure_rate: 0.0`
- `retry_rate: 0.0`
- `zero_result_rate: 0.0`
- `low_confidence_rate: 0.0`
- `avg_search_confidence: 0.983417`

Leitura:

- a base local atual mostrou estabilidade operacional na rodada

## Onde o ganho ainda é parcial

### Domínio específico

Nem a versão antiga nem a atual eliminam a dependência de contexto local quando o problema é muito ligado ao negócio:

- `CEP/ViaCEP`: falta modelagem de endereço/estado do domínio
- `JWT`: faltam roles e contratos concretos do produto
- `Saga onboarding`: faltam os detalhes do fluxo real e do estado persistido concreto

### Leitura

O projeto atual melhora muito o “como consumir o corpus”, mas não cria, por si só, conhecimento de domínio que não exista no corpus ou no repositório-alvo.

## Conclusão

### Ganho evidente

A versão local atual superou a instância global antiga em ergonomia de consumo e em consistência do contrato nos três cenários.

### Ganho mais forte

O maior ganho apareceu em `Auth/JWT`, porque esse tema já era bem coberto pelo corpus e as tools novas reduziram bastante a ambiguidade operacional.

### Ganho mais limitado

O menor ganho apareceu em `CEP/ViaCEP`, porque o principal gargalo continua sendo a falta de guidance de domínio específico, não de infraestrutura MCP.

### Veredicto prático

Para os cenários 2, 3 e 4, o projeto atual mostrou-se melhor do que a instância global antiga não só por expor mais tools, mas por transformar melhor o corpus em contexto utilizável. Ainda assim, a redução de inferência continua parcial quando a tarefa depende fortemente do modelo de negócio do repositório-alvo.
