---
titulo: "Análise comparativa — Outbox + Mensageria (Baseline vs MCP vs Instructions locais)"
data: "2026-05-02"
modelo_analise: "Opus 4.6 (Cursor Agent)"
modelo_execucao: "GitHub Copilot (chat/agent — modelo exato não registrado nos artefatos)"
rubrica: "research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md"
escopo: "Vertical slice: outbox transacional + mensageria + consumidor + idempotência + DLQ em API .NET 8 com Dapper/SQL Server"
iteracao: 1
delta_vs: ""
ajustes_aplicados:
  - "Primeira síntese — sem iteração anterior para comparar"
  - "Cenários executados em sessões separadas, mesmo repositório-alvo"
---

# Análise comparativa — Outbox + Mensageria (Iteração 1)

## Contexto

Esta é a **primeira síntese comparativa** do experimento de outbox + mensageria no ciclo `2026-05-04-tentativa-montagem-contexto-mcp`. Três cenários foram executados sobre o mesmo repositório .NET 8 (API de clientes com Dapper/SQL Server), cada um com uma fonte diferente de contextualização:

- **Cenário A (Instructions locais):** apenas `.github/copilot-instructions.md`; sem pasta `.github/instructions/` presente.
- **Cenário B (MCP):** servidor MCP corporativo ativo, com acesso a 9 instructions de domínio + instruction local complementar.
- **Cenário C (Baseline):** sem corpus estruturado; apenas prompt e código do repositório.

Nenhuma iteração anterior existe; portanto, colunas Δ são omitidas.

---

## Identificação dos cenários

| Cenário | Rótulo | Artefato | Copilot-instructions ativo | Fonte de contexto |
|---|---|---|---|---|
| **A** | Instructions locais | `2026-05-02__outbox-mensageria__instructions-locais.md` | `.github/copilot-instructions.md` | Arquivo local (genérico) |
| **B** | MCP (STDIO) | `2026-05-02__cenario-1-outbox-mensageria__mcp.md` | `.github/copilot-instructions.md` + MCP | 9 instructions corporativas via MCP |
| **C** | Baseline | `2026-05-02__cenario-1-outbox-mensageria__baseline.md` | Nenhum | Código do repositório + prompt |

---

## Diferença-chave desta iteração

Primeira síntese — não há iteração anterior.

---

## Avaliação por critério (0–10)

### 1) Qualidade do plano

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 5 | Plano BMAD presente mas enxuto; passos genéricos (estender contratos → persistir → publicar → consumir → DLQ). Sem trade-offs explícitos, sem alternativas rejeitadas, sem mapeamento de riscos detalhado. |
| B — MCP | 7 | Plano BMAD com refinamento por risco/dependência. Approach em 6 passos com referência explícita a preservação de contrato OpenFinance e semântica HTTP. Menciona mapeamento de riscos e validação por critérios de aceite. |
| C — Baseline | 6 | Plano mais detalhado que A: menciona entidades específicas (tabelas), estratégias (BackgroundService, upsert), mas sem ancoragem a padrões corporativos. Trade-offs implícitos. |

**Evidências:**
- B cita explicitamente 6 passos no Approach com concerns transversais (OpenFinance, camadas, DI).
- C nomeia tabelas concretas (`ClienteEventosOutbox`, `ClienteEventosFila`, `ClienteReadModel`, `ClienteEventosProcessados`, `ClienteEventosDlq`) no plano.
- A é o mais conciso — 5 bullets sem detalhamento de validação ou riscos.

---

### 2) Aderência ao contexto disponível

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 4 | Declara uso de `.github/copilot-instructions.md` e identifica lacuna de `.github/instructions/`. Porém as decisões de mensageria/outbox não têm ancoragem em corpus estruturado — dependem de inferência. |
| B — MCP | 8 | Lista 9 instructions MCP aplicáveis com IDs (`microservice-messaging-rabbitmq-publish-consume`, `microservice-data-access-and-sql-security`, etc.) e mapeia decisões a esses IDs. Ancoragem explícita MCP + código_repo em 5 das 6 decisões. |
| C — Baseline | 5 | Decisões ancoradas no código observável (Dapper, camadas, ausência de broker), mas sem referência a normas/padrões estruturados. 3 das 5 decisões com ancoragem "inferencia". |

