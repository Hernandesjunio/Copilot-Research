# Plano técnico — Reorientação do MCP para Instruction Retrieval v1

> **Origem**: este documento foi consolidado com suporte de outra LLM para reduzir viés de implementação no repositório.
> **Objetivo**: registrar a decisão e o desenho para fortalecer as 3 tools básicas do MCP (retrieval), adiando o compositor automático de contexto.

## 1. Objetivo deste documento

Este documento consolida uma análise crítica sobre a tentativa de evoluir um MCP de instructions para um compositor automático de contexto e propõe uma reorientação arquitetural mais simples, incremental e testável.

O objetivo é permitir avaliar o que já existe e propor melhorias objetivas nas três tools básicas do MCP:

1. `list_instructions_index`
2. `search_instructions`
3. `get_instruction` / `get_instructions_batch`

A proposta principal é pausar temporariamente o investimento no compositor automático de contexto e evoluir o MCP para uma primeira versão robusta de recuperação de instructions normativas aplicáveis.

---

## 2. Contexto da pesquisa

O MCP está sendo desenvolvido para funcionar como provedor de contexto para agentes de IA em ambientes de desenvolvimento de software.

O cenário-alvo envolve mais de 100 microservices e a necessidade de compartilhar contexto global, padrões, regras e instructions normativas entre múltiplas aplicações.

O objetivo maior é substituir ou complementar estratégias como `.github/instructions`, instruções locais por repositório e prompts fixos, centralizando a recuperação de contexto em uma camada MCP.

---

## 3. Diagnóstico da falha na evolução para compositor de contexto

A tentativa de transformar o MCP em compositor de contexto fez com que o sistema passasse a assumir responsabilidades demais ao mesmo tempo.

Antes, o MCP era responsável por:

- listar instructions;
- buscar instructions candidatas;
- carregar instructions por ID.

Depois, o MCP passou a tentar:

- entender a intenção da query;
- recuperar documentos candidatos;
- decidir documentos primários;
- decidir documentos de suporte;
- montar o bundle final de contexto;
- evitar documentos meta/governance;
- promover policies;
- resolver conflitos;
- controlar ruído;
- selecionar o que o agente deveria usar.

Essa mudança aumentou muito a superfície de erro.

O problema não está no conceito de compositor em si. O problema está em tentar construir o compositor antes de estabilizar a recuperabilidade básica das instructions normativas.

---

## 4. Hipótese crítica

> A pesquisa tentou avançar cedo demais de um MCP de recuperação de instructions para um MCP compositor de contexto. O próximo passo mais seguro é fortalecer as três tools básicas e validar se o agente consegue recuperar e aplicar instructions normativas corretamente.

Em vez de perguntar:

> O MCP consegue compor automaticamente o melhor contexto para o agente?

Pergunta-se:

> Um MCP com tools simples, filtráveis e orientadas à aplicabilidade melhora a capacidade do agente de recuperar instructions normativas corretas?

---

## 5. Nova direção proposta

Evoluir para uma primeira versão chamada:

> **MCP Instruction Retrieval v1**

Essa versão **não** deve ser tratada como compositor de contexto. Ela deve ser tratada como um provedor inteligente de instructions normativas aplicáveis.

A responsabilidade passa a ser:

> Dado um arquivo, uma tarefa, uma query e alguns filtros, retornar as instructions mais aplicáveis para que o agente decida o que carregar.

---

## 6. Mudança de filosofia

### 6.1 Filosofia anterior

- O MCP recupera candidatos.
- O MCP decide o bundle.
- O MCP define primary/supporting.
- O MCP tenta montar o contexto ideal.
- O agente consome o pacote pronto.

### 6.2 Filosofia proposta

- O agente possui a tarefa.
- O agente conhece o arquivo atual.
- O agente conhece o diff, erro ou requisito atual.
- O MCP retorna instructions candidatas e explica aplicabilidade.
- O agente decide quais instructions carregar.
- O agente aplica as regras ao trabalho.

---

## 7. Por que pausar o compositor agora

