# copilot-instructions.md (neutro para experimento)

Este ficheiro deve ser mantido **mínimo** para não interferir no experimento.

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Não inventar**: sem evidência no código ou no guardrail ativo, rotule como **HIPÓTESE** e descreva como validar.

## Guardrail ativo (cenário)

Escolha **um** dos ficheiros no mesmo diretório `orquestrador/` como fonte de regras do experimento e não misture guardrails entre condições:

- **C (Baseline)** — sem MCP nem instructions locais: `copilot-instructions-baseline.md`
- **B (Instructions locais)** — `.github/instructions/`: `copilot-instructions-instructions-locais.md`
- **A (MCP)** — `corporate-instructions`: `copilot-instructions-mcp.md`

Se o guardrail escolhido não estiver disponível no projeto (por exemplo, pasta em falta), declare **lacuna** e não substitua por política inventada.