**Evidências:**
- B: `DECISIONS_JSON` mostra ancoragem "MCP" em 4 de 6 decisões, "codigo_repo" nas restantes.
- C: `DECISIONS_JSON` mostra ancoragem "inferencia" em 2 de 5 decisões, "codigo_repo" em 2, "inferencia" em 1.
- A: `DECISIONS_JSON` mostra ancoragem "codigo_repo" em 2 decisões, "inferencia" em 2, "instruction_local" em 1.

---

### 3) Completude

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 5 | Cobre outbox, POST/PUT, read-model, idempotência, DLQ, correlação. Falta: observabilidade, testes, cache justificado, validação funcional. Métricas de execução quase todas N/A. |
| B — MCP | 7 | Mesma cobertura funcional + documenta lacunas MCP (migração, bootstrap, testes). Métricas mais completas (57 tool calls, bytes lidos, estimativa de tokens). |
| C — Baseline | 6 | Cobertura funcional equivalente a B. Métricas parciais (42 tool calls, duração 681s). Menos reflexão sobre lacunas estruturais. |

**Evidências:**
- A: `qtd_tool_calls_total: N/A`, `duracao_ms: N/A` — métricas indisponíveis.
- B: `qtd_tool_calls_total: 57`, `duracao_ms: 3480000`, `bytes_aprox_lidos: 108000`.
- C: `qtd_tool_calls_total: 42`, `duracao_ms: 681019`.

---

### 4) Consistência interna

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 6 | Sem contradições aparentes. Camadas respeitadas. Mas avaliação final (escala 0–2) desalinhada da rubrica oficial (0–10) sem justificativa. |
| B — MCP | 7 | Decisões se reforçam: MCP → guardrails → código. Avaliação 0–2 também desalinhada da rubrica. Coerência entre plano e implementação confirmada no relatório. |
| C — Baseline | 6 | Plano e implementação coerentes. Uma falha de tool (patch inválido) recuperada com retry. Avaliação 0–2 igualmente desalinhada. |

**Evidências:**
- Todos usam escala 0–2 na autoavaliação em vez de 0–10 da rubrica — possível artefato do template de execução.
- B: "Patch vs plano: coerente (camadas e contratos respeitados)".
- C: `falhas: 1` (patch inválido ao criar interface), `retries: 1` — recuperação documentada.

---

### 5) Centralização efetiva

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 2 | Corpus local (`.github/copilot-instructions.md`) é por-repositório. Sem mecanismo de centralização. Lacuna explícita: sem `.github/instructions/`. |
| B — MCP | 7 | Corpus centralizado via servidor MCP com IDs estáveis e tools de busca/listagem/batch. Atualização central propaga-se automaticamente a qualquer repo conectado. |
| C — Baseline | 0 | Sem qualquer mecanismo de centralização. |

**Evidências:**
- B usa 3 tools de discovery MCP (`corporate_instructions_list_instructions_index`, `corporate_instructions_search_instructions`, `corporate_instructions_get_instructions_batch`).
- A constata "não existe pasta `.github/instructions/`" — sem fallback centralizado.

---

### 6) Governança e auditabilidade

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 3 | Versionado em Git, mas sem metadados estruturados (id, tags, priority). Auditoria limitada ao histórico do arquivo único. |
| B — MCP | 7 | Instructions com frontmatter (id, tags, priority, kind, scope). IDs estáveis citados nos relatórios. Auditoria por hash/diff do corpus central possível. |
| C — Baseline | 0 | Sem corpus; sem rastreabilidade. |

**Evidências:**
- B cita 9 IDs de instructions com nomes estáveis — rastreabilidade direta.
- A cita apenas 1 arquivo genérico.

