# EPIC-04 — Experiências E1–E5 e hardening

## Objetivo

Validar na prática o modelo híbrido (nativas mínimas + MCP) e afinar descrições de tools, `max_results` e formato de retorno.

## Experiências

| ID | Hipótese | Protocolo | Métrica |
|----|----------|-----------|---------|
| **E1** | Nativas reduzidas + `search_instructions` mantém ou melhora a qualidade. | Mesmo conjunto de 5–10 prompts “antes” (corpus só nativo) e “depois” (nativo mínimo + MCP obrigatório no texto da nativa). | Nota 1–5 por critério (correção, aderência a padrões, completude); contagem aproximada de tokens das nativas (copiar para contador). |
| **E2** | Descrições com **“Use when…”** aumentam invocação da tool. | Rodada A: tools com descrições genéricas. Rodada B: descrições atuais do servidor. | Contagem manual de turnos em que o agente chama `search_instructions` / `get_instruction` (anotar em folha de sessão). |
| **E3** | `max_results=8` adiciona ruído vs `3`. | Mesma query em corpus real; comparar outputs com K=3 e K=8. | Relevância percebida (binário por resultado: útil / ruído); tempo até resposta útil. |
| **E4** | Embeddings (fase futura) superam fulltext em queries vagas. | Construir 20–30 queries reais do time; rotular documentos esperados. | Precisão@5 fulltext vs embeddings (quando implementado). |
| **E5** | Omitir do MCP temas já na nativa reduz conflitos. | Checklist em PRs piloto: “houve contradição entre nativa e tool?” | Contagem de PRs com conflito detectado / resolvido. |

## Registo de sessão (template)

```
Data:
Repo piloto:
Prompt ID:
Ferramentas MCP invocadas (s/n): 
Qualidade (1-5):
Notas:
```

## Hardening pós-piloto

- Documentar no README do servidor os **limites de tokens** implícitos (`max_results`, `max_chars` em `get_instruction`).
- Cache em memória por sessão (já é o caso do índice em RAM); evoluir para invalidação explícita se necessário.
- Telemetria **sem conteúdo**: opcionalmente contar apenas nomes de tools e códigos de erro (se a organização permitir).

**Aceite deste épico:** pelo menos **E1–E3** executados em 1 repo piloto com registo preenchido; ajustes aplicados ao servidor (descrições, defaults) com commit referenciado.
