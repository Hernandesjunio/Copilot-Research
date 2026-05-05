# 1. Resumo Executivo

O experimento **não prova que o MCP falhou**. A evidência aponta mais para uma combinação de:

- **prompt excessivamente ambicioso e pouco determinístico**;
- **orquestração boa no papel, mas fraca em enforcement**;
- **tools úteis para descoberta, mas fracas para seleção/rastreabilidade/avaliação**;
- **relatório sem baseline comparável e sem métricas de qualidade de recuperação**;
- **limitação prática do fluxo do Copilot Chat em compor contexto progressivamente sob muita instrução**.

## Diagnóstico curto

A causa principal mais provável é:

**falha de desenho experimental e de orquestração determinística, não falha pura do MCP**.

O MCP foi usado como **guardrail de veto** e isso funcionou. O que não funcionou foi transformá-lo no **principal provedor operacional de contexto suficiente para melhorar o resultado final**.

---

# 2. Diagnóstico Principal

## Causa raiz provável

A principal falha é a combinação de:

1. **Prompt original mistura implementação, governança, relatório, métricas, exportação e avaliação crítica em uma única execução**.
2. **`copilot-instructions.md` orienta bem o processo, mas não impõe um pipeline verificável de retrieve → rank → select → read → decide → implement**.
3. **As tools do MCP ajudam a encontrar policies, mas não ajudam a responder a pergunta decisiva do experimento:**  
   “o contexto recuperado realmente melhorou a solução em relação ao baseline?”
4. **O relatório mede volume de uso de tool, não qualidade causal do contexto recuperado**.

## Evidência forte

- O relatório mostra uso de MCP, mas a conclusão final é apenas:  
  **“MCP ajudou parcialmente”** e o ganho principal foi evitar RabbitMQ sem evidência. Isso é **veto arquitetural**, não melhoria substantiva de resultado.
- O próprio relatório admite:
  - **validação comportamental parcial**;
  - **ausência de testes**;
  - **inferência em correlação e endpoints técnicos**;
  - **alta dependência de descoberta manual**;
  - **plano truncado e reescrita parcial**.
- O prompt exige muita coisa ao mesmo tempo: implementação + validação + relatório + exportação + métricas + classificação FATO/HIPÓTESE/RISCO + comparação implícita de escalabilidade.

## O que isso significa

O experimento mediu mais a capacidade de **seguir um protocolo extenso** do que a capacidade de o MCP **melhorar tecnicamente a implementação**.

---

# 3. Análise do Prompt Original

## Julgamento geral

O prompt é **forte como especificação de auditoria**, mas **fraco como instrumento experimental determinístico**.

## Acertos

- Define idioma, segurança e escopo.
- Exige uso explícito do MCP.
- Diferencia `FATO`, `HIPÓTESE` e `RISCO DE INTERPRETAÇÃO`.
- Define critérios de aceite.
- Exige relatório estruturado e exportação.
- Pede “tool-first”.

## Falhas

### 3.1. Excesso de objetivos concorrentes
O prompt pede simultaneamente:

- implementar uma feature relativamente complexa;
- consultar MCP de forma extensa;
- produzir BMAD;
- validar build/testes;
- escrever relatório experimental completo;
- gerar métricas operacionais;
- exportar artefato final.

**Impacto:** dilui atenção do modelo e aumenta chance de execução superficial.

**Evidência:** o relatório admite:
- plano truncado;
- retry lógico;
- validação parcial;
- forte inspeção manual;
- ausência de prova runtime.

### 3.2. Determinismo insuficiente
O prompt manda usar:
- `list_instructions_index`
- várias `search_instructions`
- `get_instructions_batch`

Mas **não define critério de parada nem critério de seleção**.

Exemplos do que faltou:
- quantas searches são suficientes;
- como decidir quais `id`s entram no batch;
- quando uma instruction é “aplicável” versus apenas “relacionada”;
- qual evidência mínima do repo deve ser coletada antes de codar.

**Resultado:** o modelo pode chamar tools corretamente e ainda assim compor contexto de forma inconsistente.

