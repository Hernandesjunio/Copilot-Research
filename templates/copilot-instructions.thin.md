# Instruções locais (camada mínima)

<!-- Ajuste ao repositório: idioma, segurança, limites do serviço. Mantenha curto (5–15 temas). -->

## Contexto do repositório

- Descreva em 2–3 linhas o propósito deste serviço e o stack relevante (ex.: .NET 8, ASP.NET Core).

## Regras sempre ativas

- Responda em **português** (ou o idioma acordado pela equipa).
- **Nunca** inclua segredos, tokens ou dados pessoais em exemplos ou commits.
- Respeite os limites deste repo: não assuma código de outros microserviços como disponível aqui.

## Padrões organizacionais (via MCP)

Para **padrões de arquitetura**, convenções partilhadas, exemplos de handlers, resiliência, segurança transversal ou ADRs da organização:

1. Chame o servidor MCP **corporate-instructions** (ou o nome que configurou).
2. Use **`search_instructions`** com uma query clara sobre o tópico **antes** de propor desenho ou refatoração grande.
3. Se precisar do texto completo, use **`get_instruction`** com o `id` devolvido na busca.

As regras **deste ficheiro** prevalecem se houver conflito com o catálogo MCP.

## Fluxo de trabalho sugerido

- Antes de editar ficheiros críticos, leia o ficheiro alvo (ou use as ferramentas do IDE).
- Após alterações substanciais, valide com build/testes do projeto.
