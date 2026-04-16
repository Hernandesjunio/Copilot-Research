---
titulo: "Análise comparativa (iteração 2) — MCP (STDIO) vs Instructions locais vs Baseline"
data: "2026-04-16"
modelo_analise: "Opus 4.6 (Cursor Agent)"
modelo_execucao: "GPT 5.4 (Copilot Chat) — cenários A/B/C executados em threads separadas"
rubrica: "../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md (11 critérios, escala 0–10)"
escopo: "Vertical slice PUT/GET /clientes/{id} — planejamento + implementação + validação"
iteracao: 2
delta_vs: "analise-comparativa-iteracao-1.md"
ajustes_aplicados:
  - "Prompt copilot-instructions-mcp.md: list_instructions_index obrigatório, múltiplas buscas, leitura em batch, cruzamento policy×código, conservadorismo explícito"
  - "Tool search_instructions: max_results default 10, cap 20, expansão por sinônimos"
  - "Tool list_instructions_index: campo by_tag com agrupamento por tags"
  - "Nova tool get_instructions_batch: leitura em lote de múltiplas instructions"
  - "search_instructions: campo related_ids no retorno"
---

# Análise comparativa (iteração 2) — MCP (STDIO) vs Instructions locais vs Baseline

> **Contexto:** Esta é a segunda análise comparativa do mesmo experimento. A primeira iteração (`analise-comparativa-iteracao-1.md`) identificou que o MCP perdia para Instructions locais nos critérios 2 (Aderência: 8 vs 9) e 4 (Consistência: 7 vs 8). Um plano de melhoria (`artefatos/plano-bmad-melhoria-mcp-criterios-2-4.md`) foi executado, ajustando prompt e tools. O cenário MCP (hipotese1) foi re-executado; os cenários B e C permanecem inalterados para isolar o efeito das melhorias.

## Identificação dos cenários

| Cenário | Artefato | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|
| **A — MCP (v2)** | `artefatos/hipotese1.md` | `copilot-instructions-mcp.md` (ajustado) | MCP `corporate-instructions` (tools STDIO melhoradas) + código local |
| **B — Instructions locais** | `artefatos/hipotese2.md` | `copilot-instructions-instructions-locais.md` | `.github/instructions/*.md` + código local |
| **C — Baseline** | `artefatos/hipotese3.md` | `copilot-instructions-baseline.md` | Apenas código local + conhecimento geral do modelo |

**Protocolo:** threads separadas, partindo do zero, sem contaminação. Mesmo ticket canônico (`PUT /clientes/{id}` + `GET /clientes/{id}`). Metodologia staged (plano + implementação + validação).

---

## Ajustes aplicados entre iteração 1 e iteração 2

| Frente | Ajuste | Alvo |
|---|---|---|
| Prompt | `list_instructions_index` obrigatório antes de busca | Critério 2 |
| Prompt | Múltiplas buscas por tema (não apenas 1 query) | Critério 2 |
| Prompt | `get_instructions_batch` para ler todas as relevantes de uma vez | Critério 2, 9 |
| Prompt | Cruzamento policy×código com conservadorismo explícito | Critério 4 |
| Prompt | Citação de IDs + arquivos em cada decisão | Critério 2, 6 |
| Tool `search_instructions` | `max_results` default 10 (era 5), cap 20 (era 10) | Critério 2 |
| Tool `search_instructions` | Expansão de query com sinônimos por domínio | Critério 2 |
| Tool `search_instructions` | Campo `related_ids` no retorno | Critério 2 |
| Tool `list_instructions_index` | Campo `by_tag` com agrupamento por tags | Critério 2 |
| Nova tool `get_instructions_batch` | Leitura em lote de múltiplas instructions | Critério 2, 9 |

---

## Avaliação por critério (0–10)

### 1) Qualidade do plano

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 8 | **+1** | BMAD completo (Background com 4 FATOs, Mission, Approach em 5 passos, Delivery). 11 instructions MCP consultadas por ID fornecem base normativa ampla para cada decisão do plano. Decomposição por camada explícita. Decisão de cache ancorada em policy com HIPÓTESE para TTL. Faltou: critérios de aceite formais e mapeamento de riscos como seção dedicada. |
| B — Instructions locais | **8** | 8 | 0 | BMAD completo, 5 passos no Approach. 8 instructions listadas com ID e kind. Decisão conservadora de NÃO implementar cache (FATO: sem IMemoryCache no código). Faltou: critérios de aceite formais. |
| C — Baseline | **6** | 6 | 0 | BMAD funcional mas simplificado. FATOs claros sobre código existente, porém sem ancoragem normativa. Faltou: risks, test plan, alternativas rejeitadas. |

