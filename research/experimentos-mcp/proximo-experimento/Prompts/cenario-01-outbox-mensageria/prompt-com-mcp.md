Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, engenharia de contexto e escalabilidade em múltiplos repositórios.

## Contexto do experimento

**Identificação:** Cenário 1 (Outbox / mensageria) — condição **A: MCP** (`corporate-instructions`).

Estou avaliando o comportamento do Copilot em um cenário com MCP `corporate-instructions`.

Objetivo do experimento:
- avaliar a qualidade da implementação produzida (plano + patch + validação);
- avaliar o quanto a solução depende de contexto local real;
- analisar a viabilidade dessa abordagem em cenários com muitos repositórios;
- identificar riscos de duplicação, drift, manutenção, inconsistência e acoplamento ao repositório.

Neste teste, considere que o contexto vem de:
- contexto recuperado via MCP `corporate-instructions` (tools/resources), como fonte principal de guardrails organizacionais;
- instructions locais (quando existirem) e código disponível no workspace como evidência observável complementar.

**Regras de orquestração (condição A)**

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Stack assumida:** API de clientes em C#, .NET 8, ASP.NET Core, arquitetura em camadas.
- **MCP `corporate-instructions`:** padrões organizacionais vêm do MCP (não estão no repo). Este bloco de orquestração prevalece sobre o MCP se houver conflito **explícito** com o que se pede abaixo.
- **Consulta MCP obrigatória em decisões transversais:**
  1. `list_instructions_index` — ver corpus e agrupamentos.
  2. `search_instructions` — várias queries por tema (mensageria, outbox, idempotência, resiliência, SQL, observabilidade); não uma única busca.
  3. `get_instructions_batch` — ler o corpo completo de todas as instructions relevantes de uma vez.
  4. Cruzar policy do MCP com o código: o que já existe no repo é **FATO**; o que não existe é **HIPÓTESE**. O código existente prevalece.
  5. Citar nas decisões: id da instruction + ficheiros do repo tocados.
- **Fluxo:** antes de editar ficheiros críticos, ler o alvo; após mudanças grandes, executar `dotnet build` e testes se existirem.

## Tarefa

**Título:** Implementar publicação de eventos de cliente via mensageria com garantia de entrega.

**Descrição:**

Quando um cliente é criado (`POST /clientes`) ou atualizado (`PUT /clientes/{id}`):

1. Persistir o evento numa tabela **Outbox** local na **mesma transação** do `INSERT`/`UPDATE` do cliente.
2. Publicar o evento para um tópico ou fila de mensageria (RabbitMQ **ou** simulação em memória / fila local se o projeto não tiver broker real).
3. Implementar **consumidor** que lê eventos do tópico/fila e atualiza um **modelo de leitura** (`ClienteReadModel` ou equivalente alinhado ao projeto).
4. Garantir **idempotência:** o mesmo evento publicado duas vezes não duplica efeito na read-model.
5. Implementar **DLQ** (Dead Letter Queue ou tabela equivalente) para eventos que falharem após **N** tentativas (definir N de forma explícita no código, p.ex. 3).

**Restrições:**

- Não quebrar o CRUD existente (`GET`, `PUT`, `POST`, `DELETE`).
- Cache em `GET`, se existir, deve ser invalidado após publicação bem-sucedida **ou** usar TTL curto se a mensageria falhar (documentar a escolha).
- O build deve passar; testes de integração são desejáveis se o repositório já os suportar.

**Cenários de comportamento esperados:**

- Cliente criado com sucesso → evento publicado e consumido; read-model coerente.
- Cliente atualizado com sucesso → evento publicado e consumido; idempotência verificável.
- Falha ao publicar → evento permanece processável via Outbox/retry.
- Consumidor falha uma vez e sucede na segunda → DLQ vazio; read-model atualizado.

**Orientação de desenho (não prescritiva se o MCP/código indicar outro padrão coerente):**

- Tabela tipo `ClienteEventosOutbox` com campos incluindo: identificador, tipo de evento, payload, criado em, estado processado/publicado.
- Serviço de domínio: após `INSERT`/`UPDATE` bem-sucedido do cliente, registar evento no Outbox na mesma transação.
- Interface de publicação: tentar publicar; em falha, deixar registo no Outbox para retry.
- Idempotência: chave de idempotência, hash do evento ou equivalente.
- DLQ: após esgotar retries, mover ou registar em estrutura de DLQ.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| Outbox | Tabela (ou equivalente) com tipo de evento, payload, timestamps e controlo de processamento |
| POST gera evento | Criar cliente → registo de evento no Outbox |
| PUT gera evento | Atualizar cliente → registo de evento no Outbox |
| Read-model | Após consumo, modelo de leitura reflete o cliente |
| Idempotência | Publicar o mesmo evento duas vezes → um único efeito na read-model |
| DLQ | Após falhas repetidas do consumidor → evento em DLQ ou equivalente |
| Cache | Após `PUT` + fluxo de publicação, `GET` reflete alterações (ou TTL documentado) |
| Correlação | Evento ou pipeline carrega `CorrelationId` alinhado ao pedido HTTP, se o projeto já usar esse conceito |
| Segurança | SQL parametrizado; sem concatenação insegura |

A implementação deve ser validável contra a tabela acima (comandos e critérios de sucesso explícitos na Parte 1).

## Regras obrigatórias

