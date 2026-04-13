# Análise Técnica: Tools versus Prompts e Resources no MCP (corpus de instructions governadas)

## 1. Objetivo do documento

Este documento consolida uma **análise técnica detalhada** sobre a adequação dos primitivos do **Model Context Protocol (MCP)** — **tools**, **prompts** e **resources** — ao desenho do servidor read-only **`corporate-instructions`** (pacote em `mcp-instructions-server/`), que expõe **recuperação parametrizada** sobre um **corpus Markdown** com frontmatter.

Os objetivos específicos são:

- explicar **por que cada tool atual** não pode ser **substituída de forma equivalente** apenas por **prompt** ou **resource**, sem perder semântica, controlo ou propriedades operacionais;
- caracterizar o **melhor uso** de **prompts** e de **resources** no ecossistema MCP (separação de responsabilidades);
- identificar **cenários em que prompts/resources são complementares** ao modelo por tools, incluindo arquiteturas híbridas;
- acrescentar **pontos transversais** (cliente/host, custo de contexto, segurança, versionamento, testabilidade) úteis para decisão e para comunicação com equipas.

A análise **não** pretende afirmar que tools são “superiores em geral”: pretende afirmar que, **para o problema de retrieval governado sobre N documentos**, a superfície **tool-shaped** é normalmente a mais fiel ao que o servidor já implementa — e que **prompt/resource** resolvem **outras classes de problema** ou funcionam como **camadas complementares**.

Salvo indicação em contrário, **“substituir”** segue a premissa da secção 3: eliminar a tool sem introduzir outra operação com a mesma semântica (incluindo handlers que apenas rebatizam a tool).

---

## 2. Contexto consolidado

O repositório investiga **centralização de contexto** e **governança de corpus** para reduzir duplicação de `.github/instructions` em cenários multi-repo. O MVP do servidor MCP:

- opera em **stdio**;
- lê o corpus a partir de **`INSTRUCTIONS_ROOT`**;
- mantém um **índice em memória** reconstruído na primeira utilização e sempre que a raiz (`INSTRUCTIONS_ROOT`) muda;
- expõe três tools: **`list_instructions_index`**, **`search_instructions`**, **`get_instruction`** (ver `mcp-instructions-server/corporate_instructions_mcp/server.py`).

A linha arquitetural já documentada separa:

1. **Base persistente / política curta** (instruções nativas “thin”, eventual conteúdo canônico endereçável).
2. **Seleção e retrieval com políticas** (descoberta, ranking, excertos, truncagem, validações).

Esta análise aprofunda a relação entre esse segundo item e os primitivos MCP.

---

## 3. Artefatos e premissas

1. **`mcp-instructions-server/corporate_instructions_mcp/server.py`** define o contrato atual das tools e os limites (`max_results`, `max_chars`, validação de `path`).
2. **`mcp-instructions-server/corporate_instructions_mcp/indexing.py`** define ingestão, hashing, scoring **determinístico e heurístico léxico** (`score_record`, `tokenize_query` — sobreposição de tokens e pesos, não IR clássico), excertos (`excerpt_around_match`) e limites defensivos (tamanho de arquivo, frontmatter).
3. **`research/analises/2026-04-09-analise-tecnica-mcp-copilot.md`** já posiciona tools vs resources/prompts ao nível arquitetural; este documento **aprofunda** ao nível **por-tool** e **por primitivo**.
4. Premissa: “substituir tool por prompt/resource” significa **eliminar a tool** e cumprir o mesmo papel **só** com `prompts/get` e/ou `resources/read` (ou equivalente), **sem** introduzir outra operação com a mesma semântica (o que, na prática, recria uma tool).

Definições operacionais usadas ao longo do texto:

