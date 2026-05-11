# Relatório — Outbox/Mensageria (A)

## Identificação

- **Data**: 2026-05-11
- **Condição**: A (baseline-sem-fixtures)
- **Slug**: `abc-outbox-mensageria-baseline-mcp-rag`
- **Modelo**: GPT-5.2 (Cursor Agent)
- **IDE**: Cursor
- **Ordem de execução**: execução parcial (apenas A)

## Checklist de validade (marcar)

- [x] Thread/sessão separada (sem contaminação)
- [x] Ticket copiado integralmente do prompt
- [x] BMAD produzido antes do patch (no arquivo de exportação)
- [x] Build/teste executado ou N/A justificado (`dotnet build`, `dotnet test`)
- [x] (Somente A) `fixtures/` foi removida **antes** de iniciar e restaurada **ao final** (N/A — não existe `fixtures/` no workspace)
- [x] `.github/instructions/` removida durante o experimento e restaurada ao final
- [x] `.github/copilot-instructions.md` removida durante o experimento e restaurada ao final

## Resultados por critério de aceite (Pass/Fail)

- [x] Build passa (`dotnet build`)
- [x] Outbox criada/implementada
- [x] POST gera evento no outbox
- [x] PUT gera evento no outbox
- [x] Publicação implementada (simulada em memória, coerente com ausência de broker no repo)
- [x] Consumidor implementado
- [x] Read-model atualiza
- [x] Idempotência demonstrável (ProcessedEvent com PK/UNIQUE)
- [x] DLQ após N tentativas (N explícito = 3)
- [ ] Cache/GET coerente (ou TTL documentado) (N/A — sem evidência de cache no código)
- [ ] CorrelationId preservado (se conceito existir no repo) (N/A — sem evidência no código)
- [x] SQL parametrizado / segurança básica (Dapper com parâmetros)

## Rubrica (0–2)

- **Aderência aos critérios de aceite**: 2
- **Qualidade arquitetural**: 1
- **Completude**: 2
- **Consistência**: 1
- **Validação objetiva**: 1
- **Segurança**: 2

## Métricas

- **inicio_iso**: 2026-05-11T09:57:00-03:00
- **fim_iso**: 2026-05-11T10:03:30-03:00
- **duracao_ms**: 390000
- **tempos_por_etapa_ms**:
  - leitura: 120000
  - decisao: 60000
  - implementacao: 150000
  - validacao: 45000
  - relatorio: 15000
- **arquivos_lidos_qtd**: 12
- **arquivos_tocados_qtd**: 15
- **comandos_executados**:
  - `ls -la`
  - `ls -la .github`
  - `dotnet build`
  - `dotnet test`
  - `mv` (backup/restauração temporária de `.github/instructions` e `.github/copilot-instructions.md`)
- **tokens_input/output**: N/A
- **custo**: N/A
- **reprompts_qtd**: 0

## Observações (FATO / HIPÓTESE / RISCO)

### FATO

- Persistência é via Dapper/SQL Server; `POST/PUT` passam por `ClienteRepositorioDapper`.
- Foram adicionadas tabelas e serviços para Outbox/ReadModel/Idempotência/DLQ.
- `.github/instructions/` e `.github/copilot-instructions.md` ficaram indisponíveis durante a implementação e foram restaurados ao final.

### HIPÓTESE

- Sem um ambiente de BD preparado neste experimento, a validação funcional completa (rodando API + aplicando scripts SQL + exercitando endpoints) não foi executada; requer executar `sql/001_...` e `sql/002_...` num SQL Server configurado em `Sql:ConnectionString`.

### RISCO DE INTERPRETAÇÃO

- A “mensageria” foi simulada com Channel por ausência de broker no repo; isso atende ao critério do prompt (simulação permitida), mas não testa integração real com RabbitMQ.

## Link para exportação

- `docs/experimentos-mcp/Resultados/2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__baseline.md`

