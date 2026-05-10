Vou tratar essa tool como “porta de entrada do catálogo”. A pergunta principal é se listar tudo ajuda o agente a se orientar ou se aumenta ruído, custo cognitivo e decisões ruins.

Thought for a few seconds

Sim. A list_instructions_index é uma tool muito importante no seu desenho atual, porque ela funciona como o catálogo inicial que permite ao agente descobrir quais instructions existem antes de decidir chamar search_instructions ou get_instruction.

Mas do jeito que ela está hoje — sem parâmetros de filtro e listando tudo — ela tem um problema estrutural: ela ajuda no começo, mas pode virar gargalo conforme o corpus cresce.

A análise crítica é: essa tool é útil como visão geral, mas se continuar listando tudo sempre, ela tende a ficar menos eficiente, menos determinística e menos orientada à tarefa. O ideal é evoluí-la de uma “listagem bruta do índice” para uma listagem navegável, filtrável e resumida por intenção.

1. O papel real da list_instructions_index

Pelo que você descreveu, ela é chamada primeiro para responder à pergunta implícita do agente:

“Quais documentos normativos existem disponíveis?”

Hoje ela retorna algo assim:

{
  "id": "artifact-encoding-line-endings-and-unicode",
  "path": "artifact-encoding-line-endings-and-unicode.md",
  "title": "Artefactos — encoding, fim de linha e Unicode",
  "tags": [
    "encoding",
    "utf-8",
    "unicode",
    "markdown",
    "line-endings",
    "repository",
    "interoperability"
  ],
  "scope": "**/*",
  "priority": "medium",
  "kind": "policy",
  "content_sha256": "4283e7f0d1521732e687a54be8e505f097563a31308951c7d42ac761a73580e6"
}

Isso é bom porque retorna metadados leves, não o conteúdo inteiro. Porém, ainda assim, se você tiver 24 arquivos hoje e depois 100, 300 ou 500 instructions, essa listagem começa a virar um mini-dump do catálogo inteiro.

O problema não é técnico de latência. Como você usa STDIO e RAM, provavelmente isso é rápido.

O problema maior é comportamental no agente.

2. O impacto no comportamento do agente Copilot/Cursor

Quando o agente chama list_instructions_index, ele recebe uma lista de documentos. A partir disso, ele precisa decidir:

Quais documentos parecem relevantes.
Quais ids usar em get_instruction.
Se deve chamar search_instructions.
Se deve ignorar tudo e seguir com o conhecimento próprio.

Se a lista for pequena, isso ajuda.

Se a lista for grande, o agente pode:

escolher pelo título mais óbvio;
se perder em tags parecidas;
ignorar instructions importantes;
carregar documents demais;
carregar documents errados;
gastar contexto lendo catálogo;
não chamar search_instructions;
usar a listagem como se fosse fonte suficiente;
tomar decisão superficial baseada só no título.

Ou seja, a tool que deveria orientar pode gerar ruído de navegação.

3. Problema principal: ausência de filtros

A ausência de filtros torna a tool muito genérica.

Hoje a única operação possível é:

listar tudo

Mas o agente geralmente não precisa de tudo. Ele precisa de uma dessas visões:

listar instructions aplicáveis ao arquivo atual
listar instructions por kind
listar instructions por tag
listar instructions por escopo
listar instructions por prioridade
listar instructions globais
listar instructions de arquitetura
listar instructions de implementação
listar instructions relacionadas a testes
listar instructions relacionadas a artifacts
listar instructions relacionadas a FIX
listar instructions relacionadas a RabbitMQ

Sem filtros, o agente precisa fazer esse refinamento mentalmente. E esse é exatamente o tipo de trabalho que você quer tirar da LLM e colocar no MCP.

4. A diferença entre list e search

É importante não transformar list_instructions_index em uma cópia da search_instructions.

Eu separaria assim:

list_instructions_index

Serve para descoberta estruturada do catálogo.

Exemplos:

