# Experimento: MCP corporate-instructions — avaliação e evolução de tools

- **Data:** 2026-04-05
- **Autor:** —
- **Objetivo:** Validar o servidor MCP `corporate-instructions` em um projeto .NET 8 real (ClientesAPI), com corpus em `fixtures/instructions`, e produzir uma avaliação sobre **tools adicionais** que melhorem a integração com o Copilot; além disso, documentar **impacto agêntico** das propostas, **métrica de janela de contexto** via `copilot-instructions.md`, e o padrão **pseudo-hook orchestrator**.

_Notas: o rascunho original indicava **Data: 2025** (ano) na metadata; o registro no repositório segue a convenção `YYYY-MM-DD`._

## Setup

### Ambiente e projeto

| Campo | Valor |
|---|---|
| **Ambiente** | Visual Studio Community 2026 (18.4.3) |
| **Target** | .NET 8 |
| **Projeto** | ClientesAPI (TestClientCorporateInstructions) |
| **Workspace Root** | `C:\Users\herna\source\repos\TestClientCorporateInstructions\` |
| **MCP Server** | `corporate-instructions` (Python, stdio) |
| **INSTRUCTIONS_ROOT** | `C:\_projeto\Copilot\fixtures\instructions` |

### Escopo deste registro

Foram documentados **3 experimentos** no mesmo contexto de pesquisa:

1. **Avaliação de tools** — gaps e 6 tools adicionais recomendadas.
2. **Análise de impacto agêntico** — se as melhorias tornam o Copilot “mais agêntico”.
3. **Métrica de janela de contexto** — se feedback de uso de contexto deve ir para `copilot-instructions.md`.

### Configuração MCP (exemplo)

```json
{
  "inputs": [],
  "servers": {
    "corporate-instructions": {
      "type": "stdio",
      "command": "python",
      "args": [ "-m", "corporate_instructions_mcp" ],
      "env": {
        "INSTRUCTIONS_ROOT": "C:\\_projeto\\Copilot\\fixtures\\instructions"
      }
    }
  }
}
```

### Tools MCP usadas neste experimento

- `list_instructions_index`, `search_instructions`, `get_instruction` (ciclo **descobrir → buscar → ler**).

---

## Procedimento

### Contexto

#### Problema original

Com mais de **100 microservices**, cada um em repositório separado, manter instruções padronizadas via `.github/copilot-instructions.md` individual tornou-se inviável. A replicação manual de regras arquiteturais, padrões de código e políticas de segurança entre repositórios gera:

- Inconsistência entre projetos
- Custo de manutenção alto
- Drift de padrões ao longo do tempo

#### Solução implementada

Foi construído um **MCP Server** (`corporate-instructions`) que centraliza instruções organizacionais em um diretório único (`INSTRUCTIONS_ROOT`) e as expõe ao Copilot via MCP (stdio). Cada instrução é um arquivo `.md` com frontmatter YAML.

### Tools existentes no MCP (referência)

O MCP já implementa 3 tools que cobrem o ciclo básico **descobrir → buscar → ler**:

#### `list_instructions_index`

- **Descrição**: Metadados leves (id, título, tags, scope, priority, kind, sha256) de todos os `.md` indexados.
- **Trigger do Copilot**: "Use when you need an overview of all available organizational instruction documents."
- **Retorno**: JSON array de objetos com metadados.

#### `search_instructions`

- **Descrição**: Busca full-text (keyword overlap) sobre o corpus.
- **Trigger do Copilot**: "Use when the user asks about architecture, patterns, DNS, security, style, or any org-specific guideline."
- **Parâmetros**: `query` (string), `tags` (filtro opcional), `max_results` (default 5, cap 10).
- **Retorno**: Resultados ordenados com relevância, score, resumo e trecho-chave.

#### `get_instruction`

- **Descrição**: Corpo markdown completo de uma instrução (após o frontmatter).
- **Trigger do Copilot**: "Use when search_instructions returned an id/path and you need the full instruction text."
- **Parâmetros**: `id` ou `path`, `max_chars` (default 12000).

### Corpus de instruções (momento da avaliação)

O index retornou **8 instruções**:

| ID | Título | Tags | Scope | Priority | Kind |
|---|---|---|---|---|---|
| `csharp-async-style` | Estilo C# — async e nomenclatura | csharp, style, async | `**/*.cs` | medium | reference |
| `dns-retry-pattern` | Padrão de retry para resolução DNS | dns, retry, resilience, polly | `src/**/Dns*/**` | high | reference |
| `security-baseline-secrets` | Linha de base — segredos e dados sensíveis | security, secrets, compliance | *(global)* | high | policy |
| `microservice-api-openfinance-patterns` | Microservice API — Open Finance, erros globais e docs | microservice, api, openfinance, minimal-api, xmldocs, error-handling | `**/Api/**/*.cs` | high | policy |
| `microservice-architecture-layering` | Microservice .NET — arquitetura por camadas | microservice, dotnet, architecture, layering, clean-architecture | `**/*.cs` | high | reference |
| `microservice-clean-architecture-guardrails` | Guardrails de Clean Architecture para microservices | microservice, clean-architecture, observability, resilience, security, testing | `**/*.cs` | high | policy |
| `microservice-di-options-extensions` | DI e configurações — Options e extension methods | microservice, dotnet, dependency-injection, ioptions, configuration | `**/*.cs` | medium | policy |
| `microservice-domain-interfaces-models-repository` | Dominio, Interfaces, Modelo e Repositorio — contrato e implementação | microservice, domain, interfaces, models, repository, dapper, table-storage | `**/*.cs` | high | reference |

#### Metadados por instrução (frontmatter)

- **id**, **title**, **tags**, **scope**, **priority** (`high` \| `medium` \| `low`), **kind** (`reference` \| `policy`), **content_sha256**.

### Experimento 1 — Pergunta e metodologia

> "Preciso de uma avaliação sua e preciso que haja como um especialista sênior no funcionamento do Copilot, e me fale se há mais alguma tool que precisa ser criada para que o Copilot possa melhorar ainda mais, pois como ele é código fechado eu não consigo fazer essa análise de forma fácil."

Metodologia:

1. Fluxo de raciocínio do Copilot (system prompt → tool selection → execution → response).
2. Gaps entre as 3 tools atuais e o que o Copilot precisa para decidir melhor.
3. Exploração de metadados existentes (scope, priority, tags, sha256).
4. Contexto de 100+ microservices com padrões compartilhados.

### Experimento 2 — Pergunta e definição de “agêntico”

> "Com todas essas melhorias eu conseguiria deixar o Copilot mais agêntico ou não?"

Para fins desta pesquisa, **agêntico** significa:

1. **Tomar decisões autónomas** sobre quais tools chamar e quando.
2. **Encadear ações** sem intervenção do usuário (tool chaining).
3. **Auto-corrigir** resultados via feedback loops (generate → evaluate → fix).
4. **Carregar contexto proativamente** antes de executar tarefas.

### Experimento 3 — Pergunta (janela de contexto)

> "Eu estava recebendo alguns feedbacks sobre o percentual de uso da janela de contexto para saber se poderia utilizar a janela atual ou se deveria abrir outra thread. Essa informação deveria ficar no copilot-instructions.md?"

Contexto adicional: durante a execução de um `implementation_plan.md` (12 fases, ~13h estimadas), o Copilot passou a reportar estimativas de uso da janela entre fases — comportamento **emergente**, induzido pelo termo "Token Economy Pattern" no `copilot-instructions.md`, não por instrução explícita.

---

## Resultado

### Impressão inicial (MCP + Copilot)

> "O resultado foi sensacional, muito além do que eu esperava, funcionou perfeitamente e com uma velocidade incrível."

O MCP funcionou de forma análoga às custom instructions nativas da pasta `.github/copilot`, com vantagem de ser **centralizado e compartilhado** entre repositórios.

### Seis tools adicionais recomendadas

#### `resolve_instructions_for_file(file_path)` — CRÍTICO

**Gap**: Cada instrução tem `scope` com globs; o Copilot precisa de `list_instructions_index` e matching mental — gasta tokens e erra.

**Solução**: Caminho de arquivo → instruções cujo `scope` faz match, ordenadas por `priority`.

```python
def resolve_instructions_for_file(file_path: str) -> list[InstructionMeta]:
    """Retorna instruções aplicáveis ao arquivo, ordenadas por priority (high > medium > low)."""
