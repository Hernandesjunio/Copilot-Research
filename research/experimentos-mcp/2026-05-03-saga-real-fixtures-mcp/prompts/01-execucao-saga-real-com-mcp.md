> **Nota (2026-05-05):** este experimento foi usado como *teste de realidade* para identificar limites da evolução do MCP rumo a “compositor de contexto”.
> O resultado motivou o redirecionamento para **Instruction Retrieval v1** (foco em filtros + aplicabilidade + 3 tools básicas), adiando composição automática.
>
> Referências:
> - Síntese datada da decisão: `research/analises/2026-05-05-redirecionamento-mcp-instruction-retrieval-v1.md`
> - Plano técnico (tema): `research/nucleo-pesquisa/instruction-retrieval-v1/plano_mcp_instruction_retrieval_v1.md`

Quero que voce atue como um arquiteto de solucoes e executor tecnico rigoroso, com foco em MCP, SAGA, consistencia eventual e reducao de inferencia indevida.

## Contexto do experimento

Estou avaliando se o MCP `corporate-instructions` ajuda de forma real em um cenario de SAGA, mas agora com uma regra mais dura:

- o cenario precisa ser **realista e ancorado no repositorio**;
- a IA nao deve partir de um fluxo inventado sem sinais suficientes;
- o corpus MCP deve ser usado como fonte principal de guardrails organizacionais;
- o codigo do workspace e as instrucoes locais devem ser usados como evidencia observavel complementar;
- se faltarem sinais suficientes, a IA deve **parar**, explicar a lacuna e nao improvisar infraestrutura.

## Escopo da tarefa

Voce deve identificar e, se houver base suficiente, implementar **um vertical slice de SAGA / Process Manager** em um fluxo real ja sugerido pelo repositorio.

### Passo 0 - Escolha do cenario real

Antes de planejar ou codificar, procure no repositorio um fluxo candidato que tenha o maximo possivel destes sinais:

1. 3 ou mais passos dependentes;
2. ao menos um passo com integracao externa, publicacao de evento, fila, worker, gateway, HTTP client ou stub equivalente;
3. risco de inconsistencia parcial em caso de falha;
4. compensacao plausivel ou fallback operacional explicito;
5. contrato publico ou ponto de entrada ja ancorado no repo.

Exemplos de cenario candidato, **somente se o repo realmente indicar**:

- onboarding;
- checkout / pedido;
- reserva / booking;
- pagamento + notificacao;
- cadastro + provisionamento + envio de evento;
- qualquer outro fluxo equivalente observado no codigo.

### Regra de selecao do cenario

Se houver varios candidatos, escolha o que combinar:

- **maior evidenca no repo**;
- **menor dependencia de infraestrutura nova**;
- **maior aderencia aos guardrails do MCP**;
- **melhor validabilidade**.

Se **nao** houver candidato suficientemente ancorado, **nao implemente**. Em vez disso:

- produza o plano BMAD do que faltou;
- explique por que o experimento ficou bloqueado;
- registre quais evidencias tornariam a implementacao segura na proxima rodada.

## Guardrails MCP que devem ser considerados quando aplicaveis

Considere especialmente estes temas via MCP:

- saga/process manager e compensacoes;
- mensageria, outbox e consumo idempotente;
- dados SQL e timeouts;
- resiliencia, retry e timeout;
- semantica REST e codigos HTTP;
- validacao e contrato de erro;
- correlacao e observabilidade;
- estrategia de testes;
- BMAD e inferencia controlada.

## Regra critica de aplicabilidade

Se uma instruction exigir `workspace_evidence_required`, voce deve cruzar com sinais reais do repo antes de trata-la como norma aplicavel.

Em particular:

- **nao** assuma RabbitMQ, outbox, MassTransit, BackgroundService, HttpClientFactory, OpenTelemetry ou qualquer stack concreta sem sinais reais do workspace;
- se esses sinais nao existirem, trate a decisao como **HIPOTESE** ou mantenha fora do escopo;
- uma SAGA manual in-process com estado duravel pode ser valida quando o repo nao tiver framework de saga.

## Tarefa tecnica

Depois de escolher o cenario real, implemente o seguinte **somente se houver base suficiente**:

- fluxo multipasso com 3 passos ou mais;
- estado duravel da saga;
- timeout global;
- retry explicito para falhas transientes e apenas em passos idempotentes;
- compensacoes idempotentes na ordem inversa;
- correlacao (`CorrelationId` / `SagaId` ou equivalente observado no projeto);
- validacao objetiva dos principais cenarios.

### Requisitos minimos de desenho

- preferir **orquestracao manual explicita** quando nao houver framework de saga no repo;
- manter regras de negocio fora da camada de API;
- nao manter transacoes abertas atravessando I/O externo;
- se houver publicacao de mensagem dependente de escrita no banco e existirem sinais de mensageria/outbox no repo, considerar o padrao de outbox;
- se nao houver sinais de mensageria/outbox, nao inventar esse stack apenas para "melhorar" a arquitetura.

## Cenarios esperados

Voce deve validar ou descrever com comando exato:

- happy path;
- falha no passo intermediario com compensacao;
- falha no passo final com compensacao reversa ou fallback operacional;
- retry com sucesso eventual em falha transiente;
- timeout global com expiracao controlada;
- idempotencia ou reentrada;
- correlacao observavel;
- quando houver mensageria real no repo, idempotencia de publicacao/consumo e, se aplicavel, outbox.

## Regras obrigatorias

