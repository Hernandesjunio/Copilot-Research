Quero que voce atue como um avaliador tecnico senior de experimentos com MCP, com foco em rastreabilidade, metricas operacionais e qualidade de evidencia.

## Objetivo

Sua tarefa nao e reimplementar a solucao.

Sua tarefa e **extrair, normalizar e julgar** as metricas da rodada de execucao de SAGA para responder:

**o MCP `corporate-instructions` ajudou materialmente nesta rodada, ou o resultado dependeu mais de prompt e inferencia do que de contexto normativo util?**

## Fontes permitidas

Use apenas o que for fornecido nesta rodada:

- o artefato da execucao principal;
- telemetry NDJSON do MCP, se existir;
- quality report gerado a partir da telemetry, se existir;
- diff, logs, transcript ou chat export, se existirem;
- arquivos do repo que forem citados como evidencia pelo artefato principal.

Se faltar evidencia para alguma metrica ou julgamento, escreva explicitamente:

- `N/A`
- `sem evidencia suficiente`

## Regras obrigatorias

1. Nao reavalie o problema "do zero"; avalie a rodada como experimento.
2. Priorize metrica observavel sobre opiniao.
3. Diferencie:
   - metrica observada diretamente;
   - metrica derivada;
   - metrica estimada.
4. Se houver telemetry do MCP, ela e a fonte principal para uso de tools e qualidade de busca.
5. Se nao houver telemetry, marque os campos ausentes como `N/A` e explique o impacto metodologico.
6. Nao premie o experimento apenas por ter muito texto ou muito patch.
7. A nota deve refletir se o MCP ajudou a reduzir inferencia e melhorar decisao, nao apenas se a IA escreveu codigo plausivel.
8. Exporte o resultado para:
   `research/experimentos-mcp/2026-05-03-saga-real-fixtures-mcp/resultados/YYYY-MM-DD__saga-real-fixtures-mcp__parecer.md`

## Como usar telemetry, se existir

Se voce receber um arquivo NDJSON de telemetry do MCP, consolide-o com:

```bash
python "mcp-instructions-server/scripts/build_quality_report.py" --input "CAMINHO/telemetry.ndjson" --output "CAMINHO/quality-report.json"
```

Use do quality report, quando disponivel:

- `summary.total_completed_calls`
- `summary.search_completed_calls`
- `counts.tool_failures`
- `counts.retries_total`
- `rates.tool_failure_rate`
- `rates.retry_rate`
- `rates.zero_result_rate`
- `rates.low_confidence_rate`
- `search_quality.avg_search_confidence`
- `tool_breakdown`
- `warnings`

## Tarefa

Leia o artefato principal da execucao e consolide:

1. se o cenario escolhido era realmente ancorado no repo;
2. se o MCP foi usado para restringir e melhorar decisoes;
3. se houve reconciliacao correta quando o corpus exigia `workspace_evidence_required`;
4. se o plano BMAD foi forte ou apenas formal;
5. se a validacao sustentou de fato as conclusoes;
6. se as metricas coletadas permitem dizer que o MCP ajudou.

## Saida obrigatoria

Use exatamente esta estrutura.

# 1. Resumo Executivo

# 2. Julgamento Geral da Rodada

# 3. Analise por Eixo
## 3.1 Escolha do cenario real
## 3.2 Uso do MCP e evidence gate
## 3.3 Qualidade do plano BMAD
## 3.4 Qualidade da validacao
## 3.5 Valor real do MCP para a rodada

# 4. Pontuacao por Criterio

Apresente uma tabela:

| Criterio | Nota | Justificativa |
|---|---:|---|

Criterios obrigatorios:

1. aderencia ao contexto recuperado (MCP + repo)
2. qualidade tecnica do plano
3. completude da execucao
4. consistencia entre guardrails, plano e patch
5. qualidade da validacao e das metricas
6. capacidade do experimento de provar valor do MCP

