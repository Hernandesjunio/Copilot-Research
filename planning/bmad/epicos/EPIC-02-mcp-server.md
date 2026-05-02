# EPIC-02 — Servidor MCP (read-only, heurístico e composto)

## Objetivo

Entregar um servidor MCP em Python, transporte **stdio**, capaz de transformar um corpus Markdown em contexto utilizável por agente/cliente sem embeddings, com foco em:

- busca heurística explicável;
- leitura em batch com foco por secção;
- resolução composta de contexto;
- checklist normativa por cenário;
- leitura explícita de conflitos e precedência;
- telemetria e relatório de qualidade para tuning iterativo.

## Estado implementado

### Runtime e indexação

- servidor read-only em [`mcp-instructions-server`](../../../mcp-instructions-server/)
- leitura de `INSTRUCTIONS_ROOT`
- índice em memória com reconstrução quando o root muda
- corpus versionado por assinatura (`corpus_version`)
- configuração por ambiente em `corporate_instructions_mcp/config.py`

### Contract tools expostas

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch`
- `resolve_instruction_context`
- `get_normative_checklist`
- `detect_instruction_conflicts`

### Capacidades entregues no código Python

- ranking heurístico com tokens, prioridade, phrases, proximidade e expansão por sinónimos
- diagnósticos de busca (`search_confidence`, `top_score_gap_1_2`, `fallback_suggestions`, termos casados)
- filtros por metadados (`tags`, `kind`, `priority`, `scope`, `workspace_evidence_required`)
- batch com `section_contains` e headings para leitura focada
- resolução composta com separação entre `normative_ids` e `supporting_ids`
- checklist por cenário a partir de `checklists.yaml`
- deteção de conflitos com regras explícitas de precedência (scope > kind > priority)
- telemetria sem conteúdo + relatório agregado em `scripts/build_quality_report.py`

## Artefactos principais

- Código:
  - [`mcp-instructions-server/corporate_instructions_mcp/server.py`](../../../mcp-instructions-server/corporate_instructions_mcp/server.py)
  - [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py)
  - [`mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`](../../../mcp-instructions-server/corporate_instructions_mcp/context_resolver.py)
  - [`mcp-instructions-server/corporate_instructions_mcp/markdown_sections.py`](../../../mcp-instructions-server/corporate_instructions_mcp/markdown_sections.py)
  - [`mcp-instructions-server/corporate_instructions_mcp/search_contract.py`](../../../mcp-instructions-server/corporate_instructions_mcp/search_contract.py)
  - [`mcp-instructions-server/corporate_instructions_mcp/checklists.yaml`](../../../mcp-instructions-server/corporate_instructions_mcp/checklists.yaml)
  - [`mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`](../../../mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml)
- Docs:
  - [`mcp-instructions-server/docs/QUALITY-DASHBOARD.md`](../../../mcp-instructions-server/docs/QUALITY-DASHBOARD.md)
  - [`mcp-instructions-server/docs/SYNONYMS-GOVERNANCE.md`](../../../mcp-instructions-server/docs/SYNONYMS-GOVERNANCE.md)
  - [`mcp-instructions-server/docs/SYNONYMS-CHANGELOG.md`](../../../mcp-instructions-server/docs/SYNONYMS-CHANGELOG.md)

## Critérios de aceite alinhados à implementação

- [x] `pip install -e .` suportado pelo projeto.
- [x] Com `INSTRUCTIONS_ROOT` apontando para [`fixtures/instructions`](../../../fixtures/instructions), as 6 tools devolvem JSON válido.
- [x] `search_instructions` expõe diagnósticos suficientes para tuning semântico/heurístico.
- [x] `get_instructions_batch` suporta foco por secção sem exigir leitura integral de cada documento.
- [x] `resolve_instruction_context` devolve pacote composto utilizável por agente/cliente.
- [x] `get_normative_checklist` devolve readiness e evidências por cenário.
- [x] `detect_instruction_conflicts` devolve conflitos, severidade e guidance de precedência.
- [x] `pytest -q` no servidor passa com smoke, integração e unit tests.

## Fora de escopo deste épico

- embeddings / busca vetorial;
- escrita no corpus via MCP;
- reindexação automática em tempo real;
- resolução de regras de negócio específicas do produto.

## Limite arquitetural explícito

Integrações de negócio específicas, como `ViaCEP`, nomes de fornecedores, shape de payload local ou estados de domínio como “validação pendente”, **não** pertencem ao corpus central por defeito. Esse tipo de regra deve viver em **instruction local** ou no código do repositório-alvo, enquanto o MCP central cobre apenas guardrails transversais.
