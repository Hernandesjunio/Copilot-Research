# Auditoria técnica — overfitting na recuperação de contexto do MCP (épicos 06 a 09)

## 0. Diagnóstico principal

**Conclusão direta:** o sistema melhorou parcialmente, mas a evidência disponível aponta mais para **tuning incremental orientado ao corpus atual e à suite de 24 casos** do que para uma evolução robusta da arquitetura de recuperação.

O padrão observado ao longo dos épicos é recorrente:

- identifica-se um fail específico da suite;
- introduz-se uma regra, lista, sinônimo ou filtro focal;
- os testes focais passam;
- o placar agregado sobe pouco (`7/24 -> 8/24 -> 8/24 -> 9/24`);
- persistem erros de bundle, supporting IDs ausentes e seleção enviesada em queries naturais.

Isso é compatível com **overfitting de ranking ao fixture e à suite atual**.

## 1. Escopo auditado

Materiais analisados:

- `planning/bmad/epicos/EPIC-06-agent-real-usage-gap-analysis-and-redesign-plan.md`
- `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
- `planning/bmad/epicos/EPIC-08-stopwords-pt-first-pass-and-rebaseline.md`
- `planning/bmad/epicos/EPIC-09-i04-observability-readiness-cross-domain-coverage.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__execucao-real-e-analise-epic-07.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__rebaseline-epic-08-i01-stopwords.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__epic-09-i02__analise-falhas-e-correcao-targeted.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__epic-09-i04__observability-readiness-cross-domain-coverage.md`
- `mcp-instructions-server/corporate_instructions_mcp/indexing.py`
- `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`
- `mcp-instructions-server/corporate_instructions_mcp/server.py`
- `mcp-instructions-server/corporate_instructions_mcp/config.py`
- `mcp-instructions-server/corporate_instructions_mcp/search_contract.py`
- `mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`
- `mcp-instructions-server/tests/test_epic07_search_ranking.py`
- `mcp-instructions-server/tests/test_epic09_i02_meta_governance.py`
- `mcp-instructions-server/tests/test_epic09_i04_cross_domain_coverage.py`
- `mcp-instructions-server/tests/smoke_test.py`
- `mcp-instructions-server/tests/integration_mcp_stdio_test.py`
- `mcp-instructions-server/tests/benchmark/queries.yaml`
- `fixtures/instructions/`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`

## 2. Tarefa 1 — Linha do tempo dos épicos

| Epic | Problema atacado | Alteração feita | Resultado medido | Risco de overfitting |
|---|---|---|---|---|
| EPIC-06 | Gap entre testes verdes e uso real por agente; pipeline não refletia bem o consumo real | Análise de contrato/orquestração; sem mudança de ranking | Diagnóstico qualitativo; sem melhoria quantitativa de ranking | **Baixo** no ranking; **alto** como alerta de viés de avaliação |
| EPIC-07 | Baixa precisão de ranking, stopwords PT ausentes, meta-governance contaminando buscas, lacunas de sinônimos e hipótese de divergência no corpus | Roadmap de correções `I-01` a `I-07`; fail-first tests; invariantes de corpus | Baselines documentados: `5/24` e depois `7/24`; alvo `>= 21/24` não alcançado | **Alto** |
| EPIC-08 | Isolar `I-01` para validar se stopwords PT eram causa-raiz dominante | Ampliação mínima de `STOPWORDS`; teste focal em `test_epic07_search_ranking.py` | `pytest`: `146 passed, 1 skipped`; suite: `7/24 -> 8/24` | **Médio** |
| EPIC-09 I-02 | Meta/governance aparecendo em queries técnicas | Heurísticas em `context_resolver.py` para detectar query técnica vs meta e despromover docs meta | Testes focais: `3 failed -> 3 passed`; suite ficou em `8/24` | **Alto** |
| EPIC-09 I-04 | Cobertura semântica fraca entre observabilidade/readiness/SQL/erros/auth | Novas pontes em `synonyms.yaml` e `DEFAULT_SYNONYMS`; testes focais dedicados | Testes focais: `6 failed -> 6 passed`; suite: `8/24 -> 9/24` | **Crítico** |

### Leitura crítica da evolução

1. O único ganho agregado claro foi de `7/24 -> 9/24` após várias intervenções.
2. Os ganhos locais vieram principalmente de ajustes focais em stopwords, classificação meta e sinônimos.
3. Não há evidência de uma troca estrutural do mecanismo de ranking; o núcleo segue heurístico e artesanal.
4. O sistema parece estar sendo ajustado para **fazer casos conhecidos passarem**, não para generalizar sob mudança de corpus ou reformulação de query.