```

**Descrição sugerida para o Copilot**: `"Use when editing or creating a file to discover which organizational rules apply to it."`

**Esforço**: baixo (`fnmatch` / `pathlib`).

#### `get_project_profile(project_type)` — ALTO

**Gap**: Nem todos os microservices precisam do mesmo subset de regras.

**Solução**: Perfil pré-configurado com IDs aplicáveis por tipo de projeto.

```python
def get_project_profile(project_type: str) -> ProjectProfile:
    """
    project_type: 'api-microservice' | 'worker-service' | 'shared-library' | 'gateway'
    Retorna: lista de instruction IDs + configurações específicas do perfil.
    """
```

**Dados** (ex.: `profiles.yaml` em `INSTRUCTIONS_ROOT`):

```yaml
profiles:
  api-microservice:
    instructions:
      - microservice-architecture-layering
      - microservice-api-openfinance-patterns
      - microservice-clean-architecture-guardrails
      - microservice-di-options-extensions
      - microservice-domain-interfaces-models-repository
      - csharp-async-style
      - security-baseline-secrets
    dotnet_version: "8.0"

  worker-service:
    instructions:
      - microservice-architecture-layering
      - microservice-clean-architecture-guardrails
      - csharp-async-style
      - security-baseline-secrets
    dotnet_version: "8.0"
