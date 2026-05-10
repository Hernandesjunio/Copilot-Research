Vou analisar este arquivo em duas dimensões: qualidade como instruction normativa e qualidade como item recuperável pelo MCP. Isso é importante porque um texto bom para humano nem sempre é bom para ranking, filtros e uso por agente.Thought for a few secondsA estrutura atual está boa como documento técnico curto, mas ainda está mais próxima de uma nota de referência para humano do que de uma instruction normativo-recuperável otimizada para MCP e agentes.
Ela tem bons elementos: frontmatter, id, title, tags, scope, priority, kind, objetivo, TL;DR, critérios, snippet e blocos “Pode/Não pode”. Porém, para o seu MCP, vejo oportunidades importantes em quatro eixos:


metadados mais precisos para recuperação determinística;


separação melhor entre regra normativa e conteúdo explicativo;


melhor granularidade para get_instructions_batch carregar seções certas;


redução de ambiguidade semântica para o agente decidir quando usar.



1. Avaliação geral
O arquivo atual:
id: microservice-design-principles-solid-performance-typestitle: "Design — SOLID, coesão, generics e performance de tipos"tags: [microservice, solid, design, performance, generics, csharp]scope: "**/*.cs"priority: mediumkind: reference
Minha avaliação:
ItemAvaliaçãoidBom, mas longo e com muitos conceitos misturadostitleBom para humano, mas amplo demais para rankingtagsÚteis, mas faltam tags de intençãoscopeFunciona como glob, mas semanticamente ambíguoprioritymedium faz sentidokindreference talvez esteja fraco para regras normativascorpoBem escrito, claro e curtoseçõesBoas, mas poderiam ser mais recuperáveissnippetÚtil“Pode/Não pode”Excelente para agenterisco principalDocumento cobre assuntos demais ao mesmo tempo
O ponto mais crítico é: este arquivo mistura design, SOLID, generics, performance de tipos, boxing, reflection, ArrayPool, Span, Repository<T> e herança/composição.
Isso não é necessariamente errado, mas reduz precisão na recuperação. Uma query sobre ArrayPool<T> pode recuperar este documento, mas o documento não é especificamente sobre performance de memória. Uma query sobre Repository<T> também pode recuperar, mas o documento não é especificamente sobre repositórios. Uma query sobre SOLID também pode recuperar, mas parte do documento fala de performance.
Para humano, isso é prático. Para MCP, pode virar ruído.

2. O principal problema: o scope está fazendo papel de applies_to
Hoje:
scope: "**/*.cs"
Isso é útil para máquina, mas ruim semanticamente.
O campo scope deveria responder:

“Qual é o escopo conceitual desta instruction?”

E não:

“Em quais arquivos ela se aplica?”

Eu sugiro separar:
scope: code-designapplies_to:  - "**/*.cs"
Ou, mais específico:
scope: csharp-designapplies_to:  - "src/**/*.cs"  - "tests/**/*.cs"
Por quê?
Porque scope: "**/*.cs" ajuda no filtro por path, mas não ajuda o agente a entender a natureza da instruction.
Melhor:
scope: csharp-designapplies_to:  - "**/*.cs"
Isso melhora:


list_instructions_index;


search_instructions;


filtro por current_file_path;


explicabilidade;


facets;


agrupamento por domínio.



3. O kind: reference talvez esteja fraco
O documento contém frases normativas:
- Evitar `object`, `Enum` em APIs quentes sem necessidade...- Reflection em caminho quente ... proibido/salvo...- Introduzir pipeline genérico complexo para um único caso de uso.
Isso não é apenas referência. Isso é parcialmente policy e parcialmente guideline.
Se o agente vê:
kind: reference
ele pode interpretar como conteúdo consultivo, não obrigatório.
Eu consideraria:
kind: guideline
ou, se você quiser reforçar:
kind: policy
Mas talvez o melhor seja separar o documento em duas categorias:
Opção A — manter como um documento único
kind: guideline
Opção B — separar em dois documentos


csharp-design-principles


SOLID, KISS, YAGNI, DRY, composição, interfaces.




csharp-performance-types-hot-paths


boxing, object, Enum, reflection, ArrayPool, Span, readonly struct.




