---
titulo: "Critérios de comparação — Instructions locais vs MCP (STDIO) vs Baseline"
data: "2026-04-16"
escopo: "Comparações reprodutíveis entre abordagens de contextualização para planejamento (e extensível para geração de código)"
---

## Objetivo

Definir critérios **operacionais** (medíveis/observáveis) para comparar abordagens de contextualização:

- **A**: Instructions locais (`.github/copilot-instructions.md` + `.github/instructions/*`)
- **B**: MCP STDIO (tools + corpus central)
- **C**: Baseline (sem corpus estruturado; apenas prompt/histórico)

O resultado esperado é permitir que qualquer avaliador repita o experimento e chegue a notas comparáveis, reduzindo subjetividade.

---

## Como usar (procedimento mínimo)

1. **Fixe o mesmo problema** (mesma tarefa, mesma definição de pronto).
2. **Fixe o mesmo protocolo de execução** (ex.: “staged: plano antes de código”; threads separadas; sem contaminação).
3. Para cada abordagem (A/B/C), produza o artefato alvo (ex.: `implementation_plan.md`) e colete evidências.
4. Aplique a rubrica abaixo e registre:
   - nota por critério (0–10)
   - evidências (bullets com links/trechos/contagens)
   - observações (trade-offs e limitações)
5. Se desejar uma nota consolidada, use **média simples** ou pesos por objetivo (ver seção “Agregação”).

> Importante: alguns critérios são **invertidos** (quanto maior, pior). Esses estão marcados explicitamente.

---

## Critérios e rubricas (0–10)

### 1) Qualidade do plano (0–10)

Mede a qualidade técnica do plano entregue para o problema proposto.

- **Evidências mínimas**
  - Estrutura (ex.: BMAD ou equivalente), com missão, passos, validação.
  - Decomposição por camadas/componentes (quando aplicável).
  - Trade-offs e alternativas rejeitadas.
  - Mapeamento de riscos e dependências.
  - Critérios de aceite/test plan.

- **Escala (âncoras)**
  - **0**: plano ausente, genérico ou não acionável; sem passos executáveis.
  - **5**: plano executável, mas com lacunas importantes (erros, camadas, testes, decisões críticas sem tratamento).
  - **10**: plano completo e acionável; decisões técnicas justificadas; riscos + validação bem definidos; minimiza ambiguidades.

---

### 2) Aderência ao contexto disponível (0–10)

Mede se a saída está **ancorada no contexto fornecido pela abordagem** (instructions/MCP/código) e não só em “boas práticas genéricas”.

- **Evidências mínimas**
  - Referências explícitas a IDs/normas/arquivos/regras do corpus (quando existem).
  - Confronto com o código real do repositório (quando aplicável).
  - Menções consistentes a padrões organizacionais específicos (contratos, status codes, envelope, observabilidade, etc.).

- **Escala**
  - **0**: ignora o contexto; resposta genérica sem sinais de leitura/consulta.
  - **5**: usa parte do contexto, mas ainda com decisões principais inferidas sem ancoragem.
  - **10**: decisões centrais claramente derivadas do contexto; baixa necessidade de suposições não ancoradas.

---

### 3) Completude (0–10)

Mede cobertura dos aspectos esperados do artefato para o nível do experimento (planejamento).

- **Evidências (planejamento de API, exemplo)**
  - Contrato HTTP (rotas, status codes, erros).
  - DTOs e validação.
  - Domínio e persistência.
  - Observabilidade (mínimo).
  - Estratégia de testes (unit/integration/contract).

- **Escala**
  - **0**: cobre apenas uma parte pequena; falha em incluir itens críticos.
  - **5**: cobre a maior parte, mas deixa lacunas relevantes (ex.: erros, testes, observabilidade, concorrência).
  - **10**: cobre todos os tópicos essenciais para execução sem reprompt estrutural.

---

### 4) Consistência interna (0–10)

Mede coerência do plano: ausência de contradições entre camadas, contratos e recomendações.

- **Evidências mínimas**
  - Status codes coerentes com causas.
  - Responsabilidades por camada sem “vazamentos” (regras de negócio fora do domínio, por exemplo).
  - Estratégia de erro consistente (não mistura padrões incompatíveis).

- **Escala**
  - **0**: múltiplas contradições; recomendações se anulam.
  - **5**: coerente na maior parte, com algumas inconsistências pontuais.
  - **10**: coerência forte; decisões se reforçam e não conflitam.

---

### 5) Centralização efetiva (0–10)

Mede quão bem a abordagem suporta uma **fonte única de verdade** para padrões transversais entre repositórios.

- **Evidências mínimas**
  - Existe “autoridade” única (corpus central) ou há cópias por repo?
  - Atualização uma vez vs atualização em massa.
  - Facilidade de consumo por múltiplos repos (setup e operacionalização).

- **Escala**
  - **0**: não existe mecanismo de centralização.
  - **5**: existe parcialmente, mas depende de replicação/manual/automação externa frágil.
  - **10**: centralização nativa e direta; baixa duplicação; atualização propagada automaticamente.

---

### 6) Governança e auditabilidade (0–10)

Mede capacidade de governar o corpus: rastreabilidade, versionamento, auditoria e classificação.