## 3. Tarefa 2 — Regras hardcoded e sinais de overfitting

| Local | Regra encontrada | Evidência | Por que pode ser overfitting | Severidade |
|---|---|---|---|---|
| `indexing.py` | `STOPWORDS` PT/EN manual | Set fixo em código, com tokens como `como`, `deve`, `ser`, `validar` | A filtragem depende de vocabulário previamente observado; não se adapta a novas formulações | Média |
| `indexing.py` | `DEFAULT_SYNONYMS` manual | Clusters manuais como `observabilidade`, `transacao`, `segredos`, `problemdetails`, `claims` | O recall depende de termos previstos manualmente; em domínio novo, tende a quebrar | Alta |
| `indexing.py` | Comentários explicitamente ligados a casos da suite | Comentários `T06/T08`, `T20/T21`, `T16/T18` dentro do dicionário de sinônimos | Sinal explícito de tuning por teste e não por teoria geral de recuperação | **Crítica** |
| `indexing.py` | `_DNS_QUERY_SIGNAL_TERMS` e regra especial para `dns` | `dns`, `resolver`, `nameserver`, `lookup`, `ttl`; multiplicador `0.6` fora de queries DNS | Defesa específica de um subdomínio/documento do corpus | Alta |
| `indexing.py` | Pesos fixos do scoring | Título `3x/4x`, tags `2x/3x`, phrase bonus `2.5/1.5`, proximidade `window=80`, expansão `0.5` | Pesos sem calibração estatística; ajustados manualmente | Alta |
| `server.py` | Boost por ID/título | `+5` para ID exato, `+4` para título exato, `+2` se ID aparece na query | Reforça dependência do naming atual do corpus | Média |
| `context_resolver.py` | Classificação manual de meta-governance | `_META_GOVERNANCE_TAG_HINTS`, `_META_QUERY_HINTS`, `_TECHNICAL_QUERY_HINTS` | Resolve os docs meta atuais, mas não generaliza para novos docs híbridos ou novos domínios | Alta |
| `context_resolver.py` | Diversidade por tema | `_THEME_QUERY_HINTS`, `_THEME_TAG_HINTS`, `_THEME_MIN_STRENGTH = 2` | Temas são pré-definidos (`architecture`, `observability`, `integration`) | Alta |
| `context_resolver.py` | Promoção de `policy` e `reference` no bundle | `ensure_normative_policy`, `ensure_supporting_reference` | Tipo documental pode vencer intenção real da query | Alta |
| `config.py` + `search_contract.py` | Thresholds mágicos | `0.2`, `0.65`, `1.5`, `0.85`, `gap/5.0` | Não há justificativa estatística nem curva de calibração | Alta |
| `search_contract.py` | Fallback suggestions prontas | Sugestões de tags como `mensageria,resiliencia,security,api` | O fallback já nasce enviesado pelo corpus atual | Média |

### Observação importante

As regras acima não são só “determinísticas”; muitas delas são **corpus-shaped**. O problema não é haver heurística; o problema é haver **heurística focal demais**, construída ao redor dos documentos e queries já conhecidos.

## 4. Tarefa 3 — Acoplamento entre testes e implementação

| Teste | O que valida | Sinal de acoplamento | Risco | Como melhorar |
|---|---|---|---|---|
| `test_epic07_search_ranking.py` | Top-3/top-5 e presença de IDs concretos em queries do fixture | Asserts por IDs específicos e ranking parcial rígido | Alto | Medir também `MRR`, `Recall@k`, `nDCG` e robustez a variações de query |
| `test_epic09_i02_meta_governance.py` | Meta docs não podem bater docs técnicos | Conhece explicitamente os docs meta do corpus atual | Alto | Testar categoria “meta” por label/corpus sintético, não por IDs fixos |
| `test_epic09_i04_cross_domain_coverage.py` | Cobertura cross-domain em bundles específicos | Cada teste vira um par `query -> documento esperado` do fixture | **Crítico** | Introduzir múltiplas reformulações por intenção e avaliar ganho agregado |
| `test_corpus_invariant_filename_slug_matches_frontmatter_id` | Integridade slug/ID de todo o corpus | Congela convenção do fixture inteiro | Médio | Manter como teste de corpus, mas separar de qualidade de ranking |
| `smoke_test.py` | Sanidade do pipeline, shape da resposta, casos conhecidos como DNS | Usa IDs do fixture como expectativa básica | Médio | Manter como smoke, não usar como evidência de qualidade de ranking |
| `integration_mcp_stdio_test.py` | Fluxo stdio fim a fim | Também depende de IDs conhecidos do fixture | Médio | Manter como integração, mas não como benchmark de relevância |
| `tests/benchmark/queries.yaml` | Benchmark pequeno por `expected_id` | Só 4 queries; benchmark muito estreito | Alto | Criar benchmark com dezenas de queries por intenção, incluindo parafrases |
| Suite de 24 casos | `primary_ids`, `supporting_ids` e `nao priorizar` | Critério altamente específico ao corpus e ao bundle esperado | **Crítico** | Separar relevância principal, supporting opcional e penalidade por off-topic |