Essa segunda opção melhora muito a recuperação.

4. O id está bom, mas tem excesso de assuntos
Atual:
id: microservice-design-principles-solid-performance-types
Ele junta:


microservice;


design principles;


SOLID;


performance;


types.


Isso pode ser um sinal de que o documento está amplo demais.
Sugestões, se mantiver unificado:
id: csharp-microservice-design-and-type-performance-guideline
Ou mais curto:
id: csharp-design-performance-guideline
Se separar:
id: csharp-solid-design-guideline
e:
id: csharp-type-performance-hot-path-policy
Para MCP, ids mais focados ajudam o agente a escolher melhor após list_instructions_index.

5. Tags atuais: boas, mas insuficientes para intenção
Atuais:
tags: [microservice, solid, design, performance, generics, csharp]
Boas, mas faltam tags que representem situações de uso.
Eu adicionaria algumas:
tags:  - csharp  - dotnet  - microservice  - design  - solid  - cohesion  - composition  - generics  - repository  - performance  - boxing  - reflection  - hot-path  - arraypool  - span  - yagni  - kiss
Mas cuidado: tags demais também diluem.
Minha recomendação equilibrada:
tags:  - csharp  - dotnet  - microservice  - design  - solid  - generics  - performance  - boxing  - reflection  - hot-path
Se o documento continuar misto, essas tags fazem sentido.
Se separar em dois documentos, cada um fica mais preciso.

6. Falta um campo summary
Para MCP, eu adicionaria obrigatoriamente um resumo curto no frontmatter.
Exemplo:
summary: "Critérios pragmáticos para aplicar SOLID, generics e otimizações de tipos em microservices .NET sem criar abstrações especulativas ou custos desnecessários em caminhos quentes."
Isso ajuda muito a list_instructions_index.
Hoje, o agente vê título e tags. Com summary, ele consegue decidir melhor se deve chamar get_instructions_batch.

7. Falta applies_when
Este é um campo muito útil para agentes.
Exemplo:
applies_when:  - "criando ou revisando código C# em microservices"  - "avaliando uso de interfaces, generics, herança ou composição"  - "avaliando performance de tipos, boxing, reflection, Span<T> ou ArrayPool<T>"
Isso ajuda o agente a decidir quando carregar a instruction.

8. Falta does_not_apply_when
Também é muito útil para reduzir falso positivo.
Exemplo:
does_not_apply_when:  - "a tarefa é exclusivamente sobre configuração de infraestrutura"  - "a tarefa é exclusivamente sobre frontend"  - "a tarefa é exclusivamente sobre SQL sem alteração de código C#"
Isso pode alimentar um filtro ou pelo menos retornar como metadado para o agente.

9. Falta severity ou rule_level
Você usa priority, mas priority pode significar prioridade de recuperação, não severidade normativa.
Exemplo:
priority: medium
Isso pode indicar:


recuperar com prioridade média;


regra média;


documento médio;


importância média.


Eu separaria:
priority: mediumrule_level: recommended
Ou:
severity: guideline
Valores possíveis:
rule_level: mandatory | recommended | advisory
Neste documento, eu usaria:
rule_level: recommended
Mas algumas regras dentro dele são mais fortes, como evitar reflection em hot path sem cache. Por isso, internamente você pode usar blocos MUST, SHOULD, MUST NOT.

10. O corpo está bom, mas pode ficar mais agent-friendly
O conteúdo atual é claro, mas eu deixaria as regras mais classificáveis.
Hoje:
## Pode ser feito- Extrair interfaces estáveis nas fronteiras de teste (ports) mantendo implementações simples.
Melhor para agente:
## Regras### SHOULD — Interfaces pequenas e estáveisUse interfaces pequenas nas fronteiras de teste, integração ou domínio. Evite criar interfaces para toda classe concreta sem necessidade demonstrada.### MUST NOT — Herança profunda para reusoNão introduza hierarquias profundas apenas para reutilizar código. Prefira composição quando não houver substituibilidade real.
O agente tende a respeitar melhor termos como:


MUST;


MUST NOT;


SHOULD;


MAY;


AVOID;


EXCEPTION.


Isso aumenta a normatividade.

