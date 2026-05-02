Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, qualidade de implementação e comportamento do Copilot na ausência de contexto estruturado.

## Contexto do experimento

**Identificação:** Cenário 1 (Outbox / mensageria) — condição **C: Baseline**.

Estou avaliando o comportamento do Copilot em um cenário sem contexto estruturado dedicado, sem uso de `copilot-instructions.md`, `.github/instructions` e MCP `corporate-instructions`.

Neste teste, considere que:
- não há `.github/instructions` como fonte confiável de orientação adicional;
- não há MCP como mecanismo de recuperação de contexto;
- o contexto disponível vem apenas do código visível no workspace e do conhecimento geral do modelo.

**Regras de orquestração (condição C)**

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Limites:** se faltar informação decisiva, explicitar a inferência e oferecer 2–3 opções.
- **Não usar** MCP `corporate-instructions`.
- **Não usar** `.github/instructions/` nem outro corpus externo de políticas. Apenas o código e artefactos deste repositório são fonte de verdade.
- Se não houver evidência no código, rotular como **HIPÓTESE** e descrever como validar; não apresentar hipótese como norma organizacional.
- **Contexto do repo:** API de gestão de clientes em camadas; C#, .NET 8, ASP.NET Core.
- **Fluxo mínimo:** usar **BMAD** antes de codificar — Background, Mission, Approach, Delivery/validation.

O objetivo do experimento não é apenas avaliar a qualidade da resposta, mas observar:
- quanto da solução depende de inferência;
- quais lacunas aparecem sem uma fonte estruturada de contexto;
- quão sustentável é esse modo de trabalho para implementação real.

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

**Orientação de desenho (derivar do código existente; não assumir stack não presente):**

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

1. Execute a tarefa normalmente com base apenas no código disponível.
2. Após a execução, produza um relatório técnico estruturado.
3. Diferencie explicitamente:
   - FATO
   - HIPÓTESE
   - RISCO DE INTERPRETAÇÃO
4. Não trate inferência como evidência.
5. Seja crítico e direto.
6. Ao final, reporte métricas de execução. Se alguma métrica não puder ser obtida automaticamente, marque como N/A e explique o método de estimativa e o impacto na validade do experimento.
7. Exporte o resultado para um arquivo Markdown no workspace (ver seção “Exportação”).

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__baseline.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`baseline`).

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação em memória/fila local conforme evidência no código).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model** (`ClienteReadModel` ou equivalente do projeto); garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite e evidência no repositório.

#### 2) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 3) Implementação (patch)
- Aplique as mudanças no código (Outbox, publicação, consumidor, read-model, idempotência, DLQ, impacto em API/domínio/infraestrutura conforme padrões do repo).

#### 4) Validação
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
- `ancoragem` (codigo_repo | inferencia)
- `evidencia` (arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

### 1. Uso de contexto
Avalie:
- quais decisões foram ancoradas diretamente no código;
- quais decisões dependeram de inferência;
- quais lacunas impediram maior precisão.

### 2. Qualidade técnica do plano
Avalie:
- estrutura do plano;
- clareza de camadas;
- coerência arquitetural;
- adequação ao nível de complexidade da tarefa;
- sinais de genericidade ou overengineering.

### 3. Limitações estruturais da abordagem
Analise:
- riscos de depender apenas do código visível;
- impacto da ausência de diretrizes explícitas;
- probabilidade de respostas inconsistentes entre execuções;
- risco de erro em desenvolvimento real.

### 4. Sustentabilidade para implementação real
Explique:
- se essa abordagem se sustenta em tarefas reais;
- qual esforço de reprompt tende a ser necessário;
- quais tipos de decisão ficam frágeis sem contexto adicional.

### 5. Experiência de uso
Avalie:
- fluidez;
- previsibilidade;
- necessidade de descoberta manual;
- dependência de interpretação do modelo.

## Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao código observável
- qualidade técnica
- completude
- consistência
- previsibilidade
- sustentabilidade para implementação real

## Conclusão final

Escolha apenas uma:

- “baseline é suficiente para este tipo de implementação”
- “baseline funciona parcialmente, mas exige muita inferência”
- “baseline é insuficiente para implementação confiável”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como arquiteto, não como usuário casual.
- Priorize evidência observável sobre opinião.