### Diagnóstico de acoplamento

Os testes atuais validam bem “**este corpus deve responder assim para estas perguntas**”, mas validam mal “**o motor de recuperação generaliza**”. Isso é suficiente para regressão local; não é suficiente para provar qualidade de IR.

## 5. Tarefa 4 — Avaliação do scoring atual

| Componente | Como funciona hoje | Fragilidade | Sinal de corpus-specific tuning |
|---|---|---|---|
| Extração de tokens | `tokenize_query()` normaliza diacríticos, separadores, variantes de versão e remove ruído por regras fixas | Não usa DF/IDF nem aprende do corpus | Stopwords foram ampliadas após falhas observadas na suite |
| Stopwords | Lista fixa PT/EN em `STOPWORDS` | Query natural fora desse vocabulário continua ruidosa | `EPIC-08` mostra tuning incremental por token |
| Sinônimos | `expand_query_with_metadata()` expande com peso `1.0` para termo do usuário e `0.5` para expansão; cap `5` por token | Expansão pode contaminar domínios adjacentes | Comentários em `indexing.py` e `synonyms.yaml` apontam T06/T08/T16/T18/T20/T21 |
| Body score | `weight * (1 + min(5, 0.25 * count))` | Soma lexical artesanal; favorece repetição de termos | Ajustes de stopwords e sinônimos tentam corrigir sintomas do body score |
| Title score | Multiplicadores fixos (`3x/4x`) | Peso alto demais pode favorecer títulos genéricos | Depende do estilo de naming dos documentos atuais |
| Tags score | Multiplicadores fixos (`2x/3x`) | Tagging do corpus vira parte crítica do ranking | Se novos docs forem menos bem tagueados, o motor piora |
| Phrase bonus | `+2.5` em título, `+1.5` no corpo | Valores arbitrários | Nenhuma evidência de calibração fora do fixture |
| Proximidade | `_proximity_bonus(window=80)` | Janela fixa; não considera estrutura do documento | Outro threshold não calibrado |
| Prioridade | `0.5 * PRIORITY_RANK` | Pode empurrar policy irrelevante acima de reference mais aderente | Meta docs e policies amplas se beneficiam disso |
| Regra especial DNS | Penalização/boost específicos para docs com tag `dns` | Regra local para um subdomínio/documento | Evidência forte de correção orientada a caso |
| Pós-seleção em `build_resolved_context()` | Escolhe âncora, garante policy, garante supporting reference, aplica theme diversity, preenche pool | Mistura intenção da query com tipo documental | Mesmo se a busca estiver razoável, o bundle final pode ficar enviesado |
| Meta-governance demotion | Despromove docs meta em queries técnicas; recoloca como fallback | Resolve um problema local, mas segue manual | Altamente dependente do corpus atual |

### Evidência operacional observada

Em execução local do ranking atual:

- query de arquitetura (`"me mostre como o projeto deve ser estruturado"`) ainda trouxe `microservice-opentelemetry-correlation-and-health` no topo do `search_instructions`;
- query de HttpClientFactory ainda trouxe `instruction-authoring-standard` no top-7;
- query de RabbitMQ ainda trouxe `assistant-workflow-bmad-planning-and-controlled-inference` no bundle final como fallback meta;
- query SQL segura elevou `microservice-configuration-production-readiness`, mas ela ainda ficou fora do corte padrão de `selected_ids=7`.

Isso mostra que o sistema está **compensando sintomas** sem estabilizar o comportamento global.

## 6. Tarefa 5 — Comparação com BM25

