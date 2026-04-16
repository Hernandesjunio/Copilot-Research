Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, centralização de conhecimento e comportamento do Copilot ao usar MCP STDIO.

## Contexto do experimento

Estou avaliando o comportamento do Copilot em um cenário com `.github/instructions`.

Neste teste, considere que:
- as `.github/instructions` são a principal fonte de guardrails/contexto adicional;
- não há MCP como mecanismo de recuperação de contexto;
- o objetivo não é apenas avaliar qualidade da resposta, mas verificar a viabilidade dessa abordagem como mecanismo de centralização e governança de conhecimento;
- o interesse está em observar se essa estratégia pode sustentar reutilização e consistência em ambientes com muitos repositórios.

Quero observar:
- se houve uso efetivo das tools;
- onde o MCP agregou valor real na construção da solução;
- se a abordagem se sustenta como fonte única de verdade em escala.

## Tarefa

Implemente (codifique) um novo endpoint para atualizar o cliente por completo e deixe a mudança validável.

Restrições:
- use evidências observáveis no código do workspace e nas `.github/instructions`;
- quando faltar informação, declare explicitamente a inferência;
- não assuma convenções não sustentadas por evidência acessível.

O trabalho deve considerar, quando aplicável:
- separação de camadas;
- contrato HTTP;
- impacto em API, domínio e infraestrutura;
- validação;
- tratamento de erros;
- resiliência e tolerância a falhas.

## Regras obrigatórias

1. Execute a tarefa considerando o MCP como mecanismo principal de contexto adicional.
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
- Liste os `id`/títulos das `.github/instructions` aplicáveis e para qual decisão cada uma será usada (ex.: status codes, validação, testes, catálogo de erros, observabilidade, resiliência).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).

#### 2) Ticket canônico (copiar no topo da resposta)
Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código/instructions; caso contrário, declarar lacuna e não inventar).
- Se houver base no código/instructions para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver base, marcar como fora de escopo.

#### 3) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 4) Implementação (patch)
- Aplique as mudanças no código (endpoint + validação + mapeamento de erros conforme padrões do repo).

#### 5) Validação
- Execute/indique validações objetivas (por exemplo: testes unitários/integração/contrato quando aplicável).
- Se não for possível executar, descreva o comando exato e o critério de sucesso.

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
- se o MCP reduz duplicação entre repositórios;
- se o conhecimento parece reutilizável;
- se há indícios de consistência transversal;
- se a abordagem favorece governança do corpus.

### 4. Escalabilidade em múltiplos repositórios
Explique:
- se o MCP se sustenta em aproximadamente 100+ repositórios;
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

- “MCP é viável como fonte única de verdade”
- “MCP ajuda, mas precisa de complementos”
- “MCP não resolve o problema de centralização”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Importante

- Seja crítico.
- Avalie como solução arquitetural, não apenas técnica.
- Considere cenário corporativo real.