11. A seção TL;DR é excelente
Para MCP, o TL;DR é valioso porque pode ser carregado em modo reduzido.
Eu manteria.
Mas talvez renomearia para:
## Resumo operacional
Ou manteria ambos:
## TL;DR — Resumo operacional
Isso ajuda section_contains.

12. Generics — critério de uso está bom, mas merece regra própria
Essa seção tem valor alto:
- Adotar generic quando reduz duplicação e mantém contratos claros.- Evitar generic quando esconde regras diferentes por tipo.
Isso poderia ser uma instruction própria:
id: csharp-generics-usage-guidelinetitle: "C# — critérios para uso de generics"tags: [csharp, generics, design, yagni, repository]scope: csharp-designapplies_to:  - "**/*.cs"
Por quê?
Porque generics é um assunto específico que o agente pode buscar isoladamente.
Exemplo de query:

“devo criar um Repository<T> genérico?”

Nesse caso, recuperar um documento focado em generics seria melhor do que recuperar uma instruction ampla sobre SOLID e performance.

13. Performance de tipos também merece separação
Essa seção contém temas de performance avançada:


readonly struct;


ArrayPool<T>;


Span<T>;


hotspots;


boxing;


object;


Enum;


reflection;


cache de delegates.


Isso é quase outro documento:
id: csharp-type-performance-hot-path-policytitle: "C# — performance de tipos em caminhos quentes"tags: [csharp, performance, hot-path, boxing, reflection, span, arraypool]scope: csharp-performanceapplies_to:  - "**/*.cs"
Esse documento seria recuperado por queries como:


“boxing em API quente”;


“usar Span<T>”;


“reflection em caminho quente”;


“ArrayPool em microservice”;


“readonly struct performance”.


Hoje, essas queries vão cair em um documento que também fala de SOLID. Funciona, mas é menos preciso.

14. A seção Snippet é boa, mas poderia ter intenção explícita
Atual:
// Bom: resultado explícito sem exceção de fluxo normalpublic sealed record Resultado<T>(bool Ok, T? Valor, string? CodigoErro);// Evitar: API pública baseada em objectpublic Task<object> ExecutarAsync(string nomeOperacao, object payload); // proibido salvo interoperabilidade documentada
Bom exemplo.
Mas o snippet mistura:


Result pattern;


evitar object.


Talvez a seção de snippet deveria explicar:
## Exemplo — contrato explícito em vez de objectUse tipos explícitos ou genéricos quando o contrato for conhecido. Evite `object` em APIs públicas porque reduz verificabilidade, dificulta validação em tempo de compilação e pode induzir casts, boxing ou contratos implícitos.
Isso aumenta a chance de o agente aplicar corretamente.

15. “Pode ser feito” e “Não pode ser feito” são ótimos
Essa é talvez a melhor parte do documento para agente.
Eu só mudaria os nomes para reforçar normatividade:
## Permitido## Proibido## Exceções permitidas
Ou, se quiser menos rígido:
## SHOULD — Pode ser feito## MUST NOT — Não pode ser feito## EXCEPTIONS — Exceções
Para agentes, “Não pode ser feito” já é forte. Mas MUST NOT é ainda mais padrão.

16. Falta uma seção Exceções
Você já tem algumas exceções embutidas:
salvo interoperabilidade documentada
e:
quando medição ou modelo de dados justificar
Eu criaria uma seção explícita:
## Exceções permitidas- `object` pode ser usado em interoperabilidade, serialização dinâmica ou integração externa quando o contrato for documentado.- `Span<T>`, `ArrayPool<T>` e `readonly struct` podem ser usados quando houver hotspot comprovado por medição, perfilamento ou requisito de latência.- Reflection pode ser usado fora de caminho quente ou com cache de delegates quando houver justificativa técnica.
Isso evita que o agente aplique a regra de forma dogmática.

17. Falta uma seção Sinais de aplicação
Para MCP e agente, isso é excelente:
## Sinais de aplicaçãoUse esta instruction quando a tarefa mencionar:- SOLID- interface- abstração- generics- Repository<T>- performance- boxing- reflection- Span<T>- ArrayPool<T>- herança- composição- microservice .NET
Mas parte disso poderia ir no frontmatter como applies_when.

