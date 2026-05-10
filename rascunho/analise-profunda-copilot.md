# Análise Profunda — Seleção de Contexto e Arquivos de Instrução no Copilot

## 1. Fatos documentados

### 1.1 O que a documentação oficial afirma sobre montagem de contexto

**Fato documentado**

1. O Copilot Chat no Visual Studio usa uma abordagem em camadas para compor contexto.
2. Há **contexto implícito** automaticamente fornecido pelo IDE, incluindo:
   - texto selecionado no editor ativo;
   - arquivo atualmente ativo.
3. O Copilot pode usar **histórico da conversa** como parte do contexto implícito.
4. O Copilot pode usar **referências explícitas** adicionadas pelo usuário, como:
   - `#arquivo`, `#método`, `#classe`;
   - `@workspace`;
   - anexos;
   - URLs públicas estáticas;
   - logs de output.
5. Para o código do workspace, o Copilot mantém um índice:
   - **remoto** se o repositório estiver em GitHub ou Azure DevOps;
   - **local** se o código estiver hospedado em outro lugar.
6. A documentação afirma explicitamente que esse índice usa **embeddings** e que o Copilot pode executar **busca semântica** sobre esse índice quando julga precisar de mais contexto.
7. Os arquivos retornados por essa busca semântica **suplementam** system prompt, instructions, contexto implícito e conteúdo explícito fornecido pelo usuário.
8. A documentação afirma que arquivos de instrução relevantes são **automaticamente detectados** e anexados como referências.
9. Quando usados, os arquivos de instrução aparecem na lista de **References** da resposta.
10. Para `.github/instructions/*.instructions.md`, a documentação exige `applyTo` no frontmatter para o uso direcionado documentado.
11. A propriedade `description` é documentada como texto mostrado no hover na UI.
12. O comando `/generateInstructions` analisa estrutura e padrões do projeto para gerar um `copilot-instructions.md`.

### 1.2 O que é fato no repositório atual

**Fato observado no workspace**

1. Existe um arquivo `.github/copilot-instructions.md` no repositório.
2. Esse arquivo define:
   - idioma: português;
   - restrição de segurança para não incluir segredos/tokens/dados pessoais;
   - restrição de escopo para não assumir código/infra de outros serviços;
   - obrigação de consultar o MCP `corporate-instructions` em decisões cross-cutting.
3. Não foi encontrada evidência, no workspace atual, de arquivos:
   - `*.instructions.md`;
   - `*.prompt.md`.
4. Portanto, **neste repositório específico**, a única fonte de instrução em arquivo claramente presente é `.github/copilot-instructions.md`.

### 1.3 Limites do que a documentação realmente cobre

**Fato documentado**

A documentação oficial **não** explica publicamente:

- o algoritmo exato de ranking entre arquivos candidatos;
- os pesos relativos entre contexto implícito, instruções, embeddings e referências explícitas;
- o limiar que dispara busca semântica;
- se há reranking lexical + vetorial, ou apenas vetorial, ou outro arranjo híbrido;
- se o corpo textual de `description` influencia recuperação semântica;
- como conflitos entre múltiplos arquivos de instrução são resolvidos internamente.

### 1.4 Fontes desta seção

- Microsoft Learn: `How Copilot Chat understands and uses context`  
  <https://learn.microsoft.com/visualstudio/ide/copilot-context-overview?view=visualstudio>
- Microsoft Learn: `Customize chat responses and set context`  
  <https://learn.microsoft.com/visualstudio/ide/copilot-chat-context?view=visualstudio#use-custom-instructions>
- Microsoft Learn: `Manage chat context with references`  
  <https://learn.microsoft.com/visualstudio/ide/copilot-chat-context-references?view=visualstudio>
- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `assistant-workflow-bmad-planning-and-controlled-inference`
  - `instruction-authoring-standard`

## 2. Inferências plausíveis

### 2.1 Sobre busca determinística vs semântica

**Inferência plausível**

Como a documentação menciona ao mesmo tempo:

- contexto implícito;
- referências explícitas;
- índice do codebase;
- embeddings;
- busca semântica “quando necessário”;
- detecção automática de instruction files relevantes;

o comportamento mais plausível é um **pipeline híbrido**, não puramente determinístico nem puramente semântico.

Modelo plausível mínimo:

1. **contexto determinístico forte** entra primeiro;
2. **instructions always-on ou quase always-on** entram por regra de produto;
3. uma etapa posterior decide se precisa de **recuperação adicional**;
4. essa recuperação adicional usa **sinais semânticos** sobre o índice;
5. o conjunto final é podado por orçamento de contexto/tokens.

