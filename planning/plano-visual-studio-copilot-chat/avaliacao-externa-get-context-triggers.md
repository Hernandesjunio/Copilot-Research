# Avaliacao Externa da Tool `get_context_triggers`

## Objetivo deste documento
Este documento resume, em linguagem externa e sem depender de conhecimento interno do servidor, o que funcionou bem na avaliacao da tool `get_context_triggers`, o que ainda nao fecha totalmente em relacao ao modelo hibrido planeado e quais melhorias valem ser analisadas.

O foco aqui e ajudar outra IA, como o Copilot, a:
- entender o comportamento esperado da tool;
- revisar aderencia ao modelo thin + tool + contexto normativo;
- identificar gaps de contrato e de orquestracao;
- sugerir melhorias com base em contrato, fluxo e comportamento observado.

## Contexto resumido
O modelo planeado parte de um `copilot-instructions.md` thin, cujo papel e:
- montar contexto antes de agir;
- planejar antes de executar;
- usar uma tool de decisao para orientar a sequencia de descoberta;
- aplicar evidence gate antes de tratar policy como norma aplicavel;
- parar quando houver risco de contrato publico, infraestrutura nova, observabilidade nova ou integracao externa sem evidencia suficiente.

Nesse modelo, a tool `get_context_triggers` deve receber um contrato estruturado de entrada e devolver um contrato estruturado de saida com:
- classificacao do cenario;
- estrategia macro;
- sequencia de tools;
- gatilhos de contexto local;
- gatilhos de contexto normativo;
- evidence gate;
- regras de stop;
- fallbacks;
- requisitos de saida para a resposta final.

## O que deu certo

### 1. A tool acertou a classificacao do cenario canonico
No cenario de referencia de pedido transversal com foco em plano, a tool conseguiu devolver:
- o mesmo `scenario_id` esperado;
- a mesma familia de cenario;
- a mesma recomendacao macro de execucao em modo `plan_only`.

Por que isso e importante:
- mostra que a tool entendeu o caso base do modelo hibrido;
- valida que a ideia de usar sinais estruturados no request esta funcionando para o cenario principal;
- reduz o risco de o agente sair implementando quando o pedido e apenas de plano.

### 2. A estrategia de alto nivel ficou coerente com o modelo hibrido
No caso canonico, a tool orientou corretamente:
- descoberta inicial do repo;
- uso de MCP para contexto normativo;
- leitura em batch antes de aplicar policy;
- producao de plano como resultado esperado.

Por que isso e importante:
- a ferramenta conseguiu reproduzir o coracao da orquestracao esperada;
- a sequencia retornada faz sentido para um pedido transversal sem ficheiros explicitos;
- isso aproxima a ferramenta do comportamento desejado pelo `copilot-instructions.md`.

### 3. A composicao de contexto normativo funcionou bem em um cenario realista
Num cenario de resiliencia HTTP com retry, timeout e circuit breaker, a ferramenta levou a uma composicao de contexto relevante, retornando instrucoes coerentes com o tema.

Por que isso e importante:
- mostra que a sequencia recomendada nao ficou apenas formalmente correta;
- na pratica, ela conduziu a policies adequadas ao problema;
- isso indica que o fluxo `decidir -> buscar -> ler em batch -> avaliar evidence gate` tem utilidade real.

### 4. O comportamento read-only ficou preservado
A tool atua como um decisor e nao como um executor. Ela nao implementa, nao altera ficheiros e nao dispara por conta propria outras acoes mutaveis.

Por que isso e importante:
- preserva o papel arquitetural da tool;
- reduz acoplamento;
- torna a ferramenta mais previsivel para orquestracao.

### 5. O stop rule funcionou quando o risco foi declarado no pedido
Quando o pedido explicitou integracao externa sem evidencia suficiente do workspace, a tool conseguiu elevar o caso para stop e sinalizar necessidade de input humano.

Por que isso e importante:
- a protecao contra inferencia perigosa existe;
- o modelo nao trata toda mudanca transversal como automaticamente segura;
- isso e coerente com o objetivo do evidence gate e das stop rules.

## O que nao fecha totalmente

### 1. O contrato de entrada nao esta realmente exposto como contrato estruturado no host
Embora conceitualmente a tool trabalhe com um contrato JSON completo, a interface observada pelo host ainda pode ficar reduzida a um unico campo textual contendo o payload inteiro.

Por que isso nao fecha totalmente:
- a intencao do plano era um contrato forte e explicito;
- um campo textual unico enfraquece validacao nativa, discoverability e usabilidade para outra IA;
- o host deixa de conhecer diretamente os campos de `request`, `workspace`, `context_state` e `constraints`.