```

**Descrição sugerida**: `"Use at the start of a session or when the project type is mentioned to load the full instruction profile."`

**Esforço**: baixo (parse YAML).

#### `get_code_template(template_id, parameters?)` — ALTO

**Gap**: Instruções dizem o quê fazer, mas não entregam scaffold pronto.

**Solução**: Templates parametrizáveis alinhados às instruções.

```python
def get_code_template(
    template_id: str,  # 'repository-dapper', 'minimal-api-endpoint', 'options-class', 'global-error-handler'
    parameters: dict | None = None  # {'entity': 'Cliente', 'table': 'Clientes'}
) -> CodeTemplate:
    """Retorna template .cs com placeholders substituídos."""
```

**Exemplo** `repository-dapper.cs.template`:

```csharp
public class {{entity}}Repository : I{{entity}}Repository
{
    private readonly IDbConnection _connection;

    public {{entity}}Repository(IDbConnection connection)
        => _connection = connection;

    public async Task<{{entity}}?> ObterPorIdAsync(Guid id)
    {
        const string sql = "SELECT * FROM {{table}} WHERE Id = @Id";
        return await _connection.QueryFirstOrDefaultAsync<{{entity}}>(sql, new { Id = id });
    }
}
```

**Descrição sugerida**: `"Use when scaffolding new classes, endpoints, or patterns to get the organization-approved template."`

**Esforço**: médio (gestão de templates + substituição de placeholders).

#### `get_glossary(term?)` — MÉDIO-ALTO

**Gap**: Terminologia de domínio sem fonte autoritativa.

**Solução**: Glossário centralizado (ex.: `glossary.yaml`).

```python
def get_glossary(term: str | None = None) -> list[GlossaryEntry]:
    """
    Sem argumento: retorna todo o glossário.
    Com term: busca fuzzy.
    """
```

**Dados** (ex.: `glossary.yaml`):

```yaml
- term: "Open Finance"
  definition: "Ecossistema de compartilhamento de dados financeiros regulado pelo BCB"
  usage: "Sempre 'Open Finance', nunca 'Open Banking' em código novo"

- term: "Envelope de resposta"
  definition: "Wrapper padrão para responses da API seguindo spec Open Finance"
  usage: "Usar classe ResponseEnvelope<T> do namespace Modelo.Saida"

- term: "PCLD"
  definition: "Provisão para Créditos de Liquidação Duvidosa"
  usage: "Usar sempre a sigla PCLD em nomes de classe/variável"
```

**Descrição sugerida**: `"Use when encountering domain-specific terms, abbreviations, or when naming classes/variables to ensure consistent terminology."`
**Esforço**: baixo (YAML parse + fuzzy match simples).

#### `check_instruction_updates(since_sha256s?)` — MÉDIO

**Gap**: `content_sha256` existe, mas não há tool para diff face a estado conhecido.

**Solução**: Mapa `{id: sha256_anterior}` → added / changed / removed.

```python
def check_instruction_updates(
    known_hashes: dict[str, str] | None = None
) -> InstructionDiff:
    """
    Retorna: { added: [...], changed: [...], removed: [...] }
    Sem argumento: retorna todas como 'added' (útil para primeiro uso).
    """