---

### 7) Escalabilidade projetada

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 3 | Escala com cópia manual entre repos + risco de divergência. Sem mecanismo de sync. |
| B — MCP | 6 | Escala para repos conectados ao mesmo servidor. Limitação: cada repo precisa setup do MCP. "Sustenta-se parcialmente: bom para guardrails corporativos repetíveis". |
| C — Baseline | 1 | Não escala — cada execução é ad-hoc. |

**Evidências:**
- B: seção "Escalabilidade em 100+ repositórios" explicita que sustenta guardrails mas falha em "sinais locais".
- A: seção "Escalabilidade em múltiplos repositórios" constata "Riscos: duplicação, drift e manutenção distribuída".

---

### 8) Risco de drift entre repositórios (INVERTIDO: maior = pior)

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 7 | Cópias locais sem sync automático. Sem detecção de divergência. Drift provável. |
| B — MCP | 4 | Consumo central reduz drift do corpus. Risco remanescente: "decisões locais (migração, operação) divergem" do MCP. |
| C — Baseline | 10 | Sem padrão — divergência silenciosa garantida entre repos. |

**Evidências:**
- B: "Risco de drift MCP x código local: médio; MCP define direção, mas decisões locais divergem".
- C: sem mecanismo algum — score máximo (pior).

---

### 9) Experiência do desenvolvedor (DX)

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 5 | "Fluidez: parcial. Previsibilidade: média. Dependência de prompt: alta pela lacuna de instruções locais específicas." |
| B — MCP | 5 | "Fluidez: média (houve interrupção por erro de sintaxe e retomada). Reprompt: necessário." 57 tool calls sugere overhead. |
| C — Baseline | 5 | "Fluidez: boa para evolução incremental. Previsibilidade: parcial." Menos tool calls (42), mas mais inferência. |

**Evidências:**
- Todos reportam previsibilidade "parcial" ou "média".
- B teve mais tool calls (57) mas incluiu tools de discovery MCP — overhead de setup vs valor de ancoragem.
- C teve duração real mais curta (681s vs ~3480s de B), embora métricas de A sejam N/A.

---

### 10) Maturidade atual da solução

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 4 | Mecanismo nativo do GitHub Copilot, mas sem corpus local efetivo (`.github/instructions/` ausente). Funciona, mas não exercido plenamente. |
| B — MCP | 5 | Servidor funcional com tools de busca e batch. MVP utilizável. Limitações: sem policy de migração, sem cobertura operacional. |
| C — Baseline | 3 | Não é "solução" — é ausência de solução. Funciona por capacidade intrínseca do modelo. |

**Evidências:**
- B usa 3 tools MCP distintas + corpus com 9 instructions relevantes — MVP operacional.
- A: "governança: potencial alta, mas não exercida por ausência do corpus esperado".

---

### 11) Viabilidade corporativa

| Cenário | Nota | Justificativa |
|---|---|---|
| A — Instructions locais | 4 | Viável para repo individual. Escala corporativa exige automação de sync/lint + processo de ownership. |
| B — MCP | 6 | Modelo de ownership central possível. Compatível com múltiplos repos via stdio. Gestão de mudanças por frontmatter + Git. Dependência: runtime local do servidor. |
| C — Baseline | 1 | Inviável para governança corporativa. Sem padronização, sem rastreio. |

---

## Quadro consolidado

| # | Critério | A (Instr. locais) | B (MCP) | C (Baseline) |
|---|---|---|---|---|
| 1 | Qualidade do plano | 5 | 7 | 6 |
| 2 | Aderência ao contexto | 4 | 8 | 5 |
| 3 | Completude | 5 | 7 | 6 |
| 4 | Consistência interna | 6 | 7 | 6 |
| 5 | Centralização efetiva | 2 | 7 | 0 |
| 6 | Governança e auditabilidade | 3 | 7 | 0 |
| 7 | Escalabilidade projetada | 3 | 6 | 1 |
| 8 | Risco de drift (**invertido**) | 7 | 4 | 10 |
| 9 | Experiência do desenvolvedor | 5 | 5 | 5 |
| 10 | Maturidade atual | 4 | 5 | 3 |
| 11 | Viabilidade corporativa | 4 | 6 | 1 |