- **Tool (MCP):** operação invocável com **argumentos estruturados**; o servidor executa lógica e devolve **resultado** (tipicamente texto/JSON) ao cliente/host.
- **Resource (MCP):** conteúdo **endereçável por URI**; foco em **obter/representar** um artefato (ou variante) como “dado”.
- **Prompt (MCP):** modelo de **mensagens** (template) com **argumentos declarados**; foco em **estruturar a interação** e padronizar entradas/saídas esperadas do fluxo de chat. *Nota:* um handler de `get_prompt` pode executar lógica no servidor; nesse caso deixa de ser “substituição pura” no sentido da premissa 4 (é fachada operacional).

---

## 4. Metodologia de análise

1. Mapear **capacidades** de cada tool (entradas, processamento, saídas, invariantes).
2. Confrontar cada capacidade com o que **prompts** e **resources** garantem nativamente (sem implementação adicional no servidor).
3. Verificar se a substituição exige **reimplementação da mesma lógica** noutro handler MCP ou **transferência da decisão** para o modelo (perda de determinismo).
4. Extrair **padrões complementares** (híbridos) coerentes com o protocolo e com o problema de governança do corpus.
5. Confrontar as conclusões com o código de referência (`server.py`, `indexing.py`, `paths.py`) para evitar divergência entre argumento e implementação.

---

## 5. Achados: por que cada tool não é substituível “1:1” por prompt/resource

### 5.1 Tabela-resumo (visão executiva)

| Tool | Papel atual | Substituir só por **resource**? | Substituir só por **prompt**? | Motivo central |
| --- | --- | --- | --- | --- |
| `list_instructions_index` | Catálogo completo com metadados estáveis (id, path, tags, hash…) | **Parcial**: dá para expor *um* resource agregado, mas vira “documento monolítico” ou exige listagem dinâmica | **Fraco**: prompt não enumera o disco; ou repete catálogo estático (drift) ou chama código (daí não é “só prompt”) | Enumerar **N fontes** com consistência e **hashes** é operação de serviço, não template |
| `search_instructions` | Ranking léxico/heurístico + filtros + excertos + `composed_context` | **Fraco** sem lógica tipo tool: resource é “get blob”, não **ranking parametrizado sobre N** | **Fraco** se “filtro” for só argumentos do template: não cobre **query aberta** + scoring + top‑K como o Python atual | O diferencial é **algoritmo + políticas** no servidor (não substituível por “só” template/read) |
| `get_instruction` | Corpo completo + truncagem + validação de path + erro estruturado | **Plausível como resource por documento**, mas **não remove** necessidade de descoberta (`list`/`search`) | **Fraco**: prompt não valida `..` nem aplica `max_chars` por política sem código no `get_prompt` | Segurança e limites são **enforcement** de entrega; resource ajuda no **endereçamento**, não substitui descoberta nem ranking |

### 5.2 `list_instructions_index` — catálogo materializado do índice

**O que a tool faz (tecnicamente):** reconstrói/usa o índice sobre `INSTRUCTIONS_ROOT` e devolve **JSON** com `instructions` (lista de objetos por arquivo `.md` indexado) e `count`, incluindo `content_sha256` e campos de frontmatter relevantes para navegação humana e para decisões downstream.

**Por que não é equivalente a “um prompt”:**

- Um **prompt MCP** resolve para **mensagens** (estrutura conversacional). Ele **não define**, por si, um **processo de ingestão** sobre o filesystem nem garante que o conteúdo listado corresponde ao **estado atual** do índice após mudanças de disco ou de `INSTRUCTIONS_ROOT`.
- Argumentos de prompt são **inputs de template**, não um substituto para **varrer `rglob('*.md')`**, aplicar limites (`MAX_INSTRUCTION_FILE_BYTES`), ignorar caminhos que escapam da raiz (p.ex. via symlink), e detectar colisões de `id` como o código faz em `build_index`.

**Por que não é equivalente a “um resource” (sem mais primitivos):**