```

**Descrição sugerida**: `"Use to check if any organizational instructions have been updated since last known state."`

**Esforço**: baixo (diff de hashes).

#### `validate_compliance(code_snippet, file_path?, instruction_ids?)` — MÉDIO

**Gap**: Pós-geração, sem verificação objetiva de conformidade.

**Solução**: Checagens baseadas em regras extraídas das instruções (regex, naming, estrutura).

```python
def validate_compliance(
    code_snippet: str,
    file_path: str | None = None,
    instruction_ids: list[str] | None = None
) -> list[ComplianceViolation]:
    """
    Retorna violações encontradas.
    Exemplo: {
        rule: 'async-suffix',
        instruction: 'csharp-async-style',
        message: 'Método GetCliente é async mas não termina em Async',
        line: 12,
        severity: 'warning'
    }
    """
```

**Descrição sugerida**: `"Use after generating or modifying code to verify compliance with organizational instructions."`

> **Nota:** A mais complexa de implementar. Começar com regras simples (naming, imports proibidos, regex) e evoluir incrementalmente — objetivo: *quick sanity check*, não um Roslyn Analyzer completo.

**Esforço**: alto (regex rules, parsing leve).

### Matriz de priorização

```
┌─────────────────────────────────────────┬──────────┬────────────────────┐
│ Tool                                    │ Impacto  │ Esforço            │
├─────────────────────────────────────────┼──────────┼────────────────────┤
│ 1. resolve_instructions_for_file        │ CRÍTICO  │ Baixo (glob match) │
│ 2. get_project_profile                  │ ALTO     │ Baixo (YAML parse) │
│ 3. get_code_template                    │ ALTO     │ Médio (templates)  │
│ 4. get_glossary                         │ MÉDIO+   │ Baixo (YAML parse) │
│ 5. check_instruction_updates            │ MÉDIO    │ Baixo (diff hash)  │
│ 6. validate_compliance                  │ MÉDIO    │ Alto (regex rules) │
└─────────────────────────────────────────┴──────────┴────────────────────┘
```

**Ordem sugerida:** Fase 1 → tools 1 e 2; Fase 2 → 3 e 4; Fase 3 → 5 e 6.

### Insight: descriptions das tools

As **descriptions** orientam **quando** o Copilot chama cada tool: preferir frases imperativas sobre o **momento** de uso, não só o que a tool retorna. As 3 tools existentes já seguem esse padrão.

**Exemplos:**

```
# Boa (descreve quando usar)
"Use when editing or creating a file to discover which organizational rules apply to it."

