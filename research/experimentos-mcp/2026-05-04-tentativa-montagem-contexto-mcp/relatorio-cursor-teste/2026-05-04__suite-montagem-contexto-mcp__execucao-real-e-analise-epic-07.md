# Suite de montagem de contexto MCP — execucao real e analise contra EPIC-07

## Escopo

Este relatorio registra a execucao real da suite definida em `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`, usando como orquestrador `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/copilot-instructions-mcp.md`.

Objetivo da rodada:

- validar o roteamento de contexto do MCP em `stdio`;
- registrar o placar atual da suite de 24 testes;
- cruzar os fails observados com as hipoteses `I-01` a `I-07` do `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`.

## Configuracao da rodada

- Data: `2026-05-04`
- Transporte: `MCP stdio`
- Servidor executado: `python -m corporate_instructions_mcp`
- Diretorio de execucao: `C:\_projeto\Copilot-Research\mcp-instructions-server`
- Corpus: `C:\_projeto\Copilot-Research\fixtures\instructions`
- Suite alvo: `testes-basicos-montagem-contexto-mcp.md`
- Orquestrador usado: `copilot-instructions-mcp.md`
- Ferramentas exercitadas por caso:
  - `get_context_triggers`
  - `resolve_instruction_context`
  - `get_instructions_batch`
  - `validate_applicability`

Antes da suite, foi executado o smoke real `mcp-instructions-server/scripts/run_epic05_stdio_real_check.py`, com resultado positivo. Isso confirma que o servidor subiu corretamente, respondeu via `stdio` e expôs o contrato MCP esperado.

## Metodo de execucao

Para cada um dos 24 casos do roteiro:

1. foi montado um payload para `get_context_triggers` compatível com o protocolo do orquestrador;
2. foi chamada `resolve_instruction_context(query, max_results=7, include_diagnostics=true)`;
3. os `selected_ids` retornados foram lidos novamente via `get_instructions_batch`;
4. os mesmos IDs foram passados para `validate_applicability`, usando `target_artifact.path = "Api/Endpoints/ClienteEndpoints.cs"` e `workspace_evidence = []`.

O criterio de `pass/fail` da suite foi o do proprio roteiro:

- todos os `primary_ids` presentes em `selected_ids`;
- pelo menos um `supporting_id` presente;
- nenhum ID marcado como "nao priorizar" entre os 2 primeiros;
- para `T24`, os 3 temas principais presentes no top-5.

Importante: `validate_applicability` foi executada como parte da orquestracao, mas nao entrou no calculo do placar final. Com evidencias vazias, era esperado observar muitos casos `hypothesis_only` ou `non_applicable`.

## Resultado consolidado

### Placar

- Total: `24`
- Aprovados: `7`
- Reprovados: `17`
- Veredicto da suite: **reprovada**

### Casos aprovados

- `T05` Observabilidade (baseline)
- `T14` Saga e compensacao
- `T15` Validacao 400 vs 422
- `T17` API de colecoes
- `T22` Estrategia de testes
- `T23` Cache em leitura
- `T24` Pergunta hibrida

### Casos reprovados

- `T01`, `T02`, `T03`, `T04`
- `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`, `T13`
- `T16`, `T18`, `T19`, `T20`, `T21`

## Leitura executiva

O MCP respondeu de forma estavel, o batch foi consistente com os IDs selecionados em todos os casos observados, e a tool `get_context_triggers` retornou contratos coerentes com o tipo de pedido. O problema principal nao foi operacional; foi de **qualidade de selecao/ranking**.

O padrao geral dos fails mostra tres classes dominantes:

- ruido semantico em queries tecnicas, especialmente arquitetura, integracao e SQL;
- ausencia recorrente de `supporting_ids` esperados, mesmo quando os `primary_ids` apareciam;
- contaminacao por documentos de meta-governance ou por documentos tecnicamente vizinhos, mas fora do foco da pergunta.

## Evidencias sinteticas por grupo

### 1. Arquitetura e organizacao ainda sofrem com ruido forte

Casos: `T01`, `T02`, `T03`, `T04`

Sinais observados:

- `T01` trouxe `microservice-opentelemetry-correlation-and-health` em primeiro e `microservice-messaging-rabbitmq-publish-consume` em quarto, apesar de ambos constarem como "nao priorizar" ou fora do foco principal.
- `T03` incluiu `assistant-workflow-bmad-planning-and-controlled-inference`.
- `T04` incluiu `instruction-authoring-standard`.

Leitura:

- arquitetura ainda nao isola bem o dominio procurado;
- documentos de meta-governance continuam entrando no pool de busca tecnica;
- ha indicio de score excessivo por conectivos e termos genericos em portugues.

### 2. Integracao e observabilidade ainda misturam dominios adjacentes