**Evidências:**
- A (v2): 7 `apply_patch`, 14 FATOs declarados, 11 MCP instructions + 1 instruction local referenciadas.
- A (v1): 7 `apply_patch`, 13 FATOs, 5 MCP instructions referenciadas.
- B: 5 `apply_patch`, 17 FATOs, 8 instructions locais.
- C: 6 `apply_patch`, 18 FATOs descritivos (não normativos).

**Evolução:** A consulta de 11 instructions (vs 5) ampliou a base normativa do plano, cobrindo domínios que antes ficavam sem ancoragem (data access, error catalog, integration patterns, resilience). Isso elevou a qualidade de justificação das decisões sem alterar a estrutura BMAD.

---

### 2) Aderência ao contexto disponível

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 8 | **+1** | 11 policies MCP citadas por ID. 7 calls de `search_instructions` com queries temáticas distintas. `list_instructions_index` chamado antes de buscar. 11 arquivos do workspace citados com 22 trechos. Decisões de camada, HTTP, validação, cache, data access e error catalog todas ancoradas em policy + código. |
| B — Instructions locais | **9** | 9 | 0 | 8 instructions listadas com ID e kind. 15 arquivos do workspace citados. Decisão de cache conservadora baseada em FATO (code_search sem IMemoryCache). Leitura direta de arquivos `.md` mantém granularidade de referência. |
| C — Baseline | **5** | 5 | 0 | Ancorada no código observável. FATOs corretos mas puramente descritivos. Sem normatividade transversal. |

**Evidências:**
- A (v2): 62 tool calls, 18 arquivos lidos, 11 citados, **11 instructions MCP** via tool, 7 `search_instructions`.
- A (v1): 21 tool calls, 20 arquivos lidos, 7 citados, **5 instructions MCP** via tool, ~1 `search_instructions`.
- B: 41 tool calls, 24 arquivos lidos, 15 citados, 8 instructions locais via arquivo.
- C: 18 tool calls, 19 arquivos lidos, 12 citados, 0 instructions.

**Evolução:** O gap de aderência foi **fechado**. Na v1, B superava A (9 vs 8) porque lia mais arquivos e referenciava mais guardrails. Na v2, A igualou B consultando 11 instructions MCP (vs 8 locais de B) e ampliando citações de 7 para 11 arquivos. A diferença residual é que B ainda cita mais arquivos do workspace (15 vs 11), mas A compensa com cobertura normativa superior (11 vs 8 policies).

**Meta do plano de melhoria:** MCP ≥ 9 → **ATINGIDA**.

---

### 3) Completude

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | Contrato HTTP completo (200/400/404/408/500). DTOs, validação, persistência Dapper. Cache implementado (IMemoryCache). Integração HTTP declarada como fora de escopo. **Faltou:** testes, observabilidade, concorrência otimista. |
| B — Instructions locais | **7** | 7 | 0 | Contrato HTTP similar. DTOs, validação, persistência. Cache NÃO implementado (lacuna declarada). Referência à policy de testing sem implementação. **Faltou:** cache efetivo, testes, observabilidade. |
| C — Baseline | **6** | 6 | 0 | Contrato HTTP funcional. DTOs, validação, persistência. **Faltou:** cache, testes, observabilidade, normatividade para guiar cobertura. |

**Evolução:** Sem mudança. A completude da implementação depende do escopo da tarefa (CRUD simples) e das lacunas do workspace (sem projeto de testes), não das tools de descoberta. Mais instructions consultadas não expandiram o escopo do patch.

---

### 4) Consistência interna

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | Status codes coerentes. Separação por camada mantida. Cache com invalidação em PUT (coerente internamente). TTL de 5 min como HIPÓTESE reconhecida. **Ponto persistente:** cache implementado sem evidência de `IMemoryCache` no código existente, apesar de o prompt instrui conservadorismo ("Consistência com o código prevalece sobre completude normativa"). A decisão segue a policy MCP mas contradiz o princípio de conservadorismo do prompt. |
| B — Instructions locais | **8** | 8 | 0 | Status codes coerentes. Separação por camada forte. Decisão de não implementar cache coerente com evidência (sem base = não introduzir). Try/catch mantido para não introduzir inconsistência. |
| C — Baseline | **6** | 6 | 0 | Status codes coerentes por inferência. Separação por camada preservada por cópia do padrão existente. Sem normatividade para validar coerência. |

