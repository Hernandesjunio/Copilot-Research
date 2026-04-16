---
titulo: "Análise comparativa (iteração 1) — MCP (STDIO) vs Instructions locais vs Baseline"
data: "2026-04-16"
modelo_analise: "Opus 4.6 (Cursor Agent)"
modelo_execucao: "GPT 5.4 (Copilot Chat) — cenários A/B/C executados em threads separadas"
rubrica: "../2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md (11 critérios, escala 0–10)"
escopo: "Vertical slice PUT/GET /clientes/{id} — planejamento + implementação + validação"
---

# Análise comparativa (iteração 1) — MCP (STDIO) vs Instructions locais vs Baseline

## Identificação dos cenários

| Cenário | Artefato | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|
| **A — MCP** | `artefatos/hipotese1.md` | `copilot-instructions-mcp.md` | MCP `corporate-instructions` (tools STDIO) + código local |
| **B — Instructions locais** | `artefatos/hipotese2.md` | `copilot-instructions-instructions-locais.md` | `.github/instructions/*.md` + código local |
| **C — Baseline** | `artefatos/hipotese3.md` | `copilot-instructions-baseline.md` | Apenas código local + conhecimento geral do modelo |

**Protocolo:** threads separadas, partindo do zero, sem contaminação. Mesmo ticket canônico (`PUT /clientes/{id}` + `GET /clientes/{id}`). Metodologia staged (plano + implementação + validação).

---

## Avaliação por critério (0–10)

### 1) Qualidade do plano

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **8** | BMAD completo (Background com 3 FATOs, Mission, Approach em 5 passos, Delivery). Decomposição por camada. Implementou cache com IMemoryCache baseado em policy MCP. TTL de 2 min reconhecido como HIPÓTESE. Faltou: critérios de aceite formais, mapeamento de riscos estruturado. |
| B — Instructions locais | **8** | BMAD completo, 5 passos no Approach. 8 instructions listadas com ID e kind. Decisão conservadora de NÃO implementar cache (FATO: sem IMemoryCache no código). Mais granular na seleção de guardrails. Faltou: critérios de aceite formais. |
| C — Baseline | **6** | BMAD funcional mas simplificado. FATOs claros sobre código existente, porém sem ancoragem normativa. Classificação de evidência presente (FATO/HIPÓTESE/RISCO). Faltou: risks, test plan, alternativas rejeitadas. |

**Evidências:**
- A: 4 itens no plano (`qtd_itens_plano: 4`), 13 FATOs declarados.
- B: 5 itens no patch (`qtd_itens_patch: 5`), 17 FATOs declarados.
- C: 5 itens no patch, 18 FATOs declarados — porém FATOs descritivos do código, não normativos.

---

### 2) Aderência ao contexto disponível

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **8** | 5 policies MCP citadas por ID (`microservice-architecture-layering`, `microservice-rest-http-semantics-and-status-codes`, etc.). 7 arquivos do workspace listados. Envelope `OpenFinanceResponse<T>` mantido por evidência de código. TTL como HIPÓTESE reconhecida. |
| B — Instructions locais | **9** | 8 instructions listadas com ID e kind (policy/reference). 8 arquivos do workspace citados. Decision de cache conservadora baseada em FATO (code_search sem IMemoryCache). Crítica do try/catch vs middleware mostra leitura efetiva do código. |
| C — Baseline | **5** | Ancorada no código observável (rotas existentes, envelope, Dapper). FATOs corretos mas puramente descritivos. HIPÓTESE para `KeyNotFoundException` → `404`. Sem normatividade transversal. |

**Evidências:**
- A: 20 arquivos lidos, 7 citados, 5 instructions MCP consumidas via tool.
- B: 24 arquivos lidos, 15 citados, 8 instructions locais referenciadas.
- C: 19 arquivos lidos, 12 citados, 0 instructions.

**Observação:** B obtém nota superior a A porque leu mais arquivos (24 vs 20), citou mais (15 vs 7) e referenciou mais guardrails (8 vs 5). A diferença sugere que a leitura direta de arquivos `.md` permite mais granularidade de referência do que a busca via MCP com 3 tools.

---