Casos: `T06`, `T07`, `T08`, `T09`, `T10`, `T11`, `T12`

Sinais observados:

- `T06` foi dominado por docs de API/erro e nao por observabilidade + integracao.
- `T08` trouxe `microservice-integration-httpclientfactory-contracts` e `microservice-opentelemetry-correlation-and-health`, mas nao trouxe `microservice-data-access-and-sql-security`.
- `T09` trouxe `httpclientfactory` e `resilience`, mas nao trouxe `microservice-di-options-extensions`.
- `T10` trouxe `instruction-authoring-standard` no top-2.
- `T11` acertou os `primary_ids`, mas falhou por nao trazer o `supporting_id` esperado de observabilidade.
- `T12` nao trouxe `microservice-api-validation-and-error-contracts` nem `microservice-api-error-catalog-baseline`.

Leitura:

- o sistema ainda mistura integracao HTTP, contratos REST, resiliencia, sagas e documentos genericos quando a query fica mais natural;
- os caminhos de expansao parecem fortes para vizinhos tecnicos, mas fracos para o contexto realmente esperado pelo roteiro.

### 3. Seguranca, SQL e contrato publico ainda tem cobertura parcial

Casos: `T16`, `T18`, `T19`, `T20`, `T21`

Sinais observados:

- `T16` nao trouxe `microservice-api-error-catalog-baseline`.
- `T18` trouxe os 3 `primary_ids`, mas falhou por nao incluir `microservice-api-error-catalog-baseline` como `supporting_id`.
- `T19` nao trouxe `example-security-baseline`.
- `T20` trouxe `example-security-baseline`, mas nao trouxe `microservice-configuration-production-readiness` nem `artifact-encoding-line-endings-and-unicode`.
- `T21` trouxe `microservice-data-access-and-sql-security`, mas nao trouxe `microservice-configuration-production-readiness` e ainda incluiu `instruction-authoring-standard`.

Leitura:

- o cluster de seguranca/secrets/logging ainda nao esta bem conectado a readiness/configuracao;
- o cluster SQL/transacao/timeout ainda nao puxa `configuration-production-readiness` como esperado no roteiro;
- contratos de erro ainda ficam subrepresentados em algumas queries de API.

## Cruzamento com o EPIC-07

### I-01 — Stopwords PT ausentes

Hipotese do epic:

- conectivos como `como`, `deve`, `ser`, `qual`, `quando`, `me` inflacionam score de documentos irrelevantes.

Compatibilidade com esta rodada: **muito alta**

Evidencias desta execucao:

- `T01` priorizou observabilidade e mensageria numa query de arquitetura em linguagem natural.
- `T03`, `T04`, `T12`, `T20` e `T21` continuam mostrando mistura de documentos genericos ou adjacentes quando a query usa formulacoes naturais.
- o padrao de ruido aparece em varios dominios, o que combina com causa-raiz de scoring ampla, nao com bug isolado por tema.

Leitura:

- os resultados atuais continuam consistentes com a hipotese de que o scoring lexical baseline ainda esta excessivamente sensivel a stopwords PT.

### I-02 — `bmad` e `instruction-authoring-standard` como ruido sistemico

Hipotese do epic:

- docs de meta-governance entram em queries tecnicas por `scope` amplo + `priority` + efeito de `I-01`.

Compatibilidade com esta rodada: **alta**

Evidencias desta execucao:

- `T03`, `T05`, `T07`, `T12`, `T13` trouxeram `assistant-workflow-bmad-planning-and-controlled-inference`.
- `T04`, `T10`, `T21` trouxeram `instruction-authoring-standard`.

Leitura:

- a contaminacao por meta-governance continua real;
- a rodada atual confirma a causa descrita em `I-02`, ainda que nem sempre no top-3.

### I-03 — mismatch de ID em `example-security-baseline`

Hipotese do epic:

- `example-security-baseline.md` declarava `id` divergente, impedindo recuperacao pelo ID esperado.

Compatibilidade com esta rodada: **baixa no estado atual**

Evidencias desta execucao:

- `T18` e `T20` retornaram `example-security-baseline` em `selected_ids`;
- `get_instructions_batch` devolveu esse ID normalmente.

Leitura:

- o problema descrito em `I-03` nao se manifestou nesta rodada;
- isso sugere que o estado atual do workspace/corpus ja nao corresponde mais ao baseline descrito no epic, ou que a fixture local disponivel para execucao ja foi ajustada.

### I-04 — `configuration-production-readiness` suprimido em observabilidade e health

Hipotese do epic:

- faltam sinonimos/ligacoes entre observabilidade, health/live/ready e `microservice-configuration-production-readiness`.

Compatibilidade com esta rodada: **parcial**

