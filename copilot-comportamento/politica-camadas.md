# Política: camadas (nativo vs MCP)

Resumo alinhado ao épico de inventário. Detalhe e critérios: [`../planning/bmad/epicos/EPIC-01-inventory-governance.md`](../planning/bmad/epicos/EPIC-01-inventory-governance.md).

## Onde vive cada tipo de conhecimento

| Tipo | Onde vive | Exemplos |
|------|-----------|----------|
| Regra sempre ativa | `.github/instructions/` ou `copilot-instructions.md` no repo do serviço | idioma, segurança, limites do repo, 5–15 temas |
| Referência on-demand | Repositório canônico + MCP (`search_instructions`, `get_instructions_batch`) | padrões de API, ADRs, exemplos por domínio |

## Precedência em conflito

1. Instructions **nativas** do repositório em que se trabalha.
2. Conteúdo **MCP** como orientação; se contrariar a nativa, perde.

## Fluxo sugerido com MCP

Antes de um design ou refatoração grande, usar `search_instructions` com query clara; usar `get_instructions_batch` com os `id` relevantes para leitura completa.

## Falha ou ausência do MCP (comportamento esperado)

Na análise consolidada **2026-04-12** ([`artefatos/analise-comparativa.md`](../research/experimentos-mcp/2026-04-12-analise-comparativa-instructions-mcp-baseline/artefatos/analise-comparativa.md), riscos operacionais MCP STDIO), quando o **path do corpus**, o **ambiente Python** ou o **módulo** não estão disponíveis, o assistente tende a **degradar** para um modo equivalente ao **sem contexto normativo central** (analogia ao baseline C naquele desenho experimental).

Implicação prática: validar `INSTRUCTIONS_ROOT` e o arranque do servidor no onboarding do repo (ver [checklist](checklist-novo-repo.md)); não assumir MCP “sempre ligado” sem verificação.
