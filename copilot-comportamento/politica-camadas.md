# Política: camadas (nativo vs MCP)

Resumo alinhado ao épico de inventário. Detalhe e critérios: [`../planning/bmad/EPIC-01-inventory-governance.md`](../planning/bmad/EPIC-01-inventory-governance.md).

## Onde vive cada tipo de conhecimento

| Tipo | Onde vive | Exemplos |
|------|-----------|----------|
| Regra sempre ativa | `.github/instructions/` ou `copilot-instructions.md` no repo do serviço | idioma, segurança, limites do repo, 5–15 temas |
| Referência on-demand | Repositório canónico + MCP (`search_instructions`, `get_instruction`) | padrões de API, ADRs, exemplos por domínio |

## Precedência em conflito

1. Instructions **nativas** do repositório em que se trabalha.
2. Conteúdo **MCP** como orientação; se contrariar a nativa, perde.

## Fluxo sugerido com MCP

Antes de desenho ou refatoração grande, usar `search_instructions` com query clara; usar `get_instruction` com o `id` quando precisares do texto completo.
