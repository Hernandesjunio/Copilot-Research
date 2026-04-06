# Comportamento do Copilot (governança local)

Este diretório agrupa **política e checklists** sobre como o Copilot e o MCP devem ser usados nesta iniciativa. O conteúdo **canónico** de arquitetura continua no corpus servido pelo MCP (`fixtures/instructions` neste repo de desenvolvimento; repositório canónico em produção).

## Árvore recomendada

```text
copilot-comportamento/
├── README.md                 ← este ficheiro (índice)
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

- [Política de camadas](politica-camadas.md)
- [Checklist novo repo](checklist-novo-repo.md)
- [Convenções de prompts](convenções-prompts.md)

## Ligações no repositório

- Template fino por repo: [`../templates/copilot-instructions.thin.md`](../templates/copilot-instructions.thin.md)
- Experimentos: [`../research/experimentos-mcp/`](../research/experimentos-mcp/)
- Governança do corpus: [`../planning/bmad/EPIC-01-inventory-governance.md`](../planning/bmad/EPIC-01-inventory-governance.md)
- Servidor MCP: [`../mcp-instructions-server/README.md`](../mcp-instructions-server/README.md)

## Anti-padrões (resumo)

- Duplicar no nativo ficheiros longos que já estão no corpus MCP.
- Colocar segredos, tokens ou dados pessoais em exemplos ou instruções.
- Ignorar a precedência: **instructions nativas do repo atual** prevalecem sobre o MCP.
