# Planeamento BMAD

Esta pasta agrupa a documentação de planeamento **BMAD** em dois eixos:

| Pasta | Propósito |
|-------|-----------|
| [`execucao/`](execucao/) | **Plano executado** — registo do trabalho concluído (guia híbrido nativas + MCP alinhado à implementação). |
| [`epicos/`](epicos/) | **Épicos** — especificações por tema (inventário, servidor MCP, rollout, experimentos) e template de inventário; servem de critérios de aceite e roadmap, não substituem o guia de execução. |

## Execução (entregue)

- [Plano de execução BMAD — modelo híbrido](execucao/plano-execucao-bmad.md)

## Épicos (especificação)

- [EPIC-01 — Inventário e governança](epicos/EPIC-01-inventory-governance.md)
- [EPIC-02 — Servidor MCP (MVP)](epicos/EPIC-02-mcp-server.md)
- [EPIC-03 — Rollout em muitos repositórios](epicos/EPIC-03-rollout-playbook.md)
- [EPIC-04 — Protocolo de experimentos](epicos/EPIC-04-experiments-protocol.md)
- [EPIC-05 — Evidence gate + compliance matrix](epicos/EPIC-05-normative-evidence-gate-and-compliance-matrix.md)
- [EPIC-06 — Gap analysis de uso real com agente](epicos/EPIC-06-agent-real-usage-gap-analysis-and-redesign-plan.md)
- [EPIC-07 — Qualidade de ranking de busca e integridade do corpus](epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md)
- [EPIC-08 — Stopwords PT first pass e rebaseline da suite de contexto](epicos/EPIC-08-stopwords-pt-first-pass-and-rebaseline.md)
- [EPIC-09 — Observability/readiness cross-domain coverage (controlled pass)](epicos/EPIC-09-i04-observability-readiness-cross-domain-coverage.md)
- [EPIC-10 — Corpus Query Expansion Map (implementação da ADR-002)](epicos/EPIC-10-corpus-query-expansion-map.md)
- [EPIC-11 — Catálogo `list_instructions_index` (implementação da ADR-003)](epicos/EPIC-11-list-instructions-index-catalog-filters-pagination.md)
- [Template de inventário (EPIC-01)](epicos/INVENTORY-TEMPLATE.md)

## Pesquisa e análises

- Metodologia e experimentos: [`../../research/README.md`](../../research/README.md)
- Índice das análises técnicas datadas (MCP, corpus, estratégias): [`../../research/analises/README.md`](../../research/analises/README.md)
