---
id: microservice-testing-strategy-unit-integration-contract
title: "Testes — unidade, integração, contrato e cenários negativos"
tags: [microservice, testing, xunit, integration, contract, quality]
scope: "**/*Tests/**/*.cs"
priority: medium
kind: policy
---

# Objetivo

Definir estratégia mínima de testes para microservices .NET que cubra domínio, infraestrutura e contratos HTTP/mensageria, priorizando comportamento e regressão sobre métricas ilusórias de cobertura.

## TL;DR

- **Unitários**: `Dominio` puro com mocks/fakes de interfaces; foco em regras e invariantes.
- **Integração**: repositório com banco real (container/testcontainer) ou em memória somente quando representativo; `WebApplicationFactory` para pipeline HTTP.
- **Contrato**: validação de schema OpenAPI ou pactos de consumidor/provedor quando houver múltiplos times.
- **Negativos**: timeouts, `5xx` de dependência, validação `400`, regras `422`, autorização `403`.

## Snippet

```csharp
public sealed class ContaServicoTests
{
    [Fact]
    public async Task Nao_deve_creditar_conta_encerrada()
    {
        var repo = new FakeContaRepo(conta: new Conta(id: "1", estado: EstadoConta.Encerrada));
        var svc = new CreditoServico(repo);
        await Assert.ThrowsAsync<BusinessRuleException>(() => svc.CreditarAsync("1", 10m, CancellationToken.None));
    }
}
```

## Pode ser feito

- Builders de dados para reduzir ruído em testes (`ContaBuilder`).
- Testes de resiliência com simuladores de latência/falha (Testcontainers + toxiproxy) para integrações críticas.

## Não pode ser feito

- Depender de ordem de execução entre testes ou estado global mutável.
- Mockar tudo de forma que o teste não valide comportamento real (ex.: mock do `DbContext` no lugar de teste de integração quando a query importa).
- Perseguir 100% de cobertura sem ganho (código trivial, auto-properties).
