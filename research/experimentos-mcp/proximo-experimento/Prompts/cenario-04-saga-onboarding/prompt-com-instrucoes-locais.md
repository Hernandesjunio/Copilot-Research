Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, centralização de conhecimento e comportamento do Copilot ao usar `.github/instructions`.

## Contexto do experimento

**Identificação:** Cenário 4 (Saga onboarding) — condição **B: Instructions locais**.

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

- **Idioma:** português. **Segurança:** não expor credenciais.
- **Fonte:** `.github/instructions/`. Declarar lacunas.
- **Sem MCP.** **BMAD** + citação de ficheiros locais.

## Tarefa

**Título:** Implementar saga (orquestração manual) para onboarding: criar cliente, criar formulário associado, enviar notificação — com compensações e timeout.

**Descrição:**

`POST` (ou rota equivalente) que executa:

1. Criar **cliente**.
2. Criar **formulário** associado (cliente HTTP mock, in-process ou fila, conforme projeto).
3. Enviar **notificação** (email simulado ou fila).

**Compensações** na ordem inversa em falhas; **idempotência** em passos e compensações.

**Requisitos:**

- Implementação **manual** (sem framework de saga obrigatório).
- Tabela **`OnboardingSagaState`** (ou equivalente).
- **Timeout** (ex.: 30s) e **retry** (ex.: 5s entre tentativas) explícitos.
- Mocks/configuração para serviços externos.

**Cenários:** happy path; falha etapa 2; falha etapa 3; retry; timeout.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | OK |
| Estado | Persistência de saga |
| Happy path | Fluxo completo |
| Compensações | Ordem reversa; consistência |
| Timeout | Abort + compensação |
| Retry | Verificável |
| Idempotência | Sem duplicação |
| Correlação | IDs de rastreio |

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
- Liste os `id`/títulos das `.github/instructions` aplicáveis e para qual decisão cada uma será usada (ex.: transações, mensageria, erros, testes, idempotência).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).
- Se `.github/instructions/` não existir ou não cobrir o tema, declare **lacuna** explicitamente.

#### 2) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- Fluxo onboarding em **3 passos** com **estado persistido**, **timeout**, **retry** e **compensações** idempotentes na ordem inversa.
- **Sem** framework de saga externo obrigatório; orquestração **manual** explícita.
- Mocks/configuração para integrações; **correlação**/IDs de rastreio.

#### 3) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 4) Implementação (patch)
- Aplique as mudanças no código conforme padrões do repo e instructions aplicáveis.

#### 5) Validação
- Execute/indique validações objetivas (por exemplo: `dotnet build`, testes quando aplicável).
- Relacione cada linha relevante da tabela de critérios de aceite a um passo de verificação ou comando, incluindo **cenários de falha** e timeout.
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
