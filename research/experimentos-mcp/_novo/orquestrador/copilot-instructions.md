# copilot-instructions.md (neutro para experimento)

Este ficheiro deve ser mantido **mínimo** para não interferir no experimento.

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Não inventar**: sem evidência no código ou no guardrail ativo, rotule como **HIPÓTESE** e descreva como validar.

## Guardrail ativo (cenário)

Escolha **um** arquivo de cenário como fonte de regras do experimento e não use outros fora desse cenário:

- Baseline (sem MCP/sem instructions): `research/experimentos-mcp/_novo/orquestrador/copilot-instructions-baseline.md`
- Instructions locais: `research/experimentos-mcp/_novo/orquestrador/copilot-instructions-instructions-locais.md`
- MCP: `research/experimentos-mcp/_novo/orquestrador/copilot-instructions-mcp.md`

Se o arquivo de cenário não existir no projeto do experimento, declare **lacuna** e não substitua por política inventada.
