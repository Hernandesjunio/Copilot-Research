# Resposta ao prompt: PROMPT-20260403-002

## Metadados
- **Prompt ID:** PROMPT-20260403-002
- **Data da resposta:** 2026-04-03
- **Fonte:** Copilot Chat no Visual Studio — resposta colada pelo usuário

## Resposta (cole integral ou trechos relevantes)

# Combinando Instructions Nativas com MCP no Visual Studio

> **Objetivo:** Guia prático para dividir responsabilidades entre custom instructions nativas (`.github/instructions/`) e um MCP Server, evitando duplicidade e maximizando a qualidade do contexto fornecido ao Copilot.

---

## Legenda de Confiança

| Ícone | Significado |
|-------|-------------|
| ✅ | Claramente suportado pela plataforma |
| 🔶 | Inferência prática baseada no comportamento observado |
| ⚠️ | Pode variar conforme modo agente e configuração do ambiente |

---

## 1. Quando a informação deve permanecer em instructions nativas

**✅ Claramente suportado**

| Cenário | Motivo |
|---------|--------|
| Convenções de estilo e formatação | Estáveis, universais — devem estar **sempre** no contexto |
| Preferências de linguagem/resposta (ex: "responda em português") | Precisam estar ativas em **toda** interação |
| Regras de segurança (ex: "nunca exponha secrets") | Não podem depender de busca para serem aplicadas |
| Padrões arquiteturais fundamentais do projeto | Referência constante, não mudam por tarefa |
| Regras de escopo com `applyTo` (globs de arquivos) | O mecanismo nativo já resolve isso com filtro por arquivo |

> **Princípio:** se a instrução precisa estar **sempre presente** independentemente da tarefa, ela é nativa.

---

## 2. Quando a informação deveria migrar para resources/tools de um MCP

**🔶 Inferência prática**

| Cenário | Motivo |
|---------|--------|
| Documentação de APIs internas extensas | Volume alto demais para injetar sempre — melhor buscar sob demanda |
| Exemplos de uso por domínio (ex: "como criar um handler de DNS") | Relevantes apenas quando o contexto da tarefa pede |
| Histórico de decisões arquiteturais (ADRs) | Úteis esporadicamente, não em toda interação |
| Catálogo de erros conhecidos e soluções | Só importam quando o erro aparece |
| Mapeamento de dependências entre módulos | Contexto pesado, relevante apenas em tarefas cross-cutting |

> **Princípio:** se a instrução é **condicional à tarefa** ou **volumosa demais** para o contexto fixo, ela é candidata a MCP.

---

## 3. Como evitar duplicidade, conflito ou redundância

**🔶 Inferência prática**

```
┌─────────────────────────────────┐
│   Instructions Nativas          │  ← Regras (O QUÊ fazer)
│   "Sempre use async/await"      │
│   "Responda em português"       │
└────────────┬────────────────────┘
             │ não repete
┌────────────▼────────────────────┐
│   MCP Tools/Resources           │  ← Conhecimento (COMO fazer)
│   "Exemplo de handler async"    │
│   "Padrão de retry do projeto"  │
└─────────────────────────────────┘
```

### Estratégia prática

- **Instructions nativas** = regras declarativas curtas (*"sempre faça X"*, *"nunca faça Y"*)
- **MCP** = base de conhecimento consultável (*"como fazemos X neste projeto"*, *"exemplo de Y"*)
- Na base de ~100 arquivos, avalie cada um: se é uma **regra** (fica nativo) ou uma **referência** (migra para MCP)
- No MCP, inclua um campo de metadado (ex: `source: instructions/dns-handler.md`) para rastreabilidade

---

## 4. Qual modelo traz mais benefício

**✅ + 🔶**

| Modelo | Benefício | Limitação |
|--------|-----------|-----------|
| **Instruções estáveis e sempre presentes** | Consistência garantida | Consome contexto fixo — com ~100 arquivos, pode saturar a janela |
| **Contexto recuperado sob demanda (MCP)** | Escala sem poluir o contexto | Depende da qualidade da busca e da invocação |
| **Híbrido** ✅ | Melhor equilíbrio | Requer governança clara de separação |

### Recomendação

O modelo **híbrido** é o mais eficiente para escala:

- **5–15 instructions nativas** com as regras universais (estilo, idioma, segurança, padrões core)
- **MCP** como camada de busca para os demais ~85+ arquivos de referência

---

## 5. Como estruturar o MCP para usar a base existente

**🔶 Inferência prática**

```
MCP Server
├── /resources
│   └── instructions-index    ← Expõe metadados da base indexada
│
├── /tools
│   ├── search_instructions   ← Busca semântica nos ~100 .md
│   │   input:  { "query": "como tratar erro DNS timeout" }
│   │   output: [ { file, score, trecho } ]
│   │
│   ├── get_instructions_batch ← Retorna conteúdo completo de 1+ .md (histórico: get_instruction)
│   │   input:  { "path": "instructions/dns-handler.md" }
│   │   output: { content, metadata }
│   │
│   └── compose_context        ← Combina múltiplas instructions relevantes
│       input:  { "task": "implementar retry no resolver" }
│       output: { combined_context, sources[] }
```

### Fluxo

1. O MCP indexa os `.md` existentes (pode usar embeddings locais ou busca por keywords/tags)
2. Quando invocado, busca os mais relevantes por similaridade com a tarefa
3. Retorna conteúdo priorizado, sem duplicar o que já está nas instructions nativas

