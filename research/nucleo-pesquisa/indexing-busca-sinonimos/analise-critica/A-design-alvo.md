# A — Design alvo

Pseudodiagrama e descrição estrutural da arquitetura de busca recomendada, construído incrementalmente ao longo das Fases 1–3 de [`analise-arquitetural.md`](analise-arquitetural.md) §6.

O desenho **não** requer runtime externo nem dependências pesadas. Todas as interfaces são Python puro + YAML + filesystem, preservando as propriedades operacionais atuais do MCP.

## Objetivos do desenho

1. Desacoplar **dado** (vocabulário, aliases, tags) de **mecanismo** (ranking, expansão).
2. Tornar cada estágio **substituível** via `Protocol` sem reescrever o consumidor.
3. Tornar o ranking **explicável**: cada pontuação vem com uma decomposição rastreável.
4. Evitar **contaminação cross-domínio** por construção (FIX ≠ RabbitMQ).
5. Manter `search_instructions` **estável em contrato JSON** — evolução por campos opcionais.

## Diagrama de componentes

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            INSTRUCTIONS_ROOT/                              │
│  ├── *.md               (documentos; frontmatter pode ter `aliases:`)      │
│  └── _vocabulary/                                                          │
│       ├── global.yaml                    (transversal, peso 0.4)           │
│       ├── messaging-rabbitmq.yaml        (domínio, peso 0.5)               │
│       ├── messaging-fix.yaml             (domínio)                         │
│       ├── frontend-web.yaml                                                │
│       ├── mobile-flutter.yaml                                              │
│       └── ...                                                              │
└────────────────────────────────────────────────┬───────────────────────────┘
                                                 │ filesystem
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                             build_index(root)                              │
│  ─ parse markdown + frontmatter (inclui `aliases:`)                        │
│  ─ load _vocabulary/*.yaml via YamlVocabularyProvider                      │
│  ─ (Fase 2) constrói índice invertido token → postings                     │
│  ─ resultado: IndexBundle(                                                 │
│       records: dict[id, InstructionRecord],                                │
│       inverted: dict[str, list[Posting]]  # Fase 2                         │
│       doc_aliases: dict[id, set[str]],                                     │
│       vocabularies: VocabularyBundle,                                      │
│       stats: CorpusStats  # Fase 2: doc lengths, avgdl, df                 │
│     )                                                                      │
└────────────────────────────────────────────────┬───────────────────────────┘
                                                 │
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                       search_instructions(query, ...)                      │
│                                                                            │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────────────────┐ │
│  │ Tokenizer   │ →  │ QueryExpansion-  │ →  │ LexicalRanker              │ │
│  │  ─ split    │    │ Provider         │    │  ─ WordBoundary (F1)       │ │
│  │  ─ NFKD     │    │  ─ aliases (F1)  │    │  ─ BM25F       (F2)        │ │
│  │  ─ lower    │    │  ─ domain (F2)   │    └──────────────┬─────────────┘ │
│  └─────────────┘    │  ─ global        │                   │               │
│                     │  returns {term:  │    ┌──────────────▼─────────────┐ │
│                     │    weight,       │    │ MetadataBooster             │ │
│                     │    provenance }  │    │  ─ priority                 │ │
│                     └──────────────────┘    │  ─ tag exact (normalized)   │ │
│                                             │  ─ scope/kind affinity      │ │
│                                             └──────────────┬─────────────┘ │
│                                                            │               │
│                                             ┌──────────────▼─────────────┐ │
│                                             │ ScoreCombiner               │ │
│                                             │  ─ lex + meta → total       │ │
│                                             │  ─ ScoreTrace se debug=on   │ │
│                                             └──────────────┬─────────────┘ │
│                                                            │               │
│                                             ┌──────────────▼─────────────┐ │
│                                             │ (F3, opcional)              │ │
│                                             │ SemanticReranker(top_N)     │ │
│                                             │  ─ flag enable_semantic     │ │
│                                             │  ─ fastembed/onnx local     │ │
│                                             └──────────────┬─────────────┘ │
│                                                            │               │
│                                             ┌──────────────▼─────────────┐ │
│                                             │ ResultComposer              │ │
│                                             │  ─ excerpt, summary         │ │
│                                             │  ─ related_ids              │ │
│                                             │  ─ explain (se debug)       │ │
│                                             └─────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
```

## Fontes do vocabulário e precedência

| Fonte | Local | Ativação | Peso recomendado | Fase |
|-------|-------|----------|------------------|------|
| **Alias por documento** | frontmatter `aliases: [...]` do próprio `.md` | sempre; só impacta o doc que declara | **0.8** | **F1** |
| **Vocabulário de domínio** | `_vocabulary/<domain>.yaml` | quando `ctx.domains ∩ {domain}` ≠ ∅ | 0.5 | F2 |
| **Vocabulário global** | `_vocabulary/global.yaml` | sempre | 0.4 | F1 |
| **Dicionário hard-coded** | `SYNONYMS` em código | fallback se `global.yaml` ausente, **com warning** | 0.4 | F1 (transitório) |

A precedência (numericamente, pelo peso) materializa "mais específico vence". A soma não é normalizada — o `LexicalRanker` tem responsabilidade de saturação (já acontece hoje via `min(5.0, 0.25 * c)`; com BM25, vem natural).

## Schema YAML recomendado (`global.yaml` / `<domain>.yaml`)

```yaml
# _vocabulary/global.yaml
version: 1
metadata:
  domain: null            # null = global; string = nome do domínio
  owner: "platform-team"
  last_reviewed: "2026-04-15"
groups:
  - canonical: persistencia
    aliases: [dapper, sql, repositorio, data-access, query]
    notes: "PT↔EN + ORM comum"
  - canonical: observabilidade
    aliases: [opentelemetry, health, correlation, tracing]
  # ...
```

```yaml
# _vocabulary/messaging-rabbitmq.yaml
version: 1
metadata:
  domain: messaging-rabbitmq
  owner: "platform-messaging"
  activation_tags: [rabbitmq, messaging-amqp]     # ativa apenas se ctx casa
groups:
  - canonical: rabbitmq
    aliases: [amqp, broker, queue, iconnection, masstransit, mass-transit, ibus]
  - canonical: publish
    aliases: [publicar, publicação, enviar-evento]
    scope: rabbitmq       # só relevante neste domínio; protege contra vazamento
```

**Limites hard-coded no loader** (defesa contra corpus adversarial):

- Máximo 200 grupos por ficheiro.
- Máximo 30 aliases por grupo.
- Tamanho máximo do ficheiro: 256 KiB.
- Profundidade YAML limitada (evita bombas YAML) — reusar `yaml.safe_load`.

## Ativação condicional por domínio (F2)

```
SearchContext inputs:
  ─ tokens_originais (query)
  ─ tag_filter (parâmetro tags=)
  ─ matches em doc_aliases (antes do ranking)

ctx.domains = union(
    vocabulary_domain(t) for t in tokens_originais
      if t aparece em activation_terms de algum <domain>.yaml,
    d for d in domain_tags_from_tag_filter(tag_filter),
)

expansion_output =
  alias_expansion(doc-local, peso 0.8)  [F1]
  ⊕
  ⋃ domain_expansion(<d>, peso 0.5) for d in ctx.domains  [F2]
  ⊕
  global_expansion(peso 0.4)  [F1]
```

**Propriedade de não-contaminação:** se `ctx.domains` é `{messaging-rabbitmq}`, o ficheiro `_vocabulary/messaging-fix.yaml` **não** é consultado. O resultado é garantidamente livre de FIX ativado por query RabbitMQ.

**Propriedade de cobertura:** queries sem domínio inferido continuam a funcionar via global + aliases de cada doc individualmente; o ranking apenas não ganha expansão de domínio específico.

## Fluxo de dados (Fase 1, sem BM25)

```
query = "persistência sql"

tokens      = ["persistencia", "sql"]                       # após normalização

expansion   = {                                             # Fase 1
  "persistencia": 1.0,                                      # direto
  "sql":          1.0,                                      # direto
  "dapper":       0.4,  # via global
  "repositorio":  0.4,  # via global
  "data-access":  0.4,  # via global
  "query":        0.4,  # via global
  # + aliases locais de qualquer doc casados pelo nome
}

ranking:
  for rec in records:
    if tag_filter and not match: skip
    lex = word_boundary_count_rank(rec, expansion)
    meta = metadata_boost(rec)                              # priority, tag exact
    score = lex + meta
    trace = ScoreTrace(...)   # se debug

sort desc; take top max_results.
```

## Fluxo de dados (Fase 2, BM25-F + domínios)

```
query = "rabbitmq publicar evento"

tokens = ["rabbitmq", "publicar", "evento"]

ctx.domains = {"messaging-rabbitmq"}     # inferido: "rabbitmq" aparece em
                                         # activation_terms de messaging-rabbitmq.yaml

expansion = {
  "rabbitmq": 1.0,
  "publicar": 1.0,
  "evento":   1.0,
  "amqp":       0.5,  # via messaging-rabbitmq
  "broker":     0.5,
  "publish":    0.5,  # canonical EN
  "masstransit":0.5,
  # global pode não aportar nada aqui
}

# messaging-fix.yaml NÃO é consultado — por construção.

ranker: BM25F por campos (title w=3, tags w=2, body w=1)
meta boost: priority, tag exact, scope compatibility

result: ordena por (lex_bm25f + meta); returna top N.
```

## Contrato de saída (`search_instructions`) — retrocompatibilidade

O JSON atual mantém:

```json
{
  "results": [
    {
      "source": "...",
      "id": "...",
      "relevance": 0.0,
      "score": 0.0,
      "summary": "...",
      "key_excerpt": "...",
      "full_available": true,
      "tags": [],
      "kind": "...",
      "related_ids": []
    }
  ],
  "composed_context": "..."
}
```

Campos **novos e opcionais** a introduzir:

- `explain` (apenas se `debug=true` no parâmetro ou flag do servidor):
  ```json
  "explain": {
    "expanded_terms": {"rabbitmq": 1.0, "amqp": 0.5, "...": "..."},
    "provenance": {"amqp": "messaging-rabbitmq.yaml", "persistencia": "global.yaml"},
    "score_components": {
      "lexical": 12.34,
      "metadata": 1.50,
      "semantic_rerank": null
    },
    "truncated_synonyms": false
  }
  ```
- `ranker` (string): identificador do ranker usado, ex. `"word-boundary-v1"`, `"bm25f-v1"`.

Consumidores atuais (incluindo o próprio IDE/Copilot) continuam a funcionar.

## Invariantes operacionais preservadas

- `build_index` permanece síncrono, em memória, sem rede.
- Não há persistência entre restarts além dos ficheiros .md e .yaml no filesystem.
- Defesas contra corpus adversarial mantidas (limite de bytes, escape de symlink, duplicate id).
- Contrato JSON de saída é aditivo apenas.

## Ligações

- Seções 5 e 6 da análise principal: [`analise-arquitetural.md`](analise-arquitetural.md).
- Interfaces `Protocol`: [`C-interfaces.md`](C-interfaces.md).
- Refatorações concretas: [`B-refatoracoes.md`](B-refatoracoes.md).
- Decisão arquitetural: [`D-adr.md`](D-adr.md).
