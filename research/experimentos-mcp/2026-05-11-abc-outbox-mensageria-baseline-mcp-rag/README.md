# Experimento A/B/C — Outbox/Mensageria (Baseline vs MCP vs RAG)

Este experimento é um recorte do experimento de 2026-05-04, focado **somente** no cenário **Outbox / mensageria**, em formato **A/B/C**:

- **A (Baseline sem fixtures)**: sem MCP e sem instructions locais; o experimentador deve **remover temporariamente** a pasta `fixtures/` do workspace durante a execução, e **restaurar ao final**.
- **B (MCP)**: usar o **MCP** (`corporate_instructions_*`) como fonte de contexto/guardrails (execução “com contexto via MCP”).
- **C (RAG geral)**: usar RAG geral sobre **todo o codebase**, com `fixtures/` **intacta** (permitido ler/recuperar conteúdo dela como parte do workspace).

Objetivo: comparar baseline “cego” (sem fixtures), vs MCP (contexto recuperado via tools), vs RAG geral (recuperação livre no workspace).

## Resultado consolidado (pontuação e ranking)

Fonte: [`relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__consolidado__A-B-C.md`](relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__consolidado__A-B-C.md)

- **Médias (0–10; média simples dos 9 critérios)**:
  - **B (MCP)**: **8.00**
  - **A (Baseline)**: **7.44**
  - **C (RAG geral)**: **7.44**
- **Ranking**: **1º=B**, **2º=A**, **3º=C** (A e C empatam em média; desempate documentado no consolidado)

## Onde está cada coisa

| Conteúdo | Localização |
|----------|-------------|
| Especificação do experimento (protocolo, métricas, rubrica) | [`experimento.md`](experimento.md) |
| Orquestradores A/B/C (copiar/colar no Cursor) | [`orquestrador/`](orquestrador/) |
| Prompts autocontidos do cenário (A, B e C) | [`Prompts/cenario-01-outbox-mensageria/`](Prompts/cenario-01-outbox-mensageria/) |
| Relatórios (A/B/C + consolidado + prompt/modelo) | [`relatorios/`](relatorios/) |

## Artefatos gerados (links diretos)

### Relatórios por condição

- **A (baseline)**: [`relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__baseline.md`](relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__baseline.md)
- **B (mcp)**: [`relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__mcp.md`](relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__mcp.md)
- **C (rag)**: [`relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__rag.md`](relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__rag.md)

### Consolidação e materiais de avaliação

- **Consolidado A/B/C (notas 0–10 + ranking + riscos)**: [`relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__consolidado__A-B-C.md`](relatorios/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__consolidado__A-B-C.md)
- **Prompt usado para consolidar**: [`relatorios/PROMPT__comparacao-consolidada__A-B-C.md`](relatorios/PROMPT__comparacao-consolidada__A-B-C.md)
- **Modelo (formato obrigatório) da consolidação**: [`relatorios/MODELO__analise-consolidada__A-B-C.md`](relatorios/MODELO__analise-consolidada__A-B-C.md)
- **Template de relatório (por corrida)**: [`relatorios/TEMPLATE__outbox-mensageria__A-ou-B-ou-C.md`](relatorios/TEMPLATE__outbox-mensageria__A-ou-B-ou-C.md)

## Como executar no Cursor (resumo)

1. Para cada condição (A, B e C), use **thread/sessão separada** (sem contaminação).
2. Cole o conteúdo do orquestrador correspondente (A, B ou C) no início da conversa.
3. Cole o prompt correspondente (A, B ou C) e execute a tarefa.
4. **Somente A (baseline):** antes de iniciar, mova `fixtures/` para fora do workspace; ao final, restaure `fixtures/`.
5. Ao final, exporte o resultado seguindo a seção **Exportação** do prompt (gera um `.md` em `docs/experimentos-mcp/Resultados/`).
6. Preencha o template em `relatorios/` com métricas e observações.

## Convenções de nomes (reprodutibilidade)

- O slug de exportação deve ser sempre: `abc-outbox-mensageria-baseline-mcp-rag`
- Sufixos:
  - `__baseline.md` para A
  - `__mcp.md` para B
  - `__rag.md` para C

