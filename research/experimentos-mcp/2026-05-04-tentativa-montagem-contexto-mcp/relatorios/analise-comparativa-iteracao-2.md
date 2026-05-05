---
titulo: "Análise comparativa — Outbox + Mensageria (Iteração 2, dados corrigidos)"
data: "2026-05-02"
modelo_analise: "Opus 4.6 (Cursor Agent)"
modelo_execucao: "GitHub Copilot (chat/agent — modelo exato não registrado nos artefatos)"
rubrica: "research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md"
escopo: "Vertical slice: outbox transacional + mensageria + consumidor + idempotência + DLQ em API .NET 8 com Dapper/SQL Server"
iteracao: 2
delta_vs: "analise-comparativa-iteracao-1.md"
ajustes_aplicados:
  - "Correção de métricas do cenário A (Instructions locais) — iteração 1 reportou N/A para dados que existem no artefato"
  - "Reavaliação de notas com métricas completas dos três cenários"
  - "Inclusão de deltas (Δ) em relação à iteração 1"
---

# Análise comparativa — Outbox + Mensageria (Iteração 2)

## Contexto

Esta é a **segunda síntese comparativa**, corrigindo a iteração 1 que apresentou métricas de execução do cenário A como N/A, apesar de o artefato `2026-05-02__cenario-1-outbox-mensageria__instructions-locais.md` conter dados completos (`duracao_ms: 1144556`, `qtd_tool_calls_total: 65`, etc.). A reavaliação utiliza os dados reais dos três artefatos.

Todos os três cenários foram executados sobre o mesmo repositório .NET 8 (API de clientes com Dapper/SQL Server) em 2026-05-02, com fontes distintas de contextualização.

---

## Identificação dos cenários

| Cenário | Rótulo | Artefato | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|---|
| **A** | Instructions locais | `2026-05-02__cenario-1-outbox-mensageria__instructions-locais.md` | `.github/copilot-instructions.md` + `.github/instructions/*` | 7 instructions locais identificadas por ID |
| **B** | MCP (STDIO) | `2026-05-02__cenario-1-outbox-mensageria__mcp.md` | `.github/copilot-instructions.md` + MCP | 10 instructions corporativas via MCP + instruction local |
| **C** | Baseline | `2026-05-02__cenario-1-outbox-mensageria__baseline.md` | Nenhum | Código do repositório + prompt |

---

## Diferença-chave desta iteração (vs iteração 1)

A iteração 1 tratou as métricas de A como N/A e atribuiu notas organizacionais mais baixas ao cenário A. Com os dados corretos:

- **A tem 65 tool calls** (mais que B=57 e C=42) e **duração de ~1145s** (entre B=552s e C=681s).
- **A documenta 7 instructions locais por ID** — não apenas `.github/copilot-instructions.md` genérico.
- **A tem 22 FATO, 4 HIPÓTESE, 6 RISCO** — perfil de rigor comparável a B.

Isso muda fundamentalmente a avaliação dos critérios de aderência, completude e governança para A.

---

## Avaliação por critério (0–10)

### 1) Qualidade do plano

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 7 | +2 | BMAD completo com Background/Mission/Approach/Delivery/Refinamento crítico. 5 passos no Approach com referências a contratos e riscos explícitos. Menciona dependências e critérios técnicos. |
| B — MCP | 7 | 0 | BMAD com refinamento similar. 7 passos no Approach com referência a preservação de contratos e semântica HTTP. Mapeamento de riscos e validação por critérios. |
| C — Baseline | 6 | 0 | Plano detalhado com entidades concretas (tabelas), mas sem ancoragem em padrões corporativos. Trade-offs implícitos. Sem refinamento de riscos estruturado. |

**Evidências:**
- A: seção "Refinamento crítico" com riscos, dependências e critérios técnicos explícitos — ausente na avaliação da iteração 1.
- B: Approach em 7 passos numerados com concerns transversais.
- C: nomeia tabelas no plano mas sem framework de riscos.

**Evolução:** A sobe de 5→7 porque o artefato mostra BMAD estruturado com refinamento crítico, não um plano "enxuto" como caracterizado na iteração 1.

---

