---
id: microservice-caching-imemorycache-policy
title: "Cache — IMemoryCache, chaves, TTL e invalidação"
tags: [microservice, caching, memory-cache, performance]
scope: "**/*.cs"
priority: medium
kind: policy
workspace_evidence_required: true
workspace_signals: [IMemoryCache, AddMemoryCache, MemoryCache, Microsoft.Extensions.Caching.Memory]
on_absence: hypothesis_only
---

# Objetivo

Padronizar uso de `IMemoryCache` em microservices .NET para reduzir pressão em dependências, com regras claras de chave, TTL, invalidação e segurança multi-tenant.

## TL;DR

- Chaves compostas e estáveis: incluir tenant/versão de contrato quando aplicável (`conta:{tenantId}:{id}:v1`).
- TTL curto por padrão; dados sensíveis ou altamente mutáveis não entram em cache compartilhado entre tenants sem isolamento estrito.
- Invalidação explícita em mutações; não depender apenas de TTL para consistência forte sem documentar eventualidade.
- Limitar tamanho de entradas; evitar armazenar coleções grandes ou payloads de integração brutos.

## Snippet

```csharp
public async Task<ContaResposta> ObterContaAsync(string tenantId, string id, CancellationToken ct)
{
    var key = $"conta:{tenantId}:{id}:v1";
    if (_cache.TryGetValue(key, out ContaResposta? cached) && cached is not null)
        return cached;

    var fresh = await _repo.ObterRespostaAsync(tenantId, id, ct);
    _cache.Set(key, fresh, new MemoryCacheEntryOptions
    {
        AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(2),
        Size = 1
    });
    return fresh;
}
```

## Pode ser feito

- Usar `PostEvictionCallbacks` para métricas de eviction quando necessário.
- Combinar cache com stampede protection (`GetOrCreateAsync` com semáforo por chave em hotspots).

## Não pode ser feito

- Cachear tokens, segredos ou PII sem requisito explícito de produto e controles de expiração.
- Usar chave sem `tenantId` em sistemas multi-tenant.
- Tratar cache como fonte de verdade para invariantes financeiras sem política de consistência documentada.
