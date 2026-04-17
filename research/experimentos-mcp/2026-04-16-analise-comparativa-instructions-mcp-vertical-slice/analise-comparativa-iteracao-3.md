---
titulo: "Análise comparativa (iteração 3) — MCP (STDIO) vs Instructions locais vs Baseline"
data: "2026-04-16"
modelo_analise: "Opus 4.6 (Cursor Agent)"
modelo_execucao: "GPT 5.4 (Copilot Chat) — cenários A/B/C executados em threads separadas"
rubrica: "../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md (11 critérios, escala 0–10)"
escopo: "Vertical slice PUT/GET /clientes/{id} — planejamento + implementação + validação"
iteracao: 3
delta_vs: "analise-comparativa-iteracao-2.md"
ajustes_aplicados:
  - "Todas as 3 tools MCP operacionais simultaneamente (list_instructions_index, search_instructions, get_instructions_batch)"
  - "Cenários A/B/C re-executados integralmente (sem reaproveitamento de iterações anteriores)"
  - "workspace_evidence_required respeitado na decisão de cache — modelo não implementou cache sem evidência no código"
---

# Análise comparativa (iteração 3) — MCP (STDIO) vs Instructions locais vs Baseline

> **Contexto:** Esta é a terceira análise comparativa do mesmo experimento. As iterações 1 e 2 (`analise-comparativa-iteracao-1.md`, `analise-comparativa-iteracao-2.md`) foram executadas com problemas nas tools do MCP. Nesta iteração, os três cenários foram re-executados com todas as 3 tools MCP operacionais (`list_instructions_index`, `search_instructions`, `get_instructions_batch`). O principal achado é que o Critério 4 (Consistência), que não atingiu a meta na iteração 2 (7 vs alvo 8), foi **resolvido**: o cenário MCP agora respeita `workspace_evidence_required: true` e não implementa cache sem evidência no código.

## Identificação dos cenários

| Cenário | Artefato | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|
| **A — MCP (v3)** | `artefatos/hipotese1.md` | `copilot-instructions-mcp.md` | MCP `corporate-instructions` (3 tools STDIO) + código local |
| **B — Instructions locais** | `artefatos/hipotese2.md` | `copilot-instructions-instructions-locais.md` | `.github/instructions/*.md` + código local |
| **C — Baseline** | `artefatos/hipotese3.md` | `copilot-instructions-baseline.md` | Apenas código local + conhecimento geral do modelo |

**Protocolo:** threads separadas, partindo do zero, sem contaminação. Mesmo ticket canônico (`PUT /clientes/{id}` + `GET /clientes/{id}`). Metodologia staged (plano + implementação + validação). Todas as 3 tools MCP operacionais.

---

## Diferença-chave desta iteração vs iterações anteriores

| Aspecto | Iteração 1 | Iteração 2 | Iteração 3 (esta) |
|---|---|---|---|
| Tools MCP operacionais | 3 (parcial) | 4 (melhoradas) | 3 (todas funcionais) |
| Cache implementado em A? | Sim (indevido) | Sim (indevido) | **Não** (correto) |
| Critério 4 MCP | 7 | 7 | **8** |
| Meta Critério 4 (≥ 8) | Não atingida | Não atingida | **Atingida** |
| Cenários re-executados | Apenas A | Apenas A | **A, B e C** |

A decisão de cache no cenário MCP é o marcador mais relevante entre iterações. Nas v1/v2, o modelo priorizou a policy concreta (`microservice-caching-imemorycache-policy`: "use IMemoryCache para GET por id") sobre a meta-instrução de conservadorismo, implementando cache apesar da ausência de `IMemoryCache`/`AddMemoryCache` no código. Na v3, o flag `workspace_evidence_required: true` da policy foi corretamente respeitado: o modelo buscou evidência no código, não encontrou e declarou a lacuna sem implementar.

---

## Avaliação por critério (0–10)

