Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, centralização de conhecimento e comportamento do Copilot ao usar `.github/instructions`.

## Contexto do experimento

**Identificação:** Cenário 1 (Outbox / mensageria) — condição **B: Instructions locais**.

Estou avaliando o comportamento do Copilot em um cenário com `.github/instructions`.

Neste teste, considere que:
- as `.github/instructions` são a principal fonte de guardrails/contexto adicional;
- não há MCP como mecanismo de recuperação de contexto;
- o objetivo não é apenas avaliar qualidade da resposta, mas verificar a viabilidade dessa abordagem como mecanismo de centralização e governança de conhecimento no repositório;
- o interesse está em observar se essa estratégia pode sustentar reutilização e consistência quando o corpus é versionado no próprio projeto.

Quero observar:
- se houve uso efetivo das instructions locais e das tools de leitura de ficheiros;
- quais decisões foram apoiadas por ficheiros em `.github/instructions/`;
- se a abordagem se sustenta como complemento ao código observável.

**Regras de orquestração (condição B)**

- **Idioma:** português. **Segurança:** não incluir segredos/tokens/dados pessoais. **Escopo:** não assumir código ou infraestrutura de outros serviços além deste repositório.
- **Não inventar:** sem evidência no código ou em `.github/instructions/`, rotular como **HIPÓTESE** e dizer como validar.
- **Fonte principal de padrões:** ficheiros em **`.github/instructions/`** deste projeto. Se essa pasta não existir ou não cobrir o tema, declarar **lacuna**; não substituir por políticas inventadas.
- **Não usar MCP** `corporate-instructions` nesta condição.
- **Fluxo mínimo:** usar **BMAD** antes de codificar — Background, Mission, Approach, Delivery/validation. Em dúvidas de convenção (mensageria, transações, erros), procurar instruction local e citar o ficheiro usado.

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

**Orientação de desenho (ajustar às instructions locais e ao código existente):**

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

1. Execute a tarefa usando `.github/instructions/` (quando existirem) e o código do workspace como fontes de evidência; quando uma decisão for sustentada por instructions locais, cite o ficheiro (e `id` se existir no frontmatter).
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
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__instructions-locais.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`instructions-locais`).

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Seleção de guardrails e evidências (antes de codar)
- Liste os `id`/títulos das `.github/instructions` aplicáveis e para qual decisão cada uma será usada (ex.: mensageria, transações, erros HTTP, testes, observabilidade).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).
- Se `.github/instructions/` não existir ou não cobrir o tema, declare **lacuna** explicitamente (não invente políticas).

#### 2) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- `POST /clientes` e `PUT /clientes/{id}`: na mesma transação da persistência do cliente, registar evento no **Outbox**; publicar para mensageria (broker real **ou** simulação conforme evidência no código e nas instructions locais).
- **Consumidor:** ler da fila/tópico e atualizar o **read-model**; garantir **idempotência** demonstrável.
- **DLQ** (ou equivalente) após **N** tentativas falhadas, com **N** explícito no código.
- Preservar o CRUD existente; cache/`GET` e correlação conforme critérios de aceite.

#### 3) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 4) Implementação (patch)
- Aplique as mudanças no código (Outbox, publicação, consumidor, read-model, idempotência, DLQ, impacto em API/domínio/infraestrutura conforme padrões do repo e instructions aplicáveis).

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
- `ancoragem` (instruction_local | codigo_repo | inferencia)
- `evidencia` (id/arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

### 1. Uso das instructions locais
Avalie:
- evidências de uso efetivo das `.github/instructions`;
- quais decisões foram claramente apoiadas por instruções;
- onde as instructions agregaram valor real;
- onde poderiam ter sido melhor utilizadas;
- qual dependência de inferência permaneceu mesmo com instructions.

### 2. Qualidade técnica do plano
Avalie:
- estrutura do plano;
- clareza de camadas;
- coerência arquitetural;
- aderência a boas práticas sustentadas pelo contexto recuperado;
- sinais de genericidade ou overengineering.

### 3. Centralização de conhecimento
Analise:
- se as instructions locais reduzem ambiguidade em relação ao código sozinho;
- se o conhecimento parece reutilizável por outros contribuidores do repo;
- se há indícios de consistência na forma como o corpus local é aplicado;
- se a abordagem favorece governança do conteúdo em `.github/instructions/`.

### 4. Escalabilidade em múltiplos repositórios
Explique:
- até que ponto um corpus em `.github/instructions/` escala quando há muitos repositórios (duplicação vs drift);
- qual esforço de manutenção tende a existir;
- quais riscos operacionais permanecem;
- quais dependências de tooling precisam ser consideradas.

### 5. Experiência de uso
Avalie:
- fluidez;
- previsibilidade;
- interrupções no fluxo;
- dependência de prompt;
- impacto do uso de tools no comportamento do assistente.

## Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao contexto recuperado
- qualidade técnica
- completude
- consistência
- capacidade de centralização
- escalabilidade
- governança

## Conclusão final

Escolha apenas uma:

- “as `.github/instructions` são viáveis como guia principal neste tipo de implementação”
- “as instructions locais ajudam, mas precisam de complementos (código, reprompt ou corpus externo)”
- “as instructions locais não cobrem o suficiente para implementação confiável neste cenário”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como solução arquitetural, não apenas técnica.
- Considere cenário corporativo real.