**Evolução:** Sem mudança. O gap de consistência entre MCP e Instructions **não foi fechado**. A instrução de conservadorismo no prompt não foi suficiente para alterar o comportamento do modelo na decisão de cache. O modelo priorizou a policy MCP (`microservice-caching-imemorycache-policy`) sobre a ausência de evidência no código, reproduzindo o mesmo padrão da v1.

**Meta do plano de melhoria:** MCP ≥ 8 → **NÃO ATINGIDA**.

**Hipótese do plano:** "O ajuste no prompt é suficiente para resolver o Critério 4 sem mudanças nas tools." → **REFUTADA** para a decisão de cache. O modelo segue a policy normativa mesmo quando o prompt instrui conservadorismo. Possível causa: a policy é mais concreta ("use IMemoryCache para GET por id") do que a meta-instrução ("consistência com o código prevalece"). Para futuras iterações, considerar uma tool de `check_applicability` ou tornar o conservadorismo mais prescritivo.

---

### 5) Centralização efetiva

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 8 | **+1** | MCP como autoridade central via tools STDIO. Corpus navegável por tags (`by_tag`), buscável com sinônimos, e com `related_ids` para descoberta cruzada. A melhor discoverabilidade torna a centralização mais efetiva — o modelo encontrou 11 instructions relevantes (vs 5 na v1). |
| B — Instructions locais | **3** | 3 | 0 | Instructions = cópia por repo. Sem mecanismo de centralização nativo. |
| C — Baseline | **0** | 0 | 0 | Não existe mecanismo de centralização. |

**Evolução:** A centralização era arquiteturalmente forte na v1 mas operacionalmente limitada (modelo encontrava apenas ~20% do corpus). Com sinônimos, `by_tag` e `related_ids`, a cobertura subiu para ~46% do corpus numa única execução, tornando a centralização efetivamente mais abrangente.

---

### 6) Governança e auditabilidade

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **9** | 8 | **+1** | 11 instructions rastreadas por ID. Metadados: `content_sha256`, `priority`, `kind`, `scope`, `tags`. 7 buscas temáticas registradas. `related_ids` permite auditar cobertura lateral. Capacidade de impor revisão/ownership centralmente. |
| B — Instructions locais | **5** | 5 | 0 | Mesmo esquema de metadados disponível dentro do repo. Sem garantia de sincronização entre repos. |
| C — Baseline | **0** | 0 | 0 | Sem rastreabilidade. |

**Evolução:** O aumento de 5 para 11 instructions rastreáveis por ID fortalece a auditoria: é possível verificar exatamente quais policies guiaram cada decisão. Na v1, 6 das 11 policies potencialmente relevantes não foram sequer descobertas, criando uma "auditoria incompleta por design".

---

### 7) Escalabilidade projetada

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **8** | 8 | 0 | Custo marginal por repo: 1 `.mcp.json`. Correção central: 1 commit. `get_instructions_batch` reduz overhead de round-trips. Limitação permanece: requer Python + módulo MCP no ambiente do dev. |
| B — Instructions locais | **3** | 3 | 0 | Custo marginal por repo: copiar 24+ arquivos. Correção global: tocar 100+ repos. |
| C — Baseline | **0** | 0 | 0 | Não escalável. |

**Evolução:** Sem mudança na projeção de escala. As melhorias de tools reduzem fricção operacional mas não alteram o modelo arquitetural (ainda 1 `.mcp.json` por repo com consumo central).

---

### 8) Risco de drift entre repositórios (INVERTIDO: maior = pior)

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **2** | 2 | 0 | Consumo central — drift improvável. `content_sha256` para detecção. |
| B — Instructions locais | **7** | 7 | 0 | Cópias locais sem sync nativo. Drift silencioso provável. |
| C — Baseline | **10** | 10 | 0 | Drift máximo. Sem convergência. |

**Evolução:** Sem mudança. O risco de drift é determinado pela arquitetura (central vs cópia), não pelas tools de busca.

---

