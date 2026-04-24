---
id: microservice-messaging-rabbitmq-publish-consume
title: "Mensageria — RabbitMQ, contratos, idempotência e dead letter"
tags: [microservice, messaging, rabbitmq, resilience, observability, idempotency]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals: [RabbitMQ, IConnection, RabbitMQ.Client, MassTransit, AddMassTransit, IBus]
on_absence: hypothesis_only
---

# Objetivo

Padronizar publicação e consumo com RabbitMQ em microservices .NET: contratos de mensagem, retries, dead letter, idempotência de consumo, correlação e observabilidade, alinhado a consistência eventual e padrão outbox quando necessário.

## TL;DR

- Contrato de mensagem versionado (`v1`, `v2` ou envelope com `schemaVersion`); produtores e consumidores explícitos sobre compatibilidade.
- Consumer **ack** somente após persistência/processamento idempotente concluído; **nack** com requeue apenas para falhas transientes documentadas.
- Filas DLQ (dead letter) configuradas para poison messages; limite de reentregas com contador ou TTL de retry.
- Propagar `traceparent` em propriedades/headers quando suportado pelo cliente.
- Consumidor que materializa **projeção** ou **modelo de leitura** (CQRS light): atualizar só após processamento idempotente; alinhar chaves com o produtor/outbox.

## Comandos vs eventos

- **Comando**: uma ação solicitada; tipicamente um handler; pode exigir idempotência por `messageId`/`Idempotency-Key`.
- **Evento**: fatos já ocorridos; consumidores não podem “falhar o mundo” se forem opcionais — usar filas separadas e política de descarte controlada.

## Consistência e outbox

- Quando publicação deve ser atômica com escrita no banco, usar **Transactional Outbox** processado por worker dedicado; não publicar diretamente no meio de transação sem padrão.

## Projeção e modelo de leitura (a partir de eventos consumidos)

- Se o produto mantiver um **modelo de leitura** ou vista desnormalizada atualizada por consumidores, cada mensagem deve ser tratada como **fato já aceite**: aplicar o efeito na projeção de forma **idempotente** (mesma mensagem/`messageId` não pode duplicar efeito).
- Preferir chave de idempotência estável: `messageId`, `(tipoDeEvento, identificadorDeNegócio, versão)` ou equivalente documentado no contrato.
- Ordem: se o domínio exige ordenação parcial, usar particionamento por chave de agregado e assinalar no estado da projeção o **último evento** aplicado quando necessário; não assumir ordem global entre tópicos sem contrato.
- Falhas de infraestrutura no consumidor: **nack**/requeue conforme política de transientes; após N tentativas, **DLQ** e intervenção — a projeção pode ficar temporariamente atrás do agregado fonte (**consistência eventual**); documentar SLAs no produto.
- Invalidação de cache em APIs de leitura: quando existir `IMemoryCache` ou cache HTTP, seguir `microservice-caching-imemorycache-policy` e as instructions locais para invalidação vs TTL após eventos aplicados.

## Snippet

```csharp
// Exemplo ilustrativo: correlação mínima (preferir integração W3C do OpenTelemetry/RabbitMQ client)
props.Headers ??= new Dictionary<string, object?>();
if (Activity.Current?.Id is { } traceId)
    props.Headers["traceparent"] = traceId; // ajustar ao formato W3C suportado pelo broker/cliente
props.MessageId ??= Guid.NewGuid().ToString("N");
```

## Pode ser feito

- Implementar um **Projetor** dedicado (classe/handler) que traduz eventos do contrato para updates no armazenamento da read model, com testes de duplicação de mensagem.
- Definir prefetch (`BasicQos`) coerente com tempo de processamento para evitar fome ou acúmulo.
- Serialização explícita (System.Text.Json) com regras de nome estáveis.
- Métricas: taxa publicada/consumida, lag, reentregas, DLQ.

## Não pode ser feito

- Tratar a read model como fonte de verdade forte **sem** aceitar atraso de replicação ou sem estratégia de reconciliação quando o consumidor falha.
- Processar mensagem gigante (“supermensagem”) sem chunking/streaming ou storage intermediário.
- Ack antes de concluir efeito durável exigido pelo domínio.
- Depender de ordenação global entre filas diferentes sem contrato explícito de particionamento.
