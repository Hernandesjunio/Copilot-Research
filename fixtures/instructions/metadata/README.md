# metadata/

Pasta reservada para artefatos de configuração do corpus.  
**Não é indexada** pelo MCP (`build_index` exclui toda a árvore `metadata/`).

## Estrutura

```
metadata/
  corpus-query-expansion-map/   ← Corpus Query Expansion Map (ADR-002); apenas `*.yaml`
    api.yaml
    messaging.yaml
    ...
  corpus/                       ← (futuro) manifesto do corpus, changelogs
  docs/                         ← (futuro) documentação interna do corpus
```

## Regras

- Arquivos `.md` aqui **não são instruções** e não entram no índice de busca.
- Ficheiros `*.yaml` dentro de `corpus-query-expansion-map/` são carregados
  pelo loader do Corpus Query Expansion Map na ordem determinística do nome.
- Subpastas futuras seguem o mesmo princípio de separação: configuração ≠ corpus.
