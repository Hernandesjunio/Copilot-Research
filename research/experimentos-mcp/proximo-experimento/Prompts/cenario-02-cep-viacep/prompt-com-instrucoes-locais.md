Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, centralização de conhecimento e comportamento do Copilot ao usar `.github/instructions`.

## Contexto do experimento

**Identificação:** Cenário 2 (CEP / ViaCEP) — condição **B: Instructions locais**.

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
- **Fonte principal:** `.github/instructions/`. Se inexistente ou incompleta, declarar **lacuna**.
- **Não usar MCP** nesta condição.
- **BMAD** antes de codificar; citar ficheiros de instructions usados.

## Tarefa

**Título:** Implementar validação de CEP com integração resiliente ao ViaCEP (ou serviço equivalente).

**Descrição:**

Ao criar ou atualizar cliente com CEP:

1. Validar **formato** do CEP (8 dígitos, sem máscara ou normalizando entrada).
2. Consultar **ViaCEP** ou **mock** configurável em testes/dev para obter logradouro, bairro, cidade, estado.
3. Armazenar endereço completo ou estado de erro de validação de forma consistente com o modelo de dados atual.
4. Implementar **resiliência:**
   - Timeout por chamada (ex.: 3s).
   - **Retry** com backoff exponencial (ex.: 1s, 2s, 4s) para falhas transitórias.
   - **Circuit breaker:** após falhas consecutivas (ex.: 5), bloquear chamadas por um período (ex.: 30s).
   - **Fallback:** circuito aberto ou falha persistente → gravar cliente com validação de endereço pendente.
5. **Cache** do resultado de lookup por TTL (ex.: 24h ou configurável).
6. **Observabilidade:** latência, sucesso/falha, estado do circuit breaker.

**Restrições:**

- Não quebrar o CRUD existente.
- Evitar bloqueio desnecessário; manter padrão assíncrono do projeto se houver.
- Consistência entre chamada HTTP e persistência (definir na implementação).

**Cenários esperados:**

- CEP válido → endereço obtido e armazenado.
- Timeout + retry → sucesso quando possível.
- Serviço fora do ar → circuit breaker → fallback.
- Mesmo CEP duas vezes no intervalo de cache → segunda via cache.

## Critérios de aceite (objetivos)

| Critério | Verificação |
|----------|-------------|
| Build | `dotnet build` sem erros |
| HttpClient | Cliente HTTP com políticas de resiliência |
| Validação | Formato inválido → erro HTTP adequado |
| ViaCEP | CEP válido → endereço persistido |
| Timeout / retry | Comportamento sob simulação |
| Circuit breaker | Falhas repetidas → circuito aberto + fallback |
| Cache | Segunda consulta dentro do TTL sem HTTP |
| Correlation | Propagação de correlation id se o projeto usar |
| Health | Indicação no health check se aplicável |
| Erros externos | Mapeamento coerente (ex. não encontrado → 422) |

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
- Liste os `id`/títulos das `.github/instructions` aplicáveis e para qual decisão cada uma será usada (ex.: HttpClient/Polly, validação, cache, erros HTTP, observabilidade).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).
- Se `.github/instructions/` não existir ou não cobrir o tema, declare **lacuna** explicitamente.

#### 2) Cenário canónico (copiar no topo da resposta)
Implemente o seguinte vertical slice (a mesma atividade será comparada em outros cenários):
- Validação de CEP + lookup **ViaCEP** (ou mock) com **HttpClient** e políticas alinhadas ao projeto e às instructions.
- **Resiliência:** timeout, retry/backoff, circuit breaker, fallback para estado “pendente”.
- **Cache** por TTL; **observabilidade** (latência, falhas, estado do circuito).
- Mapeamento de erros da API externa para o contrato da API de clientes.

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
