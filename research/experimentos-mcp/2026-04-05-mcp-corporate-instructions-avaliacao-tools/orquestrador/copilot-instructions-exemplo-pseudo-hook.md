# Copilot Instructions (exemplo — pseudo-hook orchestrator)

Exemplo mínimo documentado no relatório deste experimento: arquivo por repositório que orquestra **quando** chamar tools MCP, compensando a ausência de hooks proativos no IDE.

```markdown
# Copilot Instructions

## Contexto automático
- Este projeto é do tipo `api-microservice`.
- SEMPRE chame `get_project_profile("api-microservice")` antes de gerar ou modificar código.
- SEMPRE chame `resolve_instructions_for_file` com o path do arquivo sendo editado.
- Após gerar código, chame `validate_compliance` para verificar conformidade.
- Use `get_glossary` quando encontrar termos do domínio financeiro.
```

**Nota:** As tools `get_project_profile`, `resolve_instructions_for_file`, `validate_compliance` e `get_glossary` são **propostas** do relatório; na época do experimento o MCP expunha o ciclo descobrir → buscar → ler com as três tools base. Este ficheiro serve como modelo de orquestração quando essas extensões existirem.

Fonte: [`../2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`](../2026-04-05-mcp-corporate-instructions-avaliacao-tools.md) (secção workaround pseudo-hook).
