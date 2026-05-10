---
name: evolve-corpus-instruction
description: >-
  Padroniza instruction files do corpus (.md em fixtures/instructions/) e extrai
  entradas para o Corpus Query Expansion Map (YAML). Use quando o utilizador
  pedir para standardize, auditar, fixar ou evoluir instructions do corpus, ou
  quando pedir para gerar/actualizar entradas do query expansion map a partir do
  conteúdo de instructions.
disable-model-invocation: true
---

# Evolve Corpus Instruction

Duas operações, usadas em conjunto ou separadamente:

1. **Standardize** — auditar e corrigir um instruction file contra `instruction-authoring-standard.md`
2. **Extract expansion** — derivar entradas YAML para o Corpus Query Expansion Map a partir do conteúdo do instruction

---

## Operação 1: Standardize

### Fontes de autoridade (ler antes de auditar)

- `fixtures/instructions/instruction-authoring-standard.md`
- O ficheiro alvo

### Auditoria de frontmatter

**Campos obrigatórios** — presentes e não vazios:

| Campo | Regra |
|-------|-------|
| `id` | Corresponde ao nome do ficheiro sem `.md`; kebab-case; estável após publicação |
| `title` | Legível por humanos; máx ~80 chars |
| `tags` | Lista YAML; mínimo 2 tags substantivas de domínio; sem tags genéricas isoladas |
| `scope` | Glob string (ex.: `"**/*.cs"`); usar `"**/*.md"` para meta/governança |
| `priority` | `low` \| `medium` \| `high` |
| `kind` | `policy` \| `reference` |

**Campos recomendados** — adicionar se ausentes:

| Campo | Valor |
|-------|-------|
| `owner` | Equipa ou pessoa responsável |
| `last_reviewed` | Data ISO `YYYY-MM-DD` |
| `status` | `draft` \| `active` \| `deprecated` |

**Campos condicionais** — adicionar quando `kind: policy` E a instruction prescreve infra específica, bibliotecas, DI ou stacks concretos (Polly, HttpClientFactory, IOptions, OpenTelemetry, RabbitMQ, SQL/Dapper, IMemoryCache, etc.):

| Campo | Tipo | Regra |
|-------|------|-------|
| `workspace_evidence_required` | boolean | `true` quando o padrão exige adopção prévia |
| `workspace_signals` | lista | Nomes de classe/interface para grep (ex.: `[Polly, AddPolicyHandler]`) |
| `on_absence` | string | Usar `hypothesis_only` salvo política diferente da equipa |

Não adicionar estes campos para instructions contratuais ou de processo (HTTP semântica, validação, layering, BMAD, catálogo de erros).

### Auditoria de estrutura de secções

Para `kind: policy`, o ficheiro DEVE ter:

- `# Objetivo` — frase única
- `## TL;DR` — bullets accionáveis
- `## Pode ser feito` — lista de padrões permitidos
- `## Não pode ser feito` — lista de padrões proibidos

Recomendado (adicionar quando aplicável):

- `## Snippet` — exemplo de código curto e anónimo
- `## Tabela de decisão` ou secção de critérios (quando há ramos de comportamento)
- `## Anti-exemplos` — para políticas sensíveis a extrapolação

Para `kind: reference`, as secções são flexíveis; mínimo `# Objetivo` e `## TL;DR`.

### Aplicar correcções

Editar o ficheiro. Aplicar apenas alterações necessárias:

- Adicionar campos de frontmatter obrigatórios em falta (perguntar ao utilizador pelo `owner` se desconhecido)
- Adicionar `status: active` e `last_reviewed: <hoje>` se ausentes
- Adicionar secções estruturais em falta com placeholder e marcar com `<!-- TODO -->`
- **Nunca** alterar o `id` de um instruction já publicado
- **Nunca** remover conteúdo existente; apenas adicionar ou corrigir

### Relatório de alterações

Produzir um sumário conciso:

- Campos adicionados ao frontmatter
- Secções adicionadas ou corrigidas
- Campos intencionalmente deixados em branco (com razão)

---

## Operação 2: Extract Corpus Query Expansion Map

### Fontes de autoridade (ler antes de extrair)