18. Falta uma seção Conflitos com outras instructions
Em corpus maior, uma instruction pode conflitar com outra.
Exemplo:


uma instruction de performance pode recomendar reduzir abstração;


uma instruction de arquitetura pode recomendar depender de abstrações;


uma instruction de testes pode recomendar interfaces para mock;


uma instruction de DDD pode recomendar repositórios por agregado.


Seria útil ter:
related:  - csharp-async-style  - csharp-testing-mocking-guideline  - ddd-aggregate-repository-policyconflicts_with:  - none
Ou no corpo:
## Relação com outras instructions- Se houver conflito com instruction específica de DDD, priorize a instruction específica do domínio.- Se houver conflito com instruction de performance em hot path comprovado, priorize a regra de performance específica.
Isso ajuda muito no ranking e na composição de contexto.

19. Falta estratégia de precedência
Como priority: medium, uma instruction mais específica deveria ganhar.
Exemplo:
precedence: general
Ou:
specificity: general
Valores possíveis:
specificity: global | layer | domain | file_pattern
Para este documento:
specificity: layer
ou:
specificity: general
Isso ajudaria o MCP em caso de disputa.

20. Versão melhorada mantendo documento único
Se você quiser manter este arquivo como está, eu sugeriria esta versão de frontmatter:
---id: csharp-microservice-design-performance-guidelinetitle: "C# Microservices — design pragmático, generics e performance de tipos"summary: "Orienta decisões pragmáticas de design em microservices .NET, equilibrando SOLID, KISS/YAGNI, uso de generics e cuidados com performance de tipos em caminhos quentes."tags:  - csharp  - dotnet  - microservice  - design  - solid  - generics  - performance  - boxing  - reflection  - hot-pathscope: csharp-designapplies_to:  - "**/*.cs"priority: mediumkind: guidelinerule_level: recommendedspecificity: generalapplies_when:  - "criando ou revisando código C# em microservices"  - "avaliando uso de interfaces, generics, herança, composição ou abstrações"  - "avaliando custos de boxing, reflection, object, Span<T> ou ArrayPool<T>"does_not_apply_when:  - "a tarefa é exclusivamente sobre frontend"  - "a tarefa é exclusivamente sobre infraestrutura sem alteração de código C#"  - "a tarefa é exclusivamente sobre SQL sem código .NET"---
Isso já melhoraria bastante o MCP sem alterar muito o corpo.

21. Versão melhorada do corpo
Eu reestruturaria assim:
# ObjetivoOrientar decisões de design em microservices .NET para manter código legível, extensível e eficiente, aplicando SOLID com pragmatismo e evitando custos desnecessários de alocação, boxing e abstração especulativa.## TL;DR — Resumo operacional- Use interfaces pequenas e estáveis nas fronteiras reais do sistema.- Prefira composição a herança profunda.- Aplique KISS/YAGNI antes de introduzir camadas, pipelines ou abstrações genéricas.- Use generics quando houver reuso real e invariantes equivalentes.- Evite `object`, `Enum`, reflection e coleções não genéricas em caminhos quentes sem justificativa.- Use `ArrayPool<T>`, `Span<T>` e `readonly struct` apenas quando houver hotspot comprovado ou requisito técnico claro.## Sinais de aplicaçãoUse esta instruction quando a tarefa envolver:- design de classes C#;- criação de interfaces;- uso de generics;- avaliação de `Repository<T>`;- performance de tipos;- boxing;- reflection;- `Span<T>`;- `ArrayPool<T>`;- herança versus composição.## Regras de design### SHOULD — Interfaces pequenasCrie interfaces pequenas e orientadas a comportamento real. Evite interfaces artificiais para toda classe concreta.### SHOULD — Composição antes de herançaPrefira composição quando o objetivo for reutilizar comportamento. Use herança apenas quando houver substituibilidade real.### MUST NOT — Abstração especulativaNão crie pipelines, camadas ou padrões genéricos para um único caso de uso sem necessidade demonstrada.## Generics — critério de uso### SHOULD — Usar generics com invariantes equivalentesAdote generics quando reduzirem duplicação e mantiverem contratos claros, como `Result<T>`, `PagedResult<TItem>` ou policies internas.### MUST NOT — Esconder regras divergentes por tipoNão use `where T : class` com ramificações internas baseadas em `typeof(T)` para comportamentos divergentes.## Performance de tipos### SHOULD — Evitar contratos baseados em objectEvite `object`, `Enum` e coleções não genéricas em APIs quentes quando houver alternativa tipada.### SHOULD — Usar otimizações avançadas apenas com justificativaUse `ArrayPool<T>`, `Span<T>` e `readonly struct` apenas em hotspots comprovados por medição, perfilamento ou requisito de latência.### MUST NOT — Reflection sem cache em caminho quenteNão use reflection em caminho quente para mapeamento ou dispatch sem cache de delegates ou estratégia equivalente.## Exemplo```csharp// Bom: resultado explícito sem exceção de fluxo normalpublic sealed record Resultado<T>(bool Ok, T? Valor, string? CodigoErro);// Evitar: API pública baseada em objectpublic Task<object> ExecutarAsync(string nomeOperacao, object payload); // proibido salvo interoperabilidade documentada
Exceções permitidas