### 3.3. Ambiguidade entre “usar MCP” e “não inferir”
O prompt exige forte uso de MCP, mas a tarefa real contém lacunas:
- sem broker real;
- sem testes;
- sem infraestrutura de observabilidade;
- sem migração.

Isso força o modelo a preencher lacunas por inferência local.

**Evidência:** o relatório declara inferência em:
- `X-Correlation-Id`;
- endpoints técnicos;
- bootstrap SQL.

### 3.4. Critério de sucesso mal alinhado com a hipótese do experimento
Se o objetivo é avaliar se o MCP melhora o resultado, o prompt deveria exigir explicitamente:

- comparação com baseline;
- quais decisões mudaram por causa do MCP;
- quais decisões seriam iguais sem MCP;
- custo em tokens/latência por decisão útil.

Isso não está no prompt.

## Veredito sobre o prompt

**Sim, o próprio prompt pode ter causado a falha do experimento.**  
Não por orientar mal o MCP, mas por **misturar tarefa de implementação com tarefa de avaliação científica sem um protocolo suficientemente controlado**.

---

# 4. Análise do Projeto Implementado

Vou separar em dois planos:

1. **projeto da aplicação implementada**;
2. **projeto de contexto/tooling observado**.

## 4.1. Aplicação implementada

### Pontos positivos
Há coerência com o repo:

- `Program.cs` mantém composição por extensions.
- `ClienteEndpoints.cs` preserva CRUD e adiciona endpoints técnicos.
- `ClienteServico.cs` continua fino.
- `ClienteRepositorioDapper.cs` centraliza persistência e transação.

Isso confirma aderência ao estilo local.

### Problemas
A solução aumentou funcionalidade, mas não necessariamente qualidade do resultado experimental.

#### a) Crescimento grande da superfície técnica
O relatório lista muitos arquivos novos e alterados. Para um experimento, isso aumenta:
- custo cognitivo;
- chance de erro;
- dificuldade de validar causalidade do MCP.

#### b) Mistura de objetivo de produto com objetivo de validação
Os endpoints:
- `/_outbox`
- `/_dlq`
- `/read-model`

foram adicionados para validar o experimento, não por evidência do produto.

**Evidência:** o próprio relatório classifica isso como inferência.

#### c) Repositório assumindo múltiplas responsabilidades
`ClienteRepositorioDapper.cs` passa a concentrar:
- CRUD;
- outbox;
- marcação de publicação;
- falhas;
- processamento;
- read-model;
- DLQ.

Para o experimento, isso entrega feature. Para análise arquitetural, reduz clareza causal do ganho do MCP.

## 4.2. Projeto de tools/contexto

Aqui está o ponto mais importante.

### As tools são úteis?
**Sim, mas principalmente para descoberta normativa.**

Exemplos observados:
- `corporate_instructions_resolve_instruction_context`
- `search_instructions`
- `get_instructions_batch`
- `get_normative_checklist`
- `detect_instruction_conflicts`

### Onde falham para esta atividade?

#### a) Faltam sinais fortes de ranking aplicável
As tools retornam:
- ids;
- excerpts;
- frontmatter;
- relevância textual.

Mas não retornam algo como:
- `why_selected_for_this_repo`;
- `applicability_score`;
- `evidence_requirements_satisfied`;
- `conflicts_with_repo_style`;
- `decision_template`.

Isso força o modelo a fazer muito trabalho intermediário.

#### b) Falta rastreabilidade decisão → tool output → patch
O relatório cita ids e arquivos, mas não há estrutura que prove:
- qual trecho do batch alterou qual decisão;
- qual decisão teria sido diferente sem MCP;
- qual parte do patch deriva de inferência.

#### c) Recuperação ainda é lexical/normativa, não operacional
Pelo material, o MCP parece excelente para “quais guardrails existem”, mas fraco para “qual implementação mínima e validável devo preferir aqui”.

### Veredito
O projeto implementado **entrega tools úteis**, mas **não suficientes para tornar o MCP o principal provedor de contexto operacional**.

---

# 5. Análise do Relatório Final

## Julgamento geral

O relatório é **bom como narrativa**, mas **fraco como evidência experimental comparativa**.

