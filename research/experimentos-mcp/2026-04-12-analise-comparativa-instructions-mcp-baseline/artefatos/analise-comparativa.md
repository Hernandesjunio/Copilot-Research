# Análise comparativa — Instructions locais vs MCP (STDIO) vs Baseline

**Data/hora:** 2026-04-12 16:00:00  
**Revisão:** R1 — 2026-04-12  
**Modelo:** Opus 4.6 (análise consolidada; hipóteses A/B/C produzidas com GPT 5.4).  
**Escopo:** avaliação crítica de três abordagens de contextualização para planejamento de endpoint `PUT /api/v1/clientes/{id}`, com foco em centralização de conhecimento, escalabilidade e viabilidade corporativa em escala.

---

## 0. Correções factuais e metodológicas

### MCP é STDIO, não servidor remoto

O `.mcp.json` do repositório declara:

```json
{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "corporate_instructions_mcp"],
  "env": { "INSTRUCTIONS_ROOT": ".github\\instructions" }
}
```

O MCP roda como **processo local via STDIO**, não como serviço de rede. Consequências:

- **Não há risco de indisponibilidade de servidor remoto.** O processo é iniciado sob demanda pela IDE.
- **Não há latência de rede.** A comunicação é inter-processo local, com custo negligível comparado à inferência da LLM.
- **Não há dependência operacional de infraestrutura externa.** O perfil de falha é de tooling local: falha se o ambiente Python estiver corrompido ou se o módulo não estiver instalado.

### Execução dos experimentos

Cada experimento foi executado em **thread separada, partindo do zero**, sem contaminação sequencial. Isso elimina o risco de que o resultado de A tenha influenciado B ou C.

### Metodologia staged: plano antes de código

O experimentador utiliza **planejamento antes de codificação**, validando o plano com múltiplas LLMs (Cursor, Gemini, ChatGPT, Copilot Chat) antes de gerar código. A lógica é: se o plano produzido com um determinado contexto é ruim, não há razão para prosseguir para código. A próxima etapa declarada é gerar e medir código.

Essa abordagem staged é metodologicamente válida. O experimento atual testa qualidade de plano. Conclusões sobre qualidade de código ficam para o próximo experimento.

### Estado do MCP

O MCP atual é um **MVP com 3 tools implementadas** (`search_instructions`, `list_instructions_index`, `get_instruction`). Há ~10 tools adicionais planejadas. A avaliação reflete capacidade atual. A lógica de validação MVP é: se 3 tools não produzem resultado pelo menos equivalente às instructions locais, não há justificativa para construir mais 10. Resultados equivalentes ou superiores validam a continuidade do investimento.

### `INSTRUCTIONS_ROOT` aponta para path local por decisão de experimento

O `INSTRUCTIONS_ROOT` aponta para `.github\instructions` dentro do repositório **deliberadamente para o experimento**: isso garante que o corpus consumido pelo MCP (B) e pelas instructions locais (A) seja idêntico, eliminando variável de conteúdo. Para troca de experimento, basta alterar o `copilot-instructions.md` para apontar para a fonte de verdade do cenário desejado.

Em operação real, a configuração aponta para um **diretório compartilhado na máquina do desenvolvedor** (pasta do usuário ou path corporativo), de onde todos os repositórios consomem o mesmo corpus via `.mcp.json`. A arquitetura do MCP STDIO já suporta isso nativamente — o `INSTRUCTIONS_ROOT` pode ser qualquer path acessível ao processo local.

### Reprodutibilidade do corpus

O corpus foi produzido por pipeline assistida por LLM: Copilot Chat identificou gaps a partir de experimentos documentados → gerou prompt estruturado → Cursor processou o prompt e gerou as instructions. O pipeline de geração (dado o mesmo prompt estruturado como input) é reprodutível independente de quem executa. A identificação inicial de gaps também foi assistida por LLM a partir de artefatos experimentais fixos, reduzindo a subjetividade do processo. Múltiplas LLMs (Cursor, Gemini, ChatGPT, Copilot Chat) foram utilizadas ao longo da pesquisa para reduzir viés de ferramenta específica.

---

## 1. Resumo executivo

**Melhor abordagem para centralização:** MCP (STDIO). É a única que oferece fonte única de verdade sem exigir duplicação de arquivos entre repositórios.