1. Execute a tarefa usando MCP `corporate-instructions` como fonte principal de guardrails organizacionais, cruzando sempre com o código do repositório; quando instructions locais existirem, incorpore-as como evidência complementar.
2. Após a execução, produza um relatório técnico estruturado.
3. Diferencie explicitamente:
   - FATO
   - HIPÓTESE
   - RISCO DE INTERPRETAÇÃO
4. Não trate inferência como evidência.
5. Seja crítico e direto.
6. Ao final, reporte métricas de execução. Se alguma métrica não puder ser obtida automaticamente, marque como N/A e explique o método de estimativa e o impacto na validade do experimento.
7. Exporte o resultado para um arquivo Markdown no workspace (ver seção “Exportação”).
8. Política de uso de tools: prefira “tool-first” para recuperar guardrails via MCP (e ler ficheiros do repo) antes de propor mudanças; se exceder o necessário, justifique no relatório (custo/benefício e o que foi obtido).

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__mcp.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`mcp`).

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Seleção de guardrails e evidências (antes de codar)
- Liste os `id` das instructions aplicáveis via MCP (e, se existirem, locais) e para qual decisão cada uma será usada (ex.: mensageria, outbox, idempotência, SQL, observabilidade, erros).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).

#### 2) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação conforme MCP + código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite.

#### 3) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 4) Implementação (patch)
- Aplique as mudanças no código (Outbox, publicação, consumidor, read-model, idempotência, DLQ, impacto em API/domínio/infraestrutura conforme padrões do repo e corpus MCP aplicável).

#### 5) Validação
- Execute/indique validações objetivas (por exemplo: `dotnet build`, testes unitários/integração quando aplicável).
- Relacione cada linha relevante da tabela de critérios de aceite a um passo de verificação ou comando.
- Se não for possível executar algo, descreva o comando exato e o critério de sucesso.

## Relatório do experimento

### 0. Métricas de execução (obrigatório)
Reporte, no mínimo, os itens abaixo (use N/A quando a plataforma não fornecer o dado):
- tempo total (wall-clock): `inicio_iso`, `fim_iso`, `duracao_ms`
- latência por etapa: exploração/leitura, raciocínio/decisão, escrita do patch, validação, escrita do relatório (em ms)
- uso de tools: `qtd_tool_calls_total`, `qtd_por_tool`, `sucessos`, `falhas`, `retries`
- I/O de contexto: `qtd_arquivos_lidos`, `qtd_arquivos_citados`, `qtd_trechos_citados`, `bytes_aprox_lidos` (ou N/A)
- tokens: `tokens_input` e `tokens_output` (se disponível); senão `tokens_input_est` e `tokens_output_est` + método + margem de erro assumida
- custo: `custo_total` e `moeda` (ou N/A)
- tamanho do resultado: `caracteres_resposta` (ou N/A) e `qtd_itens_patch`
- contagens para rigor experimental: `qtd_afirmacoes_FATO`, `qtd_afirmacoes_HIPOTESE`, `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`

Ao final do relatório, inclua obrigatoriamente um bloco único chamado `EXPERIMENT_METRICS_JSON` contendo exatamente os campos acima em JSON.

Inclua também obrigatoriamente um bloco único chamado `DECISIONS_JSON` (em JSON) com, no mínimo, uma lista de decisões-chave contendo:
- `decisao`
- `ancoragem` (MCP | instruction_local | codigo_repo | inferencia)
- `evidencia` (id/arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

### 1. Evidência de uso de contexto
Para cada decisão importante da solução, classifique como:
- ancorada em instruction MCP;
- ancorada em instruction local;
- ancorada no código do repositório;
- inferida por conhecimento geral.

Aponte:
- quais decisões mostram uso efetivo do corpus MCP;
- onde houve lacunas;
- onde o plano dependeu de inferência.

### 2. Qualidade técnica do plano
Avalie:
- estruturação do plano (BMAD) e adequação do patch ao plano;
- clareza de camadas;
- coerência arquitetural;
- adequação ao nível de complexidade da tarefa;
- presença de excesso de genericidade ou overengineering.

### 3. Limitações estruturais da abordagem
Analise criticamente:
- duplicação entre repositórios;
- risco de drift entre MCP e código local;
- dificuldade de evolução centralizada do corpus;
- acoplamento do conhecimento ao repositório.

### 4. Escalabilidade em 100+ repositórios
Explique:
- se a abordagem MCP + código se sustenta;
- em que condições ela deixa de se sustentar;
- qual esforço de manutenção ela tende a exigir;
- quais riscos operacionais são previsíveis.

### 5. Experiência de uso
Avalie:
- fluidez;
- necessidade de reprompt;
- dependência de descoberta manual;
- previsibilidade do comportamento.

## Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao contexto recuperado (MCP + repo)
- qualidade técnica
- completude
- consistência
- escalabilidade da abordagem
- facilidade de manutenção

## Conclusão final

Escolha apenas uma:

- “MCP corporate-instructions foi suficiente para ancorar guardrails neste tipo de implementação”
- “MCP ajudou parcialmente, mas ainda foi necessária inferência significativa”
- “MCP não foi adequado para reduzir inferência ou guiar a implementação de forma confiável”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como arquiteto de soluções corporativas, não como usuário casual.
- Priorize evidência observável (código, corpus MCP, instructions locais) sobre opinião.
- Não produza resposta diplomática quando a evidência for fraca; registre o risco.