# Ruim (descreve o que faz, não quando usar)
"Returns instructions filtered by file path glob matching."
```

### Experimento 2 — Duas dimensões: eficiência agêntica vs proatividade autónoma

As tools propostas impactam o comportamento em **duas dimensões separadas**:

#### Dimensão 1: Eficiência agêntica (melhora significativamente)

Quando o Copilot **já está em modo Agent**, as tools reduzem round-trips e decisões internas:

| Fluxo atual (sem tools) | Fluxo proposto (com tools) |
|---|---|
| `list_index` → ler 8 scopes → decidir mentalmente quais aplicam → `get_instruction` × N | `resolve_instructions_for_file` → **1 call, contexto pronto** |
| Gerar código → "espero que esteja certo" | Gerar → `validate_compliance` → corrigir → **feedback loop** |
| Inferir estrutura de instrução textual | `get_code_template` → **scaffold correto de partida** |

O **feedback loop** de `validate_compliance` implementa **generate → evaluate → correct**. Hoje o Copilot gera e "confia"; com a tool, gera, valida e corrige de forma mais autónoma.

#### Dimensão 2: Proatividade autónoma (limitação arquitetural)

O Copilot **não tem hooks proativos**. Não pode, por si só:

- Ao abrir um arquivo, chamar automaticamente `resolve_instructions_for_file`.
- No início da sessão, chamar automaticamente `get_project_profile`.
- Periodicamente chamar `check_instruction_updates`.

O Copilot é **reativo** — a **inicialização** é sempre do usuário, mesmo em Agent mode.

**Limitações identificadas:**

| Limitação | Descrição |
|---|---|
| **Sem session start hooks** | Não existe `on_session_start`. |
| **Sem file change listeners** | Não existe `on_file_open`. |
| **Sem persistent state** | Não lembra dados entre sessões — `check_instruction_updates` perde hashes anteriores sem mecanismo externo. |
| **Sem background execution** | Não corre sem prompt explícito. |

#### Classificação por tool (Experimento 2)

```
┌────────────────────────────────┬─────────────┬──────────────┬──────────────────────┐
│ Tool                           │ Eficiência  │ Proatividade │ Padrão agêntico      │
│                                │ agêntica    │ autônoma     │                      │
├────────────────────────────────┼─────────────┼──────────────┼──────────────────────┤
│ resolve_instructions_for_file  │ ★★★★★       │ ★★☆☆☆        │ Context loading      │
│ get_project_profile            │ ★★★★☆       │ ★★☆☆☆        │ Session bootstrap    │
│ get_code_template              │ ★★★★☆       │ ★★★☆☆        │ Informed generation  │
│ get_glossary                   │ ★★★☆☆       │ ★★☆☆☆        │ Reference lookup     │
│ check_instruction_updates      │ ★★☆☆☆       │ ★☆☆☆☆        │ Staleness detection  │
│ validate_compliance            │ ★★★★★       │ ★★★★☆        │ Generate→Eval→Fix    │
└────────────────────────────────┴─────────────┴──────────────┴──────────────────────┘
```

**Síntese Experimento 2:** As tools fazem o Copilot **agir melhor quando age**, mas não fazem **agir sozinho** sem prompt — a limitação é arquitetural.

### Workaround — `copilot-instructions.md` como pseudo-hook orchestrator

O `.github/copilot-instructions.md` é injetado no **system prompt** de cada interação — o **único mecanismo de “pró-atividade”** disponível na arquitetura atual, funcionando como pseudo-hook de inicialização.

**Padrão recomendado** (arquivo mínimo por repo que orquestra o MCP):

```markdown
# Copilot Instructions

## Contexto automático
- Este projeto é do tipo `api-microservice`.
- SEMPRE chame `get_project_profile("api-microservice")` antes de gerar ou modificar código.
- SEMPRE chame `resolve_instructions_for_file` com o path do arquivo sendo editado.
- Após gerar código, chame `validate_compliance` para verificar conformidade.
- Use `get_glossary` quando encontrar termos do domínio financeiro.
```

**Custo de manutenção:**

| Aspecto | Sem workaround | Com workaround |
|---|---|---|
| **Conteúdo no repo** | Muitas instruções replicadas × N repos | ~10 linhas × N repos |
| **Atualização de regras** | Editar muitos repos | Editar `INSTRUCTIONS_ROOT` central |
| **Consistência** | Drift provável | Centralizada pelo MCP |
| **Tipo de projeto** | Mesmas regras para todos | Perfis (`api-microservice`, `worker-service`, …) |

**Fluxo resultante (conceitual):** usuário envia prompt → system prompt inclui `copilot-instructions.md` → Copilot chama tools conforme orquestrado → gera/modifica código → opcionalmente `validate_compliance` e correção.

### Experimento 3 — Métrica de janela de contexto

#### Como o Copilot “estima” contexto

O Copilot **não expõe API interna** de contagem de tokens. Qualquer “percentual” é **heurística** (comprimento acumulado da conversa), **direcional, não exata**.

**Paradoxo:** instruções sobre gestão de contexto **também consomem** contexto — há retorno decrescente.

**Sem persistência explícita:** a estimativa recomeça por turno com base no que está visível (system prompt + histórico).

#### Decisão: abordagem qualitativa

| Abordagem | Custo por resposta | Precisão | Risco |
|---|---|---|---|
| Percentual exato a cada mensagem | Alto | Falsa precisão (heurística) | Gasto de tokens em todo turno |
| **Qualitativa por fase (low/medium/high)** | Baixo | Direcional suficiente | Mínimo — marcos de fase |
| Sem instrução | Zero | Inconsistente | Comportamento emergente imprevisível |

**Instrução implementada (exemplo):**

```markdown
- Context window monitoring: After completing each phase, provide a brief context usage estimate (low/medium/high). When high (~70%+), recommend opening a new thread. Prefer qualitative estimates over exact percentages.
```

#### Onde colocar

| Opção | Veredicto | Justificativa |
|---|---|---|
| `copilot-instructions.md` (per-repo) | Escolhido | Extensão natural do Token Economy Pattern; meta-instrução sobre comportamento do Copilot |
| Instrução corporativa via MCP | Futuro | Possível `kind: meta`; hoje desalinhado com o corpus (arquitetura, padrões, segurança) |
| Ambos | Descartado | Overhead duplo desnecessário neste momento |

**Implicação:** o pseudo-hook não orquestra só **quais tools chamar**, mas também **como gerir a sessão** (incluindo marcos de contexto).

### Arquivos do workspace no momento dos experimentos

```
C:\Users\herna\source\repos\TestClientCorporateInstructions\
├── .github\
│   └── copilot-instructions.md
├── .mcp.json
├── RESEARCH_MCP_CORPORATE_INSTRUCTIONS.md
├── ClientesAPI.Api\
│   ├── appsettings.json
│   ├── Program.cs
│   └── Endpoints\
│       └── ClienteEndpoints.cs
├── ClientesAPI.Repositorio\
│   └── ClienteRepositorioDapper.cs
├── ClientesAPI.Modelo\
│   └── ClienteResposta.cs
└── ClientesAPI.Dominio\
    └── Entidades\
        └── Cliente.cs