### 2) Aderência ao contexto disponível

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 7 | +3 | Identifica 7 instructions locais por ID (`assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-messaging-rabbitmq-publish-consume`, etc.) com mapeamento explícito decisão↔instruction. `DECISIONS_JSON` mostra ancoragem "instruction_local" em 5 de 8 decisões. |
| B — MCP | 8 | 0 | Lista 10 instructions MCP por ID + 1 instruction local. `DECISIONS_JSON` mostra ancoragem "MCP" em 5 de 6 decisões. |
| C — Baseline | 5 | 0 | Decisões ancoradas no código observável. 3 de 5 decisões com ancoragem "inferencia" ou "codigo_repo". Sem referência a normas estruturadas. |

**Evidências:**
- A: seção "Instructions locais aplicáveis e decisões suportadas" lista 7 IDs com decisão suportada por cada. `DECISIONS_JSON` tem 8 decisões, 5 ancoradas em "instruction_local".
- B: seção "Instructions MCP usadas" lista 10 IDs. `DECISIONS_JSON` com 6 decisões, 5 com ancoragem "MCP".
- C: sem referência a corpus. `DECISIONS_JSON` com 5 decisões, 2 "inferencia", 2 "codigo_repo".

**Evolução:** A sobe de 4→7. A iteração 1 ignorou que o artefato de A documenta 7 instructions locais aplicáveis por ID, com mapeamento direto decisão→instruction.

---

### 3) Completude

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 7 | +2 | Cobre outbox, POST/PUT, read-model, idempotência, DLQ, correlação. Documenta 10 arquivos criados + 9 alterados. Métricas completas: 65 tool calls, 1145s, 22 FATO. Lacuna: sem testes automatizados (igual aos outros). |
| B — MCP | 7 | 0 | Mesma cobertura funcional. 17 arquivos de patch. 57 tool calls, 552s. Documenta lacunas MCP explicitamente. |
| C — Baseline | 6 | 0 | Cobertura funcional equivalente. 18 itens de patch, 42 tool calls, 681s. Menos reflexão sobre lacunas. |

**Evidências:**
- A: `qtd_tool_calls_total: 65`, `duracao_ms: 1144556`, `qtd_itens_patch: 19`, `qtd_afirmacoes_FATO: 22`.
- B: `qtd_tool_calls_total: 57`, `duracao_ms: 551974`, `qtd_itens_patch: 17`, `qtd_afirmacoes_FATO: 20`.
- C: `qtd_tool_calls_total: 42`, `duracao_ms: 681019`, `qtd_itens_patch: 18`, `qtd_afirmacoes_FATO: 22`.

**Evolução:** A sobe de 5→7 com métricas reais disponíveis. Os três cenários têm completude funcional muito próxima.

---

### 4) Consistência interna

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 7 | +1 | Decisões se reforçam: instructions locais → guardrails → código. Camadas respeitadas (Interfaces/Modelo/Repositorio/Api). Autoavaliação usa escala 0–2 (desalinhada da rubrica). |
| B — MCP | 7 | 0 | Decisões MCP → guardrails → código. Coerência confirmada no relatório. Mesma escala 0–2 desalinhada. |
| C — Baseline | 6 | 0 | Plano e implementação coerentes. Uma falha de tool recuperada. Sem framework de reforço externo. |

**Evidências:**
- A: 8 decisões no `DECISIONS_JSON`, todas coerentes com as 7 instructions citadas. Sem contradições entre plano e implementação.
- B: 6 decisões coerentes com instructions MCP citadas.
- C: 5 decisões internamente coerentes mas sem reforço externo.
- Todos: escala 0–2 na autoavaliação — artefato do template de execução, não inconsistência lógica.

---

### 5) Centralização efetiva

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 4 | +2 | Instructions versionadas no repo (`.github/instructions/`) com IDs estáveis. Funciona como fonte de verdade local. Limitação: não é central entre repos — cada repo mantém sua cópia. |
| B — MCP | 7 | 0 | Corpus centralizado via servidor MCP com tools de busca/listagem/batch. Atualização central propaga a qualquer repo conectado. |
| C — Baseline | 0 | 0 | Sem mecanismo de centralização. |

**Evidências:**
- A: 7 instructions com IDs estáveis (`assistant-workflow-bmad-planning-and-controlled-inference`, `microservice-messaging-rabbitmq-publish-consume`, etc.) versionadas em Git.
- B: 3 tools MCP de discovery (`list_instructions_index`, `search_instructions`, `get_instructions_batch`).
- C: nenhum mecanismo.

**Evolução:** A sobe de 2→4. A iteração 1 descreveu A como "corpus local genérico (`.github/copilot-instructions.md` apenas)", mas o artefato mostra 7 instructions estruturadas em `.github/instructions/` com IDs.

