---
id: instruction-authoring-standard
title: "Corpus — padrão de autoria de instructions"
tags: [governance, instructions, frontmatter, corpus, mcp]
scope: "**/*.md"
priority: medium
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Garantir que novas ou alteradas instructions no corpus canónico sejam **recuperáveis**, **normativamente claras** e **fáceis de manter**, alinhadas ao servidor MCP (`list_instructions_index`, `search_instructions`, `get_instruction`).

## TL;DR

- Todo ficheiro começa com **frontmatter YAML** mínimo alinhado ao [EPIC-01](../../planning/bmad/epicos/EPIC-01-inventory-governance.md): `id`, `title`, `tags`, `scope`, `priority`, `kind`.
- Políticas (`kind: policy`) devem incluir **tabela de decisão** ou critérios explícitos, secções **Pode ser feito** / **Não pode ser feito**, e preferencialmente **anti-exemplos**.
- Manter `id` estável após publicação; mudanças incompatíveis → novo `id` e deprecar o anterior no texto.
- Campos recomendados para governança: `owner`, `last_reviewed`, `status` (`draft` | `active` | `deprecated`).

## Valores de `kind`

| kind | Uso |
| --- | --- |
| `policy` | Norma mandatória; a IA não deve contradizer sem exceção aprovada. |
| `reference` | Guia, contexto, padrões técnicos sem força de lei total. |

Outros tipos (`adr`, `template`, `catalog`, `playbook`) podem ser introduzidos no frontmatter quando o índice e ferramentas suportarem; até lá, usar `reference` + `tags` descritivas.

## Estrutura mínima sugerida (Markdown)

1. **Objetivo** — uma frase.
2. **TL;DR** — bullets acionáveis.
3. **Tabela de decisão** ou **Critérios** — quando houver ramos de comportamento.
4. **Snippet** (opcional) — exemplo curto e anónimo.
5. **Pode ser feito** / **Não pode ser feito** — limites claros.
6. **Anti-exemplos** — para políticas sensíveis a extrapolação.
7. **Impacto esperado na resposta da IA** ou **Quando explicitar incerteza** — quando a instruction orienta assistentes.

## Pode ser feito

- Referenciar outras instructions por `id` em texto (“ver `microservice-rest-http-semantics-and-status-codes`”).
- Duplicar apenas o estritamente necessário; preferir um documento canónico e links.
- Usar `scope` como glob documental (ex.: `**/Api/**/*.cs`); ajustar por repositório quando o MCP apontar para outra raiz.

## Não pode ser feito

- Publicar `policy` sem qualquer critério verificável (só narrativa vaga).
- Reutilizar o mesmo `id` para um tema diferente do original.
- Colocar regras exclusivas de um produto ou entidade de negócio num documento destinado a multi-repo, salvo `scope` e `applies_to` deixarem isso explícito.

## Anti-exemplos

- Instruction de 500 linhas sem TL;DR nem secção de decisão — difícil de recuperar por busca por palavras-chave.
- Tags genéricas demais (`dotnet`, `code`) sem substantivos de domínio (`rest`, `validation`, `bmad`).