Isso é uma inferência porque a documentação não expõe o pipeline completo, mas é coerente com o comportamento descrito e com a existência simultânea de mecanismos explícitos e semânticos.

### 2.2 Sobre `copilot-instructions.md`

**Inferência plausível**

O `.github/copilot-instructions.md` parece funcionar como uma instrução de alta prioridade e ampla aplicabilidade, porque:

- a documentação o descreve como contexto reutilizável para a sessão/projeto;
- quando utilizado, ele aparece como referência;
- não depende de `applyTo`.

Inferência controlada: ele provavelmente é tratado como **fonte global de instrução do repositório**, sujeita a inclusão por configuração habilitada no IDE e por orçamento de contexto.

O que **não** pode ser afirmado como fato: que ele entra em 100% das requisições sem exceção. A documentação fala em carregamento e uso, mas não abre o mecanismo interno de supressão em cenários extremos de orçamento.

### 2.3 Sobre `*.instructions.md`

**Inferência plausível**

Para `*.instructions.md`, o comportamento documentado é orientado por `applyTo`. Isso sugere um filtro inicial **determinístico por escopo**. Depois disso, é plausível que exista uma segunda seleção baseada em:

- arquivo ativo;
- seleção atual;
- tipo de tarefa;
- possível relevância semântica do prompt.

Ou seja, `applyTo` provavelmente reduz o espaço de candidatos, mas não precisa ser o único critério operacional em todas as situações.

### 2.4 Sobre influência semântica do texto do arquivo

**Inferência plausível**

Mesmo sem documentação explícita de que o corpo de um arquivo de instrução participa do índice semântico, isso é plausível por três motivos:

1. o sistema já indexa conteúdo do codebase e usa embeddings;
2. a documentação fala em detecção automática de instruction files relevantes;
3. arquivos Markdown do repositório são, em geral, bons candidatos a indexação textual.

Mas isso ainda **não é fato documentado**. Deve ser tratado como inferência e validado por experimento.

### 2.5 Sobre competição entre múltiplos arquivos

**Inferência plausível**

Se vários arquivos de instrução forem elegíveis ao mesmo tempo, pode ocorrer competição por:

- orçamento de tokens;
- prioridade do escopo;
- aderência lexical/semântica ao prompt;
- proximidade com arquivo ativo;
- recência do contexto de conversa.

A documentação confirma apenas que “arquivos relevantes” são detectados; ela não informa a política de desempate.

### 2.6 Fontes desta seção

- Microsoft Learn: `How Copilot Chat understands and uses context`
- Microsoft Learn: `Customize chat responses and set context`
- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `assistant-workflow-bmad-planning-and-controlled-inference`
  - `instruction-authoring-standard`

## 3. Hipótese de pipeline de decisão do Copilot

Abaixo está um **modelo mental plausível**, separado por nível de confiança.

### 3.1 Etapa 1 — Contexto implícito

**Documentado**

Entram automaticamente sinais de contexto de interação corrente, como:

- seleção ativa;
- arquivo ativo;
- histórico/thread.

### 3.2 Etapa 2 — Instruções de escopo amplo

**Documentado em parte, inferido em parte**

- **Documentado:** `copilot-instructions.md` pode ser carregado automaticamente e, quando usado, aparece nas referências.
- **Inferido:** ele atua como instrução de base do repositório, potencialmente com precedência prática sobre instruções mais específicas em temas gerais de estilo, processo e idioma.

### 3.3 Etapa 3 — Identificação da intenção da tarefa

**Inferência plausível**

O sistema provavelmente classifica implicitamente a intenção do prompt em algo como:

- explicação;
- geração;
- correção;
- documentação;
- teste;
- análise arquitetural.

E usa isso para decidir que tipo de contexto adicional recuperar.

Justificativa: a UI possui slash commands, ações contextualizadas e guided chat, todos sugerindo que há alguma camada de entendimento de intenção.

### 3.4 Etapa 4 — Seleção determinística inicial de candidatos

**Inferência plausível**

Antes da busca semântica mais cara, o sistema provavelmente monta um conjunto de candidatos de baixo custo com base em:

- arquivo ativo;
- símbolos referenciados explicitamente;
- `applyTo` de `*.instructions.md`;
- arquivos manualmente anexados;
- `@workspace`.

### 3.5 Etapa 5 — Recuperação semântica

**Documentado em alto nível; incerto em detalhe**

- **Documentado:** o Copilot pode rodar busca semântica sobre índice local/remoto e anexar arquivos semanticamente similares ao prompt.
- **Incerto:** se essa busca ocorre antes ou depois do filtro por instruções; se inclui instruções e Markdown auxiliares no mesmo espaço vetorial; se há reranking lexical posterior.

