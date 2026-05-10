# Plano de testes — Corpus Query Expansion Map (pós-implementação)

**Status:** rascunho de aceite (pronto para automatizar em `pytest` quando o loader existir)  
**Relaciona:** [ADR-002](../adr/ADR-002-corpus-query-expansion-map.md), épico [EPIC-10](../bmad/epicos/EPIC-10-corpus-query-expansion-map.md)  
**Corpus de referência (fixtures):** `fixtures/instructions/`  
**Mapa YAML de referência:** `fixtures/instructions/metadata/corpus-query-expansion-map/`  
**Cenários parametrizáveis (YAML para pytest):** [`queries-expansion-map.yaml`](queries-expansion-map.yaml)

## 1. Objetivo

Definir cenários **reais** já analisados em revisão técnica, para validar a nova expansão quando o MCP deixar de depender apenas de `synonyms.yaml` e passar a consumir o mapa modular conforme a ADR (tipagem, contextos, `applies_to`, diagnósticos).

## 2. Pré-condições de execução

- `INSTRUCTIONS_ROOT` aponta para o corpus sob teste (ex.: `fixtures/instructions` em CI).
- Implementação carrega `metadata/corpus-query-expansion-map/*.yml` e integra ao fluxo existente de `tokenize_query` + scoring (sem BM25/vetorial na V1, conforme ADR).
- Opcional: variável ou flag de teste para **desligar** expansão e comparar baseline (comportamento legado ou “sem mapa”).

## 3. O que validar (checklist normativo)

| Área | Critério (ADR-002 §2.1 e consequências) |
|------|----------------------------------------|
| Direcionalidade | Expansão canónico → termos expandidos; sem transitividade multi-hop. |
| Tipos | `aliases`, `strong_terms`, `weak_terms` com pesos distintos na integração (quando implementado). |
| Contextos | `expansion_mode: contextual` + `contexts` só aplicam ramos quando `activation_terms` e/ou `applies_to` satisfeitos. |
| Ativação cruzada | Dois contextos activos no mesmo canónico → conflito explícito no diagnóstico, sem união silenciosa. |
| `applies_to` | Com `current_file_path` conhecido: filtra; com path ausente: não causa falsos negativos; omissão registada (ex. `skipped_by_applies_to`). |
| Erro de curadoria | Contexto com `terms` sem `activation_terms` nem `applies_to` → validação rejeita ou falha estrutural (V1.2). |
| Legado | Ausência de `when_path_matches` nos YAML carregados. |

## 4. Cenários de busca — corpus `fixtures/instructions`

Cada linha é um caso **já discutido** na análise; serve para regressão manual ou para parametrizar `pytest`.

Legenda:

- **top esperado:** pelo menos um dos `id` deve aparecer no top-K (definir K=5 ou 7 alinhado ao EPIC-07).
- **must-not:** documentos que não devem ranquear alto por expansão indevida (falso positivo).

### 4.1 Resiliência / Polly / HTTP

| ID | Query | `current_file_path` (opcional) | top esperado (mín.) | must-not (se aplicável) | Notas |
|----|--------|--------------------------------|---------------------|---------------------------|-------|
| EXP-POLLY-01 | `resilience httpclient` | `src/Api/ClienteHttp.cs` (exemplo `**/*.cs`) | `microservice-resilience-polly-timeouts-and-circuit-breaker` | — | Expansão típica a partir de `10-dotnet.yml` (`polly-timeouts-retry-circuit-breaker`). |
| EXP-POLLY-02 | `como configurar retry com backoff e circuit breaker para API de pagamentos` | — | `microservice-resilience-polly-timeouts-and-circuit-breaker` | `dns-retry-pattern` | Replica intenção do teste EPIC-07: retry genérico não deve puxar DNS. |
| EXP-POLLY-03 | `retry DNS polly` | — | `dns-retry-pattern` (idealmente top-1) | — | Query DNS-específica deve recuperar o doc DNS. |

### 4.2 DI, Options, configuração

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-DI-01 | `injecao de dependencia options` | `Program.cs` ou `**/*.cs` | `microservice-di-options-extensions`, `microservice-configuration-production-readiness` | — | Simulação com termos `AddOptions`, `IOptions`, `ValidateOnStart`. |

### 4.3 Cache

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-CACHE-01 | `quando usar imemorycache ttl e invalidacao em API de consulta` | — | `microservice-caching-imemorycache-policy` | — | Alinhado ao teste existente de `resolve_instruction_context` (observar mesma expectativa após novo loader). |