1. Use o MCP `corporate-instructions` como fonte principal de guardrails, sempre cruzando com o codigo do repositorio.
2. Diferencie explicitamente `FATO`, `HIPOTESE` e `RISCO DE INTERPRETACAO`.
3. Nao trate ausencia de evidencia como licenca para inventar contrato, fila, worker ou integracao.
4. Produza plano BMAD **antes** de editar.
5. Se o cenario escolhido depender de infra nova sem evidencia suficiente, pare e peca confirmacao humana em vez de implementar.
6. Seja critico e direto no relatorio final.
7. Ao final, reporte metricas de execucao. Se alguma metrica nao puder ser obtida automaticamente, marque `N/A` e explique o metodo de estimativa.
8. Exporte o resultado para um arquivo Markdown em:
   `research/experimentos-mcp/2026-05-03-saga-real-fixtures-mcp/artefatos/YYYY-MM-DD__execucao-saga-real-mcp.md`

## Saida esperada

### Parte 1 - Execucao

#### 1) Selecao do cenario real e dos guardrails

- Liste os `id` das instructions MCP aplicaveis e para qual decisao cada uma sera usada.
- Liste as evidencias do repo que justificam o cenario escolhido.
- Explique por que esse cenario foi escolhido em vez de alternativas vistas.
- Se a implementacao ficar bloqueada, diga isso aqui e explique o bloqueio.

#### 2) Cenario canonico

Defina o vertical slice em uma formulacao curta, no formato:

- fluxo real escolhido no repo;
- 3+ passos;
- estado duravel;
- timeout global;
- retry explicito;
- compensacoes idempotentes;
- correlacao alinhada ao projeto;
- outbox/mensageria **somente se houver evidencia suficiente**.

#### 3) Plano BMAD

Use o formato:

- Background
- Mission
- Approach
- Delivery/validation

Depois acrescente obrigatoriamente:

- Riscos
- Dependencias
- Criterios de aceite tecnico

#### 4) Implementacao ou stop justificado

- Se houver base suficiente, aplique as mudancas no codigo.
- Se nao houver base suficiente, nao invente implementacao: produza stop justificado e backlog minimo do que falta.

#### 5) Validacao

- Execute ou indique validacoes objetivas (`build`, testes, cenarios manuais, consultas, filas, logs ou equivalentes).
- Relacione cada criterio de aceite a uma verificacao.
- Se algo nao puder ser executado, descreva o comando exato e o criterio de sucesso.

### Parte 2 - Relatorio do experimento

#### 0. Metricas de execucao

Reporte no minimo:

- `inicio_iso`, `fim_iso`, `duracao_ms`
- `latencia_exploracao_leitura_ms`
- `latencia_raciocinio_decisao_ms`
- `latencia_escrita_patch_ms`
- `latencia_validacao_ms`
- `latencia_escrita_relatorio_ms`
- `qtd_tool_calls_total`, `qtd_por_tool`, `sucessos`, `falhas`, `retries`
- `qtd_arquivos_lidos`, `qtd_arquivos_citados`, `qtd_trechos_citados`, `bytes_aprox_lidos`
- `tokens_input` e `tokens_output`, ou estimativa equivalente
- `custo_total`, `moeda`
- `caracteres_resposta`, `qtd_itens_patch`
- `qtd_afirmacoes_FATO`, `qtd_afirmacoes_HIPOTESE`, `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`

Inclua ao final um bloco unico `EXPERIMENT_METRICS_JSON`.

Inclua tambem um bloco unico `DECISIONS_JSON` com, no minimo:

- `decisao`
- `ancoragem` (`MCP` | `instruction_local` | `codigo_repo` | `inferencia`)
- `evidencia`
- `risco`
- `como_validar`

#### 1. Evidencia de uso de contexto

Avalie:

- quais decisoes vieram do MCP;
- quais vieram do repo;
- onde houve reconciliacao correta entre guardrail e workspace;
- onde ainda houve lacuna ou inferencia relevante.

#### 2. Qualidade tecnica do plano

Avalie:

- qualidade da escolha do cenario;
- estrutura do BMAD;
- coerencia entre plano e patch;
- sinais de sobre-engenharia;
- qualidade da estrategia de validacao.

#### 3. Limites da abordagem

Analise:

- risco de drift entre guardrail e realidade do repo;
- dependencia de sinais locais;
- risco de repeticao manual em outros repositorios;
- fragilidade quando faltam contratos ou testes.

#### 4. Escalabilidade

Explique:

- se a abordagem se sustenta em muitos repositorios;
- quando deixa de se sustentar;
- quais partes deveriam virar template, recipe ou checklist reutilizavel.

#### 5. Experiencia de uso

Avalie:

- fluidez;
- necessidade de reprompt;
- previsibilidade;
- dependencia de descoberta manual.

## Avaliacao

Use nota de 0 a 2 para cada criterio:

- aderencia ao contexto recuperado (MCP + repo)
- qualidade tecnica
- completude
- consistencia
- escalabilidade da abordagem
- facilidade de manutencao

## Conclusao final

Escolha apenas uma:

- "MCP corporate-instructions foi suficiente para ancorar guardrails neste tipo de implementacao"
- "MCP ajudou parcialmente, mas ainda foi necessaria inferencia significativa"
- "MCP nao foi adequado para reduzir inferencia ou guiar a implementacao de forma confiavel"

Depois acrescente obrigatoriamente:

- a principal evidencia que sustenta a conclusao;
- a principal limitacao do proprio experimento.

## Importante

- Seja critico.
- Priorize evidencia observavel.
- Se o experimento travar por falta de sinais reais, trate isso como resultado valido e relevante.
