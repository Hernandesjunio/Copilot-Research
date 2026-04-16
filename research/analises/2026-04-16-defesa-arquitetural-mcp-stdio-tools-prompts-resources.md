# Defesa técnica: MCP local em STDIO para composição de contexto reutilizável e redução da dependência de `.github/instructions`

**Data:** 16 de abril de 2026.

## 1. Resumo executivo

Este documento descreve a motivação, o escopo, as escolhas técnicas e os limites de uma solução baseada em **MCP local em STDIO**, criada para reduzir a dependência de `.github/instructions` como principal mecanismo de alimentação de contexto do Copilot em cenários de planejamento e arquitetura.

A proposta não busca substituir iniciativas baseadas em prompts, agentes ou outros artefatos de IA. O foco atual é mais específico: melhorar a forma como o contexto é descoberto, buscado e entregue à LLM em tarefas que hoje dependem de instruções replicadas ou pouco seletivas.

---

## 2. Problema real sendo resolvido

O problema central não é ausência de inteligência de prompt. Também não é ausência de agentes.

O problema real é:

**O uso de `.github/instructions` como mecanismo principal de contexto geral apresenta limitações de duplicação, drift, baixa seletividade e pouca previsibilidade na composição do contexto consumido pela LLM.**

Na prática, isso se manifesta em cenários como:

- repetição de instruções semelhantes em diversos repositórios
- divergência gradual entre cópias que deveriam representar a mesma diretriz
- dificuldade de atualização coordenada
- envio de contexto maior do que o necessário
- falta de controle fino sobre o que será recuperado para uma tarefa específica

---

## 3. Objetivo técnico da solução

A solução foi desenhada para atender ao seguinte objetivo:

**Fornecer ao Copilot um mecanismo local de recuperação de contexto geral reutilizável, com baixa latência e composição controlada, reduzindo a dependência de `.github/instructions` para conteúdos que não precisam estar replicados por repositório.**

---

## 4. Premissas adotadas

A proposta foi construída com as seguintes premissas:

- a experiência interativa local do desenvolvedor é crítica
- o problema atual precisa ser resolvido com baixo atrito
- não há necessidade imediata de centralização rígida em runtime
- o corpus geral não muda a todo momento
- instruções muito específicas de domínio podem continuar locais
- o valor inicial está em resolver o problema atual melhor que o baseline existente

---

## 5. Escopo funcional atual

A implementação atual foi desenhada para atuar sobre um corpus de instruções em Markdown e expor três capacidades principais:

### 5.1 `list_instructions_index`

**Função:** listar metadados dos arquivos disponíveis.

**Retorno esperado:** id, path, tags, hash.

**Valor técnico:**

- descoberta de catálogo
- inspeção rápida do corpus
- suporte a indexação e auditoria leve de conteúdo

### 5.2 `search_instructions`

**Função:**

- buscar instruções por palavras-chave
- aplicar filtro opcional por tags
- limitar volume de resultados

**Parâmetros:** texto de busca; tags opcionais; `max_results` entre 1 e 10.

**Valor técnico:**

- recuperação orientada à intenção
- filtragem inicial de contexto
- redução de leitura desnecessária

### 5.3 `get_instruction`

**Função:**

- obter conteúdo completo por id ou path relativo
- aplicar truncamento por `max_chars`

**Restrições:** sem `..`; sem caminho absoluto.

**Valor técnico:**

- leitura sob demanda
- controle de volume
- segurança básica de acesso ao conteúdo

---

## 6. Justificativa arquitetural do uso de tools

A interface principal foi construída em torno de **tools** porque o problema atual exige operações dinâmicas de recuperação, e não apenas exposição de conteúdo estático.

### 6.1 O que a solução precisa fazer

A solução precisa permitir:

- descobrir o que existe no corpus
- buscar conteúdo por necessidade atual
- filtrar por metadados
- carregar apenas o necessário
- limitar volume retornado

