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

## Comandos vs eventos

- **Comando**: uma ação solicitada; tipicamente um handler; pode exigir idempotência por `messageId`/`Idempotency-Key`.
- **Evento**: fatos já ocorridos; consumidores não podem “falhar o mundo” se forem opcionais — usar filas separadas e política de descarte controlada.

## Consistência e outbox

- Quando publicação deve ser atômica com escrita no banco, usar **Transactional Outbox** processado por worker dedicado; não publicar diretamente no meio de transação sem padrão.

## Snippet

```csharp
// Exemplo ilustrativo: correlação mínima (preferir integração W3C do OpenTelemetry/RabbitMQ client)
props.Headers ??= new Dictionary<string, object?>();
if (Activity.Current?.Id is { } traceId)
    props.Headers["traceparent"] = traceId; // ajustar ao formato W3C suportado pelo broker/cliente
props.MessageId ??= Guid.NewGuid().ToString("N");
```

## Pode ser feito

- Definir prefetch (`BasicQos`) coerente com tempo de processamento para evitar fome ou acúmulo.
- Serialização explícita (System.Text.Json) com regras de nome estáveis.
- Métricas: taxa publicada/consumida, lag, reentregas, DLQ.

## Não pode ser feito

- Processar mensagem gigante (“supermensagem”) sem chunking/streaming ou storage intermediário.
- Ack antes de concluir efeito durável exigido pelo domínio.
- Depender de ordenação global entre filas diferentes sem contrato explícito de particionamento.
