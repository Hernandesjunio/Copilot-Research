# Plano de melhoria do MCP sem embeddings/BM25

## 1. Objetivo

Definir um plano detalhado para melhorar o comportamento do MCP atual usando apenas:

- heuristicas deterministicas
- ajustes de contrato das tools
- governanca de metadados
- orquestracao de chamadas

Sem introduzir:

- embeddings
- BM25
- reranker externo
- LLM auxiliar no servidor

O alvo e reduzir o gap percebido frente ao uso de instructions locais, principalmente em:

- qualidade do contexto entregue ao agente
- consistencia de decisoes
- completude tecnica do output
- estabilidade operacional (menos retries/falhas)

---

## 2. Escopo e premissas

## 2.1 Escopo funcional

Servidor: `mcp-instructions-server/corporate_instructions_mcp/`

Tools existentes:

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch`

## 2.2 O que nao sera feito

- busca vetorial
- index invertido BM25
- tuning com modelo externo
- pipeline de embedding offline/online

## 2.3 Principio de projeto

Melhorar primeiro o que ja existe e ja e calculado internamente (score breakdown, sinais de confianca, metadados de corpus), antes de adicionar novas estruturas complexas.

---

## 3. Diagnostico tecnico resumido

O MCP atual ja possui base solida:

- indexacao segura de markdown com frontmatter
- busca lexical com expansao de sinonimos
- score por titulo/tags/corpo/prioridade
- telemetria robusta de execucao e busca

Ponto central de melhoria:

- varios sinais de qualidade ja existem no servidor, mas ficam concentrados em telemetria; o agente recebe pouco desses sinais no payload das tools.

Consequencia:

- o agente nao sabe quando o resultado de busca esta fraco/ambiguo
- o fluxo nao orienta fallback automatico
- mais idas e voltas para montar contexto util

---

## 4. Metas de resultado

## 4.1 Metas de qualidade do retrieval

- aumentar acerto do top-1 em consultas de referencia
- aumentar acerto acumulado em top-3/top-5
- reduzir resultados "apenas por expansao de sinonimo"

## 4.2 Metas operacionais

- reduzir retries por sessao
- reduzir taxa de resultados vazios
- reduzir taxa de baixa confianca

## 4.3 Metas de consumo pelo agente

- entregar contexto mais acionavel por chamada
- reduzir necessidade de multiplos batches para a mesma tarefa
- tornar a selecao explicavel e auditavel

---

## 5. Backlog completo de melhorias sem embeddings/BM25

Cada item abaixo pode ser implementado com codigo Python e ajustes de contrato MCP.

## M1 - Diagnosticos opcionais na resposta de busca

### Descricao

Adicionar parametro opcional em `search_instructions`, por exemplo `include_diagnostics`.

Quando ligado, retornar campos como:

- `search_confidence`
- `top_score_gap_1_2`
- `top3_scores`
- `matched_user_terms`
- `matched_expansion_only_terms`
- `results_only_from_expansion_count`
- `results_only_from_expansion_no_user_term_overlap_count`

### Justificativa tecnica

Esses sinais ja sao calculados internamente; expor para o cliente melhora decisao de fallback sem custo estrutural alto.

### Impacto esperado

- melhora de aderencia contextual
- menos uso cego de top-1

---

## M2 - Filtros por metadado (kind/scope/priority)

### Descricao

Adicionar filtros opcionais em `search_instructions`:

- `kind`
- `scope`
- `priority`
- opcionalmente `workspace_evidence_required`

### Justificativa tecnica

Campos ja existem no indice e no frontmatter.

### Impacto esperado

- mais precisao no recorte de documentos
- menos ruidao em corpus grandes

---

## M3 - Modo de filtro de tags (any/all)

### Descricao

Ampliar filtro de tags com:

- `tags_mode=any` (comportamento atual)
- `tags_mode=all` (todas as tags informadas devem casar)

### Justificativa tecnica

Sem BM25, aumentar seletividade por tag e uma forma barata de elevar precisao.

### Impacto esperado

- reducao de falso positivo em consultas multi-dominio

---

## M4 - Suporte a frases exatas

### Descricao

Permitir query com termos entre aspas:

- `"outbox transacional"`
- `"problem details"`

Aplicar bonus de score para match exato da frase no titulo/corpo.

### Justificativa tecnica

Frase exata ajuda muito em dominios com termo composto.

### Impacto esperado

- melhora de top-1 em consultas especificas

---

## M5 - Bonus por proximidade de termos

### Descricao

Adicionar heuristica de proximidade:

- bonus quando termos da query aparecem proximos na mesma janela de texto

### Justificativa tecnica

Aumenta qualidade semantica da busca sem embeddings.

### Impacto esperado

- ranking mais coerente em texto longo

---

## M6 - Boost de match exato por identificador/titulo

### Descricao

Bonus forte quando query casa com:

- `id` do documento
- slug de path
- titulo quase exato

### Justificativa tecnica

Acelera descoberta precisa em casos onde usuario conhece o documento.

### Impacto esperado

- menos chamadas intermediarias

---

## M7 - Normalizacao lexical mais robusta

### Descricao

Refinar tokenizacao/normalizacao:

- acentos em toda a cadeia
- hifen/underscore
- termos com versao
- stopwords minimas de baixo impacto

### Justificativa tecnica

Melhora recall sem custo de infraestrutura.

### Impacto esperado

- menos falso negativo por variacao textual

---

## M8 - Evolucao controlada do dicionario de sinonimos

### Descricao

Expandir clusters de sinonimos por dominio (mensageria, seguranca, api, observabilidade).

Incluir governanca:

- arquivo dedicado
- testes de regressao por cluster
- changelog de alteracoes

### Justificativa tecnica

Dicionario e o principal vetor de recall sem embeddings.

### Impacto esperado

- melhor cobertura de termos de negocio e stack

---

## M9 - Penalidade para score derivado so de expansao

### Descricao

Se resultado foi dominado por termos expandidos (sem match do termo original), aplicar penalidade leve.

### Justificativa tecnica

Evita top-1 artificial causado por expansao agressiva.

### Impacto esperado

- maior confiabilidade do primeiro resultado

---

## M10 - Campo explicavel de "porque casou"

### Descricao

Incluir em cada resultado:

- razoes de score (titulo/tags/corpo/prioridade/sinonimos)
- termos que de fato contribuiram

### Justificativa tecnica

Fortalece auditabilidade e explicabilidade de decisoes.

### Impacto esperado

- melhor uso do MCP para relatorios e justificativa tecnica

---

## M11 - Related IDs com score composto

### Descricao

Evoluir `_related_instruction_ids` para usar:

- overlap de tags
- compatibilidade de kind
- prioridade
- similaridade textual leve

### Justificativa tecnica

Descoberta lateral mais util para contexto completo.

### Impacto esperado

- melhora de completude por navegacao assistida

---

## M12 - Batch orientado a secoes

### Descricao

Adicionar parametros opcionais em `get_instructions_batch`:

- `section_contains`
- `include_headings`
- `headings_only`

### Justificativa tecnica

Reduz truncagem cega e entrega conteudo mais util por byte.

### Impacto esperado

- menos chamadas repetidas para extrair parte relevante

---

## M13 - Truncagem por bloco markdown

### Descricao

Em vez de cortar por char bruto, cortar por blocos de heading e manter secao integra.

### Justificativa tecnica

Mantem coerencia textual e reduz perda de contexto semantico.

### Impacto esperado

- melhor qualidade do conteudo retornado no batch

---

## M14 - Limites configuraveis por ambiente

### Descricao

Tornar configuravel por env:

- teto total de chars
- limite por instrucao
- limites de resultados default/cap

### Justificativa tecnica

Facilita tuning por ambiente sem patch de codigo.

### Impacto esperado

- melhor adaptacao a diferentes host clients

---

## M15 - Rebuild automatico por staleness do corpus

### Descricao

Detectar alteracoes no corpus mesmo com `INSTRUCTIONS_ROOT` igual:

- hash de mtimes
- contador de arquivos
- timestamp da ultima varredura

### Justificativa tecnica

Evita indice stale em sessoes longas.

### Impacto esperado

- maior consistencia entre corpus e resposta MCP

---

## M16 - Tool composta de resolucao de contexto

### Descricao

Nova tool sem LLM, por exemplo `resolve_instruction_context`:

- executa busca
- seleciona top-N com heuristica
- retorna contexto consolidado para consumo imediato

### Justificativa tecnica

Reduz friccao entre `search` e `batch`.

### Impacto esperado

- menos tool calls para chegar em contexto acionavel

---

## M17 - Tool de checklist normativa por cenario

### Descricao

Entrada por tema/cenario e saida de checklist com ids de suporte.

Exemplos:

- `mensageria_outbox`
- `api_http_contract`
- `security_baseline`

### Justificativa tecnica

Melhora completude tecnica sem necessidade de semantic retrieval.

### Impacto esperado

- menos lacunas de implementacao

---

## M18 - Tool de conflitos e precedencia

### Descricao

Nova tool para:

- detectar possivel conflito entre instrucoes selecionadas
- explicar precedencia por `priority/scope/kind`

### Justificativa tecnica

Reduz risco de recomendacao inconsistente.

### Impacto esperado

- maior consistencia das decisoes

---

## M19 - Erros acionaveis no contrato das tools

### Descricao

Padronizar erros com:

- `error_code`
- `message`
- `details`
- `suggested_next_call`

### Justificativa tecnica

Melhora resiliencia da orquestracao do agente.

### Impacto esperado

- queda de retries causados por uso incorreto

---

## M20 - Fallback automatico orientado por sinais

### Descricao

Quando baixa confianca:

- ampliar `max_results`
- sugerir filtro de tags/kind
- recomendar batch dos top resultados

### Justificativa tecnica

Usa sinal interno para autocorrecao sem modelo externo.

### Impacto esperado

- maior taxa de convergencia por sessao

---

## M21 - Benchmark offline de relevancia

### Descricao

Suite de queries de referencia com expected ids para medir:

- MRR
- Precision@1
- Precision@3
- Precision@5

### Justificativa tecnica

Sem benchmark, melhoria vira percepcao subjetiva.

### Impacto esperado

- evolucao orientada por metrica

---

## M22 - Painel de qualidade por release

### Descricao

Consolidar telemetria para acompanhar:

- zero result rate
- low confidence rate
- retry rate
- tool failure rate

### Justificativa tecnica

Transforma telemetria em governanca de qualidade.

### Impacto esperado

- deteccao precoce de regressao

---

## M23 - Template de contexto consolidado

### Descricao

Padronizar `composed_context` em blocos:

- regras obrigatorias
- recomendacoes
- riscos comuns
- lacunas detectadas

### Justificativa tecnica

Ajuda o agente a aplicar guidance de forma mais consistente.

### Impacto esperado

- melhora de qualidade tecnica percebida no output final

---

## M24 - Evidencia de versao do corpus na resposta

### Descricao

Destacar no payload:

- `content_sha256`
- snapshot/revisao do corpus

### Justificativa tecnica

Facilita rastreabilidade de decisao tecnica.

### Impacto esperado

- melhor auditabilidade e reproducibilidade

---

## 6. Roadmap em fases (priorizacao)

## Fase 0 - Baseline de medicao (pre-requisito)

Itens:

- M21 (suite offline minima)
- consolidacao de metricas atuais com telemetria (base para comparacao)

Entregavel:

- relatorio baseline com metricas pre-melhoria

Risco:

- baixo

---

## Fase 1 - Quick wins de alto impacto

Itens:

- M1
- M2
- M3
- M10
- M14
- M19

Objetivo:

- melhorar precisao e robustez sem alterar arquitetura

Indicadores de sucesso:

- reducao de retries
- reducao de chamadas com resultado fraco nao tratado

---

## Fase 2 - Qualidade de ranking heuristico

Itens:

- M4
- M5
- M6
- M7
- M8
- M9
- M11

Objetivo:

- aumentar relevancia real do top-N em consultas ambiguas

Indicadores de sucesso:

- aumento de MRR
- aumento de P@1/P@3

---

## Fase 3 - Qualidade de contexto retornado

Itens:

- M12
- M13
- M23
- M24

Objetivo:

- entregar contexto mais util por chamada

Indicadores de sucesso:

- menor numero medio de batches por tarefa
- menor truncagem inutil

---

## Fase 4 - Orquestracao orientada a tarefa

Itens:

- M15
- M16
- M17
- M18
- M20

Objetivo:

- reduzir dependencia de engenharia manual no cliente

Indicadores de sucesso:

- menos tool calls para completar tarefa
- mais consistencia entre sessoes

---

## Fase 5 - Operacao continua

Itens:

- M22
- revisoes trimestrais do dicionario (M8)
- revisao de thresholds de fallback (M20)

Objetivo:

- evitar regressao apos evolucoes

---

## 7. Plano de execucao tecnico por modulo

## 7.1 Arquivos alvo principais

- `corporate_instructions_mcp/server.py`
- `corporate_instructions_mcp/indexing.py`
- `corporate_instructions_mcp/telemetry.py`

Arquivos novos sugeridos:

- `corporate_instructions_mcp/search_contract.py` (shapes de resposta/diagnostico)
- `corporate_instructions_mcp/context_resolver.py` (M16, M17, M18)
- `corporate_instructions_mcp/config.py` (M14)

## 7.2 Testes a adicionar/ajustar

- `tests/smoke_test.py`
- `tests/integration_mcp_stdio_test.py`
- novos testes unitarios de score e filtros
- suite offline de benchmark (M21)

## 7.3 Ordem recomendada de codificacao

1. M14 (config) para preparar base configuravel
2. M1/M2/M3/M19 (contrato e robustez)
3. M7/M8/M9 (lexico/sinonimos)
4. M4/M5/M6/M11 (ranking)
5. M12/M13/M23 (qualidade do conteudo)
6. M15/M16/M17/M18/M20 (orquestracao)
7. M22 (painel continuo)

---

## 8. Matriz de prioridade (valor x esforco)

## Alto valor / baixo esforco (fazer primeiro)

- M1
- M2
- M3
- M10
- M14
- M19

## Alto valor / medio esforco

- M7
- M8
- M9
- M12
- M13
- M20

## Alto valor / alto esforco

- M16
- M17
- M18
- M22

## Valor medio / baixo esforco

- M24
- parte de M11 (versao simplificada)

---

## 9. Criterios de aceite por fase

## Fase 1 aceita se

- testes existentes continuam verdes
- novos campos de diagnostico funcionam sem quebrar compatibilidade
- filtros por metadado aplicam corretamente
- erros retornam formato padrao

## Fase 2 aceita se

- benchmark mostra melhora estatica em P@1/P@3 ou MRR
- sem regressao relevante em latencia

## Fase 3 aceita se

- queda no numero medio de chamadas de batch por tarefa
- melhora de utilidade do contexto em avaliacao manual

## Fase 4 aceita se

- tool composta resolve casos de uso ponta-a-ponta com menos chamadas
- conflitos/preferencias aparecem de forma explicita

## Fase 5 aceita se

- dashboard operacional acompanha regressao por release

---

## 10. Riscos e mitigacoes

## R1 - Excesso de heuristica e comportamento imprevisivel

Mitigacao:

- tunar por benchmark controlado (M21)
- ajustar thresholds com dados de telemetria

## R2 - Quebra de contrato consumido por clientes

Mitigacao:

- manter novos campos opcionais
- preservar estrutura atual por default

## R3 - Aumento de latencia na busca

Mitigacao:

- medir custo por etapa
- limitar calculos caros a top-K parcial

## R4 - Drift de sinonimos por expansao sem governanca

Mitigacao:

- revisao periodica do dicionario
- testes dedicados por cluster

## R5 - Overfitting ao fixture de testes

Mitigacao:

- incluir queries reais de cenarios experimentais
- comparar em ao menos dois corpus distintos

---

## 11. Definicao de pronto (DoD)

Uma melhoria so e considerada concluida quando:

- codigo implementado
- testes unitarios e de integracao passando
- documentacao da tool atualizada
- changelog atualizado
- metrica de qualidade comparada contra baseline

---

## 12. Resultado esperado

Com esse plano, o MCP evolui de "catalogo de instrucoes" para "fornecedor de contexto tecnico orientado por tarefa", sem depender de tecnologias vetoriais.

O ganho principal esperado para aproximar ou igualar instructions locais nao vem de "mais IA", e sim de:

- melhor contrato de busca
- melhor explicabilidade
- melhor selecao heuristica
- melhor ergonomia operacional

Esse conjunto tende a reduzir variabilidade, melhorar aderencia tecnica e aumentar confianca nas respostas produzidas com apoio do MCP.

