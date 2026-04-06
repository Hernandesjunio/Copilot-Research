# Resposta ao prompt: PROMPT-20260403-002

## Metadados
- **Prompt ID:** PROMPT-20260403-002
- **Data da resposta:** 2026-04-03
- **Fonte:** Copilot Chat no Visual Studio (modo agente) — conforme indicado pelo utilizador

> **Nota:** A resposta original incluía um preâmbulo repetido e parcialmente truncado (segunda versão de tabelas e JSON incompleto). Abaixo fica o corpo consolidado e completo fornecido pelo Copilot.

## Resposta (cole integral ou trechos relevantes)

# Arquitetura MCP para Projetos .NET Corporativos

---

## 1) Tipos de Tools Recomendadas

### Descoberta & Navegação

| Tool | Descrição |
|------|-----------|
| `get_solution_structure` | Retorna projetos, dependências e camadas da solução |
| `get_project_files` | Lista arquivos de um projeto específico |
| `find_symbol` | Localiza definições, referências e implementações de símbolos via compilador |
| `code_search` | Busca semântica por conceitos no workspace |

### Leitura & Contexto

| Tool | Descrição |
|------|-----------|
| `get_file` | Lê faixas específicas de linhas de um arquivo |
| `get_errors` | Retorna erros de compilação de arquivos específicos |
| `get_output_logs` | Lê logs de build, debug, testes, Git, NuGet |

### Mutação

| Tool | Descrição |
|------|-----------|
| `replace_in_file` | Substituição cirúrgica com contexto obrigatório |
| `multi_replace` | Batch de substituições atômicas |
| `create_file` | Criação de novos arquivos |
| `remove_file` | Remoção com limpeza de referências no `.csproj` |

### Validação

| Tool | Descrição |
|------|-----------|
| `run_build` | Compila o workspace e retorna erros |
| `get_tests` | Descobre testes relevantes (por assembly, tipo, método, outcome) |
| `run_tests` | Executa testes com filtros compostos |

### Execução & Infra

| Tool | Descrição |
|------|-----------|
| `run_terminal` | Executa comandos no terminal (último recurso) |
| `get_best_practices` | Consulta boas práticas por serviço Azure/tecnologia |
| `generate_cli_command` | Gera comandos `az` CLI a partir de intenção natural |

---

## 2) Quando Cada Tool Deve Ser Usada

```
┌─────────────────────────────────────────────────────┐
│              FLUXO DE DECISÃO DO AGENTE              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Usuário fez pedido                                 │
│       │                                             │
│       ▼                                             │
│  Tenho o arquivo exato? ──SIM──► get_file           │
│       │ NÃO                                         │
│       ▼                                             │
│  Tenho o nome do símbolo? ──SIM──► find_symbol      │
│       │ NÃO                                         │
│       ▼                                             │
│  É um conceito/comportamento? ──SIM──► code_search  │
│       │ NÃO                                         │
│       ▼                                             │
│  Preciso da estrutura? ──SIM──► get_solution +      │
│       │                         get_project_files   │
│       ▼                                             │
│  Após mudanças:                                     │
│    ► get_errors (arquivo) → run_build (workspace)   │
│    ► get_tests → run_tests                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Regras de ativação

| Situação | Tool(s) | Justificativa |
|----------|---------|---------------|
| Usuário menciona arquivo | `get_file` direto | Evita buscas desnecessárias |
| Precisa rastrear dependências | `find_symbol` (refs/impl) | Resultado autoritativo do compilador |
| Busca por conceito ("autenticação", "retry") | `code_search` | Semântica > texto literal |
| Primeiro contato com workspace | `get_solution_structure` → `get_project_files` | Entender camadas antes de agir |
| Pós-edição, arquivo individual | `get_errors` | Validação rápida antes do build completo |
| Pós-edição, finalização | `run_build` | Garantia de integridade total |
| Envolve Azure | `get_best_practices` **antes** de gerar código | Compliance desde o início |

---

## 3) Formato Ideal de Entrada e Saída

### Entrada (Request)

```json
{
  "tool": "find_symbol",
  "parameters": {
    "filepath": "src/Services/DnsService.cs",
    "symbolName": "ResolveAsync",
    "lineText": "public async Task<DnsResult> ResolveAsync(string domain)",
    "navigationType": 2
  }
}
```

Comentário no exemplo original: `navigationType`: 1 = Definition, 2 = References, 3 = Implementation.

**Princípios:**

- Tipos primitivos para escalares (`string`, `int`, `bool`)
- JSON para arrays e objetos
- Enums numéricos com documentação inline
- Campos `required` explícitos no schema
- Evitar parâmetros opcionais sem default documentado

### Saída (Response)

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "file": "src/Workers/BlockerWorker.cs",
        "line": 47,
        "snippet": "var result = await _dnsService.ResolveAsync(domain);"
      }
    ],
    "totalCount": 3,
    "truncated": false
  },
  "hints": {
    "suggestNext": ["get_file"],
    "relatedSymbols": ["DnsResult", "IDnsService"]
  }
}
```