Risco pratico:
- erros de shape ou combinacao de campos so aparecem tardiamente;
- outra IA pode nao perceber claramente a estrutura esperada;
- fica mais dificil orientar prompting, tool calling e validacao automatica.

Melhoria sugerida:
- expor o contrato em campos estruturados no schema da tool;
- se isso nao for possivel de imediato, quebrar o input em blocos maiores explicitamente tipados em vez de um unico texto bruto.

### 2. O evidence gate ainda depende demais do que o pedido declara, e menos do que o corpus realmente revela
Em cenarios transversais, foi possivel observar que as policies retornadas em batch exigiam evidencia de workspace, mesmo quando o pedido nao marcava explicitamente certos riscos.

Por que isso nao fecha totalmente:
- o modelo planeado pressupoe que a policy so pode ser tratada como norma aplicavel depois da leitura em batch;
- se o batch trouxer `workspace_evidence_required=true`, isso deveria influenciar diretamente a saida final da orquestracao;
- sem essa reconciliacao, a tool pode subestimar a necessidade de verificar sinais locais.

Risco pratico:
- a tool pode devolver um evidence gate insuficiente;
- outra IA pode prosseguir com excesso de confianca;
- o comportamento fica correto apenas quando o chamador ja souber marcar todos os riscos no request.

Melhoria sugerida:
- introduzir uma fase de reconciliacao pos-batch;
- apos a leitura normativa, a orquestracao deve reavaliar:
  - se alguma instruction exige `workspace_signals`;
  - se isso deveria ativar `must_verify_workspace_signals`;
  - se isso deveria elevar `stop_required`.

### 3. Os criterios de sucesso da `tool_sequence` estao simplificados demais
O contrato planeado previa condicoes de sucesso especificas por tool. Na pratica, um criterio muito generico tende a ser insuficiente.

Por que isso nao fecha totalmente:
- um passo de descoberta de repo nao deve ser considerado bem-sucedido apenas porque devolveu algo;
- um passo normativo nao deveria ser considerado suficiente sem confirmar que policy, frontmatter e requisitos de evidencia ficaram claros;
- criterios muito genericos enfraquecem a auditabilidade do fluxo.

Risco pratico:
- um agente pode interpretar qualquer retorno nao vazio como sucesso;
- isso pode reduzir a qualidade da decisao seguinte;
- fica mais dificil medir se a etapa cumpriu seu objetivo semantico.

Melhoria sugerida:
- manter `success_condition` especifico por passo;
- preferir condicoes orientadas a objetivo, por exemplo:
  - identificar ao menos um projeto relevante;
  - encontrar area candidata plausivel;
  - selecionar entre 3 e 6 IDs relevantes;
  - confirmar kind da policy e exigencia de evidencia.

### 4. O catalogo canonico existe, mas ainda nao governa totalmente o comportamento
O modelo planeado favorece um catalogo com regras canonicamente declaradas. Quando a maior parte das decisoes continua embutida na logica procedural, o catalogo perde forca como fonte principal de governanca.

Por que isso nao fecha totalmente:
- mudancas no catalogo nao necessariamente alteram o comportamento real;
- parte da governanca continua escondida na implementacao;
- isso reduz a escalabilidade do modelo hibrido.

Risco pratico:
- divergencia entre o que o catalogo declara e o que a tool faz;
- manutencao mais cara;
- menor flexibilidade para evoluir a taxonomia de cenarios e gatilhos.

Melhoria sugerida:
- mover mais decisao para um motor orientado a catalogo;
- usar a logica procedural apenas para validacao, normalizacao e resolucao de conflitos;
- deixar cenarios, roteamento, evidence gate e fallbacks declarativos sempre que possivel.

## Contratos sugeridos para evolucao

### Contrato de entrada recomendado
```json
{
  "schema_version": "1.0.0",
  "request": {
    "user_goal": "string",
    "operation_mode": "plan_only|analyze_only|implement|refactor|debug|review|unknown",
    "explicit_deliverable": "string|null",
    "ambiguity_level": "low|medium|high|unknown",
    "risk_level": "low|medium|high|unknown",
    "mentions_current_file": true,
    "mentions_specific_files": true,
    "mentions_symbols": true,
    "mentions_cross_cutting_concerns": true,
    "mentions_public_contract": false,
    "mentions_new_infrastructure": false,
    "mentions_external_integration": false,
    "wants_tests": false,
    "wants_only_plan": true
  },
  "workspace": {
    "repo_known": false,
    "current_file_available": false,
    "solution_available": true,
    "project_count_known": false,
    "has_mcp": true,
    "tech_stack_signals": [".NET 8"],
    "workspace_signals_known": false
  },
  "context_state": {
    "repo_structure_loaded": false,
    "current_file_loaded": false,
    "target_files_loaded": false,
    "symbols_loaded": false,
    "mcp_index_loaded": false,
    "mcp_batch_loaded": false,
    "plan_already_created": false
  },
  "constraints": {
    "prefer_plan_first": true,
    "prefer_minimal_context": true,
    "allow_mcp_usage": true,
    "allow_repo_scan": true,
    "max_search_iterations": 5,
    "max_instruction_ids": 6
  }
}
```

