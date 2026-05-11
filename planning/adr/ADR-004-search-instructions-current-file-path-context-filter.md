# ADR-004: `search_instructions` com `current_file_path` opcional como evidência contextual de filtro

**Status**: Proposto  
**Data**: 2026-05-10  
**Contexto**: MCP `corporate_instructions_mcp` — tool `search_instructions`  
**Relaciona-se com**: [ADR-002 — Corpus Query Expansion Map](ADR-002-corpus-query-expansion-map.md)

---

## 1. Título (resumo executivo)

Evoluir `search_instructions` **in-place** para aceitar `current_file_path` como **evidência contextual opcional** usada pelo MCP em mecanismos declarativos de aplicabilidade, principalmente `applies_to` do **Corpus Query Expansion Map**, sem leitura do projeto do utilizador, sem `context_mode`, sem BM25 e sem alterar o mecanismo base atual de busca por tokens.

---

## 2. Contexto

`search_instructions` já suporta busca textual com o mecanismo atual de **token scoring** e integração com o **Corpus Query Expansion Map** definido na ADR-002.

Na ADR-002 V1.1, `applies_to` no nível do termo já tem semântica explícita:

- quando `current_file_path` é conhecido, `applies_to` pode **filtrar a expansão**;
- quando `current_file_path` está ausente, `applies_to` é ignorado para evitar falsos negativos em queries gerais.

Hoje, porém, a tool `search_instructions` ainda **não expõe** `current_file_path` no seu contrato público, o que impede o agente/host de fornecer essa evidência contextual diretamente à busca.

---

## 3. Problema

1. A ADR-002 já define comportamento dependente de `current_file_path`, mas `search_instructions` não recebe esse campo.  
2. A ausência do campo obriga a expansão a operar em modo genérico mesmo quando o agente sabe qual ficheiro está em contexto.  
3. O desenho desta evolução precisa evitar um erro de escopo: `current_file_path` **não** deve implicar leitura do workspace do utilizador, verificação de existência física do ficheiro nem inspeção do projeto.  
4. O contrato deve evoluir **in-place**, preservando todos os campos existentes e adicionando apenas a nova evidência contextual necessária.

---

## 4. Decisão

### 4.1 Frase-guia (obrigatória)

> **`current_file_path` em `search_instructions` é evidência contextual opcional fornecida pelo agente/host para filtrar aplicabilidade declarativa do corpus; não é telemetria garantida nem autorização para o MCP ler o projeto do utilizador.**

### 4.2 O que o campo é

`current_file_path` é um **input runtime opcional** que representa o ficheiro actualmente em contexto para a tarefa.

Na V1 desta decisão, esse campo serve para:

- permitir que o MCP aplique a semântica de `applies_to` do **Corpus Query Expansion Map** conforme ADR-002;
- reduzir expansão cruzada indevida quando há evidência suficiente de tipo de artefacto;
- melhorar precisão **sem** trocar o mecanismo base de busca.

### 4.3 O que o campo não é

`current_file_path` **não** significa:

- leitura do ficheiro físico;
- inspeção do repositório do utilizador;
- validação forte de existência no disco;
- descoberta automática garantida pela IDE;
- novo modo semântico de busca;
- substituição de `query`.

### 4.4 `context_mode` fica fora desta ADR

`context_mode` **não** entra neste contrato.

Justificativa:

- nesta iteração, `current_file_path` será usado apenas como evidência para filtros declarativos;
- a tool não passa a ler o ficheiro físico;
- introduzir `context_mode` agora aumentaria o contrato sem acrescentar comportamento determinístico indispensável.

### 4.5 Evolução do contrato: in-place

A tool `search_instructions` deve ser evoluída **no mesmo nome**, preservando o contrato existente e acrescentando um novo argumento opcional:

```python
def search_instructions(
    query: str,
    tags: str | None = None,
    max_results: int = 10,
    include_diagnostics: bool = False,
    tags_mode: str = "any",
    kind: str | None = None,
    scope: str | None = None,
    priority: str | None = None,
    workspace_evidence_required: bool | None = None,
    telemetry_expected_instruction_id: str | None = None,
    queries: list[str] | None = None,
    max_results_per_query: int = 5,
    current_file_path: str | None = None,
) -> str:
```

Regra normativa:

