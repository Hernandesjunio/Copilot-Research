# Experimento — Cenário 1 (Outbox / mensageria) — Condição **A: MCP**

## Regras de orquestração (condição A)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Stack assumida:** API de clientes em C#, .NET 8, ASP.NET Core, arquitetura em camadas.
- **MCP `corporate-instructions`:** padrões organizacionais vêm do MCP (não estão no repo). Este bloco prevalece sobre o MCP se houver conflito explícito com o que pedimos abaixo.
- **Consulta MCP obrigatória em decisões transversais:**
  1. `list_instructions_index` — ver corpus e agrupamentos.
  2. `search_instructions` — várias queries por tema (mensageria, outbox, idempotência, resiliência, SQL, observabilidade); não uma única busca.
  3. `get_instructions_batch` — ler o corpo completo de todas as instructions relevantes de uma vez.
  4. Cruzar policy do MCP com o código: o que já existe no repo é **FATO**; o que não existe é **HIPÓTESE**. O código existente prevalece.
  5. Citar nas decisões: id da instruction + ficheiros do repo tocados.
- **Fluxo:** antes de editar ficheiros críticos, ler o alvo; após mudanças grandes, executar `dotnet build` e testes se existirem.

## Tarefa (implementação no repositório)

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

**Orientação de desenho (não prescritiva se o MCP/código indicar outro padrão coerente):**

- Tabela tipo `ClienteEventosOutbox` com campos incluindo: identificador, tipo de evento, payload, criado em, estado processado/publicado.
- Serviço de domínio: após `INSERT`/`UPDATE` bem-sucedido do cliente, registar evento no Outbox na mesma transação.
- Interface de publicação: tentar publicar; em falha, deixar registo no Outbox para retry.
- Idempotência: chave de idempotência, hash do evento ou equivalente.
- DLQ: após esgotar retries, mover ou registar em estrutura de DLQ.

## Critérios de aceite (objetivos)

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

## Entrega pedida

1. Produz primeiro um plano **BMAD** (Background, Mission, Approach, Delivery/validation) com **FATO** vs **HIPÓTESE** explícitos face ao código atual.
2. Implementa a solução no repositório.
3. Lista como validar manualmente cada critério de aceite acima.