Essas operações caracterizam um fluxo de **recuperação dinâmica**.

### 6.2 Por que isso favorece tools

Tools são adequadas quando o valor está em executar uma operação orientada ao contexto atual da tarefa.

No caso desta solução, o valor não está apenas em armazenar documentos. O valor está em:

- selecionar o documento certo
- evitar leitura excessiva
- controlar o retorno
- usar critérios objetivos de busca

Portanto, tools foram adotadas como o mecanismo natural para o estágio atual.

---

## 7. Por que a solução não foi centrada em prompts

A opção por não centrar a solução em prompts decorre do objetivo técnico atual, não de rejeição ao uso de prompts em si.

### 7.1 O que prompts resolvem bem

Prompts são adequados para:

- orientar comportamento da LLM
- definir formato de saída
- estabelecer papel de atuação
- padronizar execução de determinadas tarefas

### 7.2 O que prompts não resolvem diretamente neste caso

O problema atual não é, primordialmente, falta de instrução de comportamento. O problema é:

- seleção de contexto
- redução de duplicação
- economia de tokens
- composição mais controlada

Mesmo um bom prompt ainda dependeria de uma base de contexto bem selecionada para produzir bons resultados de forma consistente.

### 7.3 Conclusão sobre prompts

Prompts podem coexistir com a solução e ser úteis em outras frentes, inclusive como camada complementar. Porém, para este problema específico, eles não são o artefato central.

---

## 8. Por que a solução não foi centrada em resources

Resources também não foram escolhidos como elemento principal da solução atual por uma razão simples: o uso inicial exige mais do que simples leitura de conteúdo estável.

### 8.1 Onde resources seriam adequados

Resources são úteis quando o valor principal está em disponibilizar artefatos relativamente estáveis e reutilizáveis como unidades consultáveis.

### 8.2 Limitação para o objetivo atual

No estágio atual, a solução precisa:

- listar
- buscar
- filtrar
- carregar sob demanda
- truncar

Isso ultrapassa o simples consumo de conteúdo canônico.

### 8.3 Conclusão sobre resources

Resources continuam sendo uma possibilidade válida para evolução futura, especialmente para conteúdos mais estáveis e canônicos. No entanto, eles não cobrem sozinhos a necessidade principal deste estágio.

---

## 9. Justificativa do uso de STDIO

A escolha por **STDIO** foi feita considerando o caminho crítico da interação.

### 9.1 Critérios adotados

Foram priorizados:

- baixa latência
- simplicidade no hot path
- experiência local fluida
- menor atrito operacional para uso inicial

### 9.2 Benefício observado

Na prática, o uso local via STDIO foi um dos diferenciais percebidos na interação, com resposta rápida durante a execução das tools.

### 9.3 Por que não colocar HTTP no centro da solução agora

HTTP é uma opção válida para outros cenários, mas não foi priorizado porque, neste estágio, o projeto não busca maximizar centralização online. Busca maximizar eficiência local comparada ao uso atual de `.github/instructions`.

A existência futura de um mecanismo híbrido não invalida o acerto do STDIO como base do fluxo principal.

---

## 10. Comparação com o baseline atual

A avaliação precisa ser feita comparando a solução com o que existe hoje no fluxo real de trabalho.

### 10.1 Baseline

O baseline atual é o uso de `.github/instructions` replicados nos repositórios.

### 10.2 Limitações do baseline

- drift entre cópias
- manutenção distribuída
- contexto pouco seletivo
- pouca capacidade de composição sob demanda
- dificuldade de evolução coordenada

### 10.3 Vantagem prática da proposta

A proposta melhora esse cenário ao:

- centralizar o corpus geral reutilizável
- evitar replicação desnecessária
- permitir recuperação por busca
- limitar volume retornado
- manter experiência local rápida

---

## 11. O que a solução deliberadamente não resolve agora

É importante deixar claro o limite da proposta.

A solução atual não pretende resolver, neste estágio:

