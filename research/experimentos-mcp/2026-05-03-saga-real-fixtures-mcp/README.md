# Experimento - SAGA realista com fixtures MCP

Este experimento foi desenhado para testar o MCP `corporate-instructions` em um cenario de SAGA mais realista e menos artificial do que o onboarding anterior.

O foco aqui nao e forcar um dominio inventado. O foco e verificar se outra IA consegue:

- encontrar no repositorio um fluxo real com sinais de SAGA;
- compor contexto normativo a partir do corpus do MCP;
- limitar inferencia quando faltarem sinais do workspace;
- produzir um plano e uma implementacao auditavel;
- consolidar metricas para julgar se o MCP ajudou de fato.

## Diferenca para o experimento anterior

No experimento anterior, o cenario de onboarding acabou ficando parcialmente plausivel, mas ainda dependente de inferencia relevante sobre contrato publico, correlacao e operacao.

Neste experimento, o agente deve primeiro provar que existe um fluxo real candidato no repo. So depois ele pode planejar e implementar.

Isso reduz dois riscos:

- construir uma SAGA "bonita" em cima de um caso pouco ancorado;
- atribuir ao MCP uma ajuda que na pratica veio de inferencia ad hoc.

## O que o corpus `fixtures/instructions/` sustenta bem

Este pacote foi montado com base principalmente nestes guardrails:

- `microservice-saga-process-manager-and-compensation`
- `microservice-messaging-rabbitmq-publish-consume`
- `microservice-data-access-and-sql-security`
- `microservice-resilience-polly-timeouts-and-circuit-breaker`
- `microservice-rest-http-semantics-and-status-codes`
- `microservice-api-validation-and-error-contracts`
- `microservice-opentelemetry-correlation-and-health`
- `microservice-testing-strategy-unit-integration-contract`
- `assistant-workflow-bmad-planning-and-controlled-inference`

## Estrutura

```text
2026-05-03-saga-real-fixtures-mcp/
├── README.md
├── experiment-guide.md
├── prompts/
│   ├── 01-execucao-saga-real-com-mcp.md
│   └── 02-extracao-metricas-e-parecer.md
├── artefatos/
│   └── .gitkeep
└── resultados/
    └── .gitkeep
```

## Resultado esperado

Ao final de uma rodada bem executada, voce deve conseguir responder com evidencia:

1. o MCP ajudou a selecionar guardrails de SAGA de forma util;
2. o repo realmente tinha sinais suficientes para um fluxo compensavel;
3. a IA evitou inventar infraestrutura nova quando o corpus exigia `workspace_evidence_required`;
4. a qualidade final subiu por causa do MCP, e nao apenas por causa do prompt.

## Como usar

Siga o fluxo descrito em `experiment-guide.md`.