- nenhum parâmetro existente deve mudar de significado nesta ADR;
- `current_file_path` é **aditivo**;
- `query` continua obrigatório no fluxo single-query;
- `queries` + `max_results_per_query` permanecem suportados no fluxo multi-query;
- quando `queries` for usado, um único `current_file_path` vale para a chamada inteira.

### 4.6 Schema aditivo proposto

```json
{
  "current_file_path": {
    "anyOf": [{ "type": "string" }, { "type": "null" }],
    "default": null,
    "description": "Caminho do ficheiro actualmente em contexto para a tarefa. Este valor é usado apenas como evidência contextual para filtros declarativos como applies_to do mapa de expansão. Não invente caminhos e não use este campo para queries gerais sem ficheiro em contexto."
  }
}
```

### 4.7 Semântica operacional

Pipeline normativo desta ADR:

1. Receber `query` e filtros existentes, mais `current_file_path` opcional.  
2. Normalizar `current_file_path` apenas no plano **sintático** (por exemplo separadores, trim, null/vazio).  
3. Se `current_file_path` for utilizável, passá-lo ao pipeline de expansão para que `applies_to` seja avaliado conforme ADR-002.  
4. Manter o mecanismo base atual de **token scoring**.  
5. Retornar resultados normalmente, com diagnóstico opcional quando solicitado.

### 4.8 Limites de validação

Nesta ADR, o MCP **não** deve tentar provar:

- que o ficheiro existe no disco;
- que o path está dentro do workspace do utilizador;
- que o host enviou o ficheiro “certo”.

Em vez disso:

- se o valor for sintaticamente inútil, tratar como ausente;
- não falhar a busca por causa disso;
- quando `include_diagnostics = true`, registar que o path foi ignorado ou considerado ausente.

### 4.9 Relação com ADR-002

Esta ADR **não altera** a semântica já decidida na ADR-002:

- `applies_to` no nível do termo continua a actuar como filtro de precisão **apenas** quando `current_file_path` está disponível;
- com `current_file_path` ausente, `applies_to` continua a ser ignorado para evitar falsos negativos;
- conflitos de contexto e diagnósticos continuam regidos pela ADR-002.

### 4.10 Fora do escopo

Ficam fora desta ADR:

- BM25;
- busca vetorial / RAG;
- `context_mode`;
- `current_directory`;
- `related_file_paths`;
- validação por leitura do workspace do utilizador;
- alteração do significado de `scope` no frontmatter;
- qualquer mudança semântica nos filtros já existentes.

---

## 5. Consequências positivas

- A `search_instructions` passa a conseguir usar a semântica já definida em ADR-002 sem depender de contexto implícito.  
- A expansão contextual fica mais precisa em queries ambíguas com ficheiro em contexto.  
- O MCP continua auditável: usa evidência declarativa, não inferência invisível sobre o projeto.

---

## 6. Consequências negativas / trade-offs

- O host/agente pode omitir `current_file_path`, e a busca continuará em modo genérico.  
- O host/agente pode fornecer um path impreciso; como não há validação forte nesta ADR, o sistema depende de diagnóstico e de uso conservador do campo.  
- O ganho inicial concentra-se na expansão contextual, não em toda a cadeia de ranking.

---

## 7. Critérios de aceite

Esta decisão considera-se implementada quando:

1. `search_instructions` aceitar `current_file_path` como argumento opcional sem quebrar chamadas existentes.  
2. O valor for passado ao pipeline de expansão para avaliação de `applies_to`.  
3. O comportamento continuar alinhado com ADR-002 quando `current_file_path` estiver ausente.  
4. Não houver leitura do repositório do utilizador nem validação por existência física de ficheiro nesta implementação.  
5. `context_mode` não tiver sido introduzido no contrato desta tool.  
6. A documentação da tool explicitar que `current_file_path` é evidência contextual opcional e não deve ser inventado.  
7. Testes automatizados cobrirem a passagem do argumento pela tool até ao motor de expansão.

---

## 8. Referências

- [ADR-002 — Corpus Query Expansion Map](ADR-002-corpus-query-expansion-map.md)  
- `mcp-instructions-server/corporate_instructions_mcp/server.py`  
- `mcp-instructions-server/corporate_instructions_mcp/expansion.py`  
- `mcp-instructions-server/docs/UBIQUITOUS-LANGUAGE-GLOSSARY.md`  
- `fixtures/instructions/instruction-authoring-standard.md`