```

(Versão resumida referida no primeiro ciclo de notas:)

```
ClientesAPI.Api\appsettings.json
ClientesAPI.Api\Program.cs
ClientesAPI.Api\Endpoints\ClienteEndpoints.cs
ClientesAPI.Repositorio\ClienteRepositorioDapper.cs
ClientesAPI.Modelo\ClienteResposta.cs
ClientesAPI.Dominio\Entidades\Cliente.cs
.mcp.json
.github\copilot-instructions.md
```

### Stack de extensibilidade (síntese visual)

```
┌─────────────────────────────────────────────────────────────────┐
│                 STACK DE EXTENSIBILIDADE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  .github/copilot-instructions.md (por repo)            │   │
│  │  → Pseudo-hook: orquestra QUAIS tools chamar           │   │
│  │  → Gestão de sessão (context window, marcos)           │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐   │
│  │  MCP Server corporate-instructions (centralizado)      │   │
│  │  → 3 tools base + 6 tools propostas                    │   │
│  │  → INSTRUCTIONS_ROOT com 8+ instruções .md             │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐   │
│  │  Corpus de Instruções (.md com frontmatter YAML)       │   │
│  │  → Regras, padrões, políticas, glossário, templates    │   │
│  │  → Versionado por SHA256, filtrado por scope/tags      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusões e próximos passos

- **Experimento 1 (tools):** O MCP centraliza bem instruções multi-repo. As 3 tools cobrem **descobrir → buscar → ler**; as 6 propostas reforçam auto-contexto por arquivo/projeto, scaffolding, glossário, detecção de mudanças e verificação leve de conformidade.
- **Experimento 2 (agêntico):** As propostas aumentam **eficiência e encadeamento** quando já há tarefa em curso; **proatividade verdadeira** continua limitada pela arquitetura (sem hooks, sem estado persistente). O **MCP + `copilot-instructions.md` como orchestrator** aproxima o máximo de comportamento agêntico extraível sem APIs internas do IDE.
- **Experimento 3 (janela de contexto):** Meta-instruções **qualitativas** em `copilot-instructions.md` (low/medium/high por fase) equilibram custo de tokens e utilidade; percentuais “exatos” tendem a **falsa precisão**. Localização escolhida: **per-repo** no `copilot-instructions.md`; MCP com `kind: meta` fica como evolução futura opcional.
- **Evolução do orchestrator (tool descriptions):** mover descrições estáticas das tools (o “o que faz / quando usar”) para um **resource versionado/snapshot** (ex.: `tools-catalog`), e manter no `copilot-instructions.md` apenas o fluxo de uso + referência ao resource. Para reprodutibilidade, registrar no output do experimento a versão/hash/data do resource consumido.
- **Alterações propostas ao corpus / template / servidor:** Roadmap por fases — `resolve_instructions_for_file` e `get_project_profile` primeiro; depois templates e glossário; por fim diff por hash e `validate_compliance` incremental. Ao adicionar tools, alinhar **descriptions** ao padrão “when to use”.
- **Decisão:** **Iterar** — adotar roadmap por fases; o design atual do MCP é viável e performático face às instructions nativas; o papel do orchestrator no repo foi validado como complemento essencial às limitações de hooks.


