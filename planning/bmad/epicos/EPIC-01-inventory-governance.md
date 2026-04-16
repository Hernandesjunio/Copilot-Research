# EPIC-01 — Inventário e governança do corpus de instructions

## Objetivo

Reduzir duplicação em 100+ repositórios mantendo **uma fonte da verdade** para o conhecimento arquitetural, com regras claras sobre o que permanece em `.github` (nativo) versus o que é recuperado via MCP.

## Critérios de classificação

| Tipo | Definição | Onde vive |
|------|-----------|-----------|
| **Regra sempre-ativa** | Deve influenciar **toda** interação (idioma, segurança, estilo, boundaries do repo). | `.github/instructions/` ou `copilot-instructions.md` (mínimo, 5–15 temas) |
| **Referência on-demand** | Volumosa, condicional à tarefa, exemplos por domínio, ADRs, catálogos. | Repositório canônico + MCP (`search_instructions` / `get_instructions_batch`) |

## Hierarquia em caso de conflito

1. **Instructions nativas** do repositório atual têm precedência (“lei”).
2. **Conteúdo do MCP** é orientação; se contradizer a nativa, a nativa vence.
3. O servidor MCP deve poder marcar documentos como `kind: reference` para deixar explícito que não substituem políticas locais.

## Frontmatter obrigatório (repositório canônico)

Cada arquivo `.md` do corpus deve começar por:

```yaml
---
id: unique-kebab-id
title: "Título legível"
tags: [tag1, tag2]
scope: "glob/ou/caminho/** opcional"
priority: low | medium | high
kind: reference | policy
---
```

| Campo | Obrigatório | Notas |
|-------|-------------|--------|
| `id` | Sim | Estável; usado em `get_instructions_batch`. |
| `title` | Sim | Aparece no índice e em resultados de busca. |
| `tags` | Recomendado | Filtragem em `search_instructions`. |
| `scope` | Opcional | Documentação de aplicação; pode espelhar `applyTo` mental. |
| `priority` | Opcional | Desempate na ordenação de resultados. |
| `kind` | Opcional | `policy` se for norma organizacional; `reference` (default) para guias. |

Se `id` estiver ausente, o MCP deriva um id a partir do nome do arquivo (avisar na pipeline de qualidade).

## Inventário (template)

Use uma planilha ou tabela Git com colunas:

| path | id | classificação (regra / referência) | ação (manter nativo / só MCP / dividir) | owner | notas |
|------|----|------------------------------------|----------------------------------------|-------|-------|

**Aceite deste épico:** política acordada + lista priorizada dos 5–15 temas que **cada** repo mantém em nativo + corpus canônico com frontmatter nos arquivos novos ou migrados.

## Próximo passo

Implementar o servidor MCP ([`mcp-instructions-server`](../../../mcp-instructions-server/README.md)) apontando `INSTRUCTIONS_ROOT` para o clone do repositório canônico.
