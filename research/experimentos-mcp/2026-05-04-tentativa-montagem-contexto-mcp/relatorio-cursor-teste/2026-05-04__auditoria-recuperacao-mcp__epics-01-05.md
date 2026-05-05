# Auditoria técnica — recuperação de contexto do MCP (épicos 01 a 05)

## 0. Diagnóstico principal

**Conclusão direta:** os épicos 01 a 05 concentraram os **ganhos mais legítimos e estruturalmente defensáveis** da evolução do MCP. O sistema ficou melhor principalmente porque passou a ter:

- corpus com contrato explícito;
- indexação lexical mais séria;
- separação de campos e metadados úteis;
- leitura em batch e composição de contexto;
- melhor contrato de tools;
- maior explicabilidade e observabilidade do ranking.

Ao mesmo tempo, os **sinais iniciais de acoplamento ao corpus já estavam presentes** ao final desse período, sobretudo a partir do momento em que:

- sinônimos manuais cresceram;
- boosts fixos se acumularam;
- o resolvedor passou a selecionar `policy` e `reference` por regra;
- o sistema começou a “opinar” sobre o bundle final, não apenas recuperar candidatos.

**Leitura crítica:** o ganho dominante dos épicos 01 a 05 foi de **estrutura**, não de tuning fino.  
O problema é que o próprio EPIC-04/05 já plantou a base do que, nos épicos 06–09, virou **heurística focal e corpus-shaped tuning**.

---

## 1. Escopo auditado

Materiais analisados:

