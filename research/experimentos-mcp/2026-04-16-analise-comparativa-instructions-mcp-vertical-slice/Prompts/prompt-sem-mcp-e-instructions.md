Quero que você atue como um avaliador técnico rigoroso com foco em arquitetura de soluções, qualidade de implementação e comportamento do Copilot na ausência de contexto estruturado.

## Contexto do experimento

Estou avaliando o comportamento do Copilot em um cenário sem contexto estruturado dedicado, sem uso de `copilot-instructions.md`, `.github/instructions` e `mcp corporate-instructions`.

Neste teste, considere que:
- não há `.github/instructions` como fonte confiável de orientação adicional;
- não há MCP como mecanismo de recuperação de contexto;
- o contexto disponível vem apenas do código visível no workspace e do conhecimento geral do modelo.

O objetivo do experimento não é apenas avaliar a qualidade da resposta, mas observar:
- quanto da solução depende de inferência;
- quais lacunas aparecem sem uma fonte estruturada de contexto;
- quão sustentável é esse modo de trabalho para implementação real.

## Tarefa

Implemente (codifique) um novo endpoint para atualizar o cliente por completo e deixe a mudança validável.

Restrições:
- use apenas evidências observáveis no código do workspace;
- quando faltar informação, declare explicitamente a inferência;
- não assuma convenções organizacionais não evidenciadas.

O trabalho deve considerar, quando aplicável:
- separação de camadas;
- contrato HTTP;
- impacto em API, domínio e infraestrutura;
- validação;
- tratamento de erros;
- resiliência e tolerância a falhas.

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

#### 1) Ticket canônico (copiar no topo da resposta)
Implemente o seguinte “vertical slice” (a mesma atividade será comparada em outros cenários):
- `PUT /clientes/{id}`: atualização total do cliente com persistência (repositório/DB) + validação + contrato de erros/status codes.
- `GET /clientes/{id}`: leitura com cache (se houver base no código; caso contrário, declarar lacuna e não inventar).
- Se houver evidência no código para integrações externas, incluir um exemplo de chamada HTTP com timeouts/resiliência; se não houver evidência, marcar como fora de escopo.

#### 2) Plano BMAD (obrigatório)
Use o formato:
- Background
- Mission
- Approach
- Delivery/validation

#### 3) Implementação (patch)
- Aplique as mudanças no código (endpoint + validação + mapeamento de erros conforme padrões do repo).

#### 4) Validação
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