- **Evidências mínimas**
  - Identificadores estáveis (ex.: `id`) e metadados (tags, priority, kind, scope).
  - Capacidade de auditar mudanças (ex.: hash, changelog, diff).
  - Possibilidade de impor revisão/ownership e políticas (ex.: `priority: high`).

- **Escala**
  - **0**: sem rastreabilidade; impossível auditar qual regra estava vigente.
  - **5**: rastreabilidade limitada; auditoria possível mas cara/manual.
  - **10**: rastreabilidade forte; auditoria barata e objetiva; suporte a políticas de governança.

---

### 7) Escalabilidade projetada (0–10)

Mede como o custo cresce ao escalar para muitos repositórios (ex.: 100+).

- **Evidências mínimas**
  - Custo marginal por repositório (setup + manutenção).
  - Esforço para corrigir/introduzir uma policy transversal.
  - Risco de divergência ao longo do tempo.

- **Escala**
  - **0**: custo explode com o número de repos; impraticável.
  - **5**: escalável com automação considerável, ainda com pontos de falha e custos recorrentes.
  - **10**: custo marginal baixo; manutenção principalmente central; baixa fricção operacional.

---

### 8) Risco de drift entre repositórios (0–10) — **INVERTIDO (maior = pior)**

Mede probabilidade de repositórios divergirem do padrão organizacional ao longo do tempo.

- **Evidências mínimas**
  - Existência de cópias locais vs consumo central.
  - Mecanismos de detecção de divergência (hash, diff, auditoria).
  - Facilidade de atualização sincronizada.

- **Escala (invertida)**
  - **0**: drift improvável (consumo central + mecanismos de detecção).
  - **5**: drift possível, mas mitigável com processos/automação.
  - **10**: drift altamente provável; sem mecanismos nativos; divergência silenciosa.

---

### 9) Experiência do desenvolvedor (DX) (0–10)

Mede fluidez no uso diário (tempo, fricção, previsibilidade).

- **Evidências mínimas**
  - Número de passos extras (setup, chamadas, “orquestração”).
  - Interrupções no fluxo (latência percebida, round-trips).
  - Clareza de “como obter o contexto certo” (descoberta).

- **Escala**
  - **0**: fricção alta; uso diário inviável.
  - **5**: usável, mas com custos frequentes (setup/latência/reprompt).
  - **10**: fluido; baixo overhead; previsível.

---

### 10) Maturidade atual da solução (0–10)

Mede prontidão “hoje” (não o potencial futuro).

- **Evidências mínimas**
  - Cobertura de funcionalidades necessárias (ex.: tools do MCP, qualidade/curadoria do corpus).
  - Robustez operacional (setup, falhas, degradação).
  - Aderência consistente em múltiplas execuções.

- **Escala**
  - **0**: protótipo frágil; resultados instáveis.
  - **5**: MVP utilizável com limitações conhecidas.
  - **10**: maduro; confiável; pronto para escala com governança.

---

### 11) Viabilidade corporativa (0–10)

Mede adequação para adoção organizacional: manutenção, suporte, governança e operação.

- **Evidências mínimas**
  - Modelo de ownership e publicação de normas.
  - Compatibilidade com muitos times/repos.
  - Gestão de mudanças (versionamento, depreciação, rollout).
  - Dependências operacionais (ex.: runtime local).

- **Escala**
  - **0**: inviável (custo/risco alto; difícil governar).
  - **5**: viável com restrições e investimento de processo/automação.
  - **10**: viável e sustentável; governável; baixo custo marginal.

---

## Métricas auxiliares (opcionais, mas recomendadas)

Estas ajudam a justificar notas e reduzir subjetividade:

- **# de suposições não ancoradas**: contagem de “assumindo que…”, “provavelmente…”, “não tenho como saber…”.
- **# de reprompts necessários**: quantas vezes o humano precisou corrigir/fornecer detalhes para destravar.
- **Tempo total até artefato final** (aprox.): do prompt inicial até o plano final.
- **# de chamadas de tool (para MCP)**: separando busca vs leitura completa (proxy de latência/custo).
- **Cobertura do check de validação**: quantos cenários/testes/aceite foram explicitados.

---

## Agregação (nota consolidada)

### Opção A — média simples

Use quando o objetivo é “comparação geral” entre abordagens.

### Opção B — pesos por objetivo do experimento

Sugestão (planejamento, foco em centralização e escala):

- Qualidade do plano: **20%**
- Centralização efetiva: **15%**
- Governança e auditabilidade: **15%**
- Escalabilidade projetada: **15%**
- Risco de drift (invertido): **10%**
- DX: **10%**
- Maturidade atual: **10%**
- Viabilidade corporativa: **5%**

> Se o experimento for “qualidade do plano local apenas” (single repo), aumente “Qualidade do plano” e “DX” e reduza “Centralização/Escala”.

---

## Template de registro (copiar/colar)

```markdown
### Comparação: <Tarefa/Artefato>

**Data:** YYYY-MM-DD
**Modelo(s):** <...>
**Protocolo:** staged? threads separadas? (sim/não)

#### A — Instructions locais
- Notas:
  - Qualidade do plano: X/10
  - Aderência ao contexto: X/10
  - ...
- Evidências:
  - ...

#### B — MCP (STDIO)
- Notas: ...
- Evidências: ...

#### C — Baseline
- Notas: ...
- Evidências: ...

#### Observações
- ...
```

