# Análise Técnica de Estratégias para Substituição de `.github/instructions` com MCP no GitHub Copilot

## 1. Objetivo do documento

Este documento consolida os pontos arquiteturais levantados ao longo da pesquisa e organiza uma análise técnica comparativa para apoiar a decisão entre diferentes estratégias de uso de MCP (Model Context Protocol) com GitHub Copilot, com foco no seguinte objetivo principal:

> **Substituir ou complementar o uso de `.github/instructions` como mecanismo principal de composição de contexto para o time**, preservando qualidade de resposta, desempenho percebido durante o desenvolvimento, governança do conteúdo e possibilidade de evolução futura.

O documento não parte de uma conclusão pré-definida. A intenção é comparar cenários, explicitar trade-offs e deixar claro **o que cada abordagem atende bem, onde ela falha, qual a complexidade de implementação e como pode evoluir**.

---

## 2. Contexto consolidado do problema

O cenário atual considera um repositório de instruções customizadas consumidas por um MCP utilizado pelo Copilot. No modelo atual/local:

- o MCP opera via **STDIO**;
- ele aponta para uma pasta local para leitura/indexação dos arquivos;
- para obter novas instruções, o desenvolvedor normalmente teria que atualizar esse conteúdo manualmente, por exemplo fazendo `pull` do repositório;
- isso cria risco de divergência entre ambientes, esquecimento de atualização e inconsistência de contexto entre desenvolvedores.

A partir disso, surgiram três linhas de investigação:

1. **MCP local via STDIO com atualização manual ou semiautomática**;
2. **MCP central via HTTP**, servindo contexto remotamente;
3. **modelo híbrido**, em que a distribuição é centralizada, mas a execução/composição principal continua local.

Também surgiu uma discussão complementar importante:

- **o MCP deve expor principalmente _tools_, _resources_ ou _prompts_?**
- como isso muda quando o objetivo principal não é “executar ações”, mas sim **substituir instruções de projeto que hoje vivem em `.github/instructions`**?

---

## 3. Base documental e fatos relevantes

O GitHub documenta que os arquivos de custom instructions do repositório fornecem ao Copilot **contexto adicional sobre como entender o projeto e como construir, testar e validar mudanças**. Isso confirma que `.github/instructions` e `copilot-instructions.md` são mecanismos voltados a comportamento persistente e contexto de projeto, não apenas snippets de prompt ad hoc. citeturn458046search0turn458046search19

A documentação do GitHub também distingue **custom instructions** de **prompt files**: custom instructions fornecem orientação contínua para o comportamento do Copilot, enquanto prompt files definem prompts reutilizáveis para tarefas específicas e são invocados sob demanda. citeturn458046search15turn458046search4

Sobre MCP, o GitHub o descreve como a forma de **estender o Copilot por integração com outros sistemas**, e a documentação do protocolo define que MCP conecta aplicações de IA a **data sources, tools e workflows especializados, incluindo prompts**. Isso é importante porque indica que o MCP pode entregar valor não apenas com tools executáveis, mas também com recursos e prompts. citeturn458046search12turn458046search1

A especificação do MCP também diferencia claramente os transportes **STDIO** e **HTTP**, e a orientação atual segue no sentido de que clientes devem suportar `stdio` sempre que possível; já os transportes HTTP trazem preocupações adicionais de autorização e operação distribuída. citeturn458046search1turn458046search6turn458046search18

A própria evolução do ecossistema MCP mostra que **STDIO** nasceu muito forte para integração local, enquanto o crescimento de cenários remotos e distribuídos puxou a evolução do transporte HTTP e temas como escalabilidade, middleware e operação distribuída. citeturn458046search11turn458046search14

---

## 4. Pergunta arquitetural central

A pergunta central não é apenas “STDIO ou HTTP?”, mas sim:

> **Qual arquitetura atende melhor a substituição de `.github/instructions` como mecanismo principal de contexto do time, equilibrando desempenho, governança, distribuição, isolamento e capacidade de evolução?**

Essa pergunta pode ser decomposta em outras:

- Onde o contexto deve residir: localmente, centralmente ou em camadas?
- A prioridade principal é latência percebida ou governança central?
- O sistema precisa ser multi-time desde o início?
- O conteúdo deve ser entregue como prompt persistente, recurso pesquisável, tool, ou combinação?
- O update deve ser automático, assistido ou manual?
- O objetivo é resolver o problema do time agora ou criar uma plataforma corporativa desde já?