O compositor de contexto exige resolver problemas complexos simultaneamente:

- classificação de intenção;
- seleção de documentos primários;
- seleção de documentos de suporte;
- resolução de conflito;
- controle de orçamento de tokens;
- priorização por escopo;
- distinção entre documento técnico e meta/governance;
- deduplicação semântica;
- ordenação final;
- explicabilidade;
- avaliação do bundle final.

Sem uma base forte de recuperação, o compositor tende a compensar falhas com heurísticas manuais, gerando risco de:

- tuning por teste;
- regras orientadas ao corpus;
- sinônimos artificiais;
- promotion/demotion hardcoded;
- dependência de IDs específicos;
- baixa generalização para novos domínios.

---

## 8. Instructions como unidades normativas

Um ponto central da nova abordagem é tratar os arquivos de instructions como unidades normativas, e não como documentos comuns de conhecimento.

Uma instruction normativa pode conter regras aplicáveis somente a determinado:

- domínio;
- tecnologia;
- camada;
- tipo de arquivo;
- modo de trabalho;
- escopo organizacional.

Por isso, a recuperação não deve depender apenas de termos textuais: ela deve considerar **aplicabilidade**.

---

## 9. Conceito-chave: aplicabilidade

A pergunta central da recuperação não deve ser apenas:

> Este documento é semanticamente parecido com a query?

Mas sim:

> Esta instruction deve ser aplicada neste arquivo, nesta camada, nesta tecnologia e nesta tarefa?

Para instructions normativas, metadados estruturados podem ser mais importantes do que busca semântica vetorial no primeiro momento.

---

## 10. Metadados mínimos recomendados

Cada instruction deve possuir frontmatter estruturado. Exemplo:

```yaml
---
id: backend-httpclient-resilience
title: Padrão de resiliência para chamadas HTTP
summary: Define regras para timeout, retry, circuit breaker e observabilidade em chamadas HTTP externas.
domains:
  - backend
technologies:
  - dotnet
  - aspnetcore
layers:
  - infrastructure
  - integration
  - external-client
file_patterns:
  - "**/*Client.cs"
  - "**/*HttpClient*.cs"
  - "**/Clients/**/*.cs"
  - "**/Integrations/**/*.cs"
applies_to:
  - implementation
  - refactoring
  - code-review
kind: guideline
scope: global
priority: high
tags:
  - httpclient
  - retry
  - timeout
  - resilience
  - circuit-breaker
  - polly
---
```

---

## 11. Taxonomia recomendada

### 11.1 Domains

```yaml
domains:
  - backend
  - frontend
  - mobile
  - database
  - messaging
  - observability
  - security
  - devops
  - architecture
  - testing
  - ai-engineering
  - documentation
```

### 11.2 Technologies

```yaml
technologies:
  - dotnet
  - aspnetcore
  - csharp
  - angular
  - typescript
  - sqlserver
  - redis
  - azure-functions
  - aks
  - service-bus
  - github-actions
  - docker
  - kubernetes
```

### 11.3 Layers

```yaml
layers:
  - api
  - controller
  - application
  - domain
  - infrastructure
  - repository
  - integration
  - external-client
  - database
  - migration
  - frontend-component
  - pipeline
  - test
```

### 11.4 Applies to

```yaml
applies_to:
  - implementation
  - refactoring
  - code-review
  - troubleshooting
  - test-generation
  - documentation
  - architecture-decision
  - migration
```

### 11.5 Kinds

```yaml
kinds:
  - policy
  - standard
  - guideline
  - reference
  - example
  - decision
  - playbook
  - troubleshooting
  - glossary
  - checklist
  - meta-governance
```

### 11.6 Scopes

```yaml
scopes:
  - global
  - platform
  - tribe
  - product
  - repository
  - service
```

---

## 12. Evolução das três tools básicas

### 12.1 Tool 1 — list_instructions_index

**Responsabilidade recomendada**: listar instructions com filtros estruturados, sem carregar corpo completo.

Entrada sugerida:

```json
{
  "domain": "backend",
  "technology": "dotnet",
  "layer": "api",
  "kind": "standard",
  "applies_to": "implementation",
  "file_path": "src/MyApi/Controllers/OrdersController.cs",
  "max_results": 20
}
```

Regras:

- Não retornar corpo completo.
- Não montar bundle.
- Retornar metadados suficientes para o agente decidir o próximo passo.

### 12.2 Tool 2 — search_instructions

**Responsabilidade recomendada**: buscar por query textual combinada com metadados e aplicabilidade.

Entrada sugerida:

```json
{
  "query": "como implementar retry em chamada HTTP externa",
  "domain": "backend",
  "technology": "dotnet",
  "applies_to": "implementation",
  "file_path": "src/Payments/ExternalClients/StripeClient.cs",
  "max_results": 10
}
```

Componentes de score recomendados:

```
instruction_score =
    textual_relevance
  + metadata_match
  + file_pattern_match
  + mode_match
  + priority_boost
  - deprecated_penalty
  - wrong_layer_penalty
  - wrong_domain_penalty
```

Melhorias possíveis:

1. Começar com scoring simples e explicável.
2. Adicionar BM25 por campos como melhoria da busca textual.
3. Não adicionar FAISS no primeiro momento.

### 12.3 Tool 3 — get_instruction / get_instructions_batch

**Responsabilidade recomendada**: carregar por ID com controle de tamanho, metadados e rastreabilidade.

Entrada sugerida:

```json
{
  "ids": ["backend-httpclient-resilience", "observability-correlation"],
  "max_chars_per_instruction": 6000,
  "include_metadata": true
}
```

Regras:

- Permitir batch.
- Retornar metadados junto com conteúdo.
- Indicar truncamento.
- Retornar hash/versão.
- Não decidir se o agente deve aplicar.

---

## 13. Exemplo de fluxo ideal (com as 3 tools)

1. Agente chama `search_instructions` com `query + file_path + filtros`.
2. MCP retorna candidatas com explicação de aplicabilidade.
3. Agente chama `get_instructions_batch` para carregar as principais.
4. Agente aplica as regras ao código.

---

## 14. Riscos da nova abordagem

Ao deixar o agente decidir o que carregar, o MCP transfere parte da inteligência para o agente:

- o agente pode não chamar a tool;
- o agente pode ignorar o melhor resultado;
- o agente pode carregar documentos demais;
- o agente pode não perceber conflitos.

Esses riscos são aceitáveis nesta fase porque fazem parte da pergunta de pesquisa.

---

## 15. O papel do BM25 nesta fase

Ordem recomendada:

1. Melhorar metadados.
2. Melhorar filtros da listagem.
3. Melhorar search com aplicabilidade.
4. Adicionar BM25 por campos.
5. Medir ganho real com o agente.
6. Só depois avaliar FAISS.
7. Só depois retomar compositor.

---

## 16. Métricas recomendadas

- Instruction Hit@1 / Hit@3 / Hit@5
- Wrong Domain Rate
- Wrong Layer Rate
- Wrong File Applicability Rate
- Agent Load Rate
- Agent Correct Use Rate
- Tool Call Rate
- Token Waste Rate

---

## 17. Benchmark recomendado (cenários)

Criar cenários por domínio/camada/arquivo (ex.: controller, migration SQL, componente frontend, pipeline CI, testes).

---

## 18. Decisão recomendada

> Pausar o compositor de contexto e investir em uma versão robusta das três tools básicas, orientada por metadados, filtros e aplicabilidade de instructions normativas.

---

## 19. Sequência final recomendada

1. Congelar temporariamente o compositor.
2. Voltar o foco para as três tools básicas.
3. Definir metadados normativos obrigatórios.
4. Melhorar listagem com filtros.
5. Melhorar busca com aplicabilidade.
6. Melhorar carregamento com controle de conteúdo.
7. Criar benchmark por domínio/camada/arquivo.
8. Medir comportamento com agente real.
9. Reavaliar compositor somente após evidência.