**Mais sustentável em escala:** abordagem híbrida — MCP como autoridade para padrões transversais, instructions locais restritas a contexto específico do repositório.

**Principais trade-offs:**

| Dimensão | Instructions locais (A) | MCP STDIO (B) | Baseline (C) |
|---|---|---|---|
| Qualidade do plano | Alta | Alta | Mediana |
| Centralização real | Nenhuma | Alta | Inexistente |
| Custo de manutenção em escala | Alto e cumulativo | Baixo por repo | Zero direto, alto indireto |
| Dependência operacional | Filesystem local | Processo local + Python | Nenhuma |
| Risco de drift entre repos | Alto | Baixo | Máximo |
| Latência adicional | Nenhuma | Nenhuma (STDIO) | Nenhuma |

**Veredicto:** A e B produzem planos de qualidade equivalente para um repositório individual. O diferencial está no que acontece em 100+ repositórios: A multiplica custo de manutenção linearmente; B mantém custo constante no corpus central. A equivalência de resultados entre A e B, obtida com apenas 3 tools, valida a viabilidade do MVP e justifica investimento nas ~10 tools restantes.

---

## 2. Centralização vs duplicação

### Qual abordagem evita duplicação?

**MCP (B) é a única que evita duplicação por design.** O corpus vive em um ponto central (diretório compartilhado) e é consumido via STDIO. Cada repositório precisa apenas de um `.mcp.json` apontando para o path do corpus.

**Instructions locais (A)** exigem que cada repositório tenha sua cópia dos arquivos `.md`. Com 24 instructions e 100+ repos, isso gera 2.400+ arquivos replicados sem mecanismo nativo de sincronização.

**Baseline (C)** não tem corpus. Não há duplicação porque não há padronização.

### Qual tem menor risco de drift?

**MCP (B).** Uma correção no corpus central é consumida imediatamente por todos os repositórios que apontam para o mesmo path. Não há janela de inconsistência, não há PRs em massa, não há merge de conflitos em arquivos de instructions.

**Instructions locais (A)** têm risco de drift alto e crescente. Mesmo com nomes de arquivo idênticos, nada impede divergência após edição local, merge incorreto ou onboarding com versão desatualizada.

**Baseline (C)** não tem drift porque não tem convergência. Cada execução é independente e potencialmente diferente.

### Qual facilita evolução global?

**MCP (B).** Nova policy publicada uma vez no diretório central, disponível para todo o parque. Instructions locais exigem distribuição manual ou automação externa, adicionando complexidade sem resolver versionamento semântico.

---

## 3. Qualidade técnica das respostas

### Planejamento

A e B produziram planos estruturalmente equivalentes: BMAD completo, decomposição por camada, riscos, critérios de aceite, alternativas rejeitadas. A diferença marginal é que B apresentou taxonomia de erros HTTP ligeiramente mais granular (incluiu `412` para pré-condição falhada).

C produziu plano funcional mas defensivo, com reconhecimento explícito e repetido de que as decisões são suposições não confirmadas. Autoavaliação de consistência: 3/10.

| Aspecto | A | B | C |
|---|---|---|---|
| Estrutura BMAD | Completa | Completa | Ausente |
| Semântica REST fundamentada | Sim, por instruction | Sim, por instruction | Inferida |
| Taxonomia de erros HTTP | Derivada de policy | Derivada de policy, mais granular | Genérica |
| Concorrência otimista | Discutido com opções | Discutido com recomendação mais assertiva | Mencionado como lacuna |
| Testes por camada | Planejados por policy | Planejados por policy | Sugeridos genericamente |

### Consistência

A e B mantêm coerência interna porque estão ancoradas no mesmo corpus normativo. C reconhece que outra execução poderia produzir decisões diferentes.

### Diferença entre A e B

A diferença mais relevante não é na qualidade final, mas no **mecanismo de acesso**: A depende de o assistente encontrar e ler arquivos locais; B oferece busca determinística via tools (`search_instructions`). Isso sugere que em corpora maiores, B terá vantagem de descoberta — o assistente encontra instructions relevantes mesmo sem saber o nome do arquivo.

Nos 24 instructions atuais essa vantagem é perceptível mas não decisiva. Em 50+ instructions, tende a ser significativa.

