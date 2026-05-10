# EPIC-11 — Catálogo `list_instructions_index`: filtros, paginação, facets e fronteira com `search_instructions`

## Objetivo

Implementar a [ADR-003](../../adr/ADR-003-list-instructions-index-catalog-metadata.md): evoluir `list_instructions_index` para um **catálogo filtrável por metadados**, **paginado**, com **facets** e **diagnóstico opcionais**, preservando a regra de que **não** é ferramenta de busca textual nem de expansão de query.

## Motivação

Corpora grandes expõem demasiados metadados de uma só vez, degradando a qualidade das decisões do agente e desviando fluxos que deveriam usar `search_instructions` + `get_instructions_batch`. É necessário reduzir volume por defeito e tornar explícitos total filtrado, página e agregados.

## Escopo

### Em escopo

- Parâmetros da tool: `tags`, `tags_mode`, `kind`, `scope`, `priority`, `status`, `owner`, `workspace_evidence_required`, `limit`, `offset`, `include_facets`, `include_diagnostics`, `current_file_path`, `include_non_matching_global` (sem campo `query`).  
- Resposta: campos de paginação (`total_indexed`, `total_matched`, `limit`, `offset`, `has_more`) + página de itens com metadados leves; opcionalmente `summary`, `workspace_evidence_required` e `match_reason` quando aplicável.  
- Ordenação determinística conforme ADR-003.  
- Glob matching de `current_file_path` contra `scope` (path normalizado).  
- Facets: contagens por `kind`, `priority`, `tags`, `scope`, `status` no **conjunto filtrado** (com política de top N se a cardinalidade explodir).  
- Política `limit == 0` apenas com `include_facets == true`.  
- Manter envelope de saúde do índice existente, com alinhamento de nomenclatura para evitar colisão com `status` do documento (`index_status`, `index_health`, `warnings`, `errors`, `corpus_version`).  
- Decisão técnica documentada: evolução de `by_tag` (restrito ao conjunto filtrado vs. deprecação em favor de `facets.tags`).  
- Atualização da docstring / descrição registada no MCP (texto da ADR-003).  
- Criação e adopção do glossário operativo em `mcp-instructions-server/docs/UBIQUITOUS-LANGUAGE-GLOSSARY.md` como fonte normativa de linguagem ubíqua entre `list_instructions_index`, `search_instructions` e `get_instructions_batch`.  
- Atualização de `mcp-instructions-server/README.md`, `docs/TESTS.md` e referências em scripts que assumem listagem completa.  
- Testes: unitários e smoke/integração; fixture opcional com 100+ ficheiros gerados em teste ou corpus dedicado de teste.

### Fora do escopo

- BM25, embeddings, busca vetorial, RAG.  
- Query textual ou expansão (Corpus Query Expansion Map, sinónimos) em `list_instructions_index`.  
- Alteração do significado de `scope` no frontmatter das instructions (glob documental mantém-se).  
- Nova tool `list_instructions_index_v2` **só** se a ADR for emendada após prova de impossibilidade de migração in-place.

## Princípios de implementação

- Uma fase de cada vez; testes verdes entre merges.  
- Nenhuma chamada de `list_instructions_index` a código de expansão ou scoring de `search_instructions`.  
- Reutilizar, quando fizer sentido, helpers de normalização já usados noutras tools (sem acoplar ao motor de busca).
- Mesmo nome, mesmo significado: se um campo existir em duas ou três tools, deve conservar o mesmo tipo e a mesma semântica.

## Fases

| Fase | Conteúdo |
|------|-----------|
| **1** | Filtros de metadados + `limit`/`offset` + ordenação determinística |
| **2** | Envelope `total_indexed` / `total_matched` / `has_more` + migração da chave da página (`instructions` vs `items`) acordada na ADR |
| **3** | `include_facets` + política de cardinalidade + `limit: 0` condicionado |
| **4** | `current_file_path` + `match_reason` + `include_non_matching_global` + diagnósticos de scope |
| **5** | Documentação, descrição da tool, sugestões em `suggested_next_call` que hoje pedem `{}`, bateria de testes e fixture de escala |

## Tasks técnicas (checklist)

