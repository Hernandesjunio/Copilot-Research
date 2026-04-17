# Análise arquitetural — indexação e expansão por sinónimos

> **Referência de código.** Todas as citações desta análise apontam para [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) e para o consumidor [`corporate_instructions_mcp/server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py) no ponto em que a tool `search_instructions` chama o ranker.

---

## 1. Visão geral do funcionamento atual

A ingestão e a busca do MCP seguem um fluxo linear, totalmente in-process, sem índice invertido e sem qualquer persistência entre chamadas além do cache de módulo (`_index`, `_index_root` em `server.py`).

### 1.1 Ingestão — `build_index(root)`

```103:148:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def build_index(root: Path) -> dict[str, InstructionRecord]:
    """Load all ``*.md`` under ``root`` (recursive). Keys are document ids (must be unique).
    ...
    """
    root = root.resolve()
    if not root.is_dir():
        return {}

    by_id: dict[str, InstructionRecord] = {}
    for path in sorted(root.rglob("*.md")):
        ...
        rec = _parse_markdown(path, root)
        ...
        by_id[rec.id] = rec
    ...
    return by_id
```

- Percorre `*.md` recursivamente sob `INSTRUCTIONS_ROOT` (definido em `paths.py`/`server.py`).
- Aplica **três defesas explícitas contra abuso do corpus** (`MAX_INSTRUCTION_FILE_BYTES = 5 MiB`, `MAX_FRONTMATTER_SECTION_CHARS = 65536`, `is_path_under_root` para escape via symlink).
- IDs duplicados são **erro fatal** (`raise ValueError`) — o índice tem contrato de unicidade por documento.
- **Fato observado:** não há índice invertido (token → documentos). O dicionário retornado é `id → InstructionRecord` e a busca varre todos os registos em tempo linear.

### 1.2 Parsing — `_parse_markdown(path, root)`

```50:100:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def _parse_markdown(path: Path, root: Path) -> InstructionRecord:
    text = path.read_text(encoding="utf-8", errors="replace")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    ...
    parts = FRONTMATTER_SPLIT.split(text, maxsplit=2)
    if len(parts) >= 3 and parts[0].strip() == "":
        ...
        loaded = yaml.safe_load(fm_raw)
        meta = loaded if isinstance(loaded, dict) else {}
        ...
    ...
    return InstructionRecord(
        id=doc_id, rel_path=rel, title=title, tags=tags,
        scope=scope, priority=priority, kind=kind,
        body=body.strip(), content_hash=h, raw_frontmatter=meta,
    )
```

- Frontmatter YAML em `--- ... ---` no topo do ficheiro; delimitador regex `FRONTMATTER_SPLIT`.
- Metadados extraídos: `id`, `title`, `tags` (lista de strings lowercased), `scope`, `priority`, `kind`. `raw_frontmatter` preserva o dicionário completo (inclusive chaves como `workspace_signals`, `workspace_evidence_required`, `on_absence` presentes nos fixtures).
- **Fato observado:** o frontmatter dos fixtures já declara sinais específicos por documento — por exemplo, `microservice-messaging-rabbitmq-publish-consume.md` tem `workspace_signals: [RabbitMQ, IConnection, RabbitMQ.Client, MassTransit, AddMassTransit, IBus]`. **Estes sinais não são consumidos pelo ranker atual** (voltaremos a isto em §2 e §5).

### 1.3 Tokenização — `tokenize_query` e `_normalize_token`

```151:152:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def tokenize_query(q: str) -> list[str]:
    return [t for t in re.split(r"\W+", q.lower()) if len(t) > 1]
```

```171:174:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def _normalize_token(token: str) -> str:
    normalized = unicodedata.normalize("NFKD", token)
    no_diacritics = "".join(c for c in normalized if not unicodedata.combining(c))
    return no_diacritics.lower()
```

- `tokenize_query` divide por qualquer não-alfanumérico, descarta tokens de tamanho ≤ 1. **Não há stopwords, stemming, lemmatization nem fronteira de palavra preservada.**
- `_normalize_token` é usado **apenas no lookup de sinónimos**, não no scoring do corpo/título. O documento "Persistência — SQL" vs a query "persistencia" casam porque o corpo é convertido em `.lower()` (em `search_blob`) e porque o lookup de sinónimos normaliza ambos os lados; mas o scoring lexical propriamente dito **não** normaliza diacríticos dos tokens contra o blob — isto é assimétrico e subtil.

### 1.4 Expansão por sinónimos — `SYNONYMS`, `_build_synonym_lookup`, `expand_query_with_synonyms`

```157:168:mcp-instructions-server/corporate_instructions_mcp/indexing.py
SYNONYMS: dict[str, list[str]] = {
    "cache": ["imemorycache", "idistributedcache", "caching", "ttl", "invalidation"],
    "persistencia": ["dapper", "sql", "repositorio", "data-access", "query"],
    "validacao": ["validation", "error-contracts", "400", "422"],
    "http": ["rest", "status-codes", "get", "put", "post", "delete", "endpoint"],
    "resiliencia": ["polly", "retry", "circuit-breaker", "timeout", "tolerancia"],
    "arquitetura": ["layering", "camadas", "clean-architecture", "solid"],
    "testes": ["testing", "unit", "integration", "contract"],
    "observabilidade": ["opentelemetry", "health", "correlation", "tracing"],
    "mensageria": ["rabbitmq", "messaging", "publish", "consume"],
    "seguranca": ["security", "secrets", "tokens"],
}
```

```177:187:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def _build_synonym_lookup(synonyms: dict[str, list[str]]) -> dict[str, list[str]]:
    lookup: dict[str, set[str]] = {}
    for canonical, related in synonyms.items():
        terms = [canonical, *related]
        normalized_terms = {_normalize_token(term): term for term in terms}
        for term_norm in normalized_terms:
            others = {other for other_norm, other in normalized_terms.items() if other_norm != term_norm}
            if not others:
                continue
            lookup.setdefault(term_norm, set()).update(others)
    return {key: sorted(values) for key, values in lookup.items()}
```

```193:201:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def expand_query_with_synonyms(tokens: list[str]) -> dict[str, float]:
    """Expand query tokens with related terms weighted lower than direct matches."""
    expanded: dict[str, float] = {}
    for token in tokens:
        expanded[token] = max(expanded.get(token, 0.0), 1.0)
        normalized = _normalize_token(token)
        for related in _SYNONYM_LOOKUP.get(normalized, [])[:5]:
            expanded[related] = max(expanded.get(related, 0.0), 0.5)
    return expanded
```

**Observações técnicas não-triviais** (que a observação inicial não capturou):

1. **A expansão é bidirecional, simétrica e transitiva no grupo.** `_build_synonym_lookup` cria, para cada termo do grupo, todas as relações para os demais. Consequência: querying **"rabbitmq"** expande para `{mensageria, messaging, publish, consume}`. Querying **"get"** expande para `{http, rest, status-codes, put, post, delete, endpoint}[:5]`. Todos os termos do mesmo grupo são considerados equivalentes a peso 0.5 — não existe direção canônica `termo genérico → específicos` ou vice-versa.

2. **Truncamento silencioso via `[:5]`.** Grupos maiores (ex.: `http` com 7 variantes) perdem termos silenciosamente. A ordem vem de `sorted(values)` em `_build_synonym_lookup` — a verdade de corte é alfabética, não semântica. Querying "http" perde `"rest"` e `"status-codes"` da expansão porque `sorted(["delete","endpoint","get","post","put","rest","status-codes"])[:5]` = `["delete","endpoint","get","post","put"]`.

3. **`_SYNONYM_LOOKUP` é construído no import do módulo.** Qualquer alteração a `SYNONYMS` exige reinicialização do processo. Não existe mecanismo de hot-reload nem parâmetro de inversão para testes — os testes em `test_indexing.py` validam o comportamento estático.

4. **`[:5]` não é configurável.** É um limite rígido, codificado, sem telemetria de quando ocorre truncamento.

### 1.5 Scoring — `score_record`

```204:220:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def score_record(rec: InstructionRecord, tokens: list[str], tag_filter: set[str] | None) -> float:
    if tag_filter and not (tag_filter & set(rec.tags)):
        return 0.0
    blob = rec.search_blob()
    score = 0.0
    title_l = rec.title.lower()
    for t, weight in expand_query_with_synonyms(tokens).items():
        c = blob.count(t)
        if c:
            score += weight * (1.0 + min(5.0, 0.25 * c))
        if t in title_l:
            score += weight * 3.0
        for tag in rec.tags:
            if t == tag or t in tag:
                score += weight * 2.0
    score += 0.5 * PRIORITY_RANK.get(rec.priority, 0)
    return score
```

**O que este trecho efetivamente calcula**, termo a termo:

- **`blob.count(t)`**: conta **ocorrências de substring** (não de palavra) no `search_blob`, que é `f"{title}\n{' '.join(tags)}\n{body}".lower()`. Diacríticos **não** são removidos do blob (apenas lowercase). Portanto querying "persistencia" **não** casa o corpo "persistência" via `blob.count`, **casa apenas via expansão para `dapper`/`sql`/etc.**
- **`t in title_l`** e **`t in tag`**: também substring. Querying "test" casa com tags hipotéticas `"latest"` ou `"contest"`.
- **Peso por ocorrência**: `1.0 + min(5.0, 0.25 * c)`. Um documento com 20 ocorrências de um termo atinge o teto (6.0 × peso). É uma saturação razoável, mas o termo expandido (peso 0.5) compete em pé quase igual ao direto (peso 1.0) quando a contagem é alta.
- **Boost de título**: 3× peso (aditivo por termo).
- **Boost de tag**: 2× peso por tag que contenha o termo como substring.
- **Boost de prioridade**: `0.5 × PRIORITY_RANK` (`high=3, medium=2, low=1, None=0`). Constante por documento, adicionado uma vez.

**Custo**: `O(|docs| × |tokens_expandidos| × (|blob| + |tags|))`. Para o corpus fixture (~26 ficheiros), é trivial. Não é este o problema.

### 1.6 Composição do resultado

No consumidor [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py) (linhas 178–238):

- Tokeniza a query; se vazia mas há `tags`, cai num ranking por prioridade+path.
- Caso contrário, calcula `score_record` para todos os documentos, filtra `score > 0`, ordena, pega `[:cap]`.
- Para cada hit produz `key_excerpt` via `excerpt_around_match(body, tokens)` — note-se: `tokens` crus, **sem** expansão por sinónimos, o que é coerente (o excerto deve mostrar o termo efetivamente pedido pelo utilizador, não o expandido).
- Monta `composed_context` concatenando `### {title} ({id})\n{summarize_body(body, 280)}`.

### 1.7 Resumo do fluxo ponta-a-ponta

```
INSTRUCTIONS_ROOT/*.md
  └─ build_index ──→ dict[id → InstructionRecord]      (parse YAML + body, enforça limites)

query (str)
  └─ tokenize_query ──→ [t1, t2, ...]
      └─ expand_query_with_synonyms(tokens)  ──→  {t: 1.0, related_i: 0.5, ...}  (cap [:5])
          └─ score_record(rec, tokens, tag_filter)  para cada doc
              └─ blob.count(t) (substring)   +   3×(t in title_l)   +   2×(t in tag)   +   0.5×priority
  └─ sort desc, [:cap]
      └─ excerpt_around_match(body, tokens_crus)
      └─ summarize_body
```

---

## 2. Limitações arquiteturais identificadas

Esta seção **separa defeitos de correção** (bugs de comportamento dentro do modelo atual) de **limitações de modelo** (o que o modelo, mesmo implementado perfeitamente, não consegue fazer). A observação inicial concentra-se no segundo grupo; o primeiro é igualmente real e mais urgente.

### 2.1 Defeitos de correção (presentes hoje, independentes de multi-domínio)

**L-1. Scoring por substring inflaciona falsos positivos para tokens curtos/genéricos.**
`blob.count("get")` casa `getter`, `widget`, `target`, `budget`. Combinado com a expansão de `"http"` que injeta `get/put/post/delete` na query, qualquer documento que discuta "getters em C#" ou "put de configuração" pontua por uma query semanticamente não-relacionada. O teste `test_score_record_boosts_related_domain_terms` em `test_indexing.py` valida o **sentido** do boost (direto > relacionado) mas **não** exerce este cenário adversarial.

**L-2. Expansão bidirecional trata todos os termos de um grupo como equivalentes.**
Não existe conceito de termo canônico → variantes ou termo específico → generalização. `rabbitmq ↔ mensageria ↔ messaging ↔ publish ↔ consume` são todos mutuamente equivalentes a peso 0.5. O impacto é duplo: (a) querying "rabbitmq" traz para cima documentos sobre outros brokers que usem a palavra `publish`, e (b) querying "publish" (um verbo genérico) ativa o ramo inteiro de mensageria. Este é exatamente o risco descrito na observação para o caso FIX/RabbitMQ — mas **já ocorre hoje** com os termos do grupo, antes de qualquer extensão de domínio.

**L-3. Truncamento `[:5]` silencioso e alfabético.**
Sem telemetria, sem aviso, sem teste. A ordem vem de `sorted(values)` em `_build_synonym_lookup`, logo é **alfabética**, não ponderada. Para o grupo `http`, "rest" e "status-codes" ficam fora da expansão — uma decisão arbitrária invisível.

**L-4. Inconsistência de normalização entre query e blob.**
`_normalize_token` (remoção de diacríticos + lowercase) é aplicado **apenas** na pesquisa do `_SYNONYM_LOOKUP`. O `search_blob` é só `.lower()`. Consequência: querying "persistência" **não encontra** a palavra "persistência" por `blob.count` se o token original mantiver os diacríticos — o casamento direto falha e o documento só entra na ranking via a expansão para `dapper/sql/...`. O teste `test_expand_query_with_synonyms_handles_accents` verifica que a expansão funciona, mas não detecta a assimetria.

**L-5. Substring matching em tags via `t in tag`.**
`"api" in "rest-api"` é desejável; `"test" in "latest"` ou `"ci" in "policia"` não é. O custo de suportar o primeiro caso é pagar todos os segundos. Tags são identificadores discretos — deveriam casar por igualdade exata (eventualmente com um normalizador de hífen/underscore).

**L-6. `_SYNONYM_LOOKUP` materializado no import.**
Não há parâmetro de injeção nem fábrica. Testes que queiram exercer outro vocabulário precisam de `monkeypatch` no módulo. Isso já viola um princípio básico de testabilidade e bloqueia qualquer hipótese de configuração externa sem refactor.

### 2.2 Limitações de modelo (o que a observação corretamente aponta)

**L-7. Vocabulário acoplado ao código.**
Adicionar ou ajustar termos exige PR no pacote Python, revisão de engenharia e redeploy. Em prática, **vocabulário é um artefato editorial** — deveria pertencer a quem domina o domínio (frontend, mobile, security). O mecanismo atual transforma curadoria de domínio em trabalho de equipa de plataforma, criando gargalo.

**L-8. Zero separação "mecanismo de busca" vs "conhecimento do domínio".**
`SYNONYMS` mistura conhecimento de domínio (C#/Polly/RabbitMQ), heurísticas linguísticas (PT↔EN) e convenções de tags do próprio repositório. Qualquer mudança num eixo força revisão dos outros.

**L-9. Sem governança, provenance nem versionamento semântico.**
Não sabemos **quem** adicionou "dapper" a `persistencia`, **quando**, **por que**, nem **para que domínio**. O `git blame` é a única fonte de verdade — adequado para código, insuficiente para léxico corporativo multi-equipa.

**L-10. Sem partição por domínio.**
Se uma equipa de trading adiciona `fix, fix-44, 4.4, sbe` ao grupo `mensageria`, essa expansão passa a contaminar queries do time que trabalha com RabbitMQ, e vice-versa. Não há mecanismo para dizer "este grupo de sinónimos só se aplica a documentos com tag `trading` ou `messaging-fix`". Este é o ponto central e correto da observação.

**L-11. `workspace_signals` e outras metadatas ricas do frontmatter são ignoradas.**
Cada documento fixture já declara sinais precisos do seu domínio (ver 1.2). O ranker atual não consome essa informação. Existe um vocabulário controlado **auto-declarado** no próprio corpus que está a ser ignorado em favor de um dicionário externo curado manualmente.

**L-12. Sem modelo de relevância estatístico (BM25/TF-IDF).**
Documentos longos e documentos curtos competem com a mesma escala de `blob.count`. Um documento de 300 linhas que cita "cache" 20 vezes casualmente pode bater um documento de 30 linhas inteiramente sobre `IMemoryCache`. A saturação `min(5.0, 0.25*c)` ameniza, mas não compensa a ausência de normalização por comprimento.

**L-13. Sem re-ranking nem separação de estágios.**
Hoje o scoring é um "one-shot" por documento. Não há estágio de recall (candidatos) seguido de precisão (re-ranking). Qualquer evolução semântica (embeddings, re-ranking cross-encoder, LLM-judge) encontra zero pontos de extensão.

### 2.3 O que a observação **não** captura

- O defeito **L-1** (substring counting) é, a meu ver, **mais urgente** que a governança de vocabulário. Multiplicar o vocabulário **sem** corrigir L-1 agrava o ruído não-linearmente.
- A confusão entre "FIX é como RabbitMQ" descrita na observação **não é um risco futuro hipotético** — a mecânica que a gera (expansão bidirecional via grupo) já opera no corpus atual para `publish/consume/rabbitmq/messaging`.
- A observação recomenda "desacoplar do código", o que é correto, mas não explicita que, **sem partição por domínio no momento da ranking**, desacoplar só muda o local onde o ruído é produzido.

---

## 3. Riscos práticos para uso corporativo

Riscos ordenados pela combinação probabilidade × impacto observável.

### R-1. Contaminação cruzada entre domínios (alto / alto)

Cenário: a equipa de trading adiciona instruções sobre FIX messaging. Para garantir recall, alguém adiciona `fix, fix44, sbe` ao grupo `mensageria`. Imediatamente, queries do time .NET sobre `rabbitmq` passam a trazer documentos FIX como resultados válidos (peso 0.5), e vice-versa. **O custo de manter o recall do domínio A degrada a precisão do domínio B.**

Mitigação que o modelo atual **não** suporta: vocabulário por domínio, com ativação condicionada à interseção `query.domains ∩ doc.domains` (via tags ou frontmatter).

### R-2. Viés de curadoria inicial (médio / alto)

O `SYNONYMS` atual cobre 10 temas, todos centrados em backend .NET. Um utilizador a fazer query sobre **frontend**, **mobile**, **observabilidade de browser**, **segurança ofensiva**, **governo de dados** não recebe nenhum ganho de expansão. **O ranker torna-se involuntariamente tendencioso em favor dos domínios cobertos.** Não é um bug, é uma decisão de curadoria implícita — mas invisível para quem sofre o viés.

### R-3. Falsos positivos por tokens genéricos (alto / médio)

`get`, `put`, `post`, `delete` são sinónimos de `http`. Uma query como "post-mortem review" (seguindo convenções DevOps) é tokenizada como `["post", "mortem", "review"]`, onde `post` aciona a expansão HTTP completa. Documentos sobre PUT/DELETE endpoints pontuam indevidamente. **O MCP responde algo plausível mas errado.**

### R-4. Falsos negativos por vocabulário ausente (alto / médio)

Sem entradas para `auth/oauth/oidc/jwt/scopes`, uma query "oauth scopes" só casa documentos que literalmente contenham essas strings, perdendo instruções sobre `AuthorizationPolicy`, `ClaimsPrincipal`, `Bearer`. A **baseline de recall** do MCP fica abaixo do que seria razoável esperar.

### R-5. Custo de manutenção e gargalo de equipa de plataforma (médio / alto)

Cada nova área técnica (frontend, mobile, database, security) demanda PR no pacote. O proprietário do vocabulário é a equipa que mantém o servidor MCP, não as equipas que produzem instruções. Isto cria um **funil artificial** que escala mal com adoção corporativa.

### R-6. Rankeamento não-explicável (médio / médio)

Quando um documento aparece no topo, não há trilha de *por que*: foi o boost de título? A expansão via sinónimo? A ocorrência de substring acidental em tag? Para ferramentas de assistente, **explicabilidade é requisito de confiança**. Hoje só é possível reconstituir com `pdb`.

### R-7. Ausência de regressão semântica (médio / médio)

`test_indexing.py` tem exatamente **um** teste que valida relação entre sinónimo e corpus real (`test_score_record_boosts_related_domain_terms`). Qualquer mudança em `SYNONYMS` ou em `score_record` pode degradar queries do mundo real sem falhar um único teste. **Não existe suite de golden queries.** (ver §7, refatoração R-T).

### R-8. Sem observabilidade do ranker (médio / baixo)

Nenhum log estruturado do score, dos termos expandidos, do truncamento `[:5]`. Em produção, quando um utilizador reporta "não encontrou X", não há evidência para triagem. É defensável no MVP; é insuficiente para um MCP corporativo de múltiplos times.

### R-9. Segurança do vocabulário externo (baixo / médio — emergente)

Ao mover `SYNONYMS` para YAML externo (recomendação em §5), surge uma superfície nova: quem pode editar, qual o limite de entradas, qual o limite de expansão. A mitigação é trivial (schema + limites hard-coded), mas deve ser explícita.

---

## 4. Comparação entre alternativas

Cada alternativa avaliada em quatro eixos: **complexidade de implementação**, **custo operacional**, **ganho em relação ao baseline atual** e **aderência ao objetivo do MCP** (servir `.github/instructions` de forma escalável sem overengineering).

| Alternativa | Implementação | Operação | Ganho vs hoje | Aderência | Veredicto |
|-------------|---------------|----------|----------------|-----------|-----------|
| **(A1) Manter `SYNONYMS` em código, só aumentar** | trivial | nenhum | baixo; amplifica L-1 a L-11 | baixa | ❌ Escala o problema |
| **(A2) YAML externo versionado + schema** | baixa | baixo (carga no `build_index`, hash p/ invalidar) | médio; resolve L-7, L-9 | alta | ✅ Fase 1 |
| **(A3) Vocabulário por domínio (partição + ativação por tag)** | média | baixo | alto; resolve L-10, R-1 | alta | ✅ Fase 2 |
| **(A4) `aliases:` no frontmatter do próprio doc** | baixa | nenhum | médio/alto; resolve L-11 e democratiza curadoria | muito alta | ✅ Fase 1 (complemento de A2) |
| **(A5) Word-boundary + normalização consistente (fix L-1, L-4, L-5)** | baixa | nenhum | alto em **precisão** | muito alta | ✅ Fase 1, **pré-requisito** |
| **(A6) BM25 (via `rank_bm25`, puro Python)** | média | baixo (índice em memória reconstruído no `build_index`) | médio a alto; resolve L-12 | alta (sem runtime externo) | ✅ Fase 2 |
| **(A7) Stemming/Lemmatization (`nltk`, `spacy`, `simplemma`)** | média-alta | médio (modelos PT+EN) | baixo-médio; não fundamental para instruções técnicas (vocabulário já estável) | média | ⚠️ Só se métricas mostrarem recall pobre em PT após A5+A6 |
| **(A8) Embeddings vetoriais (`fastembed`, `onnxruntime` local)** | alta | médio-alto (modelo ~30-90MB, inicialização lenta) | alto em **recall semântico** para queries fora do vocabulário | média: não essencial no MVP corporativo; valor claro só >100 docs e queries abertas | ⚠️ Fase 3, **opcional**, apenas como re-ranker |
| **(A9) Busca híbrida lexical+semântica (BM25 + embedding re-rank)** | alta | médio-alto | alto | média (adequado quando corpus cresce e queries são mais abertas) | ⚠️ Fase 3, condicionado a métrica |
| **(A10) LLM para reescrita/expansão de query em runtime** | baixa p/ escrever, alta p/ operar | alto (latência, custo, auditoria) | alto mas **imprevisível** | **baixa**: mata explicabilidade e introduz dependência externa | ❌ Não |
| **(A11) Ranking por campos estruturados (BM25-F sobre title/tags/body)** | média | baixo | alto | alta | ✅ Fase 2 (subconjunto natural de A6) |
| **(A12) Ontologias leves por domínio (YAML com hierarquia `broader/narrower`)** | média-alta | médio (modelagem, revisão) | alto em precisão | média (valor só se corpus >100 docs e múltiplas equipas ativas) | ⚠️ Avaliar Fase 3 |
| **(A13) Provider/plug-in de expansão semântica externo** | alta | alta | alto, se houver provedor maduro | baixa: introduz dependência operacional externa | ❌ Não agora |
| **(A14) Vocabulário controlado por área técnica (taxonomia fechada)** | média (requer processo) | médio | alto em consistência | média (processo pesado para 26 docs) | ⚠️ Fase 2+ |

**Leitura consolidada:**

1. **A5 é pré-requisito de qualquer outra alternativa.** Sem corrigir substring counting e normalização, qualquer expansão de vocabulário amplifica ruído.
2. **A2 + A4 resolvem o problema de governança observado** com custo mínimo e **sem** introduzir dependências runtime. Estes dois juntos cobrem ~80% da proposta de valor da observação.
3. **A3 resolve o problema FIX/RabbitMQ** de forma estrutural e explicável. Não requer ML.
4. **A6 (BM25)** é o próximo ganho incremental em qualidade de ranking, **sem** dependências pesadas (`rank_bm25` é ~200 linhas de Python puro; ou pode ser implementado inline).
5. **A8/A9 (embeddings) não são a resposta agora.** O MCP tem objetivos operacionais claros: corpus pequeno (~dezenas a baixas centenas de docs), queries formuladas por utilizadores técnicos (que sabem dizer "Polly" quando querem resiliência), restrição de explicabilidade. Embeddings trariam custo operacional (modelo local de 30–90 MB, inicialização lenta, invalidação por re-indexação) sem solucionar L-1 a L-11.
6. **A10 (LLM para reescrita)** é explicitamente **contra** os princípios: imprevisível, custoso, não-auditável.

---

## 5. Arquitetura recomendada

### 5.1 Princípios

1. **Corrigir antes de ampliar**: a correção lexical (A5) vem antes de qualquer extensão de vocabulário.
2. **Vocabulário é dado, não código**: `SYNONYMS` sai do `.py` para YAML versionado.
3. **Domínio é propriedade do documento**: preferir `aliases:` em frontmatter sempre que possível; vocabulário global só para termos transversais (linguísticos PT↔EN).
4. **Ativação condicional por domínio**: sinónimos específicos de domínio só se aplicam a documentos com tag/kind compatível.
5. **Estágios explícitos**: expansão, scoring lexical, boosts de metadado e prioridade são etapas separadas, plugáveis, testáveis e logáveis.
6. **Explicabilidade embutida**: o ranker devolve, em modo debug, a decomposição do score por termo e por componente.
7. **Zero runtime externo no MVP**: Python puro, YAML, `rglob`. Qualquer dependência adicional deve justificar-se por métrica.

### 5.2 Componentes (alvo, não todos na Fase 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              search_instructions                            │
│                                 (server.py)                                 │
└──────────────┬──────────────────────────────────────────────────────────────┘
               │ query, tags, ctx
               ▼
┌──────────────────────────┐       ┌────────────────────────────────────────┐
│  QueryTokenizer          │       │  SearchContext                         │
│  - split, normalize      │──────▶│  - domains (from tags/frontmatter)     │
│  - stopwords (opt)       │       │  - tag_filter                          │
└──────────────────────────┘       │  - debug                               │
                                   └────────────────────────────────────────┘
               │ tokens                              │ context
               ▼                                     │
┌──────────────────────────────────────────────┐    │
│  QueryExpansionProvider (Protocol)           │    │
│    DictQueryExpansionProvider                │◀───┘
│      - GlobalVocabulary (YAML)               │
│      - DomainVocabulary[tag/kind] (YAML)     │
│      - AliasVocabulary (from frontmatter)    │
│    ↳ returns {term: weight, provenance}      │
└──────────────┬───────────────────────────────┘
               │ expanded_terms
               ▼
┌──────────────────────────────────────────────┐
│  LexicalRanker (Protocol)                    │
│    WordBoundaryCountRanker     (Fase 1)      │
│    BM25Ranker                   (Fase 2)     │
│    BM25FieldedRanker            (Fase 2+)    │
│    ↳ lexical_score                           │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  MetadataBooster                             │
│    - priority bonus                          │
│    - tag exact-match bonus                   │
│    - scope/kind affinity                     │
│    ↳ metadata_score                          │
└──────────────┬───────────────────────────────┘
               │ combined score + decomposição
               ▼
┌──────────────────────────────────────────────┐
│  ResultComposer                              │
│    - excerpt, summary, related_ids           │
│    - explain (debug)                         │
└──────────────────────────────────────────────┘
```

Detalhe visual e fluxo de dados em [`A-design-alvo.md`](A-design-alvo.md). Interfaces `Protocol` em [`C-interfaces.md`](C-interfaces.md).

### 5.3 Fontes do vocabulário (por ordem de precedência na expansão)

1. **`aliases:` no frontmatter do documento** — peso 0.8 (alto). Quem escreve a instrução sabe melhor do que o vocabulário global. *Exemplo:* `microservice-messaging-rabbitmq-publish-consume.md` passaria a declarar `aliases: [rabbitmq, amqp, broker, queue, iconnection, mass-transit]`. Estes aliases entram no índice invertido do próprio documento, não contaminam outros.
2. **Vocabulário de domínio** — YAML por domínio sob `INSTRUCTIONS_ROOT/_vocabulary/<domain>.yaml`, ativado apenas quando `query.tokens` ou `query.tags` intersectam o domínio. Peso 0.5.
3. **Vocabulário global** — YAML único sob `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`, para mapeamentos transversais e linguísticos (PT↔EN). Peso 0.4.

A precedência materializa a regra "mais específico vence". O peso descendente reflete incerteza crescente.

### 5.4 Regra para evitar o problema FIX/RabbitMQ

**Domínios são disjuntos por defeito.** Um grupo `mensageria` no vocabulário global **não** existe. Em vez disso:

- `_vocabulary/messaging-rabbitmq.yaml` ativado apenas para docs com tag `rabbitmq` ou `messaging-amqp`.
- `_vocabulary/messaging-fix.yaml` ativado apenas para docs com tag `messaging-fix` ou `trading`.
- `_vocabulary/global.yaml` pode ter apenas mapeamentos linguísticos seguros (`mensageria ↔ messaging`), **nunca** entre produtos distintos.

Consequência: querying "rabbitmq" nunca traz documentos FIX via expansão; querying "mensageria" traz ambos, mas com peso menor (0.4 via global) e **sem** implicar equivalência entre FIX e AMQP.

---

## 6. Plano evolutivo em fases

Cada fase é entregável independente, com critério de aceite mensurável, e **não** quebra consumidores da tool `search_instructions` (a API JSON permanece estável).

### Fase 1 — Correção e desacoplamento básico (1–2 sprints)

**Objetivo:** corrigir defeitos de correção, desacoplar vocabulário do código, manter comportamento observável idêntico ou melhor em todas as queries hoje testadas.

**Entregáveis:**

1. **F1-1.** Trocar `blob.count(t)` por contagem com fronteira de palavra (regex pré-compilado por termo, cache). Normalizar blob e tokens simetricamente (NFKD + lowercase).
2. **F1-2.** Trocar `t in tag` por igualdade com normalização de hífen/underscore. Exato para tags, substring apenas para título se justificado (recomendo remover substring do título também).
3. **F1-3.** Extrair `SYNONYMS` para `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`, com schema validado (`id: str`, `aliases: list[str]`, `domain: str | null`, limite de 50 grupos × 20 termos). Fallback para o dicionário atual se ficheiro ausente, **com warning**.
4. **F1-4.** Ler `aliases:` do frontmatter dos próprios documentos. Estes aliases entram num índice inverso por-documento (`aliases_by_doc[doc.id] → set[alias]`). Query que casa um alias específico de um doc ganha boost direto naquele doc, sem contaminação global.
5. **F1-5.** Introduzir `Protocol` `QueryExpansionProvider` e `LexicalRanker` (ver [`C-interfaces.md`](C-interfaces.md)). Implementação atual refatorada como `DictQueryExpansionProvider` e `WordBoundaryCountRanker`. Código consumidor (`server.py`) injeta implementações via fábrica.
6. **F1-6.** Remover `[:5]` rígido; substituir por limite configurável com default 8, e **log estruturado** quando ocorre truncamento.
7. **F1-7.** Golden queries: suite de 15–30 pares `(query, docs_esperados_no_top_3)` baseada no fixture. Falha se o top-3 mudar sem justificativa no PR.

**Critério de aceite:**

- Toda a suite `test_indexing.py` e `smoke_test.py` continua verde.
- Golden queries verdes.
- Benchmark: `search_instructions` em corpus fixture permanece < 50 ms p95 (baseline atual ~5–10 ms).
- Log estruturado do ranker em `log.debug` com decomposição por termo.

### Fase 2 — Ranking estatístico e partição por domínio (2–3 sprints)

**Objetivo:** melhorar precisão/recall usando sinal estatístico (BM25) e eliminar contaminação cross-domínio.

**Entregáveis:**

1. **F2-1.** `BM25Ranker` como alternativa selecionável via configuração (`INSTRUCTIONS_RANKER=bm25`). Índice invertido `token → list[(doc_id, field, count)]` construído em `build_index`. Parâmetros `k1`, `b` configuráveis. Pure Python (inspirado em `rank_bm25`) — **zero dependência nova** ou `rank_bm25` como dependência opcional.
2. **F2-2.** Campos estruturados (BM25-F): pesos distintos para `title`, `tags`, `body` no cálculo estatístico, substituindo os boosts aditivos hoje espalhados em `score_record`.
3. **F2-3.** Vocabulários por domínio sob `_vocabulary/<domain>.yaml`. Sistema de ativação: tokens da query casam `_vocabulary/<d>.yaml` se `d ∩ inferred_domains(query, ctx)` for não-vazio. `inferred_domains` vem de `ctx.tag_filter` e de matches em `aliases` de documentos indexados.
4. **F2-4.** Explicabilidade: modo `explain=true` na tool devolve, por resultado, a decomposição do score (tokens diretos, tokens expandidos, contribuições BM25 por campo, boosts de metadado, provenance da expansão — de qual YAML ou frontmatter veio cada sinónimo).
5. **F2-5.** Telemetria: métricas de truncamento, hits por fonte de vocabulário, contagem de queries sem match — em `log.info` estruturado.

**Critério de aceite:**

- Teste adversarial `FIX ≠ RabbitMQ` passa: query "rabbitmq" não retorna docs marcados como `messaging-fix`, e vice-versa. Suite de golden queries expandida para cobrir cada domínio declarado.
- Benchmark: `search_instructions` em corpus 10× fixture < 150 ms p95.
- Documentação em `mcp-instructions-server/docs/` sobre como adicionar um domínio.

### Fase 3 — Híbrido opcional, **sob demanda medida** (sem prazo fixo)

**Objetivo:** preencher lacunas residuais de recall semântico **apenas se** métricas do mundo real mostrarem necessidade.

**Gatilho para entrar na Fase 3:** análise de queries sem match ou com má posição mostra que >N% são de variações parafrásticas que o léxico não cobre (e não é viável cobrir via `aliases`).

**Entregáveis candidatos (não encomendar todos):**

1. **F3-1.** Embeddings locais via `fastembed` (modelo `bge-small-en-v1.5` ou `multilingual-e5-small`, ~30–90 MB) como **re-ranker** do top-30 da BM25. **Nunca** como recall primário.
2. **F3-2.** Índice vetorial em memória (NumPy puro ou `hnswlib` opcional).
3. **F3-3.** Bandeira `enable_semantic_rerank` configurável; default **off**.
4. **F3-4.** Teste de regressão que verifica paridade lexical quando a flag está off.

**Critério de aceite:**

- Corpus real mostra melhoria mensurável (MRR@10 ou nDCG@10) em conjunto de validação.
- Inicialização do servidor < 5 s (modelo em lazy-load no primeiro uso).
- Off por omissão; comportamento determinístico quando off.

### O que deve continuar simples (invariantes do projeto)

- `build_index` continua síncrono, in-memory, sem dependência externa (filesystem + YAML).
- A tool `search_instructions` continua devolvendo JSON com o mesmo contrato (acrescentando apenas campos opcionais).
- `.github/instructions` como modelo mental: um ficheiro, um frontmatter, uma verdade. A evolução reforça isto ao deslocar `aliases:` para o próprio ficheiro.

### O que deve ser desacoplado desde já (Fase 1, inegociável)

- `SYNONYMS` do código.
- `_SYNONYM_LOOKUP` como constante de módulo.
- Scoring substring-based.
- Acesso direto a funções livres em `indexing.py` a partir de `server.py` (passar a usar providers injetados).

---

## 7. Refatorações concretas no `indexing.py`

Lista priorizada e granular. Ver [`B-refatoracoes.md`](B-refatoracoes.md) para o detalhe de cada item (impacto, esforço, dependências, teste associado).

**Fase 1 — inegociáveis:**

- **R-1.** Trocar `blob.count(t)` por `_word_count(blob, t)` com regex `\b{re.escape(t)}\b`, em `score_record` (linha 211).
- **R-2.** Normalizar tokens e blob via `_normalize_token` (incluir diacríticos) **antes** do scoring. Linhas 151, 174, 207.
- **R-3.** Remover substring em tag: `if t == _normalize_tag(tag)` em vez de `t in tag` (linhas 216–218).
- **R-4.** Remover substring em título **ou** limitar a casos com `\b`. Linha 214.
- **R-5.** Extrair `SYNONYMS` → `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`, carregado por um `VocabularyProvider` novo. Fallback para o dicionário atual com `log.warning` se ausente. Linhas 157–168.
- **R-6.** Tornar `expand_query_with_synonyms` um método de `DictQueryExpansionProvider` injetado via fábrica em `server.py`. Linhas 193–201.
- **R-7.** Parametrizar o limite de relacionados (hoje `[:5]`); emitir `log.debug` quando o corte efetivo ocorre. Linha 199.
- **R-8.** Suportar `aliases: list[str]` em frontmatter. `InstructionRecord` ganha campo `aliases: list[str]`. `build_index` preenche. Linhas 26–42, 50–100.
- **R-9.** Introduzir `Protocol` `QueryExpansionProvider` e `LexicalRanker`. Ver [`C-interfaces.md`](C-interfaces.md).
- **R-10.** Golden queries: novo ficheiro `tests/test_search_goldens.py` parametrizado sobre pares `(query, [expected_top_ids])`.

**Fase 2 — quando se avança:**

- **R-11.** Índice invertido em `build_index`: `inverted_index: dict[str, list[Posting]]`.
- **R-12.** `BM25Ranker` implementando `LexicalRanker`.
- **R-13.** `DomainVocabularyProvider` com ativação condicional.
- **R-14.** Campo `explain` opcional no `score_record` / novo método `score_record_with_trace` que devolve `(score, ScoreTrace)`.

**Fase 3 — opcional:**

- **R-15.** `SemanticReranker` como pós-processamento do top-N, atrás de flag.

### 7.1 Exemplo de correção para `R-1` e `R-2` (ilustrativo)

O código atual (linhas 204–220):

```204:220:mcp-instructions-server/corporate_instructions_mcp/indexing.py
def score_record(rec: InstructionRecord, tokens: list[str], tag_filter: set[str] | None) -> float:
    if tag_filter and not (tag_filter & set(rec.tags)):
        return 0.0
    blob = rec.search_blob()
    score = 0.0
    title_l = rec.title.lower()
    for t, weight in expand_query_with_synonyms(tokens).items():
        c = blob.count(t)
        if c:
            score += weight * (1.0 + min(5.0, 0.25 * c))
        if t in title_l:
            score += weight * 3.0
        for tag in rec.tags:
            if t == tag or t in tag:
                score += weight * 2.0
    score += 0.5 * PRIORITY_RANK.get(rec.priority, 0)
    return score
```

Esboço da versão corrigida (não aplicar ainda; é referência de alvo para F1-1..F1-3):

```python
_WORD_RE_CACHE: dict[str, re.Pattern[str]] = {}

def _word_pattern(term: str) -> re.Pattern[str]:
    if term not in _WORD_RE_CACHE:
        _WORD_RE_CACHE[term] = re.compile(rf"\b{re.escape(term)}\b")
    return _WORD_RE_CACHE[term]

def _search_blob_normalized(rec: InstructionRecord) -> str:
    blob = f"{rec.title}\n{' '.join(rec.tags)}\n{rec.body}"
    return _normalize_token(blob)

def score_record(
    rec: InstructionRecord,
    tokens: list[str],
    tag_filter: set[str] | None,
    expansion: Mapping[str, float] | None = None,
) -> float:
    if tag_filter and not (tag_filter & set(rec.tags)):
        return 0.0
    terms = expansion if expansion is not None else expand_query_with_synonyms(tokens)
    blob = _search_blob_normalized(rec)
    title_n = _normalize_token(rec.title)
    tags_n = {_normalize_token(t) for t in rec.tags}
    score = 0.0
    for term, weight in terms.items():
        t = _normalize_token(term)
        pat = _word_pattern(t)
        c = len(pat.findall(blob))
        if c:
            score += weight * (1.0 + min(5.0, 0.25 * c))
        if pat.search(title_n):
            score += weight * 3.0
        if t in tags_n:
            score += weight * 2.0
    score += 0.5 * PRIORITY_RANK.get(rec.priority, 0)
    return score
```

Diferenças essenciais: (a) `\b ... \b` elimina substring; (b) `_normalize_token` é aplicado aos dois lados do casamento; (c) tag compara por igualdade de set normalizado; (d) `expansion` é injetável, preparando para `QueryExpansionProvider`.

### 7.2 Testes de regressão sugeridos (detalhe em [`B-refatoracoes.md`](B-refatoracoes.md))

Referenciando a estrutura existente em [`tests/test_indexing.py`](../../../../mcp-instructions-server/tests/test_indexing.py) e [`docs/TESTS.md`](../../../../mcp-instructions-server/docs/TESTS.md):

1. **Substring falsa.** Documento com `body = "The getter pattern..."`, tag `["architecture"]`. Query `"get"` não deve pontuar `blob.count`-mente depois de R-1.
2. **Acento simétrico.** Documento com `body = "persistência em SQL"`. Query `"persistencia"` deve casar **diretamente** no blob depois de R-2, não apenas via sinónimo.
3. **Tag substring.** Documento com tag `"latest"`. Query `"test"` não deve ganhar o boost ×2 depois de R-3.
4. **FIX ≠ RabbitMQ** (Fase 2). Documento A tagged `["rabbitmq"]`, documento B tagged `["messaging-fix"]`, vocabulários separados. Query `"rabbitmq"` retorna A no top e B fora do top-10.
5. **Trunca alfabético.** Query `"http"` com `[:5]` default; depois de R-7, verificar que `log.debug` emite `synonym_truncated` e que, com limite 10, "rest" está na expansão.
6. **Golden queries.** Pares `(query, [expected_top_3_ids])` executando sobre o fixture atual; falha o PR se o top-3 mudar sem justificativa documentada no YAML de goldens.

---

## 8. Conclusão e recomendação final

### 8.1 Diagnóstico executivo

O MCP é um produto deliberadamente enxuto e isso é uma virtude. O mecanismo de indexação e busca atual **serve bem o MVP** mas carrega **dois defeitos independentes** que se amplificam mutuamente quando o corpus cresce:

- **Defeito de correção**: scoring por substring + expansão bidirecional ⇒ ruído já presente no corpus atual, não teórico.
- **Defeito de governança**: vocabulário acoplado ao código e sem partição por domínio ⇒ impossível escalar a múltiplas equipas e domínios (FIX vs RabbitMQ é o caso canônico).

A observação em [`../observacao.md`](../observacao.md) descreve corretamente o segundo defeito mas **subestima o primeiro**. Uma evolução que cuide só da governança (mover o YAML para fora) e não corrija o scoring vai criar a ilusão de melhoria enquanto multiplica os falsos positivos.

### 8.2 Diagnóstico técnico detalhado

Resumido em §2 (L-1 a L-13). Em ordem de criticidade:

1. **L-1** (substring counting) e **L-5** (tag substring) — correção, Fase 1.
2. **L-4** (normalização assimétrica) — correção, Fase 1.
3. **L-7/L-8/L-9** (acoplamento ao código, sem governança) — desacoplamento, Fase 1.
4. **L-10** (sem partição por domínio) — partição, Fase 2.
5. **L-11** (`workspace_signals` e frontmatter ricos ignorados) — aliases no frontmatter, Fase 1.
6. **L-12** (sem BM25/TF-IDF) — Fase 2.
7. **L-13** (sem re-ranking em estágios) — arquitetura, Fase 1 (introdução dos `Protocol`) + Fase 3 (uso opcional).

### 8.3 Melhor caminho recomendado

**Solução: A5 + A2 + A4 na Fase 1, A3 + A6 + A11 na Fase 2, avaliar A8/A9 só em Fase 3 sob métrica.**

Em linguagem direta:

1. **Corrigir o scoring** (fronteira de palavra, normalização consistente, tag por igualdade).
2. **Extrair `SYNONYMS` para YAML** versionado sob `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`.
3. **Adicionar `aliases:` no frontmatter** dos próprios documentos (a curadoria vai para o autor da instrução, que é quem sabe).
4. **Introduzir `Protocol`s** (`QueryExpansionProvider`, `LexicalRanker`) para que as fases seguintes sejam substituições e não reescritas.
5. **Partição por domínio** (Fase 2) elimina FIX ≠ RabbitMQ de forma estrutural.
6. **BM25-F** (Fase 2) substitui a heurística atual de boosts aditivos por uma fórmula com fundamento estatístico, sem dependências pesadas.
7. **Embeddings só entram se métricas exigirem** (Fase 3, opcional, como re-ranker).

### 8.4 Estratégia incremental (sem ruptura)

- Cada refatoração da Fase 1 é internamente pequena; o contrato externo de `search_instructions` não muda.
- `VocabularyProvider` tem fallback para o dicionário hard-coded atual — se `_vocabulary/global.yaml` não existir, o servidor continua a funcionar com aviso.
- `Protocol`s são introduzidos **antes** de mudar o algoritmo; isto evita acoplamento forte entre correção e mudança de modelo.
- Goldens garantem que otimizações futuras não degradam queries conhecidas.
- BM25 (Fase 2) é gated por configuração: `INSTRUCTIONS_RANKER=bm25` para rollout gradual.

### 8.5 O que preservar do código atual

- `build_index`, `_parse_markdown` e todas as defesas de segurança (`MAX_INSTRUCTION_FILE_BYTES`, `MAX_FRONTMATTER_SECTION_CHARS`, `is_path_under_root`, falha em `id` duplicado).
- `InstructionRecord` como dataclass central — estender com `aliases: list[str]` em vez de reescrever.
- `_normalize_token` — expandir o uso, não substituir.
- `excerpt_around_match`, `summarize_body` — corretos e independentes do ranker.
- `PRIORITY_RANK` como boost determinístico — integrar no `MetadataBooster` sem mudar pesos.
- A tokenização `tokenize_query` — possivelmente com um parâmetro de stopwords opcional; não mudar sem métrica.

### 8.6 O que refatorar imediatamente

Itens R-1 a R-10 da Fase 1 (§7 e [`B-refatoracoes.md`](B-refatoracoes.md)). Em especial, **R-1 (word boundary)**, **R-2 (normalização simétrica)**, **R-5 (YAML externo)** e **R-10 (goldens)** — estes quatro sozinhos eliminam a maior parte do risco descrito na observação.

### 8.7 O que **não** fazer agora

- **Não** adicionar embeddings / vector DB / ML como primeiro passo. O corpus é pequeno, o caso de uso é técnico, os utilizadores são desenvolvedores que conhecem a terminologia. Embeddings trariam custo operacional sem resolver L-1 a L-11.
- **Não** introduzir stemming/lemmatization para PT/EN agora. Instruções corporativas usam vocabulário estável; o ganho em recall é marginal e vem com dependências pesadas (NLTK, spaCy, simplemma).
- **Não** construir ontologia hierárquica genérica (`broader/narrower`, SKOS-like). Requer curadoria que o projeto não tem hoje; vocabulário por domínio plano cobre o caso sem o custo.
- **Não** fazer o servidor chamar LLM para reescrever a query em runtime. Custo, latência, não-determinismo e perda de explicabilidade.
- **Não** implementar todas as `Protocol` da Fase 1 em implementações múltiplas no dia 1 — uma implementação concreta + uma `Protocol` é suficiente para destravar testes e Fase 2.
- **Não** permitir que `aliases:` do frontmatter "vazem" para outros documentos. Devem ser sempre locais ao doc que os declara.

---

> **Separação de factos e inferências.** Tudo nas seções 1 e início de 2 é factual a partir do código em [`indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) e [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py). Os riscos em §3, a avaliação comparativa em §4 e a arquitetura-alvo em §5–§7 são inferência e recomendação, fundamentados nos factos e no objetivo declarado do MCP. Nenhuma métrica de produção foi assumida — onde a decisão depende de métrica (Fase 3), isto é dito explicitamente.
