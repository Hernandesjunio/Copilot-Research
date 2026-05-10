# Plano de testes MCP — expansão de query (3 tools apenas)

Este documento descreve um protocolo **manual** (ou semi-automatizado) para validar a expansão de consulta do **Corporate Instructions MCP** em **stdio**, usando apenas as três tools expostas no catálogo mínimo de produto.

## Execução automatizada (regressão local)

A partir da pasta `mcp-instructions-server/`:

```bash
pip install -e ".[dev]"
python scripts/run_query_expansion_manual_battery.py
```

- Por omissão usa `INSTRUCTIONS_ROOT` do ambiente, ou — se não estiver definido — o corpus de exemplo do monorepo: `fixtures/instructions` (relativamente à raiz do repositório Copilot-Research).
- Saída: tabela Markdown no stdout com top-1, termos `matched_user_terms` / `matched_expansion_only_terms` e indicação Pass/Fail.
- Opções úteis:
  - `--json` — relatório completo em JSON.
  - `--strict` — código de saída 1 se **qualquer** caso E1–E7, fase 1 ou fase 3 falhar (adequado a gate mais rígido).
  - `--instructions-root CAMINHO` — corpus alternativo (deve conter `metadata/corpus-query-expansion-map/*.yaml` ao lado dos `.md` para a expansão estar activa).

Código de saída: **0** se o critério pragmático for atendido (≥ 5 de 7 casos E1–E7 com regras do fixture de referência, fase 1 OK, fase 3 OK); **1** caso contrário; **2** se o directório do corpus não existir.

## Contexto e restrições

- **Servidor:** Corporate Instructions MCP em **stdio** (`python -m corporate_instructions_mcp` ou entrypoint equivalente).
- **Variável obrigatória:** `INSTRUCTIONS_ROOT` aponta para a **raiz do corpus** de instructions (pasta que contém os `.md` e, para estes testes, também `metadata/corpus-query-expansion-map/*.yaml`).
- **Tools permitidas nesta sessão:** apenas:
  1. `list_instructions_index`
  2. `search_instructions`
  3. `get_instructions_batch`
- **Não usar:** `resolve_instruction_context`, `get_context_triggers`, `validate_applicability`, `build_compliance_matrix`, etc. (fora de âmbito / versão pausada conforme ADR de produto).
- **Foco:** validar que a **expansão de termos** do mapa corporativo influencia a **relevância** e é **observável** na resposta de `search_instructions` quando `include_diagnostics: true`.

## Pré-requisitos

1. Instalar o pacote do servidor (`pip install -e ".[dev]"` a partir de `mcp-instructions-server/`) no interpretador que o MCP usa.
2. Definir `INSTRUCTIONS_ROOT` para o mesmo corpus usado nos testes (ex.: clone com `fixtures/instructions` do repositório Copilot-Research, ou corpus interno equivalente **com** o mapa YAML em `metadata/corpus-query-expansion-map/`).
3. Confirmar que existem ficheiros `*.yaml` nesse directório (expansão desactiva-se se o directório estiver vazio).

## O que é “expansão” nesta versão

- O servidor carrega `metadata/corpus-query-expansion-map/*.yaml` (schema `domain` + `entries`).
- Cada token da query é comparado com **`canonical`** das entradas; aliases/strong/weak alimentam termos adicionais com pesos (alias/forte/fraco).
- O **limite por token** na expansão aplicada ao score é pequeno (ordem de **5** candidatos por token após ordenação); o mapa pode ter mais termos no lookup, mas só os primeiros entram nos pesos efectivos.
- **Importante para validação:** a lista global `expanded_terms` pode **não** aparecer no JSON devolvido ao cliente; use **sempre** os campos abaixo para provar expansão.

## Campos a inspeccionar (sucesso / falha)

Após cada `search_instructions` com `include_diagnostics: true`:

1. **`results[i].match_explanation.matched_user_terms`** — tokens da query que bateram directamente no documento.
2. **`results[i].match_explanation.matched_expansion_only_terms`** — termos que entraram **só via mapa** (expansão), não como token literal da query.
3. **`diagnostics.matched_expansion_only_terms`** — união (aproximada) dos termos só-expansão nos primeiros resultados.
4. **`diagnostics.results_only_from_expansion_count`** — quantos resultados têm match por expansão sem overlap de termos do utilizador (quando aplicável).
5. **`results[0].id` / `score` / `relevance`** — coerência do ranking esperado para cada cenário.

Critério geral de **expansão a funcionar:** para queries que usam **um canónico do mapa** (ex. `persistência`, `mensageria`), o top-1 deve ser plausível para o domínio **e** `matched_expansion_only_terms` no top-1 (ou nos top-3) deve ser **não vazio** quando a query não contém explicitamente todos os sinónimos (ex. só “persistência” → aparecem termos como `dapper`, `sql`, `data`, etc., conforme o mapa e o documento).

---

## Fase 1 — `list_instructions_index`

**Chamada:** `list_instructions_index` com argumentos vazios `{}` (ou conforme schema do host).

**Verificar:**

- `status` e `index_health.loaded == true` (ou equivalente).
- `count` ≥ 1; lista `instructions` com `id`, `tags`, etc.
- `by_tag` presente.

**Falha:** `status` erro, `count == 0`, ou ausência de instruções esperadas no corpus de referência.

**Nota:** esta tool **não** mostra expansão; serve só para garantir índice saudável antes das buscas.

---

## Fase 2 — `search_instructions` (bateria de expansão)

Para **cada** caso, chamar:

```json
{
  "query": "<QUERY>",
  "max_results": 5,
  "include_diagnostics": true
}
```

(Ajustar nomes de parâmetros ao schema exacto exposto pelo MCP — em geral `query`, `max_results`, `include_diagnostics`.)

### Caso E1 — Persistência (mapa persistence.yaml)

- **Query:** `persistência`
- **Esperado:** top-1 tendencialmente `microservice-data-access-and-sql-security` (ou ID equivalente no teu corpus).
- **Expansão:** no top-1, `matched_expansion_only_terms` deve incluir termos relacionados do mapa/corpus (ex.: dapper, sql, data, repositorio — os exactos dependem do mapa e do texto indexado).
- **Critério:** `matched_user_terms` pode estar vazio no top-1 se só o termo normalizado/expandido pontuar; o importante é haver evidência em `matched_expansion_only_terms` ou match forte via termos expandidos nos top resultados.

### Caso E2 — Mensageria (mapa messaging.yaml)

- **Query:** `mensageria`
- **Esperado:** topo com documento de saga ou RabbitMQ (ex.: `microservice-saga-process-manager-and-compensation` ou `microservice-messaging-rabbitmq-publish-consume` — conforme corpus).
- **Expansão:** `matched_expansion_only_terms` deve incluir termos como publish, consume, outbox, messaging, etc., quando aplicável.

### Caso E3 — DNS + Polly (mapa dns.yaml + resilience.yaml, desambiguação)

- **Query:** `retry DNS polly`
- **Esperado:** top-1 deve ser `dns-retry-pattern` (no fixture de referência).
- **Expansão:** algum termo só-expansão (ex. resolver, ttl) pode aparecer em `matched_expansion_only_terms`; utilizador deve ver dns, retry, polly em `matched_user_terms` se tokenizados.

### Caso E4 — Polly / circuit breaker sem sinal DNS (regressão conhecida)

- **Query:** `polly retry circuit breaker` (sem a palavra dns nem sinónimos DNS do mapa de sinal).
- **Esperado:** o documento DNS não deve dominar o ranking; no fixture de referência espera-se comportamento que favoreça política de resiliência/Polly em detrimento de `dns-retry-pattern`.
- **Critério:** top-1 ≠ `dns-retry-pattern` (ajustar se o teu corpus diferir).

### Caso E5 — API / ProblemDetails (mapa api.yaml)

