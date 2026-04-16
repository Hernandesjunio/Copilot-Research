---
titulo: "Plano BMAD — Melhoria do MCP para critérios 2 (Aderência) e 4 (Consistência)"
data: "2026-04-16"
tipo: "plano-de-execução"
escopo: "Ajustes em tools existentes + prompt de orquestração para fechar gap com Instructions locais"
criterios_alvo: [2, 4]
notas_atuais: { mcp_criterio_2: 8, mcp_criterio_4: 7, instructions_criterio_2: 9, instructions_criterio_4: 8 }
meta: { mcp_criterio_2: ">=9", mcp_criterio_4: ">=8" }
---

# Plano BMAD — Melhoria do MCP para critérios 2 e 4

## Background

### Contexto do experimento anterior

O experimento comparativo (análise em [`analise-comparativa-iteracao-1.md`](../analise-comparativa-iteracao-1.md)) revelou que o MCP perdeu para Instructions locais em **2 critérios de qualidade individual**:

| Critério | MCP (A) | Instructions (B) | Delta |
|---|---:|---:|---:|
| 2 — Aderência ao contexto | 8 | 9 | -1 |
| 4 — Consistência interna | 7 | 8 | -1 |

### Causa raiz — Critério 2 (Aderência)

**FATO:** O cenário MCP consultou 5 instructions de um corpus de 24 disponíveis. O cenário Instructions locais consultou 8.

**FATO:** O MCP fez 1 call de `search_instructions` (keyword overlap, max 5 resultados) + 5 calls de `get_instruction` (equivalente atual: `get_instructions_batch`). Instructions locais fez leitura direta de 24 arquivos e citou 15.

**FATO:** A instruction `microservice-data-access-and-sql-security` foi usada pelo cenário B mas **não foi retornada** pela busca MCP — a query não continha os termos certos para keyword overlap.

**Diagnóstico:** O gargalo é duplo:
1. **Prompt insuficiente**: não instruía o modelo a fazer `list_instructions_index` nem múltiplas buscas por tema.
2. **Tool limitada**: `search_instructions` com default 5 resultados e busca por keyword overlap perde instructions relevantes cujos termos não coincidem com a query.

### Causa raiz — Critério 4 (Consistência)

**FATO:** O cenário MCP implementou cache com `IMemoryCache` baseado na policy `microservice-caching-imemorycache-policy`, apesar de o repositório não ter nenhum uso de `IMemoryCache`.

**FATO:** O cenário Instructions locais fez `code_search` sem resultados para `IMemoryCache` e decidiu **não implementar cache** — decisão mais consistente com o código existente.

**Diagnóstico:** O MCP aplicou uma policy sem cruzar com o estado real do repo. O prompt não instruía conservadorismo nem cruzamento policy×código.

### O que já foi feito

**FATO:** O arquivo `copilot-instructions-mcp.md` foi ajustado com:
- Passo 1: obrigatoriedade de `list_instructions_index` antes de qualquer busca.
- Passo 2: múltiplas buscas por tema com `max_results: 10`.
- Passo 3: leitura de TODAS as instructions relevantes (não apenas as 5 primeiras).
- Passo 4: cruzamento policy×código com conservadorismo explícito.
- Passo 5: rastreabilidade com citação de IDs + arquivos.

**Pendente:** Ajustes nas tools do MCP server para amplificar o efeito do novo prompt.

---

## Mission

Evoluir as tools existentes do MCP server (`mcp-instructions-server/`) para que o cenário MCP atinja nota **>=9 em Aderência** e **>=8 em Consistência** no próximo experimento, sem quebrar a API existente nem adicionar dependências pesadas.

---

## Approach

### Frente 1 — Melhoria do `search_instructions` (Critério 2)

#### 1.1 Aumentar `max_results` default de 5 para 10

**Arquivo:** `corporate_instructions_mcp/server.py`, linha 124
**Mudança:** Alterar `max_results: int = 5` para `max_results: int = 10` e cap de 10 para 20.

**Justificativa:** O corpus tem 24 instructions. Com default 5, o modelo vê no máximo ~20% do corpus por busca. Com default 10 e cap 20, uma única busca pode cobrir ~40-80% do corpus.

**Risco:** Baixo. Aumento de payload no retorno é proporcional mas controlado (metadados + excerpts, não corpos completos).

**Impacto em testes:** Ajustar `smoke_test.py` e `integration_mcp_stdio_test.py` onde `max_results=3` é passado explicitamente (esses não quebram, pois o valor explícito prevalece).

#### 1.2 Melhorar scoring para reduzir falsos negativos

**Arquivo:** `corporate_instructions_mcp/indexing.py`, função `score_record`

**Problema atual:** O scoring é puramente baseado em contagem de tokens (`blob.count(t)`). Se a query for "persistência SQL Dapper" mas a instruction usa "data access" e "parameterized queries", o score será 0 — falso negativo.

