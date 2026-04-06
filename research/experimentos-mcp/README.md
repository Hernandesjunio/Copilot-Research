# Experimentos MCP

Registro de experimentos (prompts, setup, resultados) para evoluir o corpus, o template fino ou o servidor MCP sem misturar com conteúdo canônico.

## Árvore por experiência

**Opção A — arquivo único na raiz desta pasta**

```text
experimentos-mcp/
├── README.md
├── _template-experimento.md
└── 2026-04-05-slug-curto.md
```

**Opção B — pasta por ensaio** (útil com anexos, exports de chat, screenshots)

```text
experimentos-mcp/
└── 2026-04-05-slug-curto/
    ├── notas.md          # copiar a partir de _template-experimento.md
    └── (opcional) chat-export.txt
```

Use data `YYYY-MM-DD` e um `slug` em minúsculas com hífens.

Exemplo preenchido: [`2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`](2026-04-05-mcp-corporate-instructions-avaliacao-tools.md) (origem: [`rascunho.md`](rascunho.md)).

## Ligações

- Comportamento e prompts: [`../../copilot-comportamento/convenções-prompts.md`](../../copilot-comportamento/convenções-prompts.md)
- Governança: [`../../planning/bmad/EPIC-01-inventory-governance.md`](../../planning/bmad/EPIC-01-inventory-governance.md)
- Servidor: [`../../mcp-instructions-server/README.md`](../../mcp-instructions-server/README.md)