### 9) Experiência do desenvolvedor (DX)

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **8** | 7 | **+1** | 62 tool calls (0 falhas, 0 retries). `get_instructions_batch` eliminou round-trips individuais. `search_instructions` com sinônimos reduziu buscas em branco. Previsibilidade alta: modelo seguiu o protocolo de 5 passos do prompt. Setup permanece: Python + módulo + `.mcp.json`. |
| B — Instructions locais | **8** | 8 | 0 | 41 tool calls (0 falhas). Setup zero extra. Previsibilidade média-alta. |
| C — Baseline | **5** | 5 | 0 | 18 tool calls (0 falhas). Previsibilidade parcial. Descoberta manual alta. |

**Evidências:**
- A (v2): 0 falhas em 62 calls; v1: 1 falha em 21 calls.
- A (v2): 7 `search_instructions` + 1 `list_instructions_index` — protocolo de descoberta sistemático.
- B: 0 falhas em 41 calls — consistente entre iterações.

**Evolução:** A eliminação de falhas (0 vs 1) e o protocolo de busca sistemático melhoraram a experiência. O aumento de tool calls (62 vs 21) é transparente ao usuário e reflete maior profundidade de consulta, não maior fricção.

---

### 10) Maturidade atual da solução

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 6 | **+1** | MVP evoluído: 4 tools (era 3), busca com sinônimos, by_tag, related_ids, batch. Resultados consistentes e mais abrangentes no caso testado. Distância para produção reduzida. |
| B — Instructions locais | **7** | 7 | 0 | Funcionalidade nativa do Copilot. Cobertura adequada para guardrails locais. Estável. |
| C — Baseline | **3** | 3 | 0 | Dependente da capacidade do modelo. Instável entre execuções. |

**Evolução:** O MVP deixou de ser "3 de ~13 tools" para "4 tools com melhorias significativas de discoverabilidade". A maturidade subiu porque as tools existentes ficaram mais eficazes, não apenas porque houve uma tool a mais.

---

### 11) Viabilidade corporativa

| Cenário | Nota | v1 | Δ | Justificativa |
|---|---:|---:|---:|---|
| A — MCP | **7** | 7 | 0 | Modelo de ownership claro. Compatível com muitos repos. Gestão de mudanças via versionamento central. Dependência: Python runtime local. Sinônimos requerem curadoria. |
| B — Instructions locais | **4** | 4 | 0 | Ownership difuso. Custo de manutenção cumulativo. |
| C — Baseline | **1** | 1 | 0 | Inviável para governança. |

**Evolução:** Sem mudança na projeção de viabilidade. Os sinônimos adicionam um custo de manutenção (curadoria do dicionário), mas é marginal e centralizado.

---

## Quadro consolidado

| # | Critério | MCP v2 (A) | MCP v1 | Δ | Instructions (B) | Baseline (C) |
|---|---|---:|---:|---:|---:|---:|
| 1 | Qualidade do plano | **9** | 8 | +1 | 8 | 6 |
| 2 | Aderência ao contexto | **9** | 8 | +1 | 9 | 5 |
| 3 | Completude | 7 | 7 | 0 | 7 | 6 |
| 4 | Consistência interna | 7 | 7 | 0 | 8 | 6 |
| 5 | Centralização efetiva | **9** | 8 | +1 | 3 | 0 |
| 6 | Governança e auditabilidade | **9** | 8 | +1 | 5 | 0 |
| 7 | Escalabilidade projetada | 8 | 8 | 0 | 3 | 0 |
| 8 | Risco de drift *(invertido)* | 2 | 2 | 0 | 7 | 10 |
| 9 | DX | **8** | 7 | +1 | 8 | 5 |
| 10 | Maturidade atual | **7** | 6 | +1 | 7 | 3 |
| 11 | Viabilidade corporativa | 7 | 7 | 0 | 4 | 1 |

**Resumo de deltas:** 6 critérios melhoraram (+1 cada), 5 mantiveram-se estáveis. Nenhum critério regrediu.

---

## Agregação

### Opção A — Média simples (11 critérios)

Para comparação, o critério de drift é invertido: usa-se `(10 − nota)` para normalizar.

| Cenário | Cálculo | Nota final | v1 | Δ |
|---|---|---:|---:|---:|
| MCP v2 | (9+9+7+7+9+9+8+**8**+8+7+7) / 11 | **8,0** | 7,5 | **+0,5** |
| Instructions locais | (8+9+7+8+3+5+3+**3**+8+7+4) / 11 | **5,9** | 5,9 | 0 |
| Baseline | (6+5+6+6+0+0+0+**0**+5+3+1) / 11 | **2,9** | 2,9 | 0 |

