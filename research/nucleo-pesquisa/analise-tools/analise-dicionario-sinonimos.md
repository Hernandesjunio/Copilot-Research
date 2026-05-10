Especificação Técnica — Corpus Query Expansion Map
Contexto
Tenho um MCP chamado `user-corporate-instructions` que indexa arquivos Markdown normativos de instructions corporativas.
Atualmente existe um recurso chamado `synonyms` ou “dicionário de sinônimos”, usado para expandir queries antes da busca. Porém, o conceito está incorreto: os termos não são apenas sinônimos, mas aliases, termos técnicos relacionados, tags, relações contextuais e pontes entre a linguagem natural do usuário/agente e o vocabulário real do corpus.
O novo conceito oficial será:
```text
Corpus Query Expansion Map
```
O objetivo é migrar completamente o conceito antigo `synonyms` para `Corpus Query Expansion Map`.
Além disso, o mapa não será mais um único arquivo grande. Ele será modularizado em múltiplos arquivos YAML dentro de uma pasta chamada:
```text
corpus-query-expansion-map/
```
Exemplo de estrutura desejada:
```text
instructions/
  docs/
    *.md

  metadata/
    corpus-query-expansion-map/
      00-core.yml
      10-dotnet.yml
      20-api.yml
      30-data.yml
      40-messaging.yml
      50-observability.yml
      60-security.yml
      70-architecture.yml
      80-governance.yml
      90-project-specific.yml
```
Tools existentes no MCP
O MCP possui ou possuirá tools como:
`list_instructions_index`
`search_instructions`
`get_instructions_batch`
A busca pode usar:
BM25;
metadados do frontmatter;
tags;
kind;
priority;
scope/applies_to;
futuramente `current_file_path`;
futuramente diagnóstico detalhado com `include_diagnostics`.
---
Objetivo da análise
Gerar uma especificação técnica objetiva para:
Migrar o conceito antigo `synonyms` para `Corpus Query Expansion Map`.
Substituir todas as referências antigas a `synonyms` no código, testes, documentação, logs e diagnósticos.
Definir a estrutura modular com múltiplos arquivos YAML dentro da pasta `corpus-query-expansion-map/`.
Definir regras de carregamento, validação, composição, duplicidade, namespace, conflito e diagnóstico.
Definir como o mapa será usado junto com BM25, sem substituir o BM25.
Definir critérios de aceite técnicos para validar a migração.
---
1. Visão geral
O `Corpus Query Expansion Map` deve ser uma camada de alinhamento entre:
```text
linguagem do usuário/agente
```
e:
```text
vocabulário técnico presente no corpus de instructions
```
Ele não deve ser tratado como um dicionário de sinônimos. Seu papel é aumentar o recall da busca de forma controlada, ajudando o MCP a conectar termos naturais, termos em português, termos em inglês, nomes de tecnologias, conceitos relacionados e vocabulário real usado nos arquivos Markdown.
O mapa não substitui:
BM25;
filtros por metadados;
`current_file_path`;
busca vetorial futura;
reranking futuro;
boa estruturação do frontmatter dos documentos.
Ele deve atuar como uma camada auxiliar de expansão de consulta.
---
2. Problema atual
O recurso atual chamado `synonyms` induz a uma interpretação incorreta.
Exemplo antigo:
```yaml
cache:
  - imemorycache
  - idistributedcache
  - caching
  - ttl
  - invalidation
```
O problema é que esses termos não são todos sinônimos.
`caching` pode ser alias de `cache`.
`IMemoryCache` e `IDistributedCache` são tecnologias/APIs relacionadas.
`ttl` é conceito associado.
`invalidation` é operação relacionada.
Outro exemplo:
```yaml
mensageria:
  - rabbitmq
  - messaging
  - publish
  - consume
  - outbox
```
Nesse caso:
`messaging` é alias aproximado.
`RabbitMQ` é tecnologia.
`publish`, `consume` e `outbox` são conceitos relacionados.
Logo, chamar tudo isso de sinônimo é tecnicamente incorreto e pode induzir decisões ruins no código, nos testes e na documentação.
---
3. Novo conceito: Corpus Query Expansion Map
O novo conceito oficial será:
```text
Corpus Query Expansion Map
```
Definição:
> O `Corpus Query Expansion Map` é um mapa versionado e modular de expansão de consultas, usado para conectar termos da linguagem do usuário/agente ao vocabulário técnico presente no corpus de instructions.
Ele deve suportar diferentes tipos de relação:
aliases;
termos fortemente relacionados;
termos fracamente relacionados;
expansão contextual;
expansão baseada em path;
namespaces;
origem do arquivo YAML;
diagnóstico de expansão.
---
4. Nomenclatura oficial
Migrar todas as referências antigas para a nova nomenclatura.
Antigo	Novo
`synonyms`	`query_expansion_map` ou `corpus_query_expansion_map`
`SynonymDictionary`	`CorpusQueryExpansionMap`
`SynonymProvider`	`QueryExpansionProvider`
`ExpandSynonyms`	`ExpandQueryTerms`
`synonym_terms`	`expanded_terms`
`synonym_match`	`expansion_match`
`synonym_score`	`expansion_score`
`synonyms_applied`	`query_expansion`
A migração deve remover o termo `synonyms` de:
nomes de classes;
métodos;
variáveis;
arquivos;
schemas;
testes;
documentação;
logs;
diagnósticos;
mensagens de erro.
Exemplo em C#:
```csharp
public sealed class CorpusQueryExpansionMap
{
    public IReadOnlyDictionary<string, QueryExpansionTerm> Terms { get; init; }
}

public interface IQueryExpansionProvider
{
    QueryExpansionResult ExpandQueryTerms(QueryExpansionRequest request);
}
```
---
5. Estrutura de diretórios proposta
A estrutura recomendada é:
```text
instructions/
  docs/
    *.md

  metadata/
    corpus-query-expansion-map/
      00-core.yml
      10-dotnet.yml
      20-api.yml
      30-data.yml
      40-messaging.yml
      50-observability.yml
      60-security.yml
      70-architecture.yml
      80-governance.yml
      90-project-specific.yml
```
A escolha por múltiplos arquivos YAML tem os seguintes objetivos:
melhorar organização por domínio;
reduzir conflitos de merge;
permitir ownership por área;
facilitar revisão em PR;
permitir diagnóstico por origem;
preparar o corpus para escala;
evitar um arquivo único grande e difícil de manter.
---
6. Estrutura YAML proposta
Cada arquivo YAML deve seguir uma estrutura uniforme.
Exemplo:
```yaml
version: 1
namespace: messaging
description: "Expansões relacionadas a mensageria, filas, eventos e integração assíncrona."

terms:
  mensageria:
    aliases:
      - messaging
    strong_terms:
      - publish
      - consume
      - outbox
    weak_terms:
      - event
      - queue
    expansion_mode: contextual
    contexts:
      rabbitmq:
        activation_terms:
          - rabbitmq
          - amqp
          - exchange
        applies_to:
          - "**/*.cs"
        terms:
          - rabbitmq
          - exchange
          - queue
          - consumer
          - dlq

      servicebus:
        activation_terms:
          - servicebus
          - azure-service-bus
          - deadletter
        applies_to:
          - "**/*.cs"
        terms:
          - servicebus
          - queue
          - deadletter

      fix:
        activation_terms:
          - fix-protocol
          - heartbeat
          - session
        applies_to:
          - "**/*.cs"
        terms:
          - fix
          - session
          - heartbeat
```
Campos obrigatórios por arquivo:
```yaml
version: 1
namespace: string
description: string
terms: object
```
Campos por termo:
```yaml
aliases: []
strong_terms: []
weak_terms: []
expansion_mode: normal | contextual
contexts: {}
```
---
7. Regras de carregamento e composição
O loader deve seguir comportamento determinístico:
Localizar a pasta `metadata/corpus-query-expansion-map/`.
Carregar todos os arquivos `.yml` e `.yaml`.
Ordenar os arquivos por nome antes do carregamento.
Validar o schema de cada arquivo.
Validar `version`.
Validar `namespace`.
Montar um índice final em memória.
Guardar `source_file` e `namespace` de cada termo para diagnóstico.
Falhar no startup se houver erro estrutural grave.
A ordenação por nome é importante para evitar comportamento diferente entre sistemas operacionais.
Nomes recomendados:
```text
00-core.yml
10-dotnet.yml
20-api.yml
30-data.yml
40-messaging.yml
50-observability.yml
60-security.yml
70-architecture.yml
80-governance.yml
90-project-specific.yml
```
---
8. Regras de duplicidade, merge e override
A política inicial recomendada é:
duplicidade de termo entre arquivos diferentes deve falhar por padrão;
merge automático não deve ser permitido inicialmente;
override só deve ser permitido se declarado explicitamente.
Exemplo de override explícito:
```yaml
terms:
  mensageria:
    override: true
    override_reason: "Neste projeto, mensageria se refere majoritariamente a FIX."
    aliases:
      - messaging
    strong_terms:
      - fix
      - session
      - heartbeat
    expansion_mode: contextual
```
Riscos do merge automático:
expansão ampla demais;
perda de precisão;
contaminação do ranking;
dificuldade de diagnóstico;
comportamento inesperado em termos ambíguos.
Regra recomendada:
```text
Duplicidade sem override explícito deve falhar no startup.
```
---
9. Regras de expansão
O mapa deve diferenciar tipos de expansão.
aliases
Termos equivalentes ou quase equivalentes.
Exemplo:
```yaml
resiliencia:
  aliases:
    - resilience
    - tolerancia
```
strong_terms
Termos fortemente relacionados ao conceito.
Exemplo:
```yaml
resiliencia:
  strong_terms:
    - retry
    - timeout
    - circuit-breaker
    - polly
```
weak_terms
Termos relacionados, mas periféricos. Devem ter peso menor.
Exemplo:
```yaml
logs:
  weak_terms:
    - secrets
    - readiness
    - production
```
expansion_mode: normal
A expansão pode ocorrer sem contexto adicional.
expansion_mode: contextual
A expansão contextual só deve ocorrer quando houver evidência adicional, como:
`current_file_path`;
tags;
kind;
scope;
applies_to;
metadados da busca.
Exemplo crítico:
```text
mensageria não deve expandir automaticamente para rabbitmq quando o contexto do arquivo indicar FIX.
```
---
10. Suporte a global/local
A arquitetura deve considerar que futuramente pode existir:
corpus global;
corpus específico por projeto.
Regra de precedência recomendada:
Carregar corpus global primeiro.
Carregar corpus local depois.
Corpus local pode adicionar termos novos.
Corpus local só pode sobrescrever termo global com `override: true` e justificativa.
Sem `override: true`, duplicidade deve gerar erro.
Exemplo:
```yaml
terms:
  mensageria:
    override: true
    override_reason: "Neste projeto, mensageria significa FIX, não RabbitMQ."
    aliases:
      - messaging
    strong_terms:
      - fix
      - session
      - heartbeat
```
---
11. Integração com BM25
O `Corpus Query Expansion Map` não deve substituir BM25.
Pipeline recomendado:
```text
1. Receber query original
2. Tokenizar query original
3. Detectar termos presentes no Corpus Query Expansion Map
4. Aplicar expansão controlada
5. Rodar BM25 com query original
6. Rodar BM25 com query expandida com peso menor
7. Combinar scores
8. Aplicar boost/filtro por metadados:
   - tags
   - kind
   - priority
   - scope
   - applies_to
   - current_file_path
9. Retornar resultados com diagnóstico opcional
```
Regra obrigatória:
```text
A query original deve ter peso maior que a query expandida.
```
Exemplo conceitual:
```text
score_final =
  1.00 * bm25_original
+ 0.35 * bm25_expanded
+ 0.30 * path_match
+ 0.20 * tag_match
+ 0.10 * priority_boost
```
Os pesos devem ser configuráveis ou pelo menos centralizados.
---
12. Diagnóstico esperado
Quando `include_diagnostics = true`, a resposta da busca deve incluir algo semelhante a:
```json
{
  "query_expansion": {
    "enabled": true,
    "source": "corpus-query-expansion-map",
    "matched_terms": [
      {
        "term": "mensageria",
        "namespace": "messaging",
        "source_file": "40-messaging.yml",
        "expansion_mode": "contextual"
      }
    ],
    "expanded_terms": [
      {
        "term": "rabbitmq",
        "relation": "contextual",
        "context": "rabbitmq",
        "weight": 0.8,
        "source_file": "40-messaging.yml"
      }
    ],
    "skipped_terms": [
      {
        "term": "fix",
        "reason": "context_not_matched"
      }
    ]
  }
}
```
O diagnóstico deve mostrar:
query original;
termos detectados no mapa;
termos expandidos;
relação aplicada;
peso aplicado;
namespace;
source_file;
se expansão contextual foi aplicada;
termos ignorados e motivo.
---
13. Impacto nas tools
search_instructions
Deve usar o `Corpus Query Expansion Map` para expandir query de forma controlada.
Deve respeitar:
`current_file_path`, se existir;
tags;
kind;
scope;
priority;
`include_diagnostics`.
list_instructions_index
Não precisa expandir query.
Pode expor metadados que ajudem o agente a entender:
namespaces existentes;
tags disponíveis;
kinds disponíveis;
scopes disponíveis;
prioridades disponíveis.
get_instructions_batch
Não deve aplicar expansão de query, pois recebe ids.
No máximo, pode retornar:
metadados do documento;
origem;
frontmatter;
diagnóstico de truncamento;
informações úteis para rastreabilidade.
---
14. Processo de migração
Processo recomendado:
Localizar todas as referências a `synonyms`.
Criar o novo modelo `CorpusQueryExpansionMap`.
Criar o provider `QueryExpansionProvider`.
Criar o método `ExpandQueryTerms`.
Criar loader para pasta `corpus-query-expansion-map/`.
Criar schema de validação dos YAML.
Migrar o arquivo antigo de sinônimos para múltiplos arquivos YAML agrupados.
Renomear classes, métodos, variáveis e testes.
Atualizar documentação.
Atualizar logs e diagnósticos.
Manter compatibilidade temporária se necessário, mas marcando `synonyms` como deprecated.
Criar testes comparando:
BM25 puro;
BM25 + expansão antiga;
BM25 + Corpus Query Expansion Map.
Validar queries ambíguas.
Queries ambíguas obrigatórias para teste:
mensageria RabbitMQ;
mensageria FIX;
validação API;
logs/secrets;
transação SQL;
health/readiness;
resiliência HttpClient.
---
15. Impactos no código
Áreas impactadas:
carregamento de configuração;
modelos internos;
parser YAML;
validação de schema;
indexação em memória;
pipeline de busca;
scoring;
diagnósticos;
testes unitários;
testes de integração;
documentação das tools MCP.
Possíveis nomes de classes:
```csharp
CorpusQueryExpansionMap
QueryExpansionTerm
QueryExpansionContext
QueryExpansionProvider
QueryExpansionResult
QueryExpansionDiagnostic
QueryExpansionLoader
QueryExpansionMapValidator
```
Possíveis métodos:
```csharp
LoadExpansionMap()
ExpandQueryTerms()
ResolveContextualTerms()
ValidateExpansionMap()
BuildExpansionIndex()
```
---
16. Impactos nos testes
Testes recomendados:
Loader
carrega múltiplos arquivos `.yml`;
carrega múltiplos arquivos `.yaml`;
ordena por nome;
falha com YAML inválido;
falha com `version` inválida;
falha com `namespace` ausente;
falha com termo duplicado sem override;
aceita override explícito com justificativa.
Expansão
expande aliases;
expande strong_terms;
expande weak_terms com peso menor;
não expande contexto quando `current_file_path` não bate;
expande contexto quando `current_file_path` bate;
não trata todos os termos como equivalentes.
Busca
BM25 original continua funcionando;
BM25 expandido melhora recall;
query original pesa mais que expansão;
path/context reduz ambiguidade;
diagnóstico retorna termos usados e ignorados.
Regressão
Comparar:
BM25 puro;
BM25 + synonyms antigo;
BM25 + Corpus Query Expansion Map.
---
17. Critérios de aceite
Critérios técnicos:
Nenhuma referência pública ao termo `synonyms` deve permanecer.
O loader deve carregar múltiplos arquivos YAML de forma determinística.
A pasta `corpus-query-expansion-map/` deve ser a fonte oficial do mapa.
Duplicidade de termo sem override deve falhar.
Override explícito deve funcionar com justificativa.
Diagnóstico deve mostrar `namespace` e `source_file`.
Expansão contextual só deve ocorrer quando o contexto bater.
BM25 original deve continuar tendo maior peso que expansão.
Testes devem cobrir termos normais e termos ambíguos.
Configuração inválida deve falhar com erro claro.
Documentação deve explicar que o mapa não é dicionário de sinônimos.
O mapa não pode ficar hardcoded no código.
`search_instructions` deve usar expansão controlada.
`get_instructions_batch` não deve aplicar expansão de query.
O diagnóstico deve permitir entender por que um termo foi expandido, ignorado ou usado em contexto.
---
18. Riscos e mitigação
Risco: expansão agressiva demais
Mitigação:
usar pesos diferentes;
manter query original com maior peso;
tratar termos ambíguos como contextuais;
registrar diagnóstico.
Risco: termos duplicados contaminarem ranking
Mitigação:
falhar duplicidade por padrão;
permitir override somente com justificativa.
Risco: mapa virar ontologia informal difícil de manter
Mitigação:
manter schema simples;
separar por namespace;
revisar em PR;
evitar relações genéricas demais.
Risco: merge automático ampliar contexto indevidamente
Mitigação:
não permitir merge automático na primeira versão.
Risco: comportamento não explicável
Mitigação:
diagnóstico obrigatório quando `include_diagnostics = true`;
registrar `source_file`, `namespace`, relação e peso.
Risco: dependência excessiva do mapa
Mitigação:
BM25 original deve permanecer como base;
expansão deve ser complementar;
testes devem comparar BM25 puro com BM25 expandido.
---
Restrições
Não tratar todos os termos como sinônimos equivalentes.
Não aplicar expansão agressiva em termos ambíguos.
Não deixar o mapa hardcoded no código.
Não substituir BM25 pelo mapa.
Não criar solução complexa demais para a primeira versão.
Priorizar implementação incremental, testável e compatível com o MCP atual.
---
Prompt para análise por outra IA
```markdown
Aja como um arquiteto de software especialista em MCP, recuperação de contexto, BM25, engenharia de corpus e design de tools para agentes de IA.

## Contexto

Tenho um MCP chamado `user-corporate-instructions` que indexa arquivos Markdown normativos de instructions corporativas.

Atualmente existe um recurso chamado `synonyms` ou “dicionário de sinônimos”, usado para expandir queries antes da busca. Porém, o conceito está incorreto: os termos não são apenas sinônimos, mas aliases, termos técnicos relacionados, tags, relações contextuais e pontes entre a linguagem natural do usuário/agente e o vocabulário real do corpus.

O novo conceito oficial será:

`Corpus Query Expansion Map`

O objetivo é migrar completamente o conceito antigo `synonyms` para `Corpus Query Expansion Map`.

Além disso, o mapa não será mais um único arquivo grande. Ele será modularizado em múltiplos arquivos YAML dentro de uma pasta chamada:

```text
corpus-query-expansion-map/
```
Exemplo de estrutura desejada:
```text
instructions/
  docs/
    *.md

  metadata/
    corpus-query-expansion-map/
      00-core.yml
      10-dotnet.yml
      20-api.yml
      30-data.yml
      40-messaging.yml
      50-observability.yml
      60-security.yml
      70-architecture.yml
      80-governance.yml
      90-project-specific.yml
