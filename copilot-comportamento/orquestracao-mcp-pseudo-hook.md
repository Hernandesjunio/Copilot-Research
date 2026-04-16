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

Pode ser útil citar `search_instructions` e `get_instructions_batch` no thin por serem o “caminho feliz” do servidor atual. Evite citar tools não existentes ou experimentais.

### Descriptions das tools (“quando usar”)

No mesmo experimento **2026-04-05** (secção “Insight: descriptions das tools” em [`2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`](../research/experimentos-mcp/2026-04-05-mcp-corporate-instructions-avaliacao-tools/2026-04-05-mcp-corporate-instructions-avaliacao-tools.md)), a pesquisa regista que descrições **imperativas sobre o momento de uso** (“Use when…”) orientam melhor a seleção de tools do que texto que só descreve o retorno.

Quem mantiver o servidor deve alinhar descrições ao README canónico; o thin não substitui isso, mas pode apontar o fluxo (descoberta → busca → leitura em lote).

### Protocolo de descoberta (observado na pesquisa, não prescrição rígida)

Na segunda iteração do vertical slice **2026-04-16** ([`analise-comparativa-iteracao-2.md`](../research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-2.md)), o cenário MCP melhorou aderência após reforços documentados: **`list_instructions_index` antes das buscas**, **várias** chamadas a `search_instructions` por tema, e **`get_instructions_batch`** para leitura em lote. O thin pode espelhar esse padrão em linguagem genérica (“descubra o índice, refine por tema, leia em lote”) sem amarrar a uma versão fixa de parâmetros de tool.

### Conflito: policy concreta (corpus/MCP) vs meta-instrução abstrata (thin)

Ainda em **2026-04-16** (iteração 2, critério 4 e conclusão na mesma síntese), o registo indica que uma **policy normativa concreta** (ex.: cache) pode prevalecer sobre uma meta-instrução de **conservadorismo** (“alinhar ao código existente”) — a meta não basta, por si só, para impedir implementação alinhada à policy.

Implicação para governança: combinar (1) policies com critérios de aplicabilidade ao código, (2) checklists explícitos no thin, ou (3) evolução de tools de verificação, conforme planeado no `research/` (sugestões na própria síntese: ex. `check_applicability`, flag em policy).

## Fonte da verdade das tools

- **Canônico**: `mcp-instructions-server/README.md` (lista de tools disponíveis).
- **Thin por repo**: pode citar tools, mas deve permanecer alinhado com o README do servidor.

### Regra prática

Se o thin citar uma tool por nome, ela precisa existir e estar documentada em `mcp-instructions-server/README.md`.

## Prevenção de drift (check rápido)

- Ao mudar tools no servidor: atualizar `mcp-instructions-server/README.md` e validar se `templates/copilot-instructions.thin.md` continua correto.
- Ao copiar o template para um repo novo: validar as tools com uma query de fumo (ver checklist).