| Problema atual | BM25 ajudaria? | Por quê | Limitação |
|---|---|---|---|
| Peso lexical artesanal e sensível a tuning manual | Sim | BM25 lida melhor com frequência e raridade sem multiplicadores ad hoc por ocorrência | Ainda precisa de boa tokenização e indexação por campos |
| Dependência de muitos pesos fixos | Sim | Substitui parte grande do scoring manual | Não resolve sozinho bundle final e supporting docs |
| Generalização para corpus novo | Sim | IDF se ajusta ao corpus | Não resolve sinonimia forte ou mudança total de domínio |
| Queries longas em português natural | Parcialmente | Em geral comporta-se melhor que soma linear de hits | Ainda sofre quando não há sobreposição lexical suficiente |
| Dependência de sinônimos fixos | Parcialmente | Reduz a necessidade de várias pontes manuais | Não elimina aliases realmente necessários |
| Ranking por `title`, `tags`, `body` | Sim | BM25 por campo com pesos é abordagem clássica e sólida | Precisa de desenho explícito de fields |
| Supporting docs errados | Parcialmente | Um baseline lexical mais forte reduz ruído antes da montagem do bundle | Ainda exige rerank/selection policy |
| Robustez a crescimento do corpus | Sim | BM25 costuma degradar melhor que scoring artesanal quando o corpus cresce | Continua lexical; semântica ainda pode faltar |

### Avaliação objetiva

**BM25 resolveria boa parte do problema atual de scoring artesanal.**  
Não resolveria:

- distinção fina entre intenção técnica vs meta/governance;
- bundle final com supporting docs corretos;
- parafrases sem vocabulário compartilhado;
- ambiguidade semântica forte.

### Recomendação sobre campos

Se BM25 for adotado, o ideal é indexar separadamente:

- `title`
- `tags`
- `body`
- `kind`
- `scope` (como campo auxiliar / filtro, não como núcleo do score)

### Como medir se BM25 é melhor

Métricas mínimas:

- `MRR`
- `Recall@k`
- `nDCG@k`
- `Precision@1/3/5`
- taxa de off-topic no top-3
- taxa de supporting correto no top-k
- estabilidade sob reformulação de query
- estabilidade sob corpus perturbado (adição de novos documentos)

Sem isso, trocar heurística por BM25 pode apenas produzir **novo tipo de overfitting**.

## 7. Tarefa 6 — Comparação com FAISS / embeddings

| Problema atual | FAISS ajudaria? | Por quê | Risco |
|---|---|---|---|
| Reformulações de query | Sim | Embeddings capturam proximidade semântica além do token exato | Pode recuperar docs semanticamente parecidos, mas operacionalmente errados |
| Dependência de sinônimos manuais | Sim | Parte das pontes artificiais pode sair do dicionário manual | Sem controle, recall sobe junto com falso positivo |
| Domínio novo / vocabulário novo | Sim | Melhor adaptação sem depender de lista fixa de termos | Qualidade depende muito do modelo de embedding |
| Meta/governance vs técnico | Parcialmente | Pode ajudar, mas também pode aproximar docs processuais de docs técnicos | Exige filtro ou rerank por metadado/intent |
| Supporting docs semânticos | Sim | Pode encontrar documentos adjacentes não lexicalmente explícitos | Sem rerank, supporting errado pode contaminar bundle |
| Determinismo do MCP | Parcialmente | A busca vetorial pode ser determinística com índice fixo | Mudança de modelo/índice altera ranking; requer versionamento |
| Medição de qualidade | Sim | Recall semântico fica mais mensurável | Se medir só a suite atual, o viés continua |

### Resposta direta

- **FAISS reduziria dependência de sinônimos fixos?** Sim, parcialmente.
- **FAISS melhoraria queries semânticas?** Sim.
- **FAISS sozinho resolveria o problema atual?** Não.

### Risco principal

O maior risco é trazer documento “semanticamente próximo” e “operacionalmente inadequado”. Exemplo típico:

- documento meta/governance semanticamente próximo de “padrão” e “workflow”;
- documento técnico adjacente, mas não o correto para implementar ou justificar decisão.

Por isso, um desenho com embeddings precisaria de:

- rerank lexical ou híbrido;
- filtros por `kind`, `scope`, `tags`;
- separação explícita entre documentos técnicos e meta/governance;
- versionamento de embeddings por corpus/modelo.

## 8. Tarefa 7 — Arquitetura alternativa candidata