object pode ser usado em interoperabilidade documentada, serialização dinâmica ou integração externa.


Reflection pode ser usado fora de caminhos quentes ou com cache adequado.


Span<T>, ArrayPool<T> e readonly struct podem ser usados quando houver medição, requisito de latência ou modelo de dados que justifique.


Pode ser feito


Extrair interfaces estáveis nas fronteiras de teste ou integração mantendo implementações simples.


Documentar invariantes de agregados no próprio modelo de domínio.


Usar generics para resultados, paginação e contratos realmente reutilizáveis.


Não pode ser feito


Criar herança profunda apenas para reuso de código.


Introduzir pipeline genérico complexo para um único caso de uso.


Usar reflection em caminho quente para “magia” de mapeamento sem cache.


---# 22. Minha recomendação mais forte: dividir em 2 ou 3 arquivosPara o seu MCP, eu acho que esta instruction está **um pouco ampla demais**.Eu dividiria em três:## 1. `csharp-solid-design-guideline.md`Foco:- SOLID;- KISS/YAGNI;- DRY;- interfaces;- composição;- herança;- coesão.## 2. `csharp-generics-usage-guideline.md`Foco:- quando usar generics;- quando evitar;- `Repository<T>`;- `Result<T>`;- `PagedResult<T>`;- `typeof(T)` smell.## 3. `csharp-type-performance-hot-path-policy.md`Foco:- boxing;- `object`;- `Enum`;- reflection;- `Span<T>`;- `ArrayPool<T>`;- `readonly struct`;- hotspots comprovados.Por quê?Porque no seu MCP, o ranking fica muito melhor.Exemplo:```textQuery: "devo usar Repository<T> genérico?"
Documento ideal:
csharp-generics-usage-guideline
Não um documento amplo sobre SOLID e performance.
Outro exemplo:
Query: "reflection em mapper de alta performance"
Documento ideal:
csharp-type-performance-hot-path-policy
Não um documento geral de design.
Outro exemplo:
Query: "criar interface para service"
Documento ideal:
csharp-solid-design-guideline

23. Mas cuidado: dividir demais também pode atrapalhar
A divisão melhora a precisão, mas pode criar outro problema: o agente precisar carregar muitos arquivos.
Então eu usaria uma regra:

Divida quando uma seção possuir intenção de busca própria e puder ser usada de forma independente.

Neste caso, sim, eu dividiria pelo menos em dois:


design/SOLID/generics;


performance de tipos/hot path.


Generics pode ficar com design inicialmente.

24. Como esse arquivo seria recuperado hoje
Com seu contrato atual, ele provavelmente seria recuperado por queries como:
solidgenericsperformancemicroservicecsharpdesign
Mas talvez não seja recuperado por queries como:
Repository<T>boxingobject payloadreflection cache delegatesSpanArrayPoolherança profundacomposiçãoabstração especulativaYAGNI
Alguns desses termos estão no corpo, então BM25 pode encontrar, mas list_instructions_index não mostraria claramente esses sinais se o agente olhar só metadados.
Por isso, melhorar tags e summary ajuda.

