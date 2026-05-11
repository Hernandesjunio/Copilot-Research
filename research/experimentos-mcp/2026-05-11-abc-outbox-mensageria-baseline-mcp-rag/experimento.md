# Protocolo — Experimento A/B/C (Outbox/Mensageria)

## 0) Definição do experimento

**Nome:** `abc-outbox-mensageria-baseline-mcp-rag`  
**Objeto:** um único cenário canônico (Outbox / mensageria) executado em três condições controladas.

### Condições

| Letra | Condição | Regra operacional |
|------:|----------|-------------------|
| **A** | **Baseline (sem `fixtures/`)** | Durante a execução, a pasta `fixtures/` deve estar **temporariamente removida do workspace** (o experimentador move para fora e devolve ao final). Sem MCP e sem `.github/instructions` como corpus. |
| **B** | **MCP** | Usar MCP `corporate-instructions` como fonte de contexto/guardrails via tools `corporate_instructions_*` (consultar, ler batch e citar IDs). `fixtures/` pode estar presente (não é a variável de controle aqui). |
| **C** | **RAG geral** | Usar RAG geral sobre **todo o codebase**, com `fixtures/` **intacta** (permitido recuperar/ler conteúdo dela como parte do workspace). Sem restrições de MCP (pode estar desligado). |

**O que está sendo testado:** diferenças entre (A) sem fixtures e sem recuperação; (B) recuperação via MCP; (C) recuperação geral via workspace RAG.  
**O que não está sendo testado aqui:** robustez estatística; comparação multi-repo; tuning de ranking/expansão.

## 1) Unidade experimental e controle de contaminação

- **Unidade experimental:** uma execução completa do ticket canônico (plano BMAD + patch + validação + relatório) em **uma sessão/thread**.
- **Controle de contaminação (obrigatório):**
  - executar A, B e C em **threads separadas**;
  - não reutilizar texto de uma condição na outra;
  - não “levar” decisões de A para B (ou vice-versa); se algo for repetido, deve emergir de novo a partir do código e do ticket.

## 2) Ticket canônico (imutável)

O ticket usado é o mesmo corpo do cenário 01 do experimento de 2026-05-04 (Outbox / mensageria):

- persistir evento em tabela Outbox na mesma transação de `POST /clientes` e `PUT /clientes/{id}`;
- publicar em mensageria real ou simulação (conforme evidência do repo);
- implementar consumidor + read-model;
- garantir idempotência;
- implementar DLQ após N tentativas.

Para reduzir variação, o ticket deve ser copiado **integralmente** do prompt de cada condição.

## 3) Procedimento (passo a passo)

Para **A**:

- aplicar orquestrador `orquestrador/cursor-orq__A-baseline.md`
- colar `Prompts/cenario-01-outbox-mensageria/prompt-A-baseline.md`
- **antes de iniciar**: mover `fixtures/` para fora do workspace; **ao final**: restaurar `fixtures/`
- executar até concluir (incluindo exportação)

Para **B**:

- aplicar orquestrador `orquestrador/cursor-orq__B-mcp.md`
- colar `Prompts/cenario-01-outbox-mensageria/prompt-B-mcp.md`
- executar até concluir (incluindo exportação)

Para **C**:

- aplicar orquestrador `orquestrador/cursor-orq__C-rag-geral.md`
- colar `Prompts/cenario-01-outbox-mensageria/prompt-C-rag-geral.md`
- executar até concluir (incluindo exportação)

## 4) Hipóteses e métricas

### Hipótese principal

- **H1:** B (MCP) e C (RAG geral) terão maior aderência e menor inferência do que A (baseline sem fixtures).

### O que medir (mínimo)

- **Qualidade do resultado**: aderência aos critérios de aceite do ticket (Pass/Fail por item).
- **Necessidade de inferência**: contagem de afirmações rotuladas como FATO / HIPÓTESE / RISCO.
- **Esforço**: wall-clock total; e tempos por etapa (leitura, decisão, implementação, validação).
- **Interação**: número de reprompts; número de correções/ajustes após primeira tentativa.
- **Alterações no repo**: número de arquivos tocados; impacto (camadas, migrations, infra).

### Métricas “desejáveis” (se disponíveis)

- tokens input/output e custo (ou N/A com estimativa explícita)
- número de comandos executados (build/test)

## 5) Rubrica (0–2 por critério)

- **Aderência aos critérios de aceite** (0–2)
- **Qualidade do desenho arquitetural** (0–2)
- **Completude** (0–2)
- **Consistência / não contradição** (0–2)
- **Testabilidade / validação objetiva** (0–2)
- **Segurança básica (SQL parametrizado, sem segredos)** (0–2)

## 6) Artefatos obrigatórios

Após rodar A, B e C, devem existir:

- 3 arquivos exportados em `docs/experimentos-mcp/Resultados/`:
  - `YYYY-MM-DD__abc-outbox-mensageria-baseline-mcp-rag__baseline.md`
  - `YYYY-MM-DD__abc-outbox-mensageria-baseline-mcp-rag__mcp.md`
  - `YYYY-MM-DD__abc-outbox-mensageria-baseline-mcp-rag__rag.md`
- 3 relatórios preenchidos a partir do template em `relatorios/` (ou um comparativo consolidado).

## 7) Ameaças à validade (registrar no relatório)

- **Efeito de aprendizado do experimentador**: ao fazer A primeiro, você aprende o repo.
  - mitigação: se possível, sorteie a ordem (AB vs BA) em repetições futuras.
- **Variação do modelo**: atualizações/temperatura/estado interno afetam resultados.
  - mitigação: registrar modelo e timestamp; repetir em dias/horários diferentes.
- **Baseline com remoção de fixtures**: risco de esquecer de restaurar `fixtures/` ao final.
  - mitigação: checklist + comando explícito de restore.