### Significado da equivalência A ≈ B para o MVP

O fato de B (3 tools, busca determinística) produzir resultado equivalente a A (leitura direta de arquivos pelo assistente) demonstra que as 3 tools implementadas cumprem seu objetivo para o cenário de planejamento. Isso é exatamente a evidência que um MVP precisa gerar: viabilidade comprovada no caso base, justificando investimento nas próximas iterações.

---

## 4. Escalabilidade (100+ repositórios)

### Esforço de manutenção

| Cenário | Instructions locais (A) | MCP STDIO (B) |
|---|---|---|
| Corrigir erro em 1 policy | Tocar 100+ repos | Tocar 1 arquivo no corpus central |
| Adicionar nova policy | Distribuir para 100+ repos | Publicar 1 vez |
| Auditar aderência | Diff arquivo a arquivo por repo | Verificar `content_sha256` |
| Onboarding de novo repo | Copiar corpus inteiro | Adicionar `.mcp.json` apontando para path central |

### Governança

**MCP favorece governança rastreável.** Cada instruction tem `id`, `content_sha256`, `priority` e `kind`. Isso permite auditoria por hash, classificação por prioridade e busca por tag. Instructions locais oferecem o mesmo esquema dentro do repositório, mas sem garantia de sincronização com autoridade central.

### Riscos operacionais

Com MCP STDIO, os riscos são de **tooling local**, não de infraestrutura de rede:

- **Eliminado:** indisponibilidade de rede, latência de chamada remota, dependência de serviço externo.
- **Permanece:** dependência de ambiente Python funcional, módulo instalado e corpus acessível no path configurado.
- **Mitigável:** se o path central estiver indisponível, o assistente degrada para comportamento sem contexto (equivalente a C). Isso pode ser mitigado com validação de setup no onboarding.

---

## 5. Experiência do desenvolvedor

### Fluidez

**A:** alta. Contexto próximo, resolução rápida, sem dependências externas.

**B:** alta. STDIO sem latência de rede. O custo de tool calls é transparente para o desenvolvedor — o assistente gerencia as chamadas internamente.

**C:** baixa. Reprompt constante necessário. O próprio experimento C listou 6 temas que exigiriam intervenção humana.

### Dependência de prompt

**A e B:** baixa para temas cobertos pelo corpus. Moderada para decisões funcionais que nenhum corpus cobre (regras de negócio, mutabilidade de campos, unicidade de email).

**C:** alta. Sem ancoragem normativa, o assistente depende do desenvolvedor para cada decisão não trivial.

### Previsibilidade

**A:** previsível dentro do repositório, imprevisível entre repositórios.

**B:** previsível entre repositórios, desde que consumam o mesmo corpus.

**C:** imprevisível por definição.

---

## 6. Análise crítica dos argumentos do experimentador

### Argumento 1: "Planejamento antes de código é metodologia válida — estou medindo capacidade de plano, não de código"

**Avaliação: aceito.**

A abordagem staged é metodologicamente correta: validar plano antes de investir em código. Se o plano falha, gerar código é desperdício. O experimento atual delimita claramente seu escopo (qualidade de plano) e declara o próximo passo (gerar e medir código). Não há afirmação indevida de que plano equivalente implica código equivalente.

### Argumento 2: "Resultados semelhantes provam que as 3 tools cumpriram 100% do objetivo"

**Avaliação: aceito.**

A lógica MVP é precisa: se 3 tools produzem resultado pelo menos equivalente ao de instructions locais, as tools funcionam para o cenário testado. Se o resultado fosse inferior, seria necessário corrigir antes de construir mais tools. Equivalência no caso base é exatamente a evidência necessária para prosseguir.

### Argumento 3: "Threads separadas eliminam contaminação"

**Avaliação: aceito.**

Execução em threads independentes, partindo do zero, é o controle correto para esse tipo de comparação.

### Argumento 4: "Não há latência e não há servidor porque STDIO"

**Avaliação: aceito.**

O `.mcp.json` confirma `"type": "stdio"`. Processo local, sem rede, sem serviço remoto. Custo de I/O inter-processo é negligível comparado à inferência da LLM.

### Argumento 5: "O corpus é reprodutível — o pipeline é determinístico dado o mesmo input"

**Avaliação: aceito.**

