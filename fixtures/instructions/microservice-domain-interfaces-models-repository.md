---
id: microservice-domain-interfaces-models-repository
title: "Dominio, Interfaces, Modelo e Repositorio — contrato e implementação"
tags: [microservice, domain, interfaces, models, repository, dapper, table-storage]
scope: "**/*.cs"
priority: high
kind: reference
---

# Objetivo

Definir fronteiras claras entre `Dominio`, `Interfaces`, `Modelo` e `Repositorio` para preservar testabilidade, clareza de contrato e flexibilidade de infraestrutura.

## TL;DR

- `Dominio` depende apenas de abstrações (`Interfaces`) e modelos de negócio.
- `Interfaces` contém contratos puros, sem implementação.
- `Modelo` separa DTOs por contexto de entrada, saída e integração.
- `Repositorio` implementa contratos com Dapper e/ou Table Storage.

## Regras por camada

- `Dominio`
  - Implementa casos de uso e validações de negócio.
  - Orquestra repositórios/serviços externos por interfaces.
- `Interfaces`
  - Declara `IRepositorioEspecifico`, `IServicoDominio`, `IGatewayIntegracao`, etc.
  - Contratos assíncronos, com `CancellationToken`.
- `Modelo`
  - `Requisicao`: contrato de entrada da API.
  - `RequisicaoIntegracao`: contrato enviado para API externa.
  - `Resposta`: contrato de saída para consumidor.
  - `RespostaRequisicaoIntegracao`: retorno bruto/mapeado da integração.
- `Repositorio`
  - Dapper para consultas/comandos SQL com query parametrizada.
  - Table Storage para cenários NoSQL/chave-valor conforme necessidade.

## Snippet

```csharp
public interface IContaRepositorio
{
    Task<Conta?> ObterPorIdAsync(string id, CancellationToken ct);
}

public sealed class ContaRepositorioDapper : IContaRepositorio
{
    private readonly IDbConnectionFactory _connectionFactory;
    public ContaRepositorioDapper(IDbConnectionFactory connectionFactory) => _connectionFactory = connectionFactory;

    public async Task<Conta?> ObterPorIdAsync(string id, CancellationToken ct)
    {
        const string sql = "SELECT Id, Numero, Saldo FROM Conta WHERE Id = @Id";
        using var conn = await _connectionFactory.CreateOpenConnectionAsync(ct);
        return await conn.QuerySingleOrDefaultAsync<Conta>(new CommandDefinition(sql, new { Id = id }, cancellationToken: ct));
    }
}
```

## Pode ser feito

- Mapear modelos de integração para modelos internos antes de aplicar regra de negócio.
- Criar repositórios específicos por agregado/caso de uso.
- Cobrir domínio com testes unitários usando mocks/fakes das interfaces.

## Não pode ser feito

- Chamar Dapper/Table Storage diretamente a partir de `Dominio`.
- Acoplar contrato de `Interfaces` a detalhes de banco (query, tabela, provider).
- Reutilizar `RespostaRequisicaoIntegracao` como resposta pública sem adaptação.
