# Checklist — novo repositório de serviço

- Copiar/adaptar `[../templates/copilot-instructions.thin.md](../templates/copilot-instructions.thin.md)` para o local nativo acordado (ex. `.github/instructions/` ou raiz).
- Garantir 5–15 temas no nativo: contexto do serviço, idioma, segurança, limites, referência ao MCP.
- Configurar o cliente MCP (ex. `.mcp.json` / configurações do IDE) com o servidor **corporate-instructions** e `INSTRUCTIONS_ROOT` correto.
- Validar: `list_instructions_index`, `search_instructions` e `get_instructions_batch` com uma query de fumo.
- Se validar em **modo agente** (comandos de build/teste), conferir paths e artefactos reais do repo: no vertical slice **2026-04-16** ([`analise-comparativa-iteracao-1.md`](../research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-1.md)) registou-se **1 falha** de tool ligada a path de solução/projeto e **1 retry** no cenário MCP — erros operacionais do fluxo, não necessariamente do servidor MCP em si.
- Se o repo tiver trabalho longo/por fases, considerar adicionar a política de sessão do `[gestao-sessao-janela-contexto.md](gestao-sessao-janela-contexto.md)` no thin.
- Registrar no inventário (folha ou tabela) se a equipe mantiver um — ver EPIC-01.

