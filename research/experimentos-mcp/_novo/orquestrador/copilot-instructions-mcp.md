# Instruções locais (camada mínima)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Limites**: se faltar dado decisivo, explicite a inferência e ofereça 2–3 opções.

## Contexto do repositório

- **Descrição:** API para gerenciamento de clientes, estruturada em arquitetura de camadas (API, Domínio, Interfaces, Modelos e Repositório).
- **Stack:** C#, .NET 8, ASP.NET Core

## Padrões organizacionais (via MCP)

Para arquitetura, convenções, resiliência, ADRs ou catálogo de erros:
use as tools do MCP `corporate-instructions`.

As regras **deste arquivo** prevalecem se houver conflito com o MCP.

## Como usar o MCP (para reduzir inferência)

1. Para descobrir políticas relevantes: use `search_instructions` com uma query descritiva.
2. Para ler o texto completo: use `get_instruction` com o `id` retornado.
3. Se precisar de múltiplas referências: selecione os `id` com `search_instructions` e leia apenas os necessários via `get_instruction` (evite carregar conteúdo irrelevante).
4. Sempre que a tarefa envolver design, tratamento de erros, validação, status codes, resiliência, cache, mensageria ou dúvida de convenção: faça `search_instructions` antes de decidir.

## Fluxo de trabalho

- Antes de editar arquivos críticos: leia o arquivo alvo.
- Após mudanças substanciais: rode build/testes.