---

### 6) Governança e auditabilidade

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 5 | +2 | Instructions com IDs estáveis, versionadas em Git. Permite auditoria por histórico do repo. Sem metadados avançados (tags, priority, kind) visíveis no artefato. |
| B — MCP | 7 | 0 | Instructions com frontmatter (id, tags, priority, kind, scope). IDs citados nos relatórios. Auditoria por hash/diff do corpus central. |
| C — Baseline | 0 | 0 | Sem corpus; sem rastreabilidade. |

**Evidências:**
- A: cita 7 IDs de instructions — rastreabilidade direta decisão→instruction. Git provê histórico.
- B: 10 IDs + metadados estruturados (frontmatter YAML).
- C: zero rastreabilidade.

**Evolução:** A sobe de 3→5 por ter IDs estáveis e rastreabilidade por Git. Gap vs B mantém-se pelo frontmatter estruturado do MCP.

---

### 7) Escalabilidade projetada

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 3 | 0 | Escala com cópia entre repos. Risco de divergência explicitado: "versões divergentes de policies, duplicação de conteúdo". Sem sync automático. |
| B — MCP | 6 | 0 | Escala para repos conectados ao mesmo servidor. Limitação: setup local por repo. |
| C — Baseline | 1 | 0 | Não escala. |

**Evidências:**
- A: seção "Escalabilidade em múltiplos repositórios": "risco de drift entre repositórios", "esforço de manutenção: moderado/alto sem automação".
- B: seção "Escalabilidade em 100+ repositórios": "sustenta-se se houver templates/base packages".

---

### 8) Risco de drift entre repositórios (INVERTIDO: maior = pior)

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 7 | 0 | Cópias locais sem sync. Risco de divergência explicitado. |
| B — MCP | 4 | 0 | Consumo central reduz drift do corpus. Risco remanescente em decisões locais. |
| C — Baseline | 10 | 0 | Sem padrão. Divergência silenciosa garantida. |

**Evidências:**
- A: "Riscos operacionais: versões divergentes de policies, duplicação de conteúdo e interpretação inconsistente."
- B: "Drift: risco entre corpus MCP e implementação local ao longo do tempo."

---

### 9) Experiência do desenvolvedor (DX)

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 5 | 0 | "Fluidez: boa na fase de implementação. Previsibilidade: razoável." 65 tool calls, 1 falha, 1 retry. Duração ~19 min. |
| B — MCP | 5 | 0 | "Fluidez: boa no contexto técnico." 57 tool calls, 4 falhas, 3 retries. Duração ~9 min. Mais falhas mas menor duração. |
| C — Baseline | 5 | 0 | "Fluidez: boa para evolução incremental." 42 tool calls, 1 falha, 1 retry. Duração ~11 min. Menos overhead. |

**Evidências:**
- A: `sucessos: 64, falhas: 1, retries: 1, duracao_ms: 1144556`.
- B: `sucessos: 53, falhas: 4, retries: 3, duracao_ms: 551974`.
- C: `sucessos: 41, falhas: 1, retries: 1, duracao_ms: 681019`.

**Nota:** A tem duração significativamente maior (~19 min vs ~9 min de B) apesar de ambos terem semelhante número de tool calls. B teve mais falhas (4 vs 1) mas convergiu mais rápido. C teve menos tool calls e duração intermediária. Todos reportam previsibilidade "parcial/média" — empate.

---

### 10) Maturidade atual da solução

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 5 | +1 | Mecanismo nativo do GitHub Copilot com corpus `.github/instructions/` efetivamente usado (7 instructions). Funcionalidade exercida. |
| B — MCP | 5 | 0 | Servidor funcional com tools de busca e batch. MVP utilizável. Limitações: sem policy de migração, sem cobertura operacional. |
| C — Baseline | 3 | 0 | Não é "solução" — é ausência de solução. Funciona por capacidade intrínseca do modelo. |

**Evidências:**
- A: usou 7 instructions distintas, ancorou 5 de 8 decisões. Mecanismo exercido.
- B: 3 tools MCP + 10 instructions — MVP operacional.
- Ambos chegam ao mesmo nível funcional de maturidade.

**Evolução:** A sobe de 4→5 por exercício efetivo do mecanismo.

---

### 11) Viabilidade corporativa