---

## 5. Hipóteses e premissas consolidadas

As análises abaixo partem das seguintes premissas levantadas nas discussões:

1. O objetivo imediato é **substituir ou complementar `.github/instructions`**, não construir uma plataforma universal de agente corporativo.
2. O consumidor principal é **desenvolvedor**, não usuário final leigo.
3. O contexto é **fortemente específico por time/projeto**.
4. Há preocupação real com **desempenho percebido durante o fluxo de desenvolvimento**, especialmente quando o Copilot precisa fazer várias consultas para compor contexto.
5. O time deseja manter possibilidade de evolução para:
   - distribuição centralizada;
   - arquitetura híbrida;
   - eventual cenário server-based no futuro.
6. A solução deve ser analisada sem viés prévio para STDIO ou HTTP.

---

## 6. Papel de `.github/instructions`, `copilot-instructions.md`, prompt files e MCP

### 6.1 `.github/instructions` e `copilot-instructions.md`

Esses mecanismos são adequados para:

- orientação persistente;
- estilo de projeto;
- convenções;
- prioridades de build/test/validation;
- comportamento recorrente esperado do Copilot.

São fracos quando:

- o volume de contexto cresce demais;
- há necessidade de atualização/versionamento mais sofisticado;
- o conteúdo precisa ser particionado ou buscado dinamicamente;
- deseja-se reduzir manutenção direta no repositório do projeto ou evitar duplicação entre projetos.

### 6.2 Prompt files

Prompt files funcionam melhor para:

- tarefas específicas e invocáveis;
- fluxos repetitivos com entrada/saída previsível;
- templates de trabalho (ex.: criar endpoint, documentar API, gerar plano de onboarding).

Eles não substituem integralmente instruções persistentes de projeto, porque sua natureza é mais **task-oriented** do que **behavior-oriented**. citeturn458046search15turn458046search22

### 6.3 MCP com tools, resources e prompts

Para o caso em análise, o MCP não precisa ser visto apenas como um catálogo de tools. O protocolo admite uso para **dados, tools e workflows especializados/prompting**. citeturn458046search1turn458046search12

Por isso, há três formas arquiteturais plausíveis:

- **MCP orientado a tools**: o Copilot chama operações que buscam contexto específico ou realizam atualização;
- **MCP orientado a resources**: o Copilot acessa conteúdos estruturados, categorizados e recuperáveis;
- **MCP orientado a prompts/workflows**: o MCP expõe modelos de instrução reutilizáveis por tipo de tarefa.

### 6.4 Implicação prática

Para substituir ou complementar `.github/instructions`, é útil separar o problema em **dois sub-problemas distintos**, que pedem mecanismos diferentes:

1. **Base persistente (o que deve estar sempre “ligado”)**: princípios, políticas e convenções curtas que precisam valer em toda interação. Aqui, **instructions nativas mínimas** e/ou **resources canônicos** funcionam bem porque são estáveis, rastreáveis e auditáveis.
2. **Seleção/retrieval (qual subconjunto usar agora, com controle de custo)**: descobrir rapidamente *quais* instruções são relevantes para um arquivo/tarefa e trazer **apenas** o necessário (top‑K, filtro por tags/scope, truncagem por tamanho). Aqui, **tools** são o mecanismo mais forte, pois executam filtragem e ordenação de forma determinística e parametrizada (ex.: `search` + `get` com `max_chars`).

Implicação: **prompts não substituem retrieval**. Prompts são templates de texto (com argumentos), úteis para padronizar interação e formato de saída; já **tools** carregam a “capacidade” de busca/seleção/truncagem. Na prática, o padrão “thin per-repo” pode funcionar como *pseudo-hook* para orquestrar quando chamar as tools (dado que não há hooks proativos), enquanto o corpus governado vive no MCP como resource/conteúdo.

---

## 7. Cenários analisados

## 7.1 Cenário A — MCP local via STDIO

### Descrição

O MCP roda localmente, via `stdio`, lendo conteúdo já disponível na máquina do desenvolvedor.

### O que esse cenário atende bem

- baixa latência local;
- menor dependência de rede durante a composição de contexto;
- forte aderência ao contexto específico do projeto/time;
- isolamento natural por ambiente/repositório;
- simplicidade operacional inicial;
- menor superfície de segurança do que um servidor remoto multi-tenant.