- auditoria central por request
- revogação imediata global
- governança rígida de runtime
- substituição total de instruções locais
- cobertura completa de todos os cenários de IA da organização

Esses pontos podem ser tratados em evoluções futuras, se se tornarem relevantes para o uso real.

---

## 12. Estratégia de convivência com `.github/instructions`

A proposta não exige ruptura total com o modelo atual.

Uma estratégia técnica razoável é:

- usar MCP para contexto geral, guardrails e instruções reutilizáveis
- manter `.github/instructions` para regras muito específicas de um repositório ou domínio particular

Isso reduz duplicação sem forçar centralização indevida de conhecimento altamente local.

---

## 13. Possíveis questionamentos e respostas técnicas

### 13.1 “Por que não resolver isso com prompt?”

Porque o problema principal é de recuperação e composição de contexto, não apenas de instrução de comportamento. Prompt pode orientar a resposta, mas não substitui um mecanismo de busca, seleção e leitura sob demanda.

### 13.2 “Por que não expor tudo como resource?”

Porque o estágio atual exige operações dinâmicas de descoberta, busca e controle de volume. Resource pode expor conteúdo, mas não substitui sozinho a interface operacional necessária.

### 13.3 “Por que não começar diretamente com HTTP?”

Porque o ganho principal do projeto está no fluxo interativo local e na comparação com o baseline atual. Inserir transporte remoto no caminho principal agora aumentaria complexidade e poderia prejudicar a experiência que se deseja preservar.

### 13.4 “Não seria mais simples continuar apenas com `.github/instructions`?”

Seria mais simples no curto prazo apenas se ignorarmos custos já conhecidos de replicação, drift e manutenção distribuída. O objetivo do projeto é justamente reduzir esses custos sem sacrificar a usabilidade.

### 13.5 “Essa solução pretende substituir agentes?”

Não. O foco da solução está na camada de contexto. Agentes, prompts e outras abordagens continuam úteis em camadas complementares.

---

## 14. Evidência já observada

Os experimentos realizados indicaram, em cenários de planejamento:

- melhor seleção do contexto
- menor desperdício de tokens
- qualidade marginalmente superior em alguns resultados
- interação rápida por uso local

Essas evidências ainda podem e devem ser ampliadas, mas já são suficientes para justificar continuidade da investigação.

---

## 15. Caminho de evolução possível

Sem alterar a natureza da solução atual, a evolução pode seguir etapas como:

| Etapa | Foco |
| --- | --- |
| 1 | Consolidação do uso local com corpus geral reutilizável |
| 2 | Melhoria de indexação, busca e critérios de priorização |
| 3 | Definição clara do que permanece local no repositório e do que migra para o corpus central |
| 4 | Avaliação de artefatos complementares, como resources e prompts, onde fizer sentido técnico |
| 5 | Mecanismos de atualização controlada do corpus com rollback |

---

## 16. Conclusão

A solução proposta é adequada para o problema atual porque atua diretamente sobre a principal limitação observada no uso de `.github/instructions`: a falta de um mecanismo mais controlado, reutilizável e seletivo para fornecer contexto geral ao Copilot.

A decisão por **tools** e **STDIO**, neste estágio, não representa rejeição a prompts, resources ou HTTP. Representa apenas adequação entre:

- o problema atual
- o tipo de operação necessária
- a experiência que se deseja manter
- o baseline real com o qual a solução precisa competir

Em termos técnicos, a proposta pode ser resumida assim:

**Para o problema atual de contexto geral reutilizável, a solução baseada em MCP local com tools em STDIO é uma abordagem coerente, incremental e superior ao modelo puramente replicado em `.github/instructions`, sem impedir evoluções futuras para outros tipos de artefato ou mecanismos de distribuição.**

---

## Documento relacionado

Para a versão curta de apresentação (pitch ~5 minutos), ver `2026-04-16-pitch-tecnico-mcp-stdio-contexto-github-instructions.md`.
