# Frontmatter Template — Corpus Instruction

Copiar para o topo do ficheiro `.md` e preencher todos os campos assinalados com `# REQUIRED`.

```yaml
---
id: <kebab-case-igual-ao-nome-do-ficheiro>        # REQUIRED — estável após publicação
title: "<Título legível por humanos>"              # REQUIRED
tags: [dominio, subtema, tecnologia]               # REQUIRED — mínimo 2 tags substantivas
scope: "**/*.cs"                                   # REQUIRED — glob documental
priority: medium                                   # REQUIRED — low | medium | high
kind: policy                                       # REQUIRED — policy | reference
owner: platform-architecture                       # RECOMMENDED
last_reviewed: 2026-01-01                          # RECOMMENDED — atualizar a cada revisão
status: active                                     # RECOMMENDED — draft | active | deprecated

# Campos condicionais — APENAS para policies de infra/bibliotecas/DI/stack concreto
# workspace_evidence_required: true
# workspace_signals: [ClassName, InterfaceName]
# on_absence: hypothesis_only
---
```

## Regras de preenchimento

### `id`
- Deve corresponder **exactamente** ao nome do ficheiro sem `.md`
- Kebab-case: `microservice-resilience-polly-timeouts-and-circuit-breaker`
- Nunca alterar depois de publicado; mudança incompatível → novo `id` + deprecar o anterior

### `tags`
- Mínimo 2 tags, sendo pelo menos uma substantiva de domínio
- Evitar tags únicas e genéricas (`dotnet`, `code`) sem substantivo de domínio junto
- Exemplos bons: `[microservice, resilience, polly, httpclient, retry, circuit-breaker]`
- Exemplos maus: `[dotnet]`, `[code, patterns]`

### `scope`
- Glob que indica a que ficheiros do repositório esta instruction se aplica
- `"**/*.cs"` — código C# em geral
- `"**/Api/**/*.cs"` — apenas código na camada API
- `"**/*.md"` — para instructions de meta-governança ou processo

### `priority`
- `high` — norma crítica; violação é bloqueante
- `medium` — padrão preferido; desvio requer justificação
- `low` — recomendação; desvio é aceitável com contexto

### `kind`
- `policy` — norma mandatória; a IA não deve contradizer sem excepção aprovada
- `reference` — guia, contexto, padrões técnicos sem força de lei total

### Campos condicionais (workspace)

Adicionar **apenas** quando `kind: policy` E a instruction prescreve um destes padrões:
cache, mensageria, Polly, HttpClientFactory, OpenTelemetry, options/DI, configuração operacional, acesso a dados com stack concreta (Dapper, EF Core, etc.)

Não adicionar para:
- Instructions de contrato HTTP (status codes, validação, REST semântica)
- Layering e arquitectura sem dependência de biblioteca concreta
- Processo e governança (BMAD, planeamento, meta)
- Catálogo de erros

### `workspace_signals`
- Nomes de classe ou interface que o assistente pode grep no repositório
- Não duplicar o corpo da policy; apenas identificadores de código
- Exemplos: `[Polly, AddPolicyHandler, IAsyncPolicy]`, `[IMemoryCache, AddMemoryCache]`

## Mapa de expansão de query (ADR-002) — sem confundir com frontmatter

- `scope` aqui é **aplicabilidade documental** da instruction (que ficheiros do repositório ela descreve).
- O campo `applies_to` nos YAML em `metadata/corpus-query-expansion-map/` é **outro contrato**: globs genéricos para filtrar expansão de query quando `current_file_path` existe na busca; não substitui nem duplica `scope`.
- Curar entradas do mapa usa o conteúdo da instruction (frontmatter + corpo) como **evidência**; manter esses dois conceitos separados evita acoplamento desnecessário entre autoria `.md` e artefactos YAML do mapa.
