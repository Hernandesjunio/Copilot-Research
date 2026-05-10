# EPIC-06 — Gap analysis de uso real com agente (MCP tools + orquestração)

## Objetivo

Documentar, com base em evidências, os problemas observados entre:

- planejamento original da evolução do MCP;
- implementação entregue (P0/P1/P2);
- testes automatizados que passaram;
- comportamento real durante consumo via agente.

Este documento consolida **issues sistêmicas** para investigação e redesign, sem implementação nesta etapa.

## Contexto do problema

Foi observada divergência entre o comportamento esperado no planejamento e o comportamento em uso real com agente:

- tools novas e testes unitários/integrados estão verdes;
- durante simulação/consumo real, parte do fluxo não se comporta como esperado para orquestração robusta;
- há sinais de desalinhamento entre contrato de tool, instruções de consumo e comportamento de chamada de LLM.

## Escopo de análise

1. Reconstrução da intenção original.
2. Mapeamento do comportamento implementado.
3. Gap analysis planejamento vs implementação.
4. Avaliação crítica dos testes existentes.
5. Causas prováveis da diferença entre testes e uso real.
6. Avaliação de contrato das tools MCP.
7. Avaliação específica da tool de orquestração.

---

## 1) Reconstrução da intenção original

| Item | Intenção planejada | Evidência encontrada | Observação |
|---|---|---|---|
| Objetivo do EPIC-05 | Separar formalmente aplicabilidade vs conformidade, com estados conservadores | `planning/bmad/epicos/EPIC-05-normative-evidence-gate-and-compliance-matrix.md`; `planning/plano-visual-studio-copilot-chat/especificacao-final-evolucao-incremental-mcp-corporate-instructions.md` | Intenção está consistente e explícita |
| `validate_applicability` | Decidir apenas aplicabilidade (`applicable`, `non_applicable`, `hypothesis_only`, `blocked_by_missing_evidence`) | Especificação seção 10.1; implementação em `mcp-instructions-server/corporate_instructions_mcp/applicability.py` | Aderente ao planejamento |
| `build_compliance_matrix` | Consolidar status operacional com base em aplicabilidade + observações | Especificação seção 10.2; implementação em `applicability.py` e `server.py` | Aderente, porém com validação semântica fraca de observações |
| `resolve_instruction_context` (P1) | Camada preparatória aditiva, sem substituir applicability/matrix | Especificação seção 11; implementação em `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py` | Entrega feita, mas com sinais de pré-decisão excessiva |
| Tool de orquestração (`get_context_triggers`) | Orquestrar sequência de contexto, sem executar nem concluir em excesso | `planning/plano-visual-studio-copilot-chat/copilot-instructions.md`; docstring em `context_triggers.py` | Objetivo era orquestrador thin |
| Comportamento real esperado | Fluxo completo: discover -> resolve -> batch -> applicability -> matrix | `planning/plano-visual-studio-copilot-chat/plano-implementacao-etapas-atomicas-mcp-corporate-instructions.md` | Fluxo alvo não está totalmente refletido no encadeamento sugerido pela orquestração |
| Premissas | Evolução aditiva, anti-alucinação e conservação sob incerteza | Especificação seções 5, 8 e 17 | Premissas corretas; problema está na operacionalização sob chamada LLM |

---

## 2) Mapeamento do comportamento implementado

| Tool | Responsabilidade real | Entrada | Saída | Decisões internas | Riscos encontrados |
|---|---|---|---|---|---|
| `get_context_triggers` | Classifica cenário e devolve estratégia/roteiro/stop/evidence gate | `input_payload` como string JSON com contrato estrito | Estratégia detalhada, `tool_sequence`, `stop_rules`, `advanced_signals` | Heurísticas por flags de entrada e estado declarado | Contrato pesado para LLM; chance alta de erro de chamada; risco de decidir além da orquestração |
| `resolve_instruction_context` | Faz search + batch e compõe contexto acionável | `query`, `max_results`, `include_diagnostics` | `selected_ids`, `resolution`, `implementation_brief`, campos P1 | Seleção heurística de policy/reference e priorização contextual | Pode induzir decisão antes de `validate_applicability`/`build_compliance_matrix` |
| `validate_applicability` | Evidence gate formal por instruction | `instruction_ids`, `target_artifact.path`, `workspace_evidence` | `results` + `summary.by_applicability` | Scope glob + matching textual de sinais/evidências | Matching permissivo pode gerar falso positivo |
| `build_compliance_matrix` | Consolida estado operacional | `instruction_results`, `artifact_observations`, `target_artifact.path` | `matrix` + `summary` | Mapeamento mecânico de estados e observações | Observação fraca pode resultar em `conformant` sem robustez semântica suficiente |
| `search_instructions` | Discovery textual + contexto composto | `query` e/ou `queries` | `results`, `consolidated`, `composed_context` | Ranking, expansão de termos, consolidação multi-query | `composed_context` pode ser usado como resposta final prematura |
| `get_instructions_batch` | Leitura canônica do corpus + frontmatter | `ids` CSV e filtros opcionais | Conteúdo, truncagem, frontmatter parseado, `missing_ids` | Limites de tamanho e filtragem de seção | Bom contrato técnico; não força etapa posterior de gate |
| `list_instructions_index` | Inventário e saúde do índice | sem args | `status`, `index_health`, `warnings`, `errors`, `instructions` | Rebuild e warnings de indexação | Sem risco crítico relevante |