## O que ele mede bem

- quais tools foram chamadas;
- quantas vezes;
- quais decisões foram ancoradas em MCP;
- onde houve inferência;
- quais lacunas existiam no repo;
- quais riscos de escalabilidade existem.

## O que ele não mede e deveria medir

### 5.1. Não há baseline
Sem baseline, não é possível afirmar rigorosamente que “não melhorou”.

**Evidência ausente necessária:**
- patch baseline sem MCP;
- relatório baseline com mesma rubrica;
- tempo/latência/token por abordagem;
- comparação de decisões e defeitos.

### 5.2. Não mede qualidade de recuperação
Faltam métricas como:
- precision@k das instructions recuperadas;
- recall de policies realmente aplicáveis;
- taxa de contexto lido e realmente usado;
- ruído por instruction irrelevante;
- custo por decisão útil.

### 5.3. Não mede causalidade
O relatório diz que certas decisões foram ancoradas no MCP, mas não prova:
- quais delas já seriam óbvias só pelo repo;
- quais decisões mudaram graças ao MCP;
- quais decisões continuaram dependentes de inferência.

### 5.4. Métricas operacionais estão em `N/A`
Isso enfraquece bastante a validade.

Especialmente faltam:
- timestamps;
- tokens;
- custo;
- latência por etapa;
- bytes lidos.

Sem isso, a tese “mais contexto / mais MCP / mais features não melhorou” fica incompleta.

## Veredito
O relatório **não permite concluir com segurança se a falha foi do MCP, do Copilot, do prompt ou da metodologia**.  
Ele permite apenas concluir que **o ganho observado do MCP foi limitado**.

---

# 6. Análise do `copilot-instructions.md`

## Julgamento geral

O arquivo é **bom como política de orquestração**, mas **insuficiente como protocolo operacional determinístico**.

## Pontos fortes

- Diz claramente para responder em português.
- Proíbe assumir infraestrutura sem evidência.
- Define quando chamar MCP.
- Explica discover/read/evidence gate/decide/plan.
- Exige leitura de batch antes de aplicar policy.
- Valoriza evidência do workspace.

## Limitações

### 6.1. Está correto, mas permissivo demais
Ele diz:
- usar `search`;
- depois `get_instructions_batch`;
- depois decidir.

Mas não define:
- número mínimo/máximo de searches;
- regra de deduplicação de ids;
- critério para descartar resultado irrelevante;
- formato obrigatório de tabela de evidência antes de implementar.

### 6.2. Não obriga estratégia progressiva explícita
A estratégia ideal seria algo como:

1. levantar hipótese de contexto necessário;
2. buscar;
3. ranquear;
4. selecionar ids;
5. ler batch;
6. registrar matriz decisão/evidência;
7. só então implementar.

O arquivo sugere isso, mas **não força estrutura verificável**.

### 6.3. Não define fallback claro
Quando o corpus não fecha a decisão, o arquivo diz para nomear lacuna e tratar como hipótese. Isso é bom.  
Mas faltam regras como:

- parar e pedir confirmação humana se a lacuna afetar contrato público;
- não criar endpoint técnico sem autorização explícita;
- não introduzir cross-cutting novo se não houver evidência prévia.

### 6.4. Pode gerar ruído por excesso de metaprocesso
Para um modelo conversacional, há bastante protocolo abstrato.  
Isso ajuda governança, mas pode atrapalhar execução quando combinado com um prompt já muito pesado.

## Veredito
O `copilot-instructions.md` **não é o principal culpado**, mas **não é forte o suficiente para produzir execução determinística repetível**.

---

# 7. Limitações Possíveis do Copilot Chat

## Evidência forte

### 7.1. O modelo chamou tools, mas isso não virou melhoria proporcional
O relatório mostra uso amplo de tools:
- `list`
- `search`
- `batch`
- `checklist`
- `detect_conflicts`

Mesmo assim:
- a validação ficou parcial;
- houve reescrita;
- houve inferência relevante;
- o ganho principal foi apenas evitar RabbitMQ indevido.

