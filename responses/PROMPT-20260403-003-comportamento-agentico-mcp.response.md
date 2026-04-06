# Resposta ao prompt: PROMPT-20260403-003

## Metadados
- **Prompt ID:** PROMPT-20260403-003
- **Data da resposta:** 2026-04-03
- **Fonte:** Copilot Chat no Visual Studio (modo agente) — conforme indicado pelo utilizador

## Resposta (cole integral ou trechos relevantes)

# Comportamento Agêntico com MCP Tools

## 1) Iteração de chamadas de tools ao longo da resolução

**Sim.** É possível encadear múltiplas chamadas de tools em sequência, onde o resultado de uma chamada informa a próxima decisão. Exemplo real:

```text
get_projects_in_solution()          → descobre os projetos
    ↓
get_files_in_project("Proj.csproj") → descobre os arquivos
    ↓
get_file("Worker.cs")               → lê o código
    ↓
find_symbol(...)                     → rastreia dependências
    ↓
replace_string_in_file(...)          → aplica a mudança
    ↓
run_build()                          → valida compilação
    ↓
run_tests(...)                       → valida comportamento
```

Também é possível fazer chamadas **em paralelo** quando não há dependência entre elas (ex: ler 3 arquivos ao mesmo tempo).

---

## 2) Detecção de lacunas de contexto

**Sim, parcialmente.** Lacunas de contexto são detectadas de duas formas:

| Situação | Comportamento |
|---|---|
| Usuário menciona um conceito vago ("arrume o bug do DNS") | Usa `code_search` para localizar o conceito no workspace |
| Resultado de uma tool revela dependência desconhecida | Faz nova chamada para investigar (ex: `find_symbol` → `get_file`) |
| Erro de build após edição | Lê o erro, busca o arquivo afetado, corrige |
| Arquivo referencia tipo desconhecido | Usa `get_symbols_by_name` para encontrar a definição |

**Limitação:** Só detecta lacunas que surgem *durante a execução*. Não há um modelo mental persistente do workspace antes de começar.

---

## 3) Interrupção para buscar mais informação

**Sim.** Exemplo concreto:

1. Começa a editar `Worker.cs`
2. Percebe que ele depende de `IDnsService`
3. **Interrompe** a edição
4. Chama `find_symbol` para achar a implementação de `IDnsService`
5. Lê a implementação com `get_file`
6. Só então continua a edição original com contexto completo

Isso acontece naturalmente — não precisa de instrução explícita do usuário.

---

## 4) Fluxo ideal passo a passo

### Fase 1 — Análise

```text
📋 Recebe o pedido do usuário
   ↓
🧠 Decompõe em sub-tarefas conceituais
   ↓
❓ Identifica: "O que preciso saber que ainda não sei?"
```

### Fase 2 — Busca de Contexto (breadth-first)

```text
🔍 get_projects_in_solution()     → visão macro
   ↓
📂 get_files_in_project(...)      → estrutura do projeto relevante
   ↓
📄 get_file(...) / code_search()  → código específico
   ↓
🔗 find_symbol(...)               → dependências e implementações
```

### Fase 3 — Refinamento

```text
🧩 Cruza informações coletadas
   ↓
⚠️ Detecta lacunas? → Volta para Fase 2
   ↓
📝 Formula plano de mudanças (quais arquivos, quais edições)
```

### Fase 4 — Implementação

```text
✏️ replace_string_in_file(...) / create_file(...)
   ↓
🔨 run_build()                    → valida compilação
   ↓
❌ Erros? → Lê erro, corrige, rebuild (loop)
   ↓
🧪 run_tests(...)                 → valida comportamento
   ↓
❌ Falhas? → Investiga, corrige, re-testa (loop)
   ↓
✅ Entrega resultado
```

---

## 5) Limitações que impedem comportamento totalmente agêntico

| Limitação | Impacto |
|---|---|
| **Sem memória entre conversas** | Cada chat começa do zero; não lembra do workspace |
| **Sem execução proativa** | Só age quando o usuário envia uma mensagem |
| **Sem observação contínua** | Não monitora logs, builds ou eventos em tempo real |
| **Contexto finito (token window)** | Em projetos grandes, não consegue "ver tudo" de uma vez |
| **Sem backtracking sofisticado** | Se uma abordagem falha, pode tentar outra, mas não tem árvore de decisão formal |
| **Sem planejamento multi-step persistente** | Não mantém um "plano" entre mensagens — ele é reconstruído a cada turno |
| **Dependência de tools disponíveis** | Só consegue o que as tools expõem (ex: não consegue debugar step-by-step) |

---

## Como induzir comportamento mais agêntico via MCP

### 1. No prompt/instructions, seja explícito sobre o fluxo esperado

```markdown
Antes de implementar qualquer mudança:
1. Mapeie a estrutura do projeto
2. Identifique todas as dependências do código afetado
3. Valide com build e testes após cada mudança
```

### 2. Use o `.github/copilot-instructions.md` para regras persistentes

```markdown
## Workflow
- Sempre leia o arquivo antes de editá-lo
- Sempre rode build após edições
- Sempre busque implementações de interfaces antes de alterá-las
```

### 3. Dê tarefas com escopo claro mas sem micro-gerenciar

```text
❌ "Edite a linha 42 do Worker.cs"
✅ "O serviço de DNS não está filtrando domínios de apostas. Investigue e corrija."
```

O segundo formato **força** a iteração: buscar contexto → entender → implementar → validar.

---

## Resumo

O MCP já oferece capacidade agêntica significativa — iteração, busca dinâmica, validação em loop. As limitações principais são a **ausência de estado entre conversas** e a **falta de proatividade** (só age quando acionado). O melhor que se pode fazer é estruturar instruções que incentivem o ciclo completo de **análise → contexto → implementação → validação**.

## Extração rápida
- **Ferramentas citadas:** `get_projects_in_solution`, `get_files_in_project`, `get_file`, `find_symbol`, `get_symbols_by_name`, `code_search`, `replace_string_in_file`, `create_file`, `run_build`, `run_tests` (nomes ilustrativos do ecossistema VS/Copilot)
- **Limitações mencionadas:** sem memória entre conversas; só age com mensagem do utilizador; sem observação contínua; janela de contexto finita; backtracking informal; plano não persistente entre turnos; dependência do que as tools expõem
- **Insights para MCP / extensões:** prompts explícitos com fases; `copilot-instructions.md` com workflow; tarefas por objetivo (não micro-gestão) para forçar iteração análise → contexto → implementação → validação
- **Follow-up sugerido (próximo prompt):** medir na prática (mesmo repo) se instruções persistentes alteram taxa de build/teste após edição; ou desenhar MCP que exponha apenas operações de alto nível vs. granularidade atual
