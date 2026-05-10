Vou analisar essa tool como a etapa de “hidratação” do contexto: depois que o agente escolhe os ids, ela decide quanto conteúdo entra no prompt e com qual granularidade. Aqui o risco principal não é encontrar o documento errado, mas carregar conteúdo demais, de menos ou em formato difícil para o agente usar.

Thought for a couple of seconds

A get_instructions_batch é provavelmente a tool mais sensível das três, porque ela é a que coloca conteúdo real dentro do contexto do agente.

Enquanto:

list_instructions_index = descoberta do catálogo
search_instructions = seleção/ranking de candidatos
get_instructions_batch = materialização do contexto normativo

Ou seja, se list ou search forem ruins, o agente pode selecionar mal. Mas se get_instructions_batch for ruim, ele pode receber conteúdo demais, truncado de forma perigosa, seções erradas ou um formato que dificulta seguir as regras.

A análise crítica é: a ideia da tool é muito boa, principalmente por aceitar vários ids de uma vez, mas o contrato atual tem pontos frágeis que podem limitar bastante o uso por Copilot/Cursor.

1. O papel real da get_instructions_batch

Essa tool responde à pergunta:

“Agora que já sei quais instructions são relevantes, carregue o conteúdo delas para eu aplicar na tarefa.”

Ela evita chamadas repetidas como:

get_instruction(id1)
get_instruction(id2)
get_instruction(id3)

E permite um fluxo mais eficiente:

search_instructions -> top ids
get_instructions_batch -> conteúdo consolidado

Isso é bom para STDIO, para redução de overhead e para comportamento do agente.

Mas ela precisa ser muito bem desenhada porque é o ponto onde você controla:

volume de tokens;
granularidade do contexto;
ordem dos documentos;
preservação de regras;
truncamento;
seções relevantes;
rastreabilidade;
frontmatter;
conteúdo normativo aplicado.
2. Problema 1: ids como string separada por vírgula

O contrato atual usa:

{
  "ids": "id1,id2,id3"
}

Funciona, mas não é o ideal.

Para agente e para schema, o mais correto seria:

{
  "ids": ["id1", "id2", "id3"]
}

Por quê?

Porque ids é naturalmente uma coleção.

Com string separada por vírgula, você cria pequenos problemas:

precisa fazer parse manual;
pode vir espaço depois da vírgula;
pode vir vírgula duplicada;
pode vir id inválido misturado;
o agente pode mandar quebra de linha;
fica menos claro para o modelo que é uma lista;
dificulta validação de quantidade mínima/máxima;
dificulta mensagens de erro por item.

Exemplo problemático:

{
  "ids": " artifact-encoding-line-endings-and-unicode, csharp-async-style,"
}

Você precisa tratar trim, item vazio e duplicado.

Minha recomendação:

{
  "ids": {
    "type": "array",
    "items": { "type": "string" },
    "minItems": 1,
    "maxItems": 10,
    "description": "Lista de ids de instructions a carregar. Use ids retornados por list_instructions_index ou search_instructions."
  }
}

Para compatibilidade, você pode aceitar os dois formatos temporariamente:

{
  "ids": {
    "anyOf": [
      { "type": "array", "items": { "type": "string" } },
      { "type": "string" }
    ]
  }
}

Mas internamente eu normalizaria para array.

3. Problema 2: saída como result contendo JSON string

Esse é um ponto importante.

Você disse:

A saída é um objeto JSON com result string obrigatório, e o result contém um JSON string com os itens retornados.

Ou seja, algo assim:

{
  "result": "[{\"id\":\"...\",\"body\":\"...\"}]"
}

Isso é ruim para uso por agente.

O ideal seria o outputSchema retornar JSON estruturado de verdade:

{
  "items": [
    {
      "id": "artifact-encoding-line-endings-and-unicode",
      "frontmatter": {},
      "content": "...",
      "truncated": false
    }
  ]
}

Quando você coloca JSON dentro de string, você cria problemas:

o agente precisa interpretar JSON serializado dentro de JSON;
aspas e quebras de linha ficam escapadas;
fica pior de ler;
dificulta validação;
dificulta inspeção;
aumenta chance de o agente tratar o conteúdo como texto bruto;
reduz a utilidade do schema;
atrapalha ferramentas futuras que queiram consumir a resposta programaticamente.

A melhor saída é:

{
  "items": [...],
  "errors": [...],
  "diagnostics": {...}
}

Se o MCP ou SDK atual força result como string, tudo bem, mas conceitualmente isso é inferior. Nesse caso, eu faria o result ser Markdown estruturado, não JSON serializado. Mas se você controla o schema, prefira objeto estruturado.

4. Problema 3: max_chars_per_instruction é útil, mas perigoso

O campo:

{
  "max_chars_per_instruction": 8000
}

é importante para controlar token, mas pode gerar um problema sério: truncamento cego.

Se uma instruction normativa tem uma regra importante depois dos 8000 caracteres, ela pode ser cortada.

Pior: o agente pode não perceber que foi cortada.

Então toda resposta deveria informar, por item:

{
  "truncated": true,
  "original_char_count": 12400,
  "returned_char_count": 8000
}

E, idealmente:

{
  "truncation_reason": "max_chars_per_instruction"
}

Sem isso, o agente pode aplicar uma regra incompleta como se fosse completa.

Minha sugestão: manter max_chars_per_instruction, mas sempre retornar metadados de truncamento.

5. Problema 4: section_contains é bom, mas pode ser frágil

O campo:

{
  "section_contains": "retry"
}

pode ser muito útil para carregar só seções relevantes.

Mas ele tem ambiguidades:

busca no título da seção?
busca no corpo?
busca em ambos?
case-sensitive?
suporta acento?
suporta múltiplos termos?
retorna a seção inteira?
retorna subseções?
retorna headings pais?
o que acontece se não encontrar seção?

Por exemplo, se o documento tem:

## Política de retentativa

### Backoff exponencial

### Retry-After

E o agente manda:

{
  "section_contains": "retry"
}

Pode não encontrar nada se o texto estiver em português como “retentativa”.

Então section_contains é útil, mas não deveria ser o único mecanismo de recorte.

Eu consideraria evoluir para:

{
  "sections": ["Retentativa", "Backoff", "Retry-After"]
}

ou:

{
  "section_query": "retry backoff retry-after retentativa"
}

Mas, para manter simples, section_contains pode continuar, desde que você documente exatamente como funciona.

6. Problema 5: include_headings e headings_only podem conflitar

Você tem:

{
  "include_headings": true,
  "headings_only": false
}

Esses dois campos são úteis, mas podem gerar combinações confusas.

Exemplo:

{
  "include_headings": false,
  "headings_only": true
}

O que acontece?

Se headings_only = true, naturalmente você precisa retornar headings. Então include_headings = false perde sentido.

Eu simplificaria o contrato com um campo único:

{
  "mode": "full"
}

Com enum:

{
  "mode": {
    "type": "string",
    "enum": ["full", "headings_only", "sections"]
  }
}

Ou:

{
  "content_mode": {
    "type": "string",
    "enum": ["full", "headings_only", "matching_sections", "summary_plus_headings"],
    "default": "full"
  }
}

Isso é mais fácil para o agente entender.

Em vez de raciocinar sobre duas flags booleanas, ele escolhe um modo.

7. Melhor contrato sugerido

Uma versão mais robusta seria:

{
  "type": "object",
  "properties": {
    "ids": {
      "anyOf": [
        {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1,
          "maxItems": 10
        },
        {
          "type": "string"
        }
      ],
      "description": "Ids das instructions a carregar. Prefira array de strings. Aceita string separada por vírgula por compatibilidade."
    },
    "max_chars_per_instruction": {
      "type": "integer",
      "default": 8000,
      "minimum": 500,
      "maximum": 30000,
      "description": "Limite máximo de caracteres retornados por instruction. A resposta deve indicar se houve truncamento."
    },
    "content_mode": {
      "type": "string",
      "enum": [
        "full",
        "headings_only",
        "matching_sections",
        "summary_plus_headings"
      ],
      "default": "full",
      "description": "Controla a granularidade do conteúdo retornado."
    },
    "section_contains": {
      "anyOf": [{ "type": "string" }, { "type": "null" }],
      "default": null,
      "description": "Quando content_mode for matching_sections, retorna seções cujo heading ou corpo contenha esse texto."
    },
    "include_frontmatter": {
      "type": "boolean",
      "default": true
    },
    "include_diagnostics": {
      "type": "boolean",
      "default": false
    },
    "preserve_order": {
      "type": "boolean",
      "default": true,
      "description": "Quando true, retorna os itens na mesma ordem dos ids solicitados."
    }
  },
  "required": ["ids"],
  "title": "get_instructions_batchArguments"
}

Esse contrato é mais claro para agente e mais seguro para evolução.

8. Melhor outputSchema

Eu recomendo fortemente sair de:

{
  "result": "JSON string..."
}

para:

{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "path": { "type": "string" },
          "title": { "type": "string" },
          "frontmatter": { "type": "object" },
          "content": { "type": "string" },
          "headings": {
            "type": "array",
            "items": { "type": "string" }
          },
          "matched_sections": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "heading": { "type": "string" },
                "content": { "type": "string" },
                "level": { "type": "integer" }
              }
            }
          },
          "truncated": { "type": "boolean" },
          "original_char_count": { "type": "integer" },
          "returned_char_count": { "type": "integer" },
          "content_sha256": { "type": "string" }
        },
        "required": ["id", "title", "content", "truncated"]
      }
    },
    "not_found": {
      "type": "array",
      "items": { "type": "string" }
    },
    "diagnostics": {
      "type": "object"
    }
  },
  "required": ["items"]
}

Esse formato facilita muito a vida do agente.

9. O campo frontmatter é muito importante

Você mencionou que cada item inclui frontmatter.

Isso é excelente.

Mas eu recomendo não deixar o frontmatter como um “blob qualquer” apenas. Você pode retornar alguns campos normalizados também:

{
  "id": "csharp-async-style",
  "title": "C# — padrão async/await",
  "kind": "policy",
  "scope": "application",
  "priority": "high",
  "tags": ["csharp", "async", "await", "task"],
  "applies_to": ["src/**/*.cs"],
  "frontmatter": {
    "...": "..."
  },
  "content": "..."
}

Por quê?

Porque o agente consegue usar campos explícitos melhor do que depender de frontmatter.

O frontmatter completo serve para rastreabilidade, mas os campos principais devem vir normalizados.

10. Essa tool deveria aceitar current_file_path?

Aqui tem uma nuance.

A princípio, get_instructions_batch carrega por ids. Então ela não precisa de current_file_path.

Mas pode ser útil em dois casos:

Caso 1 — validação

O agente pede ids que não deveriam ser aplicáveis ao arquivo atual.

Exemplo:

{
  "ids": ["rabbitmq-consumer-policy"],
  "current_file_path": "src/Trading/Fix/Session.cs"
}

O MCP poderia retornar:

{
  "warning": "Instruction rabbitmq-consumer-policy does not match current_file_path."
}
Caso 2 — recorte contextual

Mesmo carregando por id, a tool poderia priorizar seções aplicáveis ao arquivo atual.

Mas eu não adicionaria isso na primeira versão, para não misturar responsabilidades.

Minha recomendação:

current_file_path é essencial em search_instructions.
current_file_path é útil em list_instructions_index.
current_file_path é opcional e secundário em get_instructions_batch.

Se adicionar, que seja para diagnóstico/validação, não para seleção principal.

11. O que essa tool influencia no comportamento do agente

Ela influencia de forma muito direta.

Se a tool retorna conteúdo longo e bruto, o agente tende a:

tentar resumir sozinho;
perder regra no meio;
sofrer com lost in the middle;
ignorar documentos menos recentes no contexto;
misturar policies;
aplicar parte da regra e esquecer exceções.

Se a tool retorna conteúdo estruturado, com headings e seções, o agente tende a:

citar a regra correta;
seguir melhor as instruções;
entender hierarquia;
diferenciar regra global de regra específica;
aplicar conteúdo normativo com mais precisão.

Então essa tool é onde você pode combater o problema clássico de “joguei um monte de regra no contexto e a LLM se virou”.

12. headings_only é muito útil como etapa intermediária

Apesar das críticas às flags, a ideia de headings_only é excelente.

Ela permite um fluxo em duas etapas:

1. get_instructions_batch(ids, headings_only=true)
2. Agente vê estrutura dos documentos
3. Agente chama de novo com section_contains para carregar só as seções úteis

Exemplo:

{
  "ids": ["csharp-async-style"],
  "headings_only": true
}

Resposta:

{
  "items": [
    {
      "id": "csharp-async-style",
      "headings": [
        "# C# — async/await",
        "## Quando usar async",
        "## Quando evitar Task.Run",
        "## CancellationToken",
        "## ConfigureAwait",
        "## Erros comuns"
      ]
    }
  ]
}

Depois:

{
  "ids": ["csharp-async-style"],
  "section_contains": "CancellationToken",
  "headings_only": false
}

Esse fluxo é muito bom para reduzir contexto.

Mas eu reforço: um enum content_mode ficaria mais claro.

13. Cuidado com section_contains em múltiplos documentos

Quando você usa batch e section_contains, a mesma busca será aplicada a todos os documentos.

Exemplo:

{
  "ids": "artifact-encoding-line-endings-and-unicode,csharp-async-style",
  "section_contains": "async"
}

Isso pode retornar:

seção útil em csharp-async-style;
nada em artifact-encoding-line-endings-and-unicode.

Tudo bem, mas a resposta precisa deixar claro:

{
  "id": "artifact-encoding-line-endings-and-unicode",
  "matched_sections": [],
  "section_match_found": false
}

Sem isso, o agente pode interpretar ausência de conteúdo como falha da instruction.

14. Ordem dos documentos importa

Essa tool deveria preservar a ordem dos ids recebidos.

Se search_instructions retornou:

1. csharp-async-style
2. error-handling-policy
3. logging-policy

A get_instructions_batch deve retornar nessa mesma ordem.

Por quê?

Porque a ordem provavelmente reflete relevância.

Se a tool reordenar por path, título ou hash, você perde o ranking original.

Portanto, preserve_order: true deveria ser padrão.

15. Duplicidade de ids

Se o agente mandar:

{
  "ids": "csharp-async-style,csharp-async-style"
}

Eu recomendo deduplicar por padrão, mas informar diagnóstico se include_diagnostics = true.

Exemplo:

{
  "diagnostics": {
    "requested_count": 2,
    "unique_count": 1,
    "duplicates_removed": ["csharp-async-style"]
  }
}
16. Controle de quantidade máxima

Sem limite de quantidade de ids, o agente pode pedir 20, 50, 100 documents.

Isso pode explodir o contexto.

Eu colocaria limite:

{
  "maxItems": 10
}

Ou pelo menos no servidor:

Se ids > 10:
  retornar erro amigável ou truncar com warning

Para tasks comuns, 3 a 5 instructions completas já costuma ser bastante.

17. Estratégia ideal de uso com suas três tools

O fluxo recomendado para tarefa específica:

1. search_instructions
   Entrada:
   - query
   - current_file_path
   - kind/scope/tags se conhecidos

2. get_instructions_batch
   Entrada:
   - ids dos top 3 ou top 5
   - content_mode: summary_plus_headings ou full
   - max_chars_per_instruction controlado

3. Se necessário:
   - get_instructions_batch novamente com matching_sections

O fluxo recomendado para exploração:

1. list_instructions_index com include_facets
2. search_instructions para intenção específica
3. get_instructions_batch para conteúdo selecionado

