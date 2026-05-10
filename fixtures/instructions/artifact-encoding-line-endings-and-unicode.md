---
id: artifact-encoding-line-endings-and-unicode
title: "Artefactos — encoding, fim de linha e Unicode"
tags: [encoding, utf-8, unicode, markdown, line-endings, git, editorconfig, gitattributes, interoperability]
scope: "**/*"
priority: medium
kind: policy
owner: platform-architecture
last_reviewed: 2026-04-12
status: active
---

# Objetivo

Definir regras mínimas e reutilizáveis para ficheiros de texto no repositório (Markdown, YAML, JSON, código-fonte), evitando diffs ruidosos, problemas de CI entre Windows e Linux e ambiguidade para assistentes de código.

## TL;DR

- Texto fonte: **UTF-8 sem BOM**, salvo exceção explícita de ferramenta legada documentada no repositório.
- Fim de linha: **LF** em repositórios servidos por Git em ambientes mistos; alinhar ao `.gitattributes` do projeto se existir.
- Markdown e código: usar caracteres Unicode normais (acentos, símbolos) quando legível; evitar substituir sistematicamente por entidades HTML em ficheiros fonte.
- Nomes de caminhos: ASCII preferível para novos artefactos; se usar Unicode, validar suporte em pipelines e SO alvo.

## Tabela de decisão

| Tipo de ficheiro | Encoding | BOM | Fim de linha |
| --- | --- | --- | --- |
| `.cs`, `.md`, `.json`, `.yml`, `.yaml`, `.csproj` | UTF-8 | Não | LF (preferido) |
| Scripts shell (`.sh`) | UTF-8 | Não | LF |
| Scripts Windows legados (`.bat`, `.ps1` quando exigido) | UTF-8 | Evitar BOM salvo necessidade documentada | CRLF apenas se contrato do repo mandar |

## Pode ser feito

- Configurar `.editorconfig` com `charset = utf-8` e `end_of_line = lf` para conjuntos de extensões acordados.
- Normalizar aspas tipográficas em documentação quando o doc for gerado ou copiado de processadores de texto; em código e contratos máquina, preferir ASCII (`'` `"`) onde o compilador o exigir.
- Documentar exceções pontuais (ex.: ficheiro de recursos com encoding herdado) num comentário ou ADR curta.

## Não pode ser feito

- Misturar BOM e sem-BOM no mesmo tipo de ficheiro sem regra explícita.
- Commitar ficheiros com fins de linha mistos no mesmo ficheiro.
- Usar caracteres de controlo ou separadores inválidos em nomes de ficheiro (`< > : " / \ | ? *` no Windows; respeitar limites de caminho).

## Anti-exemplos

- Marcar o repositório como UTF-8 mas abrir e gravar com encoding regional implícito que corrompe caracteres acentuados.
- Forçar CRLF globalmente num mono-repo que só corre em Linux em CI, gerando ruído permanente em PRs.

## Impacto esperado na resposta da IA

- Gerar e editar artefactos sempre em **UTF-8 sem BOM** e **LF** salvo instrução nativa do repositório em sentido contrário.
- Ao criar nomes de ficheiro ou pasta, preferir **kebab-case** ou convenção já usada no repo, sem caracteres problemáticos para URLs ou shells.

## Quando explicitar incerteza

- Se o repositório não tiver `.editorconfig` nem `.gitattributes` visíveis, declarar a suposição (UTF-8/LF) como convenção sugerida e convidar a confirmar com a equipa.