Evidencias desta execucao:

- `T05` passou e trouxe `microservice-configuration-production-readiness`.
- `T07` tambem trouxe `microservice-configuration-production-readiness`.
- `T20` e `T21`, embora nao sejam os cenarios centrais de `I-04`, falharam justamente por nao trazer esse documento como apoio esperado.

Leitura:

- o problema descrito em `I-04` parece **melhor do que no baseline do epic** para observabilidade/health estritos;
- ainda existe lacuna de conectividade com queries de secrets/logging/SQL/readiness.

### I-05 — expansao cruzada indevida de resiliencia/DNS

Hipotese do epic:

- `dns-retry-pattern` invade queries de resiliencia HTTP/Polly por expansao bidirecional indevida.

Compatibilidade com esta rodada: **nao observada diretamente**

Evidencias desta execucao:

- nenhum dos fails principais mostrou `dns-retry-pattern` como ruido recorrente.

Leitura:

- esta rodada nao refuta `I-05`, mas tambem nao a reforca;
- o problema pode existir sem ter sido acionado pelas 24 queries desta rodada especifica.

### I-06 — queries multi-tema nao garantem representacao no top-5

Hipotese do epic:

- em queries compostas, o top-5 tende a ser dominado por um tema ou por ruido de scoring.

Compatibilidade com esta rodada: **baixa nesta execucao**

Evidencias desta execucao:

- `T24` passou;
- os tres temas esperados apareceram no top-5: arquitetura, observabilidade e integracao externa.

Leitura:

- pelo menos no caso hibrido do roteiro, o problema descrito em `I-06` nao apareceu;
- isso enfraquece a severidade atual da hipotese, embora nao a elimine para outras combinacoes de temas.

### I-07 — `api-openfinance-patterns` ausente em queries de paginacao/colecoes

Hipotese do epic:

- faltam caminhos de expansao de `paginacao`/`colecoes` para `microservice-api-openfinance-patterns`.

Compatibilidade com esta rodada: **baixa no estado atual**

Evidencias desta execucao:

- `T17` passou;
- `microservice-api-openfinance-patterns` apareceu em `selected_ids`.

Leitura:

- esta rodada nao reproduziu a falha descrita em `I-07`;
- assim como `I-03`, este ponto pode estar defasado em relacao ao estado atual do workspace.

## Mapa de cobertura das hipoteses

Hipoteses mais fortemente corroboradas por esta execucao:

- `I-01` stopwords PT ausentes
- `I-02` contaminacao por meta-governance

Hipoteses parcialmente corroboradas:

- `I-04` readiness/configuracao ainda subrepresentada fora dos casos centrais

Hipoteses nao reproduzidas nesta rodada:

- `I-03` mismatch de ID de `example-security-baseline`
- `I-05` ruido de `dns-retry-pattern`
- `I-06` falha de representacao multi-tema no caso hibrido testado
- `I-07` ausencia de `api-openfinance-patterns` em colecoes

## Interpretacao do delta em relacao ao EPIC-07

O `EPIC-07` registra baseline de `5/24`. A execucao atual resultou em `7/24`.

Leitura mais segura:

- ha **melhora pequena**, mas a suite continua muito abaixo do criterio de aprovacao (`>= 21/24`);
- o nucleo do problema permanece em **qualidade de ranking/seleção**, nao em disponibilidade do MCP;
- parte das hipoteses do epic continua atual (`I-01`, `I-02`);
- parte parece ja nao refletir integralmente o estado atual do corpus/test fixture (`I-03`, `I-07`, e parcialmente `I-04` e `I-06`).

## Conclusao

Esta rodada confirma que:

- o servidor MCP local esta funcional em `stdio`;
- a orquestracao proposta em `copilot-instructions-mcp.md` e executavel;
- a suite de 24 testes continua reprovada por **baixa precisao de roteamento**.

O diagnostico mais consistente com os dados atuais e:

1. `I-01` continua sendo a principal causa-raiz provavel;
2. `I-02` continua ativa como fonte secundaria de ruido sistemico;
3. `I-04` ainda merece tratamento, mas com escopo mais focado do que o descrito originalmente;
4. `I-03`, `I-06` e `I-07` devem ser revalidados antes de qualquer implementacao, porque o estado atual da fixture parece diferente do baseline usado no epic.

## Proximos passos recomendados

- atualizar o baseline do `EPIC-07` para registrar explicitamente esta nova rodada `7/24`;
- reexecutar os testes de reproducoes pontuais de `I-03`, `I-06` e `I-07` antes de mexer no codigo;
- atacar primeiro `I-01`, depois medir novamente a suite inteira;
- so entao decidir se `I-02` exige ajuste de `scope`, `tag` ou exclusao de busca para docs de meta-governance.
