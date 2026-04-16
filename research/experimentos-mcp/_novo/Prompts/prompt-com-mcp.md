Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, engenharia de contexto e escalabilidade em múltiplos repositórios.

## Contexto do experimento

Estou avaliando o uso []

Objetivo do experimento:
- avaliar a qualidade do planejamento técnico produzido;
- avaliar o quanto esse planejamento depende de contexto local real;
- analisar a viabilidade dessa abordagem em um cenário com aproximadamente 100+ repositórios;
- identificar riscos de duplicação, drift, manutenção, inconsistência e acoplamento ao repositório.

Neste teste, considere que o contexto vem exclusivamente das instructions locais e do código disponível no workspace.

## Tarefa

Faça um planejamento de implementação de um novo endpoint para atualizar o cliente por completo.

Restrições:
- use apenas evidências observáveis no c��digo e nas instructions locais;
- quando faltar informação, declare explicitamente a inferência;
- não assuma comportamento organizacional não evidenciado.

O planejamento deve considerar:
- separação de camadas;
- contrato HTTP;
- impacto em domínio, aplicação e infraestrutura;
- validação;
- tratamento de erros;
- resiliência e tolerância a falhas apenas se houver base contextual suficiente para recomendá-las.

## Saída esperada

### Parte 1 — Planejamento técnico
Apresente o plano de implementação normalmente.

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

#### 1. Evidência de uso de contexto
Para cada decisão importante do plano, classifique como:
- ancorada em instruction local;
- ancorada no código do repositório;
- inferida por conhecimento geral.

Aponte:
- quais decisões mostram uso efetivo das instructions locais;
- onde houve lacunas;
- onde o plano dependeu de inferência.

#### 2. Qualidade técnica do plano
Avalie:
- estruturação do plano;
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