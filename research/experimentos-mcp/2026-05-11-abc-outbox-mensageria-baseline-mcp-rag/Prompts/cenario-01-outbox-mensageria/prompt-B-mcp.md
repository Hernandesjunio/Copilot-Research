Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, engenharia de software e qualidade de implementação.

## Contexto do experimento

**Identificação:** Cenário 01 (Outbox / mensageria) — condição **B: MCP**.

Estou avaliando o comportamento do agente usando **MCP `corporate-instructions`** como fonte de contexto/guardrails (consulta via tools), comparado a um baseline e a um cenário de RAG geral.

**Regras de orquestração (condição B)**

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **MCP (obrigatório nesta condição):**
  - Usar tools `corporate_instructions_*` para recuperar guardrails e decisões cross-cutting (mensageria/outbox/idempotência/dados/observabilidade/erros/testes).
  - Antes de aplicar um padrão, ler o corpo completo via `corporate_instructions_get_instructions_batch`.
  - Citar no relatório: `instruction_id` + quais decisões foram ancoradas nele.
- **Não usar** `.github/instructions/` como corpus normativo (fora do escopo do experimento).
- O que existe no código é **FATO**; o que não existe é **HIPÓTESE**. Não apresente hipótese como regra organizacional. Para cada hipótese, indique como validar.
- **Fluxo:** antes de editar ficheiros críticos, ler o alvo; após mudanças relevantes, executar build e testes se existirem.

## Tarefa

**Título:** Implementar publicação de eventos de cliente via mensageria com garantia de entrega.

**Descrição:**

Quando um cliente é criado (`POST /clientes`) ou atualizado (`PUT /clientes/{id}`):

1. Persistir o evento numa tabela **Outbox** local na **mesma transação** do `INSERT`/`UPDATE` do cliente.
2. Publicar o evento para um tópico ou fila de mensageria (RabbitMQ **ou** simulação em memória / fila local se o projeto não tiver broker real).
3. Implementar **consumidor** que lê eventos do tópico/fila e atualiza um **modelo de leitura** (`ClienteReadModel` ou equivalente alinhado ao projeto).
4. Garantir **idempotência:** o mesmo evento publicado duas vezes não duplica efeito na read-model.
5. Implementar **DLQ** (Dead Letter Queue ou tabela equivalente) para eventos que falharem após **N** tentativas (definir N de forma explícita no código, p.ex. 3).

**Restrições:**

- Não quebrar o CRUD existente (`GET`, `PUT`, `POST`, `DELETE`).
- Cache em `GET`, se existir, deve ser invalidado após publicação bem-sucedida **ou** usar TTL curto se a mensageria falhar (documentar a escolha).
- O build deve passar; testes de integração são desejáveis se o repositório já os suportar.

**Cenários de comportamento esperados:**

- Cliente criado com sucesso → evento publicado e consumido; read-model coerente.
- Cliente atualizado com sucesso → evento publicado e consumido; idempotência verificável.
- Falha ao publicar → evento permanece processável via Outbox/retry.
- Consumidor falha uma vez e sucede na segunda → DLQ vazio; read-model atualizado.

**Critérios de aceite (objetivos)**

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Outbox | Tabela (ou equivalente) com tipo de evento, payload, timestamps e controlo de processamento |
| POST gera evento | Criar cliente → registo de evento no Outbox |
| PUT gera evento | Atualizar cliente → registo de evento no Outbox |
| Read-model | Após consumo, modelo de leitura reflete o cliente |
| Idempotência | Publicar o mesmo evento duas vezes → um único efeito na read-model |
| DLQ | Após falhas repetidas do consumidor → evento em DLQ ou equivalente |
| Cache | Após `PUT` + fluxo de publicação, `GET` reflete alterações (ou TTL documentado) |
| Correlação | Evento ou pipeline carrega `CorrelationId` alinhado ao pedido HTTP, se o projeto já usar esse conceito |
| Segurança | SQL parametrizado; sem concatenação insegura |

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice:
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação em memória/fila local conforme evidência no código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite e evidência no repositório.

#### 2) Plano BMAD (obrigatório)
- Background
- Mission
- Approach
- Delivery/validation

#### 3) Implementação (patch)

#### 4) Validação
- Execute/indique validações objetivas (por exemplo: `dotnet build`, testes unitários/integração quando aplicável).
- Relacione cada linha relevante dos critérios de aceite a um passo de verificação ou comando.

### Parte 2 — Relatório do experimento (obrigatório)

- Diferencie explicitamente: **FATO**, **HIPÓTESE**, **RISCO DE INTERPRETAÇÃO**.
- Declare explicitamente: `mcp_tools_chamadas: <N>` e liste quais tools foram usadas e com quais queries/ids.
- Informe métricas (use N/A quando não disponível): tempo total, tempos por etapa, comandos executados, qtd de arquivos lidos/tocados, tokens/custo (ou estimativa com método).

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__abc-outbox-mensageria-baseline-mcp-rag__mcp.md`

O conteúdo do arquivo deve conter:
- Parte 1 (Execução)
- Parte 2 (Relatório)
- Blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