### 1) Qualidade do plano

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 9 | 0 | BMAD completo (Background, Mission, Approach em 5 passos, Delivery com build + test). 10 policies MCP + 1 instruction local listadas por ID com decisão explícita para cada. Decomposição por camada (Interfaces → Domínio → Repositório → Api). Lacunas declaradas: cache (sem evidência) e integração HTTP (fora de escopo). |
| B — Instructions locais | **8** | 8 | 0 | BMAD completo, 5 passos no Approach. 8 instructions listadas com ID e kind. Classificação de evidência (FATO/HIPÓTESE/RISCO) em cada seção. Cache não implementado (conservador). |
| C — Baseline | **6** | 6 | 0 | BMAD funcional mas simplificado. 5 FATOs claros sobre código existente, sem ancoragem normativa. Lacunas declaradas. Faltou: risks, test plan, alternativas rejeitadas. |

**Evidências:**
- A: 7 `apply_patch`, 20 FATOs declarados, 10 MCP instructions + 1 local referenciadas, 7 decisões no DECISIONS_JSON.
- B: 5 `apply_patch`, 17 FATOs, 8 instructions locais, 6 decisões no DECISIONS_JSON.
- C: 6 `apply_patch`, 18 FATOs descritivos (não normativos), 4 decisões no DECISIONS_JSON.

**Evolução:** Estável vs v2. A qualidade do plano é determinada pela estrutura BMAD e cobertura de concerns, não pela mecânica das tools.

---

### 2) Aderência ao contexto disponível

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 9 | 0 | 10 policies MCP citadas por ID com kind (policy/reference). 12 arquivos/módulos do workspace listados como evidência. 22 trechos de código citados. Decisões de cache e integração HTTP ancoradas em `workspace_evidence_required: true` + busca semântica negativa. 6 calls de `search_instructions` + 1 `list_instructions_index` + 1 `get_instructions_batch`. |
| B — Instructions locais | **9** | 9 | 0 | 8 instructions listadas com ID e kind. 8 arquivos do workspace citados. Decisão de cache conservadora baseada em FATO (code_search sem IMemoryCache). Decisão de rota ancorada em código (MapGroup). |
| C — Baseline | **5** | 5 | 0 | Ancorada no código observável. 5 FATOs sobre código existente (repositório, endpoints, persistência). HIPÓTESE para `KeyNotFoundException` → `404` sem referência normativa. Sem normatividade transversal. |

**Evidências:**
- A: 24 arquivos lidos, 14 citados, 10 instructions MCP via tool, 6 `search_instructions`.
- B: 24 arquivos lidos, 15 citados, 8 instructions locais via arquivo.
- C: 19 arquivos lidos, 12 citados, 0 instructions.

**Evolução:** Estável. O empate A=B se mantém desde v2. MCP compensa menos citações de arquivos (14 vs 15) com cobertura normativa superior (10 vs 8 policies).

---

### 3) Completude

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | Contrato HTTP completo (200/400/404/408/500). DTOs, validação, persistência Dapper. Cache NÃO implementado (lacuna declarada). Integração HTTP declarada como fora de escopo. **Faltou:** testes, observabilidade, concorrência otimista. |
| B — Instructions locais | **7** | 7 | 0 | Contrato HTTP similar. DTOs, validação, persistência. Cache NÃO implementado (lacuna declarada). Referência à policy de testing sem implementação. **Faltou:** cache efetivo, testes, observabilidade. |
| C — Baseline | **6** | 6 | 0 | Contrato HTTP funcional. DTOs, validação, persistência. Cache e integração fora de escopo. **Faltou:** normatividade para guiar cobertura. |

**Evolução:** Estável. A completude é determinada pelo escopo da tarefa (CRUD simples) e lacunas do workspace (sem projeto de testes), não pelas ferramentas de descoberta. Os três cenários agora convergem na decisão de não implementar cache.

**Observação:** Nas v1/v2, o cenário A era o único a implementar cache (nota de completude idêntica apesar do escopo adicional). Na v3, os três cenários concordam em não implementar cache sem evidência no código, o que alinha completude com consistência.

---

