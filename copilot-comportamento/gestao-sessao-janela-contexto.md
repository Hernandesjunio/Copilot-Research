## Objetivo

Definir um padrão simples para **gestão de sessão** (especialmente em trabalhos longos) sem gastar tokens com “percentuais” artificiais.

## Política (recomendada)

- Usar **estimativa qualitativa por marcos**: `low` / `medium` / `high`.
- Reportar a estimativa **ao final de uma fase** (ou a cada entrega relevante), não em toda mensagem.
- Quando `high`, recomendar abrir uma **nova thread** e resumir:
  - objetivo
  - decisões
  - arquivos tocados
  - próximos passos

## Por que qualitativo

- O Copilot não expõe uma contagem interna confiável de tokens; “percentuais” são heurísticos e podem induzir falsa precisão.
- Meta-instruções muito longas sobre tokens consomem o próprio contexto (retorno decrescente).

## Texto enxuto para o thin (opcional)

Se for importante para o fluxo do time, adicionar ao `copilot-instructions.md` do repo:

> Ao concluir cada fase, informe uma estimativa de uso de contexto (low/medium/high). Se estiver high, recomende abrir uma nova thread e faça um resumo curto do estado atual.

