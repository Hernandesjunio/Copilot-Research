# Plano Final Incremental - MCP `get_context_triggers`

## Objetivo

Definir um plano final, incremental e testavel para evoluir o MCP `get_context_triggers` por etapas pequenas, segregadas e verificaveis, permitindo desenvolvimento empirico com validacao continua por comportamento observado.

Este plano assume:

- ausencia de acesso ao codigo-fonte do runtime externo avaliado;
- necessidade de iteracao por tentativa e erro;
- foco em previsibilidade observavel;
- prioridade para reduzir ambiguidade entre agentes consumidores da tool.

---

## Principios de execucao

1. Implementar primeiro o que aumenta **interoperabilidade e auditabilidade**.
2. Separar incrementos por **responsabilidade funcional**.
3. Nao introduzir campos sofisticados antes de estabilizar os campos centrais.
4. Cada incremento precisa ter:
   - objetivo claro;
   - mudanca contratual delimitada;
   - testes dedicados;
   - criterio explicito de pronto.
5. Nenhum incremento deve depender de comportamento "intuido" da IA; sempre preferir sinal observavel.

---

## Macro-fases

O plano esta dividido em 6 etapas:

1. Baseline contratual
2. Evidence gate em duas fases
3. Sequenciamento auditavel e fallbacks
4. Invariantes e suite de testes black-box
5. Governanca declarativa progressiva
6. Sinais avancados de estabilidade e granularidade

Cada fase pode ser entregue e validada isoladamente.

---

## Etapa 0 - Preparacao do baseline experimental

## Objetivo

Congelar um baseline minimo para comparacao entre rodadas.

## Escopo

- Fixar cenarios canonicos de teste.
- Fixar pacote minimo de entrada.
- Fixar formato de captura de saida observada.

## Artefatos

- conjunto de prompts de teste A/B/C/D;
- snapshots de `input.json` e `output.json`;
- template de registro de divergencias por rodada.

## Implementacao

1. Definir cenarios minimos:
   - bug local;
   - feature vaga;
   - pedido apenas de plano;
   - decisao transversal com policy plausivel.
2. Padronizar variacoes lexicais de cada cenario.
3. Definir quais campos serao sempre coletados na saida:
   - `scenario`;
   - `strategy`;
   - `tool_sequence`;
   - `mcp_usage` ou equivalente;
   - `evidence_gate`;
   - `stop_rules`;
   - `fallbacks`.

## Testes

- Repetir cada cenario pelo menos 3 vezes.
- Verificar se o baseline atual e estavel o suficiente para servir de comparador.

## Criterio de aceite

- Existe um conjunto fixo de cenarios reutilizavel.
- Existe um formato comum para comparar respostas entre rodadas.

## Dependencias

Nenhuma.

---

## Etapa 1 - Estruturacao do contrato publicado ao host

## Objetivo

Eliminar ambiguidade de consumo da tool por outra IA.

## Escopo

- Substituir ou reduzir dependencia de `payload` textual unico.
- Publicar contrato estruturado com blocos explicitos.

## Mudancas propostas

### Entrada

- `request`
- `workspace`
- `context_state`
- `constraints`

### Saida minima

- `scenario`
- `strategy`
- `tool_sequence`
- `evidence_gate`
- `stop_rules`
- `fallbacks`

## Implementacao

1. Modelar schema de entrada e saida em formato estruturado.
2. Garantir enums e booleanos explicitos nos campos centrais.
3. Remover campos vagos que so repetem texto livre.
4. Documentar obrigatorios vs opcionais.

## Testes

### Testes de contrato

- chamada valida com todos os campos;
- chamada com campos opcionais ausentes;
- chamada com enum invalido;
- chamada com shape invalido.

### Testes black-box

- comparar facilidade de consumo por outra IA antes/depois;
- medir reduçao de erro de shape ou respostas incoerentes.

## Criterio de aceite