“quais instructions existem?”
“quais instructions existem para esse arquivo?”
“quais policies existem?”
“quais scopes existem?”
“quais documentos globais existem?”
“quais instructions são high priority?”

Ela deve ser mais determinística e baseada em metadados.

search_instructions

Serve para recuperação por intenção textual.

Exemplos:

“retry em mensageria”
“encoding de artifact”
“padrão de controller”
“resiliência em chamadas HTTP”
“regras de FIX session”

Ela pode usar BM25, expansão, ranking e boosts.

A list_instructions_index não precisa ranquear por BM25. Ela precisa filtrar e organizar.

5. O risco de listar tudo primeiro

A documentação diz:

Use when you need an overview of all available organizational instruction documents (ids, titles, tags).

Essa frase incentiva o agente a usar a tool como primeira chamada para obter visão geral.

Isso faz sentido para um corpus pequeno.

Mas no seu objetivo de escala — vários repositórios, corpus compartilhado, regras por camada, regras globais e normativas — “listar tudo” pode virar antipadrão.

O agente pode desenvolver este fluxo:

1. Sempre chama list_instructions_index.
2. Recebe tudo.
3. Escolhe ids por heurística fraca.
4. Chama get_instruction.
5. Talvez nem use search_instructions.

Esse fluxo pode competir com o fluxo mais robusto:

1. Identifica intenção + arquivo atual.
2. Chama search_instructions com query + current_file_path.
3. Recebe ranking filtrado.
4. Chama get_instruction somente nos ids relevantes.

Então existe um risco: a listagem total pode enfraquecer o uso da busca inteligente.

6. O que eu mudaria na documentação da tool

A documentação atual:

Use when you need an overview of all available organizational instruction documents (ids, titles, tags).

Returns lightweight metadata for every indexed .md file under INSTRUCTIONS_ROOT. Restart the server or
set INSTRUCTIONS_ROOT to a new path to refresh. JSON array of objects.

Eu mudaria para algo mais restritivo e orientado:

Use this tool to inspect the instruction catalog metadata, not to retrieve instruction content.

Prefer `search_instructions` when the user task has a specific intent, query, technology, file path, or implementation goal.

Use this tool when you need a lightweight overview of available instruction documents, available scopes, tags, kinds, priorities, or when you need to select candidate instruction ids before calling `get_instruction`.

When a current file is known, provide `current_file_path` so the server can filter instructions by `scope` or `applies_to`.

Do not call this tool just to solve a specific implementation task if `search_instructions` can be called directly with the task intent.

Essa mudança é importante porque orienta o agente a não transformar a listagem em etapa obrigatória.

7. Parâmetros que eu adicionaria

Eu não deixaria ela sem filtros.

Uma versão inicial simples poderia ser:

{
  "type": "object",
  "properties": {
    "current_file_path": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Caminho relativo ao root do workspace do arquivo atualmente analisado, editado ou criado. Use para filtrar instructions aplicáveis por scope/applies_to. Não invente um caminho."
    },
    "tags": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Lista de tags separadas por vírgula para filtrar o catálogo."
    },
    "tags_mode": {
      "type": "string",
      "enum": ["any", "all"],
      "default": "any"
    },
    "kind": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Filtra por tipo de instruction, como policy, guide, architecture, testing, implementation."
    },
    "scope": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Filtra por escopo declarado da instruction."
    },
    "priority": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null
    },
    "include_global": {
      "type": "boolean",
      "default": true,
      "description": "Inclui instructions globais aplicáveis a qualquer arquivo, como scope **/*."
    },
    "limit": {
      "type": "integer",
      "default": 50,
      "minimum": 1,
      "maximum": 200
    },
    "offset": {
      "type": "integer",
      "default": 0,
      "minimum": 0
    },
    "include_facets": {
      "type": "boolean",
      "default": false,
      "description": "Quando true, retorna agregações de tags, kinds, scopes e priorities disponíveis."
    }
  },
  "required": [],
  "title": "list_instructions_indexArguments"
}

