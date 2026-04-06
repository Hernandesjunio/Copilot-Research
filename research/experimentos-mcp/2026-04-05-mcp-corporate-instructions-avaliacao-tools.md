# Experimento: MCP corporate-instructions — avaliação e evolução de tools

- **Data (registo):** 2026-04-05
- **Autor:** —
- **Objetivo:** Validar o servidor MCP `corporate-instructions` num projeto .NET 8 real (ClientesAPI), com corpus em `fixtures/instructions`, e produzir uma avaliação sobre **tools adicionais** que melhorem a integração com o Copilot.

_Notas: o rascunho original indicava **Data: 2025** (ano) na metadata; o registo no repositório segue a convenção `YYYY-MM-DD`._

## Setup

### Ambiente e projeto

| Campo | Valor |
|---|---|
| **Ambiente** | Visual Studio Community 2026 (18.4.3) |
| **Target** | .NET 8 |
| **Projeto** | ClientesAPI (TestClientCorporateInstructions) |
| **MCP Server** | `corporate-instructions` (Python, stdio) |
| **INSTRUCTIONS_ROOT** | `C:\_projeto\Copilot\fixtures\instructions` |

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

Foi construído um **MCP Server** (`corporate-instructions`) que centraliza instruções organizacionais num diretório único (`INSTRUCTIONS_ROOT`) e as expõe ao Copilot via MCP (stdio). Cada instrução é um ficheiro `.md` com frontmatter YAML.

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

### Pergunta colocada e metodologia

> "Preciso de uma avaliação sua e preciso que haja como um especialista sênior no funcionamento do Copilot, e me fale se há mais alguma tool que precisa ser criada para que o Copilot possa melhorar ainda mais, pois como ele é código fechado eu não consigo fazer essa análise de forma fácil."

Metodologia:

1. Fluxo de raciocínio do Copilot (system prompt → tool selection → execution → response).
2. Gaps entre as 3 tools atuais e o que o Copilot precisa para decidir melhor.
3. Exploração de metadados existentes (scope, priority, tags, sha256).
4. Contexto de 100+ microservices com padrões partilhados.

---

## Resultado

### Impressão inicial (MCP + Copilot)

> "O resultado foi sensacional, muito além do que eu esperava, funcionou perfeitamente e com uma velocidade incrível."

O MCP funcionou de forma análoga às custom instructions nativas da pasta `.github/copilot`, com vantagem de ser **centralizado e partilhado** entre repositórios.

### Seis tools adicionais recomendadas

#### `resolve_instructions_for_file(file_path)` — CRÍTICO

**Gap**: Cada instrução tem `scope` com globs; o Copilot precisa de `list_instructions_index` e matching mental — gasta tokens e erra.

**Solução**: Caminho de ficheiro → instruções cujo `scope` faz match, ordenadas por `priority`.

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

### Ficheiros do workspace no momento do experimento

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

---

## Conclusões e próximos passos

- **Síntese:** O MCP `corporate-instructions` centraliza bem instruções multi-repo. As 3 tools cobrem descoberta, busca e leitura; as 6 propostas reforçam auto-contexto por ficheiro/projeto, scaffolding, glossário, deteção de mudanças e verificação leve de conformidade.
- **Alterações propostas ao corpus / template / servidor:** Evoluir o servidor com prioridade a `resolve_instructions_for_file` e `get_project_profile`; depois templates e glossário; por fim diff por hash e `validate_compliance` incremental. Ao adicionar tools, alinhar **descriptions** ao padrão “when to use”.
- **Decisão:** **Iterar** — adotar roadmap por fases; o desenho atual do MCP é viável e performático face às instructions nativas.

---

*Adaptado de [`rascunho.md`](rascunho.md).*