### 3) Completude

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **7** | Contrato HTTP completo (200/400/404/408/500). DTOs, validação, persistência Dapper. Cache implementado (IMemoryCache). Integração HTTP externa declarada como fora de escopo. **Faltou:** testes, observabilidade, concorrência otimista. |
| B — Instructions locais | **7** | Contrato HTTP similar. DTOs, validação, persistência. Cache NÃO implementado (lacuna declarada). Referência à policy de testing mas sem implementação. **Faltou:** cache efetivo, testes, observabilidade. |
| C — Baseline | **6** | Contrato HTTP funcional. DTOs, validação, persistência. Cache e integração fora de escopo. **Faltou:** tudo acima + sem normatividade para guiar cobertura. |

**Evidências:**
- A: implementou 7 arquivos (`apply_patch: 7`), incluindo `AddMemoryCache` em DI.
- B: implementou 5 arquivos (`apply_patch: 5`), sem cache.
- C: implementou 5 arquivos (`apply_patch: 6`), sem cache.

**Observação:** A e B empatam porque A ganha em cache mas B é mais conservadora (não inventar sem base). C perde por não ter guardrails guiando o que cobrir.

---

### 4) Consistência interna

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **7** | Status codes coerentes com causas. Separação por camada mantida. Cache com invalidação em PUT (coerente). RISCO reconhecido: ausência de `422` pode ser simplificação. `KeyNotFoundException` como HIPÓTESE internamente consistente. |
| B — Instructions locais | **8** | Status codes coerentes. Separação por camada forte. Decisão de não implementar cache coerente com evidência (sem base = não introduzir). Try/catch mantido para não introduzir inconsistência — reconhece dívida técnica sem ampliar. |
| C — Baseline | **6** | Status codes coerentes por inferência. Separação por camada preservada por cópia do padrão existente. Sem normatividade para validar coerência. Risco de divergência reconhecido. |

**Evidências:**
- A: RISCO DE INTERPRETAÇÃO reconhecido sobre `400` vs `422` (5 riscos total).
- B: try/catch mantido + crítica de dívida técnica documenta trade-off conscientemente.
- C: RISCO DE INTERPRETAÇÃO sobre rota canônica vs existente; sem referência normativa para resolver.

---

### 5) Centralização efetiva

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **8** | MCP como autoridade central via tools STDIO. Corpus em path configurável (central ou local). Atualização propaga por consumo direto. Setup por repo: 1 `.mcp.json`. |
| B — Instructions locais | **3** | Instructions = cópia por repo. 24 instructions × 100 repos = 2.400+ arquivos replicados. Atualização requer distribuição em massa. Sem mecanismo nativo de sincronização. |
| C — Baseline | **0** | Não existe mecanismo de centralização. Cada execução é independente. |

**Evidências:**
- A: `.mcp.json` com `INSTRUCTIONS_ROOT` apontando para path (central em produção, local no experimento por controle).
- B: arquivos `.md` replicados em `.github/instructions/` de cada repo.
- C: nenhum corpus.

---

### 6) Governança e auditabilidade

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **8** | IDs estáveis por instruction. Metadados: `content_sha256`, `priority`, `kind`, `scope`, `tags`. Busca determinística via `search_instructions`. Capacidade de impor revisão/ownership centralmente. |
| B — Instructions locais | **5** | Mesmo esquema de metadados (frontmatter) disponível dentro do repo. Sem garantia de sincronização com autoridade central. Auditoria por repo possível; entre repos, custosa (diff arquivo a arquivo). |
| C — Baseline | **0** | Sem rastreabilidade. Decisões efêmeras. Impossível auditar qual regra estava vigente. |

**Evidências:**
- A: decisões rastreáveis até ID de instruction MCP (ex.: `microservice-caching-imemorycache-policy`).
- B: decisões rastreáveis até arquivo local (ex.: `microservice-data-access-and-sql-security`), mas local por repo.
- C: decisões rastreáveis apenas até inferência do modelo.

---

### 7) Escalabilidade projetada

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **8** | Custo marginal por repo: 1 `.mcp.json`. Correção central: 1 commit. Baixo risco de divergência. Limitação: requer Python + módulo MCP no ambiente do dev. |
| B — Instructions locais | **3** | Custo marginal por repo: copiar 24+ arquivos. Correção global: tocar 100+ repos. Alto risco de divergência. Mitigável com automação (CI, sync scripts) mas não nativo. |
| C — Baseline | **0** | Não escalável. Cada execução reinventa decisões. |

