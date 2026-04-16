# Instruções locais (cenário: `.github/instructions`)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Não inventar**: sem evidência no código ou nas instructions locais, rotule como **HIPÓTESE** e descreva como validar.

## Fonte de guardrails (instructions locais)

- Use como fonte principal de padrões e políticas os ficheiros em `.github/instructions/`.
- Se o projeto do experimento não tiver `.github/instructions/`, declare **lacuna** e não substitua por políticas inventadas.

## Fluxo mínimo (para reduzir variação)

Use BMAD antes de codar:
- Background
- Mission
- Approach
- Delivery/validation

Se houver dúvida de convenção (status codes, validação, erros, resiliência, cache, mensageria), procure uma instruction específica e cite o ficheiro usado.
