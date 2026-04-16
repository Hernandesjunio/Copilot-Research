# Comportamento do Copilot (governança local)

Este diretório agrupa **política e checklists** sobre como o Copilot e o MCP devem ser usados nesta iniciativa. O conteúdo **canônico** de arquitetura continua no corpus servido pelo MCP (`fixtures/instructions` neste repo de desenvolvimento; repositório canônico em produção).

## Árvore recomendada

```text
copilot-comportamento/
├── README.md                 ← este arquivo (índice)
├── politica-camadas.md       ← nativo vs MCP, precedência
├── checklist-novo-repo.md    ← ao criar/adotar um serviço
└── convenções-prompts.md     ← frases e fluxos no chat

research/
├── README.md                 ← índice da pasta research
└── experimentos-mcp/
    ├── README.md
    ├── _template-experimento.md
    └── YYYY-MM-DD-<slug>/    ← opcional: pasta por ensaio
        └── notas.md
```

## Documentos nesta pasta

As políticas aqui **devem** poder ser rastreadas a evidência em [`../research/`](../research/README.md) (experimentos e análises datados). Onde houver números ou comportamento observado, cite o artefato correspondente em `research/experimentos-mcp/…` ao atualizar estes ficheiros.

- [Política de camadas](politica-camadas.md)
- [Checklist novo repo](checklist-novo-repo.md)
- [Convenções de prompts](convenções-prompts.md)
- [Orquestração MCP (pseudo-hook)](orquestracao-mcp-pseudo-hook.md)
- [Gestão de sessão (janela de contexto)](gestao-sessao-janela-contexto.md)
- [Roadmap de tools MCP](roadmap-tools-mcp.md)

## Ligações no repositório

- Template fino por repo: [`../templates/copilot-instructions.thin.md`](../templates/copilot-instructions.thin.md)
- Experimentos: [`../research/experimentos-mcp/`](../research/experimentos-mcp/)
- Governança do corpus: [`../planning/bmad/epicos/EPIC-01-inventory-governance.md`](../planning/bmad/epicos/EPIC-01-inventory-governance.md)
- Servidor MCP: [`../mcp-instructions-server/README.md`](../mcp-instructions-server/README.md)

## Anti-padrões (resumo)

- Duplicar no nativo arquivos longos que já estão no corpus MCP.
- Colocar segredos, tokens ou dados pessoais em exemplos ou instruções.
- Ignorar a precedência: **instructions nativas do repo atual** prevalecem sobre o MCP.