```
Tools existentes no MCP
O MCP possui ou possuirá tools como:
`list_instructions_index`
`search_instructions`
`get_instructions_batch`
A busca pode usar:
BM25;
metadados do frontmatter;
tags;
kind;
priority;
scope/applies_to;
futuramente `current_file_path`;
futuramente diagnóstico detalhado com `include_diagnostics`.
Objetivo da análise
Gere uma especificação técnica objetiva para:
Migrar o conceito antigo `synonyms` para `Corpus Query Expansion Map`.
Substituir todas as referências antigas a `synonyms` no código, testes, documentação, logs e diagnósticos.
Definir a estrutura modular com múltiplos arquivos YAML dentro da pasta `corpus-query-expansion-map/`.
Definir regras de carregamento, validação, composição, duplicidade, namespace, conflito e diagnóstico.
Definir como o mapa será usado junto com BM25, sem substituir o BM25.
Definir critérios de aceite técnicos para validar a migração.
Pontos obrigatórios da análise
1. Novo conceito
Explique que `Corpus Query Expansion Map` não é um dicionário de sinônimos.
Ele deve ser descrito como uma camada de alinhamento entre:
```text
linguagem do usuário/agente
```
e:
```text
vocabulário técnico presente no corpus de instructions
```
Ele deve servir para aumentar recall de forma controlada, sem substituir BM25, filtros por metadados ou busca vetorial futura.
2. Nomenclatura oficial
Migrar todas as referências antigas:
Antigo	Novo
`synonyms`	`query_expansion_map` ou `corpus_query_expansion_map`
`SynonymDictionary`	`CorpusQueryExpansionMap`
`SynonymProvider`	`QueryExpansionProvider`
`ExpandSynonyms`	`ExpandQueryTerms`
`synonym_terms`	`expanded_terms`
`synonym_match`	`expansion_match`
`synonym_score`	`expansion_score`
`synonyms_applied`	`query_expansion`
A especificação deve orientar a remoção do termo `synonyms` de:
nomes de classes;
métodos;
variáveis;
arquivos;
schemas;
testes;
documentação;
logs;
diagnósticos;
mensagens de erro.
3. Estrutura modular dos arquivos YAML
Propor uma estrutura de arquivo como:
```yaml
version: 1
namespace: messaging
description: "Expansões relacionadas a mensageria, filas, eventos e integração assíncrona."