### Opção B — Média ponderada (foco em centralização e escala)

Pesos conforme rubrica:

| Critério | Peso | MCP v2 | MCP v1 | Instructions | Baseline |
|---|---:|---:|---:|---:|---:|
| Qualidade do plano | 20% | 1,80 | 1,60 | 1,60 | 1,20 |
| Centralização efetiva | 15% | 1,35 | 1,20 | 0,45 | 0,00 |
| Governança e auditabilidade | 15% | 1,35 | 1,20 | 0,75 | 0,00 |
| Escalabilidade projetada | 15% | 1,20 | 1,20 | 0,45 | 0,00 |
| Risco de drift *(10 − nota)* | 10% | 0,80 | 0,80 | 0,30 | 0,00 |
| DX | 10% | 0,80 | 0,70 | 0,80 | 0,50 |
| Maturidade atual | 10% | 0,70 | 0,60 | 0,70 | 0,30 |
| Viabilidade corporativa | 5% | 0,35 | 0,35 | 0,20 | 0,05 |
| **Total** | **100%** | **8,35** | **7,65** | **5,25** | **2,05** |

**Evolução da nota ponderada MCP:** 7,65 → 8,35 (**+0,70**).

---

## Métricas auxiliares

| Métrica | MCP v2 (A) | MCP v1 | Δ | Instructions (B) | Baseline (C) |
|---|---:|---:|---:|---:|---:|
| # suposições não ancoradas (HIPÓTESE + RISCO) | 7 | 9 | -2 | 9 | 9 |
| # de FATOs declarados | 14 | 13 | +1 | 17 | 18 |
| Ratio FATO / (HIPÓTESE+RISCO) | 2,00 | 1,44 | +0,56 | 1,89 | 2,00 |
| # reprompts necessários | 0 | 0 | 0 | 0 | 0 |
| # tool calls total | 62 | 21 | +41 | 41 | 18 |
| # falhas de tool | 0 | 1 | -1 | 0 | 0 |
| # retries | 0 | 1 | -1 | 0 | 0 |
| # arquivos lidos | 18 | 20 | -2 | 24 | 19 |
| # arquivos citados | 11 | 7 | +4 | 15 | 12 |
| # trechos de código citados | 22 | N/A | — | N/A | 12 |
| # instructions consultadas | 11 (via MCP) | 5 (via MCP) | +6 | 8 (via arquivo) | 0 |
| # search_instructions calls | 7 | ~1 | +6 | — | — |
| list_instructions_index chamado? | Sim | Não | ✓ | — | — |
| Cache implementado? | Sim | Sim | = | Não | Não |
| Build com sucesso? | Sim | Sim | = | Sim | Sim |
| Testes automatizados executados? | Não | Não | = | Não | Não |
| Duração estimada (ms) | 1.140.025 | N/A | — | N/A | 856.913 |

**Observações sobre métricas:**

1. **Instructions consultadas (11 vs 5):** A melhoria mais expressiva. O modelo passou de ~20% para ~46% do corpus de 24 instructions. O novo protocolo (index → buscas temáticas → batch) cumpriu o objetivo de ampliar cobertura.

2. **Ratio FATO/(HIPÓTESE+RISCO) subiu de 1,44 para 2,00:** MCP v2 agora iguala o baseline em ratio, mas com qualidade de FATOs superior (normativos vs descritivos). A redução de HIPÓTESE+RISCO de 9 para 7 indica melhor ancoragem.

3. **Tool calls (62 vs 21):** Aumento de 3x reflete o protocolo de descoberta mais profundo (7 buscas + index + 30 leituras de arquivo). O custo adicional é de latência, não de falhas (0 vs 1).

4. **Arquivos citados (11 vs 7):** Melhoria de 57%, mas ainda abaixo de Instructions locais (15). O modelo MCP ancora-se mais em policies e menos em leitura direta de arquivos do workspace.

5. **Zero falhas em 62 calls:** Robustez operacional atingiu paridade com Instructions locais (0 falhas em 41 calls).

---

## Evolução do gap MCP vs Instructions locais

### Critérios de qualidade individual (1–4)