### O que esse cenário atende mal

- distribuição e atualização do conteúdo;
- governança central imediata;
- garantia de uniformidade de versão entre todos os devs;
- observabilidade corporativa consolidada;
- revogação ou rollout central instantâneo.

### Calcanhar de Aquiles

**Distribuição de contexto**.  
Sem mecanismo de atualização, cada máquina pode ficar com uma versão diferente.

### Complexidade de implementação

**Baixa a média**, dependendo do nível de automação de update.

### Quando faz mais sentido

- quando o foco principal é desempenho percebido;
- quando o contexto é específico de time/projeto;
- quando se quer resolver a dor atual sem criar uma plataforma distribuída;
- quando a organização ainda não precisa de governança forte multi-time.

---

## 7.2 Cenário B — MCP local via STDIO com AutoUpdate

### Descrição

Mantém-se a execução local via `stdio`, mas adiciona-se um mecanismo de atualização de conteúdo, idealmente baseado em artefato versionado (por exemplo release), staging, validação e swap.

### O que esse cenário atende bem

- preserva as vantagens de desempenho do local;
- reduz divergência entre ambientes;
- permite governança melhor que o modelo totalmente manual;
- mantém baixo acoplamento com infraestrutura remota durante uso interativo;
- permite rollout por canal/versionamento.

### O que esse cenário atende mal

- ainda não entrega governança central completa;
- continua exigindo alguma lógica local por máquina;
- pode introduzir complexidade de lifecycle, cache e reindexação.

### Calcanhar de Aquiles

**Coordenação de atualização sem degradar a experiência do dev**.  
Se a atualização ocorrer no momento errado ou sem transparência, pode gerar inconsistência de sessão.

### Complexidade de implementação

**Média**.

### Observação importante

Este cenário pode ter três submodos:

- **manual**: o dev escolhe atualizar;
- **assistido via chat**: o sistema detecta nova versão e pergunta se deve baixar/aplicar;
- **automático com política**: update no startup ou em intervalo.

---

## 7.3 Cenário C — MCP central via HTTP

### Descrição

O contexto é servido por um MCP remoto via HTTP.

### O que esse cenário atende bem

- centralização;
- atualização única e imediata;
- potencial de observabilidade central;
- maior controle sobre rollout e versionamento;
- possibilidade de compartilhar padrões entre múltiplos times;
- menor esforço de sincronização local de conteúdo.

### O que esse cenário atende mal

- latência acumulada em composições com múltiplas chamadas;
- maior dependência de rede, disponibilidade e autenticação;
- necessidade de projeto de multi-tenancy/isolamento;
- risco de mistura de contexto entre times se o desenho for ingênuo;
- maior esforço operacional e de segurança.

### Calcanhar de Aquiles

**Multi-tenancy + latência + governança de escopo**.  
Se o servidor for central mas o contexto for específico por time, é obrigatório decidir como o sistema identifica qual contexto entregar a cada cliente/projeto. Isso não pode ficar dependente apenas de prompt.

### Complexidade de implementação

**Média a alta**, podendo chegar a **alta** rapidamente em cenário corporativo multi-time.

### Quando faz mais sentido

- quando a prioridade é governança central;
- quando múltiplos times precisam operar sob política comum;
- quando uniformidade e auditoria são mais importantes que latência local;
- quando há capacidade real de operar o serviço com segurança e observabilidade.

---

## 7.4 Cenário D — Arquitetura híbrida

### Descrição

A origem do conteúdo é centralizada, mas a composição principal do contexto continua local. Em vez de um servidor HTTP servir cada consulta, ele pode distribuir manifesto, release ou pacote versionado; o MCP local consome esse material.

### O que esse cenário atende bem

- governança central de distribuição;
- desempenho local durante uso;
- menor risco de latência acumulada em cada consulta;
- melhor isolamento por time do que um servidor remoto genérico;
- evolução gradual sem ruptura.

### O que esse cenário atende mal

- exige implementação em duas camadas;
- precisa de desenho claro de versionamento e cache;
- adiciona alguma complexidade de sincronização local;
- pode ficar mais complexo de explicar do que as abordagens “puras”.

### Calcanhar de Aquiles

**Complexidade de coordenação entre distribuição central e uso local**.

### Complexidade de implementação

**Média a alta**, mas mais controlável do que um HTTP central full multi-tenant para todos os fluxos desde o início.

