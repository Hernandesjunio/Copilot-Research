---
id: microservice-api-collection-resources-pagination-filters
title: "API — coleções, paginação, filtros, ordenação e compatibilidade"
tags: [microservice, api, pagination, filtering, sorting, versioning, backward-compatibility]
scope: "**/Api/**/*.cs"
priority: medium
kind: reference
---

# Objetivo

Padronizar comportamento de endpoints de coleção (listagens) e evolução de contratos, mantendo performance previsível e compatibilidade retroativa controlada.

## TL;DR

- Paginação explícita por padrão (`page`/`pageSize` **ou** `cursor`); limites máximos obrigatórios no servidor.
- Ordenação apenas por campos whitelist documentados; ordenação padrão estável (incluir desempate por chave).
- Filtros com nomes estáveis; evitar filtros arbitrários tipo “query SQL”.
- Mudanças incompatíveis exigem novo path de versão (`/v2`) ou negociação documentada; nunca quebrar clientes silenciosamente.

## Regras de paginação

- Impor `pageSize <= N` com `N` definido por política (ex.: 100); rejeitar acima do limite com `400` e `ProblemDetails`.
- Para cursores, usar token opaco assinado ou encoding estável; não vazar chaves internas sensíveis.
- Respostas devem incluir metadados mínimos: total (quando barato), próxima página, ou `nextCursor`, conforme estratégia.

## Regras de ordenação e filtros

- `sort` aceita apenas valores enumerados no contrato (ex.: `createdAt`, `-createdAt`).
- Filtros mapeiam para colunas/índices suportados; adicionar novo filtro sem índice exige revisão de performance.
- Não aceitar `sort` livre concatenado em SQL.

## Snippet

```csharp
public sealed record ListagemConsulta(int Page, int PageSize, string? Sort);

public static bool TryValidar(ListagemConsulta q, int maxPageSize, out IDictionary<string, string[]> errors)
{
    errors = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase);
    if (q.Page < 1) errors["page"] = new[] { "page deve ser >= 1" };
    if (q.PageSize is < 1 or > maxPageSize) errors["pageSize"] = new[] { $"pageSize deve estar entre 1 e {maxPageSize}" };
    return errors.Count == 0;
}
```

## Pode ser feito

- Usar projeção/DTO de listagem para não expor entidades de persistência.
- Documentar campos deprecados com período de transição e telemetria de uso.

## Não pode ser feito

- Retornar coleções sem limite em produção.
- Permitir ordenação por campos não indexados sem análise de impacto.
- Reutilizar mesma versão de rota para alterar semântica de campo existente.