### 3.6 Etapa 6 — Composição final do contexto

**Inferência plausível**

O conjunto final provavelmente combina:

1. system prompt;
2. contexto implícito;
3. instruções globais;
4. instruções direcionadas candidatas;
5. arquivos recuperados semanticamente;
6. anexos e referências explícitas.

Depois disso, deve haver uma poda por:

- limite de tokens;
- redundância;
- confiança/relevância estimada.

### 3.7 Etapa 7 — Geração e mapeamento de resposta

**Documentado em parte**

- **Documentado:** o Copilot usa model based code mapping / speculative decoding para aplicar sugestões com precisão ao código.
- **Incerto para o tema desta pesquisa:** se a mesma camada de mapeamento influencia a seleção do contexto anterior.

### 3.8 Resumo visual do pipeline

```text
1. Contexto implícito                  [documentado]
2. Instruções amplas do repositório    [documentado + inferido]
3. Classificação da tarefa             [inferido]
4. Candidatos determinísticos          [inferido]
5. Recuperação semântica               [documentado em alto nível]
6. Reranking/poda por orçamento        [inferido]
7. Resposta final                      [documentado em parte]
```

### 3.9 Fontes desta seção

- Microsoft Learn: `How Copilot Chat understands and uses context`
- Microsoft Learn: `Customize chat responses and set context`
- Microsoft Learn: `Manage chat context with references`
- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `assistant-workflow-bmad-planning-and-controlled-inference`

## 4. Fragilidades observáveis

### 4.1 Problema estrutural: proximidade semântica não equivale a identidade de domínio

**Fato técnico geral sobre recuperação semântica**

Sistemas semânticos aproximam significado por padrões estatísticos de coocorrência e representação vetorial. Eles são bons para recuperar “coisas parecidas”, mas isso não garante separação robusta entre conceitos vizinhos que compartilham vocabulário, objetivo operacional ou topologia arquitetural.

**Inferência plausível para o Copilot**

Se o Copilot usa embeddings sobre o codebase para recuperar arquivos relevantes, então erros de vizinhança semântica são esperados quando dois domínios:

- compartilham termos superficiais;
- usam os mesmos verbos de ação;
- aparecem em contextos arquiteturais semelhantes;
- diferem mais por contrato/protocolo do que por vocabulário comum.

### 4.2 Cenário: FIX vs RabbitMQ

**Por que pode falhar**

- ambos podem aparecer próximos de termos como: mensagem, fila, broker, latência, roteamento, consumer, producer, integração, evento;
- um embedding treinado sobre texto geral pode aproximar “mensageria financeira FIX” e “mensageria assíncrona RabbitMQ” por compartilharem o macrotema “messaging/integration”.

**Risco prático**

Um arquivo sobre FIX pode ser recuperado para um prompt sobre publicação em RabbitMQ se o texto tiver vocabulário genérico demais, por exemplo “mensageria confiável”, “roteamento”, “integração assíncrona”.

### 4.3 Cenário: JWT vs OAuth client credentials

**Por que pode falhar**

- ambos orbitam autenticação/autorização/token;
- prompts curtos como “como autenticar integração entre serviços” podem ser semanticamente compatíveis com ambos;
- muitos textos tratam JWT como token e OAuth como fluxo, mas o embedding pode colapsar isso em “segurança baseada em token”.

**Risco prático**

O sistema pode trazer instrução sobre validação de JWT quando a tarefa real é aquisição de token por `client_credentials`, ou o inverso.

### 4.4 Cenário: cache em memória vs cache distribuído Redis

**Por que pode falhar**

- ambos respondem a termos como cache, TTL, invalidação, performance, key, hit, expire;
- a distinção crítica está em propriedades não triviais: escopo do processo, coerência entre instâncias, serialização, custo de rede, falha parcial.

**Risco prático**

Arquivo sobre `IMemoryCache` ser recuperado em prompt que deveria priorizar Redis, especialmente se o prompt disser apenas “melhorar performance com cache”.

### 4.5 Cenário: fila, tópico, stream, evento

**Por que pode falhar**

Esses termos são semanticamente próximos, mas arquiteturalmente não são intercambiáveis:

- fila enfatiza consumo concorrente e work queue;
- tópico enfatiza pub/sub;
- stream enfatiza sequência ordenada e retenção/offset;
- evento enfatiza fato de domínio, não mecanismo.

**Risco prático**

Um MCP baseado em sinônimos pode colapsar tudo em “mensageria”, perdendo a semântica operacional necessária para recuperar a instrução correta.

### 4.6 Cenário: API REST vs integração assíncrona

