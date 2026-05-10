# ADR-003: `list_instructions_index` como catálogo filtrável, paginado e facetado (sem busca textual)

**Status**: Proposto (aguardando aprovação)  
**Data**: 2026-05-10  
**Contexto**: MCP `corporate_instructions_mcp` — tool `list_instructions_index`  
**Relaciona-se com**: [ADR-002 — Corpus Query Expansion Map](ADR-002-corpus-query-expansion-map.md) (expansão permanece exclusiva de `search_instructions`)

---

## 1. Título (resumo executivo)

Evoluir `list_instructions_index` de listagem completa implícita para **catálogo normativo filtrável por metadados**, com **paginação**, **facets opcionais**, **diagnóstico opcional** e **ordenação determinística**, preservando a fronteira arquitetural: **catálogo por metadados** versus **busca por intenção textual** em `search_instructions`.

---

## 2. Status

Proposto — documento preparado para revisão e aprovação antes de implementação encadeada ao [EPIC-11](../bmad/epicos/EPIC-11-list-instructions-index-catalog-filters-pagination.md).

---

## 3. Contexto

O MCP serve um corpus de ficheiros Markdown com frontmatter YAML. O campo `scope` no frontmatter é um **glob documental** (ex.: `**/*.cs`, `**/Api/**/*.cs`) — padrão já aceite; **não** se propõe, nesta ADR, separar `scope` conceptual de `applies_to` adicional no frontmatter das instructions.

Três tools base de leitura/descoberta:

| Tool | Papel |
|------|--------|
| `list_instructions_index` | Navegação e descoberta **estruturada** do catálogo por **metadados** |
| `search_instructions` | Recuperação por **intenção textual**, tokens, índice textual e **expansão de query** (Corpus Query Expansion Map, quando configurado) |
| `get_instructions_batch` | Carga de **conteúdo** completo ou parcial por identificadores |

**Estado atual do código** (referência): `list_instructions_index` em `mcp-instructions-server/corporate_instructions_mcp/server.py` devolve um **objeto** JSON com, entre outros, `instructions` (lista completa de metadados leves), `by_tag` (mapeamento tag → ids do corpus completo), `index_health`, `warnings`, `errors` e `status` de saúde do índice (`ok` / `partial` / `error`). A docstring ainda fala em “array JSON”, mas o payload já é estruturado — a evolução é **extensão e alteração semântica da página devolvida**, não a introdução do primeiro envelope JSON.

O problema principal, à medida que o corpus cresce (por exemplo 100+ ficheiros), não é só latência: é **interferência no contexto do agente** — listagens grandes incentivam escolha superficial por título, ignoram documentos específicos, substituem chamadas a `search_instructions` e inflacionam o prompt com metadados de baixa relevância.

---

## 4. Problema

1. Chamadas típicas sem filtros devolvem **todo** o catálogo em `instructions`, o que não escala em utilidade para o agente.  
2. A descrição atual da tool incentiva visão global (“overview of **all** available…”), reforçando o anti-padrão de listar tudo sempre.  
3. Falta **paginação explícita** e **filtros de metadados** no contrato da tool de listagem (filtros existem hoje sobretudo em `search_instructions`).  
4. Risco de **convergência acidental** entre `list_instructions_index` e `search_instructions` se a listagem ganhar `query`, ranking textual ou expansão.

---

## 5. Decisão

### 5.1 Frase-guia (obrigatória)

> **`list_instructions_index` deve ajudar o agente a navegar pelo catálogo normativo por metadados, enquanto `search_instructions` deve recuperar instructions por intenção textual e expansão de query.**

### 5.2 O que a tool passa a ser (e a não ser)

**É:** filtro por metadados estruturados, paginação, visão leve do catálogo, facets opcionais, diagnóstico opcional de filtros e paginação, ordenação **determinística** (prioridade, kind, id — ver secção 10), e opcionalmente `match_reason` quando filtros ou `current_file_path` esclarecem o motivo da inclusão (**explicação de filtro**, não score).

**Não é:** aceitar `query` textual; usar Corpus Query Expansion Map; usar `synonyms`; BM25; busca vetorial; ranquear por relevância textual; pesquisar o corpo das instructions; devolver conteúdo completo; substituir `search_instructions`.

