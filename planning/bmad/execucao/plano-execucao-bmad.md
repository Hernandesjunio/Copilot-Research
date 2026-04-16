# Combinando Instructions Nativas com MCP no Visual Studio

> **Objetivo:** Guia prático para dividir responsabilidades entre custom instructions nativas (`.github/instructions/`) e um MCP Server, evitando duplicidade e maximizando a qualidade do contexto fornecido ao Copilot.

## Implementação de referência

Este repositório inclui o servidor **[`mcp-instructions-server`](../../../mcp-instructions-server/README.md)** (pacote **corporate-instructions-mcp**, transporte **stdio**). As secções **5–7** descrevem o comportamento **como implementado** nesse código; as outras secções permanecem como orientação geral (princípios e riscos). Governança do frontmatter: [`EPIC-01-inventory-governance.md`](../epicos/EPIC-01-inventory-governance.md).

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

## 5. Como o MCP está estruturado (implementação atual)

**✅** Comportamento do pacote [`mcp-instructions-server`](../../../mcp-instructions-server/README.md): servidor **read-only**, **stdio**, variável de ambiente obrigatória **`INSTRUCTIONS_ROOT`** apontando para a pasta raiz do corpus (todos os `*.md` recursivos).

### Tools expostas

Não há recurso MCP separado “resources”; o catálogo é exposto via **tool** dedicada.

```
MCP Server (stdio)
└── tools
    ├── list_instructions_index
    │   └── Sem parâmetros. Devolve JSON: lista de metadados por ficheiro
    │       (id, path, title, tags, scope, priority, kind, content_sha256) e count.
    │
    ├── search_instructions
    │   ├── query: texto livre (obrigatório para pontuar; ver nota abaixo)
    │   ├── tags: opcional, tags separadas por vírgulas (filtro AND com o conjunto do doc)
    │   ├── max_results: 1–20 (predefinição 10)
    │   └── Busca por **sobreposição de palavras-chave** (tokenização + pontuação em título,
    │       corpo e tags; reforço por priority no frontmatter). **Não** usa embeddings.
    │       O JSON inclui `results[]` e um campo **`composed_context`** (texto agregado dos
    │       melhores matches) — não existe tool separada `compose_context`.
    │
    └── get_instructions_batch
        ├── ids: lista separada por vírgula (1 ou mais IDs)
        └── Conteúdo completo do corpo Markdown (após frontmatter); `max_chars_per_instruction`
            para truncagem individual e teto máximo total por resposta.
```

### Fluxo

1. À primeira utilização (ou quando `INSTRUCTIONS_ROOT` muda), o servidor **constrói um índice em memória** a partir dos `.md` (frontmatter YAML + corpo).
2. `search_instructions` ranqueia documentos por **relevância heurística por keywords**, não por semântica vetorial.
3. Para texto integral, o cliente chama `get_instructions_batch` com os `id` devolvidos na pesquisa.

> **Importante:** os ficheiros `.md` são a **fonte da verdade**. O servidor apenas lê e indexa em memória; **reiniciar o processo** passa a ser necessário após alterações no disco (não há *watch* nem reindexação automática em tempo real).

> **Extensão futura:** embeddings ou busca semântica podem substituir ou complementar o passo 2; o desenho atual é deliberadamente simples e local.

---

## 6. Formato de retorno (como no servidor atual)

**✅** O desenho combina resumo, excerto e lista ranqueada na resposta de **`search_instructions`**; o texto completo vem de **`get_instructions_batch`**.

| Formato | Onde aparece | Tokens |
|---------|----------------|--------|
| **Resumo** (`summary`) | Por resultado em `search_instructions` | Económico |
| **Trecho** (`key_excerpt`) | Por resultado (à volta de match ou resumo curto) | Precisão parcial |
| **Contexto agregado** (`composed_context`) | Mesma resposta de pesquisa | Vários resumos concatenados |
| **Corpo completo** (`content`) | Em `get_instructions_batch` | Completo (com truncagem por item e teto total) |

### Estrutura real de `search_instructions` (campos principais)

```json
{
  "results": [
    {
      "source": "instructions/dns-retry-pattern.md",
      "id": "dns-retry-pattern",
      "relevance": 0.1234,
      "score": 12.34,
      "summary": "Primeira linha do corpo condensada…",
      "key_excerpt": "Trecho do corpo perto de um token da query…",
      "full_available": true,
      "tags": ["dns", "retry"],
      "kind": "guideline"
    }
  ],
  "composed_context": "### Título (id)\nResumo curto…\n\n### Outro…"
}
```

Mensagens de aviso (`note`) podem aparecer quando a query está vazia ou não há matches. **`get_instructions_batch`** devolve `instructions[]`, `missing_ids`, `found_count` e limites aplicados.

---

## 7. Como a priorização funciona na implementação

**✅** Mecânica do `mcp-instructions-server` (pode evoluir em versões futuras).

- **Nível 1 — Metadados:** `tags` e `scope` no frontmatter; em `search_instructions`, filtro opcional **`tags=`** (lista separada por vírgulas, intersecção com as tags do documento). `scope` existe para governança e contexto humano; **não** é aplicado automaticamente como glob ao ficheiro aberto no IDE.
- **Nível 2 — Pontuação por keywords:** tokens da `query` contra título, corpo e tags; contributo extra conforme `priority` (`high` / `medium` / `low`). Não há embeddings nem “similaridade semântica” no código atual.
- **Nível 3 — Top-K:** `max_results` limita a lista (1–20; por omissão 10).
- **Nível 4 — Deduplicação com instructions nativas:** **não implementada** no servidor; a hierarquia “nativas > MCP” está indicada nas *instructions* do próprio MCP para o modelo, mas o servidor não lê as nativas nem remove hits automaticamente.

### Exemplo de frontmatter alinhado ao inventário (EPIC-01)

```markdown
---
id: dns-retry-pattern
title: Padrão de retry DNS
tags: [dns, retry, resilience]
scope: "src/DnsBlocker.Worker/**"
priority: high
kind: guideline
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
| **Drift** | `.md` é atualizado mas índice do MCP fica desatualizado | **Reiniciar** o processo do servidor para reconstruir o índice (sem *watch* no MVP) |
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
│  │                   │   │  list_instructions_  │  │
│  │ • Estilo/idioma   │   │    index               │  │
│  │ • Segurança       │   │  search_instructions │  │
│  │ • Padrões core    │   │  (+ composed_context │  │
│  │                   │   │   no JSON)           │  │
│  │                   │   │ get_instructions_    │  │
│  │                   │   │   batch              │  │
│  │                   │   │  Fonte: mesmos .md   │  │
│  │ SEMPRE no contexto│   │  SOB DEMANDA         │  │
│  └─────────────────┘   └──────────────────────┘  │
│         ▲ prioridade alta    ▲ prioridade média   │
└──────────────────────────────────────────────────┘
```

---

> **⚠️ Nota sobre variação por ambiente:** o suporte a MCP no Visual Studio está em evolução ativa. A forma como tools MCP são invocados (automática vs. explícita), a prioridade entre fontes de contexto, e o limite de tokens disponível **podem variar** conforme a versão do VS, o modo (Chat vs. Agent), e as configurações do usuário. A arquitetura acima é projetada para ser resiliente a essas variações.