- Um resource típico endereça **um** artefato. Um catálogo completo pode ser **um** resource (ex.: `catalog.json`), mas:
  - a **geração** desse artefato continua a ser **materialização de índice** (operação);
  - a **atualização** quando o corpus muda continua a exigir **rebuild** e políticas de frescura;
  - se o cliente passar a depender de “listar resources” como substituto, o comportamento depende de **como o host expõe** `resources/list` e de como modela **milhares** de URIs — o que pode ser **pior** do que uma resposta JSON compacta e estável;
  - **URI templates** (quando suportados) podem reduzir a cardinalidade de URIs “estáticas”, mas a **descoberta materializada** e as políticas de frescura continuam a ser implementação do servidor (equivalente operacional ao catálogo).

**Conclusão:** `list_instructions_index` é uma **operação de observabilidade + descoberta** sobre o estado do servidor. Prompt não cobre; resource só cobre ao **empacotar o resultado da operação** como blob — o que **relabela** o output, não elimina a necessidade da operação.

### 5.3 `search_instructions` — ranking léxico/heurístico e compressão de contexto

**O que a tool faz:** tokeniza query (`tokenize_query`), aplica filtro opcional por tags, calcula score (`score_record` com pesos por título/tag/prioridade), ordena, limita (`max_results` clamp), gera **excerto** (`excerpt_around_match`) e um **`composed_context`** agregado. Não é IR clássico (p.ex. BM25); é **sobreposição de tokens + regras** reprodutíveis no servidor.

**Por que “prompt com filtros por critérios” não substitui isto:**

- Em MCP, “filtros” em prompts normalmente significam **argumentos declarados** para compor um template. Isso cobre bem **conjuntos fechados** de variantes (“modo A/B”, “stack=dotnet”, “área=segurança”). **Não** cobre, por definição, a mesma classe de problema que **texto livre** + **ranking sobre N documentos** + **excerto dependente do match**.
- Se alguém propõe “o modelo filtra”: isso transfere a seleção para **heurística do LLM**, não para o **algoritmo** do servidor. Perdem-se propriedades que o projeto trata como valor:
  - **repetibilidade do resultado da tool** (mesma query/corpus e mesma versão do código → mesma ordenação devolvida ao cliente; **não** confundir com o comportamento posterior do LLM sem protocolo adicional);
  - **auditabilidade** (“porque este doc apareceu?” → score explicável por regras);
  - **controlo de custo** (top‑K e resumo antes do full text).

**Por que resources não substituem:**

- `resources/read` é **“obtém este endereço”**. Não inclui, por omissão, **função de ranking** sobre o espaço de URIs nem **política de excerto** dependente de tokens a menos que isso seja **implementado** no servidor — e aí **constrói-se** um **serviço** por trás do URI (semelhante a uma tool).

**Conclusão:** `search_instructions` é **computação + política**. Prompt/resource **não são**, por si, **motores de seleção/ranking sobre N**; no máximo **transportam resultados** de um motor que continua a existir (na implementação atual, esse motor é a própria tool).

### 5.4 `get_instruction` — fetch governado do corpo completo

**O que a tool faz:** resolve `id` ou `path` relativo, valida segurança de `path` (`instruction_path_needle_is_safe`), aplica `max_chars` com clamp, devolve JSON com metadados e `truncated`.

**Onde resource é mais “substituível”:**

- Faz sentido modelar **o corpo canônico** como **resource** por URI (ex.: esquema ilustrativo `…/instructions/{id}`), porque o output é essencialmente **conteúdo endereçável**.

**O que não desaparece mesmo com resource:**

- **Resolução segura** e **anti-traversal** continuam necessárias no servidor.
- **Truncagem como política** pode ser **modelada** no contrato do resource (ranges/leituras parciais) ou permanecer numa tool — dependendo do cliente e das capacidades de leitura parcial.

**Por que prompt não substitui bem:**

- Prompt não é o lugar natural para **enforcement** de `max_chars` e validação de entrada; isso é **código**. Um `get_prompt` poderia, em teoria, executar a mesma lógica — mas então o prompt torna-se **fachada** de uma operação, não o substituto conceptual da tool.

**Conclusão:** `get_instruction` é a face **“get blob governado”** do sistema. Resource pode ser **melhor representação** do *artifact*, mas **não elimina** `list/search` nem a **lógica** de validação/truncagem — apenas pode **reorganizar** onde vive.