- O contrato pode ser entendido sem depender de texto explicativo externo.
- Os campos centrais sao validaveis por shape.
- Outra IA consegue chamar a tool com menor ambiguidade.

## Riscos

- schema grande demais cedo demais.

## Mitigacao

- manter apenas campos centrais nesta fase.

---

## Etapa 2 - Formalizacao da classificacao e da estrategia macro

## Objetivo

Estabilizar o nucleo decisorio antes de sofisticar o restante do contrato.

## Escopo

- classificar cenario;
- definir estrategia macro;
- separar claramente decisao de execucao.

## Mudancas propostas

### `scenario`

- `scenario_id`
- `scenario_family`
- `scenario_confidence`

### `strategy`

- `should_plan_first`
- `should_use_repo_tools_first`
- `recommended_execution_mode`
- `should_stop_for_human_input`

### `mcp_usage`

- `level: required|recommended|not_needed`

## Implementacao

1. Fixar taxonomia inicial de cenarios.
2. Fixar regras minimas de roteamento para estrategia macro.
3. Introduzir tricotomia de uso de MCP.
4. Garantir que "plan_only" nao implica "sem MCP".

## Testes

### Estabilidade de classificacao

- Rodar 5 variacoes lexicais por cenario.
- Medir estabilidade de:
  - `scenario_family`;
  - `recommended_execution_mode`;
  - `mcp_usage.level`.

### Testes de consistencia

- caso local simples -> `mcp_usage = not_needed`;
- caso transversal -> `mcp_usage = recommended` ou `required`;
- caso `plan_only` -> sem tools mutaveis na estrategia.

## Criterio de aceite

- Classificacao central estavel nos cenarios canonicos.
- Estrategia macro muda de forma coerente conforme o tipo de pedido.

## Dependencias

- Etapa 1.

---

## Etapa 3 - Evidence gate em duas fases

## Objetivo

Evitar aplicacao prematura de policy e tornar a decisao normativa rastreavel.

## Escopo

- fase preliminar;
- reconciliacao pos-batch;
- estado do gate observavel.

## Mudancas propostas

### Campos minimos

- `required`
- `phase: preliminary|reconciled`
- `must_verify_frontmatter`
- `must_verify_workspace_signals`
- `must_reconcile_after_batch`
- `workspace_evidence_required_detected`
- `reconciliation_status`
- `reconciliation_reasons`
- `apply_policy_without_batch`
- `apply_policy_without_repo_evidence`

## Implementacao

1. Definir gate preliminar com base em pedido + sinais conhecidos.
2. Definir evento de reconciliacao apos leitura normativa em batch.
3. Atualizar campos do gate depois do batch.
4. Tornar explicito quando a policy ainda nao pode ser aplicada.

## Testes

### Casos positivos

- cenario transversal que exige batch;
- cenario em que `workspace_evidence_required` surge apenas apos batch.

### Casos negativos

- nunca aplicar policy sem batch quando `apply_policy_without_batch = false`;
- apos detectar `workspace_evidence_required`, exigir `must_verify_workspace_signals = true`.

## Criterio de aceite

- O sistema diferencia claramente decisao preliminar de decisao reconciliada.
- Casos de risco emergente no batch alteram o gate de forma observavel.

## Dependencias

- Etapas 1 e 2.

---

## Etapa 4 - `tool_sequence` auditavel com efeitos de falha e fallback

## Objetivo

Melhorar auditabilidade sem transformar a tool em workflow engine rigido.

## Escopo

- sequencia recomendada;
- `success_condition` semantico;
- `failure_effect`;
- `fallback_on_failure`.

## Mudancas propostas

### Campos por passo

- `order`
- `phase`
- `tool`
- `required`
- `why`
- `expected_output`
- `success_condition`
- `failure_effect`
- `fallback_on_failure`

### Campo global

- `tool_sequence_mode: recommended_order`

## Implementacao

