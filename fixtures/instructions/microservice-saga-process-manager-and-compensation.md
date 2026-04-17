---
id: microservice-saga-process-manager-and-compensation
title: "Consistência eventual — Saga / Process Manager, compensações e orquestração"
tags: [microservice, saga, process-manager, orchestration, messaging, outbox, consistency, resilience, idempotency]
scope: "**/*.cs"
priority: high
kind: reference
workspace_evidence_required: true
workspace_signals: [MassTransit, Saga, StateMachine, IBus, RabbitMQ, Outbox]
on_absence: hypothesis_only
---

# Objetivo

Fornecer guia reutilizável para coordenar fluxos distribuídos com **consistência eventual**, usando **Sagas / Process Managers** e **compensações**, sem depender de transações distribuídas.

## TL;DR

- Use **orquestração** (process manager) quando há múltiplas etapas e compensações claras; use **coreografia** quando eventos independentes e acoplamento baixo.
- Persistir estado da saga (durável) e tratar **idempotência** em todos os handlers.
- Publicação de mensagens que dependem de escrita no banco: aplicar **Transactional Outbox**.
- Timeouts e retries devem respeitar **não-idempotência**; não “repetir” comandos que geram efeitos irreversíveis sem deduplicação.

## Quando escolher Saga / Process Manager

| Sinal | Indica |
| --- | --- |
| Fluxo com 3+ passos e dependências entre serviços | Considerar orquestração |
| Falha parcial precisa de “desfazer” (compensar) | Saga com compensações explícitas |
| Regras de negócio exigem visibilidade do estado | Persistir estado e expor leitura interna (observabilidade) |
| Integrações externas com latência/instabilidade | Timeouts, retries controlados e transições explícitas |

## Modelo mental

- **Comando** inicia uma intenção (“executar passo”).
- **Evento** registra um fato (“passo concluído/falhou”).
- **Saga** mantém estado e decide o próximo comando/compensação.

## Regras de desenho (genéricas)

### Estado e durabilidade

- Persistir estado mínimo necessário: `CorrelationId`, status, timestamps, tentativas, “último evento processado”.
- Evitar armazenar payloads grandes no estado; guardar referências.

### Correlação

- Definir um `CorrelationId` estável desde o início do fluxo.
- Propagar `CorrelationId` e `traceparent` em mensagens e chamadas HTTP relacionadas.

### Idempotência

- Todo consumidor de comando/evento deve deduplicar por `messageId`/`CorrelationId` + tipo + versão.
- “Executar passo” deve ser **reentrante**: se receber duplicado, não repetir o efeito.

### Compensações

- Preferir compensações que também sejam idempotentes.
- Se não existir compensação segura (efeito irreversível), modelar como “tarefa manual”/fallback operacional e registrar no estado.

### Timeouts e expiração

- Definir timeout por etapa e transição para estado de falha controlada.
- Não deixar saga “pendurada” indefinidamente; expirar com decisão explícita.

## Anti-exemplos (evitar)

- “Saga” sem estado durável (apenas em memória) para fluxos críticos.
- Usar retry automático em comandos não idempotentes sem deduplicação.
- Misturar orquestração e coreografia sem contrato claro (responsabilidade difusa).

## Pode ser feito

- Implementar saga como máquina de estados (state machine) com transições explícitas.
- Publicar eventos de mudança de estado para observabilidade/monitoramento (sem vazar PII).
- Usar outbox para garantir atomicidade entre gravação de estado e publicação.

## Não pode ser feito

- Depender de transação distribuída (2PC) como premissa padrão.
- Propagar DTOs externos (integração) como estado “canônico” do fluxo.
- Omitir correlação e depois tentar “reconstruir” o fluxo via logs.