---

## 6. O que sustenta a linha por tools (pontos fortes)

- **Separação clara entre “dados endereçáveis” e “operações”**: no desenho atual, o servidor já implementa operações com contratos (`query`, `tags`, `max_results`, `max_chars`) — o que mapeia **diretamente** para tools (escolha de implementação, não uma exigência absoluta do MCP).
- **Two-stage retrieval** (metadados/resumo → corpo completo) é um padrão clássico para **economia de contexto**; tools tornam esse padrão **explícito** e **mensurável** nos experimentos do repositório.
- **Determinismo e repetibilidade** são vantagens quando o valor do projeto inclui **governança** e **metodologia experimental** (baseline, condições controladas).

---

## 7. Riscos, tensões e equívocos comuns

1. **Confundir “prompt tem argumentos” com “prompt faz retrieval”**: argumentos parametrizam **templates**, não substituem **índice + ranking** sobre muitos arquivos.
2. **Confundir “resource” com “distribuição/updates”**: resource expõe conteúdo **servível**; **distribuir** nova versão do corpus para máquinas continua a ser **release/sync/git** (operação organizacional), salvo arquitetura explícita de artefatos remotos + cache. Um artefato publicado como resource **pode** ser o meio de entrega, mas ainda assim exige pipeline e política de atualização do lado cliente/host.
3. **Hiper-endereçamento**: modelar **cada parágrafo** como resource pode explodir cardinalidade e piorar UX de listagem no host — volta-se ao problema de **descoberta**.
4. **Dependência do host**: a forma como Copilot/VS prioriza tools vs resources vs prompts pode alterar **descoberta** e **custo**; decisões devem considerar **o consumidor real**, não só o protocolo.

---

## 8. Implicações para o servidor `corporate-instructions`, thin repo e documentação

### 8.1 Servidor MCP

- **Manter tools** como interface principal de **retrieval** é coerente com o código e com o problema.
- Evolução híbrida opcional:
  - **resources** para **documentos canónicos** (por `id` / versão);
  - **prompts** para **fluxos padronizados** (“como aplicar o corpus ao PR em curso”);
  - **tools** para **search/list** e para operações que exigem **parametrização fina** e **políticas**.

### 8.2 Template fino (`templates/copilot-instructions.thin.md`)

- O thin pode referenciar **prompts** como “modo de trabalho”, mas não deve sugerir que **prompt substitui** `search_instructions` sem equivalente servidor.
- Se adotares resources, o thin deve instruir **quando** anexar URIs vs **quando** chamar tools — senão o modelo pode **saltar** o estágio de compressão.

### 8.3 Documentação de produto

- Documentar explicitamente: **“prompt/resource não são substitutos automáticos de ranking/seleção sobre N; no máximo transportam o output de um motor (na implementação atual, exposto como tool).”**

### 8.4 Melhor uso de prompts e resources (guia de desenho)

**Prompts MCP — melhor quando:**

- Padronizar **formato de saída** (planos, checklists, estilo de revisão).
- Encapsular **fluxos** repetíveis com **parâmetros fechados** (ex.: `severidade`, `tipo_de_mudança`, `linguagem`).
- Definir **política conversacional**: “sempre que usar instruções corporativas, citar `id` e `path` na resposta”.
- **Pós-recuperação**: depois de `search_instructions`, um prompt pode dizer como **combinar** resultados com código local.

**Resources MCP — melhor quando:**

- Expor **artefatos estáveis** e **auditáveis** (documento inteiro, pacote de política, schema).
- Suportar **endereçamento versionado** (`…@sha256`, `…/v2026.04/…`) como **identidade** de conteúdo — **convenção** ilustrativa; cache e anexos dependem do host.
- Permitir que o cliente anexe dados por URI sem reinventar JSON tool-first — útil quando o host integra bem attachments.

### 8.5 Cenários complementares (híbridos recomendados)