**Por que pode falhar**

- ambos tratam integração entre sistemas;
- ambos usam termos como contrato, payload, retry, idempotência, observabilidade, versionamento;
- a diferença está mais no padrão de interação e no acoplamento temporal do que no vocabulário básico.

**Risco prático**

Prompt “integração de clientes com sistema externo” pode recuperar guias REST quando a necessidade real é assíncrona, ou o inverso.

### 4.7 Fragilidade central para arquivos de instrução

**Inferência plausível**

Se a seleção de instruções tiver qualquer componente semântico além de escopo determinístico, então arquivos com vocabulário “aderente” porém normativamente errados podem competir melhor do que arquivos corretos com texto pobre.

Isso gera dois falsos positivos clássicos:

1. **arquivo errado com palavras certas**;
2. **arquivo certo com taxonomia ruim**.

### 4.8 Fontes desta seção

- Microsoft Learn: `How Copilot Chat understands and uses context`
- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `instruction-authoring-standard` (ênfase em recuperabilidade, tags e clareza normativa)

## 5. Impacto no desenho do MCP customizado

### 5.1 Avaliação do desenho atual

Cenário informado: MCP usa hoje

- dicionário fixo de sinônimos técnicos;
- busca por metadados;
- carregamento de conteúdo completo apenas sob demanda.

### 5.2 Onde essa estratégia é boa

**Vantagens reais**

1. **Baixo custo de tokens**  
   Não carrega tudo por padrão; isso é objetivamente melhor que depender de anexação ampla e oportunista.

2. **Governança explícita**  
   Metadados e taxonomia permitem explicar por que um artefato foi incluído.

3. **Maior previsibilidade**  
   Busca por metadados é auditável. Diferente da recuperação semântica pura, é mais fácil depurar falso positivo.

4. **Controle de escopo**  
   Dá para separar domínio, tipo de tarefa, criticidade, stack e tipo de artefato sem depender só da interpretação probabilística do modelo.

5. **Boa compatibilidade com workflow BMAD**  
   Ajuda a explicitar fato vs hipótese, o que está alinhado com o MCP `assistant-workflow-bmad-planning-and-controlled-inference`.

### 5.3 Limites dessa estratégia

**Limitações estruturais**

1. **Cobertura frágil de linguagem natural**  
   Dicionário fixo falha quando o usuário usa formulações fora do catálogo.

2. **Manutenção cara**  
   Cada novo termo, gíria interna, sigla ou variação precisa ser curado manualmente.

3. **Sinônimos são insuficientes para desambiguação**  
   Termos próximos não são equivalentes. Ex.: “evento” pode significar domínio, mensagem, webhook, auditoria.

4. **Busca por metadados depende da qualidade da autoria**  
   Se tags e descrições forem ruins, o sistema erra mesmo com boa governança.

5. **Sem reranking, a primeira recuperação pode ser enganosa**  
   Um match por metadado não garante aderência real à intenção da tarefa.

6. **Sem tipagem de tarefa, domínios colidem**  
   O mesmo termo em tarefa de explicação, implementação, troubleshooting ou arquitetura demanda contextos distintos.

### 5.4 Em que ele é melhor do que depender só do comportamento nativo do Copilot

**Conclusão crítica**

O MCP customizado é superior ao comportamento nativo do Copilot em pelo menos quatro aspectos:

1. **explicabilidade**;
2. **governança**;
3. **controle de custo**;
4. **desambiguação por política corporativa**.

O Copilot nativo é forte em conveniência e recall amplo. O MCP customizado pode ser melhor em precisão contextual de domínio, desde que o ranking seja bom.

### 5.5 O que deveria evoluir primeiro

#### Prioridade 1 — Taxonomia canônica

Sem taxonomia canônica, sinônimos e embeddings ficam sem chão semântico estável.

Deve organizar pelo menos:

- domínio técnico;
- subtópico;
- tipo de artefato;
- tipo de tarefa;
- stack/protocolo;
- criticidade/escopo.

#### Prioridade 2 — Desambiguação por tipo de tarefa

A mesma consulta muda de sentido conforme a intenção:

- explicar;
- decidir arquitetura;
- implementar;
- depurar;
- validar policy.

Isso precisa entrar cedo, porque reduz falso positivo mesmo antes de embeddings sofisticados.

#### Prioridade 3 — Reranking

Mesmo com recuperação inicial simples, reranking melhora precisão prática. É aqui que se filtra “parecido demais, mas errado”.

#### Prioridade 4 — Embeddings

Embeddings ajudam recall e linguagem livre, mas sem taxonomia e reranking tendem a aumentar confusão em domínios próximos.

