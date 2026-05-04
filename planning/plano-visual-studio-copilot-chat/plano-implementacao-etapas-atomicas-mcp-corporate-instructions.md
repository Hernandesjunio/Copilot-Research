# Plano de implementação em etapas atômicas — MCP `corporate_instructions*`

Documento derivado de [`especificacao-final-evolucao-incremental-mcp-corporate-instructions.md`](especificacao-final-evolucao-incremental-mcp-corporate-instructions.md). Cada etapa abaixo deve ser **mergeável sozinha** e ter **teste(s) que provem o comportamento** antes de avançar.

**Princípio:** ordem = dependências técnicas + risco. Nada de “grande PR” sem um gate de teste no fim do slice.

---

## Visão geral do pipeline a validar (referência)

```
list_instructions_index | search_instructions
  → resolve_instruction_context (P1; preparatório)
  → get_instructions_batch
  → validate_applicability (P0)
  → build_compliance_matrix (P0)
```

Testes manuais com a “outra IA” fazem sentido **após P0 completo**; antes disso, use testes automatizados + smoke no cliente MCP.

---

## Fase 0 — Congelamento e baseline (sem lógica nova de negócio)

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| 0.1 | **Checklist de contrato** | Tabela única: estados de `validate_applicability`, estados da matrix, regra default sem `on_absence`, contrato mínimo de `workspace_evidence` (rico + strings), política aditiva. | Revisão; nenhum código obrigatório. |
| 0.2 | **Baseline de regressão** | Rodar suíte atual do servidor contra `fixtures/instructions/`; capturar saída relevante (ou snapshot aprovado) como “antes”. | `pytest` (ou comando do repo) verde; diff vazio em tools existentes. |
| 0.3 | **Estrutura de testes P0** | Diretório/arquivo de testes dedicado a P0 (vazio ou skip) para não misturar com testes legados. | Coleta de testes encontra o módulo; CI verde. |

**Gate Fase 0:** baseline verde + contrato escrito alinhado à secção 9 da especificação.

---

## P0 — Evidence gate + matrix (valor principal)