**Evidências:**
- A: relatório cita "escala parcialmente" com ressalvas de corpus estável e CI.
- B: relatório cita escalabilidade viável "desde que haja versionamento + revisão + automações de conformidade" — 3 dependências externas.
- C: relatório cita "exige reprompt frequente para padronização fina".

---

### 8) Risco de drift entre repositórios (INVERTIDO: maior = pior)

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **2** | Consumo central — drift improvável para policies transversais. `content_sha256` para detecção. Risco residual apenas em instructions locais complementares. |
| B — Instructions locais | **7** | Cópias locais sem sync nativo. Drift silencioso provável após edição local, merge incorreto ou onboarding com versão desatualizada. Mitigável com automação, mas frágil. |
| C — Baseline | **10** | Drift máximo. Não há convergência. Cada execução potencialmente diferente. O próprio relatório reconhece: "probabilidade de inconsistência: moderada". |

**Evidências:**
- A: hipotese1 não reporta divergência de normativa — todas as decisões ancoradas em MCP ou código.
- B: hipotese2 cita "drift entre repositórios e corpus central" como risco operacional.
- C: hipotese3 cita "sem guideline explícita de catálogo de erros, o mapeamento de exceções pode divergir".

---

### 9) Experiência do desenvolvedor (DX)

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **7** | Fluidez boa. 21 tool calls (1 falha, 1 retry). Previsibilidade média-alta com MCP consultado. Setup requerido: Python + módulo + `.mcp.json`. |
| B — Instructions locais | **8** | Fluidez boa. 41 tool calls (0 falhas, 0 retries). Setup zero extra (instructions já no repo). Previsibilidade média-alta. Mais interações mas mais robustas. |
| C — Baseline | **5** | Fluidez boa para implementação incremental. 18 tool calls (0 falhas). Previsibilidade parcial. Descoberta manual alta. Alta dependência do modelo para preencher lacunas. |

**Evidências:**
- A: 1 falha em `dotnet test` (path `.sln` inexistente) + 1 retry.
- B: zero falhas em 41 calls — robustez operacional superior.
- C: zero falhas mas relata "dependência do modelo: média/alta para preencher lacunas não explicitadas".

---

### 10) Maturidade atual da solução

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **6** | MVP com 3/~13 tools. Funcional para planejamento + implementação CRUD. Resultados consistentes no caso testado. ~10 tools restantes planejadas. |
| B — Instructions locais | **7** | Funcionalidade nativa do GitHub Copilot. Cobertura adequada para guardrails locais. Robusta (leitura de arquivos `.md`). Não escala, mas madura para uso individual. |
| C — Baseline | **3** | "Funciona" para CRUD simples. Altamente dependente da capacidade do modelo. Instável entre execuções. Sem garantias de consistência. |

**Evidências:**
- A: MVP validado — 3 tools cumprem objetivo para o cenário testado.
- B: mecanismo estável, sem dependências externas.
- C: autoavaliação reconhece fragilidade ("exige muita inferência").

---

### 11) Viabilidade corporativa

| Cenário | Nota | Justificativa |
|---|---:|---|
| A — MCP | **7** | Modelo de ownership claro (squad plataforma). Compatível com muitos times/repos. Gestão de mudanças via versionamento central. Dependência: Python runtime local. Em evolução (MVP). |
| B — Instructions locais | **4** | Ownership difuso (cada repo tem cópias). Compatível mas com custo de manutenção cumulativo. Gestão de mudanças cara (distribuição em massa). Sem dependência operacional extra. |
| C — Baseline | **1** | Inviável para governança. Sem consistência entre equipes. Zero custo operacional, máximo custo de inconsistência. |

**Evidências:**
- A: arquitetura STDIO suporta path central sem infra de rede.
- B: relatório cita "viável desde que haja versionamento, revisão e automações" — 3 pré-requisitos.
- C: relatório conclui "baseline funciona parcialmente, mas exige muita inferência".

---

## Quadro consolidado