**Mudança proposta:** Adicionar um dicionário de sinônimos/termos relacionados por domínio para expandir a query antes do scoring.

```python
SYNONYMS: dict[str, list[str]] = {
    "cache": ["imemorycache", "idistributedcache", "caching", "ttl", "invalidação"],
    "persistência": ["dapper", "sql", "repositorio", "data-access", "query"],
    "validação": ["validation", "error-contracts", "400", "422"],
    "http": ["rest", "status-codes", "get", "put", "post", "delete", "endpoint"],
    "resiliência": ["polly", "retry", "circuit-breaker", "timeout", "tolerância"],
    "arquitetura": ["layering", "camadas", "clean-architecture", "solid"],
    "testes": ["testing", "unit", "integration", "contract"],
    "observabilidade": ["opentelemetry", "health", "correlation", "tracing"],
    "mensageria": ["rabbitmq", "messaging", "publish", "consume"],
    "segurança": ["security", "secrets", "tokens"],
}
```

**Lógica:** Antes de scoring, expandir `tokens` com sinônimos. Peso dos sinônimos: 50% do peso de match direto (para não dominar o ranking).

**Risco:** Médio. Sinônimos muito amplos podem introduzir falsos positivos. Mitigação: limitar a 3-5 sinônimos por termo e testar com o corpus real.

**Impacto em testes:** Adicionar testes unitários para `expand_query_with_synonyms` e verificar que a busca "persistência SQL" retorna `microservice-data-access-and-sql-security`.

#### 1.3 Adicionar campo `related_instructions` no retorno de `search_instructions`

**Arquivo:** `corporate_instructions_mcp/server.py`, dentro da tool `search_instructions`

**Mudança:** Após rankear os resultados, para cada instruction retornada, incluir um campo `related_ids` baseado em intersecção de tags com outras instructions do corpus.

**Justificativa:** Permite ao modelo descobrir instructions que não apareceram na busca mas compartilham tags com as encontradas. No experimento, `microservice-data-access-and-sql-security` compartilha tags com `microservice-architecture-layering` — se o modelo encontra uma, descobre a outra.

**Risco:** Baixo. É metadata adicional, não altera o comportamento do modelo a menos que ele escolha ler as relacionadas.

### Frente 2 — Melhoria do `list_instructions_index` (Critério 2)

#### 2.1 Adicionar agrupamento por tags no retorno

**Arquivo:** `corporate_instructions_mcp/server.py`, tool `list_instructions_index`

**Mudança:** Além da lista flat, incluir um campo `by_tag` que agrupa IDs por tag.

```json
{
  "instructions": [...],
  "count": 24,
  "by_tag": {
    "microservice": ["microservice-architecture-layering", "microservice-rest-http-semantics-and-status-codes", ...],
    "api": ["microservice-api-validation-and-error-contracts", "microservice-api-openfinance-patterns", ...],
    "cache": ["microservice-caching-imemorycache-policy"],
    "testing": ["microservice-testing-strategy-unit-integration-contract"],
    ...
  }
}
```

**Justificativa:** Permite ao modelo navegar o corpus por tema em vez de ler 24 títulos e decidir quais buscar. Reduz dependência de keyword match.

**Risco:** Baixo. Payload ligeiramente maior, mas são apenas IDs (strings curtas).

### Frente 3 — Nova tool `get_instructions_batch` (Critério 2)

#### 3.1 Leitura em lote

**Arquivo:** `corporate_instructions_mcp/server.py` — nova tool

**Problema:** O modelo precisa fazer N calls de `get_instruction` para ler N instructions (equivalente atual: `get_instructions_batch` em uma única chamada). No experimento, foram 5 calls. Com o novo prompt pedindo "leia TODAS as relevantes", serão 8-12 calls. Cada call é um round-trip JSON-RPC.

**Mudança:** Adicionar tool `get_instructions_batch` que aceita uma lista de IDs e retorna todos os corpos num único retorno.

```python
@mcp.tool()
def get_instructions_batch(
    ids: str,
    max_chars_per_instruction: int = 8000,
) -> str:
    """Fetch multiple instructions in a single call. Provide comma-separated ids.
    
    Use after list_instructions_index or search_instructions when you need
    the full text of several instructions at once. More efficient than
    calling get_instructions_batch repeatedly.
    """
```

**Justificativa:** Reduz tool calls (de 8-12 para 1), melhorando DX (critério 9) sem afetar qualidade. Mais importante: facilita o modelo a de facto ler todas as instructions relevantes em vez de parar nas primeiras 5 por "fadiga de round-trips".

**Risco:** Médio. Payload grande se muitas instructions forem solicitadas. Mitigação: `max_chars_per_instruction` com default conservador e cap total de retorno.

**Impacto em testes:** Novos testes unitários + smoke test para batch com 3+ IDs, edge cases (ID inexistente no batch, lista vazia).

