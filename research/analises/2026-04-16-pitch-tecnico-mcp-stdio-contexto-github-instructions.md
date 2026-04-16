# Pitch técnico (5 minutos): MCP local em STDIO para composição determinística de contexto

**Data:** 16 de abril de 2026.

## Objetivo

Apresentar uma solução técnica para reduzir limitações operacionais do uso de `.github/instructions` como principal mecanismo de orientação do Copilot em tarefas de planejamento e arquitetura, mantendo experiência fluida de interação e melhor controle sobre a composição de contexto.

---

## Problema atual

Hoje, parte relevante do contexto utilizado pelo Copilot depende de arquivos `.github/instructions` distribuídos nos repositórios. Esse modelo funciona, mas apresenta limitações conhecidas:

- duplicação de conteúdo entre repositórios
- risco de drift entre instruções semelhantes
- dificuldade de evolução coordenada
- envio de contexto pouco seletivo
- baixa previsibilidade sobre quais trechos serão mais relevantes para cada tarefa

O problema que está sendo tratado neste momento não é ausência de prompts, nem ausência de agentes. O problema atual é:

**Como fornecer ao Copilot um contexto mais controlado, mais econômico e mais aderente à tarefa, sem perder fluidez na interação local do desenvolvedor.**

---

## Proposta

Utilizar um **MCP local via STDIO** para compor contexto de forma determinística, com baixa latência, a partir de uma base centralizada de conhecimento reutilizável.

A proposta inicial não substitui todo o modelo atual. Ela ataca especificamente a camada de contexto geral e guardrails reutilizáveis, preservando instruções específicas de domínio diretamente nos repositórios quando isso fizer mais sentido.

---

## Escopo atual da solução

A solução atual foi desenhada para atuar principalmente em cenários de:

- planejamento técnico
- definição arquitetural
- uso de guardrails gerais
- recuperação de instruções reutilizáveis
- redução de dependência de arquivos replicados

---

## Tools implementadas

As tools atuais atendem ao fluxo de descoberta, busca e leitura do corpus:

### `list_instructions_index`

Retorna metadados dos arquivos `.md`, incluindo id, path, tags e hash.

### `search_instructions`

Realiza busca por palavras-chave, com tags opcionais e controle de `max_results`.

### `get_instruction`

Retorna o conteúdo completo por id ou path, com truncamento por `max_chars`.

---

## Valor técnico observado

Nos experimentos realizados até o momento, a solução apresentou ganhos práticos em relação ao uso passivo de `.github/instructions` para tarefas equivalentes de planejamento:

- melhor seleção de contexto
- menor volume de contexto irrelevante
- economia de tokens na composição
- experiência de interação rápida por uso local via STDIO
- resultado marginalmente melhor em determinados cenários avaliados

A proposta, portanto, não está sendo conduzida como hipótese abstrata. Ela já produziu evidências iniciais de valor.

---

## Por que a solução está focada em tools

Neste estágio, a necessidade principal é recuperar contexto de forma dinâmica, com controle sobre:

- busca por intenção
- seleção orientada por tags
- leitura sob demanda
- truncamento
- composição controlada do conteúdo retornado

Esse tipo de necessidade se encaixa naturalmente em **tools**, porque o valor principal está em decidir o que deve ser carregado para a tarefa atual, e não apenas em expor conteúdo bruto.

---

## Por que o foco inicial não é prompt

Prompts são úteis para orientar comportamento da LLM. No entanto, o problema principal tratado aqui é anterior:

- selecionar melhor o contexto
- reduzir duplicação de instruções
- evitar depender apenas de texto fixo replicado
- compor informação útil para a tarefa corrente

Ou seja, o foco atual está na **engenharia de contexto**, não na formatação do comportamento da resposta.

Isso não invalida o uso de prompts em iniciativas paralelas ou futuras. Apenas indica que, para este problema específico, prompt não é o artefato central.

---

## Por que o foco inicial não é resource

Resources são adequados quando o valor principal está em expor conteúdo relativamente estável de maneira consultável. Isso pode ser útil em fases futuras, principalmente para artefatos canônicos e pouco mutáveis.

No estágio atual, porém, a necessidade principal ainda é:

- descobrir
- buscar
- selecionar
- carregar parcialmente
- controlar volume de retorno

Essas necessidades favorecem **tools** como interface principal de acesso.

---

## Por que STDIO foi escolhido

O objetivo da solução é preservar a qualidade da experiência local com o agente. O uso de **STDIO** foi escolhido porque:

- reduz overhead de comunicação
- mantém o fluxo interativo rápido
- simplifica o caminho crítico de execução
- permite uso local com baixa fricção

Para o objetivo atual, o ganho de fluidez local é mais relevante do que mover toda a solução para um modelo remoto.

---

## O que a solução não pretende fazer neste momento

A proposta não pretende, neste estágio:

- substituir todo e qualquer uso de `.github/instructions`
- invalidar iniciativas de prompts ou agentes
- transformar o MCP em plataforma corporativa completa
- resolver todos os cenários de governança em tempo real
- atender todos os tipos de contexto possíveis

O foco é mais restrito e objetivo: **resolver melhor o problema atual de contexto geral reutilizável no Copilot, com experiência local equivalente ou melhor.**

---

## Próximo passo sugerido

Seguir com evolução controlada, comparando o modelo atual com o proposto em cenários reais de uso, medindo:

- aderência ao objetivo da tarefa
- economia de tokens
- consistência do contexto retornado
- tempo de interação
- esforço de manutenção

---

## Documento relacionado

Para a defesa arquitetural detalhada (premissas, comparação com baseline, Q&A), ver `2026-04-16-defesa-arquitetural-mcp-stdio-tools-prompts-resources.md`.