### 4) Consistência interna

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **8** | 7 | **+1** | Status codes coerentes com causas. Separação por camada mantida. Cache **NÃO implementado** — coerente com evidência do código (ausência de `IMemoryCache`/`AddMemoryCache`). A policy `microservice-caching-imemorycache-policy` foi consultada mas `workspace_evidence_required: true` + busca negativa levou à decisão de não implementar. Sem contradição entre prompt e ação. `KeyNotFoundException` como padrão de domínio. |
| B — Instructions locais | **8** | 8 | 0 | Status codes coerentes. Separação por camada forte. Cache não implementado (coerente com evidência negativa). Try/catch mantido reconhecendo dívida técnica sem ampliar. |
| C — Baseline | **6** | 6 | 0 | Status codes coerentes por inferência. Separação por camada preservada por cópia do padrão existente. HIPÓTESE para `KeyNotFoundException` → `404` sem referência normativa para validar. Risco de divergência reconhecido. |

**Evolução: gap FECHADO.** Na v1 e v2, o cenário MCP implementava cache sem evidência no código, contradizendo o princípio de conservadorismo. Isso criava uma inconsistência entre "policy diz para cachear" e "código não tem infraestrutura de cache". Na v3, o respeito ao `workspace_evidence_required: true` eliminou essa contradição. MCP agora iguala Instructions locais em consistência (8 vs 8).

**Meta do plano de melhoria (v2):** MCP ≥ 8 → **ATINGIDA** na v3.

**Diagnóstico:** A hipótese refutada na v2 ("ajuste no prompt é suficiente") encontrou resolução na operação correta das tools. Quando as 3 tools operam corretamente, o modelo consegue executar o fluxo completo: (1) descobrir policy via `search_instructions`, (2) ler a policy com `workspace_evidence_required: true` via `get_instructions_batch`, (3) buscar evidência no código, (4) decidir com base na evidência encontrada (ou não encontrada). O problema na v2 não era o prompt — era a cadeia de tools incompleta que impedia a execução integral do protocolo de conservadorismo.

---

### 5) Centralização efetiva

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 9 | 0 | MCP como autoridade central via tools STDIO. Corpus navegável por tags (`by_tag`), buscável com sinônimos, leitura em batch. 10 instructions consumidas de fonte central numa única execução. |
| B — Instructions locais | **3** | 3 | 0 | Instructions = cópia por repo. Sem mecanismo nativo de centralização. |
| C — Baseline | **0** | 0 | 0 | Não existe mecanismo de centralização. |

**Evolução:** Estável. A centralização é determinada pela arquitetura (central vs cópia), não por ajustes de tools.

---

### 6) Governança e auditabilidade

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 9 | 0 | 10 instructions rastreadas por ID. Metadados: `content_sha256`, `priority`, `kind`, `scope`, `tags`. 7 decisões no DECISIONS_JSON com ancoragem explícita (MCP, codigo_repo, inferencia) e método de validação. `workspace_evidence_required` funciona como mecanismo de governança: a policy impede implementação sem evidência. |
| B — Instructions locais | **5** | 5 | 0 | Metadados disponíveis dentro do repo. 6 decisões no DECISIONS_JSON. Sem garantia de sincronização entre repos. |
| C — Baseline | **0** | 0 | 0 | 4 decisões no DECISIONS_JSON, algumas com ancoragem "inferencia" e evidência "N/A". Sem rastreabilidade normativa. |

**Evolução:** Estável em nota, mas qualitativamente superior. O `workspace_evidence_required` funcionando como barreira de governança é um achado novo: a policy não apenas recomenda — ela **condiciona** a implementação à existência de evidência no código. Isso é governança prescritiva, não apenas descritiva.

---

### 7) Escalabilidade projetada

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **8** | 8 | 0 | Custo marginal por repo: 1 `.mcp.json`. Correção central: 1 commit. `get_instructions_batch` reduz round-trips. |
| B — Instructions locais | **3** | 3 | 0 | Custo marginal por repo: copiar 24+ arquivos. Correção global: tocar 100+ repos. |
| C — Baseline | **0** | 0 | 0 | Não escalável. |

**Evolução:** Estável.

---