1. Revisar cada etapa da sequencia para usar criterio semantico.
2. Acrescentar fallback apenas nos pontos realmente criticos.
3. Definir que `required=true` depende do contexto ainda nao satisfeito.
4. Evitar microregras de implementacao.

## Testes

### Testes de robustez

- simular retorno insuficiente em uma etapa;
- verificar se `failure_effect` e `fallback_on_failure` ficam coerentes;
- verificar se a sequencia continua sendo recomendacao, nao compulsao.

### Testes de consistencia

- `plan_only` nao deve sugerir etapa mutavel;
- `not_needed` para MCP nao deve exigir batch.

## Criterio de aceite

- Cada passo tem objetivo observavel.
- O fluxo explica o que fazer quando a etapa falha.
- A sequencia continua adaptavel.

## Dependencias

- Etapas 1, 2 e 3.

---

## Etapa 5 - Invariantes negativas e suite de testes black-box

## Objetivo

Criar uma malha minima de seguranca comportamental para validar o contrato sem acesso ao codigo-fonte.

## Escopo

- invariantes obrigatorias;
- matriz de cenarios;
- verificacao automatizavel por saida.

## Invariantes minimas

1. Se `recommended_execution_mode = plan_only`, entao:
   - `should_plan_first = true`
   - nao pode haver tool mutavel no `tool_sequence`
2. Se `mcp_usage.level = not_needed`, entao:
   - `batch_required = false` ou equivalente
3. Se `stop_required = true`, entao:
   - `stop_reasons` nao pode estar vazio
4. Se `workspace_evidence_required_detected = true` apos reconciliacao, entao:
   - `must_verify_workspace_signals = true`

## Implementacao

1. Escrever tabela de invariantes.
2. Associar cada invariante a pelo menos um cenario de teste.
3. Criar planilha ou artefato com:
   - campo observado;
   - valor esperado;
   - valor real;
   - severidade da divergencia.

## Testes

- executar bateria A/B/C/D;
- repetir com variacoes lexicais;
- registrar divergencias por severidade:
  - baixa;
  - media;
  - critica.

## Criterio de aceite

- zero divergencias criticas nas invariantes minimas;
- divergencias medias compreendidas e documentadas.

## Dependencias

- Etapas 1 a 4.

---

## Etapa 6 - Separacao da origem dos sinais

## Objetivo

Melhorar explicabilidade e reduzir alucinacao na interpretacao da decisao.

## Escopo

- separar sinais do pedido;
- sinais do repo;
- sinais descobertos no batch.

## Mudancas propostas

### `signal_sources`

- `request_declared_signals`
- `repo_observed_signals`
- `batch_discovered_signals`

## Implementacao

1. Mapear cada decisao importante para sua fonte principal.
2. Evitar misturar inferencia do pedido com evidencia observada.
3. Tornar batch-discovered explicitamente distinto do repo.

## Testes

- validar se casos iguais com repo diferente mudam apenas os sinais observados;
- validar se casos com mesmo pedido, mas batch diferente, alteram apenas sinais do batch.

## Criterio de aceite

- E possivel explicar de onde veio cada gatilho critico.

## Dependencias

- Etapas 2 a 5.

---

## Etapa 7 - Separacao entre contrato publicado, derivacoes internas e catalogo

## Objetivo

Preparar o sistema para governanca mais forte sem confundir consumidores externos.

## Escopo

- contrato publicado ao host;
- derivacoes internas;
- regras orientadas por catalogo.

## Implementacao

1. Delimitar o que o host precisa ver.
2. Delimitar o que e apenas logica interna.
3. Delimitar o que passa a ser configuravel por catalogo.

## Resultado esperado

- menos ambiguidade em debugging;
- menos mistura entre observacao externa e mecanismo interno;
- melhor caminho para evolucao catalog-driven.

## Testes

- verificar se mudancas internas nao quebram contrato publicado;
- verificar se novas regras declarativas alteram o comportamento de forma previsivel.

## Criterio de aceite

