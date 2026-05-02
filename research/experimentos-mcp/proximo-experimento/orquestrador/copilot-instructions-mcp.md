# Instruções locais

- **Idioma:** português. **Segurança:** sem segredos/tokens/PII. **Escopo:** não assumas outros serviços.

## Repositório

- API de gestão de clientes, camadas. **Stack:** C#, .NET 8, ASP.NET Core.

## Padrões organizacionais (MCP `corporate-instructions`)

O catálogo normativo **não está** neste repo. **Este ficheiro prevalece** se houver conflito.

**Quando chamar o MCP:** trabalho **cross-cutting** (segurança, contratos API, resiliência, mensageria, dados, testes, observabilidade, estilo) ou dúvida se uma regra orgânica aplica — **antes** de desenhar ou impor o padrão.

### Tools (ordem habitual)

| Tool | Uso |
|------|-----|
| `list_instructions_index` | Ver **todos** os ids e metadados leves (título, tags) de uma vez; útil no início ou para confirmar que um id existe. |
| `search_instructions` | Achar candidatos por **pergunta em linguagem natural** (várias buscas, temas diferentes). Podes filtrar por **tags** (frontmatter do catálogo). |
| `get_instructions_batch` | Ler o **texto completo** de uma ou mais instructions de uma vez; passa **ids** em lista separada por vírgula. |

**Pesquisa** = palavras-chave (não exijas “entendimento profundo” numa única frase longa). **Resultados da busca** são atalhos; para aplicar regra, lê o corpo no batch.

### Exemplos

```
search_instructions(query="JWT bearer authorization")
search_instructions(query="outbox rabbitmq", max_results=15)
search_instructions(query="", tags="security,microservice")
get_instructions_batch(ids="microservice-auth-jwt-bearer-and-authorization,microservice-api-validation-and-error-contracts")
```

- **`max_results`:** omite (10) ou sobe até **20** se o tema for largo.
- Se faltar conteúdo ou truncar no batch, **repete** `get_instructions_batch` só para os ids que faltaram.

### Depois de obter as instructions

1. **Código primeiro:** o que já existe no repo = facto; o resto é hipótese até confirmares. O código prevalece sobre o catálogo se forem incompatíveis.
2. **Cita** o **`id`** da instruction (e ficheiros do repo) nas decisões relevantes.

## Fluxo

- Antes de mudar ficheiros sensíveis: lê o alvo. Depois de alterações grandes: build/testes.