- `planning/bmad/epicos/EPIC-01-inventory-governance.md`
- `planning/bmad/epicos/EPIC-02-mcp-server.md`
- `planning/bmad/epicos/EPIC-03-rollout-playbook.md`
- `planning/bmad/epicos/EPIC-04-experiments-protocol.md`
- `planning/bmad/epicos/EPIC-05-normative-evidence-gate-and-compliance-matrix.md`
- `planning/bmad/epicos/EPIC-06-agent-real-usage-gap-analysis-and-redesign-plan.md`
- `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
- `planning/bmad/epicos/EPIC-08-stopwords-pt-first-pass-and-rebaseline.md`
- `planning/bmad/epicos/EPIC-09-i04-observability-readiness-cross-domain-coverage.md`
- `mcp-instructions-server/corporate_instructions_mcp/indexing.py`
- `mcp-instructions-server/corporate_instructions_mcp/context_resolver.py`
- `mcp-instructions-server/corporate_instructions_mcp/server.py`
- `mcp-instructions-server/corporate_instructions_mcp/config.py`
- `mcp-instructions-server/corporate_instructions_mcp/search_contract.py`
- `mcp-instructions-server/corporate_instructions_mcp/synonyms.yaml`
- `mcp-instructions-server/tests/smoke_test.py`
- `mcp-instructions-server/tests/integration_mcp_stdio_test.py`
- `mcp-instructions-server/tests/test_indexing.py`
- `mcp-instructions-server/tests/test_context_triggers.py`
- `mcp-instructions-server/tests/test_epic05_tools.py`
- `mcp-instructions-server/tests/benchmark/test_relevance_benchmark.py`
- `mcp-instructions-server/tests/benchmark/queries.yaml`
- `fixtures/instructions/`
- `research/experimentos-mcp/2026-04-05-mcp-corporate-instructions-avaliacao-tools/2026-04-05-mcp-corporate-instructions-avaliacao-tools.md`
- `research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-1.md`
- `research/experimentos-mcp/2026-04-16-analise-comparativa-instructions-mcp-vertical-slice/analise-comparativa-iteracao-2.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/orquestrador/testes-basicos-montagem-contexto-mcp.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__global-antigo-vs-local-atual-cenarios-2-3-4.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__local-atual-vs-iteracao-2.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-02__comparativo-smoke-mcp-stdio__local-atual-iteracao-2-vs-iteracao-3.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__execucao-real-e-analise-epic-07.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__suite-montagem-contexto-mcp__rebaseline-epic-08-i01-stopwords.md`
- `research/experimentos-mcp/2026-05-04-tentativa-montagem-contexto-mcp/relatorio-cursor-teste/2026-05-04__auditoria-overfitting-recuperacao-mcp__epics-06-09.md`

---

## 2. Tarefa 1 — Linha do tempo dos épicos 1 a 5

| Epic | Problema atacado | Tipo de solução | Resultado obtido | Tipo de ganho |
|---|---|---|---|---|
| EPIC-01 | Corpus sem governança e sem schema estável | Frontmatter obrigatório, IDs estáveis, distinção `policy` vs `reference`, regra nativo > MCP | Não melhora ranking sozinho, mas cria a infraestrutura semântica correta para IR | **estrutural** |
| EPIC-02 | Não havia MCP útil nem pipeline de discovery/search/read | Servidor stdio read-only, índice em memória, ranking heurístico básico, `list/search/get` e contrato MCP inicial | Grande salto de utilidade prática; base real para recuperação | **estrutural** |
| EPIC-03 | Problema de rollout e escalabilidade multi-repo | Playbook de distribuição, fronteira central vs local, template thin | Ganho operacional e de governança, quase nenhum ganho direto de ranking | **estrutural** |
| EPIC-04 | Faltava experimento reproduzível e endurecimento do produto | Benchmark mínimo, smoke/comparativos, `by_tag`, `related_ids`, batch, sinônimos, telemetria | MCP v2 fecha gap de aderência no vertical slice e melhora consumo do contexto | **misto: estrutural + heurístico** |
| EPIC-05 | Faltava evidence gate e camada de contexto mais acionável | `validate_applicability`, `build_compliance_matrix`, `resolve_instruction_context`, checklist, conflitos | Grande ganho de orquestração e usabilidade; ranking puro melhora pouco e fica mais mediado por heurísticas de montagem | **misto: estrutural + heurístico** |

### Leitura crítica da trajetória

1. **EPIC-01 e EPIC-02** são claramente a base correta. Sem eles não existe motor de recuperação de verdade.
2. **EPIC-03** é importante para escala, mas não para qualidade de ranking.
3. **EPIC-04** é o ponto onde o sistema melhora muito de forma legítima, mas já começa a misturar estrutura com tuning.
4. **EPIC-05** melhora o produto para consumo por agente, porém já desloca parte do valor do ranking bruto para a montagem heurística do bundle.

---

## 3. Tarefa 2 — Mudanças estruturais reais

| Mudança | Onde ocorreu | Por que é estrutural | Generaliza para outro corpus? |
|---|---|---|---|
| Frontmatter com `id`, `title`, `tags`, `scope`, `priority`, `kind` | EPIC-01; parsing em `indexing.py` | Transforma markdown solto em corpus recuperável por campos | **Sim** |
| Separação entre instrução nativa sempre ativa e corpus MCP on-demand | EPIC-01 / EPIC-03 | Resolve corretamente o papel do MCP como camada de recuperação, não como substituto de política local | **Sim** |
| Índice em memória com IDs estáveis, hash e rebuild controlado | `indexing.py`, `server.py` | Dá consistência operacional e reprodutibilidade ao mecanismo de busca | **Sim** |
| Busca lexical com campos `title`/`tags`/`body` | `indexing.py` | É um baseline lexical correto; muito melhor do que tratar tudo como blob indiferenciado | **Sim** |
| Endurecimento de segurança e parsing do corpus | `paths.py`, `indexing.py`, `server.py` | Reduz ruído de ingestão e melhora confiança no índice | **Sim** |
| `get_instructions_batch` e leitura em lote | `server.py` | Separa descoberta de leitura completa, reduz round-trips e melhora consumo do recall | **Sim** |
| Foco por seção e headings no batch | `markdown_sections.py`, `server.py` | Aproxima a recuperação de contexto útil sem exigir documento inteiro | **Sim** |
| Telemetria, score breakdown e benchmark mínimo | `telemetry.py`, `test_relevance_benchmark.py`, relatórios | Não melhora ranking sozinho, mas cria ciclo sério de medição | **Sim** |
| Separação formal entre aplicabilidade e conformidade | `applicability.py`, `server.py` | Boa arquitetura para corpus normativo; evita alucinação normativa direta | **Sim**, especialmente em corpus de policy |

### Decisão importante

As mudanças acima são as que **realmente valem preservar**. Elas melhoram o sistema por arquitetura, não porque “ajudam este fixture”.

---

## 4. Tarefa 3 — Sinais iniciais de overfitting

| Local | Regra encontrada | Evidência | Sinal de overfitting | Severidade |
|---|---|---|---|---|
| `indexing.py` | Sinônimos manuais por domínio | `SYNONYMS`/`DEFAULT_SYNONYMS` com clusters específicos | Recall depende de vocabulário previsto manualmente | Média |
| `indexing.py` | Pesos fixos por campo | multiplicadores de `title`, `tags`, `body`, `priority` | Score depende do estilo de naming/tagging do corpus atual | Média |
| `server.py` | Boost por ID/título exato | bônus `+5`, `+4`, `+2` no ranking | Naming do corpus passa a influenciar demais a busca | Alta |
| `context_resolver.py` | Seleção forçada de `policy` | `ensure_normative_policy` | O bundle passa a refletir tipologia documental, não só relevância da query | Alta |
| `context_resolver.py` | Seleção forçada de `reference` de apoio | `ensure_supporting_reference` | Supporting pode entrar por regra, não por score real | Alta |
| `context_resolver.py` | Theme diversity por lista fixa | `_THEME_QUERY_HINTS`, `_THEME_TAG_HINTS`, `_THEME_MIN_STRENGTH` | O sistema assume temas “esperados” em vez de inferir do corpus | Alta |
| `benchmark/queries.yaml` | Benchmark muito estreito | 4 queries com `expected_id` único | Boa regressão local, péssima evidência de generalização | Alta |
| `smoke_test.py` / `integration_mcp_stdio_test.py` | Asserts por IDs concretos | DNS, SQL e outros IDs de fixture | Testa contrato do fixture, não motor geral de IR | Média |

### Julgamento

Nos épicos 1–5 o overfitting ainda **não domina** o sistema.  
Mas ele **já nasce** na forma de:

- dicionário manual de sinônimos;
- pesos fixos não calibrados;
- heurísticas de montagem do bundle;
- testes fortemente ancorados no fixture.

---

## 5. Tarefa 4 — Evolução do scoring

| Epic | Mudança no scoring | Benefício | Risco |
|---|---|---|---|
| EPIC-02 | Keyword overlap básico em `title`, `tags`, `body`, com `priority` | Simples, barato, explicável | Sem noção de raridade, stopwords pobres, muito sensível a tokens frequentes |
| EPIC-03 | Sem mudança material de scoring | Nenhum risco novo | Nenhum ganho novo |
| EPIC-04 | Expansão com sinônimos e melhor descoberta lateral (`related_ids`) | Melhora recall e aderência temática | Sinônimos manuais começam a moldar o comportamento ao corpus |
| EPIC-04 | Aumento de `max_results`, batch e leitura cruzada | Melhora consumo do resultado, não apenas ranking bruto | Pode mascarar fragilidade do score base |
| EPIC-04/05 | Normalização melhor, frase exata, proximidade, expansão penalizada | Sistema lexical fica mais robusto para queries naturais e técnicas | Acúmulo de thresholds e bônus arbitrários |
| EPIC-05 | Pós-seleção em `build_resolved_context()` | Bundle final fica mais acionável | O sistema compensa ranking fraco com seleção opinativa |

### Explicação crítica

O scoring evoluiu em duas fases:

1. **fase boa**: sair de busca tosca para um baseline lexical realmente utilizável;
2. **fase perigosa**: começar a resolver no pós-processamento problemas que deveriam ser tratados por um ranking de base melhor.

O sistema fica mais robusto quando melhora:

- normalização;
- tokenização;
- leitura por campos;
- batch;
- observabilidade do score.

O sistema fica mais frágil quando começa a depender de:

- boosts fixos;
- sinônimos crescentes;
- composição opinativa do contexto.

---

## 6. Tarefa 5 — Qualidade dos testes

| Teste | Tipo | Generalização | Sinal de acoplamento | Observação |
|---|---|---|---|---|
| `test_paths.py` | Unitário estrutural | Alta | Baixo | Ótimo teste: protege invariantes reais |
| `test_indexing.py` (partes estruturais) | Unitário estrutural | Alta | Baixo | Bom para garantir parsing, tokenização, duplicidade, limites |
| `smoke_test.py` | Smoke/contrato | Baixa | Médio | Bom para sanidade; ruim para provar qualidade de IR |
| `integration_mcp_stdio_test.py` | Integração real | Média para protocolo, baixa para ranking | Médio | Muito útil para validar stdio, pouco conclusivo sobre generalização |
| `test_relevance_benchmark.py` | Benchmark de ranking | Baixa | Alta | Métricas corretas, conjunto insuficiente |
| `queries.yaml` | Golden set mínimo | Baixa | Alta | Pouquíssimas queries; quase um sanity benchmark |
| `test_context_triggers.py` | Contrato/orquestração | Média-baixa | Médio | Payloads limpos demais; pouco parecidos com agente real |
| `test_epic05_tools.py` | Aceitação semântica controlada | Média | Médio | Bom para estados oficiais; limitado para ruído real de evidência |

### Veredito sobre os testes

Os testes dos épicos 1–5 são **melhores como proteção de contrato e estrutura do produto** do que como prova de generalização do motor de recuperação.

Em especial:

- bons para evitar regressão mecânica;
- insuficientes para demonstrar robustez de ranking em corpus e formulações diferentes.

---

## 7. Tarefa 6 — Comparação com épicos 6 a 9

| Aspecto | Épicos 1–5 | Épicos 6–9 | Impacto |
|---|---|---|---|
| Filosofia predominante | Construção do produto MCP | Correção de falhas da suite e uso real | Mudança de arquitetura para tuning |
| Tipo de ganho | Corpus, indexação, contrato, batch, observabilidade | Stopwords, demotion meta, sinônimos focais, cobertura dirigida | Menor generalidade nos 6–9 |
| Papel do resolvedor | Composição útil do contexto | Composição cada vez mais prescritiva | Bundle passa a compensar ranking |
| Relação com a suite | Evidência e observação | Driver dominante de intervenção | Maior risco de otimizar para casos conhecidos |
| Heurísticas corpus-shaped | Presentes, mas ainda contidas | Crescentes e explícitas | Fragilidade aumenta muito |
| Natureza do score | Heurístico, porém ainda próximo de baseline lexical | Heurístico artesanal com patches sucessivos | Distanciamento de um motor IR limpo |

### Síntese comparativa

Os épicos 1–5 são majoritariamente **estruturais**.  
Os épicos 6–9 são majoritariamente **corretivos e heurísticos**.

Essa mudança de filosofia explica por que:

- os primeiros ganhos parecem maiores;
- os ganhos posteriores parecem menores e menos confiáveis;
- o sistema nos 6–9 fica mais parecido com “ajuste para passar casos” do que com evolução de IR.

---

## 8. Tarefa 7 — Decisões que devem ser preservadas

| Decisão | Por que é correta | Risco se remover |
|---|---|---|
| Frontmatter forte e estável | Sem schema consistente não há corpus pesquisável sério | Volta a busca opaca e sem governança |
| Separação entre contexto nativo e contexto MCP | Resolve corretamente o que deve ser sempre ativo vs consultado sob demanda | Ou satura contexto, ou empurra tudo para busca |
| Indexação por campos | Baseline correto para IR lexical | Perda de precisão e explicabilidade |
| Batch com leitura focada por seção | Separa descoberta de leitura integral | Mais ruído no contexto final |
| Telemetria e breakdown de score | Permite tuning com evidência | Tuning volta a ser intuitivo e arbitrário |
| Rebuild controlado e corpus versionado | Dá reprodutibilidade operacional | Mais drift e debugging difícil |
| Separar aplicabilidade de conformidade | Excelente defesa contra alucinação normativa | O agente volta a afirmar demais com pouca evidência |

---

## 9. Tarefa 8 — Decisões que devem ser evitadas

| Decisão | Problema potencial | Evidência | Recomendação |
|---|---|---|---|
| Expandir sinônimos manuais como motor principal | O sistema passa a memorizar o fixture | `SYNONYMS`/`DEFAULT_SYNONYMS` já crescem bastante no período | Tratar sinônimos como exceção governada, não como eixo da busca |
| Usar boosts por ID e título como atalho | Naming do corpus interfere demais na busca | bônus no `search_instructions` | Deixar isso no máximo como tie-break marginal |
| Resolver falta de ranking com bundle opinativo | Bundle bom mascara ranking ruim | `ensure_normative_policy` / `ensure_supporting_reference` | Manter composição mais fina e menos intrusiva |
| Confiar em benchmark pequeno como evidência de generalização | Facilita overfitting involuntário | 4 queries em `queries.yaml` | Criar holdout por intenção, reformulação e perturbação de corpus |
| Acumular thresholds e bônus sem modelo estatístico | Sistema fica difícil de calibrar e imprevisível | phrase/proximity/gap/confidence/priority/expansion | Migrar o score base para um baseline lexical mais canônico |

---

## 10. Tarefa 9 — Compatibilidade com BM25

| Componente atual | Compatível com BM25? | Observação |
|---|---|---|
| Tokenização e normalização | Sim | Devem ser preservadas como pré-processamento |
| Campos `title`, `tags`, `body` | Sim | BM25 por campo encaixa naturalmente |
| `priority`, `kind`, `scope` | Parcial | Melhor como filtro/rerank leve do que como núcleo do score |
| Sinônimos manuais | Parcial | BM25 reduz a dependência, mas não elimina aliases importantes |
| Phrase/proximity bonus | Parcial | Podem virar rerank opcional, não base do ranking |
| `resolve_instruction_context` | Não diretamente | BM25 melhora candidatos; não resolve seleção final sozinho |
| Applicability/compliance | Ortogonal | Não devem ser substituídos por BM25 |

### Resposta direta

**BM25 substituiria boa parte do scoring atual.**  
Principalmente a parte artesanal de:

- frequência manual;
- pesos arbitrários por campo;
- compensações por expansão.

**BM25 também reduziria a necessidade de heurísticas**, mas não eliminaria:

- filtragem por tipo de documento;
- classificação técnico vs meta;
- montagem final do bundle.

---

## 11. Tarefa 10 — Compatibilidade com FAISS / embeddings

| Componente atual | FAISS ajudaria? | Risco |
|---|---|---|
| Queries naturais com paráfrase | Sim | Pode recuperar docs semanticamente próximos, mas operacionalmente inadequados |
| Sinônimos manuais | Sim, parcialmente | Pode trocar dicionário manual por ruído vetorial se não houver rerank lexical |
| Meta-governance vs técnico | Parcialmente | Embeddings podem aproximar demais documentos processuais de técnicos |
| Supporting docs | Sim | Sem filtros por `kind/scope/tags`, o bundle pode contaminar |
| Corpus normativo com applicability | Não como camada única | Vetorial puro enfraquece previsibilidade e auditabilidade |

### Julgamento

Embeddings fariam sentido:

- como camada híbrida de recall;
- depois de existir um baseline lexical forte;
- com rerank e filtros claros.

Embeddings seriam perigosos:

- se usados para substituir diretamente o score lexical artesanal;
- se misturarem documentos meta e técnicos;
- se a avaliação continuar centrada na mesma suite estreita.

---

## 12. Tarefa 11 — Modelo mental recomendado

## Modelo mental recomendado

1. O sistema deve ser pensado em **quatro camadas distintas**:
   - ingestão/governança do corpus;
   - recuperação lexical;
   - leitura/batch/context slicing;
   - decisão normativa (`applicability` / `compliance`).

2. A **recuperação base** deve ser:
   - lexical;
   - explicável;
   - estável;
   - baseada em campos.

3. A camada lexical ideal deve ser:
   - **BM25-first** em `title`, `tags`, `body`;
   - com `scope`, `kind`, `priority` como filtros e sinais auxiliares;
   - com poucas heurísticas.

4. A camada semântica deve ser **opcional e controlada**:
   - embeddings/FAISS entram para recall complementar;
   - nunca como substituto único da busca lexical;
   - sempre combinados com rerank e filtros.

5. O papel da metadata deve ser:
   - organizar o corpus;
   - permitir filtros;
   - dar governança;
   - **não** virar um atalho para distorcer o ranking.

6. O papel das heurísticas deve ser:
   - mínimo;
   - residual;
   - justificado por evidência ampla;
   - revisto sempre que não generalizar para corpus novo.

7. O papel dos testes deve ser dividido:
   - contrato/protocolo/shape das tools;
   - invariantes do corpus;
   - benchmark de ranking;
   - avaliação de generalização.

8. Benchmark de ranking bom precisa medir:
   - `MRR`;
   - `Recall@k`;
   - `nDCG@k`;
   - `Precision@1/3/5`;
   - estabilidade sob reformulação de query;
   - estabilidade sob crescimento do corpus.

9. O corpus não deve ser “memorizado” pelo algoritmo.
   O algoritmo deve usar o corpus como fonte de evidência, não como coleção de exceções para tuning artesanal.

---

## 13. Respostas objetivas às 9 perguntas do objetivo

### 1. Quais mudanças realmente melhoraram a qualidade de recuperação?

As que melhoraram de verdade foram:

- frontmatter e metadata úteis;
- indexação por campos;
- normalização/tokenização melhores;
- batch com foco por seção;
- observabilidade do ranking;
- benchmark mínimo.

### 2. Quais mudanças são generalizáveis para qualquer corpus?

As acima, mais:

- separação nativo vs MCP;
- rebuild/versionamento do corpus;
- applicability/compliance para corpus normativo.

### 3. Quais mudanças já introduziram dependência do corpus atual?

- dicionário manual de sinônimos;
- boosts por ID/título;
- testes com `expected_id` estreito;
- resolvedor com seleção opinativa por `policy/reference`.

### 4. Quais decisões influenciaram positivamente o baseline?

- sair de markdown solto para corpus estruturado;
- tornar o MCP um produto real com tools úteis;
- melhorar a leitura do contexto, não apenas a busca;
- medir melhor o comportamento.

### 5. Quais decisões criaram base para problemas futuros (épicos 6–9)?

- expansão manual de sinônimos;
- pesos e thresholds arbitrários;
- resolver bundle com regras fixas;
- misturar melhora de ranking com melhora de orquestração.

### 6. O sistema nesses épicos estava mais “limpo” e menos heurístico?

**Sim.**  
Principalmente até o EPIC-04. O EPIC-05 ainda é bem mais limpo do que 06–09, mas já começa a ficar mais opinativo.

### 7. Qual era a natureza do ganho?

Predominantemente **estrutura**.  
Não era apenas “tuning para ganhar placar”.

### 8. Quais princípios devem ser preservados?

- governança forte do corpus;
- recuperação lexical simples e explicável;
- separação entre recuperar, ler, decidir aplicabilidade e decidir conformidade;
- medição séria e contínua.

### 9. Quais decisões devem ser evitadas daqui pra frente?

- continuar aumentando scoring artesanal;
- continuar expandindo sinônimos sem holdout;
- confundir bundle “bonito” com ranking realmente bom;
- usar a suite atual como única definição de qualidade.

---

## 14. Veredito final

**Os épicos 1 a 5 foram, no geral, a fase mais saudável da evolução do MCP.**

O sistema melhorou ali porque:

- ficou mais bem estruturado;
- passou a ter corpus governado;
- ganhou um baseline lexical utilizável;
- passou a expor um contrato MCP mais maduro;
- tornou a recuperação de contexto mais consumível por outra IA.

**O ganho principal foi estrutural.**

Mas o fim desse ciclo já introduz a semente do desvio posterior:

- sinônimos demais;
- score artesanal demais;
- resolvedor opinativo demais.

Por isso, a leitura correta não é:

> “épicos 1–5 deram resultado alto, então o desenho estava perfeito”

e sim:

> “épicos 1–5 acertaram o esqueleto do sistema; o erro posterior foi insistir em tuning heurístico em cima desse esqueleto em vez de consolidar um baseline lexical mais canônico”.

### Recomendação final

Preservar:

- corpus estruturado;
- fields;
- batch;
- telemetria;
- applicability/compliance.

Evitar:

- ampliar heurística corpus-shaped;
- confundir relevância com montagem opinativa;
- ajustar o motor para fixture específico.

**Direção mais coerente daqui pra frente:**  
`BM25-first`, híbrido opcional com embeddings depois, e avaliação de generalização muito mais forte do que a atual.