---

## Agregação

### Média simples (com normalização do drift)

Para o critério 8 (invertido), usa-se `(10 − nota)` na média.

| Cenário | Soma (c1–7, c9–11) + (10−c8) | Média simples (/11) |
|---|---|---|
| A — Instructions locais | 5+4+5+6+2+3+3+(10−7)+5+4+4 = 44 | **4.0** |
| B — MCP | 7+8+7+7+7+7+6+(10−4)+5+5+6 = 71 | **6.5** |
| C — Baseline | 6+5+6+6+0+0+1+(10−10)+5+3+1 = 33 | **3.0** |

### Média ponderada (pesos da rubrica)

| Critério | Peso | A | B | C |
|---|---|---|---|---|
| 1. Qualidade do plano | 20% | 1.00 | 1.40 | 1.20 |
| 5. Centralização efetiva | 15% | 0.30 | 1.05 | 0.00 |
| 6. Governança | 15% | 0.45 | 1.05 | 0.00 |
| 7. Escalabilidade | 15% | 0.45 | 0.90 | 0.15 |
| 8. Drift (10−nota) | 10% | 0.30 | 0.60 | 0.00 |
| 9. DX | 10% | 0.50 | 0.50 | 0.50 |
| 10. Maturidade | 10% | 0.40 | 0.50 | 0.30 |
| 11. Viabilidade corp. | 5% | 0.20 | 0.30 | 0.05 |
| **Total ponderado** | **100%** | **3.60** | **6.30** | **2.20** |

> **Nota:** os critérios 2 (aderência), 3 (completude) e 4 (consistência) não têm peso explícito na tabela da rubrica (que soma 100% sem eles). Para a média ponderada acima, foram usados apenas os 8 critérios com pesos definidos. Na média simples, todos os 11 critérios contribuem igualmente.

---

## Métricas auxiliares

| Métrica | A (Instr. locais) | B (MCP) | C (Baseline) |
|---|---|---|---|
| Tool calls totais | N/A | 57 | 42 |
| Falhas de tool | N/A | 2 | 1 |
| Retries | N/A | 2 | 1 |
| Arquivos lidos | 20 | 23 | 20 |
| Arquivos citados | 12 | 19 | 18 |
| Trechos citados | N/A | 34 | 20 |
| Duração (ms) | N/A | 3.480.000 | 681.019 |
| Itens de patch | 18 | 17 | 18 |
| Afirmações FATO | 12 | 18 | 22 |
| Afirmações HIPÓTESE | 3 | 6 | 3 |
| Afirmações RISCO | 3 | 8 | 4 |
| Bytes lidos (aprox.) | N/A | 108.000 | N/A |

**Observações:**

1. **Duração de B é 5× maior que C**, mas inclui discovery MCP (3 tools extras) e mais arquivos lidos/citados. Parte pode ser overhead de rede/servidor ou diferença de plataforma de execução (horários distintos no `inicio_iso`).
2. **A não reporta métricas de execução** — a plataforma usada não expôs consolidação automática. Isso limita comparação quantitativa.
3. **B tem mais HIPÓTESE e RISCO que C**, o que pode indicar maior consciência de incerteza (positivo para rigor) ou maior dependência de inferência. Dado que B também tem mais FATO que A, interpreta-se como rigor de documentação superior.
4. **Ratio FATO/(HIPÓTESE+RISCO):** A = 2.0, B = 1.3, C = 3.1. C documenta proporcionalmente menos incerteza — pode ser viés de omissão ou menor complexidade percebida.

---

## Observações cruzadas

### Onde B (MCP) supera claramente

