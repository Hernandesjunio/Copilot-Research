# Skill: Validate Analysis Findings

Use esta skill quando houver um documento com análise técnica prévia e for necessário validar se os **achados que exigem evidência no repositório** se sustentam no projeto (críticas, riscos, limitações declaradas, afirmações comparativas fortes, ou alegações de reprodutibilidade/setup — não só “pontos negativos” no sentido coloquial).

## Contexto `research/`

Navegação geral do repositório: [`AGENTS.md`](../../AGENTS.md). Se o documento estiver em `research/analises/` ou `research/experimentos-mcp/`, seguir o guia de citação em [`research/README.md`](../../research/README.md) (secção **“Como citar internamente”**: caminho, data, revisão quando existir). Em **sínteses comparativas** de experimentos, confrontar afirmações relevantes com a rubrica em [`research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md`](../../research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/criterios-de-comparacao.md) quando o texto depender dessa escala ou desses critérios.

## Processo

1. Ler o documento informado
2. Extrair os achados que precisam de âncora factual no repo (críticas, riscos, limitações, comparativos, claims de execução/protocolo, etc.)
3. Validar cada achado no projeto
4. Classificar:

   * Confirmado
   * Parcialmente confirmado
   * Não confirmado
   * Possível alucinação
5. Sugerir melhoria apenas para os achados sustentados

## Saída

Relatório em Markdown com:

* resumo executivo
* validação detalhada por achado
* lista de pontos fracos ou alucinatórios
* melhorias justificadas