### 5.3 Diferença obrigatória entre tools

| Tool | Responsabilidade | Entrada principal | Usa expansão? | Usa texto do corpo? | Retorno |
|------|------------------|-------------------|---------------|---------------------|---------|
| `list_instructions_index` | Catálogo por metadados | Filtros estruturados | Não | Não | Metadados **paginados** (+ facets/diagnostics opcionais) |
| `search_instructions` | Busca por intenção | Query textual (+ filtros auxiliares) | Sim, **quando configurada** no pipeline de busca | Sim / índice textual | Resultados ranqueados |
| `get_instructions_batch` | Carregar conteúdo | ids | Não | Sim | Conteúdo completo ou parcial **mantendo o mesmo vocabulário de metadados** |

### 5.3.1 Regra de linguagem ubíqua entre as três tools

Os nomes de metadados e filtros devem formar uma **linguagem ubíqua única** em `mcp-instructions-server`.

Regra normativa:

> **Se duas ou três tools expõem o mesmo nome de campo, esse nome deve preservar o mesmo tipo, a mesma normalização e o mesmo significado.**

Isto aplica-se a `tags`, `tags_mode`, `kind`, `scope`, `priority`, `status`, `owner`, `workspace_evidence_required`, `current_file_path`, `content_sha256`, `frontmatter`, `id`, `path` e `title`, sempre que esses campos existirem na tool em causa.

Consequência arquitectural:

- as três tools podem ter **objectivos diferentes**;
- as três tools **não** podem redefinir o significado de um mesmo termo;
- diferenças entre tools devem existir apenas em:
  - modo de recuperação (`list` vs `search` vs `batch`);
  - parâmetros exclusivos do modo (`query`, `limit`, `offset`, `ids`, etc.);
  - campos de retorno específicos do modo (`facets`, `relevance`, `content`, etc.).

### 5.4 `scope`, `current_file_path` e vocabulário comum

- `scope` deve ter o **mesmo significado nas três tools**: valor do metadado declarado no frontmatter, normalmente um glob documental como `**/*.cs` ou `**/Api/**/*.cs`.  
- `current_file_path` deve ter o **mesmo significado nas tools que o aceitarem**: path runtime do ficheiro em contexto, usado para avaliar se o `scope` declarado pela instruction se aplica ao ficheiro actual.  
- `workspace_evidence_required`, quando exposto, deve manter o mesmo significado nas tools: metadado/frontmatter que exige evidência do workspace para aplicação segura da instruction.  
- `scope` **não** deve significar “arquivo actual” numa tool e “glob declarado” noutra; para match entre glob e ficheiro, o campo correcto é `current_file_path`.

- `scope` no filtro da tool: corresponde ao valor declarado no frontmatter (glob documental), com semântica de **igualdade de string normalizada** em todas as tools que exponham esse filtro.  
- `current_file_path` (opcional): path do ficheiro em contexto; a tool **compara** esse path ao glob de `scope` de cada instruction (semântica de correspondência glob ↔ path normalizado). Isto **não** é busca semântica sobre nomes de classe ou domínio.  
- `include_non_matching_global`: quando `true` junto com outros filtros, permite incluir entradas que não casam o path mas satisfazem filtros explícitos (comportamento a detalhar na implementação para evitar surpresas).

### 5.5 Facets e `limit: 0`

**Decisão proposta**: permitir `limit: 0` **apenas** quando `include_facets: true`, para obter agregados do catálogo (ou do conjunto filtrado) **sem** devolver linhas em `items` / página de `instructions`. Caso `include_facets` seja `false` e `limit` seja `0`, a implementação deve rejeitar ou tratar como erro de validação (evitar chamadas ambíguas).

### 5.6 Relação com `by_tag` existente

Hoje `by_tag` agrega **todo** o índice. Com filtros, counts por tag devem refletir preferencialmente o **conjunto filtrado** (coerente com facets). **Decisão proposta**: manter `by_tag` apenas se for redefinido para o conjunto filtrado **ou** deprecar gradualmente em favor de `facets.tags` + documentação; o épico escolhe uma das duas e atualiza testes em conformidade.

---

## 6. Alternativas consideradas

