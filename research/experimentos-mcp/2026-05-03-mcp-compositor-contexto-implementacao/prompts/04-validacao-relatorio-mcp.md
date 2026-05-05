# Prompt 04 — Validação final e relatório do experimento

## Modelo recomendado

`GPT 5.4`

Alternativo: `Gemini Pro 2.5`

## Objetivo da etapa

Consolidar a validação final, as métricas e a rastreabilidade da rodada.

## Instruções de uso

1. Abra uma nova thread.
2. Forneça como entrada:
   - o contexto composto;
   - o plano BMAD;
   - o resultado da implementação;
   - o diff ou resumo das alterações;
   - logs de build/testes, se existirem.
3. Cole o prompt abaixo integralmente.

## Prompt

```md
Quero um relatório técnico final do experimento "MCP como compositor de contexto" para o cenário de outbox/mensageria.

Use como base obrigatória:
- artefato de composição de contexto;
- plano BMAD;
- execução da implementação;
- validação disponível;
- diff ou resumo do patch.

Objetivo:
avaliar se o MCP foi usado como compositor de contexto de forma útil, rastreável e profissional.

Não quero comparação A/B/C.
Quero análise desta rodada única.

Sua saída deve conter exatamente estas seções:

# Parte 1 — Execução

## 1. Contexto composto utilizado
Resuma o que foi efetivamente usado do MCP, do repo e de inferência.

## 2. Plano aplicado
Resuma o BMAD executado.

## 3. Implementação realizada
Liste o que foi alterado e qual era o objetivo de cada bloco de mudança.

## 4. Validação
Mapeie cada critério de aceite para:
- comando executado;
- evidência observada;
- status (`OK`, `N/A`, `PENDENTE`).

# Parte 2 — Relatório do experimento

## 0. Diagnóstico principal
Explique se o MCP realmente compôs contexto útil antes do patch.

## 1. Uso do MCP como compositor de contexto
Avalie:
- contexto útil recuperado;
- ruído;
- lacunas;
- dependência de inferência remanescente.

## 2. Qualidade técnica do fluxo em fases
Avalie:
- separação entre contexto, decisão, implementação e validação;
- redução de sobrecarga do super prompt;
- clareza da rastreabilidade.

## 3. Qualidade da implementação
Avalie:
- aderência ao plano;
- coerência arquitetural;
- escopo mínimo;
- sinais de overengineering.

## 4. Limitações da rodada
Liste limitações metodológicas e técnicas.

## 5. Conclusão final
Escolha uma das opções:
- `MCP compôs contexto de forma útil e rastreável`
- `MCP ajudou, mas ainda deixou lacunas relevantes`
- `MCP ainda não compôs contexto de forma suficiente para este cenário`

Depois explique:
- principal evidência;
- principal limitação;
- recomendação para a próxima rodada.

## 6. Métricas
Inclua obrigatoriamente os blocos:
- `EXPERIMENT_METRICS_JSON`
- `DECISIONS_JSON`
- `CONTEXT_COMPOSITION_JSON`

Regras para os blocos:

### `EXPERIMENT_METRICS_JSON`
Deve incluir pelo menos:
- `inicio_iso`
- `fim_iso`
- `duracao_ms`
- `composicao_contexto_ms`
- `plano_bmad_ms`
- `implementacao_ms`
- `validacao_relatorio_ms`
- `qtd_tool_calls_total`
- `qtd_por_tool`
- `sucessos`
- `falhas`
- `retries`
- `search_confidence_avg`
- `zero_result_rate`
- `low_confidence_rate`
- `qtd_arquivos_lidos`
- `qtd_arquivos_citados`
- `qtd_trechos_citados`
- `qtd_itens_patch`
- `build_status`
- `tests_status`
- `qtd_criterios_aceite_ok`
- `qtd_criterios_aceite_na`
- `qtd_criterios_aceite_pendentes`
- `precisou_reprompt`
- `qtd_reprompts`
- `dev_precisou_citar_tool`
- `agente_pediu_confirmacao_por_lacuna_critica`
- `houve_overengineering`

### `DECISIONS_JSON`
Cada item deve conter:
- `decisao`
- `ancoragem`
- `evidencia`
- `risco`
- `como_validar`

### `CONTEXT_COMPOSITION_JSON`
Deve conter:
- `scenario`
- `context_mode`
- `models_used`
- `decisions_required`
- `ids_selected`
- `ids_used_in_final_decisions`
- `repo_evidence_items`
- `critical_gaps`
- `decisions_from_mcp`
- `decisions_from_repo`
- `decisions_from_inference`

Restrições:
- responder em português;
- ser crítico e direto;
- marcar `N/A` quando não houver dado confiável;
- não tratar inferência como evidência.
```

## Saída esperada

Salvar o resultado final em:

`resultados/YYYY-MM-DD__cenario-01-outbox__mcp-context-composer.md`