---

## 3) Gap analysis — planejamento versus implementação

| Gap | Planejado | Implementado | Impacto | Consequência provável no agente real |
|---|---|---|---|---|
| Sequência de orquestração incompleta | Orquestração deveria sustentar pipeline completo com gates finais | `tool_sequence` não explicita applicability/matrix no roteiro | Crítico | Agente pode encerrar fluxo sem evidence gate formal e matrix |
| Contrato de entrada da orquestração | Uso robusto por agente real | Payload string JSON com muitos campos obrigatórios e flags | Alto impacto | Falha de chamada, simplificação indevida ou preenchimento artificial |
| Thin orchestrator | Orquestrar sem pré-concluir decisão | Saída inclui recomendações e sinais de pré-decisão | Alto impacto | Ambiguidade entre decisão do agente e decisão implícita da tool |
| Stop rules orientadas por evidência reconciliada | Stop deveria refletir reconciliação com evidências reais | Stop deriva majoritariamente de flags declarativas de request/workspace | Alto impacto | Stop prematuro/excessivo ou bloqueio fora de contexto |
| Suficiência de evidência | Critério conservador e auditável | Matching textual por inclusão (bidirecional) | Médio impacto | `applicable` com evidência fraca |
| Conformidade operacional | Não afirmar conformidade cedo | `conformant` pode surgir com observação positiva mínima | Alto impacto | Falso senso de aderência operacional |
| Alinhamento planejamento/testes/execução | Testes deveriam representar fluxo real com agente | Predomínio de cenários determinísticos e “inputs limpos” | Crítico | Testes verdes sem capturar falhas de uso real |

---

## 4) Avaliação dos testes unitários e de integração existentes

| Teste | O que valida | Limitação | Risco | Novo teste recomendado |
|---|---|---|---|---|
| `tests/test_epic05_tools.py` | Estados oficiais de applicability/matrix | Cenários artificiais, controlados e determinísticos | Cobertura semântica insuficiente para input LLM | Casos com evidência ruidosa/ambígua/contraditória e assert de conservadorismo |
| `tests/test_context_triggers.py` | Contrato e invariantes de roteamento | Payloads perfeitos e completos | Não mede robustez contra payload natural de agente | Matriz com payload incompleto/parcial e validação de degradação segura |
| `tests/smoke_test.py` | Sanidade de tools e regressão geral | Foco em shape e caminho feliz | Fluxo real de orquestração pode quebrar sem ser detectado | Smoke encadeado completo com decisão final validada |
| `tests/integration_mcp_stdio_test.py` | Protocolo stdio real e presença de tools | Predomínio de chamadas guiadas e previsíveis | Não replica cadeia emergente de decisão de LLM | Testes de jornada fim-a-fim por cenário real de prompt |
| `scripts/run_epic05_stdio_real_check.py` | Verificação real resumida de requisitos P0/P1/P2 | Pouca variabilidade de cenários | Confiança excessiva em sanidade pontual | Expandir para suíte parametrizada com cenários ambíguos |
| Simulação v1/v2 em `research/experimentos-mcp/...` | Evidência prática de uso real e lacunas | Processo manual, sem gate automatizado | Regressões futuras sem alerta automático | Transformar cenários v2 em regressão automatizada (golden checks) |

---

## 5) Causas prováveis da diferença entre teste e uso real

