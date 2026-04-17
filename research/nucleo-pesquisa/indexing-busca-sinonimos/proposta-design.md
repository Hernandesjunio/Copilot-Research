# Proposta de desenho — sinónimos na busca

> **Superseded.** O conteúdo desta proposta foi consolidado e expandido na análise arquitetural Staff-level em [`analise-critica/`](analise-critica/README.md). Este ficheiro fica como ponteiro e resumo curto.

## Direção recomendada (resumo)

Evoluir o mecanismo de indexação em **três fases**, preservando invariantes operacionais do MCP (Python puro, YAML, `rglob`, sem runtime externo no MVP):

- **Fase 1 — correção e desacoplamento**: corrigir `blob.count` → casamento com fronteira de palavra; normalização simétrica (NFKD) entre query e blob; tag exata normalizada; extrair `SYNONYMS` para `INSTRUCTIONS_ROOT/_vocabulary/global.yaml` com fallback; suportar `aliases:` no frontmatter; introduzir `Protocol`s (`QueryExpansionProvider`, `LexicalRanker`, `VocabularyProvider`, `MetadataBooster`); golden queries de regressão.
- **Fase 2 — estatístico + partição por domínio**: índice invertido; `BM25FieldedRanker` selecionável por variável; vocabulários `_vocabulary/<domain>.yaml` ativados condicionalmente (resolve FIX ≠ RabbitMQ estruturalmente); modo `explain` com `ScoreTrace`.
- **Fase 3 — semântico opcional**: re-ranker embedding-based sobre o top-N da BM25, atrás de flag `enable_semantic_rerank` off-by-default, apenas se métricas reais justificarem.

## Ligações

- **Análise completa**: [`analise-critica/analise-arquitetural.md`](analise-critica/analise-arquitetural.md)
- **Design alvo / pseudodiagrama**: [`analise-critica/A-design-alvo.md`](analise-critica/A-design-alvo.md)
- **Lista priorizada de refatorações**: [`analise-critica/B-refatoracoes.md`](analise-critica/B-refatoracoes.md)
- **Interfaces (`Protocol`s)**: [`analise-critica/C-interfaces.md`](analise-critica/C-interfaces.md)
- **ADR resumida**: [`analise-critica/D-adr.md`](analise-critica/D-adr.md)
- Tema no núcleo: [`README.md`](README.md)
- Código: [`referencias-codigo.md`](referencias-codigo.md)