### 4.4 Integração HTTP

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-HTTP-01 | `integracao com api externa` ou `como fazer integracao externa` | — | `microservice-integration-httpclientfactory-contracts`, `microservice-resilience-polly-timeouts-and-circuit-breaker` | — | Aceitar também doc de observabilidade no top-K se `traceparent` expandir; registar como **aceitável** ou apertar `weak_terms` na curadoria. |

### 4.5 Testes (unit / integração / contrato)

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-TEST-01 | `estrategia de testes dotnet` | `**/*Tests/**/*.cs` | `microservice-testing-strategy-unit-integration-contract` | — | Mapa restringe por `applies_to` de testes; validar com path de ficheiro de teste. |

### 4.6 API — coleções, paginação, contrato

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-API-01 | `como implementar paginacao filtro e ordenacao em colecoes sem quebrar contrato` | — | `microservice-api-collection-resources-pagination-filters`, `microservice-api-openfinance-patterns` | — | Cenário já usado em EPIC-07. |
| EXP-API-02 | `api 400 422 problem details` | `**/Api/**/*.cs` | `microservice-api-validation-and-error-contracts` | — | Valida expansão de validação/erros com filtro de camada Api se implementado. |

### 4.7 Observabilidade + readiness

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-OBS-01 | `me informe como a observabilidade deve ser implementada` | — | `microservice-opentelemetry-correlation-and-health`, `microservice-configuration-production-readiness` | — | Exige que expansão ligue observabilidade a readiness/config (comportamento já coberto por teste atual com sinónimos). |
| EXP-OBS-02 | `como separar /health/live de /health/ready em servico .NET` | — | `microservice-configuration-production-readiness` | — | Teste existente; manter após novo mapa. |

### 4.8 Arquitetura / composição

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-ARCH-01 | `como o projeto deve ser estruturado` | — | Pelo menos 2 entre: `microservice-architecture-layering`, `microservice-clean-architecture-guardrails`, `microservice-domain-interfaces-models-repository` | `instruction-authoring-standard`, `assistant-workflow-bmad-planning-and-controlled-inference` | Evitar meta-governança no top-3 (teste EPIC-07). |

### 4.9 Mensageria — contexto (quando implementado)

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-MSG-01 | `mensageria` + query só com termos neutros | — | Comportamento dependente de `contexts`; validar diagnóstico de ambiguidade se dois ramos activáveis. | — | Documentar resultado esperado após implementação (conflito explícito vs ramo único). |
| EXP-MSG-02 | `mensageria rabbitmq amqp` | `**/*.cs` | `microservice-messaging-rabbitmq-publish-consume` | — | Activação por vocabulário RabbitMQ. |

### 4.10 Curadoria — termos sem evidência no corpus (negativo / gap)

| ID | Query | Path | top esperado | must-not | Notas |
|----|--------|------|--------------|----------|-------|
| EXP-GAP-01 | `fix-protocol heartbeat session` | — | — (ou baixo score) | Qualquer doc que só exista no mapa sem instruction correspondente | Se o ramo `fix` permanecer no YAML sem instruction de origem, **corrigir YAML** ou marcar teste como XFAIL até haver evidência. |

## 5. Métricas sugeridas (alinhamento benchmark existente)

Reutilizar `mcp-instructions-server/tests/benchmark/test_relevance_benchmark.py` e `queries.yaml`:

- Após implementação, **re-baseline** MRR / P@1 / P@3 / P@5.
- Manter limiares atuais como mínimo ou justificar alteração no PR.

## 6. Telemetria / diagnóstico

Para cada cenário crítico, com `include_diagnostics=true`:

- Lista de termos do utilizador vs termos só por expansão (`matched_user_terms` vs `matched_expansion_only_terms`).
- Se aplicável: entradas `skipped_by_applies_to`, conflitos de contexto, expansão truncada (`EXPANSION_CAP_PER_TOKEN` no código legado — revisar nome/limites no novo mapa).

## 7. Histórico de análise

Cenários deste documento foram consolidados a partir de:

- Revisão Staff do mapa YAML vs corpus e vs ADR-002.
- Comparação Estado A (`synonyms`) vs Estado B (mapa modular, ainda não ligado ao runtime).
- Simulações manuais de expansão (ex.: entrada `polly-timeouts-retry-circuit-breaker` em `10-dotnet.yml`).

---

**Automatização:** manter a tabela deste documento alinhada ao ficheiro [`queries-expansion-map.yaml`](queries-expansion-map.yaml); o YAML é a fonte preferida para `pytest` parametrizado (evitar divergência manual).

Ver também referência normativa em [ADR-002 §5.1](../adr/ADR-002-corpus-query-expansion-map.md#51-plano-de-testes-de-regressão).
