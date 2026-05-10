---
name: experimento-mcp-prompt-protocolo
description: >-
  Monta prompts de experimento comparativo Copilot/MCP com relatório, métricas
  JSON e exportação consistentes. Use quando o utilizador correr ensaios em
  research/experimentos-mcp, pedir protocolo de EXPERIMENT_METRICS_JSON ou
  alinhar prompts entre cenários (baseline, instructions locais, MCP).
disable-model-invocation: true
---

# Experimento MCP — protocolo de prompt (fino)

## Fonte canónica

1. Abrir o template em `research/experimentos-mcp/templates/prompt-experimento-comparativo.md`.
2. O texto **acima** de `---` + `## Referência` é o prompt a enviar ao modelo depois de substituir os placeholders.
3. O ficheiro base de integridade estrutural é `research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/Prompts/prompt-sem-mcp-e-instructions.md`.

## Regras

- **Não** remover nem renomear campos da secção “0. Métricas de execução”, nem os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`, nem a lista de etapas de latência, salvo decisão explícita de novo protocolo.
- Manter **iguais** entre experimentos as secções 1–5 do relatório, a escala 0–2 e a estrutura da Parte 1 (BMAD, patch, validação), trocando só o que os placeholders cobrem.
- `{{REGRA_1_EXECUCAO}}`: uma linha **sem** newline final (o template já separa da regra `2.`).
- Para `{{ANCORAGEM_DECISIONS_JSON}}`, usar o conjunto permitido no cenário (ex.: baseline `(codigo_repo | inferencia)`; outros cenários podem acrescentar `instruction_local` ou `MCP` conforme o prompt desse ensaio).
- Exportação: `docs/experimentos-mcp/Resultados/YYYY-MM-DD__SLUG__{{SUFIXO_ARQUIVO}}.md` — alinhar `{{SUFIXO_ARQUIVO}}` e `{{SUFIXO_ARQUIVO_LABEL}}` ao cenário.

## Validação local

Na raiz do repositório:

```bash
python research/experimentos-mcp/templates/validate_prompt_experimento_comparativo.py
```

Compara o template instantiado com placeholders do baseline ao ficheiro base (newline final normalizado).
