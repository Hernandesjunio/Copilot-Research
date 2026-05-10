# ADR-002: Corpus Query Expansion Map como camada de expansão de query

**Status**: Aceito  
**Data**: 2026-05-09  
**Revisão V1.1**: 2026-05-10  
**Revisão V1.2 (especificação operacional)**: 2026-05-10  
**Contexto**: MCP `corporate_instructions_mcp` — mecanismo de busca de instructions  
**Revisão agendada**: após validação experimental da V1

---

## 1. Contexto

O MCP usa um mecanismo de busca por tokens para recuperar instructions a partir de queries em linguagem natural. Existe um gap documentado entre o vocabulário do usuário/agente e o vocabulário técnico presente no corpus (ex: usuário escreve "resiliência", corpus usa "polly", "retry", "circuit-breaker").

Até esta decisão, o mecanismo utilizava um dicionário de sinônimos (`synonyms.yaml`) com as seguintes limitações identificadas:

- Modelo plano e bidirecional: `mensageria → rabbitmq` gerava automaticamente `rabbitmq → mensageria`, criando expansão cruzada indevida entre domínios.
- Todas as relações eram tratadas como equivalências, sem distinção de intensidade.
- Termos ambíguos (ex: `ttl` pode ser DNS ou cache) não tinham mecanismo de contenção.
- Vocabulário embutido no código (`DEFAULT_SYNONYMS`) criava um estado de fallback silencioso invisível ao operador.
- Nenhuma rastreabilidade de qual expansão foi aplicada e por quê.

---

## 2. Decisão

Substituir o dicionário de sinônimos pelo **Corpus Query Expansion Map**: uma camada de expansão modular, tipada, unidirecional e observável, integrada ao mecanismo atual de busca sem substituí-lo.

### Decisões específicas dentro desta decisão

| Decisão | Escolha | Alternativa rejeitada |
|---|---|---|
| Modelo de relação | Tipado: `aliases`, `strong_terms`, `weak_terms`, `contexts` | Flat (todos equivalentes) |
| Direcionalidade | Unidirecional (canônico → expandidos) | Bidirecional automático |
| Mecanismo de busca base | Manter o atual (token scoring) | Substituir por BM25 |
| Escopo do mapa | Local ao corpus ativo (`INSTRUCTIONS_ROOT`) | Global + local com merge |
| Expansão transitiva | Não (lookup de um nível) | Multi-hop (grafo) |
| Busca vetorial | Não (fora do escopo V1) | RAG / embedding retrieval |
| Fallback em erro | Desabilitar expansão (binário) | Fallback para mapa embutido |
| Formato de configuração | YAML modular por domínio em `metadata/corpus-query-expansion-map/` | YAML único centralizado |

---

## 2.1 Refinamento técnico do schema — V1.1 (2026-05-10)

### Motivação

Durante a validação experimental do template de entrada, três limitações do schema V1 foram identificadas:

1. `when_path_matches` vincula o mapa à estrutura de pastas do repositório específico, tornando-o não portável entre projetos com layouts distintos.
2. Ausência de sinal de tipo de artefato no nível do termo impede filtragem de precisão quando o contexto de arquivo é conhecido.
3. Ativação de contexto exclusivamente por path não cobre casos onde o vocabulário da query é suficiente para discriminar a tecnologia sem informação de diretório.

### Decisões adicionais

| Decisão | Escolha | Alternativa rejeitada |
|---|---|---|
| Ativação de contexto | `activation_terms` (vocabulário da query) + `applies_to` opcional (tipo de artefato) | `when_path_matches` (path específico de projeto) |
| Semântica de `applies_to` no nível do termo | Filtro de precisão: aplicado apenas quando `current_file_path` é conhecido; ignorado quando ausente | Boost (peso adicional sem filtro) |
| `applies_to` no bloco de contexto | Opcional — discrimina tipo de artefato (código vs. configuração vs. documentação) | Obrigatório |
| `activation_terms` no bloco de contexto | Opcional — vocabulário discriminante de tecnologia/protocolo | Obrigatório |
| Ativação cruzada (múltiplos contextos ativados simultaneamente) | MCP sinaliza conflito ao agente; agente decide o contexto a seguir | União silenciosa / falha silenciosa |
| Legado `when_path_matches` | Fora do schema e do loader; mapas devem usar `activation_terms` + `applies_to` | Manter ativação por pastas específicas de projeto nos YAML |

### Semântica de `applies_to` no nível do termo

Quando `current_file_path` está disponível na requisição de busca:
- O termo só expande se o path do arquivo em edição corresponder a pelo menos um padrão em `applies_to`.
- Termos sem `applies_to` expandem sempre (comportamento neutro).

Quando `current_file_path` não está disponível:
- `applies_to` é ignorado; todos os termos elegíveis expandem normalmente, sem falsos negativos em queries gerais.