#### Prioridade 5 — Pesos por domínio

Importante quando certos domínios têm alto risco de confusão, como segurança, mensageria, observabilidade, autenticação.

#### Prioridade 6 — Dicionário de governança

Ainda é útil, mas como apoio a normalização e aliases, não como mecanismo principal de compreensão.

### 5.6 Recomendação objetiva de evolução

**Ordem recomendada**

1. taxonomia canônica;
2. desambiguação por tipo de tarefa;
3. reranking;
4. embeddings;
5. pesos por domínio;
6. dicionário de governança como camada auxiliar.

### 5.7 Fontes desta seção

- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `instruction-authoring-standard`
  - `assistant-workflow-bmad-planning-and-controlled-inference`
- Microsoft Learn: `How Copilot Chat understands and uses context`

## 6. Arquitetura evolutiva recomendada para o MCP

### 6.1 MVP

**Objetivo**  
Aumentar precisão sem elevar muito custo e sem depender de embeddings desde o início.

**Componentes**

1. inventário canônico de artefatos;
2. frontmatter obrigatório com campos mínimos;
3. taxonomia básica;
4. classificador simples de tarefa por regras;
5. busca lexical + metadados;
6. carregamento lazy do conteúdo completo apenas após shortlist.

**Ganho esperado**

- explicabilidade alta;
- custo baixo;
- boa previsibilidade operacional;
- redução imediata de matches absurdos.

**Custo/complexidade**

- baixo a médio;
- depende mais de curadoria do que de ML.

**Risco mitigado**

- anexar contexto irrelevante;
- depender demais do comportamento opaco do Copilot.

### 6.2 Evolução intermediária

**Objetivo**  
Melhorar recall e reduzir fragilidade do dicionário fixo.

**Componentes**

1. embeddings dos títulos, tags, descrição e resumo do corpo;
2. busca híbrida: lexical + metadados + vetorial;
3. reranking leve com features explícitas;
4. pesos por domínio;
5. penalização por conflitos semânticos conhecidos.

**Features úteis para reranking**

- match de domínio canônico;
- match de tipo de tarefa;
- overlap em entidades/protocolos;
- compatibilidade com stack;
- score lexical exato em termos críticos;
- score vetorial.

**Ganho esperado**

- melhora em prompts livres;
- menor dependência de sinônimos manuais;
- melhor recuperação de artefatos bem escritos, mesmo sem vocabulário idêntico ao prompt.

**Custo/complexidade**

- médio;
- exige pipeline de indexação e avaliação offline.

**Risco mitigado**

- baixa cobertura linguística;
- excesso de manutenção manual do dicionário.

### 6.3 Evolução robusta

**Objetivo**  
Atingir alta precisão em domínios próximos e com tarefas ambíguas.

**Componentes**

1. classificador de intenção/tarefa mais robusto;
2. taxonomia hierárquica com relações `broader`, `narrower`, `related-but-not-equivalent`;
3. reranking treinado ou heurístico avançado;
4. expansão de consulta controlada por domínio;
5. detecção de conflito e pedido ativo de desambiguação quando a confiança for baixa;
6. observabilidade da recuperação:
   - artefatos candidatos;
   - motivo da seleção;
   - motivo da exclusão;
   - score por feature.

**Ganho esperado**

- maior precisão em casos ambíguos;
- menor risco de anexar artefato “quase certo”; 
- melhor capacidade de auditoria e tuning.

**Custo/complexidade**

- médio a alto.

**Risco mitigado**

- confusão entre domínios semanticamente vizinhos;
- difícil diagnóstico de falso positivo/negativo.

### 6.4 Princípios de desenho recomendados

1. **retrieval primeiro, geração depois**;
2. **nunca tratar sinônimo como equivalência semântica plena**;
3. **não carregar corpo completo antes da shortlist**;
4. **preferir pedir desambiguação quando a confiança for baixa**;
5. **registrar por que um artefato foi incluído**.

### 6.5 Fontes desta seção

- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `instruction-authoring-standard`
  - `assistant-workflow-bmad-planning-and-controlled-inference`
  - `artifact-encoding-line-endings-and-unicode`
- Microsoft Learn: `How Copilot Chat understands and uses context`

## 7. Experimentos propostos

A seguir, um conjunto de experimentos desenhado para validar comportamento observável do Copilot sem presumir mecanismos internos não documentados.

---

### Experimento 1 — Ambiguidade lexical curta

**Objetivo**  
Ver se prompts curtos e ambíguos disparam recuperação de artefatos semanticamente próximos, mas não necessariamente corretos.

**Setup**  
Criar dois arquivos de instrução/documentação:

- um sobre RabbitMQ;
- outro sobre FIX;

ambos contendo palavras como “mensagem”, “roteamento”, “integração”, “baixa latência”.

**Prompt de teste**  
`Como devo tratar mensageria neste serviço?`

**Hipótese**  
O Copilot tenderá a recuperar ambos ou priorizará o que tiver vocabulário mais genérico/aderente, não necessariamente o domínio correto.

**Resultado esperado**  
Referências inconsistentes ou necessidade de pergunta clarificadora.

**Sinal de falha**  
Sempre recuperar o arquivo errado sem pedir desambiguação.

**Insight extraível**  
Mede sensibilidade a termos macro e baixa capacidade de separação por protocolo.

---

### Experimento 2 — Mesmo termo em domínios distintos

**Objetivo**  
Testar colisão do termo `token` entre JWT e OAuth client credentials.

**Setup**  
Criar dois arquivos:

- `jwt.instructions.md`;
- `oauth-client-credentials.instructions.md`;

com bom vocabulário técnico e escopo parecido.

**Prompt de teste**  
`Como obtenho e valido o token da integração?`

**Hipótese**  
O termo `token` sozinho é insuficiente; o sistema pode misturar aquisição e validação.

**Resultado esperado**  
Recuperação concorrente ou resposta híbrida/confusa.

**Sinal de falha**  
Resposta assertiva escolhendo um dos fluxos sem evidência contextual.

**Insight extraível**  
Mostra necessidade de desambiguação por tipo de tarefa: obter vs validar.

---

### Experimento 3 — Cache genérico vs cache correto

**Objetivo**  
Medir se “cache” sozinho puxa `IMemoryCache` quando o contexto correto é Redis.

**Setup**  
Criar:

- um arquivo forte sobre cache em memória;
- um arquivo forte sobre Redis distribuído.

**Prompt de teste**  
`Quero melhorar performance com cache.`

**Hipótese**  
Sem sinais adicionais, a recuperação pode favorecer o artefato lexicalmente mais simples ou mais frequente.

**Resultado esperado**  
Baixa precisão semântica ou resposta pedindo mais contexto.

**Sinal de falha**  
Resposta prescritiva sobre cache local para cenário multi-instância.

**Insight extraível**  
Quantifica risco de matching por tema amplo em vez de propriedade arquitetural.

---

### Experimento 4 — Fila vs tópico vs stream vs evento

**Objetivo**  
Avaliar colapso semântico entre conceitos de integração assíncrona.

**Setup**  
Criar quatro artefatos curtos, cada um definindo um desses conceitos e suas invariantes.

**Prompt de teste**  
`Preciso publicar eventos para consumidores independentes com replay.`

**Hipótese**  
“evento” e “consumidores” podem puxar tópico; “replay” pode puxar stream. O sistema talvez oscile.

**Resultado esperado**  
Recuperação múltipla ou mistura de conceitos.

**Sinal de falha**  
Escolha inequívoca de fila simples ignorando `replay`.

**Insight extraível**  
Ajuda a desenhar taxonomia com relações `related-but-not-equivalent`.

---

### Experimento 5 — Instrução curta vs longa

**Objetivo**  
Ver se o comprimento do arquivo afeta probabilidade de recuperação ou uso.

**Setup**  
Criar dois arquivos equivalentes em conteúdo normativo:

- um curto e muito denso;
- outro longo, com muita narrativa e o mesmo núcleo semântico.

**Prompt de teste**  
`Quais padrões devo seguir para mensageria RabbitMQ?`

**Hipótese**  
O arquivo curto e denso pode performar melhor em recuperação e orçamento de contexto.

**Resultado esperado**  
Maior frequência de referência ao arquivo compacto.

**Sinal de falha**  
Arquivo longo sempre domina, mesmo com baixa densidade informacional.

**Insight extraível**  
Mede efeito de densidade semântica e custo de contexto.

---

### Experimento 6 — Descrição forte vs descrição genérica

**Objetivo**  
Testar se `description` parece influenciar seleção para além do hover documentado.

**Setup**  
Criar dois `*.instructions.md` com mesmo corpo e mesmo `applyTo`, mudando apenas:

- `description: Regras para integração RabbitMQ com DLQ, idempotência e retry`;
- `description: Instruções gerais do projeto`.

**Prompt de teste**  
`Como devo tratar dead letter e idempotência no publish?`

**Hipótese**  
Se o arquivo com descrição forte for favorecido, há indício experimental de que a descrição participa direta ou indiretamente do matching.

**Resultado esperado**  
Diferença observável de referência.

**Sinal de falha**  
Nenhuma diferença estatística após várias execuções.