| Cenário | Complemento sugerido | O que permanece em tool |
| --- | --- | --- |
| **Documento canônico por `id`** | Resource por instrução + metadados mínimos | `search_instructions` + `list_instructions_index` (descoberta) |
| **Padronizar aplicação pós-busca** | Prompt “modo revisão de segurança” com argumentos fechados | `search_instructions` com `tags=security` |
| **Publicação versionada do corpus** | Resource(s) ou artefato empacotado; *distribuição* via pipeline/git | Reindexação/restart conforme política local |
| **Cliente com forte suporte a attachments** | Resource para `get` do corpo; tool para `search` | Ranking léxico/heurístico (`search_instructions`) |
| **Experimentação A/B de template** | Prompt variants | Retrieval inalterado para comparar baseline |

### 8.6 Pontos adicionais sugeridos (roadmap e discussão)

1. **Contrato de erro**: `get_instruction` devolve JSON com `error`/`hint` em casos de validação ou não encontrado; outras tools podem falhar por exceção ou transporte RPC. Prompts/resources exigem disciplina equivalente se houver fallback.
2. **Observabilidade**: logs em stderr (já no servidor) são parte da operação; híbridos devem manter **rastreio** de “qual URI/tool/prompt foi usado”.
3. **Testes**: as tools atuais são facilmente testáveis em integração (`tests/` no pacote); resources/prompts acrescentam **matriz** de testes (URI estável, conteúdo esperado).
4. **Compatibilidade upstream**: primitivos suportados e UX dependem da stack `mcp` + host; evoluir para híbrido deve incluir **matriz de suporte** explícita.
5. **Caching**: resource pode ser cacheável por URI; `search` é menos cacheável por natureza (entrada variável) — útil para desenho de performance.
6. **Segurança**: `get_instruction` valida paths; resources precisam de **modelo de ameaça** equivalente (quem pode pedir que URI, e como evitar exfiltração por encadeamento).
7. **Tamanho do catálogo**: com N grande, `list_instructions_index` pode ser pesado — complemento futuro pode ser **paginação** (continua a ser operação tool-shaped).

---

## 9. Posicionamento: adotar, iterar ou descartar

**Iterar (evolução híbrida opcional), sem substituição cega.**  
A linha atual por **tools** permanece **tecnicamente justificada** para `list` e `search`, e **parcialmente substituível** por resources apenas na face “**get do documento**”, desde que **descoberta + políticas** permaneçam explícitas.

---

## 10. Síntese final

1. **Tools** neste servidor não são “atalhos de leitura de arquivo”: são **API de retrieval** com ranking léxico/heurístico, truncagem e validações — isso **não é o núcleo semântico** de prompts nem o modelo mental típico de resources.
2. **Prompts** servem para **templates e fluxos**; **resources** servem para **endereçamento de conteúdo**; **tools** servem para **operações parametrizadas** — este caso mistura dados e operações, mas **a parte operacional** encaixa melhor em tools.
3. **Complementaridade** faz sentido como **híbrido**: resources para blobs canônicos; prompts para padronização; tools para descoberta e ranking (heurístico léxico na implementação atual).
4. **Substituir tools por prompts** por causa de “filtros” confunde **argumentos de template** com **motor de seleção** sobre corpus — só não cai no equívoco se, por trás do prompt, existir **a mesma lógica** (e aí a discussão é de **fachada MCP**, não de capacidade).

---

## 11. Fontes e referências internas ao repositório

1. `mcp-instructions-server/corporate_instructions_mcp/server.py` — definição das tools e políticas de resposta.
2. `mcp-instructions-server/corporate_instructions_mcp/indexing.py` — ingestão, scoring e limites defensivos.
3. `mcp-instructions-server/README.md` — contrato operacional e limites.
4. `research/analises/2026-04-09-analise-tecnica-mcp-copilot.md` — enquadramento arquitetural tools/resources/prompts.
5. `research/analises/2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md` — template de análise e relação thin ↔ MCP.
6. `README.md` (raiz) — objetivo de pesquisa e metodologia.