**Diagnóstico quando o filtro barra a entrada:** se `applies_to` existir ao nível do termo, `current_file_path` for conhecido e não corresponder a nenhum padrão, a entrada **não** expande; o diagnóstico deve registar explicitamente essa omissão (ex.: `skipped_by_applies_to` com identificação do termo e motivo), em vez de falhar em silêncio.

### Combinação `applies_to` (termo × contexto)

- `applies_to` no **termo** restringe a entrada inteira: `aliases`, `strong_terms`, `weak_terms`, e a elegibilidade para avaliar `contexts` desse termo.
- `applies_to` dentro de um **contexto** restringe apenas esse ramo.
- Com `current_file_path` **conhecido**: para aplicar os `terms` de um contexto, o path deve satisfazer **todos** os `applies_to` definidos (do termo e do contexto). Se um dos dois estiver omitido, só o definido aplica.
- Com `current_file_path` **ausente**: os `applies_to` deixam de actuar como filtro (alinhado ao parágrafo anterior sobre falsos negativos).

### Ativação de contexto

- Um contexto pode candidatar-se à activação por `activation_terms`, por `applies_to`, ou por **ambos**.
- Se **ambos** `activation_terms` e `applies_to` estiverem presentes no mesmo contexto, **ambos** devem estar satisfeitos para tratar o contexto como activo (maior precisão).
- Só `activation_terms`: activação por vocabulário da query (e metadados acordados, quando existirem).
- Só `applies_to`: activação apenas quando `current_file_path` é conhecido e corresponde; com path ausente, esse ramo **não** se activa pelo tipo de artefato.
- **Nem** `activation_terms` **nem** `applies_to` num contexto com `terms`: erro de curadoria — o loader / validador deve rejeitar o mapa ou reportar falha estrutural.

### Frases multi-token (chave canónica)

- O canónico pode ser uma expressão de vários tokens em YAML entre aspas (ex.: `"problem details"`).
- O pipeline de tokenização / match de frases deve preferir **longest match wins** quando implementado, para não partir expressões estáveis em tokens fracos.

### Semântica de ativação cruzada

A avaliação de conflito aplica-se **apenas entre `contexts` do mesmo termo canónico**. Dois termos canónicos distintos presentes na mesma query não produzem o mesmo tipo de diagnóstico de “ativação cruzada” entre si.

Quando **dois ou mais contextos** do **mesmo** termo são simultaneamente candidatos activos (por sobreposição de `activation_terms`, por ambiguidade de sinais, ou por coincidência de critérios de activação):

- O MCP não aplica nenhum dos contextos de forma silenciosa.
- O diagnóstico registra os contextos em colisão e os sinais que os activaram.
- A resposta ao agente inclui ambiguidade explícita; o agente decide o contexto antes de prosseguir ou pede clarificação ao utilizador.

Este comportamento é preferido à união silenciosa porque transforma gaps de curadoria em feedback observável, em vez de ocultá-los como ruído de expansão.

### Evidência para curadoria do mapa

Cada entrada do mapa (incluindo `aliases`, `strong_terms`, `weak_terms`, `activation_terms` e padrões em `applies_to`) deve poder ser justificada a partir da instruction de origem — por exemplo `id`, `title`, `summary`, `tags`, headings, `TL;DR`, corpo Markdown, e secções explícitas de aplicabilidade ou de termos úteis à recuperação **quando existirem**. Não há campo formal de “source” no schema YAML; rastreabilidade humana (comentário acima da entrada) é suficiente na V1.1 sem acoplar o loader MCP a esse comentário.

---

## 3. Alternativas consideradas e rejeitadas

### 3.1 BM25 como base da busca

**Rejeitado para V1.**  
BM25 requereria reescrever o mecanismo de scoring atual, gerar um índice pré-computado e adicionar dependência. O experimento necessita validar se a *expansão estruturada* melhora recall antes de trocar o mecanismo base. Misturar as duas variáveis tornaria o experimento ininterpretável.  
**Roadmap**: avaliar BM25 puro e BM25 + expansão como fase futura após validação da V1.

### 3.2 Busca vetorial / RAG

**Rejeitado para V1.**  
Requer modelo de embedding, infraestrutura de indexação vetorial e aumenta significativamente a superfície de falha. O corpus é pequeno e estável; a busca por tokens com expansão controlada é suficiente para o experimento de validação.

### 3.3 Manter o dicionário de sinônimos bidirecional

**Rejeitado.**  
O modelo bidirecional gera expansão cruzada indevida entre domínios sem mecanismo de contenção. A ambiguidade não é diagnosticável (não há log de qual expansão foi aplicada). O modelo não distingue equivalência de associação, gerando ruído na precisão.

### 3.4 Expansão transitiva (grafo multi-hop)

**Rejeitado para V1.**  
`resiliencia → retry → httpclient → integration` aumenta recall de forma incontrolável, dificulta diagnóstico e mascara erros de corpus. O lookup de um nível é suficiente para o experimento e mantém o sistema auditável.

### 3.5 YAML único centralizado