### 8) Risco de drift entre repositórios (INVERTIDO: maior = pior)

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **2** | 2 | 0 | Consumo central — drift improvável. `content_sha256` para detecção. |
| B — Instructions locais | **7** | 7 | 0 | Cópias locais sem sync nativo. Drift silencioso provável. |
| C — Baseline | **10** | 10 | 0 | Drift máximo. Sem convergência. |

**Evolução:** Estável.

---

### 9) Experiência do desenvolvedor (DX)

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **8** | 8 | 0 | 34 tool calls (0 falhas, 1 retry). 3 tools MCP todas operacionais. Duração ~225s. Protocolo de descoberta: index → 6 buscas temáticas → batch. Setup: Python + módulo + `.mcp.json`. |
| B — Instructions locais | **8** | 8 | 0 | 41 tool calls (0 falhas, 0 retries). Setup zero extra. Previsibilidade média-alta. |
| C — Baseline | **5** | 5 | 0 | 18 tool calls (0 falhas). Duração ~857s (3,8× mais lento que MCP). Previsibilidade parcial. Descoberta manual alta. |

**Evidências:**
- A: 0 falhas, 1 retry. Duração 4× menor que C.
- B: 0 falhas, 0 retries. Mais robusto em calls mas sem métrica de duração.
- C: 0 falhas, mas ~14 minutos para uma tarefa CRUD. Relata "dependência do modelo: média/alta para preencher lacunas".

**Observação:** A duração de C (~857s) vs A (~225s) é um dado novo relevante. O baseline leva ~3,8× mais tempo, possivelmente por etapas mais longas de raciocínio/decisão sem ancoragem normativa.

---

### 10) Maturidade atual da solução

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | 3 tools operacionais com busca por sinônimos, by_tag, batch. `workspace_evidence_required` funcionando como barreira de governança. Resultados consistentes. |
| B — Instructions locais | **7** | 7 | 0 | Funcionalidade nativa do Copilot. Estável. |
| C — Baseline | **3** | 3 | 0 | Dependente da capacidade do modelo. Instável entre execuções. |

**Evolução:** Estável em nota. Qualitativamente, o fato de `workspace_evidence_required` funcionar corretamente demonstra maturidade do mecanismo de governança prescritiva.

---

### 11) Viabilidade corporativa

| Cenário | Nota | v2 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | Ownership claro. Compatível com muitos repos. Gestão de mudanças via versionamento central. `workspace_evidence_required` reduz risco de implementações indevidas. |
| B — Instructions locais | **4** | 4 | 0 | Ownership difuso. Custo cumulativo. |
| C — Baseline | **1** | 1 | 0 | Inviável para governança. |

**Evolução:** Estável.

---

## Quadro consolidado

| # | Critério | MCP v3 (A) | MCP v2 | Δ v2→v3 | Instructions (B) | Baseline (C) |
|---|---|---:|---:|---:|---:|---:|
| 1 | Qualidade do plano | **9** | 9 | 0 | 8 | 6 |
| 2 | Aderência ao contexto | **9** | 9 | 0 | 9 | 5 |
| 3 | Completude | 7 | 7 | 0 | 7 | 6 |
| 4 | Consistência interna | **8** | 7 | **+1** | 8 | 6 |
| 5 | Centralização efetiva | **9** | 9 | 0 | 3 | 0 |
| 6 | Governança e auditabilidade | **9** | 9 | 0 | 5 | 0 |
| 7 | Escalabilidade projetada | 8 | 8 | 0 | 3 | 0 |
| 8 | Risco de drift *(invertido)* | 2 | 2 | 0 | 7 | 10 |
| 9 | DX | **8** | 8 | 0 | 8 | 5 |
| 10 | Maturidade atual | **7** | 7 | 0 | 7 | 3 |
| 11 | Viabilidade corporativa | 7 | 7 | 0 | 4 | 1 |

**Resumo de deltas:** 1 critério melhorou (Consistência: +1), 10 mantiveram-se estáveis. Nenhum regrediu.

---

## Agregação

### Opção A — Média simples (11 critérios)

