# Indexação e busca — sinónimos (`SYNONYMS`)

Recuperação por palavras-chave no servidor MCP usa um mapa estático de sinónimos e expansão de tokens em [`indexing.py`](../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py).

## Documentos

| Ficheiro | Conteúdo |
|----------|----------|
| [`observacao.md`](observacao.md) | Achado sobre o comportamento atual e riscos (ex.: viés lexical, extensibilidade). |
| [`prompt-analise-critica.md`](prompt-analise-critica.md) | Prompt(s) para análise assistida (Cursor, ChatGPT, etc.). |
| [`analise-critica/`](analise-critica/README.md) | **Análise arquitetural Staff-level** que valida/refuta a observação e propõe evolução em fases. |
| [`proposta-design.md`](proposta-design.md) | Placeholder inicial — consolidado em [`analise-critica/D-adr.md`](analise-critica/D-adr.md). |
| [`referencias-codigo.md`](referencias-codigo.md) | Entradas no código (incl. `SYNONYMS`, `expand_query_with_synonyms`). |

## Estado

- [x] Estrutura criada
- [x] Observação e prompt preenchidos
- [x] Análise arquitetural consolidada em [`analise-critica/`](analise-critica/README.md)
- [ ] Decisão de início de Fase 1 (ver [`analise-critica/D-adr.md`](analise-critica/D-adr.md))