## Arquitetura candidata

### Estratégia 1 — BM25-first

**Ideia:** substituir o scoring artesanal atual por um baseline lexical forte e simples.

Componentes:

- indexação por campos (`title`, `tags`, `body`);
- BM25 por campo com pesos explícitos;
- filtros estruturados por `kind`, `scope`, `workspace_evidence_required`;
- seleção final mais simples, evitando promotion heuristics por tipo documental quando não houver sinal suficiente.

Vantagens:

- reduz quantidade de heurística manual;
- generaliza melhor com corpus novo;
- facilita tuning mensurável;
- mantém determinismo operacional alto.

Limitações:

- não resolve parafrases profundas;
- continua dependente de vocabulário lexical.

### Estratégia 2 — Hybrid BM25 + FAISS

**Ideia:** usar BM25 como baseline e embeddings como camada de recall semântico.

Fluxo:

1. BM25 recupera candidatos lexicais fortes.
2. FAISS recupera candidatos semanticamente próximos.
3. União dos candidatos.
4. Rerank determinístico com:
   - score lexical;
   - similaridade vetorial;
   - filtros por `kind`, `scope`, `tags`;
   - penalidade explícita para docs meta em intent técnico.

Vantagens:

- melhora recall em reformulações;
- reduz necessidade de dicionário manual gigante;
- tende a lidar melhor com corpus crescente.

Limitações:

- mais complexo;
- exige versionamento de embeddings e índice;
- precisa de rerank e avaliação séria para não introduzir novo ruído.

### Estratégia 3 — Current heuristic + BM25 shadow mode

**Ideia:** manter o sistema atual em produção de forma temporária e rodar BM25 em modo sombra.

Objetivo:

- comparar resultados sem trocar imediatamente o contrato MCP;
- medir divergência entre heurístico atual e baseline BM25;
- criar evidência antes de migrar.

Métricas recomendadas em shadow mode:

- concordância top-1 / top-3;
- `MRR`, `Recall@k`, `nDCG`;
- off-topic rate;
- supporting coverage rate;
- taxa de mudança sob novas queries e novos documentos.

Vantagens:

- risco operacional baixo;
- produz dados de comparação;
- evita refactor às cegas.

Limitações:

- não corrige o problema no curto prazo;
- exige disciplina de observabilidade e benchmark.

### Recomendação

**Recomendação principal:** seguir para **BM25-first** e colocar o sistema atual em **shadow mode** durante a transição.

Motivos:

1. O problema dominante hoje está no **scoring artesanal e no excesso de heurísticas locais**.
2. BM25 ataca diretamente esse núcleo com menor complexidade que embeddings.
3. Embeddings fazem mais sentido **depois** que houver um baseline lexical forte, estável e mensurável.
4. O sistema atual já mostrou sinais claros de tuning orientado a casos específicos; insistir na mesma linha tende a ampliar o overfitting.

## 9. Recomendação de avaliação futura

Antes de qualquer nova rodada de tuning:

1. separar testes de contrato (`smoke`, `stdio`, shape da tool) de testes de ranking;
2. criar golden set por **intenção**, não só por documento;
3. adicionar múltiplas reformulações por caso;
4. introduzir holdout queries que não sejam usadas no tuning;
5. medir comportamento após inserir novos documentos no corpus;
6. explicitar um conjunto de documentos meta/governance e técnicos para testes de separação de intenção.

## 10. Veredito final

**Melhoria real houve, mas foi pequena e local.**  
**O sistema atual ainda está mais próximo de “heurística para passar na suite atual” do que de “arquitetura robusta de recuperação”.**

Os sinais mais fortes são:

- sinônimos adicionados com referência explícita a casos da suite;
- demotion de meta/governance baseada em listas fixas do corpus atual;
- thresholds e boosts sem justificativa estatística;
- testes fortemente acoplados a IDs e bundles do fixture;
- placar agregado muito baixo mesmo após várias correções focais.

Em termos práticos:

- o ranking atual **não parece confiável o suficiente** para generalizar bem quando:
  - o corpus crescer;
  - o corpus mudar;
  - o domínio mudar;
  - a formulação das queries variar;
  - surgirem documentos semanticamente próximos, mas com metadados diferentes.

**Síntese final:** hoje o MCP está melhor ajustado ao corpus e à suite atuais, mas ainda não demonstrou evolução suficiente para ser considerado um mecanismo de recuperação generalista e robusto.
