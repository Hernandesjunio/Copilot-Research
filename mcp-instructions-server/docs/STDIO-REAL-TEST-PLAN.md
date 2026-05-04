# Plano de teste real — consumo MCP STDIO (EPIC-05)

Este plano descreve como validar os requisitos de P0/P1/P2 em consumo **real** do servidor MCP (`python -m corporate_instructions_mcp`) por um cliente MCP sobre stdio.

## Objetivo

Verificar, em ambiente semelhante ao host real, que:

1. as novas tools estão publicadas em `tools/list`;
2. os contratos de entrada/saída de P0 (`validate_applicability`, `build_compliance_matrix`) funcionam;
3. os campos aditivos de P1 em `resolve_instruction_context` estão presentes;
4. as evoluções de P2 (`list_instructions_index` com saúde/status e `search_instructions` multi-query) funcionam com saída estável.

## Pré-condições

- Dependências instaladas em `mcp-instructions-server`:
  - `pip install -e ".[dev]"`
- `INSTRUCTIONS_ROOT` apontando para corpus válido.
  - Recomendado para repetibilidade: `../fixtures/instructions`
- Python 3.10+.

## Execução automática recomendada

```bash
python scripts/run_epic05_stdio_real_check.py
```

### Critério de sucesso

- Processo encerra com código `0`.
- JSON final contém `"ok": true`.
- Cada item em `checks` indica validação concluída.

## Matriz de cenários (entrada -> saída esperada)

1) **Descoberta de tools**
- **Tool:** `tools/list` (protocolo MCP)
- **Entrada:** sem payload
- **Esperado:** presença de:
  - `list_instructions_index`
  - `search_instructions`
  - `get_instructions_batch`
  - `resolve_instruction_context`
  - `validate_applicability`
  - `build_compliance_matrix`

2) **Saúde do índice (P2)**
- **Tool:** `list_instructions_index`
- **Entrada:** `{}`
- **Esperado:**
  - `status` em `{"ok","partial"}`
  - `index_health.loaded = true`
  - campos `warnings` e `errors` presentes

3) **Aplicabilidade com evidência positiva (P0)**
- **Tool:** `validate_applicability`
- **Entrada (resumo):**
  - `instruction_ids = ["microservice-authorization-resource-scope-and-audit"]`
  - `target_artifact.path = "Api/Endpoints/ClienteEndpoints.cs"`
  - `workspace_evidence = ["HttpContext.User"]`
- **Esperado:**
  - `results[0].applicability = "applicable"`

4) **Matrix operacional com positivo + gap (P0)**
- **Tool:** `build_compliance_matrix`
- **Entrada (resumo):**
  - `instruction_results[0].applicability = "applicable"`
  - `artifact_observations` com `positive` e `gap`
- **Esperado:**
  - `matrix[0].status = "partial_conformance"`

5) **Campos aditivos P1**
- **Tool:** `resolve_instruction_context`
- **Entrada (exemplo):**
  - `query = "authorization owner audit endpoint"`
  - `max_results = 3`
- **Esperado em `resolution`:**
  - `selection_rationale`
  - `pending_evidence`
  - `required_workspace_signals`
  - `next_repo_evidence_actions`

6) **Multi-query consolidado (P2)**
- **Tool:** `search_instructions`
- **Entrada (resumo):**
  - `queries = ["minimal api rest status codes", "response envelope global error handling"]`
  - `max_results_per_query = 3`
- **Esperado:**
  - `queries` como lista
  - `consolidated.top_policies` (lista)
  - `consolidated.top_references` (lista)
  - `consolidated.coverage_gaps` (lista)

## Diagnóstico em caso de falha

- Falha em `tools/list`: verificar ambiente Python/instalação do pacote.
- Falha de indexação: verificar `INSTRUCTIONS_ROOT` e permissões de leitura.
- Falha de contrato em P0/P1/P2: rodar regressão local:
  - `pytest -q tests/test_epic05_tools.py tests/smoke_test.py`
- Diferença entre host IDE e teste local: anexar saída de:
  - `python scripts/print_mcp_tools_list.py`
  - `python scripts/run_epic05_stdio_real_check.py`

## Extensão para outro contexto (corpus real)

Quando trocar de corpus:

1. definir `INSTRUCTIONS_ROOT` para a raiz real;
2. repetir o script de teste real;
3. validar que os cenários de entrada do item 3/4 usam IDs existentes no índice real;
4. se necessário, adaptar os exemplos de `instruction_ids` sem alterar os critérios de saída por estado.