- [ ] Mapear `InstructionRecord` / `raw_frontmatter` para expor `status`, `owner`, `summary` de forma consistente na listagem.  
- [ ] Alinhar `scope`, `current_file_path`, `status`, `workspace_evidence_required`, `owner` e `tags_mode` com a mesma semântica usada ou desejada nas três tools.  
- [ ] Implementar parsing de argumentos MCP (parâmetros opcionais com defaults da ADR).  
- [ ] Implementar pipeline: índice completo → filtros → ordenação → janela `[offset, offset+limit)`.  
- [ ] Implementar facets sobre o conjunto **pós-filtro** (antes da paginação de itens).  
- [ ] Implementar `include_diagnostics` (filtros aplicados, contagens matched/unmatched de scope quando relevante, paginação).  
- [ ] Resolver `by_tag` vs facets e atualizar consumidores internos.  
- [ ] Renomear o campo de topo `status` para `index_status` na listagem, com estratégia de compatibilidade documentada.  
- [ ] Garantir que `get_instructions_batch` devolve o mesmo vocabulário canónico de metadados sempre que os campos existirem no item e/ou no `frontmatter`.  
- [ ] Atualizar `tests/smoke_test.py`, `tests/integration_mcp_stdio_test.py`, `scripts/run_epic05_stdio_real_check.py` e quaisquer asserts de `count` total.  
- [ ] Atualizar telemetria / métricas de `list_instructions_index.completed` para refletir `total_matched` e tamanho da página.  
- [ ] CHANGELOG com nota de migração para clientes.

## Testes (plano mínimo)

1. **Compatibilidade básica**: chamada com argumentos mínimos não gera erro; respeita `limit` por defeito; resposta inclui campos de saúde do índice preservados.  
2. **Filtros**: `kind`, `priority`, `status`, `scope`, `tags` any/all, `owner`, `workspace_evidence_required`.  
3. **Paginação**: `limit`, `offset`, `has_more`, `total_matched`, `total_indexed`.  
4. **Facets**: ausente por defeito; presente quando solicitado; `limit: 0` + facets conforme política.  
5. **`current_file_path`**: `.cs` casa `**/*.cs`; `.md` casa `**/*.md`; glob tipo `**/appsettings*.json` quando presente no corpus de teste.  
6. **Não sobreposição com search**: ausência de parâmetro `query`; teste estático ou de importação garantindo que o módulo da listagem não importa loader do mapa de expansão (ou equivalente acordado com revisão).  
7. **Linguagem ubíqua**: testes de contrato confirmam que campos com o mesmo nome mantêm o mesmo significado entre `list_instructions_index`, `search_instructions` e `get_instructions_batch`.  
8. **Escala**: corpus de teste com 100+ entradas sintéticas (ou geradas) valida tempo/memória aceitáveis em CI.

## Critérios de aceite (épico)

- [ ] Todos os critérios da ADR-003 (secção 16) satisfeitos.  
- [ ] `pytest -q` no servidor MCP sem regressões não explicadas.  
- [ ] Documentação atualizada com a tabela de fronteira entre as três tools.  
- [ ] Fluxos documentados: (a) overview por facets; (b) policies C# ativas; (c) aplicáveis ao ficheiro corrente; (d) tarefa por intenção → `search_instructions`.

## Riscos

- Iguais à ADR-003 (compatibilidade, facets grandes, `scope` mal curado, agente sem filtros).  
- Risco de implementação: divergência entre contagem em `by_tag` e `facets` — mitigar com uma única fonte de verdade no código.

## Plano de rollback

- Reverter commit(s) da feature; manter branch de backup.  
- Se libertação já ocorreu: reintroduzir limite elevado temporário atrás de flag de configuração apenas se a ADR for emendada para o permitir.

## Métricas de sucesso

- Redução mediana do tamanho em caracteres da resposta de `list_instructions_index` em chamadas sem filtros explícitos (baseline vs. após), medida em teste ou telemetria agregada sem conteúdo sensível.  
- Zero ocorrências de `query` no schema da tool.  
- Cobertura de testes novos ≥ casos listados na secção Testes deste épico.

## Referências cruzadas

- [ADR-003 — decisão](../../adr/ADR-003-list-instructions-index-catalog-metadata.md)  
- [EPIC-02 — Servidor MCP](EPIC-02-mcp-server.md) (contexto histórico)  
- [EPIC-10 — Expansion Map](EPIC-10-corpus-query-expansion-map.md) (fronteira com expansão)
