# Corpus Query Expansion Map

Mapa modular de expansão de query para o corpus de instructions.  
Cada arquivo YAML cobre um domínio semântico do corpus ativo.

## Convenções de nomenclatura

| Prefixo | Domínio |
|---------|---------|
| `00-core.yml` | Termos transversais (sem domínio específico) |
| `10-dotnet.yml` | .NET, C#, runtime |
| `20-api.yml` | REST, HTTP, contratos de API |
| `30-data.yml` | Persistência, SQL, repositórios |
| `40-messaging.yml` | Mensageria, filas, eventos |
| `50-observability.yml` | Telemetria, health, logs |
| `60-security.yml` | Autenticação, autorização, segredos |
| `70-architecture.yml` | Arquitetura, camadas, padrões |
| `80-governance.yml` | Governança, conformidade, planejamento |
| `90-project-specific.yml` | Termos específicos deste corpus |

## Campos obrigatórios por arquivo

```yaml
version: 1
namespace: <nome-do-dominio>
terms:
  <termo-canonico>:
    aliases: []        # termos equivalentes
    strong_terms: []   # termos fortemente relacionados
    weak_terms: []     # termos periféricos
```

## Campos opcionais por termo

- `applies_to` — lista opcional de globs genéricos (extensão / padrões de artefato, ex.: `**/*.cs`); filtro de precisão quando `current_file_path` existe na busca; ignorado quando não existe — ver ADR-002 §2.1.
- `expansion_mode: contextual` — uso de `contexts` para contenção quando o mesmo canónico desdobra-se por tecnologia/protocolo.
- `contexts:` — mapa nomeado por contexto; dentro de cada contexto usar `activation_terms` (opcional), `applies_to` (opcional) e `terms` (lista associada quando o contexto é activado). Não usar `when_path_matches` — não faz parte do schema.
- `override: true` + `override_reason: "..."` — substitui definição de outro arquivo

## Regras

- Arquivo vazio ou ausente desabilita a expansão (nunca falha o MCP).
- Termo duplicado em dois arquivos sem `override` invalida o mapa inteiro.
- Loader ordena arquivos pelo nome antes de carregar (ordem determinística).
- Aceita `.yml` e `.yaml`.
