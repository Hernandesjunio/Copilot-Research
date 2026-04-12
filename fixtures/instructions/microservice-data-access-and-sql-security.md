---
id: microservice-data-access-and-sql-security
title: "Dados — acesso seguro, parametrização, transações e timeouts"
tags: [microservice, data, sql, dapper, efcore, security, transactions, performance]
scope: "**/*.cs"
priority: high
kind: policy
---

# Objetivo

Reduzir riscos clássicos (SQL injection, vazamento de detalhes, N+1, queries sem limite) e padronizar acesso a dados em microservices .NET, cobrindo Dapper/SQL direto e diretrizes mínimas para EF Core quando usado.

## TL;DR

- **Toda** consulta/comando SQL deve ser parametrizado; concatenação de valores dinâmicos na SQL é proibida.
- Timeouts explícitos em conexão/comando; pool configurado; não manter transações abertas atravessando I/O externo.
- Transações curtas; UoW explícito quando múltiplos agregados precisam consistência imediata; operações longas usam padrões assíncronos/outbox (ver mensageria).
- Paginação no banco (`OFFSET/FETCH` ou keyset) para listagens; proibir `SELECT *` em caminhos quentes sem justificativa.

## EF Core (quando aplicável)

- Preferir `AsNoTracking()` em leituras; projeções (`Select`) para DTOs em listagens.
- Evitar `Include` em cadeia que gere explosão cartesiana; dividir consultas quando necessário.
- Usar `ExecuteUpdate`/`ExecuteDelete` para operações em massa quando suportado, em vez de carregar entidades inteiras sem necessidade.

## Dapper / SQL direto

- Usar `CommandDefinition` com `CancellationToken` e timeout.
- Nomes de tabela/coluna controlados por whitelist no código, nunca vindos de input do cliente.

## Snippet

```csharp
const string sql = """
    SELECT Id, Nome
    FROM Cliente
    WHERE TenantId = @TenantId AND Ativo = 1
    ORDER BY Id
    OFFSET @Off ROWS FETCH NEXT @Ps ROWS ONLY
    """;

await conn.QueryAsync<ClienteListaDto>(
    new CommandDefinition(sql, new { TenantId = tenantId, Off = offset, Ps = pageSize }, cancellationToken: ct, commandTimeout: 15));
```

## Pode ser feito

- Implementar concorrência otimista com coluna de versão quando o domínio exigir.
- Isolar leituras pesadas em repositório/consulta dedicada com limites e índice revisado.

## Não pode ser feito

- Interpolar input do usuário em SQL (`$" ... {id} ... "`).
- Executar migrações implícitas em runtime de produção a partir do microserviço sem pipeline controlado.
- Expor exceções de provedor SQL ao cliente da API.