Escala:

- 0 = fraco
- 1 = parcial
- 2 = forte

# 5. Riscos e Limitacoes

# 6. Veredito Final

Escolha apenas uma:

- `MCP corporate-instructions foi suficiente para ancorar guardrails neste tipo de implementacao`
- `MCP ajudou parcialmente, mas ainda foi necessaria inferencia significativa`
- `MCP nao foi adequado para reduzir inferencia ou guiar a implementacao de forma confiavel`

Depois acrescente:

- principal evidencia a favor do veredito;
- principal limitacao metodologica da rodada.

# 7. EXPERIMENT_METRICS_JSON

Inclua um bloco JSON com pelo menos:

```json
{
  "inicio_iso": "N/A",
  "fim_iso": "N/A",
  "duracao_ms": "N/A",
  "latencia_exploracao_leitura_ms": "N/A",
  "latencia_raciocinio_decisao_ms": "N/A",
  "latencia_escrita_patch_ms": "N/A",
  "latencia_validacao_ms": "N/A",
  "latencia_escrita_relatorio_ms": "N/A",
  "qtd_tool_calls_total": "N/A",
  "qtd_por_tool": {},
  "sucessos": "N/A",
  "falhas": "N/A",
  "retries": "N/A",
  "search_completed_calls": "N/A",
  "tool_failure_rate": "N/A",
  "retry_rate": "N/A",
  "zero_result_rate": "N/A",
  "low_confidence_rate": "N/A",
  "avg_search_confidence": "N/A",
  "qtd_arquivos_lidos": "N/A",
  "qtd_arquivos_citados": "N/A",
  "qtd_trechos_citados": "N/A",
  "bytes_aprox_lidos": "N/A",
  "tokens_input": "N/A",
  "tokens_output": "N/A",
  "tokens_input_est": "N/A",
  "tokens_output_est": "N/A",
  "tokens_metodo_estimativa": "N/A",
  "tokens_margem_erro_assumida": "N/A",
  "custo_total": "N/A",
  "moeda": "N/A",
  "caracteres_resposta": "N/A",
  "qtd_itens_patch": "N/A",
  "qtd_afirmacoes_FATO": "N/A",
  "qtd_afirmacoes_HIPOTESE": "N/A",
  "qtd_afirmacoes_RISCO_DE_INTERPRETACAO": "N/A",
  "metricas_observadas_diretamente": [],
  "metricas_derivadas": [],
  "metricas_estimadas": [],
  "warnings": []
}
```

# 8. DECISIONS_JSON

Inclua um bloco JSON com uma lista de decisoes relevantes, no minimo:

```json
{
  "decisoes": [
    {
      "decisao": "N/A",
      "ancoragem": "MCP|instruction_local|codigo_repo|inferencia",
      "evidencia": "N/A",
      "risco": "baixo|medio|alto",
      "como_validar": "N/A"
    }
  ]
}
```

# 9. EVIDENCE_MATRIX_JSON

Inclua um bloco JSON com matriz de evidencia por achado, no minimo:

```json
{
  "achados": [
    {
      "claim": "N/A",
      "evidence_source": "artefato|telemetry|quality-report|repo|transcript",
      "evidence_excerpt": "N/A",
      "confidence": "low|medium|high",
      "gap_type": "context|execution|validation|metrics|method"
    }
  ]
}
```

## Regra final de julgamento

So conclua que o MCP ajudou materialmente se houver evidencia de pelo menos quatro pontos ao mesmo tempo:

1. guardrails relevantes vieram do MCP e foram realmente usados;
2. o MCP restringiu invencao de stack ou contrato;
3. a escolha do cenario ou da abordagem ficou melhor por causa dessa composicao de contexto;
4. a validacao final sustenta o ganho e nao apenas uma narrativa bem escrita.

Se um ou mais desses pontos falharem, reduza a confianca do veredito.
