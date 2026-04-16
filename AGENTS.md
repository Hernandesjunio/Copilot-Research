# Orientação para agentes (IA)

Entrada **curta** para navegar o repositório com poucos tokens. Detalhes narrativos e metodologia: [`README.md`](README.md) e, em pesquisa, [`research/README.md`](research/README.md).

## Fluxo do MVP (servidor MCP)

```
IDE (GitHub Copilot) —stdio JSON-RPC→ corporate_instructions_mcp —lê→ INSTRUCTIONS_ROOT (*.md com frontmatter)
```

Logs operacionais do servidor vão para **stderr**; **stdout** é só o protocolo MCP.

## Limites importantes

| Zona | Papel |
|------|--------|
| [`research/`](research/) | Análises, experimentos e metodologia — **não** é o corpus canónico servido pelo MCP. |
| [`fixtures/instructions/`](fixtures/instructions/) | Corpus de **exemplo** para desenvolvimento e testes locais do servidor. |
| `INSTRUCTIONS_ROOT` (ambiente) | Corpus real em produção — caminho configurado na instalação ([`mcp-instructions-server/README.md`](mcp-instructions-server/README.md)). |

## Mapa por tarefa

| Tarefa | Abrir primeiro |
|--------|------------------|
| Código Python do MCP, testes, CI | [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md), [`CONTRIBUTING.md`](CONTRIBUTING.md), [`mcp-instructions-server/docs/TESTS.md`](mcp-instructions-server/docs/TESTS.md) |
| Índice de análises (por data/tema) | [`research/analises/README.md`](research/analises/README.md) |
| Metodologia completa e citações | [`research/README.md`](research/README.md) |
| Experimentos MCP | [`research/experimentos-mcp/README.md`](research/experimentos-mcp/README.md) |
| Planejamento BMAD / épicos | [`planning/bmad/README.md`](planning/bmad/README.md) |
| Políticas de uso do Copilot | [`copilot-comportamento/README.md`](copilot-comportamento/README.md) |
| Template “thin” de instruções nativas | [`templates/copilot-instructions.thin.md`](templates/copilot-instructions.thin.md) |
| Prompts e respostas datadas | [`prompts/`](prompts/), [`responses/`](responses/) |
| Validar achados de análise externa | [`.cursor/rules/review-rules.md`](.cursor/rules/review-rules.md) |

## Tabela resumo (igual à raiz)

| Área | Caminho |
|------|---------|
| Políticas Copilot | [`copilot-comportamento/README.md`](copilot-comportamento/README.md) |
| Metodologia e pesquisa | [`research/README.md`](research/README.md) |
| Índice de análises | [`research/analises/README.md`](research/analises/README.md) |
| Servidor MCP | [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md) |
| Corpus de exemplo | [`fixtures/instructions/`](fixtures/instructions/) |

## Segurança e contribuição

- Ameaças e reporte: [`SECURITY.md`](SECURITY.md).
- PRs e ambiente de desenvolvimento: [`CONTRIBUTING.md`](CONTRIBUTING.md).
