# Checklist — novo repositório de serviço

- Copiar/adaptar `[../templates/copilot-instructions.thin.md](../templates/copilot-instructions.thin.md)` para o local nativo acordado (ex. `.github/instructions/` ou raiz).
- Garantir 5–15 temas no nativo: contexto do serviço, idioma, segurança, limites, referência ao MCP.
- Configurar o cliente MCP (ex. `.mcp.json` / configurações do IDE) com o servidor **corporate-instructions** e `INSTRUCTIONS_ROOT` correto.
- Validar: `list_instructions_index`, `search_instructions` e `get_instructions_batch` com uma query de fumo.
- Se o repo tiver trabalho longo/por fases, considerar adicionar a política de sessão do `[gestao-sessao-janela-contexto.md](gestao-sessao-janela-contexto.md)` no thin.
- Registrar no inventário (folha ou tabela) se a equipe mantiver um — ver EPIC-01.