Isso sugere limitação de **transformação de contexto em execução ótima**, não ausência de tool use.

### 7.2. Houve dificuldade de composição progressiva
O relatório admite:
- plano truncado;
- reescrita parcial;
- alta dependência de descoberta manual.

Isso é compatível com limitação prática de chat agent sob alto volume de instruções/contexto.

## Indícios

- O modelo pode ter usado tools de forma mais **ritualística** do que **seletiva**.
- Pode ter lido policies suficientes para conformidade, mas não para otimização do desenho.
- Pode ter priorizado satisfazer o prompt/relatório em vez de maximizar qualidade arquitetural mínima.

## Hipóteses não comprovadas

- que o Copilot “ignorou” o retorno das tools;
- que o ranking interno do chat degradou o uso do conteúdo lido;
- que havia truncamento silencioso relevante na composição do contexto.

## Evidência que precisaria ser coletada

- transcript completo de tool call + outputs usados;
- ordem temporal real das chamadas;
- quais trechos entraram no contexto final do modelo;
- comparação entre ids recuperados e ids efetivamente citados/acionados no patch;
- baseline com mesmo repo sem MCP.

---

# 8. Matriz de Causa Raiz

| Causa | Probabilidade | Evidência observada | Impacto | Como confirmar | Correção recomendada |
|---|---|---|---|---|---|
| Prompt excessivamente amplo e pouco determinístico | Alta | mistura implementação, validação, relatório, métricas, exportação | Alto | executar A/B com prompt enxuto vs atual | separar execução técnica de avaliação experimental |
| Falta de baseline comparável | Alta | relatório não compara com execução sem MCP | Alto | repetir mesmo cenário sem MCP e mesma rubrica | tornar baseline obrigatório |
| MCP útil como guardrail, mas fraco como contexto operacional | Alta | ganho principal foi veto ao RabbitMQ; restante exigiu inferência | Alto | medir decisões alteradas pelo MCP | adicionar metadados de aplicabilidade e decision templates |
| `copilot-instructions.md` sem enforcement determinístico | Média | processo bom, mas sem critério de seleção/parada | Médio | A/B com versão prescritiva | exigir matriz retrieve→select→evidence antes do patch |
| Tools com pouca rastreabilidade causal | Média | ids/excerpts existem, mas não decisão→trecho→patch | Alto | instrumentar tool output e consumo | retornar justificativa de aplicabilidade e evidência satisfeita |
| Excesso de contexto / carga cognitiva | Média | protocolo + prompt + repo + relatório + MCP | Médio | medir token pressure e truncation | limitar contexto e fazer em fases |
| Limitação do Copilot Chat para composição progressiva | Média | plano truncado, retry, execução parcial | Alto | repetir com fluxo em duas fases | dividir descoberta, decisão e implementação em turnos |
| Falha do MCP como corpus | Baixa/Média | corpus ajudou em veto e guardrails | Médio | comparar com corpus enriquecido | enriquecer policies com fallback operacional |
| Falha pura do Copilot em usar tools | Baixa | houve tool use extenso e uso real em decisões | Médio | analisar transcript detalhado | melhorar protocolo antes de culpar o agente |

---

# 9. Recomendações Prioritárias

## A. Ajustes no prompt original

### 1. Problema
Prompt mistura execução e avaliação experimental.

- **Mudança sugerida:** dividir em 2 prompts:
  1. `execução técnica`;
  2. `avaliação experimental`.
- **Justificativa técnica:** reduz competição entre objetivos.
- **Impacto esperado:** maior foco e menor inferência ad hoc.
- **Complexidade:** baixa.
- **Como testar:** A/B com mesmo repo e mesma tarefa.

### 2. Problema
Sem critério de parada para retrieval.

- **Mudança sugerida:** exigir:
  - 1 `list` ou `resolve`;
  - 3 a 5 `search` temáticas;
  - seleção de no máximo 6 ids;
  - leitura batch de 100% dos ids selecionados;
  - tabela de aplicabilidade antes do patch.
- **Impacto esperado:** retrieval mais consistente.
- **Complexidade:** baixa.
- **Como testar:** comparar dispersão de ids entre execuções.

