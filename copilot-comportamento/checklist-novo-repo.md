# Checklist — novo repositório de serviço

- [ ] Copiar/adaptar [`../templates/copilot-instructions.thin.md`](../templates/copilot-instructions.thin.md) para o local nativo acordado (ex. `.github/instructions/` ou raiz).
- [ ] Garantir 5–15 temas no nativo: contexto do serviço, idioma, segurança, limites, referência ao MCP.
- [ ] Configurar o cliente MCP (ex. `.mcp.json` / definições do IDE) com o servidor **corporate-instructions** e `INSTRUCTIONS_ROOT` correto.
- [ ] Validar: `list_instructions_index`, `search_instructions` e `get_instruction` com uma query de fumo.
- [ ] Registar no inventário (folha ou tabela) se a equipa mantiver um — ver EPIC-01.