| Alternativa | Síntese | Veredito |
|-------------|---------|----------|
| **A — Manter como está** | Zero custo de migração | **Rejeitada** — não escala em qualidade de contexto para o agente |
| **B — Fundir com busca** | Adicionar `query`, expansão ou ranking à listagem | **Rejeitada** — duplica e obscurece `search_instructions` |
| **C — Nova tool só para facets** (`get_instructions_catalog_facets`) | Separação limpa | **Adiável** — `include_facets` cobre o MVP; reavaliar se a tool ficar sobrecarregada |
| **D — `list_instructions_index_v2`** | Nova tool, contrato limpo | **Reserva** — usar se integrações externas exigirem contrato imutável; custo de superfície dupla |
| **E — Evolução in-place** | Mesmo nome; envelope estendido; limite por defeito | **Preferida** com plano de compatibilidade (secção 12) e notas de migração |

---

## 7. Consequências positivas

- Menos ruído no contexto do agente; fluxo “facet overview → filtrar → `get_instructions_batch`” fica explícito.  
- Fronteira normativa clara com `search_instructions` e com a ADR-002.  
- Melhor comportamento determinístico (ordenação fixa, sem scores textuais na listagem).

---

## 8. Consequências negativas / custos

- **Mudança de contrato**: clientes que assumem que `instructions` contém sempre o corpus completo deixam de o poder assumir sem paginação ou limite elevado explícito.  
- **Testes e scripts** (smoke, integração, orquestração) que validam `count` igual ao total deixam de ser válidos sem ajuste.  
- Filtros `status` / `owner` podem exigir leitura consistente a partir de `raw_frontmatter` até o modelo `InstructionRecord` expuser campos de primeira classe.

---

## 9. Contrato proposto (argumentos da tool)

A tool aceita **apenas** filtros estruturados (nenhum campo `query`).

```json
{
  "type": "object",
  "properties": {
    "tags": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Tags separadas por vírgula. Filtragem por metadados; não é busca textual."
    },
    "tags_mode": {
      "type": "string",
      "enum": ["any", "all"],
      "default": "any"
    },
    "kind": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null },
    "scope": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Glob documental do frontmatter (ex.: **/*.cs)."
    },
    "priority": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null },
    "status": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": "active",
      "description": "Filtra por status no frontmatter quando existir."
    },
    "owner": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null },
    "workspace_evidence_required": {
      "anyOf": [{ "type": "boolean" }, { "type": "null" }],
      "default": null,
      "description": "Filtra instructions cujo frontmatter exige evidência de workspace para aplicação segura."
    },
    "current_file_path": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Path do ficheiro atual; cruza com o glob scope de cada instruction."
    },
    "include_non_matching_global": {
      "type": "boolean",
      "default": false,
      "description": "Com current_file_path, permite incluir não correspondentes ao path se outros filtros assim o permitirem."
    },
    "limit": { "type": "integer", "default": 50, "minimum": 0, "maximum": 200 },
    "offset": { "type": "integer", "default": 0, "minimum": 0 },
    "include_facets": { "type": "boolean", "default": false },
    "include_diagnostics": { "type": "boolean", "default": false }
  },
  "required": [],
  "title": "list_instructions_indexArguments"
}
```

**Regras de validação adicionais (normativas para implementação):**

- Se `limit == 0`, então `include_facets` deve ser `true`.  
- Não introduzir propriedades abertas tipo “filtro genérico JSON” nesta versão (evita deslizar para motor de query arbitrário).

---

## 10. Semântica dos filtros e ordenação

- **tags + tags_mode**: `any` = pelo menos uma tag pedida está presente na instruction; `all` = a instruction contém todas as tags pedidas.  
- **kind / priority / scope / status / owner**: igualdade (com normalização de texto definida no código, alinhada ao restante do servidor).  
- **workspace_evidence_required**: igualdade booleana sobre o metadado derivado do frontmatter.  
- **Ordenação sem `current_file_path`**: `priority` (high → medium → low), depois `kind` (policy antes de reference, com desempate documentado para outros valores), depois `id` lexicográfico.  
- **Ordenação com `current_file_path`**: primeiro entradas cujo `scope` casa com o path, depois a mesma regra secundária.  
- **Proibido** na implementação: score textual, expansão, BM25, vetorial, heurística semântica de ranking.