| Cenário | Nota | Δ | Justificativa |
|---|---|---|---|
| A — Instructions locais | 4 | 0 | Viável para repo individual. Escala corporativa exige automação de sync. Modelo de ownership por repo (não central). |
| B — MCP | 6 | 0 | Ownership central possível. Compatível com múltiplos repos via stdio. Gestão por frontmatter + Git. Dependência: runtime local do servidor. |
| C — Baseline | 1 | 0 | Inviável para governança corporativa. |

---

## Quadro consolidado

| # | Critério | A (Instr. locais) | Δ vs v1 | B (MCP) | Δ vs v1 | C (Baseline) | Δ vs v1 |
|---|---|---|---|---|---|---|---|
| 1 | Qualidade do plano | 7 | +2 | 7 | 0 | 6 | 0 |
| 2 | Aderência ao contexto | 7 | +3 | 8 | 0 | 5 | 0 |
| 3 | Completude | 7 | +2 | 7 | 0 | 6 | 0 |
| 4 | Consistência interna | 7 | +1 | 7 | 0 | 6 | 0 |
| 5 | Centralização efetiva | 4 | +2 | 7 | 0 | 0 | 0 |
| 6 | Governança e auditabilidade | 5 | +2 | 7 | 0 | 0 | 0 |
| 7 | Escalabilidade projetada | 3 | 0 | 6 | 0 | 1 | 0 |
| 8 | Risco de drift (**invertido**) | 7 | 0 | 4 | 0 | 10 | 0 |
| 9 | Experiência do desenvolvedor | 5 | 0 | 5 | 0 | 5 | 0 |
| 10 | Maturidade atual | 5 | +1 | 5 | 0 | 3 | 0 |
| 11 | Viabilidade corporativa | 4 | 0 | 6 | 0 | 1 | 0 |

---

## Agregação

### Média simples (com normalização do drift)

Para o critério 8 (invertido), usa-se `(10 − nota)` na média.

| Cenário | Soma (c1–7, c9–11) + (10−c8) | Média simples (/11) |
|---|---|---|
| A — Instructions locais | 7+7+7+7+4+5+3+(10−7)+5+5+4 = 57 | **5.2** |
| B — MCP | 7+8+7+7+7+7+6+(10−4)+5+5+6 = 71 | **6.5** |
| C — Baseline | 6+5+6+6+0+0+1+(10−10)+5+3+1 = 33 | **3.0** |

**Δ vs iteração 1:**
- A: 4.0 → **5.2** (+1.2) — impacto da correção dos dados.
- B: 6.5 → **6.5** (0) — sem alteração.
- C: 3.0 → **3.0** (0) — sem alteração.

### Média ponderada (pesos da rubrica — 8 critérios com peso definido)

| Critério | Peso | A | B | C |
|---|---|---|---|---|
| 1. Qualidade do plano | 20% | 1.40 | 1.40 | 1.20 |
| 5. Centralização efetiva | 15% | 0.60 | 1.05 | 0.00 |
| 6. Governança | 15% | 0.75 | 1.05 | 0.00 |
| 7. Escalabilidade | 15% | 0.45 | 0.90 | 0.15 |
| 8. Drift (10−nota) | 10% | 0.30 | 0.60 | 0.00 |
| 9. DX | 10% | 0.50 | 0.50 | 0.50 |
| 10. Maturidade | 10% | 0.50 | 0.50 | 0.30 |
| 11. Viabilidade corp. | 5% | 0.20 | 0.30 | 0.05 |
| **Total ponderado** | **100%** | **4.70** | **6.30** | **2.20** |

**Δ vs iteração 1:** A: 3.60 → **4.70** (+1.10).

> **Nota:** os critérios 2 (aderência), 3 (completude) e 4 (consistência) não têm peso explícito na tabela da rubrica (que soma 100% sem eles). Na média ponderada, foram usados apenas os 8 critérios com pesos definidos. Na média simples, todos os 11 critérios contribuem igualmente.

---

## Métricas auxiliares

| Métrica | A (Instr. locais) | B (MCP) | C (Baseline) |
|---|---|---|---|
| Tool calls totais | 65 | 57 | 42 |
| Falhas de tool | 1 | 4 | 1 |
| Retries | 1 | 3 | 1 |
| Arquivos lidos | ~26 | 20 | 20 |
| Arquivos citados | ~22 | 19 | 18 |
| Trechos citados | ~40 | 30 | 20 |
| Duração (ms) | 1.144.556 | 551.974 | 681.019 |
| Itens de patch | 19 | 17 | 18 |
| Afirmações FATO | 22 | 20 | 22 |
| Afirmações HIPÓTESE | 4 | 6 | 3 |
| Afirmações RISCO | 6 | 7 | 4 |
| Bytes lidos (aprox.) | ~120.000 | ~62.000 | N/A |
| Tokens input (est.) | ~26.000 | ~26.000 | N/A |
| Tokens output (est.) | ~9.000 | ~14.500 | N/A |

