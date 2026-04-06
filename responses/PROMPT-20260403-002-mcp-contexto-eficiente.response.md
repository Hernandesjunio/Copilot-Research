# Resposta ao prompt: PROMPT-20260403-002

## Metadados
- **Prompt ID:** PROMPT-20260403-002
- **Data da resposta:** 2026-04-03
- **Fonte:** Copilot Chat (conforme indicado pelo utilizador)

## Resposta (cole integral ou trechos relevantes)

# Design de MCP Server Eficiente em Contexto

> Guia prático baseado no comportamento real de processamento do modelo, não em teoria.

---

## 1. Formato de contexto — ranking por eficiência

| Formato | Eficiência | Por quê |
|---|---|---|
| Evidências com metadados | ⭐⭐⭐⭐⭐ | Localização imediata — filepath, linha, relevância |
| Chunks pequenos e focados | ⭐⭐⭐⭐ | Menos ruído, mais precisão na síntese |
| Resumos estruturados | ⭐⭐⭐ | Bom para overview, ruim para decisões de código |
| Documentos completos | ⭐⭐ | Funciona para arquivos pequenos, degrada em grandes |

### Formato ideal de retorno de tool

```json
{
  "source": "src/Services/BetBlockerPipeline.cs",
  "lines": "42-67",
  "relevance": "direct-match",
  "content": "// apenas o trecho relevante",
  "symbols": ["BetBlockerPipeline.ExecuteAsync", "ILogger"]
}
```

**Por quê:** Com `filepath + line range + conteúdo`, o modelo consegue:
- Referenciar com precisão no código gerado
- Fazer edits cirúrgicos
- Evitar pedir o arquivo inteiro depois

**Anti-pattern:** Retornar arquivo inteiro de 500 linhas quando só 20 importam. O modelo processa tudo, mas a atenção se dilui.

---

## 2. Reação a problemas de contexto

### Excesso de contexto

O modelo prioriza trechos mais próximos semanticamente da pergunta. O restante vira ruído — não atrapalha ativamente, mas **consome janela de contexto** que poderia ter informação útil.

```
Regra: máximo de 3-5 resultados por invocação de tool.
Se precisar de mais, o modelo invoca novamente com query refinada.
```

### Contexto irrelevante

O modelo gasta ciclos avaliando relevância, conclui que não é útil, e ignora. Mas o custo de avaliação já foi pago.

**Pior caso:** Contexto irrelevante mas *parecido* com algo relevante — causa respostas que misturam conceitos.

> Filtragem server-side é sempre melhor que deixar o modelo filtrar.

### Contexto redundante

Se o mesmo trecho aparece 3x via tools diferentes, o modelo o pesa como uma única fonte. Mas os tokens foram gastos 3x.

> Deduplicação por `filepath + range` no MCP server antes de retornar.

---

## 3. Heurísticas para o MCP server

### Quando buscar mais contexto

```
BUSCAR quando:
  - O modelo pede explicitamente (invoca a tool)
  - A query menciona símbolos não presentes no contexto atual
  - A task requer modificar arquivo ainda não lido
  - Há referência a configuração/settings não visíveis

NÃO buscar proativamente:
  - O MCP não deve "empurrar" contexto sem ser invocado
  - Pre-loading massivo desperdiça janela em 80% dos casos
```

### Quando parar de buscar

```
PARAR quando:
  - Já tem filepath + conteúdo do trecho alvo
  - Já tem a assinatura do método/classe envolvida
  - 2 buscas consecutivas retornaram sem novos resultados úteis
  - O modelo tem informação suficiente para gerar o diff
```

### Evitar repetição

```csharp
// Cache de resultados por sessão
public class ToolResultCache
{
    private readonly Dictionary<string, HashSet<string>> _returnedChunks = new();

    public bool AlreadyReturned(string filePath, string lineRange)
        => _returnedChunks.TryGetValue(filePath, out var ranges)
           && ranges.Contains(lineRange);

    public IReadOnlyList<SearchResult> Deduplicate(IReadOnlyList<SearchResult> results)
        => results.Where(r => !AlreadyReturned(r.FilePath, r.LineRange)).ToList();
}
```

### Priorização de trechos relevantes

```
1. Arquivo ativo do usuário              → sempre incluir se relevante
2. Definição do símbolo mencionado       → alta prioridade
3. Call-sites / referências diretas      → média-alta
4. Arquivos de configuração relacionados → média
5. Testes do componente                  → média (útil para entender contrato)
6. Documentação inline                   → baixa (modelo já tem conhecimento geral)
```

---

## 4. Tools especializadas vs. genéricas

**Resposta: combinação das duas, com forte viés para especializadas.**

Quando o modelo vê `get_symbols_by_name`, sabe exatamente o que ela retorna e quando usá-la. Quando vê `search_everything(query)`, precisa inferir — e frequentemente subutiliza.

### Arquitetura recomendada

```
Tools especializadas (usar primeiro):
├── find_symbol          → quando sabe o nome do símbolo
├── get_file             → quando sabe o path
├── get_project_structure → quando precisa entender layout
└── get_config           → quando precisa de settings

Tool genérica (fallback):
└── semantic_search      → quando não sabe onde procurar
```

### Padrão de implementação

```csharp
// Tool especializada — descrição clara = invocação precisa
[McpTool("get_domain_by_status")]
[Description("Returns domains filtered by classification status. " +
             "Use when you need to find domains that are pending, " +
             "blocked, or allowed.")]
public async Task<IReadOnlyList<DomainInfo>> GetDomainsByStatus(
    [Description("Status filter: pending, blocked, allowed")]
    string status,
    [Description("Maximum results to return. Default: 10")]
    int limit = 10)
{
    // Retornar objetos estruturados, não strings
    // Incluir metadados que ajudem o modelo a decidir próximo passo
}

// Tool genérica — só como fallback
[McpTool("search_domains")]
[Description("Semantic search across all domain data. " +
             "Use only when specialized tools don't cover the query.")]
public async Task<IReadOnlyList<SearchResult>> SearchDomains(
    [Description("Natural language search query")]
    string query)
{
    // ...
}
```

**Detalhe crítico:** A frase `"Use when..."` na `[Description]` é o que mais influencia a decisão de invocar ou não. Descrições vagas = tool ignorada.

---

## 5. Princípios de design — resumo

| # | Princípio |
|---|---|
| 1 | Retorne chunks pequenos com metadados |
| 2 | Máximo 3-5 resultados por invocação |
| 3 | Deduplique por `filepath + range` na sessão |
| 4 | Tools especializadas com descrições claras |
| 5 | Tool genérica apenas como fallback |
| 6 | Filtre server-side, não deixe pro modelo |
| 7 | Inclua `"Use when..."` nas descrições |
| 8 | Nunca empurre contexto não solicitado |

---

## Legenda

| Símbolo | Significado |
|---|---|
| ⭐⭐⭐⭐⭐ | Máxima eficiência |
| ⭐⭐ | Baixa eficiência |

## Extração rápida (preencher depois)
- **Ferramentas citadas:** tools MCP especializadas + busca genérica como fallback; retorno JSON com `source`, linhas, relevância, símbolos; cache/dedup no servidor
- **Limitações mencionadas:** janela de contexto consumida por excesso; custo de avaliar irrelevante; redundância gasta tokens sem multiplicar “peso” da evidência
- **Insights para MCP / extensões:** 3–5 resultados por call; filtro server-side; descrições com “Use when…”; não pré-carregar contexto sem invocação
- **Follow-up sugerido (próximo prompt):** (opcional) validar heurísticas com métricas reais no teu stack ou contrato OpenAPI/SDK do teu servidor
