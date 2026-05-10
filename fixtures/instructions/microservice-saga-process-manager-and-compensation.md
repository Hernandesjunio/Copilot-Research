---
id: microservice-saga-process-manager-and-compensation
title: "Consistência eventual — Saga / Process Manager, compensações e orquestração"
tags: [microservice, saga, process-manager, orchestration, messaging, outbox, consistency, resilience, idempotency, manual-orchestration]
scope: "**/*.cs"
priority: high
kind: policy
owner: <!-- TODO -->
last_reviewed: 2026-05-10
status: active
workspace_evidence_required: true
workspace_signals: [MassTransit, Saga, StateMachine, IBus, RabbitMQ, Outbox, BackgroundService, CancellationTokenSource]
on_absence: hypothesis_only
---

# Objetivo

Fornecer guia reutilizável para coordenar fluxos distribuídos com **consistência eventual**, usando **Sagas / Process Managers** e **compensações**, sem depender de transações distribuídas.

## TL;DR

- Use **orquestração** (process manager) quando há múltiplas etapas e compensações claras; use **coreografia** quando eventos independentes e acoplamento baixo.
- Persistir estado da saga (durável) e tratar **idempotência** em todos os handlers.
- Publicação de mensagens que dependem de escrita no banco: aplicar **Transactional Outbox**.
- Timeouts e retries devem respeitar **não-idempotência**; não “repetir” comandos que geram efeitos irreversíveis sem deduplicação.
- Uma saga pode ser implementada **manualmente no processo** (orquestrador em código, estado em tabela) **sem** MassTransit/NServiceBus/Temporal — bibliotecas listadas em `workspace_signals` são **sinais opcionais** quando o repositório já as usa.

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

## Orquestração manual em processo (sem framework de saga obrigatório)

- Quando não existir biblioteca de saga no serviço, usar um **orquestrador explícito** (serviço/classe de aplicação ou worker) que: lê e grava **estado durável**; invoca passos (HTTP, fila, in-process); e, em falha, executa **compensações na ordem inversa** dos passos já concluídos com sucesso.
- **Ponto de entrada** pode ser um único endpoint HTTP síncrono que dispara o fluxo **ou** um trabalho assíncrono; a escolha é de produto. Passos podem usar **mocks, stubs ou interfaces** configuradas para dev/test — integrações concretas ficam em configuration e instructions locais.
- **Timeout global** do fluxo: usar `CancellationToken` com prazo absoluto ou `CancellationTokenSource.CancelAfter`, persistir transição para estado de falha/expirado e **acionar compensação** sem deixar o fluxo indefinido.
- **Retry por passo** (falhas transitórias): repetir apenas o passo falhado com **intervalo explícito** entre tentativas (sleep/scheduler), limitado por contador e pelo timeout global; não “recomeçar” passos já concluídos sem verificar estado persistido e idempotência.
- **Identificadores** de instância de fluxo (`SagaId` ou correlacionado com o pedido) propagados em logs e eventos internos — alinhado a `microservice-opentelemetry-correlation-and-health` quando aplicável.
- Regras de **negócio** (quantos passos, nomes de etapa, política de rollback) **não** são prescritas aqui — apenas a disciplina de estado, idempotência, compensação e prazos.

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

- Implementar saga como máquina de estados (state machine) com transições explícitas — **em código** ou com biblioteca, conforme o repositório.
- Implementar **orquestrador manual** com tabela de estado (`Status`, `PassoAtual`, `Tentativas`, timestamps) e testes de reentrada/compensação.
- Publicar eventos de mudança de estado para observabilidade/monitoramento (sem vazar PII).
- Usar outbox para garantir atomicidade entre gravação de estado e publicação.

## Não pode ser feito

- Depender de transação distribuída (2PC) como premissa padrão.
- Propagar DTOs externos (integração) como estado “canônico” do fluxo.
- Omitir correlação e depois tentar “reconstruir” o fluxo via logs.
- Assumir que **MassTransit** (ou outro sinal em `workspace_signals`) é obrigatório para todo o serviço — ausência de biblioteca implica orquestração **manual** explícita conforme secção acima.

## Ver também

- `microservice-messaging-rabbitmq-publish-consume` — outbox e consumo idempotente quando há mensageria.
- `microservice-authorization-resource-scope-and-audit` — se o fluxo cruzar com atores e permissões por recurso.

