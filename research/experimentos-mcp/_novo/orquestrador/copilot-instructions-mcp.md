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

### Passo 1 — Descoberta do corpus (obrigatório antes de qualquer busca)

Use `list_instructions_index` para obter a lista completa de instructions disponíveis.
Analise os IDs, títulos e tags retornados para identificar **todas** as instructions potencialmente relevantes à tarefa — não dependa apenas da busca por keywords.

### Passo 2 — Busca direcionada por tema

Faça **múltiplas chamadas** de `search_instructions`, uma por tema da tarefa. Exemplos de queries separadas:
- semântica HTTP e status codes
- validação e contratos de erro
- persistência e acesso a dados
- cache e IMemoryCache
- testes e estratégia de validação
- arquitetura e separação de camadas
- resiliência e tolerância a falhas

Use `max_results: 10` para ampliar a cobertura de cada busca.

### Passo 3 — Leitura completa das instructions selecionadas

Para cada instruction relevante identificada nos passos 1 e 2, use `get_instruction` com o `id` retornado.
Leia **todas** as instructions que possam influenciar a tarefa — não se limite às 5 primeiras.

### Passo 4 — Cruzamento com o código real (conservadorismo)

Após ler as instructions MCP, **cruze cada recomendação com o estado real do repositório**:
- Se a instruction recomenda um padrão que o código **já usa**: aplique diretamente (FATO).
- Se a instruction recomenda um padrão que o código **não usa**: rotule como **HIPÓTESE**, avalie se a introdução cria inconsistência com o padrão vigente e justifique a decisão de adotar ou não.
- Prefira **não introduzir padrões novos** sem base concreta no código, mesmo que a policy MCP os recomende. Consistência com o código existente prevalece sobre completude normativa.

### Passo 5 — Rastreabilidade

Para cada decisão importante, cite:
- o `id` da instruction MCP usada;
- o(s) arquivo(s) do workspace que sustenta(m) a decisão;
- se a decisão diverge da policy MCP, justifique explicitamente.

## Fluxo de trabalho

- Antes de editar arquivos críticos: leia o arquivo alvo.
- Após mudanças substanciais: rode build/testes.