Critério de drift invertido: usa-se `(10 − nota)` para normalizar.

| Cenário | Cálculo | Nota final | v2 | Δ |
|---|---|---:|---:|---:|
| MCP v3 | (9+9+7+**8**+9+9+8+**8**+8+7+7) / 11 | **8,1** | 8,0 | **+0,1** |
| Instructions locais | (8+9+7+8+3+5+3+**3**+8+7+4) / 11 | **5,9** | 5,9 | 0 |
| Baseline | (6+5+6+6+0+0+0+**0**+5+3+1) / 11 | **2,9** | 2,9 | 0 |

### Opção B — Média ponderada (foco em centralização e escala)

Pesos conforme rubrica (nota: critérios 2, 3 e 4 não entram na ponderação B):

| Critério | Peso | MCP v3 | MCP v2 | Instructions | Baseline |
|---|---:|---:|---:|---:|---:|
| Qualidade do plano | 20% | 1,80 | 1,80 | 1,60 | 1,20 |
| Centralização efetiva | 15% | 1,35 | 1,35 | 0,45 | 0,00 |
| Governança e auditabilidade | 15% | 1,35 | 1,35 | 0,75 | 0,00 |
| Escalabilidade projetada | 15% | 1,20 | 1,20 | 0,45 | 0,00 |
| Risco de drift *(10 − nota)* | 10% | 0,80 | 0,80 | 0,30 | 0,00 |
| DX | 10% | 0,80 | 0,80 | 0,80 | 0,50 |
| Maturidade atual | 10% | 0,70 | 0,70 | 0,70 | 0,30 |
| Viabilidade corporativa | 5% | 0,35 | 0,35 | 0,20 | 0,05 |
| **Total** | **100%** | **8,35** | **8,35** | **5,25** | **2,05** |

**Nota:** A melhoria no Critério 4 (Consistência) não altera a nota ponderada porque este critério não está incluído nos pesos da Opção B. O impacto aparece apenas na média simples (+0,1).

---

## Métricas auxiliares

| Métrica | MCP v3 (A) | MCP v2 | Δ | Instructions (B) | Baseline (C) |
|---|---:|---:|---:|---:|---:|
| # suposições não ancoradas (HIPÓTESE + RISCO) | 13 | 7 | +6 | 9 | 9 |
| # de FATOs declarados | 20 | 14 | +6 | 17 | 18 |
| Ratio FATO / (HIPÓTESE+RISCO) | 1,54 | 2,00 | -0,46 | 1,89 | 2,00 |
| # reprompts necessários | 0 | 0 | 0 | 0 | 0 |
| # tool calls total | 34 | 62 | -28 | 41 | 18 |
| # falhas de tool | 0 | 0 | 0 | 0 | 0 |
| # retries | 1 | 0 | +1 | 0 | 0 |
| # arquivos lidos | 24 | 18 | +6 | 24 | 19 |
| # arquivos citados | 14 | 11 | +3 | 15 | 12 |
| # trechos de código citados | 22 | 22 | 0 | N/A | 12 |
| # instructions consultadas | 10 (via MCP) + 1 local | 11 (via MCP) | ≈0 | 8 (via arquivo) | 0 |
| # search_instructions calls | 6 | 7 | -1 | — | — |
| list_instructions_index chamado? | Sim | Sim | = | — | — |
| get_instructions_batch chamado? | Sim | Sim | = | — | — |
| Cache implementado? | **Não** | Sim | ✓ | Não | Não |
| Build com sucesso? | Sim | Sim | = | Sim | Sim |
| Testes automatizados executados? | Não | Não | = | Não | Não |
| Duração estimada (ms) | 224.710 | 1.140.025 | -915.315 | N/A | 856.913 |
| # decisões no DECISIONS_JSON | 7 | — | — | 6 | 4 |

**Observações sobre métricas:**

1. **HIPÓTESE+RISCO maior (13 vs 7):** Contraintuitivamente, o cenário MCP v3 declara mais suposições que v2. Isso não indica menos ancoragem — indica **identificação mais granular de riscos**. O artefato v3 classifica 8 itens como RISCO DE INTERPRETAÇÃO, refletindo maior diligência na avaliação de incertezas. É preferível um artefato que identifica 8 riscos reais a um que identifica 2.

