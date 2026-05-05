# Guide Step by Step — MCP como compositor de contexto

## 1. Objetivo do experimento

Este experimento existe para responder a uma pergunta específica:

**o MCP `corporate-instructions` consegue compor contexto útil, rastreável e aplicável para uma implementação real, sem depender de um super prompt que ensine manualmente o uso de tools?**

Neste ensaio, o foco **não** é comparar baseline vs instructions locais vs MCP.

O foco é:

1. usar o MCP como fonte principal de composição de contexto;
2. executar o trabalho em fases curtas e auditáveis;
3. reduzir inferência indevida;
4. verificar se o resultado final fica mais profissional e reproduzível.

## 2. Escopo

### Cenário alvo

Usar novamente o cenário de outbox/mensageria:

- `POST /clientes`
- `PUT /clientes/{id}`
- outbox transacional
- publicação assíncrona
- consumidor
- read-model
- idempotência
- DLQ

### O que este experimento quer provar

- se o agente consegue compor contexto suficiente antes de implementar;
- se a sequência em fases reduz o problema do prompt monolítico;
- se o MCP ajuda o agente sem obrigar o dev a conhecer tools específicas;
- se a rastreabilidade `contexto -> decisão -> patch -> validação` fica mais clara.

### O que este experimento não quer provar agora

- superioridade estatística entre modelos;
- comparação A/B/C;
- benchmark definitivo de ranking;
- completude do corpus para todos os cenários.

## 3. Modelos recomendados por etapa

Use esta matriz como padrão.

| Etapa | Objetivo | Modelo principal | Modelo alternativo | Observação |
|---|---|---|---|---|
| 1. Composição de contexto | recuperar contexto aplicável e explicitar lacunas | `GPT 5.4` | `Sonnet 4.6` | etapa analítica; evitar ir para implementação |
| 2. Plano BMAD | decidir abordagem mínima e verificável | `GPT 5.4` | `Sonnet 4.6` | manter foco em decisão, não em código |
| 3. Implementação | codificar com base no plano aprovado | `Codex 5.3` | `Sonnet 4.6` | etapa principal de patch |
| 4. Validação e relatório | validar critérios, consolidar métricas e decisão trace | `GPT 5.4` | `Gemini Pro 2.5` | usar modelo mais analítico |

### Regra prática

- Se você quiser máxima consistência com o fluxo atual, use `GPT 5.4` nas etapas 1, 2 e 4, e `Codex 5.3` na etapa 3.
- Se quiser uma segunda rodada de robustez, repita a etapa 3 com `Sonnet 4.6`.
- `Gemini Pro 2.5` fica melhor como leitor crítico do relatório final do que como executor principal neste experimento.

## 4. Pré-requisitos

Antes de iniciar, confirme:

1. o workspace está apontando para o repositório correto;
2. o MCP `corporate-instructions` está disponível na sessão;
3. o cenário técnico escolhido continua sendo o mesmo do experimento anterior;
4. você sabe onde salvar os artefatos desta rodada;
5. você vai usar uma thread ou chat separado para cada etapa.

### Pasta de saída desta rodada

Use:

- artefatos intermediários em `artefatos/`
- relatório final em `resultados/`

### Convenção de nomes sugerida

Use a data da execução e um slug curto.

Exemplo:

- `artefatos/2026-05-03__contexto-composto.md`
- `artefatos/2026-05-03__plano-bmad.md`
- `resultados/2026-05-03__cenario-01-outbox__mcp-context-composer.md`

## 5. Regra central do experimento

O prompt enviado ao agente deve descrever o **objetivo**, não a lista de tools.

Logo:

- o dev **não deve** instruir manualmente `list_instructions_index`, `search_instructions`, `get_instructions_batch` etc.;
- o agente deve usar o MCP de forma transparente;
- se existir resource/prompt composto do próprio MCP, ele deve ser preferido;
- se não existir, o agente ainda deve agir como se o MCP fosse a camada de composição de contexto, e não apenas um catálogo.

## 6. Sequência obrigatória de execução

Execute as etapas **na ordem abaixo**.

Não pule etapa.

Não execute implementação antes da composição de contexto e do plano.

### Resumo operacional rápido

Se você quiser seguir o experimento de forma mecânica, faça exatamente isto:

1. crie uma thread nova e rode o prompt 01 com `GPT 5.4`;
2. salve a saída em `artefatos/YYYY-MM-DD__contexto-composto.md`;
3. crie uma nova thread e rode o prompt 02 com `GPT 5.4`, usando a saída da etapa 1;
4. salve a saída em `artefatos/YYYY-MM-DD__plano-bmad.md`;
5. crie uma nova thread e rode o prompt 03 com `Codex 5.3`, usando as saídas das etapas 1 e 2;
6. salve a resposta em `artefatos/YYYY-MM-DD__implementacao-execucao.md`;
7. se houver telemetry do MCP, gere o sumário com o script indicado na seção 7;
8. crie uma nova thread e rode o prompt 04 com `GPT 5.4`, anexando os artefatos anteriores e os logs disponíveis;
9. salve o relatório final em `resultados/YYYY-MM-DD__cenario-01-outbox__mcp-context-composer.md`.

### Etapa 1 — Composição de contexto

- Modelo: `GPT 5.4`
- Prompt: [`prompts/01-composicao-contexto-mcp.md`](prompts/01-composicao-contexto-mcp.md)
- Saída esperada:
  - matriz de contexto;
  - decisões que precisam de contexto externo;
  - evidência do repo;
  - lacunas;
  - riscos de inferência.

#### Regra de término da etapa 1

Só avance se existir um artefato claro dizendo:

- o que o MCP trouxe;
- o que o repositório confirma;
- o que continua como hipótese;
- o que não pode ser implementado sem confirmação adicional.

Se a saída vier superficial ou já começar a codar, refaça a etapa.

### Etapa 2 — Plano BMAD

- Modelo: `GPT 5.4`
- Prompt: [`prompts/02-plano-bmad-mcp.md`](prompts/02-plano-bmad-mcp.md)
- Entrada obrigatória:
  - resultado da etapa 1.
- Saída esperada:
  - `Background`
  - `Mission`
  - `Approach`
  - `Delivery/validation`
  - decisões permitidas;
  - decisões bloqueadas;
  - fallback para lacunas críticas.

#### Regra de término da etapa 2

Só avance se o plano:

- estiver coerente com o contexto composto;
- limitar explicitamente o escopo;
- impedir overengineering;
- deixar claro o que será validado.

### Etapa 3 — Implementação

- Modelo: `Codex 5.3`
- Prompt: [`prompts/03-implementacao-mcp.md`](prompts/03-implementacao-mcp.md)
- Entrada obrigatória:
  - resultado da etapa 1;
  - resultado da etapa 2.
- Saída esperada:
  - patch;
  - resumo objetivo do que foi implementado;
  - lista de decisões aplicadas;
  - sinalização clara do que veio de MCP, código local ou hipótese.

#### Regra de término da etapa 3

Só avance se:

- o patch respeitar o plano;
- não houver expansão desnecessária do escopo;
- a implementação não criar infraestrutura pública nova por inferência sem aviso claro.

### Etapa 4 — Validação e relatório

- Modelo: `GPT 5.4`
- Prompt: [`prompts/04-validacao-relatorio-mcp.md`](prompts/04-validacao-relatorio-mcp.md)
- Entrada obrigatória:
  - resultado da etapa 1;
  - resultado da etapa 2;
  - diff/resultado da etapa 3.
- Saída esperada:
  - validação dos critérios de aceite;
  - relatório técnico final;
  - métricas;
  - blocos JSON;
  - conclusão.

#### Regra de término da etapa 4

Só considere a rodada completa quando existir um relatório final com:

- validação objetiva;
- `EXPERIMENT_METRICS_JSON`;
- `DECISIONS_JSON`;
- `CONTEXT_COMPOSITION_JSON`.

## 7. Como coletar métricas

Este experimento deve coletar métricas de forma explícita. Quando algo não estiver disponível automaticamente, marque `N/A` e explique o método de estimativa.

### 7.1 Métricas de tempo

Campos:

- `inicio_iso`
- `fim_iso`
- `duracao_ms`
- `composicao_contexto_ms`
- `plano_bmad_ms`
- `implementacao_ms`
- `validacao_relatorio_ms`

### Como recuperar

- marque o horário no início e no fim de cada etapa;
- se o cliente/plataforma não fornecer duração automática, calcule manualmente;
- registre no relatório final.

### 7.2 Métricas de uso do MCP

Campos:

- `qtd_tool_calls_total`
- `qtd_por_tool`
- `sucessos`
- `falhas`
- `retries`
- `search_confidence_avg`
- `zero_result_rate`
- `low_confidence_rate`

### Como recuperar

1. se houver telemetry NDJSON do MCP, use-a como fonte principal;
2. gere um sumário com `mcp-instructions-server/scripts/build_quality_report.py`;
3. se não houver telemetry disponível nesta sessão, marque os diagnósticos agregados como `N/A`.

#### Comando recomendado

Use este comando, adaptando os caminhos:

```bash
python "mcp-instructions-server/scripts/build_quality_report.py" --input "CAMINHO/telemetry.ndjson" --output "CAMINHO/quality-report.json"
```

Se você tiver um baseline interno de telemetry para comparação, pode acrescentar:

```bash
python "mcp-instructions-server/scripts/build_quality_report.py" --input "CAMINHO/telemetry.ndjson" --output "CAMINHO/quality-report.json" --baseline "CAMINHO/baseline-quality-report.json"
```

#### Campos que devem ser copiados do quality report

- `total_completed_calls`
- `tool_failures`
- `retries_total`
- `zero_result_rate`
- `low_confidence_rate`
- `avg_search_confidence`
- `tool_breakdown`

### 7.3 Métricas de composição de contexto

Campos:

- `qtd_decisoes_que_precisam_contexto`
- `qtd_ids_mcp_selecionados`
- `qtd_ids_mcp_usados_no_plano`
- `qtd_decisoes_ancoradas_em_mcp`
- `qtd_decisoes_ancoradas_no_repo`
- `qtd_decisoes_por_inferencia`
- `qtd_lacunas_criticas`

### Como recuperar

- contar a partir da matriz produzida na etapa 1;
- conferir novamente no relatório final;
- registrar em `CONTEXT_COMPOSITION_JSON`.
- se o agente citar ids MCP explicitamente, conte apenas os ids realmente usados na decisão final, não todos os ids vistos durante exploração.

### 7.4 Métricas de implementação

Campos:

- `qtd_arquivos_lidos`
- `qtd_arquivos_citados`
- `qtd_trechos_citados`
- `qtd_itens_patch`
- `build_status`
- `tests_status`
- `qtd_criterios_aceite_ok`
- `qtd_criterios_aceite_na`
- `qtd_criterios_aceite_pendentes`

### Como recuperar

- contar a partir do relatório final da etapa 4;
- usar build/testes efetivamente executados;
- quando não houver testes, marcar como `N/A` e explicar.
- para `qtd_itens_patch`, contar arquivos alterados ou criados diretamente pela implementação.

### 7.5 Métricas de ergonomia

Campos:

- `precisou_reprompt`
- `qtd_reprompts`
- `dev_precisou_citar_tool`
- `agente_pediu_confirmacao_por_lacuna_critica`
- `houve_overengineering`

### Como recuperar

- preencher manualmente no relatório final;
- usar uma escala simples:
  - `houve_overengineering`: `baixo`, `medio`, `alto`.
- `dev_precisou_citar_tool` deve ser `nao` quando o prompt do experimento não tiver ensinado nomes de tools ao agente.

## 8. Blocos obrigatórios no relatório final

O relatório final deve conter exatamente estes três blocos:

1. `EXPERIMENT_METRICS_JSON`
2. `DECISIONS_JSON`
3. `CONTEXT_COMPOSITION_JSON`

### Estrutura mínima esperada

#### `EXPERIMENT_METRICS_JSON`

Deve conter:

- tempos por etapa;
- uso de tools;
- I/O de contexto;
- patch;
- build/testes;
- critérios de aceite;
- ergonomia.

#### `DECISIONS_JSON`

Cada decisão deve ter:

- `decisao`
- `ancoragem`
- `evidencia`
- `risco`
- `como_validar`

#### `CONTEXT_COMPOSITION_JSON`

Deve conter:

- `scenario`
- `context_mode`
- `models_used`
- `decisions_required`
- `ids_selected`
- `ids_used_in_final_decisions`
- `repo_evidence_items`
- `critical_gaps`
- `decisions_from_mcp`
- `decisions_from_repo`
- `decisions_from_inference`

## 9. Resultado esperado de uma boa execução

Ao final de uma rodada bem executada, você deve conseguir responder com evidência:

1. o MCP ajudou a compor contexto antes do patch?
2. esse contexto foi realmente usado nas decisões?
3. o agente implementou com menos inferência ad hoc?
4. o fluxo em fases foi mais controlado que o super prompt anterior?

Se a resposta para esses quatro pontos continuar nebulosa, o experimento não atingiu seu objetivo e deve ser repetido com ajuste de protocolo.

## 10. Checklist final do operador

Antes de encerrar, confirme:

- [ ] executei as 4 etapas na ordem correta;
- [ ] usei o modelo recomendado em cada etapa ou registrei a exceção;
- [ ] guardei os artefatos intermediários;
- [ ] o relatório final contém os 3 blocos JSON;
- [ ] as métricas têm fonte ou justificativa de estimativa;
- [ ] o prompt do experimento não ensinou manualmente nomes de tools;
- [ ] o foco permaneceu em MCP como compositor de contexto.