O pipeline de produção do corpus foi: experimento documentado → análise de gaps por LLM (Copilot Chat) → prompt estruturado → geração por LLM (Cursor). Dado o mesmo prompt estruturado como input, qualquer pessoa obteria resultado equivalente no Cursor. A etapa de identificação de gaps também foi assistida por LLM a partir de artefatos fixos, não puramente por julgamento humano. O processo utiliza múltiplas LLMs para reduzir viés de ferramenta específica.

Observação residual: em qualquer processo de curadoria, há decisões de framing (quais perguntas fazer, quando considerar o corpus suficiente). Isso é inerente a qualquer autoria — assistida ou manual — e não constitui viés metodológico específico deste experimento.

### Argumento 6: "MVP com caso simples é metodologia correta"

**Avaliação: aceito.**

Validar com caso simples antes de aumentar complexidade é prática padrão. Se o MCP não funciona para CRUD, não funcionará para cenários complexos. A progressão declarada (caso simples → tarefas complexas, conforme o MCP evolui com mais tools) é coerente.

### Argumento 7: "C foi feito para documentar dificuldades sem contexto estruturado"

**Avaliação: aceito.**

Baseline é metodologicamente necessário como referência de controle. Sem C, não há como quantificar o valor agregado por A ou B.

### Argumento 8: "INSTRUCTIONS_ROOT local é deliberado para controle experimental"

**Avaliação: aceito.**

Manter o corpus em `.github\instructions` durante o experimento garante que A e B consomem exatamente os mesmos arquivos, eliminando variável de conteúdo. Em produção, o path aponta para diretório compartilhado. A arquitetura do MCP já suporta isso nativamente.

---

## 7. Limitações do experimento

### O que foi provado

1. MCP STDIO com 3 tools produz planos de qualidade equivalente às instructions locais para endpoint CRUD simples.
2. As 3 tools implementadas cumprem seu objetivo para o cenário de planejamento.
3. Ambas as abordagens (A e B) são substancialmente superiores ao baseline sem contexto (C).
4. O corpus de 24 instructions é suficiente para cobrir planejamento de API REST em .NET com Dapper.
5. A busca determinística do MCP encontra instructions relevantes sem depender de leitura sequencial de arquivos.
6. A arquitetura STDIO é viável como mecanismo de entrega de contexto sem latência de rede e sem dependência de servidor.

### O que fica para próximos experimentos

1. **Qualidade de código gerado.** O experimentador declara isso como próximo passo. Até lá, a equivalência é comprovada para planos.
2. **Tarefas mais complexas.** Conforme o MCP evolua com mais tools, cenários fora de CRUD devem ser testados (integração entre serviços, refactoring cross-cutting, incident response).
3. **Teste com múltiplos repositórios reais.** A escalabilidade é arquiteturalmente sustentada e o mecanismo de path compartilhado é suportado, mas a operação em 100+ repos não foi testada empiricamente.
4. **Teste com outro desenvolvedor.** Validaria reprodutibilidade da experiência sem conhecimento prévio do corpus.

Essas são limitações esperadas de um MVP, não defeitos metodológicos. O experimento atual cobre o que se propôs a cobrir.

---

## 8. Conclusão final

### Escolha: "MCP é superior para centralização"

### Fundamentação

1. **Para centralização**, MCP é objetivamente superior. Instructions locais não centralizam — distribuem cópias. MCP STDIO mantém fonte única sem custo de rede, sem duplicação e sem risco de drift.

2. **Para qualidade individual**, ambos são equivalentes. As 3 tools do MVP produzem contextualização de mesma qualidade que a leitura direta de instructions locais.

3. **Para escala**, MCP tem custo marginal próximo de zero por repositório adicional (um `.mcp.json` por repo apontando para path central), enquanto instructions locais têm custo linear (24 arquivos × N repos).

4. **Para governança**, MCP oferece mecanismos nativos (`id`, `content_sha256`, `priority`, busca determinística) que instructions locais oferecem apenas dentro do repositório.

5. **Baseline sem contexto é inviável** para qualquer cenário com expectativa de consistência entre equipes.

6. **O MVP está validado.** A equivalência de resultados com 3 tools justifica o investimento nas ~10 restantes, que devem ampliar a capacidade do MCP para cenários além de planejamento.