25. Como isso afeta suas tools
Em list_instructions_index
Com o frontmatter atual, o agente vê:
"title": "Design — SOLID, coesão, generics e performance de tipos","tags": ["microservice", "solid", "design", "performance", "generics", "csharp"],"scope": "**/*.cs","kind": "reference"
Ele pode pensar:

“É uma referência geral, talvez útil.”

Com frontmatter melhorado, ele veria:
"summary": "Orienta decisões pragmáticas de design em microservices .NET...","scope": "csharp-design","applies_to": ["**/*.cs"],"kind": "guideline","rule_level": "recommended","applies_when": [...]
A chance de uso correto sobe bastante.

Em search_instructions
O documento atual pode receber score alto em várias queries, mas por ser amplo pode competir demais com outros documentos.
Se você separar em documentos menores, o BM25 fica mais preciso.
Se mantiver unificado, use tags mais ricas e summary.

Em get_instructions_batch
As seções atuais são boas para section_contains, mas poderiam ser melhores.
Por exemplo:
## Generics — critério de uso
Boa.
## Performance de tipos
Boa.
Mas faltam headings para:
## Regras de design## Exceções permitidas## Sinais de aplicação
Isso permitiria carregar apenas partes úteis.

26. Padrão recomendado para seus arquivos de instruction
Eu começaria a padronizar todos com este template:
---id: string-estavel-e-curtotitle: "Título humano claro"summary: "Resumo curto dizendo quando e por que usar esta instruction."tags: []scope: "escopo-conceitual"applies_to:  - "glob/pattern"priority: low|medium|high|criticalkind: policy|guideline|reference|checklist|examplerule_level: mandatory|recommended|advisoryspecificity: global|layer|domain|file_patternapplies_when:  - "situação em linguagem natural"does_not_apply_when:  - "situação em que não deve ser usada"related:  - "id-relacionado"---
E corpo:
# Objetivo## TL;DR — Resumo operacional## Sinais de aplicação## Regras### MUST### SHOULD### MUST NOT## Exceções permitidas## Exemplos## Checklist para o agente
Essa estrutura é muito mais amigável para MCP.

27. Checklist para avaliar seus próximos corpus
Quando você mandar outros arquivos, eu vou avaliar principalmente estes pontos:
1. O documento tem uma intenção única ou mistura assuntos demais?2. O id é estável, curto e semanticamente claro?3. O title ajuda humano e agente?4. As tags representam domínio, tecnologia e intenção?5. scope está conceitual ou misturado com glob?6. applies_to existe e é útil para current_file_path?7. kind representa força normativa correta?8. priority é prioridade de recuperação ou severidade?9. Há summary no frontmatter?10. Há applies_when e does_not_apply_when?11. O corpo tem TL;DR?12. O corpo tem regras explícitas?13. O corpo separa MUST, SHOULD, MUST NOT e exceções?14. As seções são boas para section_contains?15. O documento é carregável parcialmente sem perder sentido?16. Ele deveria ser dividido?17. Ele conflita com outro provável documento?18. Ele ajuda ou confunde BM25?

28. Conclusão objetiva
Este arquivo é bom como conteúdo, mas ainda precisa evoluir como unidade recuperável por MCP.
Minha recomendação prática:


Separar scope e applies_to.


Trocar kind: reference por kind: guideline.


Adicionar summary.


Adicionar applies_when.


Adicionar does_not_apply_when.


Adicionar tags mais específicas: dotnet, boxing, reflection, hot-path.


Reestruturar o corpo com MUST, SHOULD, MUST NOT, EXCEPTIONS.


Considerar dividir em dois arquivos:


design/SOLID/generics;


performance de tipos/hot path.




A melhor frase para resumir a análise é:

O conteúdo está tecnicamente bom, mas a instruction ainda não está suficientemente “indexável, filtrável e aplicável” para maximizar o comportamento determinístico do MCP.

Para o seu objetivo, isso importa muito. O MCP não precisa apenas de bons textos. Ele precisa de documentos com metadados e seções desenhados para recuperação, ranking, filtro por arquivo e aplicação normativa pelo agente.