**Observações:**

1. **A tem mais tool calls que B (65 vs 57)** e duração 2× maior (1145s vs 552s), apesar de ambos produzirem output funcional equivalente. Possíveis causas: mais leituras de ficheiros (26 vs 20), mais trechos citados (40 vs 30), ou diferenças de plataforma/horário.
2. **B tem mais falhas (4) e retries (3)** que A (1/1) e C (1/1), possivelmente pelo overhead de tools MCP e resolução de dependências de pacotes.
3. **Ratio FATO/(HIPÓTESE+RISCO):** A = 2.2, B = 1.5, C = 3.1. C documenta proporcionalmente menos incerteza — possível viés de omissão por ausência de framework de rigor. A e B são mais equilibrados.
4. **Bytes lidos:** A (~120K) leu quase o dobro de B (~62K), sugerindo exploração mais profunda do codebase vs consulta a corpus central.

---

## Evolução do gap entre abordagens

### Gap qualidade (critérios 1–4) vs gap organizacional (critérios 5–8)

| Bloco | A | B | C | Gap A→B | Gap B→C |
|---|---|---|---|---|---|
| Qualidade (1–4, média) | 7.0 | 7.25 | 5.75 | 0.25 | 1.50 |
| Organizacional (5–8 normalizado, média) | 3.75 | 6.5 | 0.25 | 2.75 | 6.25 |

**Interpretação:** O gap entre A e B é **quase nulo em qualidade técnica** (0.25 pontos), mas **significativo em dimensões organizacionais** (2.75 pontos). A abordagem por instructions locais produz planos e código de qualidade técnica comparável ao MCP, mas não resolve centralização, governança e escalabilidade cross-repo.

---

## Evolução ao longo das iterações

| Critério | A (v1) | A (v2) | B (v1) | B (v2) | C (v1) | C (v2) |
|---|---|---|---|---|---|---|
| 1. Qualidade do plano | 5 | 7 | 7 | 7 | 6 | 6 |
| 2. Aderência ao contexto | 4 | 7 | 8 | 8 | 5 | 5 |
| 3. Completude | 5 | 7 | 7 | 7 | 6 | 6 |
| 4. Consistência | 6 | 7 | 7 | 7 | 6 | 6 |
| 5. Centralização | 2 | 4 | 7 | 7 | 0 | 0 |
| 6. Governança | 3 | 5 | 7 | 7 | 0 | 0 |
| 7. Escalabilidade | 3 | 3 | 6 | 6 | 1 | 1 |
| 8. Drift (invertido) | 7 | 7 | 4 | 4 | 10 | 10 |
| 9. DX | 5 | 5 | 5 | 5 | 5 | 5 |
| 10. Maturidade | 4 | 5 | 5 | 5 | 3 | 3 |
| 11. Viabilidade corp. | 4 | 4 | 6 | 6 | 1 | 1 |
| **Média simples** | **4.0** | **5.2** | **6.5** | **6.5** | **3.0** | **3.0** |
| **Média ponderada** | **3.60** | **4.70** | **6.30** | **6.30** | **2.20** | **2.20** |

---

## Validação das metas da iteração 1

| Meta (iteração 1) | Status |
|---|---|
| Repetir cenário A com `.github/instructions/` populado | **Resolvido:** o artefato de A já documenta 7 instructions em `.github/instructions/`. A iteração 1 não detectou esses dados. |
| Padronizar coleta de métricas em todos os cenários | **Parcialmente resolvido:** A e B têm métricas completas. C ainda não reporta bytes lidos nem tokens. |
| Executar 2–3 repetições por cenário | **Pendente:** ainda execução única. |
| Testar cenário híbrido (MCP + instructions locais) | **Pendente.** |
| Incluir validação funcional (testes automatizados) | **Pendente:** nenhum cenário executou testes de integração. |

---

## Observações cruzadas

### Onde B (MCP) mantém liderança clara