---

## 8. Comparativo técnico

| Critério | STDIO local | STDIO + AutoUpdate | HTTP central | Híbrido |
|---|---|---:|---:|---:|
| Desempenho percebido | Alto | Alto | Médio a variável | Alto |
| Dependência de rede durante uso | Baixa | Baixa | Alta | Baixa |
| Governança central | Baixa | Média | Alta | Alta |
| Uniformidade de versão | Baixa | Média/Alta | Alta | Alta |
| Complexidade inicial | Baixa | Média | Média/Alta | Média |
| Complexidade operacional | Baixa | Média | Alta | Média/Alta |
| Isolamento por time/projeto | Alto | Alto | Depende do desenho | Alto |
| Risco de latência acumulada | Baixo | Baixo | Médio/Alto | Baixo |
| Observabilidade central | Baixa | Média | Alta | Média/Alta |
| Facilidade de evolução incremental | Média | Alta | Média | Alta |
| Risco de vazamento entre times | Baixo | Baixo | Depende muito do tenancy | Baixo/Médio |

---

## 9. Latência e composição de contexto

Um ponto levantado na pesquisa foi o impacto de latência em interações sucessivas. O problema não é apenas o custo de uma única chamada, mas o **efeito cascata** em cenários em que o Copilot precisa descobrir contexto em múltiplas etapas.

Exemplos de composição:

- construir apenas um controller;
- construir um endpoint ponta a ponta;
- aplicar regras de observabilidade;
- inferir convenções de teste, validação, logging e padrões REST.

Nesses cenários, mesmo uma latência relativamente baixa por operação pode se acumular quando o modelo precisa consultar várias vezes as mesmas classes de informação. Por isso, **a viabilidade do HTTP central não deve ser avaliada apenas por “ms por chamada”, mas pelo perfil de encadeamento de consultas necessário para compor contexto de desenvolvimento**.

Isso não invalida HTTP. Significa apenas que, para um caso focado em substituir instruções de projeto usadas repetidamente durante coding flow, o custo acumulado precisa entrar fortemente na análise.

---

## 10. Multi-time e isolamento de contexto

Se vários times tiverem instructions próprias, um servidor HTTP central precisa decidir corretamente **qual contexto pertence a qual time/projeto**.

Possíveis estratégias:

- segmentação por repositório;
- segmentação por workspace;
- segmentação por identidade/grupo;
- namespace por time;
- instância lógica dedicada por domínio;
- servidor dedicado por time.

### Observação crítica

`copilot-instructions.md` pode ajudar a **orientar** o Copilot sobre qual MCP usar ou qual namespace priorizar, mas **não deve ser a única barreira de isolamento**. O isolamento real precisa existir na modelagem de tenant, autorização e resolução de escopo, especialmente em servidor HTTP. Isso decorre do fato de que o próprio MCP trata autorização como tema importante no transporte HTTP. citeturn458046search6turn458046search18

---

## 11. Tools vs prompts vs resources para substituir `.github/instructions`

> **Nota de escopo (base vs retrieval):** “substituir `.github/instructions`” não é uma única coisa. Há uma camada de **base persistente** e uma camada de **retrieval seletivo**. Prompts e resources ajudam mais na primeira; tools são críticas para a segunda.

## 11.1 Quando usar tools

Tools fazem mais sentido para:

- descobrir contexto filtrado;
- executar atualização/check de versão;
- acionar reindexação;
- obter pacotes por categoria;
- fornecer resumos dinâmicos por tipo de tarefa.

Exemplos:
- `knowledge_status`
- `knowledge_check_update`
- `knowledge_download_update`
- `knowledge_apply_update`
- `knowledge_get_for_task(taskType)`

## 11.2 Quando usar resources

Resources fazem mais sentido para:

- representar instruções categorizadas por domínio;
- armazenar padrões reutilizáveis de projeto;
- expor regras estruturadas por assunto;
- manter o corpo principal de conhecimento sem precisar “executar” tudo como tool.

Exemplos:
- `architecture/rest-guidelines`
- `observability/logging-patterns`
- `endpoint/e2e-checklist`
- `testing/api-test-conventions`

## 11.3 Quando usar prompts

Prompts fazem mais sentido para:

- fornecer **templates de interação** (roteiros) para tarefas recorrentes;
- orientar tarefas recorrentes;
- padronizar formato de entrada/saída e checklist de execução para classes de tarefa.