- **Aderência ao contexto** (+3 vs A, +3 vs C): ancoragem a 9 IDs de instructions corporativas vs inferência.
- **Centralização** (+5 vs A, +7 vs C): mecanismo nativo de consumo central.
- **Governança** (+4 vs A, +7 vs C): metadados estruturados, IDs estáveis.
- **Drift** (−3 vs A, −6 vs C invertido): consumo central reduz divergência.

### Onde A e B empatam ou quase empatam

- **DX** (5 vs 5 vs 5): nenhuma abordagem se destacou em fluidez neste experimento.
- **Consistência interna** (6 vs 7 vs 6): diferença marginal.

### Onde C (Baseline) surpreende

- **Qualidade do plano** (6): ligeiramente acima de A (5), embora sem corpus. Sugere que o modelo compensou parcialmente a ausência de contexto com plano mais detalhado em entidades concretas.
- **Ratio FATO/(HIPÓTESE+RISCO)** mais alto (3.1): documenta mais fatos proporcionalmente — possível efeito de menor escopo de análise.

### Onde A (Instructions locais) ficou aquém

- **Centralização** (2) e **Governança** (3): o corpus local genérico (`.github/copilot-instructions.md` apenas) não oferece estrutura suficiente.
- **Métricas N/A**: sem dados quantitativos de execução, a comparação fica prejudicada.

---

## Limitações do experimento

1. **Modelo de execução não controlado**: os artefatos não registram com certeza o mesmo modelo em todos os cenários. Variações de modelo podem confundir o efeito da fonte de contexto.
2. **Métricas de A incompletas**: sem `duracao_ms`, `qtd_tool_calls_total`, `tokens` — impossível comparação quantitativa plena.
3. **Ausência de testes automatizados**: nenhum cenário executou testes de integração. Validação funcional limitada a build + inspeção de código.
4. **Execução única por cenário**: sem repetições, não é possível medir variância intra-cenário.
5. **Cenário A com corpus empobrecido**: a ausência de `.github/instructions/` pode subestimar o potencial de instructions locais bem estruturadas. O resultado reflete o estado atual, não o potencial.
6. **Horários e condições de execução distintos**: B iniciou à meia-noite, C às 07:52, A sem timestamp — possíveis variações de carga/performance da plataforma.
7. **Escala de autoavaliação inconsistente**: os três relatórios usam escala 0–2 em vez de 0–10, o que limita granularidade da autoavaliação dos cenários.

---

## Conclusão

### Veredicto

**MCP (B) lidera com margem significativa** nas dimensões organizacionais (centralização, governança, escalabilidade, drift) e na aderência ao contexto. Em qualidade técnica do plano, a vantagem é moderada (+1–2 pontos sobre A e C).

**Instructions locais (A)** ficaram aquém do potencial por ausência de corpus `.github/instructions/` — o resultado reflete mais a lacuna do setup do que uma limitação intrínseca da abordagem.

**Baseline (C)** demonstra que o modelo produz planos funcionais mesmo sem contexto estruturado, mas sem mecanismo de padronização, governança ou escala.

### Principal evidência

O cenário MCP foi o **único que ancorou decisões de outbox/idempotência/DLQ em IDs de instructions corporativas**, reduzindo inferência em 4 de 6 decisões documentadas — contra 1 de 5 em A e 0 de 5 em C.

### Principal limitação

Métricas de execução incompletas (especialmente cenário A) e execução única por cenário impedem conclusões estatísticas robustas.

### Próximos passos sugeridos

1. **Repetir cenário A com `.github/instructions/` populado** para comparação justa do mecanismo nativo.
2. **Padronizar coleta de métricas** (tool calls, duração, tokens) em todos os cenários — idealmente via instrumentação automática.
3. **Executar pelo menos 2–3 repetições** por cenário para medir variância.
4. **Testar cenário híbrido** (MCP + instructions locais complementares) para verificar se há ganho aditivo.
5. **Incluir validação funcional** (teste de integração automatizado ou script de smoke test) como critério de aceite obrigatório.