**Princípios:**

- Resultado estruturado (não texto livre para tools de navegação)
- Truncamento explícito com flag (`truncated: true`)
- Hints para o agente encadear tools
- Limite de tokens documentado por tool

---

## 4) Como Evitar Excesso de Contexto

### Estratégia: funil progressivo

| Nível | Ferramentas | Custo aproximado |
|-------|-------------|------------------|
| 1 — Estrutura | `get_solution_structure` → nomes de projetos; `get_project_files` → nomes de arquivos | ~200 tokens |
| 2 — Localização | `find_symbol` → linhas específicas; `code_search` → chunks relevantes (max 4) | ~500–1000 tokens |
| 3 — Leitura cirúrgica | `get_file(startLine, endLine)` → apenas o trecho necessário | proporcional ao range |
| 4 — Leitura completa | arquivo inteiro apenas quando absolutamente necessário | — |

### Anti-padrões

| Anti-padrão | Problema | Solução |
|-------------|----------|---------|
| Ler arquivo inteiro sempre | Estoura janela de contexto | `get_file` com range de linhas |
| Buscar "tudo sobre X" | Retorna ruído | Queries específicas e sequenciais |
| `code_search` paralelo | Resultados redundantes | Uma busca por vez, refinar |
| Ler arquivos já no contexto | Desperdício de tokens | Verificar antes de chamar |
| Adivinhar paths sem estrutura | Paths inventados | Sempre `get_solution` → `get_project_files` primeiro |

### Técnicas de controle

1. **Budget de contexto por tool**: cada tool declara `maxTokens` no schema
2. **Deduplicação**: o orchestrator descarta resultados já presentes no contexto
3. **Relevance scoring**: `code_search` retorna score; agente ignora abaixo do threshold
4. **Lazy loading**: hints sugerem próximas tools, mas não carregam automaticamente

---

## 5) Estratégia de Composição Entre Tools

### Padrão: pipeline com gates

```
                ┌─────────────┐
                │  DISCOVER   │  get_solution + get_project_files
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │   LOCATE    │  find_symbol / code_search
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │    READ     │  get_file (ranges específicos)
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │   MUTATE    │  replace / create / remove
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │  VALIDATE   │  get_errors → run_build → run_tests
                └─────────────┘
```

### Regras de composição

| Regra | Descrição |
|-------|-----------|
| Independência paralela | Tools sem dependência entre si executam em paralelo |
| Gate de validação | Não pular `run_build` após mutação |
| Fallback | Se `find_symbol` não acha, fallback para `code_search` |
| Retry com refinamento | Se `replace_in_file` falha, `get_file` para re-ler e corrigir |
| Composição declarativa | Tools retornam hints sobre próximas tools recomendadas |

### Exemplo de composição real

**Pedido:** "Adicione retry com Polly no DnsService"

1. **[Paralelo]** `get_best_practices(intent="retry pattern .NET")` e `find_symbol("DnsService", navigationType=1)` (definição)
2. `get_file("src/Services/DnsService.cs", 1, 50)` — ler classe
3. **[Paralelo]** `find_symbol("HttpClient", navigationType=2)` (refs) e `get_file("src/DnsBlocker.csproj", 1, 30)` — verificar se Polly existe
4. `multi_replace([...])` — aplicar mudanças (ex.: pacote Polly + política de retry)
5. `run_build()` — validar
6. `get_tests(project="DnsBlocker.Tests")` → `run_tests` — testar

---

## Arquiteturas propostas

### Arquitetura mínima (MVP)

Para times de 1–5 devs, projetos com 1–3 soluções.

- **Transporte:** STDIO
- **Auth:** nenhuma (local)
- **Estado:** stateless

**Tools (6):** `get_file`, `create_file`, `replace_in_file`, `find_symbol`, `code_search`, `run_build`

**Stack sugerida:** .NET Worker Service + `Microsoft.Extensions.AI` + Roslyn Analyzer APIs

### Arquitetura intermediária

Para times de 5–20 devs, múltiplas soluções, CI/CD integrado.

- **Gateway** com rate limiting e auth (Entra ID / API Key)
- **Transporte:** HTTP + SSE
- **Cache:** IDistributedCache (Redis) para `find_symbol` e `get_solution_structure`
- **Observabilidade:** OpenTelemetry → Application Insights
- **Servidor Azure** dedicado para operações de infra

