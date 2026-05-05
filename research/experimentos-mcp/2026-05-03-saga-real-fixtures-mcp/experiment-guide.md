# Guide Step by Step - SAGA realista com fixtures MCP

## 1. Objetivo da rodada

Este experimento quer responder a uma pergunta mais forte do que a rodada anterior:

**o MCP `corporate-instructions` consegue ajudar uma IA a descobrir, planejar e implementar uma SAGA em um fluxo real do repositorio, sem inventar demais?**

## 2. Regra central

O agente nao deve partir de um dominio inventado.

Ele deve:

1. procurar no repo um fluxo real com 3+ passos e compensacao plausivel;
2. cruzar isso com o MCP;
3. declarar o que e FATO, HIPOTESE e BLOQUEIO;
4. so implementar se houver evidencias suficientes.

Se nao houver cenario real bem ancorado, a rodada ainda e valida, mas deve terminar com diagnostico e stop justificado.

## 3. Estrategia recomendada

Use duas etapas separadas:

1. **execucao do experimento**: descoberta, plano, implementacao, validacao e relatorio primario;
2. **extracao de metricas e parecer**: consolidacao das metricas e julgamento se o MCP ajudou.

## 4. Ordem de execucao

### Etapa 1 - Execucao

- Prompt: `prompts/01-execucao-saga-real-com-mcp.md`
- Saida sugerida:
  - `artefatos/YYYY-MM-DD__execucao-saga-real-mcp.md`

### Etapa 2 - Extracao de metricas e parecer

- Prompt: `prompts/02-extracao-metricas-e-parecer.md`
- Entrada obrigatoria:
  - artefato da etapa 1;
  - se existir, telemetry NDJSON do MCP;
  - se existir, diff ou chat export da execucao.
- Saida sugerida:
  - `resultados/YYYY-MM-DD__saga-real-fixtures-mcp__parecer.md`

## 5. Fontes de evidencia aceitas

Prioridade:

1. corpus MCP recuperado em runtime;
2. codigo e configuracao do repo;
3. instrucoes locais;
4. telemetry ou logs da sessao;
5. estimativa manual explicitamente rotulada.

## 6. Regra de stop

O agente deve parar antes da implementacao se ocorrer qualquer um destes casos:

- nao existe fluxo real com sinais suficientes de multipasso compensavel;
- o contrato publico necessario seria novo e nao ha base suficiente no repo;
- o fluxo exigiria RabbitMQ, outbox, worker ou outra infra sem sinais do workspace;
- a compensacao necessaria e irreversivel e nao ha fallback operacional plausivel;
- o repositorio nao oferece meios minimos de validacao para o fluxo proposto.

## 7. Como coletar metricas do MCP

Se voce tiver telemetry NDJSON do MCP, gere um sumario com:

```bash
python "mcp-instructions-server/scripts/build_quality_report.py" --input "CAMINHO/telemetry.ndjson" --output "CAMINHO/quality-report.json"
```

Se houver baseline para comparacao:

```bash
python "mcp-instructions-server/scripts/build_quality_report.py" --input "CAMINHO/telemetry.ndjson" --output "CAMINHO/quality-report.json" --baseline "CAMINHO/baseline-quality-report.json"
```

Campos mais uteis para copiar no parecer final:

- `summary.total_completed_calls`
- `counts.tool_failures`
- `counts.retries_total`
- `rates.zero_result_rate`
- `rates.low_confidence_rate`
- `search_quality.avg_search_confidence`
- `tool_breakdown`
- `warnings`

## 8. O que caracteriza uma rodada boa

Uma boa rodada nao e a que necessariamente implementa mais codigo.

E a que:

- escolhe um cenario realmente ancorado;
- usa o MCP para restringir e melhorar decisoes;
- evita extrapolar mensageria/outbox sem sinais;
- valida criterios de aceite com comandos ou evidencia objetiva;
- produz um parecer final que permita dizer se o MCP ajudou ou nao.

## 9. Checklist do operador

- [ ] rodei a etapa 1 antes da etapa 2
- [ ] guardei o artefato da execucao
- [ ] juntei telemetry se ela existir
- [ ] mantive separado o que veio de MCP, repo e inferencia
- [ ] nao tratei ausencia de evidencias como licenca para inventar stack
