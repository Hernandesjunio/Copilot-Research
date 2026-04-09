## Objetivo

Padronizar como a equipe usa `copilot-instructions.md` / `.github/instructions` como **camada mínima** (“thin”) para **orquestrar** o uso do MCP (`corporate-instructions`) sem duplicar corpus no repositório do serviço.

## Princípios

- **Nativo é lei**: instructions nativas do repositório atual têm precedência. MCP é orientação.
- **Thin é orquestrador, não corpus**: manter 5–15 temas sempre ativos; regras longas ficam no corpus via MCP.
- **MCP é reativo**: sem hooks de “on_session_start” ou “on_file_open”; o thin funciona como “pseudo-hook” por ser injetado em toda interação.

## Estilo de orquestração (recomendado)

### Preferir orquestração genérica no thin

O thin deve dizer **quando** usar MCP (situações/temas), e não listar fluxos rígidos que quebram quando tools mudam.

Exemplos de bons gatilhos no thin:

- “Para padrões organizacionais (arquitetura, segurança, resiliência, etc.), consulte o MCP `corporate-instructions`.”
- “Antes de propor design/refatoração grande, faça uma busca no corpus.”
- “Se a tarefa depender de regra organizacional, **obrigatório** consultar MCP antes de implementar.”

### Quando vale ser explícito

Pode ser útil citar `search_instructions` e `get_instruction` no thin por serem o “caminho feliz” do servidor atual. Evite citar tools não existentes ou experimentais.

## Fonte da verdade das tools

- **Canônico**: `mcp-instructions-server/README.md` (lista de tools disponíveis).
- **Thin por repo**: pode citar tools, mas deve permanecer alinhado com o README do servidor.

### Regra prática

Se o thin citar uma tool por nome, ela precisa existir e estar documentada em `mcp-instructions-server/README.md`.

## Prevenção de drift (check rápido)

- Ao mudar tools no servidor: atualizar `mcp-instructions-server/README.md` e validar se `templates/copilot-instructions.thin.md` continua correto.
- Ao copiar o template para um repo novo: validar as tools com uma query de fumo (ver checklist).