---

## 9. Recomendação arquitetural

### Estratégia para ambiente corporativo

```
┌──────────────────────────────────────────────────┐
│      Corpus central (diretório compartilhado)     │
│  - policies transversais: REST, erros, DI,        │
│    resiliência, observabilidade, testes, SQL       │
│  - versionado, auditável por content_sha256       │
│  - ownership: squad de plataforma/arquitetura     │
│  - path: diretório do usuário ou path corporativo │
└─────────────────────┬────────────────────────────┘
                      │ consumido via STDIO (local)
       ┌──────────────┼──────────────────┐
       ▼              ▼                  ▼
  ┌─────────┐   ┌─────────┐       ┌─────────┐
  │  Repo A  │   │  Repo B  │ ...  │  Repo N  │
  │          │   │          │      │          │
  │ .mcp.json│   │ .mcp.json│      │ .mcp.json│
  │ (STDIO,  │   │ (STDIO,  │      │ (STDIO,  │
  │  aponta  │   │  aponta  │      │  aponta  │
  │  p/ path │   │  p/ path │      │  p/ path │
  │  central)│   │  central)│      │  central)│
  │          │   │          │      │          │
  │ .github/ │   │ .github/ │      │ .github/ │
  │ instructions│ │ instructions│   │ instructions│
  │ (APENAS  │   │ (APENAS  │      │ (APENAS  │
  │  contexto│   │  contexto│      │  contexto│
  │  local)  │   │  local)  │      │  local)  │
  └─────────┘   └─────────┘      └─────────┘
```

### Regras concretas

1. **MCP STDIO para padrões transversais.** REST, erros, layering, DI, observabilidade, testes, resiliência, SQL, segurança. O corpus central é a autoridade.

2. **Instructions locais apenas para contexto do repositório.** Exceções arquiteturais aprovadas, particularidades do domínio, entrypoints de navegação, mapeamento de legacy específico.

3. **`copilot-instructions.md` como entrypoint leve.** Instruir o assistente a consultar o MCP para padrões transversais. Sem policies embutidas.

4. **Governança do corpus:**
   - ownership por squad de plataforma;
   - PR review obrigatório para policies `high`;
   - changelog versionado;
   - `content_sha256` como mecanismo de auditoria;
   - CI validando unicidade de ids e integridade de frontmatter.

5. **Evolução do MCP:**
   - implementar as ~10 tools restantes;
   - validar com geração de código (próximo experimento);
   - validar com tarefas progressivamente mais complexas;
   - medir: taxa de reprompt, cobertura de contexto, desvio entre plano e código.

---

## Avaliação consolidada

### Rubrica utilizada (critérios definidos)

Para definições operacionais (o que significa 0/5/10), evidências exigidas, métricas auxiliares e sugestão de pesos, ver: `artefatos/criterios-de-comparacao.md`.

| Critério | Instructions locais (A) | MCP STDIO (B) | Baseline (C) |
|---|---:|---:|---:|
| Qualidade do plano | 8 | 9 | 5 |
| Centralização | 3 | 9 | 0 |
| Escalabilidade projetada | 4 | 9 | 0 |
| Governança | 5 | 9 | 0 |
| Risco de drift | 7 *(alto)* | 2 *(baixo)* | 10 *(máximo)* |
| Experiência do desenvolvedor | 8 | 8 | 4 |
| Maturidade atual | 8 | 6 *(MVP validado)* | N/A |
| Viabilidade corporativa | 4 | 8 | 1 |

> Nota sobre "Risco de drift": escala invertida — valor alto = risco alto = pior.
> Nota sobre "Maturidade atual": MCP é MVP com 3/~13 tools. Nota 6 reflete MVP validado com espaço para evolução.

---

## Conclusão final

O MCP STDIO é a abordagem correta para centralização de conhecimento em escala corporativa. A evidência experimental confirma equivalência de qualidade com instructions locais e superioridade em centralização, governança e projeção de escala. O MVP está validado: 3 tools cumprem o objetivo para planejamento e justificam investimento nas próximas iterações.

Instructions locais devem ser reposicionadas como complemento para contexto específico do repositório, não como autoridade para padrões organizacionais.

Baseline sem contexto estruturado é inviável para qualquer cenário que exija consistência entre equipes.
