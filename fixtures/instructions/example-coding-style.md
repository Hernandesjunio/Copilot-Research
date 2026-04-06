---
id: csharp-async-style
title: "Estilo C# — async e nomenclatura"
tags: [csharp, style, async]
scope: "**/*.cs"
priority: medium
kind: reference
---

# Async e nomenclatura

- Métodos assíncronos terminam em `Async`.
- Evitar `async void` exceto em handlers de UI/eventos documentados.
- Usar `ConfigureAwait(false)` apenas onde o guideline do projeto mandar (muitos serviços ASP.NET Core não necessitam).