Aqui, o agente ainda pode chamar sem parâmetro para visão geral, mas também pode pedir uma visão reduzida.

8. Melhor ainda: separar list de facets

Uma possibilidade mais profissional seria separar duas responsabilidades:

list_instructions_index

Lista documentos filtrados.

get_instructions_catalog_facets

Retorna o resumo navegável do catálogo:

{
  "total": 24,
  "kinds": {
    "policy": 8,
    "guide": 6,
    "architecture": 4,
    "testing": 3,
    "implementation": 3
  },
  "priorities": {
    "high": 5,
    "medium": 14,
    "low": 5
  },
  "scopes": {
    "**/*": 6,
    "src/Application/**/*.cs": 4,
    "src/Infrastructure/**/*.cs": 5,
    "src/Api/**/*.cs": 3
  },
  "tags": {
    "repository": 6,
    "encoding": 2,
    "testing": 5,
    "rabbitmq": 3,
    "fix": 4
  }
}

Essa tool seria extremamente útil para o agente entender o corpus sem receber todos os documentos.

Porém, se você quiser manter simples, pode incluir include_facets na própria list_instructions_index.

9. O campo scope atual parece ambíguo

No seu exemplo:

"scope": "**/*"

Isso parece estar sendo usado como padrão de aplicação por arquivo.

Mas semanticamente, scope pode significar várias coisas:

escopo arquitetural;
glob pattern;
camada;
domínio;
abrangência;
aplicabilidade.

Se scope é um glob, talvez o nome mais claro seja:

applies_to:
  - "**/*"

E scope poderia ser algo mais conceitual:

scope: global

Exemplo melhor:

{
  "id": "artifact-encoding-line-endings-and-unicode",
  "path": "artifact-encoding-line-endings-and-unicode.md",
  "title": "Artefactos — encoding, fim de linha e Unicode",
  "tags": [
    "encoding",
    "utf-8",
    "unicode",
    "markdown",
    "line-endings",
    "repository",
    "interoperability"
  ],
  "scope": "global",
  "applies_to": ["**/*"],
  "priority": "medium",
  "kind": "policy",
  "content_sha256": "4283e7f0d1521732e687a54be8e505f097563a31308951c7d42ac761a73580e6"
}

Isso ajudaria muito o agente.

Porque scope: "**/*" é útil para máquina, mas pouco semântico para LLM.

Já scope: "global" é muito mais claro.

10. O que eu adicionaria no retorno

Hoje o retorno está bom, mas eu adicionaria alguns campos.

Retorno recomendado
{
  "id": "artifact-encoding-line-endings-and-unicode",
  "path": "artifact-encoding-line-endings-and-unicode.md",
  "title": "Artefactos — encoding, fim de linha e Unicode",
  "summary": "Regras para garantir compatibilidade de artefatos textuais usando UTF-8, finais de linha consistentes e cuidados com Unicode.",
  "tags": [
    "encoding",
    "utf-8",
    "unicode",
    "markdown",
    "line-endings",
    "repository",
    "interoperability"
  ],
  "scope": "global",
  "applies_to": ["**/*"],
  "priority": "medium",
  "kind": "policy",
  "audience": ["agent", "developer"],
  "recommended_when": [
    "gerar arquivos markdown",
    "alterar artefatos textuais",
    "criar documentação",
    "normalizar encoding"
  ],
  "content_sha256": "4283e7f0d1521732e687a54be8e505f097563a31308951c7d42ac761a73580e6"
}

O campo mais importante aqui é summary.

Sem summary, o agente decide por:

título;
tags;
kind;
scope.

Com summary, ele entende melhor quando usar aquela instruction.

11. Cuidado para não retornar metadados demais

Apesar da sugestão acima, existe um equilíbrio.

A list_instructions_index deve continuar leve.

Eu evitaria retornar:

conteúdo completo;
trechos longos;
regras completas;
exemplos grandes;
histórico;
diagnósticos extensos por padrão.