terms:
  mensageria:
    aliases:
      - messaging
    strong_terms:
      - publish
      - consume
      - outbox
    weak_terms:
      - event
      - queue
    expansion_mode: contextual
    contexts:
      rabbitmq:
        activation_terms:
          - rabbitmq
          - amqp
          - exchange
        applies_to:
          - "**/*.cs"
        terms:
          - rabbitmq
          - exchange
          - queue
          - consumer
          - dlq

      servicebus:
        activation_terms:
          - servicebus
          - azure-service-bus
          - deadletter
        applies_to:
          - "**/*.cs"
        terms:
          - servicebus
          - queue
          - deadletter

      fix:
        activation_terms:
          - fix-protocol
          - heartbeat
          - session
        applies_to:
          - "**/*.cs"
        terms:
          - fix
          - session
          - heartbeat
```
A estrutura deve suportar:
`version`;
`namespace`;
`description`;
`terms`;
`aliases`;
`strong_terms`;
`weak_terms`;
`expansion_mode`;
`contexts`;
`activation_terms`;
`applies_to` (opcional por contexto);
`terms` contextuais.
4. Regras de expansão
A especificação deve definir:
`aliases`: termos equivalentes ou quase equivalentes;
`strong_terms`: termos fortemente relacionados;
`weak_terms`: termos relacionados, mas periféricos;
`expansion_mode: normal`: expansão pode ocorrer sem contexto adicional;
`expansion_mode: contextual`: expansão contextual só deve ocorrer quando houver evidência suficiente, como correspondência de `activation_terms` na query, `applies_to` em relação a `current_file_path` quando disponível, tags ou outro metadado acordado;
termos ambíguos não devem sofrer expansão agressiva sem contexto.
Exemplo obrigatório a considerar:
`mensageria` não deve expandir automaticamente para `rabbitmq` quando `activation_terms` e sinais disponíveis indicarem o contexto `fix` em vez de RabbitMQ.
5. Regras de carregamento da pasta
Definir o comportamento do loader:
Localizar a pasta `metadata/corpus-query-expansion-map/`.
Carregar todos os arquivos `.yml` e `.yaml`.
Ordenar os arquivos por nome para garantir composição determinística.
Validar o schema de cada arquivo.
Validar `version`.
Validar `namespace`.
Montar um índice final em memória.
Guardar `source_file` e `namespace` de cada termo para diagnóstico.
Falhar no startup se houver erro estrutural grave.
A especificação deve recomendar nomes ordenáveis como:
```text
00-core.yml
10-dotnet.yml
20-api.yml
30-data.yml
40-messaging.yml
50-observability.yml
60-security.yml
70-architecture.yml
80-governance.yml
90-project-specific.yml
```
6. Regra para duplicidade de termos
Definir política clara para termos duplicados em arquivos diferentes.
Recomendação inicial esperada:
por padrão, duplicidade de termo deve falhar no startup;
merge automático não deve ser permitido inicialmente;
override só deve ser permitido se declarado explicitamente.
Exemplo:
```yaml
terms:
  mensageria:
    override: true
    override_reason: "Neste projeto, mensageria se refere majoritariamente a FIX."
    aliases:
      - messaging
    strong_terms:
      - fix
      - session
      - heartbeat
