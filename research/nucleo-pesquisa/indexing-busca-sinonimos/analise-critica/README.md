# Análise crítica — indexação e expansão por sinónimos

Análise arquitetural em nível Staff Engineer sobre o mecanismo atual de indexação e expansão por sinónimos do servidor MCP, com foco no código real em [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py).

## Entradas desta análise

- Hipótese inicial: [`../observacao.md`](../observacao.md)
- Framework de análise: [`../prompt-analise-critica.md`](../prompt-analise-critica.md)
- Código-fonte analisado: [`indexing.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) e consumidor em [`server.py`](../../../../mcp-instructions-server/corporate_instructions_mcp/server.py)
- Suite de testes de referência: [`tests/test_indexing.py`](../../../../mcp-instructions-server/tests/test_indexing.py) e [`docs/TESTS.md`](../../../../mcp-instructions-server/docs/TESTS.md)

## Artefatos

| Ficheiro | Conteúdo |
|----------|----------|
| [`analise-arquitetural.md`](analise-arquitetural.md) | Análise principal — seções 1 a 8 do framework. |
| [`A-design-alvo.md`](A-design-alvo.md) | Proposta de desenho alvo em pseudodiagrama e fluxo de dados. |
| [`B-refatoracoes.md`](B-refatoracoes.md) | Lista priorizada de refatorações concretas em `indexing.py`. |
| [`C-interfaces.md`](C-interfaces.md) | Contratos/interfaces `Protocol` para evolução desacoplada. |
| [`D-adr.md`](D-adr.md) | Architecture Decision Record resumida (contexto → decisão → consequências). |

## Veredicto executivo

A observação em [`../observacao.md`](../observacao.md) é **parcialmente correta e insuficiente**.

- **Correta**: o acoplamento do vocabulário ao código-fonte é uma limitação real para um MCP corporativo multi-domínio (falta governança, extensão exige redeploy, viés herdado da curadoria inicial).
- **Insuficiente**: a análise da observação **subestima** um defeito de correção presente hoje em [`score_record`](../../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py) — a combinação de `blob.count(token)` (substring sem fronteira de palavra) com a expansão bidirecional de sinónimos introduz falsos positivos **já hoje**, mesmo no corpus atual, independentemente de multi-domínio.

O problema arquitetural mais relevante não é "a lista é curta/estática", e sim: **o scoring lexical atual é substring-based e a expansão é bidirecional**, o que amplifica ruído exatamente na direção em que o corpus cresce. Qualquer solução de governança do vocabulário sem corrigir a correção lexical vai falhar em silêncio.

Detalhe completo em [`analise-arquitetural.md`](analise-arquitetural.md) §2 e §7.