A listagem deve responder:

“O que existe e quando talvez deva ser carregado?”

Não deve responder:

“Qual é a regra completa?”

Isso continua sendo responsabilidade de get_instruction.

12. Fluxo ideal entre as três tools

Hoje você tem três tools básicas:

list_instructions_index
search_instructions
get_instruction

O fluxo ideal deveria ser:

Tarefa genérica ou exploração:
1. list_instructions_index com filtros/facets
2. search_instructions se houver intenção específica
3. get_instruction para carregar conteúdo selecionado

Tarefa específica de implementação:
1. search_instructions com query + current_file_path
2. get_instruction dos top ids
3. opcionalmente list_instructions_index apenas se a busca não encontrar bons resultados

Tarefa de auditoria ou revisão:
1. list_instructions_index por kind/scope/priority
2. get_instruction de policies relevantes
3. search_instructions para tópicos específicos

O ponto crítico: não force o agente a listar tudo antes de buscar.

13. Como eu reescreveria a descrição da tool

Uma descrição mais forte para o agente seria:

"""
Use this tool to inspect the lightweight metadata catalog of available instruction documents.

This tool is intended for catalog discovery, filtering by metadata, and selecting candidate instruction ids.
It does not return instruction content.

Prefer `search_instructions` when the task has a specific implementation intent, technology, error, pattern, or current file path.

Use filters such as current_file_path, tags, kind, scope, and priority whenever possible to avoid listing unrelated instructions.

When current_file_path is provided, the server may return only instructions whose applies_to/scope metadata matches the file, plus global instructions.

Call `get_instruction` or `get_instructions_batch` only after selecting relevant ids.
"""

Essa documentação tende a influenciar o agente melhor do que “returns every indexed .md file”.

14. O problema de “overview of all available”

A frase:

overview of all available organizational instruction documents

parece inofensiva, mas pode induzir o agente a sempre buscar tudo.

Eu trocaria por:

overview of relevant available organizational instruction documents

ou:

filtered overview of the instruction catalog

A diferença é sutil, mas importante para comportamento de agente.

Você quer que ele pense em relevância, não em dump global.

15. Estratégia de compatibilidade

Como você já tem a tool funcionando, eu não quebraria o contrato de uma vez.

Faria evolução incremental:

Versão atual
{}

Lista tudo.

Versão evoluída compatível
{
  "current_file_path": null,
  "tags": null,
  "kind": null,
  "scope": null,
  "priority": null,
  "limit": 50,
  "offset": 0,
  "include_facets": false
}

Se nenhum filtro for informado, mantém comportamento antigo.

Mas a documentação passa a recomendar filtros.

16. O que isso influencia no agente

Com filtros, o agente tende a fazer chamadas mais qualificadas.

Antes:

{}

Depois:

{
  "current_file_path": "src/Infrastructure/RabbitMq/Consumers/OrderConsumer.cs",
  "include_global": true
}

Ou:

{
  "kind": "policy",
  "priority": "high",
  "include_facets": true
}

Ou:

{
  "tags": "encoding,markdown",
  "tags_mode": "any"
}

Isso muda o comportamento do agente porque o contrato deixa claro que o catálogo pode ser explorado por dimensões.

Na prática, o agente passa a ter mais chance de pensar:

“Não preciso listar tudo. Posso pedir só as instructions aplicáveis a esse arquivo.”

Esse é o mesmo princípio do current_file_path na search_instructions.

17. O maior risco: sobreposição com search_instructions

Se você adicionar muitos filtros e ranking na list_instructions_index, ela pode virar uma segunda busca.

Eu manteria a distinção:

Tool	Responsabilidade
list_instructions_index	Catálogo filtrado por metadados
search_instructions	Busca textual/ranking por intenção
get_instruction	Conteúdo completo de um documento
get_instructions_batch	Conteúdo de vários documentos selecionados

