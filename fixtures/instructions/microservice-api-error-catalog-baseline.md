---
id: microservice-api-error-catalog-baseline
title: "API — catálogo base de erros HTTP e referências"
tags: [microservice, api, errors, http, status-codes, problem-details, catalog]
scope: "**/Api/**/*.cs"
priority: medium
kind: reference
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Centralizar o **mapeamento canónico** de códigos HTTP mais usados em microservices, com ponte para instructions detalhadas, evitando definições divergentes entre documentos.

## Uso deste catálogo

- **Semântica de verbos, idempotência, rotas:** `microservice-rest-http-semantics-and-status-codes`.
- **`400` vs `422`, exceções de domínio, ProblemDetails vs envelope:** `microservice-api-validation-and-error-contracts`.
- **Camada Api, documentação, envelope de resposta, erros globais:** `microservice-api-openfinance-patterns` (perfil envelope + exemplos).

## Tabela de referência rápida

| Status | Uso típico | Onde aprofundar |
| --- | --- | --- |
| `200` | Sucesso com corpo | REST |
| `201` | Criação concluída | REST |
| `202` | Aceite, processamento assíncrono | REST |
| `204` | Sucesso sem corpo; semântica de `DELETE` idempotente conforme contrato | REST; política de ausência |
| `400` | Entrada inválida, binding, formato | Validação |
| `401` | Não autenticado | REST |
| `403` | Autenticado, sem permissão | REST |
| `404` | Recurso inexistente; operações de escrita com id desconhecido (salvo política de mascaramento) | REST; Validação |
| `408` | Timeout de pedido (quando exposto contratualmente) | REST; resiliência |
| `409` | Conflito de estado / duplicidade / invariante | REST; Validação |
| `412` | Pré-condição (ETag, versão) falhou | REST; Validação |
| `415` | `Content-Type` não suportado | REST |
| `422` | Regra de negócio com payload bem formado | Validação |
| `429` | Limite de taxa | REST |
| `500` | Falha interna inesperada | REST; tratamento global |
| `502`/`503`/`504` | Dependência ou gateway | REST; resiliência |

## Pode ser feito

- Estender este catálogo com códigos de erro de **negócio** estáveis (`code` em extensões) mantendo baixa cardinalidade para métricas.

## Não pode ser feito

- Definir neste ficheiro regras de produto ou de domínio (ex.: mensagens legais específicas); isso permanece em instructions nativas ou policies de produto.