> **Importante:** os arquivos `.md` continuam sendo a **fonte da verdade**. O MCP apenas os lê e indexa. Nenhuma duplicação de conteúdo.

---

## 6. Formato mais eficiente para o MCP retornar conteúdo

**🔶 Inferência prática**

| Formato | Quando usar | Eficiência de tokens |
|---------|-------------|----------------------|
| **Trecho literal** | Regras exatas, trechos de código | ⭐⭐⭐ Alta precisão |
| **Resumo** | Contexto arquitetural amplo | ⭐⭐ Econômico mas perde nuance |
| **Evidências ranqueadas** | Múltiplas instructions podem ser relevantes | ⭐⭐⭐ Permite priorização |
| **Combinação dos três** ✅ | Melhor abordagem geral | ⭐⭐⭐⭐ Adaptável |

### Estrutura recomendada de retorno

```json
{
  "results": [
    {
      "source": "instructions/dns-retry-pattern.md",
      "relevance": 0.92,
      "summary": "Define o padrão de retry exponencial para queries DNS",
      "key_excerpt": "Sempre use Polly com backoff de 1s, 2s, 4s...",
      "full_available": true
    }
  ],
  "composed_context": "Para esta tarefa, aplique: ..."
}
```

Isso permite que o modelo decida se precisa do trecho literal ou se o resumo já basta, economizando tokens.

---

## 7. Como priorizar apenas as instructions relevantes para a tarefa

**🔶 Inferência prática (a mecânica exata pode variar por ambiente)**

- **Nível 1 — Filtragem por escopo:** use metadados nos `.md` (tags, `applyTo` patterns) para pré-filtrar
- **Nível 2 — Busca semântica:** o tool `search_instructions` ranqueia por similaridade com a descrição da tarefa
- **Nível 3 — Top-K:** retorne apenas os **3–5 mais relevantes** (evita poluir o contexto)
- **Nível 4 — Deduplicação:** se uma instrução nativa já cobre o tema, o MCP a omite do retorno

### Exemplo de metadado nos `.md` existentes

```markdown
---
tags: [dns, retry, resilience]
scope: "src/DnsBlocker.Worker/**"
priority: high
---
```

---

## 8. Riscos quando muitas instruções coexistem com tools externas

| Risco | Descrição | Mitigação |
|-------|-----------|-----------|
| **Contradição** | Instrução nativa diz "use HttpClient" e MCP retorna "use Refit" | MCP deve verificar conflito com instructions core antes de retornar |
| **Saturação de contexto** | ~100 instructions nativas + retorno de MCP = janela de contexto esgotada | Mantenha nativas reduzidas (5–15); MCP retorna top-K compacto |
| **Prioridade ambígua** | Qual fonte "ganha" em caso de conflito? | Defina hierarquia: **nativas > MCP** (nativas são a lei, MCP é referência) |
| **Latência** | MCP adiciona round-trip ao fluxo | Cache de índice local; busca rápida por keyword antes de semântica |
| **Drift** | `.md` é atualizado mas índice do MCP fica desatualizado | MCP deve re-indexar ao detectar mudança nos `.md` (watch ou on-demand) |
| **Over-retrieval** | MCP retorna contexto demais, diluindo instruções críticas | Limite rígido de tokens/resultados no retorno |

---

## Resumo da Arquitetura Recomendada

```
┌──────────────────────────────────────────────────┐
│              Copilot (Visual Studio)              │
│                                                   │
│  ┌─────────────────┐   ┌──────────────────────┐  │
│  │ Instructions     │   │ MCP Server           │  │
│  │ Nativas (5-15)   │   │                      │  │
│  │                   │   │  search_instructions │  │
│  │ • Estilo/idioma   │   │ get_instructions_    │  │
│  │                   │   │   batch              │  │
│  │ • Segurança       │   │  compose_context     │  │
│  │ • Padrões core    │   │                      │  │
│  │                   │   │  Fonte: mesmos .md   │  │
│  │ SEMPRE no contexto│   │  SOB DEMANDA         │  │
│  └─────────────────┘   └──────────────────────┘  │
│         ▲ prioridade alta    ▲ prioridade média   │
└──────────────────────────────────────────────────┘
```

---

> **⚠️ Nota sobre variação por ambiente:** o suporte a MCP no Visual Studio está em evolução ativa. A forma como tools MCP são invocados (automática vs. explícita), a prioridade entre fontes de contexto, e o limite de tokens disponível **podem variar** conforme a versão do VS, o modo (Chat vs. Agent), e as configurações do usuário. A arquitetura acima é projetada para ser resiliente a essas variações.

---

## Extração rápida
- **Ferramentas citadas:** `search_instructions`, `get_instructions_batch` (histórico: `get_instruction`), `compose_context`; resource `instructions-index`; indexação (embeddings / keywords-tags)
- **Limitações mencionadas:** MCP no VS em evolução; invocação de tools automática vs. explícita; prioridade entre fontes e orçamento de tokens variam com versão, modo (Chat vs. Agent) e configuração
- **Insights para MCP / extensões:** híbrido com 5–15 nativas + restante via MCP; hierarquia **nativas > MCP**; `.md` como fonte única; retorno JSON com resumo + excerto + `full_available`; top-K 3–5; metadados (`tags`, `scope`, `priority`); mitigação de contradição, saturação, drift e over-retrieval
- **Follow-up sugerido (próximo prompt):** Implementação de re-indexação (watch vs. on-demand) e regra explícita de “omitir do MCP o que já está nas nativas” por tema ou `id`