### Arquitetura avançada

Para organizações enterprise, centenas de devs, governança obrigatória.

- **API Management / APIM** com auth Entra ID + RBAC por tool
- **MCP Orchestrator (stateful):** Context Manager (budget, dedup, TTL), Pipeline Engine (gates, retry, fan-out), Tool Registry (dynamic discovery, health, version, feature flags)
- **Tool servers** independentes e escaláveis: workspace, Roslyn/analysis, CI/CD, Azure ops, security scanner, database migrator, custom domain tools
- **Camada transversal:** OpenTelemetry, audit log (compliance), Redis cache, policy engine (bloqueio por ambiente), cost tracker por time/projeto

**Diferenciais:** registry dinâmico, RBAC por tool, pipeline declarativa, audit completo, feature flags por projeto/ambiente.

---

## Tabela consolidada

| Tool | Objetivo | Valor | Risco | Prioridade |
|------|----------|-------|-------|------------|
| `get_file` | Leitura cirúrgica de código | Alto — base de toda operação | Baixo — read-only | P0 |
| `find_symbol` | Navegação via compilador (def/refs/impl) | Alto — precisão autoritativa | Baixo — read-only | P0 |
| `replace_in_file` | Edição precisa com contexto | Alto — mutação controlada | Médio — pode corromper se mal usado | P0 |
| `run_build` | Validação de integridade | Alto — gate obrigatório | Baixo — read-only | P0 |
| `code_search` | Busca semântica por conceitos | Alto — descobre o desconhecido | Médio — pode retornar ruído | P0 |
| `get_solution_structure` | Mapeamento de projetos/camadas | Alto — evita paths inventados | Baixo — read-only | P0 |
| `create_file` | Criação de novos arquivos | Médio — necessário para features novas | Médio — pode duplicar | P1 |
| `run_tests` | Execução de testes filtrados | Alto — valida comportamento | Médio — pode ser lento | P1 |
| `get_tests` | Descoberta de testes existentes | Médio — informa antes de executar | Baixo — read-only | P1 |
| `get_errors` | Erros por arquivo (pré-build) | Médio — feedback rápido | Baixo — read-only | P1 |
| `multi_replace` | Batch de edições atômicas | Médio — eficiência em refactors | Médio — complexidade de rollback | P1 |
| `get_best_practices` | Boas práticas Azure/AI | Médio — compliance desde design | Baixo — consultivo | P1 |
| `remove_file` | Remoção com limpeza de refs | Médio — limpeza de código morto | Alto — irreversível | P2 |
| `run_terminal` | Execução de comandos arbitrários | Médio — último recurso | Alto — execução arbitrária | P2 |
| `generate_cli_command` | Gera `az` CLI de intenção | Médio — acelera operações Azure | Médio — pode gerar comando errado | P2 |
| `resource_graph_query` | Consulta recursos Azure | Médio — visibilidade de infra | Médio — custo de API | P2 |
| `security_scanner` | SAST, secrets, deps vulneráveis | Alto — segurança | Médio — falsos positivos | P2 |
| `db_migrator` | EF Core migrations e schema | Médio — automação de DB | Alto — altera schema | P3 |
| `custom_domain_tools` | Tools específicas por equipe | Médio — extensibilidade | Médio — manutenção | P3 |

---

### Resumo executivo

- **MVP:** 6 tools + STDIO + stateless — ordem de grandeza de **1 semana**
- **Intermediário:** vários servidores + HTTP/SSE + cache + telemetria — **1–2 meses**
- **Avançado:** orchestrator + registry + RBAC + audit — **3–6 meses**

Recomendação: começar pelo MVP, validar o fluxo Discover → Locate → Read → Mutate → Validate, e evoluir com a adoção.

## Extração rápida (preencher depois)

- **Ferramentas citadas:** file/símbolo/busca, mutação (`replace`, `multi_replace`, `create`, `remove`), validação (`get_errors`, `run_build`, `get_tests`, `run_tests`), infra (`run_terminal`, `get_best_practices`, `generate_cli_command`); arquiteturas MVP / gateway+servidores / orchestrator enterprise
- **Limitações mencionadas:** risco de ruído em `code_search`; mutações e terminal com risco operacional; custo/latência de APIs Azure
- **Insights para MCP / extensões:** funil progressivo + budget de tokens; hints na resposta para encadear tools; gates pós-mutação (`run_build`); RBAC e auditoria em cenários enterprise
- **Follow-up sugerido (próximo prompt):** detalhar schema OpenAPI/JSON Schema por tool; ou POC Roslyn + STDIO para uma solution de referência
