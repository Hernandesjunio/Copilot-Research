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

## O que a pesquisa registrou (evidência)

No experimento [`research/experimentos-mcp/2026-04-05-mcp-corporate-instructions-avaliacao-tools/2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`](../research/experimentos-mcp/2026-04-05-mcp-corporate-instructions-avaliacao-tools/2026-04-05-mcp-corporate-instructions-avaliacao-tools.md) (Experimento 3):

- Foi observado comportamento **emergente**: durante um plano longo em fases, o assistente passou a reportar estimativas de uso da janela **entre fases**, associado no registo à presença de *Token Economy Pattern* no `copilot-instructions.md`, **sem** haver instrução explícita dedicada a esse relatório fase a fase.
- Na mesma secção, a tabela de abordagens contrapõe política qualitativa a **“sem instrução”** (custo zero, porém comportamento **inconsistente** / imprevisível).

Isto reforça: o thin deve ser **curto e estável**; evitar combinações de meta-instruções que induzam relatórios não desejados ou “percentuais” em toda mensagem.

## Texto enxuto para o thin (opcional)

Se for importante para o fluxo do time, adicionar ao `copilot-instructions.md` do repo:

> Ao concluir cada fase, informe uma estimativa de uso de contexto (low/medium/high). Se estiver high, recomende abrir uma nova thread e faça um resumo curto do estado atual.