Exemplos:
- “Criar endpoint ponta a ponta”
- “Aplicar observabilidade ao componente”
- “Gerar controller alinhado ao padrão do time”

### Conclusão dessa seção

Se o objetivo é substituir `.github/instructions`, uma abordagem **somente** com prompts (ou somente com resources) tende a falhar no ponto mais sensível: **selecionar o subconjunto certo na hora certa** com controle de tamanho/escopo. Por outro lado, uma abordagem **somente** com tools pode virar procedural demais se ela tentar carregar também a função de “base persistente”.

Uma composição mais aderente ao problema é:

- **instructions nativas mínimas** (thin) como *pseudo-hook* e hierarquia (“regras locais > MCP”), orquestrando quando chamar tools;
- **resources** como fonte canônica e endereçável do conhecimento (documentos governados);
- **tools** para discovery/retrieval determinístico (ex.: matching por `scope`/priority para o arquivo sendo editado, busca top‑K, `get` com `max_chars`) e para operações de lifecycle (diff por hash, update);
- **prompts** para templates curtos e reutilizáveis que guiam a execução (checklists e formatos), *após* o retrieval correto ter trazido as evidências certas.

---

## 12. Estratégias de update

## 12.1 Update manual

### Vantagens
- simples;
- previsível;
- menor automação inicial.

### Desvantagens
- alta chance de esquecimento;
- drift entre máquinas;
- pouca governança.

## 12.2 Update automático cego

### Vantagens
- padronização rápida;
- menos esforço manual.

### Desvantagens
- troca de contexto no meio da sessão;
- risco de reload inesperado;
- maior dificuldade de troubleshooting.

## 12.3 Update assistido via chat

### Vantagens
- equilibra automação e controle;
- boa experiência para dev;
- baixo atrito para uma primeira versão;
- permite staging, validação e swap sob confirmação.

### Desvantagens
- ainda exige interação humana;
- precisa de UX clara no Copilot/MCP.

### Fluxo sugerido

1. detectar nova versão;
2. baixar para `staging`;
3. validar conteúdo;
4. informar ao dev que há atualização disponível;
5. oferecer aplicação da nova versão;
6. fazer swap atômico;
7. recarregar contexto;
8. manter rollback.

Este fluxo foi considerado particularmente aderente ao perfil do usuário final, já que o consumidor é um desenvolvedor com maturidade técnica para compreender ciclo de versão e atualização.

---

## 13. Caminhos de adoção por estágio

## Caminho 1 — Resolver a dor atual com menor risco

**Objetivo:** reduzir dependência de `.github/instructions` e minimizar esforço operacional inicial.

Possível composição:
- MCP local via STDIO;
- resources como base principal;
- prompts para tarefas recorrentes;
- tools para status e update;
- update assistido via chat;
- pacote versionado por release.

**Atende melhor:** desempenho, aderência ao projeto, simplicidade incremental.

---

## Caminho 2 — Preparar governança sem abrir mão do local

**Objetivo:** aumentar controle e padronização mantendo desempenho local.

Possível composição:
- manifesto central;
- distribuição centralizada de pacotes;
- cache local;
- execução via STDIO;
- canais `stable/beta`;
- política de startup check.

**Atende melhor:** equilíbrio entre governança e UX do dev.

---

## Caminho 3 — Evoluir para plataforma multi-time

**Objetivo:** atender vários times com maior centralização.

Possível composição:
- servidor HTTP com tenancy explícito;
- autenticação/autorização;
- namespace por time ou por repositório;
- observabilidade central;
- fallback local ou cache.

**Atende melhor:** escala organizacional, padronização, auditoria.

**Risco principal:** complexidade de plataforma.

---

## 14. Perguntas que devem decidir o caminho

Antes da decisão final, a arquitetura deve responder com clareza:

1. O objetivo principal é **desempenho de composição de contexto** ou **governança central**?
2. A necessidade multi-time é imediata ou futura?
3. O contexto é altamente específico por projeto ou há forte reutilização transversal?
4. O time quer uma solução de produto interno simples ou uma plataforma corporativa?
5. A equipe está disposta a operar autorização, tenancy e observabilidade em um MCP HTTP?
6. O repositório de instructions deve ser tratado como artefato versionado?
7. O update pode depender de confirmação do dev sem comprometer o objetivo do projeto?
8. O Copilot precisa principalmente de:
   - instrução persistente,
   - descoberta dinâmica,
   - workflow pronto,
   - ou combinação dessas três coisas?