| Prioridade | Causa provável | Evidência | Como validar | Possível correção |
|---|---|---|---|---|
| 1 | Contrato da orquestração complexo para LLM | `get_context_triggers` exige JSON string detalhado | Medir taxa de erro com payloads gerados por agente real | Simplificar contrato para objeto tipado + defaults robustos |
| 2 | Roteiro de tools não fecha pipeline P0 final | Ausência explícita de applicability/matrix no encadeamento recomendado | Replay de cenários e inspeção da sequência efetivamente chamada | Explicitar sequência obrigatória pós-batch |
| 3 | Ambiguidade de responsabilidade entre tools | `get_context_triggers` e `resolve_instruction_context` ambos influenciam decisão | Traçar chamadas e pontos de decisão em simulação | Redefinir fronteiras de responsabilidade |
| 4 | Stop rules baseadas em flags declarativas | `should_stop` em `context_triggers.py` depende de `mentions_*` | Comparar cenários com evidência reconciliada versus flags iguais | Mover stop final para fase pós-evidence-gate |
| 5 | Testes focados em retorno técnico, não utilidade contextual | Asserts majoritariamente estruturais | Rubrica de utilidade sobre saída final em cenários reais | Acceptance tests por resultado útil e justificável |
| 6 | Matching de evidência textual permissivo | `_signal_matches_signal_value` usa contains bidirecional | Casos de falso positivo com termos genéricos | Fortalecer matching com limites semânticos e score mínimo |
| 7 | Instruções de consumo dependem de disciplina do agente | `copilot-instructions-mcp.md` orienta, mas não impõe checkpoints verificáveis | A/B com prompts curtos e ambíguos | Protocolo com gates explícitos e critérios observáveis |

---

## 6) Avaliação do contrato das tools MCP

| Tool | Problema no contrato | Por que confunde o agente | Ajuste recomendado |
|---|---|---|---|
| `get_context_triggers` | Entrada via string JSON extensa | Alto custo cognitivo e erro de serialização/tipo | Receber objeto tipado diretamente |
| `get_context_triggers` | Saída ampla com sinais quase conclusivos | Pode substituir indevidamente decisão do agente | Restringir saída para roteamento + precondições |
| `resolve_instruction_context` | `implementation_brief` e `next_actions` com tom prescritivo | Agente pode pular applicability/matrix | Sinalizar explicitamente `requires_applicability_gate=true` |
| `search_instructions` | `composed_context` forte para consumo direto | Incentiva uso sem batch/evidence gate | Marcar como contexto preliminar não-prescritivo |
| `validate_applicability` | Ausência de score de força/confiança da evidência | Decisão binária forte sem gradação | Incluir `evidence_strength` e `decision_confidence` |
| `build_compliance_matrix` | Observações com baixa restrição semântica | Conclusões de conformidade podem ficar frágeis | Reforçar schema de observação e rastreabilidade |
| Conjunto de tools | Falta contrato explícito de sequência operacional | Chamadas fora de ordem pelo LLM | Publicar precondições/pós-condições por tool |

---

## 7) Avaliação da tool de orquestração (recomendação objetiva)

```text
Manter como está:
não

Motivo:
A implementação atual de orquestração concentra decisões demais para uma tool que deveria ser thin.
O contrato de entrada é complexo para uso natural por LLM e a saída não força claramente o fluxo
completo de evidence gate e compliance matrix.

Alteração recomendada:
1) Redesenhar `get_context_triggers` para orquestração estrita (roteamento e precondições).
2) Simplificar contrato de entrada (objeto tipado, menos campos obrigatórios, defaults).
3) Explicitar no roteiro o fluxo pós-batch: `validate_applicability` -> `build_compliance_matrix`.
4) Expor modo debug/trace de decisão (sinais, regras ativadas, motivo do stop).
5) Evitar conclusões prontas na orquestração; retornar evidências e próximos passos.
6) Consolidar fronteiras:
   - `get_context_triggers`: ordem e gates;
   - `resolve_instruction_context`: composição factual;
   - `validate_applicability` e `build_compliance_matrix`: decisão formal.

Risco se não alterar:
Persistência de falso-verde em testes, decisões inconsistentes em uso real com agente,
retrabalho operacional e baixa confiabilidade para automação orientada por policy.
```

---

## Classificação dos issues (priorização inicial)

| ID | Issue | Severidade | Tipo |
|---|---|---|---|
| I-01 | Sequência de orquestração não explicita applicability/matrix | Crítica | Design/Contrato |
| I-02 | Contrato de entrada da orquestração complexo para LLM | Alta | Contrato/Usabilidade |
| I-03 | Ambiguidade entre orquestração e composição contextual | Alta | Arquitetura |
| I-04 | Stop rule baseada em flags, não em reconciliação forte | Alta | Lógica de decisão |
| I-05 | Suficiência de evidência com matching permissivo | Média | Implementação |
| I-06 | Matrix com potencial de conformidade prematura | Alta | Semântica operacional |
| I-07 | Testes não representam adequadamente uso real | Crítica | Qualidade/Testes |

## Próximo passo recomendado (sem codar ainda)

Criar plano de execução em histórias atômicas com critérios de aceite para:

1. redesign de contrato da orquestração;
2. redefinição de responsabilidade entre tools;
3. suíte de testes orientada a uso real por agente;
4. instrumentação de trace de decisão e métricas de aderência do fluxo.