### 3. Problema
Sem comparação causal MCP vs sem MCP.

- **Mudança sugerida:** adicionar seção obrigatória:
  - `Decisões que mudaram por causa do MCP`
  - `Decisões que seriam iguais sem MCP`
- **Impacto esperado:** melhora validade do experimento.
- **Complexidade:** baixa.
- **Como testar:** revisão humana cega.

## B. Ajustes no `copilot-instructions.md`

### 1. Problema
Processo é bom, mas não verificável.

- **Mudança sugerida:** exigir formato obrigatório:
  - `Necessidades de contexto`
  - `Searches executadas`
  - `IDs candidatos`
  - `IDs selecionados`
  - `Evidência do repo`
  - `Decisões permitidas`
  - `Lacunas`
- **Impacto esperado:** menos improviso.
- **Complexidade:** baixa.

### 2. Problema
Falta fallback operacional.

- **Mudança sugerida:** adicionar:
  - se falta evidência para contrato público/cross-cutting, **pedir confirmação**;
  - não criar endpoint técnico público por inferência;
  - não introduzir correlação/observabilidade nova sem gatilho explícito.
- **Impacto esperado:** menos overengineering inferido.
- **Complexidade:** baixa.

## C. Ajustes no MCP

### 1. Problema
Policies são normativas, mas pouco prescritivas para lacunas.

- **Mudança sugerida:** enriquecer frontmatter com:
  - `applicability_examples`
  - `repo_signals_required`
  - `fallback_patterns`
  - `preferred_minimal_implementation`
- **Impacto esperado:** menos inferência quando o repo não tem infra.
- **Complexidade:** média.

### 2. Problema
MCP veta, mas não oferece caminho mínimo padrão.

- **Mudança sugerida:** para casos como mensageria, incluir no corpus:
  - opção A: broker real com evidência;
  - opção B: stub de experimento;
  - opção C: parar e pedir confirmação.
- **Impacto esperado:** mais uniformidade entre repositórios.
- **Complexidade:** média.

## D. Ajustes nas tools

### 1. Problema
Falta seleção explicável.

- **Mudança sugerida:** `search`/`resolve` devolver:
  - `applicability_reason`;
  - `workspace_evidence_required`;
  - `workspace_evidence_status`;
  - `implementation_risk`;
  - `decision_areas`.
- **Impacto esperado:** melhor escolha de contexto.
- **Complexidade:** média.

### 2. Problema
Falta rastreabilidade.

- **Mudança sugerida:** tool de `decision trace` ou output estruturado:
  - `instruction_id`
  - `repo_evidence`
  - `decision_allowed`
  - `decision_blocked`
- **Impacto esperado:** análise experimental muito melhor.
- **Complexidade:** média/alta.

## E. Ajustes no relatório/métricas

### 1. Problema
Mede volume, não qualidade.

- **Mudança sugerida:** incluir:
  - baseline obrigatório;
  - precision@k;
  - `% de ids lidos realmente usados`;
  - `decisions changed by MCP`;
  - `cost per useful decision`.
- **Impacto esperado:** validade causal.
- **Complexidade:** média.

## F. Ajustes no desenho experimental

### 1. Problema
Experimento mistura demasiadas variáveis.

- **Mudança sugerida:** controlar variáveis:
  - mesmo prompt técnico;
  - uma condição sem MCP;
  - uma com MCP mínimo;
  - uma com MCP + protocolo determinístico.
- **Impacto esperado:** identificação real da causa.
- **Complexidade:** média.

---

# 10. Novo Fluxo Determinístico Recomendado

1. **Interpretar objetivo**
   - listar 3 a 7 decisões técnicas que realmente precisam de contexto externo.

2. **Identificar contexto necessário**
   - classificar por tema: mensageria, SQL, testes, observabilidade, contrato HTTP.

3. **Consultar índice**
   - usar `list` ou `resolve` apenas para mapear o corpus.

4. **Buscar candidatos**
   - executar 3 a 5 searches temáticas curtas.

5. **Selecionar candidatos**
   - limitar a no máximo 6 ids.