---

## 11. Relação com `search_instructions`

- Tarefas de “o utilizador quer implementar X / erro Y / biblioteca Z” devem **preferir** `search_instructions` → `get_instructions_batch`.  
- `list_instructions_index` serve para inventário **por metadados**, “o que temos de kind X”, “o que aplica a este path”, ou visão agregada (facets).  
- `search_instructions` e `get_instructions_batch` devem reutilizar exactamente o mesmo vocabulário de metadados do catálogo; o que muda entre elas é o modo de recuperação, não o significado dos termos.  
- Nenhuma linha de código da listagem deve invocar o loader do Corpus Query Expansion Map nem pipelines de tokenização de busca.

---

## 12. Estratégia de compatibilidade

| Opção | Prós | Contras |
|-------|------|---------|
| Chamada sem argumentos + **limite por defeito** (ex.: 50) | Um só nome de tool; força uso responsável | Quebra clientes que esperavam lista completa implícita |
| Modo legado temporário (flag de ambiente) | Transição suave | Complexidade operacional |
| **`list_instructions_index_v2`** | Zero quebra para clientes antigos | Duplicação de manutenção e descoberta |
| Versionamento semântico do pacote + nota de migração | Clareza para consumidores | Requer comunicação |

**Decisão recomendada**: **Evolução in-place** com `limit` por defeito (50), `total_indexed` / `total_matched` / `has_more` explícitos, e **nota de migração** no CHANGELOG; reservar **v2** apenas se, durante implementação, surgir consumidor interno que não possa alterar contrato no mesmo ciclo.

O envelope existente (`status` de índice, `index_health`, `warnings`, `errors`, `corpus_version`) **mantém-se semanticamente**, mas recomenda-se renomear o campo de topo para `index_status` para evitar colisão com `status` do documento. Acrescentam-se campos de catálogo (`total_matched`, paginação, `facets`, `diagnostics`). O array paginado pode permanecer com a chave `instructions` **ou** introduzir `items` com período de duplicação documentado — preferência de implementação: **uma única chave canónica** na resposta final após migração dos testes (o épico fixa o nome).

---

## 13. Proposta de retorno (campos de catálogo)

Além dos campos já existentes para saúde do índice, o payload deve expor de forma explícita:

```json
{
  "index_status": "ok",
  "total_indexed": 124,
  "total_matched": 18,
  "limit": 50,
  "offset": 0,
  "has_more": false,
  "items": [
    {
      "id": "instruction-id",
      "path": "instruction-id.md",
      "title": "Título",
      "summary": "Resumo curto se existir no frontmatter",
      "tags": ["api", "rest"],
      "scope": "**/Api/**/*.cs",
      "priority": "medium",
      "kind": "policy",
      "status": "active",
      "owner": "platform-architecture",
      "content_sha256": "...",
      "match_reason": "scope matched current_file_path"
    }
  ],
  "facets": {}
}
```

**Nota**: se a implementação mantiver temporariamente `instructions` como sinónimo da página, documentar data de remoção.

**Campos por item (metadados leves):** `id`, `path`, `title`, `summary` (opcional), `tags`, `scope`, `priority`, `kind`, `status`, `owner` (opcional), `workspace_evidence_required` (opcional), `content_sha256`, `match_reason` (opcional).

**Não retornar:** corpo markdown completo, snippets longos, regras completas (isso é `get_instructions_batch`).

---

## 14. Nova descrição da tool (texto para docstring / registo MCP)

```text
Use this tool to inspect and filter the metadata catalog of available instruction documents.

This tool is for catalog discovery and metadata filtering only. It does not search instruction content and does not expand query terms.

Prefer search_instructions when the task has a specific intent, topic, technology, error, implementation goal, or natural-language query.

Use filters such as tags, kind, scope, priority, status, owner, or current_file_path whenever possible to avoid listing unrelated instructions.

Use pagination for large catalogs. Do not request the full catalog unless the user explicitly asks for a complete inventory.

Call get_instructions_batch only after selecting relevant ids.
```

A descrição antiga que incentiva “overview of **all**” deve ser **substituída** por esta ou equivalente aprovada em revisão.