### Frente 4 — Ajustes no prompt de orquestração (Critério 4)

**Status: CONCLUÍDO** — Ajustes já aplicados em `copilot-instructions-mcp.md`.

Resumo do que foi alterado:
- Passo 1: `list_instructions_index` obrigatório.
- Passo 2: múltiplas buscas por tema.
- Passo 3: leitura de todas as instructions relevantes.
- Passo 4: cruzamento policy×código com conservadorismo.
- Passo 5: rastreabilidade (IDs + arquivos).

**HIPÓTESE:** O ajuste no prompt é suficiente para resolver o Critério 4 sem mudanças nas tools. O cruzamento policy×código é uma decisão do modelo, não do servidor. As tools fornecem dados; o prompt guia o raciocínio.

**Como validar:** Re-executar o experimento com o prompt ajustado e tools inalteradas. Se o Critério 4 subir para >=8, o prompt foi suficiente. Se não, avaliar se uma tool de `check_applicability` é necessária (escopo futuro, não desta iteração).

---

## Delivery / Validation

### Entregáveis

| # | Entregável | Arquivo(s) | Tipo |
|---|---|---|---|
| 1 | `search_instructions` com default 10, cap 20 | `server.py` | Mudança em tool existente |
| 2 | Expansão de query com sinônimos | `indexing.py` | Mudança em módulo existente |
| 3 | Campo `related_ids` no retorno de `search_instructions` | `server.py` | Mudança em tool existente |
| 4 | Campo `by_tag` no retorno de `list_instructions_index` | `server.py` | Mudança em tool existente |
| 5 | Nova tool `get_instructions_batch` | `server.py` | Nova tool |
| 6 | Testes unitários para sinônimos, batch, by_tag | `tests/test_indexing.py`, `tests/smoke_test.py` | Novos testes |
| 7 | Teste de integração para batch | `tests/integration_mcp_stdio_test.py` | Novo teste |
| 8 | Prompt ajustado | `copilot-instructions-mcp.md` | **CONCLUÍDO** |

### Critérios de validação

#### Validação técnica (antes do experimento)
1. `pytest` passa (todos os testes existentes + novos).
2. `ruff check` e `mypy` sem erros.
3. Smoke test: `search_instructions("persistência SQL")` retorna `microservice-data-access-and-sql-security` (hoje não retorna).
4. Smoke test: `list_instructions_index()` inclui campo `by_tag` com agrupamento correto.
5. Smoke test: `get_instructions_batch(ids="microservice-architecture-layering,microservice-rest-http-semantics-and-status-codes")` retorna 2 corpos.

#### Validação experimental (re-execução)
1. Re-executar o cenário MCP com prompt ajustado + tools melhoradas.
2. Medir: `qtd_instructions_consultadas` deve ser >= 8 (era 5).
3. Medir: `qtd_arquivos_citados` deve ser >= 12 (era 7).
4. Avaliar Critério 2: nota deve ser >= 9.
5. Avaliar Critério 4: nota deve ser >= 8 (decisão de cache deve ser conservadora).

---

## Ordem de execução recomendada

| Passo | Entregável | Dependência | Estimativa |
|---|---|---|---|
| 1 | #1 — Default max_results 10, cap 20 | Nenhuma | ~10 min |
| 2 | #2 — Sinônimos na busca | Nenhuma | ~30 min |
| 3 | #3 — `related_ids` no search | #2 (usa tags para relação) | ~20 min |
| 4 | #4 — `by_tag` no list_instructions_index | Nenhuma | ~15 min |
| 5 | #5 — `get_instructions_batch` | Nenhuma | ~30 min |
| 6 | #6 + #7 — Testes | #1-#5 | ~30 min |

**Total estimado:** ~2h15 de implementação + testes.

---

## Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Sinônimos introduzem falsos positivos | Média | Médio | Limitar a 3-5 sinônimos por termo; peso 50% do match direto; testar com corpus real |
| Payload grande no batch | Baixa | Baixo | `max_chars_per_instruction` com default 8000; cap total em `get_instructions_batch` |
| Prompt melhorado mas modelo ignora instruções | Média | Alto | Validar no experimento; se necessário, tornar passos mais prescritivos |
| Melhoria do prompt resolve Critério 4 mas não Critério 2 | Baixa | Médio | As melhorias de tools (frentes 1-3) atacam Critério 2 diretamente |

---

## Fora de escopo desta iteração

- **Tool `check_instruction_applicability`**: avaliada como desnecessária se o prompt de conservadorismo funcionar. Reavaliação após experimento.
- **Busca semântica (embeddings)**: requer dependência pesada (sentence-transformers, OpenAI embeddings). Sinônimos manuais são suficientes para corpus de 24 instructions.
- **MCP Resources**: o protocolo suporta resources, mas o Copilot Chat do VS ainda não os consome de forma previsível. Foco em tools.
- **Transporte HTTP**: mantém stdio conforme roadmap existente.
