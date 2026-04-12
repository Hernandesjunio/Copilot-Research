---
id: microservice-architecture-layering
title: "Microservice .NET — arquitetura por camadas"
tags: [microservice, dotnet, architecture, layering, clean-architecture]
scope: "**/*.cs"
priority: high
kind: reference
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Definir a organização padrão de microservices .NET por camadas para manter baixo acoplamento, evolução segura e código previsível entre equipes.

## TL;DR

- Separar responsabilidades em `Api`, `Dominio`, `Interfaces`, `Modelo` e `Repositorio`.
- `Api` orquestra entrada/saída e cross-cutting; regra de negócio fica no `Dominio`.
- Dependências devem apontar para dentro (princípio da Clean Architecture).
- Contratos ficam em `Interfaces`; implementações em `Repositorio`/`Api`.

## Estrutura recomendada

- `Api`
  - Controllers/Minimal APIs.
  - Tratamento global de erro reutilizável.
  - Serialização e retorno conforme **contrato público** (JSON direto, `ProblemDetails` ou envelope organizacional — ver `microservice-api-openfinance-patterns`).
  - Configuração por `IOptions`/`IOptionsSnapshot`.
  - Registro de DI e demais configurações via extension methods.
- `Dominio`
  - Casos de uso, regras de negócio, validações de domínio e invariantes.
- `Interfaces`
  - Contratos de serviços, gateways e repositórios.
- `Modelo`
  - `Requisicao`: entrada do consumidor.
  - `RequisicaoIntegracao`: payload enviado para integrações externas.
  - `Resposta`: saída pública para consumidor.
  - `RespostaRequisicaoIntegracao`: payload recebido de integração.
- `Repositorio`
  - `IRepository` específico com Dapper para banco relacional.
  - Implementação para Table Storage quando aplicável.

## Snippet

```csharp
// Program.cs (Api)
var builder = WebApplication.CreateBuilder(args);
builder.Services
    .AddApiExtensions(builder.Configuration)
    .AddDomainExtensions()
    .AddRepositoryExtensions(builder.Configuration);

var app = builder.Build();
app.UseGlobalExceptionHandling();
app.MapEndpoints();
app.Run();
```

## Pode ser feito

- Criar extension methods por camada (`AddApiExtensions`, `AddDomainExtensions`, etc.).
- Definir contratos no projeto de `Interfaces` e implementar no `Repositorio`.
- Usar DTOs separados por contexto (`Requisicao`, `Resposta`, etc.).
- Manter `Dominio` sem dependência de frameworks de infraestrutura.

## Não pode ser feito

- Colocar regra de negócio em controller, endpoint ou repository.
- Compartilhar entidades de persistência diretamente como contrato público de API.
- Acoplar `Dominio` a Dapper, Table Storage, HTTP clients ou detalhes de framework.
- Misturar DTO de integração externa com DTO público do consumidor.