### Contrato de evidence gate recomendado para reconciliacao pos-batch
```json
{
  "evidence_gate": {
    "required": true,
    "workspace_evidence_required_detected": false,
    "must_verify_frontmatter": true,
    "must_verify_workspace_signals": false,
    "must_reconcile_after_batch": true,
    "reconciled_workspace_evidence_required": null,
    "apply_policy_without_batch": false,
    "apply_policy_without_repo_evidence": false
  }
}
```

### Contrato recomendado para `tool_sequence`
```json
{
  "tool_sequence": [
    {
      "order": 1,
      "phase": "repo_discovery",
      "tool": "get_projects_in_solution",
      "required": true,
      "why": "repo structure unknown and no explicit target files",
      "expected_output": "project list",
      "success_condition": "at least one project identified"
    },
    {
      "order": 2,
      "phase": "repo_discovery",
      "tool": "get_files_in_project",
      "required": true,
      "why": "enumerate likely target areas",
      "expected_output": "file list in selected project",
      "success_condition": "relevant API/domain/repository files identified"
    },
    {
      "order": 3,
      "phase": "normative_discovery",
      "tool": "corporate_instructions_search_instructions",
      "required": true,
      "why": "cross-cutting concern detected",
      "expected_output": "candidate instruction ids",
      "success_condition": "3 to 6 relevant ids selected"
    },
    {
      "order": 4,
      "phase": "normative_read",
      "tool": "corporate_instructions_get_instructions_batch",
      "required": true,
      "why": "policy cannot be applied from search results alone",
      "expected_output": "instruction bodies and frontmatter",
      "success_condition": "policy kind and evidence requirements known"
    }
  ]
}
```

## Fluxo sugerido para o Copilot analisar estes achados

### Fluxo 1 - Revisao de aderencia ao modelo planeado
1. Ler o `copilot-instructions.md` thin.
2. Ler o contrato de entrada esperado.
3. Ler o contrato de saida esperado.
4. Verificar se a tool realmente devolve:
   - classificacao adequada do cenario;
   - estrategia coerente;
   - tool sequence aderente;
   - evidence gate suficiente;
   - stop rules corretas.
5. Separar o que e aderencia forte e o que e aderencia parcial.

### Fluxo 2 - Revisao do evidence gate
1. Partir de um pedido transversal sem ficheiros explicitos.
2. Executar a orquestracao ate a leitura normativa em batch.
3. Observar se as instructions retornadas exigem `workspace_evidence_required`.
4. Verificar se a saida inicial da tool antecipou corretamente essa necessidade.
5. Propor uma reconciliacao pos-batch quando houver divergencia.

### Fluxo 3 - Revisao da governanca do catalogo
1. Ler o catalogo canonico.
2. Identificar quais decisoes deveriam vir do catalogo.
3. Verificar se os cenarios, roteamentos e regras de evidence gate dependem de configuracao declarativa ou de logica fixa.
4. Propor quais partes devem migrar primeiro para um modelo mais orientado por catalogo.

### Fluxo 4 - Revisao do contrato publicado ao host
1. Verificar como a tool se apresenta para o host.
2. Comparar o contrato planeado com o contrato efetivamente consumivel por outra IA.
3. Avaliar se a interface atual favorece ou dificulta tool calling preciso.
4. Propor uma versao de contrato mais clara e mais validavel.

## Perguntas que valem ser feitas ao Copilot
- A tool exposta esta suficientemente estruturada para outra IA consumi-la com baixa ambiguidade?
- O evidence gate deveria ser preliminar antes do batch e reconciliado depois do batch?
- O `tool_sequence` atual esta detalhado o suficiente para guiar execucao real sem inferencia excessiva?
- O catalogo atual parece fonte de verdade ou apenas apoio documental?
- Qual melhoria produz mais ganho imediato: contrato estruturado, reconciliacao pos-batch ou motor guiado por catalogo?

## Recomendacao final
Se o objetivo for aumentar a confiabilidade do modelo hibrido com o menor custo inicial, a melhoria mais eficiente a analisar primeiro e:

1. manter a tool como decisor principal;
2. adicionar reconciliacao pos-batch do evidence gate;
3. depois evoluir o contrato publicado para algo mais estruturado;
4. por fim, aprofundar a migracao para um motor mais guiado pelo catalogo.

Essa ordem tende a maximizar ganho funcional sem exigir uma reescrita completa do desenho atual.
