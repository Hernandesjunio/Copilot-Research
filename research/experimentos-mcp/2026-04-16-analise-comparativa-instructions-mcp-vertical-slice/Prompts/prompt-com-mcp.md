Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, engenharia de contexto e escalabilidade em múltiplos repositórios.

## Contexto do experimento

Estou avaliando o comportamento do Copilot em um cenário com MCP `corporate-instructions`.

Objetivo do experimento:
- avaliar a qualidade da implementação produzida (plano + patch + validação);
- avaliar o quanto a solução depende de contexto local real;
- analisar a viabilidade dessa abordagem em um cenário com aproximadamente 100+ repositórios;
- identificar riscos de duplicação, drift, manutenção, inconsistência e acoplamento ao repositório.

Neste teste, considere que o contexto vem de:
- contexto recuperado via MCP `corporate-instructions` (tools/resources), como fonte principal de guardrails;
- instructions locais (quando existirem) e código disponível no workspace como evidência observável complementar.

## Tarefa

Implemente (codifique) um novo endpoint para atualizar o cliente por completo e deixe a mudança validável.

Restrições:
- use apenas evidências observáveis no código, nas instructions locais e no contexto recuperado via MCP;
- quando faltar informação, declare explicitamente a inferência;
- não assuma comportamento organizacional não evidenciado.

O trabalho deve considerar:
- separação de camadas;
- contrato HTTP;
- impacto em domínio, aplicação e infraestrutura;
- validação;
- tratamento de erros;
- resiliência e tolerância a falhas apenas se houver base contextual suficiente para recomendá-las.

## Saída esperada

### Parte 1 — Execução (obrigatório)

#### 1) Seleção de guardrails e evidências (antes de codar)
- Liste os `id` das instructions aplicáveis (MCP e/ou locais) e para qual decisão cada uma será usada (ex.: status codes, validação, testes, catálogo de erros, observabilidade, resiliência).
- Liste os ficheiros/módulos do workspace que ancoram a decisão (quando existirem).

#### 2) Ticket canônico (copiar no topo da resposta)
Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código/MCP; caso contrário, declarar lacuna e não inventar).
- Se houver base no código/MCP para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver base, marcar como fora de escopo.

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

### Parte 2 — Relatório técnico do experimento

#### 0. Métricas de execução (obrigatório)
Reporte, no mínimo, os itens abaixo (use N/A quando a plataforma não fornecer o dado):
- tempo total (wall-clock): `inicio_iso`, `fim_iso`, `duracao_ms`
- latência por etapa: exploração/leitura, raciocínio/decisão, escrita do plano, escrita do relatório (em ms)
- uso de tools: `qtd_tool_calls_total`, `qtd_por_tool`, `sucessos`, `falhas`, `retries`
- I/O de contexto: `qtd_arquivos_lidos`, `qtd_arquivos_citados`, `qtd_trechos_citados`, `bytes_aprox_lidos` (ou N/A)
- tokens: `tokens_input` e `tokens_output` (se disponível); senão `tokens_input_est` e `tokens_output_est` + método + margem de erro assumida
- custo: `custo_total` e `moeda` (ou N/A)
- tamanho do resultado: `caracteres_resposta` (ou N/A) e `qtd_itens_plano`
- contagens para rigor experimental: `qtd_afirmacoes_FATO`, `qtd_afirmacoes_HIPOTESE`, `qtd_afirmacoes_RISCO_DE_INTERPRETACAO`

Ao final do relatório, inclua obrigatoriamente um bloco único chamado `EXPERIMENT_METRICS_JSON` contendo exatamente os campos acima em JSON.

Inclua também obrigatoriamente um bloco único chamado `DECISIONS_JSON` (em JSON) com, no mínimo, uma lista de decisões-chave contendo:
- `decisao`
- `ancoragem` (MCP | instruction_local | codigo_repo | inferencia)
- `evidencia` (id/arquivo/trecho) ou N/A
- `risco` (baixo|medio|alto) e `como_validar`

## Exportação (obrigatório)

Crie (ou sobrescreva) um arquivo em:
`docs/experimentos-mcp/Resultados/YYYY-MM-DD__NOME-DO-EXPERIMENTO__mcp.md`

O conteúdo do arquivo deve conter:
- a Parte 1 (Execução)
- a Parte 2 (Relatório técnico do experimento)
- os blocos `EXPERIMENT_METRICS_JSON` e `DECISIONS_JSON`

Use `YYYY-MM-DD` como a data de hoje. Em `NOME-DO-EXPERIMENTO`, use um slug curto (kebab-case). O sufixo final do arquivo identifica o cenário do experimento (`mcp`).

#### 1. Evidência de uso de contexto
Para cada decisão importante da solução, classifique como:
- ancorada em instruction local;
- ancorada no código do repositório;
- inferida por conhecimento geral.

Aponte:
- quais decisões mostram uso efetivo das instructions locais;
- onde houve lacunas;
- onde o plano dependeu de inferência.

#### 2. Qualidade técnica do plano
Avalie:
- estruturação do plano (BMAD) e adequação do patch ao plano;
- clareza de camadas;
- coerência arquitetural;
- adequação ao nível de complexidade da tarefa;
- presença de excesso de genericidade ou overengineering.

#### 3. Limitações estruturais da abordagem
Analise criticamente:
- duplicação entre repositórios;
- risco de drift;
- dificuldade de evolução centralizada;
- acoplamento do conhecimento ao repositório.

#### 4. Escalabilidade em 100+ repositórios
Explique:
- se a abordagem se sustenta;
- em que condições ela deixa de se sustentar;
- qual esforço de manutenção ela tende a exigir;
- quais riscos operacionais são previsíveis.

#### 5. Experiência de uso
Avalie:
- fluidez;
- necessidade de reprompt;
- dependência de descoberta manual;
- previsibilidade do comportamento.

### Avaliação
Use nota de 0 a 2 para cada critério:
- 0 = fraco
- 1 = parcial
- 2 = forte

Critérios:
- aderência ao contexto local
- qualidade técnica
- completude
- consistência
- escalabilidade da abordagem
- facilidade de manutenção

### Conclusão final
Escolha uma das opções:
- “instructions locais são viáveis como fonte única de verdade”
- “instructions locais funcionam, mas não escalam bem”
- “instructions locais não são adequadas para centralização de conhecimento”

Depois da escolha, acrescente obrigatoriamente:
- a principal evidência que sustenta a conclusão;
- a principal limitação do próprio experimento.

## Regras obrigatórias
- Diferencie explicitamente FATO, HIPÓTESE e RISCO DE INTERPRETAÇÃO.
- Não trate inferência como evidência.
- Não produza resposta diplomática.
- Priorize análise crítica sobre descrição.
- Ao final, reporte métricas de execução. Se alguma métrica não puder ser obtida automaticamente, marque como N/A e explique o método de estimativa e o impacto na validade do experimento.
- Política de uso de tools: prefira “tool-first” para recuperar guardrails e padrões do repo antes de propor mudanças; se exceder o necessário, justifique no relatório (custo/benefício e o que foi obtido).