# Referências no código — sinónimos na busca

| Ficheiro | Notas |
|----------|--------|
| [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) | `SYNONYMS` (~157+), `_build_synonym_lookup` (~177+), `_SYNONYM_LOOKUP`, `expand_query_with_synonyms` (~193+), uso em fluxo de pesquisa (~210+) |

## Comandos úteis (opcional)

```bash
rg -n "SYNONYMS|expand_query_with_synonyms|_SYNONYM_LOOKUP" mcp-instructions-server/corporate_instructions_mcp/indexing.py
```