| # | Critério | MCP (A) | Instructions (B) | Baseline (C) |
|---|---|---:|---:|---:|
| 1 | Qualidade do plano | 8 | 8 | 6 |
| 2 | Aderência ao contexto | 8 | 9 | 5 |
| 3 | Completude | 7 | 7 | 6 |
| 4 | Consistência interna | 7 | 8 | 6 |
| 5 | Centralização efetiva | 8 | 3 | 0 |
| 6 | Governança e auditabilidade | 8 | 5 | 0 |
| 7 | Escalabilidade projetada | 8 | 3 | 0 |
| 8 | Risco de drift *(invertido)* | 2 | 7 | 10 |
| 9 | DX | 7 | 8 | 5 |
| 10 | Maturidade atual | 6 | 7 | 3 |
| 11 | Viabilidade corporativa | 7 | 4 | 1 |

---

## Agregação

### Opção A — Média simples (11 critérios)

Para comparação, o critério de drift é invertido: usa-se `(10 − nota)` para normalizar.

| Cenário | Cálculo | Nota final |
|---|---|---:|
| MCP | (8+8+7+7+8+8+8+**8**+7+6+7) / 11 | **7,5** |
| Instructions locais | (8+9+7+8+3+5+3+**3**+8+7+4) / 11 | **5,9** |
| Baseline | (6+5+6+6+0+0+0+**0**+5+3+1) / 11 | **2,9** |

### Opção B — Média ponderada (foco em centralização e escala)

Pesos conforme rubrica:

| Critério | Peso | MCP | Instructions | Baseline |
|---|---:|---:|---:|---:|
| Qualidade do plano | 20% | 1,60 | 1,60 | 1,20 |
| Centralização efetiva | 15% | 1,20 | 0,45 | 0,00 |
| Governança e auditabilidade | 15% | 1,20 | 0,75 | 0,00 |
| Escalabilidade projetada | 15% | 1,20 | 0,45 | 0,00 |
| Risco de drift *(10 − nota)* | 10% | 0,80 | 0,30 | 0,00 |
| DX | 10% | 0,70 | 0,80 | 0,50 |
| Maturidade atual | 10% | 0,60 | 0,70 | 0,30 |
| Viabilidade corporativa | 5% | 0,35 | 0,20 | 0,05 |
| **Total** | **100%** | **7,65** | **5,25** | **2,05** |

---

## Métricas auxiliares

| Métrica | MCP (A) | Instructions (B) | Baseline (C) |
|---|---:|---:|---:|
| # suposições não ancoradas (HIPÓTESE + RISCO) | 9 | 9 | 9 |
| # de FATOs declarados | 13 | 17 | 18 |
| Ratio FATO / (HIPÓTESE+RISCO) | 1,44 | 1,89 | 2,00 |
| # reprompts necessários | 0 | 0 | 0 |
| # tool calls total | 21 | 41 | 18 |
| # falhas de tool | 1 | 0 | 0 |
| # retries | 1 | 0 | 0 |
| # arquivos lidos | 20 | 24 | 19 |
| # arquivos citados | 7 | 15 | 12 |
| # instructions consultadas | 5 (via MCP) | 8 (via arquivo) | 0 |
| Cache implementado? | Sim | Não | Não |
| Build com sucesso? | Sim | Sim | Sim |
| Testes automatizados executados? | Não | Não | Não |

**Observações sobre métricas:**

1. **Contagem de suposições idêntica (9)**: surpreendente. O baseline não produz *menos* hipóteses — apenas substitui hipóteses sobre normativa por hipóteses sobre padrões de domínio. A diferença é qualitativa: em A e B, as hipóteses são sobre detalhes (TTL, classificação de exceção); em C, são sobre decisões fundamentais (semântica de status code, mapeamento de erro).

2. **Ratio FATO/(HIPÓTESE+RISCO) crescente (1,44 → 1,89 → 2,00)**: contraintuitivo — baseline declara mais FATOs que MCP. Explicação: sem normatividade, o modelo compensa ancorando-se mais em observações descritivas do código. Quantidade de FATOs não implica qualidade normativa.

3. **Tool calls (21 vs 41 vs 18)**: instructions locais exigiu o dobro de calls que MCP. Isso reflete a diferença de mecanismo: MCP faz busca + leitura direcionada; instructions locais exige varredura mais ampla de arquivos.

4. **Arquivos citados (7 vs 15 vs 12)**: instructions locais citou mais arquivos proporcionalmente, indicando ancoragem mais distribuída no workspace.

