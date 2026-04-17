# Experimento — Cenário 1 (Outbox / mensageria) — Condição **C: Baseline**

## Regras de orquestração (condição C)

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Limites:** se faltar informação decisiva, explicitar a inferência e oferecer 2–3 opções.
- **Não usar** MCP `corporate-instructions`.
- **Não usar** `.github/instructions/` nem outro corpus externo de políticas. Apenas o código e artefactos deste repositório são fonte de verdade.
- Se não houver evidência no código, rotular como **HIPÓTESE** e descrever como validar; não apresentar hipótese como norma organizacional.
- **Contexto do repo:** API de gestão de clientes em camadas; C#, .NET 8, ASP.NET Core.
- **Fluxo mínimo:** usar **BMAD** antes de codificar — Background, Mission, Approach, Delivery/validation.

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

**Orientação de desenho (derivar do código existente; não assumir stack não presente):**

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

1. Produz primeiro um plano **BMAD** (Background, Mission, Approach, Delivery/validation) com **FATO** vs **HIPÓTESE** explícitos face apenas ao código do repositório.
2. Implementa a solução no repositório.
3. Lista como validar manualmente cada critério de aceite acima.
