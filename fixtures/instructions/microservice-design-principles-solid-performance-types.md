---
id: microservice-design-principles-solid-performance-types
title: "Design — SOLID, coesão, generics e performance de tipos"
tags: [microservice, solid, design, performance, generics, csharp]
scope: "**/*.cs"
priority: medium
kind: reference
---

# Objetivo

Orientar decisões de design em microservices .NET para manter código legível, extensível e eficiente, aplicando SOLID com pragmatismo e evitando custos desnecessários de alocação, boxing e abstração especulativa.

## TL;DR

- **S** interfaces pequenas; **O** extensão por composição; **L** substituibilidade real de implementações; **I** segregação para não forçar métodos vazios; **D** depender de abstrações nas fronteiras (domínio → interfaces).
- `KISS`/`YAGNI`: não criar camadas ou padrões sem necessidade demonstrada; `DRY` não justifica acoplamento oculto.
- Evitar `object`, `Enum` em APIs quentes sem necessidade, e coleções não genéricas que causem boxing.
- Usar **generics** quando houver reuso real (`Repository<T>` só se invariantes forem idênticas; preferir repositórios explícitos por agregado na maioria dos casos).

## Generics — critério de uso

- Adotar generic quando reduz duplicação **e** mantém contratos claros (`Result<T>`, `PagedResult<TItem>`, policies genéricas internas).
- Evitar generic quando esconde regras diferentes por tipo (`where T : class` com comportamentos divergentes via `if (typeof...)`).

## Performance de tipos

- Preferir `readonly struct` para tipos de valor pequenos e efêmeros somente quando medição ou modelo de dados justificar (cuidado com cópias).
- Usar `ArrayPool<T>`/`Span<T>` apenas em hotspots comprovados; não micro-otimizar em todo o código.

## Snippet

```csharp
// Bom: resultado explícito sem exceção de fluxo normal
public sealed record Resultado<T>(bool Ok, T? Valor, string? CodigoErro);

// Evitar: API pública baseada em object
public Task<object> ExecutarAsync(string nomeOperacao, object payload); // proibido salvo interoperabilidade documentada
```

## Pode ser feito

- Extrair interfaces estáveis nas fronteiras de teste (ports) mantendo implementações simples.
- Documentar invariantes de agregados no próprio modelo de domínio (métodos de fábrica).

## Não pode ser feito

- Reflection em caminho quente para “magia” de mapeamento sem cache de delegates.
- Herança profunda só para reuso de código; preferir composição.
- Introduzir pipeline genérico complexo para um único caso de uso.
