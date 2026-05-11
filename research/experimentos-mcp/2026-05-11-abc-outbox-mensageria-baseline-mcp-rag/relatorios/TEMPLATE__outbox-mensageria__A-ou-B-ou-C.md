# Relatório — Outbox/Mensageria (A/B/C)

Preencha este ficheiro **uma vez por execução** (A, B ou C).

## Identificação

- **Data**: YYYY-MM-DD
- **Condição**: A (baseline-sem-fixtures) | B (mcp) | C (rag-geral)
- **Slug**: `abc-outbox-mensageria-baseline-mcp-rag`
- **Modelo**: (ex.: GPT-5.x / Claude / etc.)
- **IDE**: Cursor
- **Ordem de execução**: ABC | ACB | BAC | BCA | CAB | CBA | execução parcial

## Checklist de validade (marcar)

- [ ] Thread/sessão separada (sem contaminação)
- [ ] Ticket copiado integralmente do prompt
- [ ] BMAD produzido antes do patch
- [ ] Build/teste executado ou N/A justificado
- [ ] (Somente A) `fixtures/` foi removida **antes** de iniciar e restaurada **ao final**
- [ ] (Somente B) Houve uso de MCP (`corporate_instructions_*`) para contexto/guardrails (e IDs citados)
- [ ] (Somente C) `fixtures/` permaneceu intacta e foi permitido RAG geral no codebase

## Resultados por critério de aceite (Pass/Fail)

- [ ] Build passa (`dotnet build`)
- [ ] Outbox criada/implementada
- [ ] POST gera evento no outbox
- [ ] PUT gera evento no outbox
- [ ] Publicação implementada (broker real ou simulado coerente com repo)
- [ ] Consumidor implementado
- [ ] Read-model atualiza
- [ ] Idempotência demonstrável
- [ ] DLQ após N tentativas (N explícito)
- [ ] Cache/GET coerente (ou TTL documentado)
- [ ] CorrelationId preservado (se conceito existir no repo)
- [ ] SQL parametrizado / segurança básica

## Rubrica (0–2)

- **Aderência aos critérios de aceite**: 0 | 1 | 2
- **Qualidade arquitetural**: 0 | 1 | 2
- **Completude**: 0 | 1 | 2
- **Consistência**: 0 | 1 | 2
- **Validação objetiva**: 0 | 1 | 2
- **Segurança**: 0 | 1 | 2

## Métricas

- **inicio_iso**:
- **fim_iso**:
- **duracao_ms**:
- **tempos_por_etapa_ms**:
  - leitura:
  - decisao:
  - implementacao:
  - validacao:
  - relatorio:
- **arquivos_lidos_qtd**:
- **arquivos_tocados_qtd**:
- **comandos_executados**:
- **tokens_input/output**: N/A | (valor)
- **custo**: N/A | (valor)
- **reprompts_qtd**:

## Observações (FATO / HIPÓTESE / RISCO)

### FATO

- 

### HIPÓTESE

- 

### RISCO DE INTERPRETAÇÃO

- 

## Link para exportação

- `docs/experimentos-mcp/Resultados/YYYY-MM-DD__abc-outbox-mensageria-baseline-mcp-rag__<baseline|mcp|rag>.md`