**Insight extraível**  
Ajuda a decidir se `description` deve ser tratada como metadado operacional no MCP.

---

### Experimento 7 — Conflito entre múltiplos arquivos elegíveis

**Objetivo**  
Observar competição entre instruções simultaneamente aplicáveis.

**Setup**  
Criar:

- um `copilot-instructions.md` com regra geral “prefira integrações REST síncronas”;
- um `async-integration.instructions.md` aplicável ao módulo atual com regra “para eventos de domínio, prefira integração assíncrona”.

**Prompt de teste**  
`Como integrar atualização cadastral com o sistema parceiro?`

**Hipótese**  
O sistema pode:
- combinar ambas;
- preferir a mais específica;
- produzir resposta inconsistente.

**Resultado esperado**  
Conflito observável nas referências ou no texto da resposta.

**Sinal de falha**  
Resposta ignora completamente a instrução específica sem justificativa aparente.

**Insight extraível**  
Permite estimar precedência prática entre instrução global e instrução localizada.

---

### Experimento 8 — Arquivo correto com vocabulário ruim

**Objetivo**  
Medir penalidade por baixa qualidade lexical em artefato correto.

**Setup**  
Criar um arquivo tecnicamente correto sobre OAuth client credentials, mas com vocabulário pobre, pouco alinhado ao prompt do usuário.

**Prompt de teste**  
`Como obter access token por client credentials entre serviços?`

**Hipótese**  
O arquivo correto pode perder para um artefato menos correto, mas lexicalmente mais aderente.

**Resultado esperado**  
Baixa taxa de recuperação do artefato correto.

**Sinal de falha**  
Resposta fundamentada em documento semanticamente superficial, porém vocabularmente forte.

**Insight extraível**  
Mostra por que taxonomia e resumo canônico importam tanto quanto conteúdo técnico.

---

### Experimento 9 — Arquivo ruim com vocabulário muito aderente

**Objetivo**  
Testar o falso positivo inverso.

**Setup**  
Criar um arquivo conceitualmente inadequado para OAuth, mas recheado de termos como `token`, `client credentials`, `grant`, `access token`, `machine-to-machine`.

**Prompt de teste**  
`Quero autenticar integração M2M com client credentials.`

**Hipótese**  
Se o arquivo ruim for frequentemente recuperado, o mecanismo está sensível demais a aderência lexical/semântica superficial.

**Resultado esperado**  
Competição forte com o arquivo correto.

**Sinal de falha**  
Domínio errado vencendo repetidamente.

**Insight extraível**  
Reforça a necessidade de reranking com features estruturais.

---

### Experimento 10 — Mesmo `applyTo`, conteúdos semanticamente próximos

**Objetivo**  
Testar competição intraescopo entre `*.instructions.md` igualmente elegíveis.

**Setup**  
Criar dois arquivos com `applyTo: **/*.cs`:

- um sobre resiliência HTTP com retry;
- outro sobre mensageria com retry e DLQ.

**Prompt de teste**  
`Como devo tratar retries nesta integração?`

**Hipótese**  
O termo `retry` sozinho é insuficiente; os dois arquivos podem competir fortemente.

**Resultado esperado**  
Referências múltiplas ou necessidade de clarificação.

**Sinal de falha**  
Escolha aleatória e estável do arquivo errado.

**Insight extraível**  
Mede limite do `applyTo` sem desambiguação de tarefa/domínio.

---

### Experimento 11 — Influência do arquivo ativo

**Objetivo**  
Ver quanto o arquivo ativo desloca a recuperação frente a artefatos semânticos concorrentes.

**Setup**  
Abrir um arquivo claramente pertencente ao módulo de mensageria; manter também instruções sobre HTTP com vocabulário parcialmente semelhante.

**Prompt de teste**  
`Como implementar idempotência aqui?`

**Hipótese**  
O arquivo ativo deve funcionar como forte priorizador, reduzindo ambiguidade.

**Resultado esperado**  
Recuperação coerente com o módulo aberto.

**Sinal de falha**  
Trazer instruções de HTTP quando o contexto ativo é mensageria.

**Insight extraível**  
Mede peso prático do contexto implícito frente à busca semântica.

---

### Experimento 12 — Efeito de prompt longo com termos discriminativos

**Objetivo**  
Medir se prompts ricos reduzem colisões semânticas.

**Setup**  
Usar o mesmo conjunto ambíguo de arquivos dos experimentos anteriores.

**Prompt de teste**  
`No fluxo assíncrono com RabbitMQ, preciso garantir idempotência no consumer, DLQ para mensagens inválidas e retry com backoff. Quais instruções se aplicam?`

