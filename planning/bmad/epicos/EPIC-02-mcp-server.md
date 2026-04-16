# EPIC-02 — Servidor MCP (MVP read-only)

## Entregável

Implementação em Python com **stdio**, tools (`list_instructions_index`, `search_instructions`, `get_instructions_batch`), índice em memória na inicialização e leitura de `INSTRUCTIONS_ROOT`.

## Documentação e código

- Código: [`mcp-instructions-server`](../../../mcp-instructions-server/)
- Configuração do VS: seção “Registrar no Visual Studio” no README do servidor.

## Aceite (checklist)

- [ ] `pip install -e .` com sucesso.
- [ ] Com `INSTRUCTIONS_ROOT` apontando para [`fixtures/instructions`](../../../fixtures/instructions), as tools devolvem JSON esperado.
- [ ] `pytest` (extra `dev`) passa em `tests/smoke_test.py`.