```
A especificação deve explicar os riscos de merge automático:
expansão ampla demais;
perda de precisão;
contaminação de ranking;
dificuldade de diagnóstico.
7. Suporte a global/local
Considerar que futuramente pode existir um corpus global e um corpus específico por projeto.
Definir regra de precedência:
Carregar corpus global primeiro.
Carregar corpus local depois.
Corpus local pode adicionar termos novos.
Corpus local só pode sobrescrever termo global com `override: true` e justificativa.
Sem `override: true`, duplicidade deve gerar erro.
8. Integração com BM25
Definir que o `Corpus Query Expansion Map` não substitui BM25.
Pipeline recomendado:
```text
1. Receber query original
2. Tokenizar query original
3. Detectar termos presentes no Corpus Query Expansion Map
4. Aplicar expansão controlada
5. Rodar BM25 com query original
6. Rodar BM25 com query expandida com peso menor
7. Combinar scores
8. Aplicar boost/filtro por metadados:
   - tags
   - kind
   - priority
   - scope
   - applies_to
   - current_file_path
9. Retornar resultados com diagnóstico opcional
```
Regra obrigatória:
```text
A query original deve ter peso maior que a query expandida.
```
Exemplo conceitual:
```text
score_final =
  1.00 * bm25_original
+ 0.35 * bm25_expanded
+ 0.30 * path_match
+ 0.20 * tag_match
+ 0.10 * priority_boost
```
Os pesos devem ser configuráveis ou pelo menos centralizados.
9. Diagnóstico esperado
Quando `include_diagnostics = true`, a resposta da busca deve incluir algo semelhante a:
```json
{
  "query_expansion": {
    "enabled": true,
    "source": "corpus-query-expansion-map",
    "matched_terms": [
      {
        "term": "mensageria",
        "namespace": "messaging",
        "source_file": "40-messaging.yml",
        "expansion_mode": "contextual"
      }
    ],
    "expanded_terms": [
      {
        "term": "rabbitmq",
        "relation": "contextual",
        "context": "rabbitmq",
        "weight": 0.8,
        "source_file": "40-messaging.yml"
      }
    ],
    "skipped_terms": [
      {
        "term": "fix",
        "reason": "context_not_matched"
      }
    ]
  }
}
```
O diagnóstico deve mostrar:
query original;
termos detectados no mapa;
termos expandidos;
relação aplicada;
peso aplicado;
namespace;
source_file;
se expansão contextual foi aplicada;
termos ignorados e motivo.
10. Impacto nas tools
Analisar impacto em:
`search_instructions`
Deve usar o `Corpus Query Expansion Map` para expandir query de forma controlada.
Deve respeitar:
`current_file_path`, se existir;
tags;
kind;
scope;
priority;
`include_diagnostics`.
`list_instructions_index`
Não precisa expandir query, mas pode expor metadados que ajudem o agente a entender quais namespaces/tags existem.
`get_instructions_batch`
Não deve aplicar expansão de query, pois recebe ids. No máximo, pode retornar diagnóstico de origem do documento e metadados.
11. Processo de migração
Definir passo a passo:
Localizar todas as referências a `synonyms`.
Criar o novo modelo `CorpusQueryExpansionMap`.
Criar loader para pasta `corpus-query-expansion-map/`.
Criar schema de validação dos YAML.
Migrar o arquivo antigo de sinônimos para múltiplos arquivos YAML agrupados.
Renomear classes, métodos, variáveis e testes.
Atualizar documentação.
Atualizar logs e diagnósticos.
Manter compatibilidade temporária se necessário, mas marcando `synonyms` como deprecated.
Criar testes comparando:
BM25 puro;
BM25 + expansão antiga;
BM25 + Corpus Query Expansion Map.
Validar queries ambíguas, especialmente:
mensageria RabbitMQ;
mensageria FIX;
validação API;
logs/secrets;
transação SQL;
health/readiness;
resiliência HttpClient.
12. Critérios de aceite
Gerar critérios objetivos, incluindo:
nenhuma referência pública ao termo `synonyms` deve permanecer;
loader carrega múltiplos arquivos YAML de forma determinística;
duplicidade sem override falha;
override explícito funciona com justificativa;
diagnóstico mostra `namespace` e `source_file`;
expansão contextual só ocorre quando contexto bater;
BM25 original continua tendo maior peso que expansão;
testes cobrem termos normais e termos ambíguos;
configuração inválida falha com erro claro;
documentação explica que o mapa não é dicionário de sinônimos.
Restrições
Não tratar todos os termos como sinônimos equivalentes.
Não aplicar expansão agressiva em termos ambíguos.
Não deixar o mapa hardcoded no código.
Não substituir BM25 pelo mapa.
Não criar solução complexa demais para a primeira versão.
Priorizar implementação incremental, testável e compatível com o MCP atual.
Formato da resposta esperado
Gere uma especificação técnica em Markdown com as seções:
Visão geral
Problema atual
Novo conceito: Corpus Query Expansion Map
Nomenclatura oficial
Estrutura de diretórios proposta
Estrutura YAML proposta
Regras de carregamento e composição
Regras de duplicidade, merge e override
Regras de expansão
Integração com BM25
Diagnóstico esperado
Impacto nas tools
Processo de migração
Impactos no código
Impactos nos testes
Critérios de aceite
Riscos e mitigação
Use linguagem objetiva, técnica e sem floreios.
```