**Hipótese**  
Quanto mais discriminativo o prompt, maior a chance de recuperação correta.

**Resultado esperado**  
Referências mais estáveis e precisas.

**Sinal de falha**  
Persistência de competição com arquivos de domínio vizinho.

**Insight extraível**  
Ajuda a calibrar quanto o MCP deve investir em expansão de consulta versus pedir detalhamento ao usuário.

### 7.1 Como instrumentar os experimentos

Para cada experimento, registrar pelo menos:

- prompt exato;
- arquivo ativo;
- seleção ativa;
- referências usadas pelo Copilot;
- resposta gerada;
- se houve pergunta clarificadora;
- taxa de acerto do artefato correto;
- taxa de co-referência de artefatos errados.

### 7.2 Métricas úteis

- **Top-1 correto**;
- **Top-k contém artefato correto**;
- **precision@k**;
- **taxa de ambiguidade não reconhecida**;
- **taxa de pergunta clarificadora**;
- **custo médio de contexto carregado**.

### 7.3 Fontes desta seção

- Microsoft Learn: `How Copilot Chat understands and uses context`
- Microsoft Learn: `Customize chat responses and set context`
- Microsoft Learn: `Manage chat context with references`
- Repo: `.github/copilot-instructions.md`
- MCP `corporate-instructions`:
  - `assistant-workflow-bmad-planning-and-controlled-inference`
  - `instruction-authoring-standard`

## 8. Conclusão técnica

### O que posso assumir com segurança

- O Copilot no Visual Studio usa **contexto implícito**, **referências explícitas**, **índice do codebase** e **busca semântica** em algum nível documentado.
- `copilot-instructions.md` e arquivos de instrução relevantes podem ser usados automaticamente e aparecem nas **References** quando efetivamente utilizados.
- `*.instructions.md` possuem uso documentado com `applyTo` e `description` no frontmatter.
- O sistema não é apenas busca lexical simples; a documentação afirma explicitamente uso de **embeddings** e **semantic search**.
- No repositório atual, o único arquivo de instrução presente e verificável é `.github/copilot-instructions.md`.

### O que precisa de experimento

- Se o corpo textual de `*.instructions.md` influencia seleção para além do `applyTo`.
- Se `description` influencia recuperação ou apenas UI.
- Como múltiplos arquivos competem entre si.
- Quanto o arquivo ativo pesa versus busca semântica.
- Se o pipeline é lexical+vetorial com reranking, ou outra composição.
- Quais tipos de termos ambíguos geram pergunta clarificadora versus resposta assertiva incorreta.

### O que não devo assumir

- Não devo assumir que o Copilot usa um algoritmo específico de ranking não documentado.
- Não devo assumir que todo `copilot-instructions.md` entra em toda requisição sem exceção.
- Não devo assumir que `description` participa do embedding ou do ranking.
- Não devo assumir que similaridade semântica implica adequação normativa.
- Não devo assumir que `applyTo` basta para evitar colisão entre domínios próximos.

### Síntese final

Se o objetivo do seu MCP é **reduzir custo de tokens e aumentar precisão semântica**, a aposta correta não é competir com o Copilot tentando adivinhar seu mecanismo interno. A aposta correta é complementar suas lacunas observáveis:

1. **explicabilidade**;
2. **taxonomia canônica**;
3. **desambiguação por tarefa**;
4. **reranking governado**;
5. **carregamento lazy do conteúdo completo**.

Em termos práticos: o comportamento nativo do Copilot parece suficiente para recall amplo, mas insuficiente como único mecanismo de governança e desambiguação em domínios técnicos próximos. Para esse espaço, um MCP customizado bem desenhado tende a ser mais confiável que um dicionário fixo de sinônimos e mais auditável que depender apenas da recuperação automática do Copilot.

---

## Referências consolidadas

### Documentação oficial

- Microsoft Learn — How Copilot Chat understands and uses context  
  <https://learn.microsoft.com/visualstudio/ide/copilot-context-overview?view=visualstudio>
- Microsoft Learn — Customize chat responses and set context  
  <https://learn.microsoft.com/visualstudio/ide/copilot-chat-context?view=visualstudio#use-custom-instructions>
- Microsoft Learn — Manage chat context with references  
  <https://learn.microsoft.com/visualstudio/ide/copilot-chat-context-references?view=visualstudio>

### Evidência do repositório

- `.github/copilot-instructions.md`

### Policies MCP consultadas

- `corporate-instructions:instruction-authoring-standard`
- `corporate-instructions:assistant-workflow-bmad-planning-and-controlled-inference`
- `corporate-instructions:artifact-encoding-line-endings-and-unicode`