- **Centralização** (+3 vs A, +7 vs C): mecanismo nativo de consumo central com tools de discovery.
- **Governança** (+2 vs A, +7 vs C): metadados estruturados (frontmatter) vs apenas IDs em ficheiros locais.
- **Escalabilidade** (+3 vs A, +5 vs C): propagação automática central.
- **Drift** (−3 vs A, −6 vs C invertido): consumo central reduz divergência.
- **Aderência** (+1 vs A): vantagem marginal — B usa 10 instructions vs 7 de A, mas a diferença é menor do que na iteração 1.

### Onde A (Instructions locais) fechou o gap vs B

- **Qualidade do plano** (7 = 7): empate. Com instructions locais estruturadas, A produz planos de mesma qualidade.
- **Completude** (7 = 7): empate. Mesma cobertura funcional.
- **Consistência** (7 = 7): empate.
- **Maturidade** (5 = 5): empate.

### Onde C (Baseline) permanece distante

- Critérios organizacionais (5–8): 0–1 em todos.
- Gap qualitativo (1–4) menor: 5.75 vs 7.0/7.25, demonstrando que o modelo compensa parcialmente a ausência de contexto estruturado.

### Achado principal desta iteração

**O gap A↔B é quase exclusivamente organizacional, não técnico.** Com instructions locais bem estruturadas (7 IDs, IDs estáveis, mapeamento decisão→instruction), a qualidade técnica do output é indistinguível do MCP. A vantagem do MCP concentra-se em centralização, governança cross-repo e redução de drift — dimensões que não se manifestam em cenário single-repo.

---

## Limitações do experimento

1. **Modelo de execução não controlado**: os artefatos não registram com certeza o mesmo modelo em todos os cenários.
2. **Execução única por cenário**: sem repetições, não é possível medir variância intra-cenário.
3. **Ausência de testes automatizados**: nenhum cenário executou testes de integração.
4. **Horários e condições distintas**: A às 09:57, B às 10:33, C às 07:52 — possíveis variações de carga.
5. **Escala de autoavaliação inconsistente**: os três relatórios usam escala 0–2 em vez de 0–10.
6. **Iteração 1 com dados incorretos para A**: esta iteração corrige, mas o fato de a iteração 1 ter falhado na extração de dados sugere risco de erro humano no pipeline de análise.
7. **Métricas de C incompletas**: bytes lidos e tokens não disponíveis para baseline.
8. **Critérios 2–4 sem peso na rubrica**: a média ponderada usa apenas 8 dos 11 critérios, subrepresentando qualidade técnica.

---

## Conclusão

### Veredicto

**MCP (B) lidera na pontuação global** (média simples 6.5, ponderada 6.30), mas o gap para **Instructions locais (A)** reduziu significativamente nesta iteração: de 2.5 para 1.3 pontos (média simples), de 2.70 para 1.60 (ponderada).

O gap é **quase inteiramente organizacional**. Em qualidade técnica (critérios 1–4), A e B estão empatados (média 7.0 vs 7.25). A vantagem do MCP concentra-se em centralização (+3), governança (+2), escalabilidade (+3) e redução de drift (−3 invertido) — dimensões que ganham peso em cenários multi-repo.

**Instructions locais (A) são uma abordagem viável e eficaz para cenários single-repo**, produzindo output de qualidade técnica equivalente ao MCP quando o corpus `.github/instructions/` é bem estruturado.

**Baseline (C)** confirma que o modelo produz output funcional sem contexto, mas com gap significativo em todas as dimensões, especialmente organizacionais.

### Principal evidência

Com instructions locais bem estruturadas (7 IDs, mapeamento decisão→instruction), o cenário A produziu **5 de 8 decisões ancoradas em instructions** e um plano BMAD com refinamento de riscos — resultado qualitativamente indistinguível do MCP em dimensões técnicas.

### Principal limitação

Execução única por cenário e ausência de testes automatizados impedem conclusões estatísticas robustas e validação funcional objetiva.

### Próximos passos sugeridos

1. **Executar cenário híbrido** (MCP + instructions locais) para verificar ganho aditivo — se instructions locais cobrem qualidade técnica e MCP cobre governança, a combinação pode ser superior.
2. **Repetir 2–3 vezes** cada cenário para medir variância.
3. **Padronizar coleta de métricas** (bytes, tokens, duração) via instrumentação automática em todos os cenários.
4. **Incluir testes de integração** como critério de aceite obrigatório.
5. **Testar com `.github/instructions/` empobrecido vs enriquecido** para isolar o efeito da qualidade do corpus local.
6. **Avaliar impacto multi-repo real**: executar o mesmo cenário em 2–3 repos distintos para testar as previsões de escalabilidade/drift.