O fluxo recomendado para reduzir contexto:

1. get_instructions_batch com headings_only
2. get_instructions_batch com matching_sections
18. Sugestão de documentação da tool

Eu escreveria algo assim:

"""
Use this tool to load the content of one or more instruction documents by id.

Use ids returned by `search_instructions` or `list_instructions_index`.
Prefer loading only the top relevant instructions needed for the current task.

For broad or uncertain tasks, first call this tool with `content_mode = "headings_only"` or `summary_plus_headings`
to inspect structure before loading full content.

Use `content_mode = "matching_sections"` with `section_contains` when only specific sections are needed.

Do not request too many ids at once. Prefer 1-5 highly relevant instructions.
The response indicates truncation, missing ids, and metadata for each returned instruction.
"""

Essa descrição ajuda o agente a não usar a tool como dump de corpus.

19. Minha avaliação crítica final
Aspecto	Avaliação
Batch por múltiplos ids	Muito bom
ids como string CSV	Funciona, mas é frágil
max_chars_per_instruction	Necessário, mas precisa informar truncamento
section_contains	Útil, mas precisa de semântica clara
include_headings	Bom
headings_only	Muito bom para exploração
Duas flags booleanas	Pode confundir; enum seria melhor
Output result como JSON string	Ponto fraco importante
Frontmatter parseado	Excelente
Falta de items estruturado	Limitação relevante
Falta de not_found/errors estruturado	Deve melhorar
Falta de diagnóstico de truncamento	Risco normativo
Falta de limite de ids	Risco de excesso de contexto
Falta de resumo/summary	Pode dificultar seleção progressiva
20. Recomendação objetiva

Eu evoluiria a tool em duas etapas.

Etapa 1 — sem quebrar compatibilidade

Manter entrada atual, mas melhorar saída interna:

{
  "result": "...",
  "items": [...],
  "not_found": [],
  "diagnostics": {}
}

Se o MCP exigir result, você mantém. Mas adiciona campos estruturados se possível.

Também adicionaria:

normalização de ids;
deduplicação;
limite máximo;
truncated;
original_char_count;
returned_char_count;
not_found.
Etapa 2 — contrato mais profissional

Migrar para:

{
  "ids": ["id1", "id2"],
  "content_mode": "full",
  "section_contains": null,
  "max_chars_per_instruction": 8000,
  "include_frontmatter": true,
  "include_diagnostics": false,
  "preserve_order": true
}

E saída:

{
  "items": [
    {
      "id": "id1",
      "title": "Instruction X",
      "kind": "policy",
      "scope": "global",
      "tags": [],
      "frontmatter": {},
      "content": "...",
      "headings": [],
      "truncated": false,
      "original_char_count": 4200,
      "returned_char_count": 4200,
      "content_sha256": "..."
    }
  ],
  "not_found": [],
  "diagnostics": {}
}
21. Conclusão

A get_instructions_batch é uma ótima tool e faz sentido no seu MCP. Mas ela precisa ser tratada como uma tool de controle de contexto, não apenas como “buscar conteúdo por ids”.

O objetivo dela deveria ser:

Carregar apenas o conteúdo normativo necessário, na granularidade certa, preservando metadados, ordem, rastreabilidade e sinalizando truncamento.

Hoje ela já tem boas ideias:

batch;
limite por instruction;
filtro por seção;
headings;
frontmatter.

Mas os pontos que eu priorizaria corrigir são:

trocar ids CSV por array;
evitar JSON serializado dentro de result;
retornar itens estruturados;
sinalizar truncamento;
limitar quantidade de ids;
trocar flags booleanas por content_mode;
retornar not_found e diagnóstico;
documentar melhor o uso progressivo: headings primeiro, seções depois, conteúdo completo só quando necessário.

Essa tool pode virar o principal mecanismo para evitar que o agente carregue instructions demais e sofra com ruído ou lost in the middle. Ela é o ponto onde você transforma o MCP de “buscador de arquivos” em fornecedor disciplinado de contexto normativo.