**Rejeitado.**  
Um arquivo único cresce indefinidamente, dificulta revisões parciais, não permite organização por domínio e torna conflitos de merge mais custosos. A modularização por domínio semântico permite evolução incremental.

### 3.6 Global/local com merge automático

**Rejeitado para V1.**  
Merge automático amplia expansão além do esperado, reduz precisão e dificulta diagnóstico de conflitos semânticos. O escopo local é suficiente para validar o conceito. Global/local pode ser avaliado após a V1 estar estável.

---

## 4. Consequências

### 4.1 Positivas

- Expansão controlada: relações tipadas permitem calibrar intensidade (alias vs strong vs weak).
- Ambiguidade mitigada: contextos por vocabulário (`activation_terms`) e tipo de artefato (`applies_to`) evitam expansão de termos polissêmicos sem evidência suficiente; ativação cruzada é sinalizada explicitamente ao agente em vez de ser resolvida silenciosamente.
- Observabilidade: o diagnóstico registra exatamente o que foi expandido, de onde e por quê.
- Startup resiliente: mapa ausente ou inválido desabilita expansão sem derrubar o MCP.
- Arquitetura preparada para BM25: a camada de expansão é agnóstica ao mecanismo de scoring subjacente.

### 4.2 Negativas / trade-offs aceitos

- O mapa precisa de curadoria humana — não é gerado automaticamente a partir do corpus.
- Cobertura inicial depende de quem preenche os arquivos YAML; gaps de cobertura reduzem o benefício.
- O modelo unidirecional pode parecer contraintuitivo para quem vinha do modelo bidirecional.

### 4.3 Risco principal

Expansão aumentar recall e piorar precisão se `weak_terms` forem usados de forma muito ampla.  
**Mitigação**: testes `must-not-expand` para termos contextuais e critérios de aceite explícitos na seção 22 do plano.

### 4.4 Consequências específicas do refinamento V1.1

- **Portabilidade**: o mapa deixa de depender da estrutura de pastas do projeto; o mesmo arquivo YAML funciona em repositórios com layouts distintos.
- **Precisão por contexto de arquivo**: quando `current_file_path` é fornecido, expansões irrelevantes para o tipo de artefato em edição são filtradas sem afetar queries gerais.
- **Curadoria mais exigente**: `activation_terms` genéricos compartilhados entre contextos (ex: `queue` em `rabbitmq` e `servicebus`) geram ativação cruzada; o mecanismo de sinalização transforma esse gap em feedback visível ao agente, não em ruído silencioso.
- **Sem legado silencioso**: `when_path_matches` não existe no loader — mapas que ainda o contenham devem migrar explicitamente para `activation_terms` + `applies_to` em cada contexto.

---

## 5. Critérios de validação da decisão

A decisão será considerada validada quando:

1. Recall de pelo menos 3 queries previamente com zero resultados melhorar com expansão habilitada.
2. Precisão (top-1 correto) não piorar em queries de domínio único sem contexto.
3. Termos contextuais (ex: `rabbitmq` via `mensageria`) não aparecerem em resultados quando a query não contiver `activation_terms` do contexto correspondente e `current_file_path` não corresponder ao `applies_to` do contexto.
4. O diagnóstico (`include_diagnostics = true`) reproduzir exatamente o comportamento observado.

### Critérios adicionais V1.1

5. `applies_to` no nível do termo filtrar expansão corretamente quando `current_file_path` é fornecido; não bloquear expansão quando `current_file_path` está ausente.
6. Ativação cruzada (múltiplos contextos candidatos no **mesmo** termo canónico) produzir sinal explícito de conflito no diagnóstico em vez de expansão silenciosa.
7. Ficheiros YAML do mapa utilizam apenas contextos V1.1 (`activation_terms` e `applies_to` opcionais dentro de cada contexto; sem `when_path_matches`).

### Critérios adicionais V1.2

8. Quando `applies_to` do termo existir, `current_file_path` for conhecido e não corresponder a nenhum padrão, o diagnóstico registar a omissão (ex.: `skipped_by_applies_to`), sem expansão silenciosa dessa entrada.
9. Validação do mapa rejeitar contextos com `terms` mas sem `activation_terms` nem `applies_to`.
10. Combinação termo × contexto em `applies_to` e regras de activação de contexto conforme §2.1 (combinação, ativação de contexto) reproduzíveis em testes.

Se os critérios 1–10 não forem atingidos após validação experimental, reavaliar se o problema está no mapa (curadoria) ou no modelo (arquitetura).

---

## 6. Referências

- Plano V1: `plano-final-corpus-query-expansion-map-v1-sem-bm25.md`
- ADR-001: Escolha de Storage Vetorial (FAISS) — decisão ortogonal, não relacionada
- Análise do dicionário de sinônimos: `research/nucleo-pesquisa/analise-tools/analise-dicionario-sinonimos.md`
- Épico relacionado: `planning/bmad/epicos/` (EPIC-06 ou superior, gap analysis)