- O ficheiro instruction alvo
- `fixtures/instructions/metadata/corpus-query-expansion-map/README.md`
- O ficheiro YAML de domínio provável (ver tabela de namespaces abaixo)

### Identificar termos canónicos

Extrair de:

- Lista `tags` do frontmatter (candidatos primários)
- Partes do slug `id` (dividir por `-`, descartar stop words: `microservice`, `and`, `or`, `and`)
- Nomes de biblioteca/classe/padrão no corpo (não prosa em linguagem natural)
- Substantivos dos bullets do TL;DR

**Termo canónico** = o termo mais estável e inequívoco. Preferir português se o corpus é PT-BR; usar o nome técnico inglês quando é o identificador principal no código (ex.: `polly`, `httpclientfactory`).

### Mapear relações

Para cada termo canónico, classificar termos relacionados:

| Relação | Regra |
|---------|-------|
| `aliases` | Sinónimos directos / mesmo conceito língua diferente (`resiliencia` ↔ `resilience`) |
| `strong_terms` | Fortemente acoplados; alta sobreposição de intenção de recuperação (ex.: `polly` → `retry`, `circuit-breaker`) |
| `weak_terms` | Vagamente relacionados; periféricos; ser conservador para não gerar ruído |

Usar o **corpo da instruction como evidência**: incluir apenas termos que aparecem no ficheiro ou que uma query razoável do utilizador produziria para encontrar este ficheiro.

### Determinar expansion_mode e contexts

- `expansion_mode: normal` — termo sem ambiguidade perigosa
- `expansion_mode: contextual` — termo polissémico ou específico de domínio (ex.: `mensageria` → termos RabbitMQ só quando `activation_terms` da query e/ou `applies_to` do contexto coincidem com o sinal disponível)

Adicionar bloco `contexts:` quando o termo deve expandir diferentemente por tecnologia ou tipo de artefato: `activation_terms` (vocabulário discriminante na query), `applies_to` opcional (globs genéricos por extensão/nome de ficheiro) e `terms`. Não usar `when_path_matches` nem globs de pasta de projeto — ver ADR-002 §2.1 e [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml).

### Atribuir ao ficheiro de namespace

| Prefixo | Namespace | Usar para |
|---------|-----------|-----------|
| `00-core.yml` | `core` | Termos transversais |
| `10-dotnet.yml` | `dotnet` | .NET runtime, C#, SDK |
| `20-api.yml` | `api` | REST, HTTP, contratos |
| `30-data.yml` | `data` | SQL, repositórios, ORM |
| `40-messaging.yml` | `messaging` | Filas, eventos, async |
| `50-observability.yml` | `observability` | Telemetria, health, logs |
| `60-security.yml` | `security` | Auth, authz, segredos |
| `70-architecture.yml` | `architecture` | Camadas, padrões, SOLID |
| `80-governance.yml` | `governance` | Meta, planeamento, processo |
| `90-project-specific.yml` | `project` | Termos específicos deste corpus |

Se um termo se enquadra em vários namespaces, atribuir ao mais específico. Termos transversais vão para `00-core.yml`.

### Output

Produzir um snippet YAML pronto para fusão no ficheiro alvo. Ver template em [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml).

Depois verificar se o termo já existe no YAML alvo:
- Se ausente → inserir o snippet sob `terms:`
- Se presente → mostrar diff e perguntar ao utilizador se faz merge ou salta

---

## Fluxo combinado (recomendado para evolução em massa)

Quando o utilizador quer evoluir múltiplos ficheiros:

```
Para cada instruction file:
  1. Standardize (Operação 1)
  2. Extract expansion (Operação 2)
  3. Confirmar alterações com o utilizador antes de aplicar ao YAML
```

Processar um ficheiro de cada vez; confirmar com o utilizador antes de escrever alterações no YAML do expansion map.

---

## Referências

- Padrão de autoria: `fixtures/instructions/instruction-authoring-standard.md`
- Convenções do expansion map: `fixtures/instructions/metadata/corpus-query-expansion-map/README.md`
- ADR que governa o expansion map: `planning/adr/ADR-002-corpus-query-expansion-map.md`
- Template de frontmatter: [templates/frontmatter-template.md](templates/frontmatter-template.md)
- Template de entrada de expansão: [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml)