---

## 15. Conclusões técnicas neutras

### 15.1 O que o cenário STDIO atende melhor

- uso fortemente contextual ao time/projeto;
- fluxo de coding com muitas composições de contexto;
- necessidade de baixa latência percebida;
- adoção incremental com menor risco;
- substituição prática de `.github/instructions` no curto prazo.

### 15.2 O que o cenário HTTP atende melhor

- governança central;
- política corporativa multi-time;
- atualização única e imediata;
- observabilidade consolidada;
- necessidade de padronização forte entre consumidores.

### 15.3 O que o híbrido atende melhor

- evolução controlada;
- distribuição central com uso local;
- equilíbrio entre governança e desempenho;
- transição sem ruptura.

### 15.4 Ponto técnico importante

O problema em estudo **não é apenas de transporte**, mas de **modelo de distribuição e recuperação de contexto**.  
Escolher entre STDIO e HTTP sem definir corretamente o papel de resources, prompts, tools, versionamento, tenancy e update tende a gerar uma decisão incompleta.

---

## 16. Direção de análise recomendada para a próxima IA

Para um próximo documento mais decisório, recomenda-se que a IA avalie explicitamente:

1. **Mapa de requisitos**
   - desempenho;
   - multi-time;
   - governança;
   - versionamento;
   - UX do dev;
   - segurança;
   - observabilidade;
   - custo operacional.

2. **Modelo conceitual do contexto**
   - o que vira resource;
   - o que vira prompt;
   - o que vira tool;
   - o que fica ainda em `copilot-instructions.md`.

3. **Modelo de update**
   - manual;
   - assistido via chat;
   - startup check;
   - automático;
   - rollback.

4. **Estratégia evolutiva**
   - fase 1: local;
   - fase 2: local com distribuição central;
   - fase 3: híbrido;
   - fase 4: HTTP central, se necessário.

5. **Critérios de decisão**
   - quando STDIO é suficiente;
   - quando híbrido passa a valer;
   - quando HTTP deixa de ser “overengineering” e passa a ser justificável.

---

## 17. Síntese final

A pesquisa levantou corretamente que:

- **`.github/instructions` resolve orientação persistente, mas escala mal como único mecanismo de contexto vivo**; citeturn458046search0turn458046search19
- **MCP não precisa ser reduzido a tools**; ele também pode estruturar recursos e prompts especializados; citeturn458046search1turn458046search12
- **STDIO e HTTP atendem prioridades diferentes**, e a decisão depende mais do objetivo arquitetural do que de preferência tecnológica; citeturn458046search1turn458046search6turn458046search14
- **substituir `.github/instructions` com foco em desenvolvimento interativo** exige olhar com muito peso para composição de contexto, latência acumulada, granularidade do conhecimento e experiência do desenvolvedor;
- **uma arquitetura híbrida é uma evolução plausível** quando há interesse em combinar distribuição central com execução local.

Este documento, portanto, não fecha a decisão. Ele organiza a base técnica para que uma próxima análise possa construir um direcionamento arquitetural mais prescritivo, com base em requisitos priorizados e cenários de adoção.

---

## 18. Fontes

1. GitHub Docs — Adding repository custom instructions for GitHub Copilot  
   https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot

2. GitHub Docs — Configure custom instructions for GitHub Copilot  
   https://docs.github.com/en/copilot/how-tos/configure-custom-instructions

3. GitHub Docs — Prompt files  
   https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files

4. GitHub Docs — Your first custom instructions  
   https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions/your-first-custom-instructions

5. GitHub Docs — About Model Context Protocol (MCP)  
   https://docs.github.com/en/copilot/concepts/context/mcp

6. Model Context Protocol — Getting Started / Intro  
   https://modelcontextprotocol.io/docs/getting-started/intro

7. Model Context Protocol — Authorization  
   https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization

8. Model Context Protocol — Understanding Authorization in MCP  
   https://modelcontextprotocol.io/docs/tutorials/security/authorization

9. Model Context Protocol — Roadmap  
   https://modelcontextprotocol.io/development/roadmap

10. MCP Governance / Roadmap commentary  
    https://blog.modelcontextprotocol.io/tags/governance/