- **Query:** `como padronizar ProblemDetails sem try catch duplicado nos endpoints`
- **Esperado:** resultados incluem documentos de validação/erro API; expansão pode puxar rfc7807, problem-details, error-catalog, conforme mapa e texto.

### Caso E6 — JWT + baseline (mapa security.yaml + api.yaml)

- **Query:** `qual baseline para autenticacao JWT bearer e claims authorization?`
- **Esperado (fixture referência):** `microservice-auth-jwt-bearer-and-authorization` no conjunto de top resultados; e `microservice-api-error-catalog-baseline` entre os seleccionados se o corpus incluir o texto de suporte usado no repositório de referência.

### Caso E7 — Codificação de caracteres / tokenização

- **Query:** `persistência SQL dapper`
- **Esperado:** mesmo tipo de comportamento que E1; sem erro de tool; top relacionado com dados/SQL.

---

## Fase 3 — `get_instructions_batch` (fecho do circuito)

Para cada busca bem-sucedida, escolher até 3 `id` dos `results` (prioridade: top-1 e relacionados relevantes).

**Chamada (exemplo):**

```json
{
  "ids": "id1,id2,id3",
  "max_chars_per_instruction": 4000,
  "include_headings": true
}
```

**Verificar:**

- `found_count` coerente; `missing_ids` vazio para IDs pedidos.
- Corpo Markdown e frontmatter com `id` correspondente.
- Conteúdo útil para humano validar que o search devolveu instruções certas (sanity end-to-end).

---

## Registo de resultados (tabela sugerida)

| ID caso | Query | top-1 id | matched_user (top-1) | matched_expansion_only (top-1) | Pass/Fail |
|---------|-------|----------|----------------------|----------------------------------|-----------|
| E1 | persistência | | | | |
| E2 | mensageria | | | | |
| E3 | retry DNS polly | | | | |
| E4 | polly retry circuit breaker | | | | |
| E5 | ProblemDetails… | | | | |
| E6 | JWT baseline… | | | | |
| E7 | persistência SQL dapper | | | | |

Preencha após cada corrida manual ou copie a tabela gerada por `scripts/run_query_expansion_manual_battery.py`.

---

## Falhas comuns e como interpretar

- **Sempre `matched_expansion_only_terms` vazio:** verificar se `metadata/corpus-query-expansion-map/` tem YAML válido e se `INSTRUCTIONS_ROOT` aponta para a raiz certa (a que contém `metadata/` ao lado dos `.md`).
- **Ranking “estranho”:** lembrar que expansão é heurística + limite de candidatos por token; documentos com muitos hits no título/corpo podem ganhar sem expansão.
- **`include_diagnostics: false`:** não usar para estes testes — precisa de `match_explanation` e `diagnostics` para evidência de expansão.
- **Corpus diferente do fixture:** ajustar IDs esperados nas colunas “Esperado”, mantendo os critérios (presença de termos só-expansão e ranking DNS vs Polly).

---

## Definição de “perfeito” (aceite pragmático)

- Índice lista documentos (Fase 1 OK).
- Em ≥ 5 de 7 casos E1–E7, a evidência de expansão (`matched_expansion_only_terms` ou diagnóstico coerente) e o top-1/top-k alinham com as expectativas do mapa e do corpus.
- `get_instructions_batch` recupera sem erros os IDs devolvidos pelo search (Fase 3).

O script `run_query_expansion_manual_battery.py` replica este critério pragmático quando o corpus é o fixture de referência; com `--strict`, exige 7/7 nos casos de busca.

---

## Referência de implementação

- **ADR-002:** [`../../planning/adr/ADR-002-corpus-query-expansion-map.md`](../../planning/adr/ADR-002-corpus-query-expansion-map.md)
- **Testes automatizados semelhantes:** [`../tests/test_corpus_expansion_map_merged.py`](../tests/test_corpus_expansion_map_merged.py), [`../tests/test_indexing.py`](../tests/test_indexing.py), smoke em [`../tests/smoke_test.py`](../tests/smoke_test.py) com `search_instructions` e o fixture `fixtures/instructions`.