### Bloco A — Fundações compartilhadas (sem expor tool ainda)

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P0.A1 | **Normalização de path** | `normalize_path` (Windows `\`, trim, lower para case-insensitive). | Testes unitários: pares entrada/saída. |
| P0.A2 | **`match_scope`** | Glob real (`fnmatch`) conforme pseudocódigo da spec; `scope` vazio = match. | Testes: match/mismatch, glob `**`, case Windows. |
| P0.A3 | **Parse de `workspace_evidence`** | Aceitar lista de strings e lista de objetos com `value` mínimo; normalizar para modelo interno; preservar `evidence_type` (`positive` / `negative` / `absence_observed`). | Testes: exemplos da secção 8.3 e 8.4. |

**Gate A:** apenas funções puras + testes; nada no manifest MCP.

### Bloco B — `validate_applicability` (incremental)

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P0.B1 | **Registro MCP + validação de entrada** | Tool exposta; rejeitar `instruction_ids` vazios / duplicados (se spec exigir distintos); `target_artifact.path` obrigatório; evidência opcional válida. | Testes: erros de validação JSON/contrato. |
| P0.B2 | **Resolução de instruction** | Se ID inexistente no índice → **erro estruturado** (spec 10.1). | Teste: ID fake → erro documentado. |
| P0.B3 | **Só escopo** | Se `scope` não casa → `non_applicable` + razão; diagnostics com `scope_match_strategy: glob`. | Teste critério aceite 1. |
| P0.B4 | **`kind = reference`** | Em escopo → `hypothesis_only` (sem obrigação forte). | Teste critério aceite 6. |
| P0.B5 | **Sem `workspace_evidence_required`** | Em escopo → `applicable`. | Teste critério aceite 2. |
| P0.B6 | **`workspace_evidence_required` sem sinais** | `workspace_signals` ausente ou vazio → `blocked_by_missing_evidence` + diagnóstico. | Teste regra P0 suficiência. |
| P0.B7 | **Com `workspace_signals` + evidência** | Matched/missing; ramos `applicable`, `hypothesis_only`, `on_absence`, default `blocked_by_missing_evidence`. | Testes critérios 3–5 + lista string + estruturada + negativa. |
| P0.B8 | **Polimento de saída** | `summary`, `diagnostics` estáveis (contagens, `used_on_absence`). | Teste snapshot de forma (campos obrigatórios). |

**Gate B:** todos os 10 itens de teste obrigatórios da secção 16.1 para `validate_applicability` cobertos.

### Bloco C — `build_compliance_matrix` (incremental)

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P0.C1 | **Registro + validação** | Entrada: `target_artifact`, `instruction_results` não vazio; itens com `instruction_id`, `kind`, `applicability`. | Testes de rejeição. |
| P0.C2 | **Mapeamentos mecânicos** | `non_applicable` → `not_applicable`; `hypothesis_only` / `blocked_by_missing_evidence` → `not_enforceable`. | Testes secção 16.1 itens 1–3. |
| P0.C3 | **Ramo `applicable` + observações** | Filtrar observações por `instruction_id`; pseudocódigo `positive` / `gap` / `deviation`; `summary` agregado. | Testes itens 4–7. |
| P0.C4 | **`allowed_action` / `reason`** | Textos curtos; sem `non_conformance` só por ausência genérica de evidência. | Testes anti-alucinação (secção 10.2 + 17). |

**Gate C:** todos os 7 testes obrigatórios da secção 16.1 para `build_compliance_matrix`.

### Bloco D — Integração

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P0.D1 | **Smoke end-to-end** | Script ou teste: `list` → `resolve` (opcional) → `batch` → `validate_applicability` → `build_compliance_matrix` com fixture mínima. | Um cenário verde no CI ou documentado em `docs/TESTS.md`. |
| P0.D2 | **Checklist para a outra IA** | Prompt curto com parâmetros de exemplo (path, evidência, observações). | Validação manual uma vez. |

**Gate P0:** secções 10.1–10.2 + 16.1 satisfeitas; nenhuma remoção de campos em tools existentes.

---

## P1 — `resolve_instruction_context` (aditivo)

Implementar **um campo novo por slice** (ou dois estreitamente acoplados), sempre com o mesmo padrão: preenchimento opcional + teste que o campo aparece e não quebra payload antigo.

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P1.1 | `selection_rationale` | Lista `{ instruction_id, why_selected }`. | Teste aceite P1.1; payload legado inalterado em campos antigos. |
| P1.2 | `pending_evidence` | Lista `{ instruction_id, reason }` quando policy pede evidência. | Teste aceite P1.2. |
| P1.3 | `required_workspace_signals` | Mapa `instruction_id → lista` a partir do frontmatter. | Teste aceite P1.3. |
| P1.4 | `next_repo_evidence_actions` | Lista de strings acionáveis (ex.: buscas sugeridas). | Teste aceite P1.4. |

**Gate P1:** testes secção 16.2; nenhuma mudança semântica em campos existentes (spec 11).

---

## P2 — Discovery e saúde do corpus

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P2.1 | **`list_instructions_index` saúde** | Campos aditivos: `status`, `index_health`, `warnings`, `errors`. | Testes 16.3: ok / partial / error. |
| P2.2 | **`search_instructions` multi-query (opcional)** | Entrada `queries` + saída por query + `consolidated` estável. | Testes 16.3: query única intacta; multi-query e consolidado. |

**Gate P2:** não bloqueia validação com a outra IA; pode ser paralelo a P1 após P0 estável.

---

## P3 — Refinamentos não críticos

| ID | Etapa atômica | Entrega | Como testar |
|----|----------------|---------|-------------|
| P3.1 | **`get_normative_checklist`** | Classificação `mandatory` / `recommended` / `conditional_on_evidence`. | Testes por tipo; regressão checklist. |
| P3.2 | **`detect_instruction_conflicts`** | Severidade, explicação, flags de decisão humana (conforme spec 13.2). | Testes de forma + cenários do fixtures. |

---

## P4 — Explícito fora do primeiro ciclo

Registrar issues ou secção de backlog para: parsing `must`/`must_not`, auditoria formal, scoring avançado (spec secção 14–15).

---

## Ordem recomendada de merges (resumo)

1. **Fase 0** → baseline verde.  
2. **P0.A** → **P0.B1–B8** → **P0.C1–C4** → **P0.D**.  
3. **P1.1–P1.4** (sequencial ou P1.1–P1.2 em paralelo se equipes diferentes).  
4. **P2** / **P3** quando P0 estiver em produção interna e estável.

---

## Riscos e mitigação rápida

| Risco | Mitigação no slice |
|--------|---------------------|
| Divergência semântica entre implementações | Fase 0 escrita; enums copiados da spec; testes nomeados com número do critério de aceite. |
| Regressão em tools existentes | Teste de snapshot ou contrato mínimo por tool após cada PR que toque servidor compartilhado. |
| Glob `scope` incorreto | Só mergear P0.A2 após tabela de exemplos acordada nos testes. |
| Matrix afirma conformidade cedo demais | Implementar P0.C3 estritamente após `validate_applicability` estável; nunca pular `applicable` sem observações quando a spec exige insuficiência. |

---

## Definição de “pronto para testar com a outra IA”

- P0.D1 verde.  
- Prompt de convite com: `instruction_ids`, `target_artifact.path`, `workspace_evidence` de exemplo, e para matrix um conjunto mínimo de `artifact_observations`.  
- Lista dos estados finais permitidos colada no prompt (evitar mistura aplicabilidade vs matrix).

Este arquivo pode ser usado como checklist de PR: cada linha da tabela = um commit ou PR pequeno com seu teste correspondente.
