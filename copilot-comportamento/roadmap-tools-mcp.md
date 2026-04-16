## Objetivo

Registrar, de forma “produto”, quais **tools adicionais** fazem mais diferença para reduzir custo de tokens, aumentar determinismo do retrieval e habilitar loops de validação.

Este documento não altera o servidor por si só; ele orienta priorização e mantém o `copilot-instructions.md` (thin) honesto sobre o que existe hoje.

## Baseline (tools atuais)

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch`

## Propostas priorizadas

### Fase 1 (alto impacto, baixo esforço)

- **`resolve_instructions_for_file(file_path)`**: dado um path, retornar instruções cujo `scope` faz match, ordenadas por `priority`. Evita o Copilot “fazer matching mental” e errar.
- **`get_project_profile(project_type)`**: bootstrap por tipo de serviço (ex.: `api-microservice`, `worker-service`) retornando lista de instruction IDs e metadados do perfil.

### Fase 2 (scaffold e vocabulário)

- **`get_code_template(template_id, parameters?)`**: templates aprovados (scaffold) para padrões frequentes.
- **`get_glossary(term?)`**: glossário central para termos/abreviações e regras de nomenclatura.

### Fase 3 (drift e conformidade)

- **`check_instruction_updates(known_hashes?)`**: diff por `content_sha256` (added/changed/removed).
- **`validate_compliance(code_snippet, file_path?, instruction_ids?)`**: verificação leve (regex/rules) para suportar loop **generate → evaluate → fix**.
- **`check_applicability` (nome indicativo)** ou metadado em policy (`requires_code_evidence`): reduzir casos em que uma **policy concreta** do corpus prevalece sobre conservadorismo no thin sem evidência no código — motivação documentada na síntese [`research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-2.md`](../research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-2.md) (critério 4, recomendações para v3).

## Regras de integração (importante)

- O thin por repo só deve orquestrar **tools que existem** (ver `mcp-instructions-server/README.md`).
- Quando uma nova tool for implementada, atualizar:
  - README do servidor
  - template thin (se ele citar a tool)
  - checklist de validação (se a tool virar obrigatória)