---

## Observações cruzadas

### Onde MCP supera Instructions locais

- **Centralização** (8 vs 3): fonte única de verdade vs 2.400+ cópias em 100 repos.
- **Governança** (8 vs 5): auditoria por hash + busca determinística vs diff manual entre repos.
- **Escalabilidade** (8 vs 3): custo marginal ~zero vs custo linear.
- **Drift** (2 vs 7): consumo central vs cópias divergentes.
- **Viabilidade corporativa** (7 vs 4): ownership central vs ownership difuso.

### Onde Instructions locais superam MCP

- **Aderência ao contexto** (9 vs 8): leitura direta de 24 arquivos `.md` é mais granular que 3 tools MCP; 8 instructions referenciadas vs 5. Provável que mais tools MCP reduzam essa diferença.
- **Consistência interna** (8 vs 7): conservadorismo (não implementar cache sem base) produziu coerência ligeiramente superior.
- **DX** (8 vs 7): setup zero vs dependência de Python + módulo. Zero falhas vs 1 falha.
- **Maturidade** (7 vs 6): mecanismo nativo e estável vs MVP em evolução.

### Onde ambos superam Baseline de forma decisiva

Todos os critérios estruturais (centralização, governança, escalabilidade, drift) resultam em 0 para baseline. Mesmo nos critérios de qualidade individual (plano, aderência, completude, consistência), baseline fica 1-3 pontos abaixo.

### Padrão: qualidade individual ≈ equivalente, escala ≠

Para critérios 1-4 (qualidade do artefato), a diferença entre MCP e Instructions locais é marginal (máximo 1 ponto). A divergência aparece nos critérios 5-8 (escala e governança), onde MCP tem vantagem estrutural de 3-5 pontos.

---

## Limitações do experimento

1. **Tarefa simples (CRUD)**: os 3 cenários produziram implementações estruturalmente similares. Em tarefas mais complexas (integração entre serviços, refactoring cross-cutting), a diferença tende a ampliar.

2. **MCP com apenas 3 tools**: o gap de aderência (8 vs 9) e DX (7 vs 8) pode reduzir com as ~10 tools restantes. A avaliação reflete capacidade atual.

3. **Sem validação funcional**: nenhum cenário executou testes automatizados. A validação é limitada a build com sucesso.

4. **Sem teste multi-repo real**: a escalabilidade é projetada (arquiteturalmente sustentada), não medida empiricamente em 100+ repos.

5. **Executor único**: não houve teste com outro desenvolvedor para validar reprodutibilidade.

6. **Métricas de tempo/tokens indisponíveis**: apenas baseline (hipotese3) reportou estimativas de duração. A e B reportaram N/A.

---

## Conclusão

### Veredicto por objetivo

| Objetivo | Melhor cenário | Nota |
|---|---|---:|
| Qualidade do artefato individual | B (Instructions locais) | 9 (aderência) |
| Centralização em escala | A (MCP) | 8 |
| Governança corporativa | A (MCP) | 8 |
| Escalabilidade 100+ repos | A (MCP) | 8 |
| DX imediata (setup mínimo) | B (Instructions locais) | 8 |
| Maturidade hoje | B (Instructions locais) | 7 |

### Recomendação

**MCP é a abordagem correta para escala corporativa.** A equivalência de qualidade individual (critérios 1-4) com superioridade estrutural (critérios 5-8) demonstra que o MVP cumpre seu objetivo e justifica investimento nas tools restantes.

**Instructions locais devem ser reposicionadas como complemento** para contexto específico do repositório (exceções arquiteturais, particularidades de domínio), não como autoridade para padrões transversais.

**Baseline é inviável** para qualquer cenário com expectativa de consistência entre equipes.

### Principal evidência

MCP obteve nota agregada ponderada de **7,65** contra **5,25** de instructions locais e **2,05** de baseline. A diferença concentra-se nos critérios de escala (5-8), onde MCP supera instructions locais por 3-5 pontos, enquanto nos critérios de qualidade individual (1-4) a diferença é de no máximo 1 ponto.

### Principal limitação

O experimento testou apenas CRUD simples com 3 tools MCP. A generalização para cenários complexos depende da evolução do MCP (mais tools) e de validação empírica em múltiplos repositórios reais.