| Critério | MCP v1 | MCP v2 | Instructions | Gap v1 | Gap v2 |
|---|---:|---:|---:|---:|---:|
| 1 — Qualidade do plano | 8 | **9** | 8 | 0 | **+1 MCP** |
| 2 — Aderência ao contexto | 8 | **9** | 9 | -1 | **0** |
| 3 — Completude | 7 | 7 | 7 | 0 | 0 |
| 4 — Consistência interna | 7 | 7 | 8 | -1 | **-1** |
| **Média 1-4** | **7,50** | **8,00** | **8,00** | **-0,50** | **0,00** |

**Achado principal:** A média dos critérios de qualidade individual agora é **idêntica** (8,0 vs 8,0). Na v1, Instructions locais liderava por 0,5 ponto. O gap foi eliminado nos critérios de qualidade do artefato.

### Critérios estruturais (5–8)

| Critério | MCP v1 | MCP v2 | Instructions | Gap v1 | Gap v2 |
|---|---:|---:|---:|---:|---:|
| 5 — Centralização | 8 | **9** | 3 | +5 | **+6** |
| 6 — Governança | 8 | **9** | 5 | +3 | **+4** |
| 7 — Escalabilidade | 8 | 8 | 3 | +5 | +5 |
| 8 — Drift *(normalizado)* | 8 | 8 | 3 | +5 | +5 |

**Achado:** A vantagem estrutural do MCP ampliou de 4,5 para 5,0 pontos de média nos critérios 5-8.

### Gap total (média ponderada)

| | v1 | v2 | Δ |
|---|---:|---:|---:|
| MCP | 7,65 | **8,35** | +0,70 |
| Instructions | 5,25 | 5,25 | 0 |
| **Gap** | **2,40** | **3,10** | **+0,70** |

O gap ponderado ampliou de 2,40 para 3,10 pontos.

---

## Validação das metas do plano de melhoria

| Meta | Alvo | v1 | v2 | Status |
|---|---|---:|---:|---|
| Critério 2 (Aderência) | ≥ 9 | 8 | **9** | **ATINGIDA** ✓ |
| Critério 4 (Consistência) | ≥ 8 | 7 | **7** | **NÃO ATINGIDA** ✗ |

### Análise da meta não atingida (Critério 4)

**Hipótese testada:** "O ajuste no prompt é suficiente para resolver o Critério 4 sem mudanças nas tools."

**Resultado:** O modelo consultou a policy `microservice-caching-imemorycache-policy` e implementou cache, mesmo com a instrução explícita de que "Consistência com o código prevalece sobre completude normativa" e que ausência no código deve ser rotulada como HIPÓTESE.

**Diagnóstico:** A policy MCP é mais concreta e acionável ("use IMemoryCache para GET por id com chave estável e TTL curto") do que a meta-instrução de conservadorismo ("verifique se já existe no repo; ausente = HIPÓTESE"). O modelo prioriza instruções concretas sobre meta-instruções abstratas.

**Recomendações para v3:**
1. **Tool `check_applicability`:** Verificar automaticamente se os padrões recomendados por uma policy já existem no código antes de sugerir implementação.
2. **Prompt mais prescritivo:** Substituir "consistência com o código prevalece" por checklist explícito: "Para cada policy que recomenda um padrão: (a) busque o padrão no código; (b) se ausente, rotule como HIPÓTESE e NÃO implemente sem confirmação humana."
3. **Flag na policy:** Adicionar metadado `requires_code_evidence: true` nas policies que dependem de infraestrutura existente (cache, messaging, etc.).

---

## Observações cruzadas

### Onde MCP v2 supera Instructions locais

| Critério | MCP v2 | Instructions | Delta | Evidência |
|---|---:|---:|---:|---|
| Qualidade do plano | 9 | 8 | +1 | 11 policies grounding vs 8 |
| Centralização | 9 | 3 | +6 | Fonte única vs 2.400+ cópias |
| Governança | 9 | 5 | +4 | 11 IDs rastreáveis + sha256 |
| Escalabilidade | 8 | 3 | +5 | 1 commit central vs 100+ repos |
| Drift (normalizado) | 8 | 3 | +5 | Consumo central vs cópias |
| Viabilidade corporativa | 7 | 4 | +3 | Ownership claro vs difuso |

### Onde Instructions locais superam MCP v2

| Critério | Instructions | MCP v2 | Delta | Evidência |
|---|---:|---:|---:|---|
| Consistência interna | 8 | 7 | +1 | Conservadorismo em cache; sem contradição entre prompt e ação |

### Onde estão empatados