---

## 15. Plano de implementação (fases de alto nível)

1. **Fase 1** — Filtros e paginação (`tags`, `tags_mode`, `kind`, `scope`, `priority`, `status`, `owner`, `limit`, `offset`).  
2. **Fase 2** — Envelope de resposta com `total_indexed`, `total_matched`, `has_more` e página única de resultados; ajuste de testes e integrações.  
3. **Fase 3** — `include_facets` com contagens (kind, priority, tags, scope, status), limite superior de cardinalidade (top N) se necessário.  
4. **Fase 4** — `current_file_path`, normalização de path, `match_reason`, `include_non_matching_global`, diagnóstico de correspondência de scope.  
5. **Fase 5** — Documentação (`README`, `docs/TESTS.md`), descrição da tool, orquestrações que sugerem `args: {}` para listagem completa, e fixture opcional com 100+ ficheiros para teste de escala.

---

## 16. Critérios de aceite (fecho da ADR)

A decisão considera-se **implementada** quando:

1. `list_instructions_index` suporta filtros por metadados conforme contrato.  
2. Suporta paginação com `limit` / `offset` / `has_more` / `total_matched` / `total_indexed`.  
3. Por defeito **não** devolve o corpus completo sem limite explícito (ou sem paginação que o substitua de forma equivalente).  
4. Continua a **não** devolver conteúdo completo da instruction.  
5. **Não** existe campo `query` na tool.  
6. **Não** usa expansão de query, Corpus Query Expansion Map, BM25 nem busca vetorial.  
7. Facets opcionais funcionam com `include_facets` e política para `limit: 0`.  
8. Documentação distingue claramente as três tools.  
9. Testes automatizados cobrem filtros, paginação, facets, `current_file_path` e ausência de sobreposição com `search_instructions`.  
10. Agentes são orientados pela descrição da tool a usar `search_instructions` para intenção textual.

---

## 17. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Quebra de compatibilidade por paginação | CHANGELOG, limite explícito para inventário completo, ou v2 se necessário |
| Tool virar “search disfarçada” | Revisão de código a proibir `query` / expansão; checklist em PR |
| Facets grandes (muitas tags) | `include_facets` opcional; top N; não retornar por defeito |
| Falsos negativos com `current_file_path` por `scope` mal curado | `include_diagnostics`; testes; fallback sem path; governação de corpus |
| Agente continua a chamar sem filtros | Limite por defeito; texto da tool; facets para overview |

---

## 18. Itens explicitamente fora do escopo

- BM25, busca vetorial, RAG.  
- Alterar semântica de `scope` no frontmatter para modelo conceptual + `applies_to` nas instructions (discussão fechada para esta ADR).  
- Campo `query` textual em `list_instructions_index`.  
- Expansão via Corpus Query Expansion Map na listagem.  
- Score textual ou ranking por relevância textual na listagem.  
- Retorno de conteúdo completo.  
- Grafo aberto de propriedades customizadas arbitrárias no contrato.

---

## 19. Referências

- Código: `mcp-instructions-server/corporate_instructions_mcp/server.py` (`list_instructions_index`, `search_instructions`).  
- Modelo de registo: `mcp-instructions-server/corporate_instructions_mcp/indexing.py` (`InstructionRecord`).  
- [ADR-002 — Corpus Query Expansion Map](ADR-002-corpus-query-expansion-map.md).  
- [EPIC-11 — Implementação desta evolução](../bmad/epicos/EPIC-11-list-instructions-index-catalog-filters-pagination.md).  
- `mcp-instructions-server/docs/UBIQUITOUS-LANGUAGE-GLOSSARY.md`.  
- Padrão de frontmatter: `fixtures/instructions/instruction-authoring-standard.md`.

---

## 20. Veredito da avaliação do plano de entrada

**Recomendado com ajustes** — a direção (catálogo versus busca) é a correcta para MCP orientado a agentes e alinha-se ao repositório; os ajustes obrigatórios são: alinhar a narrativa ao **payload actual** (objeto com `instructions`, não array isolado), decidir evolução de `by_tag` versus `facets`, e planear migração explícita de testes e orquestrações que assumem listagem completa implícita.