- O contrato externo permanece estavel mesmo com evolucao interna.

## Dependencias

- Etapas 1 a 6.

---

## Etapa 8 - Governanca declarativa progressiva

## Objetivo

Migrar partes adequadas da decisao para catalogo, sem perder controle sobre os casos ambiguos.

## Escopo

- taxonomia de cenarios;
- gatilhos de roteamento;
- regras de evidence gate;
- stop rules;
- fallbacks.

## Implementacao

1. Migrar primeiro cenarios e gatilhos simples.
2. Migrar depois regras de gate e stop.
3. Manter procedural para:
   - normalizacao;
   - defaults;
   - resolucao de conflitos;
   - compactacao de sequencia.

## Testes

- comparar comportamento antes/depois da migracao de cada regra;
- confirmar que o catalogo alterou comportamento observavel sem regressao.

## Criterio de aceite

- Cresce o percentual de decisoes orientadas por regra declarativa sem perda de estabilidade.

## Dependencias

- Etapa 7.

---

## Etapa 9 - Sinais avancados: `decision_stability`, `plan_granularity` e confidence por camada

## Objetivo

Adicionar sinais avancados apenas depois que o nucleo decisorio estiver estavel.

## Escopo

- `decision_stability`;
- `plan_granularity`;
- `confidence` por camada.

## Implementacao

1. Definir metrica observavel para `decision_stability`.
2. Definir rubrica objetiva para `plan_granularity`.
3. Separar confidence por:
   - cenario;
   - estrategia;
   - evidence gate;
   - stop rules.

## Testes

### `decision_stability`

- executar 5 a 10 variacoes equivalentes por cenario;
- medir repetibilidade dos campos centrais.

### `plan_granularity`

- comparar cenarios locais, medios e transversais;
- validar consistencia da granularidade.

### confidence por camada

- validar que alta confianca em classificacao nao implica alta confianca em aplicabilidade normativa.

## Criterio de aceite

- Nenhum desses campos e opinativo; todos tem rubrica observavel.

## Dependencias

- Etapas 2 a 8.

---

## Ordem recomendada de implementacao

### Trilha minima recomendada

1. Etapa 0
2. Etapa 1
3. Etapa 2
4. Etapa 3
5. Etapa 4
6. Etapa 5

Essa trilha ja entrega um MCP muito mais testavel e consumivel.

### Trilha de consolidacao

7. Etapa 6
8. Etapa 7
9. Etapa 8

### Trilha avancada

10. Etapa 9

---

## Estrategia de testes por incremento

Cada incremento deve passar por 4 camadas:

1. **Teste de contrato**
   - shape, enums, obrigatorios, opcionais
2. **Teste de cenario**
   - comportamento esperado nos cenarios A/B/C/D
3. **Teste de repetibilidade**
   - variacoes lexicais equivalentes
4. **Teste de invariantes**
   - regras que nunca devem ser violadas

---

## Regra de promocao entre etapas

Uma etapa so promove para a seguinte quando:

- contrato da etapa anterior estiver estabilizado;
- invariantes relevantes estiverem verdes;
- divergencias criticas forem zero;
- as divergencias medias estiverem documentadas e compreendidas.

---

## Backlog priorizado resumido

## P0

- Etapa 0
- Etapa 1
- Etapa 2
- Etapa 3

## P1

- Etapa 4
- Etapa 5
- Etapa 6

## P2

- Etapa 7
- Etapa 8
- Etapa 9

---

## Definicao de pronto final

O MCP pode ser considerado pronto para uma rodada mais ampla de implementacao e testes quando:

- o contrato publicado e claro para outro agente;
- a classificacao e a estrategia macro sao estaveis;
- o evidence gate em duas fases funciona de forma rastreavel;
- a `tool_sequence` e auditavel sem ser rigida;
- as invariantes minimas passam sem divergencia critica;
- os campos avancados ainda nao implementados estao explicitamente fora de escopo, e nao "implicitamente pendentes".

