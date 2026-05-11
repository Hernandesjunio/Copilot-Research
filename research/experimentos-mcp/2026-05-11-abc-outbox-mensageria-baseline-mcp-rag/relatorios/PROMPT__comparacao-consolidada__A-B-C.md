## Prompt — Comparação consolidada (A vs B vs C) com notas 0–10

Você é um avaliador técnico imparcial. Sua tarefa é **comparar e consolidar** três execuções de um mesmo experimento (cenários **A**, **B**, **C**) com base **exclusivamente** nos relatórios fornecidos como entrada.

### Objetivo

Gerar uma **análise consolidada** comparando A/B/C, atribuindo **nota de 0 a 10 para cada cenário em cada critério**, com justificativas objetivas e evidências textuais citadas dos relatórios.

### Entradas (cole os 3 relatórios completos)

Cole integralmente, na ordem A, B, C, os conteúdos dos arquivos abaixo:

- A: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__baseline.md`
- B: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__mcp.md`
- C: `2026-05-11__abc-outbox-mensageria-baseline-mcp-rag__rag.md`

> Importante:
> - **Não use conhecimento externo** (do repositório, de docs, ou de padrões). Se algo não está nos relatórios, marque como “não evidenciado”.
> - Se houver **mais de uma execução** registrada para um mesmo cenário no mesmo arquivo (ex.: “execução abortada” e “execução bem-sucedida”), trate como **múltiplas tentativas**:
>   - Use como “resultado principal” a **tentativa mais completa e válida** (preferir: build/teste executado + critérios de aceite marcados).
>   - Ainda assim, registre o “sinal de risco” da tentativa abortada na seção **Riscos e ameaças à validade**.

### Restrições

- **Não implemente nada.** Só analisar os textos fornecidos.
- **Não invente** comandos, arquivos, tabelas, decisões ou resultados não descritos.
- Onde houver conflito entre relatórios, priorize:
  1) evidência objetiva (ex.: comandos executados, checks marcados), depois
  2) seção “FATO”, depois
  3) demais observações.

### Escala de notas (0–10)

Para cada critério, dê uma nota \(0–10\) por cenário:

- **0–2**: falha/ausência clara, ou execução abortada para aquele aspecto.
- **3–4**: evidência fraca, incompleto, ou muitos pontos “não verificados”.
- **5–6**: atende parcialmente, com lacunas relevantes.
- **7–8**: atende bem, pequenas lacunas/risco residual.
- **9–10**: atende muito bem, evidência forte e validação objetiva.

> Se um item for explicitamente “N/A” no relatório, isso **não** deve reduzir nota automaticamente; avalie se o “N/A” é justificado pela evidência (“não existe no repo”, “não foi requisito”, etc.).

### Critérios a comparar (fixos; não altere nomes)

Use exatamente estes critérios, sempre com **nota 0–10 para A, B, C**:

1) **Validade do experimento (higiene/isolamento)**  
2) **Aderência aos critérios de aceite (checklist Pass/Fail)**  
3) **Completude do vertical slice** (outbox + publicação + consumo + read-model + idempotência + DLQ)  
4) **Qualidade arquitetural** (separação de responsabilidades, clareza, acoplamento; baseado no que o relatório afirma)  
5) **Validação objetiva** (build/teste, evidências, passos de validação, cobertura do “como validar”)  
6) **Segurança e boas práticas de dados** (ex.: SQL parametrizado; apenas o que está evidenciado)  
7) **Operabilidade/Confiabilidade** (retry com N explícito, DLQ, idempotência; apenas o que está evidenciado)  
8) **Coerência com o contexto do repo** (ex.: broker real vs simulado “coerente com ausência de broker”, conforme o relatório)  
9) **Clareza do relatório** (estrutura, distinção FATO/HIPÓTESE/RISCO, rastreabilidade)  

### Procedimento (obrigatório)

1) Extraia de cada cenário A/B/C:
   - checklist de validade
   - resultados Pass/Fail
   - rubrica 0–2 (se existir)
   - comandos executados
   - principais fatos/hipóteses/riscos
2) Normalize termos:
   - trate “ProcessedMessage” vs “ProcessedEvent” como **mecanismo de idempotência** se o relatório o descrever assim
   - trate “OutboxDeadLetter / DeadLetterEvent” como **DLQ** se o relatório o descrever assim
3) Atribua notas 0–10 por critério e por cenário, com:
   - justificativa curta (1–3 bullets)
   - pelo menos **1 citação textual** (trecho copiado) por critério *quando houver evidência*; se não houver, declare “não evidenciado”.
4) Gere um ranking final (1º, 2º, 3º) com base em:
   - média simples das notas dos 9 critérios
   - e um parágrafo de “por que”, considerando também riscos/validade.

### Formato de saída (obrigatório)

Produza sua resposta exatamente no formato do arquivo “MODELO” abaixo (cole e preencha):

---8<--- INÍCIO DO MODELO ---8<---

## Análise consolidada — Comparação A vs B vs C

### Escopo e fontes

- **Slug**:
- **Data(s)**:
- **Fontes analisadas**:
  - A:
  - B:
  - C:
- **Observação sobre múltiplas tentativas** (se aplicável):

### Resumo executivo (máx. 10 linhas)

- 

### Notas por critério (0–10)

Para cada critério:
- **Definição** (1 frase)
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A: (bullets + 1 citação textual quando houver)
  - B:
  - C:

#### 1) Validade do experimento (higiene/isolamento)

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 2) Aderência aos critérios de aceite (checklist Pass/Fail)

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 3) Completude do vertical slice

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 4) Qualidade arquitetural

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 5) Validação objetiva

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 6) Segurança e boas práticas de dados

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 7) Operabilidade/Confiabilidade

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 8) Coerência com o contexto do repo

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

#### 9) Clareza do relatório

- **Definição**:
- **Notas**: A=?, B=?, C=?
- **Justificativas e evidências**:
  - A:
  - B:
  - C:

### Cálculo e ranking

- **Médias**:
  - A: ?
  - B: ?
  - C: ?
- **Ranking**: 1º=?, 2º=?, 3º=?
- **Racional do ranking** (1 parágrafo):

### Riscos e ameaças à validade (consolidados)

- 

### Recomendações (para o próximo ciclo de experimento)

- 

---8<--- FIM DO MODELO ---8<---