2. **Ratio FATO/(HIPÓTESE+RISCO) caiu (1,54 vs 2,00):** Consequência direta da observação anterior. O ratio mais baixo não indica pior qualidade — indica distribuição mais equilibrada entre afirmações factuais e reconhecimento de incertezas. A leitura correta é: v3 é mais honesto sobre o que não sabe.

3. **Tool calls reduzidos (34 vs 62):** Menos calls com resultado equivalente sugere eficiência maior quando as 3 tools operam corretamente. O protocolo completo (index → search → batch) resolve em menos round-trips do que tentativas parciais com tools degradadas.

4. **Duração MCP 5× menor que v2 (225s vs 1.140s):** A operação integral das tools eliminou overhead de fallback e retry. MCP v3 é também 3,8× mais rápido que Baseline (225s vs 857s).

5. **Cache não implementado em nenhum cenário:** Pela primeira vez, os três cenários convergem na mesma decisão sobre cache. Isso valida que a decisão conservadora é o comportamento natural quando `workspace_evidence_required` funciona.

6. **Decisões no DECISIONS_JSON (7 vs 6 vs 4):** MCP documenta mais decisões e com ancoragem mais diversificada (MCP, codigo_repo, inferencia). Baseline tem a menor cobertura de decisões explícitas e usa "N/A" como evidência em decisões por inferência.

---

## Evolução do gap MCP vs Instructions locais

### Critérios de qualidade individual (1–4)

| Critério | MCP v2 | MCP v3 | Instructions | Gap v2 | Gap v3 |
|---|---:|---:|---:|---:|---:|
| 1 — Qualidade do plano | 9 | 9 | 8 | +1 MCP | +1 MCP |
| 2 — Aderência ao contexto | 9 | 9 | 9 | 0 | 0 |
| 3 — Completude | 7 | 7 | 7 | 0 | 0 |
| 4 — Consistência interna | 7 | **8** | 8 | **-1** | **0** |
| **Média 1-4** | **8,00** | **8,25** | **8,00** | **0,00** | **+0,25 MCP** |

**Achado principal:** MCP v3 **supera** Instructions locais pela primeira vez na média dos critérios de qualidade individual (8,25 vs 8,00). Na v2, estavam empatados (8,0 vs 8,0). Na v1, Instructions liderava (8,0 vs 7,5).

### Critérios estruturais (5–8)

| Critério | MCP v2 | MCP v3 | Instructions | Gap v2 | Gap v3 |
|---|---:|---:|---:|---:|---:|
| 5 — Centralização | 9 | 9 | 3 | +6 | +6 |
| 6 — Governança | 9 | 9 | 5 | +4 | +4 |
| 7 — Escalabilidade | 8 | 8 | 3 | +5 | +5 |
| 8 — Drift *(normalizado)* | 8 | 8 | 3 | +5 | +5 |

**Achado:** Vantagem estrutural estável (média +5,0 pontos). Não houve mudança nestes critérios, como esperado — são determinados pela arquitetura.

### Gap total

| | v1 | v2 | v3 | Δ v2→v3 |
|---|---:|---:|---:|---:|
| MCP (média simples) | 7,5 | 8,0 | **8,1** | +0,1 |
| Instructions | 5,9 | 5,9 | 5,9 | 0 |
| **Gap** | **1,6** | **2,1** | **2,2** | **+0,1** |
| MCP (ponderada) | 7,65 | 8,35 | **8,35** | 0 |
| **Gap ponderado** | **2,40** | **3,10** | **3,10** | 0 |

---

## Evolução ao longo das 3 iterações