A list_instructions_index não deveria usar BM25. No máximo, ordenação por:

prioridade;
path match;
kind;
título;
id.
18. Melhor retorno quando houver filtro por arquivo

Se o agente chamar:

{
  "current_file_path": "src/Trading/Fix/Parser.cs"
}

A resposta poderia incluir o motivo:

{
  "total": 3,
  "items": [
    {
      "id": "fix-parser-policy",
      "title": "FIX — regras para parser",
      "kind": "policy",
      "scope": "fix",
      "applies_to": ["src/**/Fix/**/*.cs"],
      "match_reason": "applies_to matched current_file_path",
      "priority": "high"
    },
    {
      "id": "artifact-encoding-line-endings-and-unicode",
      "title": "Artefactos — encoding, fim de linha e Unicode",
      "kind": "policy",
      "scope": "global",
      "applies_to": ["**/*"],
      "match_reason": "global instruction",
      "priority": "medium"
    }
  ]
}

Esse match_reason ajuda muito o agente a escolher.

19. Diagnóstico resumido

Assim como em search_instructions, eu adicionaria diagnóstico opcional.

Exemplo:

{
  "total_indexed": 24,
  "total_returned": 5,
  "filters_applied": {
    "current_file_path": "src/Trading/Fix/Parser.cs",
    "kind": null,
    "tags": null,
    "priority": null
  },
  "facets": {
    "kinds": {
      "policy": 3,
      "guide": 2
    },
    "priorities": {
      "high": 2,
      "medium": 3
    }
  },
  "items": []
}

Mas eu deixaria isso opcional para não poluir.

20. Minha recomendação principal

Eu evoluiria a list_instructions_index para aceitar filtros, mas mantendo compatibilidade.

A melhor primeira versão seria:

{
  "type": "object",
  "properties": {
    "current_file_path": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Caminho relativo ao root do workspace usado para listar instructions aplicáveis por applies_to/scope. Não invente um caminho."
    },
    "tags": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Tags separadas por vírgula para filtrar o catálogo."
    },
    "tags_mode": {
      "type": "string",
      "enum": ["any", "all"],
      "default": "any"
    },
    "kind": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null
    },
    "scope": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null
    },
    "priority": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null
    },
    "include_global": {
      "type": "boolean",
      "default": true
    },
    "limit": {
      "type": "integer",
      "default": 50,
      "minimum": 1,
      "maximum": 200
    },
    "offset": {
      "type": "integer",
      "default": 0,
      "minimum": 0
    },
    "include_facets": {
      "type": "boolean",
      "default": false
    },
    "include_diagnostics": {
      "type": "boolean",
      "default": false
    }
  },
  "required": [],
  "title": "list_instructions_indexArguments"
}
21. Avaliação crítica final

A tool atual é boa para uma primeira versão, mas tem estas limitações:

Aspecto	Avaliação
Listar metadados leves	Bom
Não carregar conteúdo completo	Correto
Não ter filtros	Frágil para escala
Ser chamada primeiro	Útil em corpus pequeno, arriscado em corpus grande
Retornar tags, kind, scope e priority	Bom
Não retornar summary	Limitação importante
Não diferenciar scope de applies_to	Ambiguidade semântica
Não aceitar current_file_path	Perde chance de filtro determinístico
Não ter facets	Dificulta visão geral inteligente
Não ter paginação/limit	Risco futuro
Não ter match_reason	Reduz explicabilidade

Minha conclusão:

A list_instructions_index deve deixar de ser apenas “listar tudo” e virar uma tool de descoberta controlada do catálogo normativo.

Ela não precisa ser complexa. Mas precisa permitir que o agente peça:

“mostre o que é aplicável a este arquivo”

em vez de receber:

“aqui está tudo que existe”

Para o seu MCP, essa evolução é muito coerente. Ela mantém a arquitetura simples de três tools, mas torna a navegação mais determinística, reduz ruído e melhora a chance de o agente chamar get_instruction somente para documentos realmente relevantes.