6. **Ler conteúdo detalhado**
   - `get_instructions_batch` obrigatório.

7. **Cruzar com evidência do repo**
   - montar matriz:
     - `policy`
     - `repo signal`
     - `aplica?`
     - `lacuna?`
     - `pode implementar?`

8. **Parar se faltar evidência crítica**
   - pedir confirmação humana se a lacuna afetar contrato público ou infraestrutura.

9. **Produzir BMAD mínimo**
   - só com ids realmente usados.

10. **Executar implementação mínima**
   - sem endpoints técnicos extras salvo autorização explícita.

11. **Validar**
   - build + testes + prova runtime mínima se o experimento exigir comportamento.

12. **Registrar fontes usadas**
   - decisão → instruction id → arquivo do repo → patch.

---

# 11. Experimentos A/B Sugeridos

## Experimento 1
**A:** prompt atual  
**B:** prompt dividido em execução + avaliação

- Mede: qualidade do patch, inferência extra, completude de validação.

## Experimento 2
**A:** `copilot-instructions.md` atual  
**B:** versão com pipeline obrigatório e tabela de evidência

- Mede: consistência entre execuções.

## Experimento 3
**A:** MCP atual  
**B:** MCP com `fallback_patterns` e `applicability_reason`

- Mede: redução de inferência ad hoc.

## Experimento 4
**A:** uma única conversa end-to-end  
**B:** 3 turnos:
- descoberta,
- decisão,
- implementação

- Mede: truncamento, reescrita, qualidade final.

## Experimento 5
**A:** relatório atual  
**B:** relatório com baseline + precision@k + decision trace

- Mede: capacidade real de atribuir causalidade ao MCP.

## Experimento 6
**A:** tarefa completa  
**B:** mesma tarefa sem exigência de relatório/exportação

- Mede: quanto a sobrecarga experimental piora o resultado técnico.

---

# 12. Versão Melhorada do Prompt Original

## Objetivo da melhoria
Reduzir ambiguidade, impor determinismo e separar implementação de avaliação.

### Versão recomendada

**Papel:** atuar como engenheiro de software sênior executando uma tarefa técnica com uso obrigatório do MCP `corporate-instructions`.

**Meta:** implementar o cenário de outbox/mensageria no repositório atual com o menor conjunto de mudanças necessário, preservando o CRUD existente.

**Protocolo obrigatório:**

1. **Descoberta de contexto**
   - executar `corporate_instructions_list_instructions_index` ou `corporate_instructions_resolve_instruction_context`;
   - executar entre **3 e 5** buscas temáticas;
   - selecionar no máximo **6 instructions**;
   - ler o batch completo antes de decidir.

2. **Matriz obrigatória antes do patch**
   Para cada instruction selecionada, registrar:
   - `id`
   - `kind`
   - `decisão coberta`
   - `evidência do repo`
   - `aplica?`
   - `lacuna`
   - `pode implementar sem confirmação?`

3. **Regras de parada**
   - se faltar evidência para infraestrutura nova, contrato público novo ou cross-cutting novo, **não implementar por inferência**;
   - nesses casos, declarar a lacuna e seguir com alternativa mínima ou pedir confirmação.

4. **Escopo técnico**
   - implementar apenas o necessário para satisfazer os critérios de aceite;
   - não criar endpoints técnicos públicos, middleware novo ou observabilidade nova sem justificativa explícita baseada em repo + instruction.

5. **BMAD obrigatório**
   - Background
   - Mission
   - Approach
   - Delivery/validation

6. **Validação mínima obrigatória**
   - `dotnet build`;
   - testes existentes, se houver;
   - se não houver ambiente para prova runtime, declarar exatamente o que ficou sem validação.

7. **Saída obrigatória**
   - matriz de contexto;
   - BMAD;
   - patch;
   - validação;
   - seção final: `Decisões alteradas pelo MCP` e `Decisões ainda dependentes de inferência`.

---

# 13. Versão Melhorada do `copilot-instructions.md`

## Objetivo da melhoria
Tornar o protocolo executável e auditável.

### Versão recomendada

# Instruções locais