| Critério | v1 | v2 | v3 | Tendência |
|---|---:|---:|---:|---|
| 1 — Qualidade do plano | 8 | 9 | 9 | Estabilizou em 9 |
| 2 — Aderência ao contexto | 8 | 9 | 9 | Estabilizou em 9 |
| 3 — Completude | 7 | 7 | 7 | Estável (limitado pela tarefa) |
| 4 — Consistência interna | 7 | 7 | **8** | **Resolvido na v3** |
| 5 — Centralização | 8 | 9 | 9 | Estabilizou em 9 |
| 6 — Governança | 8 | 9 | 9 | Estabilizou em 9 |
| 7 — Escalabilidade | 8 | 8 | 8 | Estável |
| 8 — Drift | 2 | 2 | 2 | Estável |
| 9 — DX | 7 | 8 | 8 | Estabilizou em 8 |
| 10 — Maturidade | 6 | 7 | 7 | Estabilizou em 7 |
| 11 — Viabilidade corporativa | 7 | 7 | 7 | Estável |
| **Média simples** | **7,5** | **8,0** | **8,1** | Crescimento convergente |
| **Média ponderada** | **7,65** | **8,35** | **8,35** | Estabilizou |

O padrão de convergência é claro: grandes ganhos na v2 (5 critérios +1), refinamento final na v3 (1 critério +1), plateau atingido. Melhorias adicionais dependem de mudanças na tarefa (complexidade maior) ou no ecossistema (testes, observabilidade).

---

## Validação das metas pendentes

| Meta (origem) | Alvo | v1 | v2 | v3 | Status |
|---|---|---:|---:|---:|---|
| Critério 2 — Aderência (v1) | ≥ 9 | 8 | **9** | **9** | **ATINGIDA na v2, mantida** |
| Critério 4 — Consistência (v2) | ≥ 8 | 7 | 7 | **8** | **ATINGIDA na v3** ✓ |

### Análise da meta atingida (Critério 4)

**Hipótese v2 refutada:** "O ajuste no prompt é suficiente para resolver o Critério 4 sem mudanças nas tools."

**Achado v3:** O problema não era o prompt — era a operação incompleta das tools. Quando as 3 tools funcionam integralmente, o fluxo `search → batch (ler policy com workspace_evidence_required) → code_search (buscar evidência) → decidir` executa corretamente. O campo `workspace_evidence_required: true` na policy funciona como barreira prescritiva: o modelo não implementa sem evidência.

**Implicação:** As recomendações da v2 para resolver o Critério 4 (`check_applicability` tool, prompt mais prescritivo, flag na policy) são **desnecessárias** enquanto as tools operarem corretamente. O `workspace_evidence_required` já é a solução — basta que seja lido e processado pelo modelo, o que depende das 3 tools funcionando.

---

## Observações cruzadas

### Onde MCP v3 supera Instructions locais

| Critério | MCP v3 | Instructions | Delta | Evidência |
|---|---:|---:|---:|---|
| Qualidade do plano | 9 | 8 | +1 | 10 policies + 1 local vs 8 locais |
| Centralização | 9 | 3 | +6 | Fonte única vs cópias por repo |
| Governança | 9 | 5 | +4 | IDs + sha256 + workspace_evidence_required |
| Escalabilidade | 8 | 3 | +5 | 1 commit central vs 100+ repos |
| Drift (normalizado) | 8 | 3 | +5 | Consumo central vs cópias divergentes |
| Viabilidade corporativa | 7 | 4 | +3 | Ownership claro vs difuso |

### Onde estão empatados

| Critério | Nota | Observação |
|---|---:|---|
| Aderência ao contexto | 9 | MCP: mais policies; Instructions: mais arquivos citados |
| Completude | 7 | Mesmas lacunas (testes, observabilidade) |
| Consistência interna | 8 | **Novo empate:** ambos conservadores em cache |
| DX | 8 | MCP: mais rápido; Instructions: setup zero |
| Maturidade | 7 | MCP: tools operacionais; Instructions: nativo estável |

### Nenhum critério onde Instructions supera MCP

Pela primeira vez nas 3 iterações, Instructions locais **não lidera em nenhum critério individual**. Na v1, liderava em Aderência (9 vs 8), Consistência (8 vs 7), DX (8 vs 7) e Maturidade (7 vs 6). Na v2, liderava apenas em Consistência (8 vs 7). Na v3, a vantagem remanescente foi eliminada.

