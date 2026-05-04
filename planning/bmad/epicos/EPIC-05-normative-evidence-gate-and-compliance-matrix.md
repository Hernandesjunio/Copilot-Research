# EPIC-05 — Evidence gate normativo + matrix operacional (`corporate_instructions*`)

## Objetivo

Evoluir o MCP normativo `corporate_instructions*` com **duas novas tools centrais** e um reforço incremental do resolvedor, para aumentar utilidade de orquestração por outra IA sem regressão:

- **`validate_applicability`**: evidence gate formal (aplicabilidade) baseado em `frontmatter` + evidência fornecida.
- **`build_compliance_matrix`**: matrix operacional (conformidade) baseada em aplicabilidade + observações do artefato.
- **P1**: fortalecer `resolve_instruction_context` como camada preparatória (campos aditivos), sem substituir as tools acima.

O resultado esperado é reduzir alucinação normativa: **na dúvida, retornar estados conservadores com razão curta** (não afirmar conformidade/violação sem evidência).

## Estado implementado

Este épico representa a próxima evolução incremental (P0/P1/P2) do servidor atual.

O servidor MCP já expõe:

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch`
- `resolve_instruction_context`
- `get_context_triggers`
- `get_normative_checklist`
- `detect_instruction_conflicts`

E o corpus já contém base para evidence gate em algumas policies (`workspace_evidence_required`, `workspace_signals`, `on_absence`).

## Motivação (problema a resolver)

Hoje falta uma separação explícita e auditável entre:

- **aplicabilidade** (em escopo? pode exigir evidência? a evidência existe?)
- **conformidade operacional** (com base em observações do artefato, afirmar conformant/partial/non_conformance?)

Sem isso, o orquestrador tende a:

- misturar ausência de evidência com não conformidade;
- “enforcement” fraco baseado em texto;
- dificuldade para automatizar coleta de evidências e reavaliar.

## Artefactos principais

### Código (servidor MCP)

- [`mcp-instructions-server/corporate_instructions_mcp/server.py`](../../../mcp-instructions-server/corporate_instructions_mcp/server.py)
- [`mcp-instructions-server/corporate_instructions_mcp/indexing.py`](../../../mcp-instructions-server/corporate_instructions_mcp/indexing.py)
- [`mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`](../../../mcp-instructions-server/corporate_instructions_mcp/context_resolver.py)
- possíveis módulos novos ou extensão dos módulos atuais para aplicabilidade e matrix (a definir na implementação)

### Docs/Specs de referência

- Especificação final: [`planning/plano-visual-studio-copilot-chat/especificacao-final-evolucao-incremental-mcp-corporate-instructions.md`](../../plano-visual-studio-copilot-chat/especificacao-final-evolucao-incremental-mcp-corporate-instructions.md)
- Testes do servidor: [`mcp-instructions-server/docs/TESTS.md`](../../../mcp-instructions-server/docs/TESTS.md)

## Contratos e estados (baseline semântico)

### Estados oficiais de `validate_applicability`

- `applicable`
- `non_applicable`
- `hypothesis_only`
- `blocked_by_missing_evidence`

### Estados oficiais de `build_compliance_matrix`

- `conformant`
- `partial_conformance`
- `non_conformance`
- `not_enforceable`
- `not_applicable`
- `insufficient_evidence`

### Regra-chave anti-alucinação

Ausência de evidência **não** é não conformidade. A matrix não deve produzir `non_conformance` só por falta genérica de sinais/observações.

## Roadmap sequencial (mergeável em PRs pequenos)

### Fase 0 — Congelamento semântico e baseline técnico

Objetivo: fechar contratos e reduzir ambiguidade antes de implementar.

- [ ] Congelar enums/estados oficiais (aplicabilidade e matrix).
- [ ] Congelar default de `on_absence` para cenários sem declaração explícita.
- [ ] Congelar regra de `scope` com glob normalizado (Windows case-insensitive).
- [ ] Congelar contrato de `workspace_evidence` (lista de strings + objetos com `value`).
- [ ] Congelar política de retrocompatibilidade (mudanças apenas aditivas nas tools existentes).
- [ ] Congelar critérios mínimos de suficiência de evidência para P0.
- [ ] Baseline: suíte atual do servidor verde apontando para `fixtures/instructions`.

### P0 — Evidence gate formal + matrix operacional (valor principal)

#### P0.A — Fundações compartilhadas (funções puras + testes)

- [ ] `normalize_path` (Windows `\\` → `/`, trim, lower).
- [ ] `match_scope` com glob real (preferir `fnmatch` / equivalente) e diagnóstico de estratégia.
- [ ] Parse/normalização de `workspace_evidence` (strings e objetos; `evidence_type` suportado).
- [ ] Regra semântica de `evidence_type`: `positive`, `negative`, `absence_observed` com comportamento conservador explícito.

#### P0.B — Tool nova: `validate_applicability`

Entregas incrementais (cada item idealmente um PR):

- [ ] Registrar tool + validação de entrada (`instruction_ids`, `target_artifact.path`, `workspace_evidence` opcional).
- [ ] ID inexistente → erro estruturado.
- [ ] `scope` não casa → `non_applicable`.
- [ ] `kind = reference` em escopo → `hypothesis_only`.
- [ ] `workspace_evidence_required = false` em escopo → `applicable`.
- [ ] `workspace_evidence_required = true` com `workspace_signals` ausente/vazio → `blocked_by_missing_evidence`.
- [ ] Matching de sinais + ramos: `applicable`, `hypothesis_only`, `on_absence`, default conservador.
- [ ] Evidência `negative` / `absence_observed` bloqueia enforcement e reforça estados conservadores; não vira não conformidade sozinha.
- [ ] Saída estável: `matched/missing`, `diagnostics`, `summary`.

**Aceite P0.B (testes obrigatórios):** cumprir os 10 testes listados na secção “16.1 Testes obrigatórios de P0” da especificação.

#### P0.C — Tool nova: `build_compliance_matrix`

Entregas incrementais:

- [ ] Registrar tool + validação de entrada (`instruction_results` não vazio; itens mínimos).
- [ ] Mapeamentos mecânicos: `non_applicable → not_applicable`, `hypothesis_only/blocked → not_enforceable`.
- [ ] Ramo `applicable` + `artifact_observations`: `conformant`, `partial_conformance`, `non_conformance`, `insufficient_evidence`.
- [ ] “allowed_action” e “reason” curtos + regra anti-alucinação (sem `non_conformance` por ausência genérica).

**Aceite P0.C (testes obrigatórios):** cumprir os 7 testes listados na secção “16.1 Testes obrigatórios de P0” (matrix) da especificação.

#### P0.D — Integração e pronto para validação com outra IA

- [ ] Smoke end-to-end com fixture mínima: `list/search → resolve → batch → validate_applicability → build_compliance_matrix`.
- [ ] Prompt/checklist de validação manual (uma vez) com inputs de exemplo.

#### P0.E — Piloto mínimo de corpus para demonstrar valor

- [ ] Escolher 1–3 policies reais do corpus com potencial de evidence gate.
- [ ] Verificar se já possuem `workspace_evidence_required`, `workspace_signals`, `on_absence` e `scope` suficientes; completar apenas onde fizer sentido.
- [ ] Confirmar que o piloto continua com template enxuto de frontmatter, sem introduzir YAML complexo nem parsing estrutural de markdown.

**Aceite P0.E:** existe ao menos um cenário real em que o novo evidence gate diferencia corretamente `applicable`, `hypothesis_only` e `blocked_by_missing_evidence` sem exigir reestruturação global do corpus.

### P1 — Fortalecer `resolve_instruction_context` (camada preparatória)

Campos aditivos (um por PR):

- [ ] `selection_rationale`
- [ ] `pending_evidence`
- [ ] `required_workspace_signals`
- [ ] `next_repo_evidence_actions`

**Aceite P1:** cumprir os 5 testes listados na secção “16.2 Testes obrigatórios de P1” da especificação sem quebrar payload atual.

### P2 — Discovery e saúde do corpus (depois de P0/P1 estáveis)

- [ ] `list_instructions_index`: `status`, `index_health`, `warnings`, `errors`
- [ ] `search_instructions` multi-query opcional + saída consolidada estável

**Aceite P2:** cumprir os testes listados na secção “16.3 Testes obrigatórios de P2” da especificação.

## Critérios de aceite alinhados à implementação

- [ ] As novas tools (`validate_applicability`, `build_compliance_matrix`) devolvem JSON válido e auditável.
- [ ] Mudanças em tools existentes são **estritamente aditivas** (sem remoção/alteração silenciosa).
- [ ] `pytest -q` no servidor passa com unit + integração para P0/P1.
- [ ] Com `INSTRUCTIONS_ROOT` apontando para `fixtures/instructions`, smoke end-to-end (P0.D) funciona.
- [ ] Com evidência insuficiente, o sistema retorna estados conservadores (sem afirmação forte).
- [ ] Evidência negativa ou `absence_observed` nunca gera `non_conformance` sozinha.
- [ ] O piloto mínimo de corpus demonstra valor sem exigir mudança estrutural ampla no corpus.

## Fora de escopo deste épico

- parsing estrutural de markdown (`must`, `must_not`, `decision_rules`, `stop_rules`);
- auditoria formal completa / scoring avançado;
- mudanças profundas no corpus (YAML complexo, taxonomias grandes);
- reescrita total de `search_instructions` e `resolve_instruction_context` (apenas evolução aditiva em P1/P2).

## Limite arquitetural explícito

As novas tools não devem “inventar” regras de negócio do produto. O MCP central continua a cobrir guardrails transversais; detalhes de domínio local (fornecedores, shapes específicos, estados de negócio) permanecem em instruction local e no código do repositório-alvo.