| Critério | Nota | Observação |
|---|---:|---|
| Aderência ao contexto | 9 | MCP: mais instructions; Instructions: mais arquivos citados |
| Completude | 7 | Mesmas lacunas (testes, observabilidade) |
| DX | 8 | MCP: 0 falhas, mais tool calls; Instructions: setup zero |
| Maturidade | 7 | MCP: MVP melhorado; Instructions: nativo estável |

### Evolução do padrão "qualidade ≈ equivalente, escala ≠"

Na v1, o padrão era: "qualidade individual marginal para Instructions, vantagem estrutural forte para MCP".

Na v2, o padrão evoluiu para: **"qualidade individual empatada, vantagem estrutural ampliada para MCP"**. O único critério onde Instructions ainda lidera (consistência, por 1 ponto) é compensado por qualidade do plano (onde MCP agora lidera por 1 ponto).

---

## Limitações do experimento

1. **Tarefa simples (CRUD):** Mesma limitação da v1. Diferenças tendem a ampliar em tarefas complexas.

2. **Cenários B e C não re-executados:** Apenas o cenário A foi re-executado. Isso isola o efeito das melhorias mas impede comparação "execução a execução" dos 3 cenários simultaneamente.

3. **Critério 4 não validado em cenário sem cache:** A decisão de cache é o único ponto de inconsistência. Em uma tarefa sem policy de cache, o critério 4 poderia ser 8+ para MCP.

4. **Sem validação funcional:** Nenhum cenário executou testes automatizados.

5. **Sem teste multi-repo real:** Escalabilidade projetada, não medida.

6. **Executor único:** Sem validação de reprodutibilidade inter-observador.

7. **Métricas de tempo/tokens incompletas:** Apenas A e C reportaram duração estimada.

---

## Conclusão

### Veredicto por objetivo

| Objetivo | v1 melhor | v2 melhor | Evolução |
|---|---|---|---|
| Qualidade do artefato individual | B (Aderência: 9) | **Empate** (A=8,0, B=8,0 média) | MCP fechou o gap |
| Centralização em escala | A (8) | A (**9**) | MCP ampliou vantagem |
| Governança corporativa | A (8) | A (**9**) | MCP ampliou vantagem |
| Escalabilidade 100+ repos | A (8) | A (8) | Estável |
| DX imediata | B (8) | **Empate** (A=8, B=8) | MCP igualou |
| Maturidade hoje | B (7) | **Empate** (A=7, B=7) | MCP igualou |

### Recomendação (atualizada)

**MCP consolida-se como a abordagem correta para escala corporativa.** As melhorias de tools e prompt eliminaram o gap de qualidade individual (critérios 1-4: média 8,0 vs 8,0) e ampliaram a vantagem estrutural (critérios 5-8). A nota ponderada subiu de 7,65 para **8,35**.

**O único gap remanescente (consistência, -1 ponto) é endereçável** com ajustes focados no tratamento de policies que dependem de infraestrutura existente (cache, messaging, etc.). Não requer redesign da arquitetura MCP.

**Instructions locais permanecem como complemento válido** para contexto específico do repositório. Sua vantagem de DX (setup zero) e conservadorismo nativo são pontos fortes para uso local.

### Principal evidência

MCP v2 obteve nota ponderada de **8,35** contra **5,25** de Instructions locais e **2,05** de Baseline (evolução de +0,70 vs v1). A igualdade nos critérios individuais (média 8,0) demonstra que as melhorias de discoverabilidade (sinônimos, by_tag, batch) traduziram-se em qualidade de artefato equivalente, sem sacrificar as vantagens estruturais que continuam a crescer.

### Principal limitação

O critério 4 (Consistência) permanece em 7, abaixo da meta de 8. A instrução de conservadorismo no prompt não foi suficiente para impedir a implementação de cache sem evidência no código. Isso indica que meta-instruções abstratas perdem para instruções concretas de policy — um achado relevante para o design de prompts futuros.

### Próximos passos sugeridos

1. **Critério 4:** Implementar `check_applicability` ou flag `requires_code_evidence` nas policies.
2. **Critério 3:** Expandir o experimento para tarefa complexa (integração entre serviços, refactoring cross-cutting).
3. **Validação empírica:** Testar em 3+ repositórios reais para medir drift e escalabilidade.
4. **Reprodutibilidade:** Repetir com segundo avaliador e/ou segundo modelo.