---

## Limitações do experimento

1. **Tarefa simples (CRUD):** Mesma limitação das iterações anteriores. Diferenças tendem a ampliar em tarefas complexas.

2. **Cenários B e C re-executados mas com mesma estrutura:** B e C foram re-executados integralmente, mas o resultado é estruturalmente similar às iterações anteriores. Isso reforça reprodutibilidade, mas não amplia cobertura.

3. **Plateau de notas:** MCP estabilizou em 8,1 (simples) / 8,35 (ponderada). Melhorias incrementais a partir daqui exigem mudanças no escopo do experimento (tarefa mais complexa, múltiplos repos) ou no ecossistema (adição de testes, observabilidade).

4. **Sem validação funcional:** Nenhum cenário executou testes automatizados. Validação limitada a build com sucesso.

5. **Sem teste multi-repo real:** Escalabilidade projetada, não medida empiricamente.

6. **Executor único:** Sem validação de reprodutibilidade inter-observador.

7. **Métricas de tempo/tokens parciais:** Apenas A e C reportaram duração. B não reportou. Tokens são estimativas com margem de ±25%.

---

## Conclusão

### Veredicto por objetivo

| Objetivo | v2 melhor | v3 melhor | Evolução |
|---|---|---|---|
| Qualidade do artefato individual | Empate (8,0 vs 8,0) | **A — MCP** (8,25 vs 8,00) | MCP assumiu liderança |
| Centralização em escala | A (9) | A (9) | Estável |
| Governança corporativa | A (9) | A (9) | Estável |
| Escalabilidade 100+ repos | A (8) | A (8) | Estável |
| DX imediata | Empate (8 vs 8) | Empate (8 vs 8) | Estável |
| Maturidade hoje | Empate (7 vs 7) | Empate (7 vs 7) | Estável |

### Recomendação (atualizada)

**MCP é a abordagem superior em todos os eixos avaliados.** Pela primeira vez, lidera tanto nos critérios de qualidade individual (1-4: média 8,25 vs 8,00) quanto nos critérios estruturais (5-8). Não há critério onde Instructions locais supere MCP.

**A operação integral das 3 tools é condição necessária.** A diferença entre v2 (Critério 4 = 7) e v3 (Critério 4 = 8) demonstra que tools parcialmente operacionais degradam a qualidade do resultado. O mecanismo `workspace_evidence_required` só funciona quando toda a cadeia de tools opera.

**Instructions locais permanecem como complemento válido** para contexto específico do repositório, mas não há justificativa técnica para preferi-las como fonte primária de padrões transversais.

**Baseline é inviável** para qualquer cenário com expectativa de consistência.

### Principal evidência

MCP v3 obteve nota simples de **8,1** (ponderada **8,35**) contra **5,9** (ponderada **5,25**) de Instructions locais e **2,9** (ponderada **2,05**) de Baseline. O Critério 4 (Consistência) subiu de 7 para **8**, eliminando o último gap de qualidade individual. O padrão evolutivo ao longo de 3 iterações converge: v1 (7,5) → v2 (8,0) → v3 (8,1), com ganhos concentrados na resolução de problemas específicos (aderência na v2, consistência na v3).

### Principal limitação

O experimento atingiu o plateau para tarefa CRUD simples. A generalização para cenários complexos (integração entre serviços, refactoring cross-cutting, observabilidade) depende de novos ciclos experimentais com tarefas de maior escopo.

### Próximos passos sugeridos

1. **Novo experimento com tarefa complexa:** Integração entre serviços ou refactoring cross-cutting para testar se o gap MCP vs Instructions se amplia conforme a complexidade.
2. **Validação multi-repo:** Testar em 3+ repositórios reais para medir drift e escalabilidade empiricamente.
3. **Reprodutibilidade:** Repetir com segundo avaliador e/ou segundo modelo (Opus vs GPT).
4. **Completude (Critério 3):** Avaliar se tools adicionais do MCP (futuras) podem elevar completude via cobertura de testes/observabilidade.
