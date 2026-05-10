---
id: csharp-async-style
title: "Estilo C# — async e nomenclatura"
tags: [csharp, async, naming, style]
scope: "**/*.cs"
priority: medium
kind: reference
owner: <!-- TODO -->
last_reviewed: 2026-05-10
status: active
---

# Objetivo

Definir um padrão consistente para métodos assíncronos em C# (nomenclatura, uso de `async/await` e exceções comuns).

## TL;DR

- Métodos assíncronos terminam em `Async`.
- Evitar `async void` exceto em handlers de UI/eventos documentados.
- `ConfigureAwait(false)` só quando houver diretriz explícita do projeto (muitos serviços ASP.NET Core não precisam).

## Async e nomenclatura

- Métodos assíncronos terminam em `Async`.
- Evitar `async void` exceto em handlers de UI/eventos documentados.
- Usar `ConfigureAwait(false)` apenas onde o guideline do projeto mandar (muitos serviços ASP.NET Core não necessitam).
