# Resposta ao prompt: PROMPT-20260403-001

## Metadados
- **Prompt ID:** PROMPT-20260403-001
- **Data da resposta:** 2026-04-03
- **Fonte:** Copilot Chat no Visual Studio (modo agente) — conforme indicado pelo utilizador

## Resposta (cole integral ou trechos relevantes)

# MCP com GitHub Copilot no Visual Studio — Limites Práticos

> Análise honesta separando comportamento garantido, provável e não controlável via MCP.

---

## 1. O que o MCP consegue ampliar

### ✅ Comportamento garantido
- Expõe **ferramentas** (tools) que podem ser invocadas para buscar dados externos: arquivos, resultados de compilação, pesquisa de símbolos, Azure Resource Graph, etc.
- Permite **recursos** (resources) que expandem o contexto com informações que não estão no prompt original
- Permite **prompts pré-construídos** que podem guiar o comportamento para tarefas específicas
- Amplia o **espaço de ação** disponível — o que o modelo *pode fazer*, não o que ele *vai fazer*

### 🔶 Comportamento provável
- Servidores MCP podem fornecer contexto especializado de domínio que melhora a qualidade das respostas
- O registro de tools no sistema instrucional provavelmente aumenta a frequência com que são invocadas

### ❌ Não controlável via MCP
- O MCP não aumenta a capacidade de raciocínio, a janela de atenção nem a velocidade de inferência do modelo

---

## 2. O que continua sendo decisão exclusiva do modelo

### ✅ Comportamento garantido
- **Decidir se invoca** uma tool ou responde diretamente
- **Interpretar** os resultados retornados pelas tools
- **Sintetizar** múltiplas fontes em uma resposta coerente
- **Recusar ou ignorar** instruções que violem políticas de conteúdo, mesmo que venham de um MCP server
- **Formato e estrutura** da resposta final

```
MCP não executa código no núcleo de inferência do modelo.
Ele apenas expande o "menu" de ações disponíveis.
```

---

## 3. Até onde tools, prompts e resources influenciam as decisões

| Camada | Influência |
|---|---|
| **System prompt / instruction files** | Alta — define comportamento base |
| **Tool results** | Média-alta — informa, não substitui julgamento |
| **Resources** | Média — contexto adicional, não imperativo |
| **MCP Prompts** | Média — são sugestões, não comandos |
| **Histórico da conversa** | Alta — principal âncora de continuidade |

### 🔶 Comportamento provável
- Tool results com alta relevância semântica tendem a pesar mais na resposta
- Contradições entre tool result e o conhecimento do modelo geram hedging ("provavelmente", "verifique...")

### ❌ Não controlável
- A ponderação exata entre fontes de contexto não é configurável externamente

---

## 4. Quando o modelo ignora ferramentas disponíveis

### ✅ Comportamento garantido
- Quando a pergunta é respondível com segurança pelo contexto já disponível — invocar seria desperdício de latência
- Quando a pergunta é claramente fora do escopo das tools disponíveis
- Quando a pergunta é meta (ex: sobre o próprio funcionamento do modelo), não requer lookup de código

### 🔶 Comportamento provável
- Quando o custo de inferência da tool é avaliado como maior que o ganho esperado
- Quando tools similares já foram invocadas na mesma conversa e o resultado foi irrelevante

### ❌ Não controlável
- A heurística interna de "quando vale invocar" não é parametrizável via MCP

---

## 5. Priorização interna de contexto

> **Comportamento provável** — não confirmável externamente.

```
1. Políticas de segurança / conteúdo      ← bloqueio hard, não negociável
2. System prompt + instruction files      ← define "quem o modelo é" nessa sessão
3. Arquivo ativo + seleção do usuário     ← maior relevância local
4. Histórico da conversa                  ← âncora de continuidade
5. Resultados de tools (quando invocados) ← informação fresh
6. Conhecimento paramétrico geral         ← fallback
```

### ❌ Não controlável via MCP
- Não é possível elevar a prioridade de um resource acima do system prompt
- Não é possível forçar que o modelo ignore o histórico de conversa
- Não é possível via MCP alterar o comportamento de safety

---

## Resumo executivo

```
MCP expande o "alcance" do modelo no ambiente.
Não expande o raciocínio, não bypassa políticas,
não controla como o modelo pondera as informações recebidas.
```

### O que um MCP server **pode** fazer de forma confiável

- Fornecer dados que o modelo não teria (arquivos, APIs, queries)
- Registrar tools que ampliam as ações possíveis
- Guiar o comportamento via prompts bem estruturados

### O que um MCP server **não pode** fazer

- Forçar uma decisão específica
- Alterar as políticas de conteúdo do modelo
- Controlar a ponderação interna entre fontes de contexto

---

## Legenda

| Símbolo | Significado |
|---|---|
| ✅ | Comportamento garantido |
| 🔶 | Comportamento provável (inferência) |
| ❌ | Comportamento não controlável via MCP |

## Extração rápida (preencher depois)
- **Ferramentas citadas:** MCP — tools, resources, prompts pré-construídos; exemplos: ficheiros, compilação, símbolos, Azure Resource Graph
- **Limitações mencionadas:** MCP não aumenta raciocínio, janela de atenção nem velocidade de inferência; não força decisões nem altera safety; ponderação entre fontes não é configurável; heurística de invocação de tools não parametrizável via MCP; prioridade de resource vs system prompt / histórico não controlável
- **Insights para MCP / extensões:** MCP amplia o “menu” de ações e o contexto acessível; o modelo continua a decidir invocação, interpretação e síntese; investir em tools com retorno claro e prompts bem estruturados; aceitar limites em políticas e ordenação interna de contexto
- **Follow-up sugerido (próximo prompt):** Testar no VS uma tool MCP concreta e documentar quando o agente a invoca vs. ignora; ou pedir ao Copilot para distinguir o que é específico do produto GitHub Copilot vs. genérico sobre LLMs
