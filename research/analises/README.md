# Análises técnicas datadas

Índice das **análises técnicas** em Markdown sob `research/analises/`. Cada ficheiro segue o padrão `YYYY-MM-DD-slug.md`. Para metodologia geral da área de pesquisa, ver [`../README.md`](../README.md).

| Data | Documento | Descrição breve |
|------|-----------|-----------------|
| 2026-04-07 | [`2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md`](2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md) | Comparativo entre o template nativo “thin” versionado e uma variante de reestruturação; inconsistências I1–I7 e decisão de iterar até fonte canónica. |
| 2026-04-09 | [`2026-04-09-analise-tecnica-mcp-copilot.md`](2026-04-09-analise-tecnica-mcp-copilot.md) | Estratégias para substituir ou complementar `.github/instructions` com MCP no Copilot; cenários STDIO, HTTP e híbrido; tools vs resources vs prompts ao nível arquitetural. |
| 2026-04-09 | [`2026-04-09-distribuicao-central-cache-local-stdio.md`](2026-04-09-distribuicao-central-cache-local-stdio.md) | Modelo híbrido: corpus centralizado + cache/update “frio” e retrieval local “quente” via MCP em STDIO. |
| 2026-04-11 | [`2026-04-11-auditoria-tecnica-estrategia-copilot-mcp.md`](2026-04-11-auditoria-tecnica-estrategia-copilot-mcp.md) | Auditoria crítica da estratégia Copilot + MCP no repositório (cobertura, lacunas de validação, riscos). |
| 2026-04-12 | [`2026-04-12-analise-tecnica-mcp-tools-prompts-resources-corpus-instructions.md`](2026-04-12-analise-tecnica-mcp-tools-prompts-resources-corpus-instructions.md) | Por tool do servidor `corporate-instructions`: por que não é substituível 1:1 por prompt ou resource; híbridos e roadmap. |
| 2026-04-16 | [`2026-04-16-pitch-tecnico-mcp-stdio-contexto-github-instructions.md`](2026-04-16-pitch-tecnico-mcp-stdio-contexto-github-instructions.md) | Pitch curto (~5 min): MCP local STDIO, foco em tools, valor observado e limites do estágio atual. |
| 2026-04-16 | [`2026-04-16-defesa-arquitetural-mcp-stdio-tools-prompts-resources.md`](2026-04-16-defesa-arquitetural-mcp-stdio-tools-prompts-resources.md) | Defesa arquitetural alinhada ao pitch: premissas, escopo das tools, baseline, Q&A e evolução. |

Para citar: prefira **caminho + data** (e revisão, se existir no próprio artefato), conforme [`../README.md`](../README.md) secção 10.
