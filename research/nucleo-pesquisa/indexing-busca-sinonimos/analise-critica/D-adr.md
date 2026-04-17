# D — ADR resumida: Indexação e expansão por sinónimos

> **Estado:** proposta. **Data:** 2026-04-17. **Proponente:** análise arquitetural em [`analise-arquitetural.md`](analise-arquitetural.md). **Escopo:** `mcp-instructions-server`.

## Contexto

O servidor MCP indexa ficheiros Markdown sob `INSTRUCTIONS_ROOT` (ver fluxo em [`AGENTS.md`](../../../../AGENTS.md)) e implementa busca lexical por palavras-chave com expansão por sinónimos. A implementação atual está em [`corporate_instructions_mcp/indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) e é consumida por [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py) via a tool `search_instructions`.

Os pontos relevantes do estado atual (§1 da análise):

- `SYNONYMS` é um `dict[str, list[str]]` **hard-coded** no módulo, com 10 grupos centrados em backend .NET (PT+EN).
- `_SYNONYM_LOOKUP` é construído no import do módulo; não é injetável; a expansão é **bidirecional** (todos os termos de um grupo são mutuamente equivalentes a peso 0.5).
- `expand_query_with_synonyms` trunca a expansão em `[:5]` por token, sem aviso, com ordem **alfabética** herdada do `sorted(values)` em `_build_synonym_lookup`.
- `score_record` usa `blob.count(t)` (substring, não fronteira de palavra), `t in title_l` e `t in tag` (substrings), `0.5 * PRIORITY_RANK`.
- A normalização por remoção de diacríticos é aplicada **apenas** no lookup de sinónimos, não no casamento com o `search_blob` — é assimétrica.
- Metadados ricos do frontmatter dos fixtures (ex.: `workspace_signals: [RabbitMQ, IConnection, ...]`) **não** são consumidos pelo ranker.

Objetivos do projeto que restringem a decisão:

1. MCP deve servir como camada centralizada de contexto para múltiplos domínios técnicos, substituindo `.github/instructions` distribuídos.
2. Simplicidade operacional — sem runtime externo no MVP (ver `AGENTS.md`: "Logs operacionais para stderr; stdout só protocolo MCP").
3. Explicabilidade das respostas (requisito implícito para uso em ferramentas assistentes).
4. Governança de vocabulário compatível com múltiplas equipas / múltiplos domínios.

## Problema

Existem **dois defeitos independentes** no mecanismo atual que se amplificam mutuamente quando o corpus cresce:

1. **Defeito de correção lexical**: `blob.count` + substring em tag/título + normalização assimétrica ⇒ **já gera ruído hoje** no corpus atual. Exemplo concreto: querying `"http"` expande para `{get, put, post, delete, endpoint}[:5]`, e `blob.count("get")` casa `getter`, `widget`, `target` em qualquer documento.
2. **Defeito de governança e extensibilidade**: vocabulário acoplado ao código, sem partição por domínio, sem provenance, sem mecanismo de extensão ⇒ não escala a múltiplas equipas nem a domínios cuja semântica colide (caso canônico: FIX messaging ≠ RabbitMQ, ambos caindo sob "mensageria" genérica).

Adicionalmente, a observação inicial em [`../observacao.md`](../observacao.md) identificou corretamente o segundo defeito mas **não** capturou o primeiro. Qualquer evolução que trate apenas da governança (mover YAML para fora) sem corrigir a correção lexical vai criar a ilusão de melhoria enquanto multiplica falsos positivos.

## Decisão

Evoluir o mecanismo de indexação e busca em **três fases**, com invariantes operacionais preservadas.

### Decisões atômicas

1. **Corrigir o scoring lexical antes de qualquer extensão de vocabulário**:
   - Casamento com fronteira de palavra (`\b`) em vez de `blob.count`.
   - Normalização simétrica (NFKD + lowercase) em ambos os lados do casamento.
   - Tag matching por igualdade normalizada, não por substring.
2. **Desacoplar vocabulário do código**:
   - `SYNONYMS` ⇒ `INSTRUCTIONS_ROOT/_vocabulary/global.yaml`, com schema validado e limites defensivos.
   - Fallback automático para o dicionário hard-coded com `log.warning` se o YAML ausente.
3. **Mover curadoria lexical para o autor do documento**:
   - Suportar `aliases:` no frontmatter de cada `.md`.
   - Estes aliases são **locais ao documento** — não entram no vocabulário global.
4. **Partição por domínio** (Fase 2):
   - Vocabulários `_vocabulary/<domain>.yaml` ativados condicionalmente por interseção `ctx.domains ∩ {domain}`.
   - Regra estrutural: **domínios são disjuntos por defeito** (garante FIX ≠ RabbitMQ).
5. **Substituir heurística aditiva por BM25-F** (Fase 2, selecionável via variável de ambiente), mantendo `WordBoundaryCountRanker` como fallback durante rollout.
6. **Explicabilidade**: modo `debug` na tool devolve `ScoreTrace` com decomposição por termo, campo e proveniência.
7. **Protocol-first**: `QueryExpansionProvider`, `LexicalRanker`, `VocabularyProvider`, `MetadataBooster` como `typing.Protocol` (ver [`C-interfaces.md`](C-interfaces.md)), permitindo evolução por substituição.
8. **Embeddings semânticos só em Fase 3, condicionados a métrica**, e apenas como **re-ranker** do top-N lexical — nunca como recall primário.

### O que explicitamente é rejeitado

- **LLM para reescrita de query em runtime** — incompatível com explicabilidade, custo e determinismo.
- **Vector DB externo** (Qdrant, pgvector, ...) — overkill para corpus < 500 docs.
- **Ontologia hierárquica (SKOS-like)** — custo de curadoria incompatível com estado atual do projeto.
- **Stemming/lemmatization PT agora** — sem evidência de recall pobre; introduz dependências pesadas.
- **Reescrever `build_index` para ser assíncrono** — sem ganho prático.

## Consequências

### Positivas

- **Precisão imediata** após Fase 1: eliminação dos substring matches reduz falsos positivos sem mudar arquitetura profunda.
- **Governança distribuída**: autores de instruções ganham controlo sobre o vocabulário dos próprios documentos (via `aliases:` no frontmatter). Equipas de domínio podem contribuir YAMLs sem tocar no pacote Python.
- **Não-contaminação estrutural**: partição por domínio resolve FIX ≠ RabbitMQ por construção, não por acaso.
- **Explicabilidade**: `ScoreTrace` permite triagem de "por que este resultado?" sem debugger.
- **Retrocompatibilidade preservada**: contrato JSON de `search_instructions` muda apenas de forma aditiva (campos novos opcionais).
- **Evolução desacoplada**: Fase 2 e Fase 3 são drop-in via `Protocol`s — não exigem reescrita do consumidor.
- **Testabilidade**: golden queries previnem regressões durante qualquer alteração no ranker ou vocabulário.

### Negativas

- **Superfície de segurança nova**: `_vocabulary/*.yaml` passa a ser superfície de edição — requer schema e limites (já incorporados na decisão; herdam as defesas existentes `yaml.safe_load`, `MAX_FRONTMATTER_SECTION_CHARS`).
- **Custo de migração não trivial**: ~10 refatorações na Fase 1, com risco de mudar top-3 de queries hoje funcionais. Mitigação: goldens + fallback.
- **Proliferação de ficheiros**: `_vocabulary/<domain>.yaml` cresce com a organização. Mitigação: limites hard-coded e revisão por CODEOWNERS quando aplicável.
- **Complexidade incremental**: `Protocol`s adicionam abstrações que não existem hoje. Mitigação: uma implementação concreta por `Protocol` na Fase 1; evoluir só se a Fase 2 for ativada.
- **BM25-F requer calibração**: pesos por campo (`title`, `tags`, `body`) têm que ser validados contra goldens reais. Mitigação: defaults conservadores e switch por variável de ambiente.

### Neutras

- **Peso dos providers na inicialização**: Fase 1 lê um YAML adicional no `build_index`. Impacto desprezível (<1 ms no fixture atual).
- **Tamanho do `InstructionRecord`**: ganha campo `aliases: list[str]`, normalmente pequeno.
- **Superfície de logs**: aumenta (eventos `synonym_truncated`, `fallback_static_vocabulary`, etc.). Alinhado com o requisito de observabilidade em contexto corporativo.

## Alternativas consideradas (e por que rejeitadas)

Detalhe completo em §4 de [`analise-arquitetural.md`](analise-arquitetural.md). Resumo das rejeições principais:

- **(A1) Manter status quo e só aumentar `SYNONYMS`**: agrava defeito de correção proporcionalmente ao número de termos.
- **(A8/A9) Embeddings como recall primário**: custo operacional sem resolver defeitos estruturais; melhor como Fase 3 opcional.
- **(A10) LLM query rewriting runtime**: imprevisibilidade + perda de explicabilidade.
- **(A12) Ontologias SKOS**: custo de curadoria desproporcional ao estágio do produto.

## Testes de verificação da decisão

- **Correção lexical (Fase 1)**: teste adversarial substring ("get" não casa "getter") passa.
- **Acento simétrico (Fase 1)**: query "persistencia" casa documentos "persistência" diretamente no blob.
- **Aliases per-doc (Fase 1)**: alias em doc A não melhora score de doc B.
- **FIX ≠ RabbitMQ (Fase 2)**: vocabulários separados por domínio. Query "rabbitmq" não traz docs `messaging-fix`.
- **Golden queries (Fase 1, em diante)**: suite de 15–30 pares `(query, expected_top_ids)` protege regressão.
- **Paridade semântica (Fase 3)**: com `enable_semantic_rerank=false`, comportamento idêntico à Fase 2.

## Revisão e evolução

Esta decisão é revisitada nos seguintes gatilhos:

1. **Antes de abrir a Fase 2**: confirmar que a Fase 1 atingiu os critérios de aceite em corpus real, não só fixture.
2. **Antes de abrir a Fase 3**: exigir métrica (MRR@10 / nDCG@10) em um conjunto de validação real; >20% de queries insatisfatórias por paráfrase para justificar embeddings.
3. **Se o corpus ultrapassar 500 documentos**: reavaliar se `rglob` + índice em memória + rebuild por hash continua suficiente.
4. **Se o MCP ganhar transporte HTTP** (ver [`docs/ROADMAP-TRANSPORT-HTTP.md`](../../../../mcp-instructions-server/docs/ROADMAP-TRANSPORT-HTTP.md)): reavaliar se a invalidação do índice precisa de estratégia diferente (webhook, watch, etc.).

## Ligações

- Análise principal: [`analise-arquitetural.md`](analise-arquitetural.md)
- Design alvo: [`A-design-alvo.md`](A-design-alvo.md)
- Refatorações: [`B-refatoracoes.md`](B-refatoracoes.md)
- Interfaces: [`C-interfaces.md`](C-interfaces.md)
- Hipótese inicial: [`../observacao.md`](../observacao.md)
- Framework do prompt: [`../prompt-analise-critica.md`](../prompt-analise-critica.md)
- Código analisado: [`indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py), [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py)
- Testes existentes: [`tests/test_indexing.py`](../../../../mcp-instructions-server/tests/test_indexing.py), [`docs/TESTS.md`](../../../../mcp-instructions-server/docs/TESTS.md)
