# Instruções locais (camada mínima)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Limites**: se faltar dado decisivo, explicite a inferência e ofereça 2–3 opções.

## Contexto do repositório

- **Descrição:** (descrição do projeto)
- **Stack:** (stack completa)

## Padrões organizacionais (via MCP)

Para padrões de arquitetura, convenções, segurança, resiliência, ADRs, exemplos de domínio ou catálogo de erros:

1. Use o MCP `corporate-instructions`.
2. Em qualquer tarefa que envolva design, implementação de padrões, tratamento de erros ou dúvida sobre convenções: `search_instructions` com query descritiva.
3. Para o texto completo: `get_instruction` com o `id` retornado.
4. Para tarefas cross-cutting que combinam múltiplas referências: `compose_context`.

As regras **deste arquivo** prevalecem se houver conflito com o MCP.

## Fluxo de trabalho

- Antes de editar arquivos críticos: leia o arquivo alvo.
- Após mudanças substanciais: rode build/testes.
