# Núcleo da pesquisa — achados de implementação e extensibilidade

Esta pasta agrega **temas** em subpastas: cada tema liga **observação** (o que o código ou o desenho faz), **prompt(s) de análise assistida** (reutilizáveis em ChatGPT, Cursor, etc.) e **proposta de solução** ou direção de desenho — sem substituir o protocolo empírico em [`../experimentos-mcp/`](../experimentos-mcp/).

## O que não é

| Área | Diferença |
|------|-----------|
| [`../analises/`](../analises/) | Análises técnicas datadas, em geral um ficheiro narrativo por data (`YYYY-MM-DD-slug.md`). Aqui o foco é **rastreabilidade código ↔ prompt ↔ proposta** por tema. |
| [`../experimentos-mcp/`](../experimentos-mcp/) | Ensaios com condições, baseline e anexos de sessão. Aqui **não** há obrigatoriamente desenho experimental A/B. |
| [`../sugestoes-futura/`](../sugestoes-futura/) | Explorações longas e voláteis. Os temas aqui tendem a estar **ancorados** a ficheiros concretos do servidor MCP. |

## Índice de temas

| Pasta | Resumo |
|-------|--------|
| [`indexing-busca-sinonimos/`](indexing-busca-sinonimos/) | Busca por palavras-chave, mapa `SYNONYMS` e expansão de consulta em `indexing.py`. |

## Novo tema

1. Copie [`_template/`](_template/) para uma nova pasta (`kebab-case`, nome estável ou prefixo `YYYY-MM-DD-` se quiser ordenação cronológica).
2. Preencha `README.md` do tema com uma linha de contexto e links para os outros ficheiros.
3. Opcional: publique uma síntese citável em [`../analises/`](../analises/) que aponte para esta pasta.

Metodologia geral: [`../README.md`](../README.md).
