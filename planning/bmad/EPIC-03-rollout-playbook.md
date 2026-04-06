# EPIC-03 — Rollout: 100+ repos sem duplicar o corpus

## Objetivo

Cada microserviço mantém **apenas** instructions nativas mínimas (5–15 temas) e obtém o restante via MCP apontando para o **mesmo** corpus versionado.

## Opções de distribuição do corpus

| Opção | Como funciona | Prós | Contras |
|-------|----------------|------|---------|
| **A — Repo Git central** | Repositório `org/architecture-instructions` (ou nome equivalente); devs clonam uma vez na máquina. | Fonte da verdade simples, PRs e revisão no Git. | Cada dev precisa de clone atualizado. |
| **B — Submodule** | Repo de serviço inclui submodule para a pasta de instructions. | Versão fixa por commit do serviço. | Manutenção de submodule; atualizações explícitas. |
| **C — Package interno** | NuGet/npm que extrai `.md` para `%ProgramData%` ou `.corp/instructions` na pipeline/local. | Onboarding padronizado. | Pipeline de empacotamento + versionamento. |
| **D — Clone único + env** | Documentação: “clone X em `C:\src\instructions`”; `INSTRUCTIONS_ROOT` no MCP aponta para lá. | Zero alteração nos 100 repos. | Disciplina de atualização manual ou script. |

Recomendação inicial: **A + D** (repo central + variável de ambiente no registro MCP do VS), evoluindo para **B** ou **C** se precisarem de **pin** por versão em CI.

## Checklist para um novo repositório (~5 minutos)

1. Criar `.github/instructions/` (ou arquivo único `copilot-instructions.md`) com **apenas** regras locais: idioma, segredos, boundaries do serviço, convenções que não podem falhar.
2. Incluir um parágrafo explícito: para padrões de arquitetura compartilhados, **usar o MCP `corporate-instructions`** (`search_instructions` antes de planejar soluções transversais).
3. Registrar o servidor MCP no Visual Studio (ver [README do servidor](../../mcp-instructions-server/README.md)) com `INSTRUCTIONS_ROOT` correto.
4. (Opcional) Script `tools/sync-instructions.ps1` que faz `git pull` no repo canônico — para quem usa clone único.

## Piloto (2–3 repos)

- Escolher serviços representativos (um API, um worker, um com legado).
- **Antes:** exportar contagem de linhas das instructions duplicadas.
- **Depois:** substituir blocos duplicados por referência ao MCP; manter nativo mínimo.
- Critério de sucesso: PRs revistos sem perda de orientação prática; desenvolvedores confirmam que o agente chama `search_instructions` em tarefas de arquitetura (observação em sessão de pair).

## Reindexação

- O processo MCP reconstrói o índice ao **iniciar**. Após `git pull` no corpus, **reiniciar** o servidor MCP no VS (ou o IDE) para ver alterações.
- Futuro: tool opcional `refresh_index` se a plataforma permitir reinício leve (não incluída no MVP para reduzir superfície).

## Template de instructions nativas “finas”

Ver [`templates/copilot-instructions.thin.md`](../../templates/copilot-instructions.thin.md).

**Aceite deste épico:** playbook acordado pela equipe + 2–3 repos piloto migrados + instruções de onboarding para novos projetos.
