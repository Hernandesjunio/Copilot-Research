# Instruções locais

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.

## Contexto do repositório

- **Descrição:** {{DESCRIÇÃO_DO_PROJETO}}
- **Stack:** {{STACK_COMPLETA}}

## MCP server: `corporate-instructions`

Padrões organizacionais são servidos via MCP — não estão neste repo.
Este arquivo prevalece sobre o MCP em caso de conflito.

### Consulta MCP (obrigatório em decisões cross-cutting)

Use sempre os **nomes literais** das tools abaixo (como no catálogo MCP); são o contrato com o servidor e dão direcção correcta a agentes assistidos ou autónomos.

1. **Indexar** — chame `list_instructions_index` para ver o corpus e agrupamento por tags.
2. **Buscar por tema** — faça `search_instructions` com queries distintas por cada concern da tarefa; não se limite a uma busca.
3. **Ler todas as relevantes** — use `get_instructions_batch` para ler o corpo completo de todas as instructions pertinentes de uma vez; não pare nas primeiras retornadas.
4. **Cruzar policy × código** — antes de aplicar um padrão MCP, verifique se já existe no repo. Existente = **FATO**; ausente = **HIPÓTESE**. Consistência com o código prevalece sobre completude normativa.
5. **Citar fontes** — referencie server + id da instruction e arquivos do repo em cada decisão.

Quando o workspace **contiver o próprio corpus** de instructions (Markdown na raiz configurada como `INSTRUCTIONS_ROOT`), use como referência **normativa** o ficheiro governamental `instruction-authoring-standard.md` (em geral `id: instruction-authoring-standard` no seu frontmatter) para autoria, metadados, mapa de expansão e esta enumeração de tools.

## Fluxo de trabalho

- Antes de editar arquivos críticos: leia o arquivo alvo.
- Após mudanças substanciais: rode build/testes.