- Responde em português.
- Nunca exponhas segredos, tokens ou PII.
- Não assumas serviços, infraestrutura ou integrações sem evidência no repo.

## Repositório

- API de gestão de clientes em camadas. Stack principal: C# / .NET 8 / ASP.NET Core.

## Uso do MCP `corporate-instructions`

Usa o MCP para decisões transversais: segurança, contratos API, mensageria, dados, testes, observabilidade, resiliência, estilo.

## Pipeline obrigatório

1. **Interpretar**
   - listar as decisões técnicas que precisam de contexto externo.

2. **Retrieve**
   - se o tema for amplo ou pouco conhecido: `corporate_instructions_list_instructions_index` ou `corporate_instructions_resolve_instruction_context`;
   - se o tema for conhecido: `corporate_instructions_search_instructions`.

3. **Rank**
   - executar entre 3 e 5 buscas temáticas curtas;
   - deduplicar resultados;
   - selecionar no máximo 6 ids.

4. **Read**
   - chamar `corporate_instructions_get_instructions_batch`;
   - não aplicar policy só com resultado de search.

5. **Evidence gate**
   - para cada id selecionado, registar:
     - `id`
     - `kind`
     - `decisão`
     - `repo evidence`
     - `workspace_evidence_required`
     - `aplica?`
     - `lacuna`
   - sem evidência suficiente, tratar como hipótese.

6. **Stop conditions**
   - pedir confirmação humana se a mudança introduzir:
     - infraestrutura nova;
     - endpoint técnico público;
     - contrato externo novo;
     - observabilidade/correlação nova sem pré-existência.

7. **Plan**
   - só depois produzir BMAD mínimo.

8. **Implement**
   - preferir a menor mudança possível;
   - não expandir escopo para facilitar demonstração do experimento.

9. **Validate**
   - após mudanças relevantes, executar build e testes existentes.

## Regras adicionais

- `kind: policy` lida no batch = regra aplicável.
- `kind: reference` = apoio, não imposição.
- Se houver múltiplas policies plausíveis, usar `corporate_instructions_detect_instruction_conflicts`.
- Se o cenário for repetível, usar `corporate_instructions_get_normative_checklist`.

## Saída obrigatória antes do patch

Apresentar sempre uma tabela com:
- `Instruction ID`
- `Tipo`
- `Decisão`
- `Evidência no repo`
- `Status` (`aplica`, `não aplica`, `hipótese`)
- `Ação permitida`

---

# 14. Conclusão Técnica

## Diagnóstico principal
A falha mais provável **não está no MCP isoladamente**. Está no fato de que o experimento usou o MCP como fonte de guardrails, mas **não estruturou um fluxo determinístico para converter guardrails em contexto operacional mínimo e comparável**.

## Causas secundárias
- prompt excessivamente carregado;
- ausência de baseline;
- métricas insuficientes;
- tools com pouca explicabilidade de aplicabilidade;
- `copilot-instructions.md` orientativo, mas pouco prescritivo;
- limitação prática do chat em executar descoberta + implementação + relatório em uma única passada.

## O que provavelmente não é o problema
- Não há evidência forte de que o **corpus MCP esteja errado**.
- Não há evidência forte de que o **Copilot tenha ignorado totalmente as tools**.
- Não há evidência forte de que a **consulta ao MCP tenha sido inútil**; ela foi útil, mas insuficiente.

## O que precisa ser medido melhor
- baseline vs MCP;
- precisão e ruído da recuperação;
- decisões efetivamente alteradas pelo MCP;
- custo por decisão útil;
- latência e token pressure;
- rastreabilidade decisão → instruction → patch.

## Alterações prioritárias
1. separar execução técnica de avaliação experimental;
2. tornar o pipeline de contexto obrigatório e verificável;
3. enriquecer tools/MCP com aplicabilidade e fallback;
4. exigir baseline e métricas causais.

## Conclusão final
**O experimento não falhou principalmente por culpa do MCP.**  
Ele falhou mais provavelmente por **desenho experimental fraco, protocolo insuficientemente determinístico e métricas incapazes de provar ganho real de qualidade**.
