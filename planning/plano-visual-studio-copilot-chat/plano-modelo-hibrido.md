# Plano detalhado para cenário híbrido: `get_context_triggers` + resource canónico + `copilot-instructions.md` minimalista

## Premissa arquitetural

Objetivo: deslocar a lógica de **gatilhos de montagem de contexto** para o MCP, mantendo o `.github/copilot-instructions.md` **thin**, distribuível e agnóstico à demanda.

### Modelo recomendado
1. **Tool MCP**: `get_context_triggers`
2. **Resource MCP**: catálogo canónico de orquestração
3. **`copilot-instructions.md` local**: fino, com precedência, regras de paragem e uso obrigatório da tool

### Motivação
Este modelo separa três camadas:

- **Camada 1 — repo local**
  - restrições locais
  - precedência
  - guardrails mínimos
- **Camada 2 — MCP tool**
  - decisão dinâmica de orquestração
  - seleção de tools
  - necessidade de plano
  - necessidade de MCP normativo
- **Camada 3 — MCP resource**
  - taxonomia canónica
  - definições de cenário
  - regras estáveis
  - catálogo versionado

---

# 1. Plano detalhado do contrato JSON ideal da tool `get_context_triggers`

## 1.1 Objetivo funcional da tool

A tool `get_context_triggers` deve responder à pergunta:

> “Dado este pedido, este estado de contexto e estes sinais do workspace, qual deve ser a estratégia de montagem de contexto e qual a sequência ótima de tools antes de responder, planear ou executar?”

Ela **não** deve:
- implementar;
- aplicar patch;
- decidir policy final;
- substituir `search_instructions`/`get_instructions_batch`.

Ela deve:
- classificar o cenário;
- definir sequência de descoberta;
- indicar quando planear;
- indicar quando usar MCP;
- indicar quando parar;
- indicar evidência mínima a recolher.

## 1.2 Requisitos do contrato

O contrato deve ser:

- **estritamente estruturado**
- **machine-readable**
- **estável**
- **versionado**
- **explicável**
- **não ambíguo**
- **independente de stack específica**
- **capaz de suportar heurística dinâmica**
- **capaz de ser expandido sem breaking changes**

## 1.3 Estrutura do input JSON

### JSON de entrada — visão geral

```json
{
  "schema_version": "1.0.0",
  "request": {
    "user_goal": "string",
    "operation_mode": "analyze_only|plan_only|implement|refactor|debug|review|unknown",
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
    "wants_tests": true,
    "wants_only_plan": false
  },
  "workspace": {
    "repo_known": true,
    "current_file_available": true,
    "solution_available": true,
    "project_count_known": true,
    "has_mcp": true,
    "tech_stack_signals": [
      ".NET 8",
      "ASP.NET Core",
      "Minimal API",
      "Dapper"
    ],
    "workspace_signals_known": true
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

## 1.4 Semântica de cada campo de entrada

### `schema_version`
- tipo: `string`
- obrigatório
- finalidade: versionamento do contrato

### `request.user_goal`
- tipo: `string`
- obrigatório
- conteúdo: pedido bruto resumido ou o prompt do utilizador

### `request.operation_mode`
- enum obrigatório
- valores:
  - `analyze_only`
  - `plan_only`
  - `implement`
  - `refactor`
  - `debug`
  - `review`
  - `unknown`

### `request.explicit_deliverable`
- tipo: `string|null`
- exemplo:
  - `markdown report`
  - `implementation plan`
  - `code fix`
  - `null`

### `request.ambiguity_level`
- enum:
  - `low`
  - `medium`
  - `high`
  - `unknown`

### `request.risk_level`
- enum:
  - `low`
  - `medium`
  - `high`
  - `unknown`

### `request.mentions_current_file`
- boolean
- verdadeiro quando há referência ao ficheiro atual ou seleção atual

### `request.mentions_specific_files`
- boolean
- verdadeiro quando o pedido cita ficheiros concretos

### `request.mentions_symbols`
- boolean
- verdadeiro quando o pedido cita classes, métodos, interfaces ou outros símbolos

### `request.mentions_cross_cutting_concerns`
- boolean
- verdadeiro quando há tema transversal:
  - segurança
  - contrato API
  - dados
  - testes
  - mensageria
  - observabilidade
  - resiliência
  - estilo/policy

### `request.mentions_public_contract`
- boolean
- verdadeiro quando pode alterar endpoint, payload, status code, schema, contrato externo

### `request.mentions_new_infrastructure`
- boolean
- verdadeiro quando há broker, observabilidade, cache, filas, storage novo, etc.

### `request.mentions_external_integration`
- boolean
- verdadeiro quando envolve sistemas externos

### `request.wants_tests`
- boolean

### `request.wants_only_plan`
- boolean

### `workspace.repo_known`
- boolean
- indica se já existe algum conhecimento estrutural do repo

### `workspace.current_file_available`
- boolean

### `workspace.solution_available`
- boolean

### `workspace.project_count_known`
- boolean

### `workspace.tech_stack_signals`
- array de strings
- sinais já conhecidos do stack

### `workspace.workspace_signals_known`
- boolean
- indica se já foram recolhidos sinais suficientes do repo

### `context_state.*`
Campos booleanos que indicam o que já foi carregado.
Finalidade: evitar overfetch e tool-calling redundante.

### `constraints.prefer_plan_first`
- boolean
- regra de orquestração local

### `constraints.prefer_minimal_context`
- boolean
- indica preferência por contexto suficiente, não máximo

### `constraints.allow_mcp_usage`
- boolean

### `constraints.allow_repo_scan`
- boolean

### `constraints.max_search_iterations`
- integer

### `constraints.max_instruction_ids`
- integer

## 1.5 Estrutura do output JSON

### JSON de saída — visão geral

```json
{
  "schema_version": "1.0.0",
  "scenario": {
    "scenario_id": "feature-vague-crosscutting",
    "scenario_family": "feature|bugfix|analysis|plan|review|migration|unknown",
    "scenario_confidence": 0.94
  },
  "strategy": {
    "should_plan_first": true,
    "should_use_repo_tools_first": true,
    "should_use_mcp": true,
    "should_stop_for_human_input": false,
    "should_ask_for_clarification_before_patch": false,
    "recommended_execution_mode": "plan_then_context_then_decide_then_execute"
  },
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
  ],
  "repo_context_triggers": {
    "must_read_current_file": false,
    "must_scan_solution": true,
    "must_scan_projects": true,
    "must_search_symbols": false,
    "must_search_concepts": true
  },
  "mcp_context_triggers": {
    "triggered": true,
    "reasons": [
      "cross_cutting_policy_domain_detected",
      "public_contract_risk"
    ],
    "retrieve_mode": "search",
    "search_query_count_min": 3,
    "search_query_count_max": 5,
    "max_instruction_ids": 6,
    "batch_required": true
  },
  "evidence_gate": {
    "required": true,
    "workspace_evidence_required_detected": true,
    "must_verify_frontmatter": true,
    "must_verify_workspace_signals": true,
    "apply_policy_without_batch": false,
    "apply_policy_without_repo_evidence": false
  },
  "decision_output_requirements": {
    "must_label_fact_vs_hypothesis": true,
    "must_produce_bmad": true,
    "must_build_evidence_matrix": true,
    "must_cite_instruction_ids": true
  },
  "stop_rules": {
    "stop_required": false,
    "stop_reasons": [],
    "human_input_required_if": [
      "public_contract_change_without_evidence",
      "new_infrastructure_without_evidence",
      "external_integration_without_evidence",
      "public_technical_endpoint_creation",
      "new_observability_stack"
    ]
  },
  "fallbacks": {
    "when_no_policy_found": "follow_repo_and_label_gap",
    "when_only_reference_found": "follow_repo_pattern_with_caveat",
    "when_workspace_evidence_missing": "do_not_introduce_stack_by_inference"
  },
  "anti_patterns": [
    "mcp_by_ritual",
    "search_without_batch",
    "repo_skip_with_vague_request",
    "edit_before_read",
    "implement_when_user_requested_plan_only"
  ],
  "explanation": {
    "short_rationale": "Cross-cutting change with no explicit files requires repo discovery, MCP retrieval and evidence gate before planning.",
    "machine_summary": "plan_first=true; repo_tools_first=true; mcp_required=true; batch_required=true; stop_required=false"
  }
}
```

## 1.6 Campos obrigatórios do output

### `scenario`
Classifica o caso atual.

Campos:
- `scenario_id`
- `scenario_family`
- `scenario_confidence`

### `strategy`
Define a decisão macro.

Campos mínimos:
- `should_plan_first`
- `should_use_repo_tools_first`
- `should_use_mcp`
- `should_stop_for_human_input`
- `recommended_execution_mode`

### `tool_sequence`
Lista ordenada de tools.

Cada item deve conter:
- `order`
- `phase`
- `tool`
- `required`
- `why`
- `expected_output`
- `success_condition`

### `repo_context_triggers`
Define o que precisa ser carregado localmente.

### `mcp_context_triggers`
Define se MCP entra, porquê e com que limites.

### `evidence_gate`
Define as regras de aplicabilidade antes de impor policy.

### `decision_output_requirements`
Define obrigações da resposta do agente.

### `stop_rules`
Define se deve parar e quais condições exigem input humano.

### `fallbacks`
Define comportamento controlado quando o MCP ou repo não fecham a decisão.

### `anti_patterns`
Lista de comportamentos proibidos.

### `explanation`
Resumo para debugging e observabilidade da tool.

## 1.7 Enums recomendados

### `scenario_family`
```json
[
  "feature",
  "bugfix",
  "analysis",
  "plan",
  "review",
  "migration",
  "debug",
  "refactor",
  "unknown"
]
```

### `recommended_execution_mode`
```json
[
  "plan_then_context_then_decide_then_execute",
  "context_then_plan_then_execute",
  "context_then_answer",
  "plan_only",
  "analysis_only",
  "stop_and_request_human_input"
]
```

### `phase`
```json
[
  "request_interpretation",
  "repo_discovery",
  "repo_read",
  "symbol_lookup",
  "concept_search",
  "normative_discovery",
  "normative_selection",
  "normative_read",
  "evidence_gate",
  "planning",
  "validation"
]
```

## 1.8 Regras não ambíguas para a tool

### Regra 1
Se `request.wants_only_plan=true`, então:
- `strategy.should_plan_first=true`
- `recommended_execution_mode="plan_only"`
- `tool_sequence` não deve incluir tools de edição

### Regra 2
Se `mentions_current_file=true`, então:
- `get_currentfile` deve aparecer antes de qualquer edição

### Regra 3
Se `mentions_specific_files=false` e `repo_known=false`, então:
- `get_projects_in_solution` deve entrar na sequência

### Regra 4
Se `mentions_cross_cutting_concerns=true`, então:
- `should_use_mcp=true`

### Regra 5
Se `should_use_mcp=true`, então:
- `corporate_instructions_get_instructions_batch` deve ser obrigatório antes da aplicação de policy

### Regra 6
Se alguma instruction tiver `workspace_evidence_required=true`, então:
- `evidence_gate.must_verify_workspace_signals=true`

### Regra 7
Se `mentions_public_contract=true` e `workspace_signals_known=false`, então:
- `should_plan_first=true`
- `should_stop_for_human_input` pode ser `true` dependendo do risco

### Regra 8
Se `mentions_new_infrastructure=true` e não houver sinais do repo, então:
- `fallbacks.when_workspace_evidence_missing="do_not_introduce_stack_by_inference"`
- potencialmente `stop_required=true`

## 1.9 Exemplo de input/output — cenário “plano detalhado”

### Input
```json
{
  "schema_version": "1.0.0",
  "request": {
    "user_goal": "quero um plano detalhado para migrar este fluxo para processamento assíncrono",
    "operation_mode": "plan_only",
    "explicit_deliverable": "detailed plan",
    "ambiguity_level": "medium",
    "risk_level": "medium",
    "mentions_current_file": false,
    "mentions_specific_files": false,
    "mentions_symbols": false,
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

### Output esperado
```json
{
  "schema_version": "1.0.0",
  "scenario": {
    "scenario_id": "plan-crosscutting-async-migration",
    "scenario_family": "plan",
    "scenario_confidence": 0.96
  },
  "strategy": {
    "should_plan_first": true,
    "should_use_repo_tools_first": true,
    "should_use_mcp": true,
    "should_stop_for_human_input": false,
    "should_ask_for_clarification_before_patch": false,
    "recommended_execution_mode": "plan_only"
  },
  "repo_context_triggers": {
    "must_read_current_file": false,
    "must_scan_solution": true,
    "must_scan_projects": true,
    "must_search_symbols": false,
    "must_search_concepts": true
  },
  "mcp_context_triggers": {
    "triggered": true,
    "reasons": [
      "cross_cutting_policy_domain_detected"
    ],
    "retrieve_mode": "resolve_or_search",
    "search_query_count_min": 3,
    "search_query_count_max": 5,
    "max_instruction_ids": 6,
    "batch_required": true
  },
  "decision_output_requirements": {
    "must_label_fact_vs_hypothesis": true,
    "must_produce_bmad": true,
    "must_build_evidence_matrix": true,
    "must_cite_instruction_ids": true
  }
}
```

# 2. Estrutura ideal do resource canónico

## 2.1 Função do resource

O resource deve ser a **fonte canónica estável** que explica:
- taxonomia de cenários;
- gatilhos;
- regras de seleção de tools;
- regras de evidence gate;
- regras de stop;
- regras de fallback.

A tool `get_context_triggers` usa esta semântica como base.

## 2.2 Formato recomendado do resource

### Recomendação principal
Usar **JSON canónico** como formato primário.

### Opcional
Gerar um espelho em Markdown para inspeção humana.

### Motivo
Para leitura por outra IA, o melhor artefacto é:
- menos narrativo;
- mais estruturado;
- semanticamente estável;
- fácil de versionar e validar.

## 2.3 Nome sugerido do resource

Exemplos:
- `context-orchestration-catalog.json`
- `agent-context-trigger-catalog.json`
- `tool-routing-playbook.json`

## 2.4 Estrutura recomendada do resource JSON

```json
{
  "schema_version": "1.0.0",
  "resource_id": "context-orchestration-catalog",
  "title": "Catálogo canónico de gatilhos de contexto e roteamento de tools",
  "status": "active",
  "owner": "platform-architecture",
  "last_reviewed": "2026-05-03",
  "purpose": {
    "primary_goal": "define scenario classification and tool-routing rules for AI assistants",
    "scope": "multi-repo, multi-team, repo-agnostic orchestration"
  },
  "global_rules": {
    "repo_is_fact": true,
    "mcp_policy_requires_batch": true,
    "inference_must_be_labeled": true,
    "plan_before_execution_when_non_trivial": true
  },
  "scenario_taxonomy": [],
  "tool_routing_rules": [],
  "evidence_gate_rules": [],
  "stop_rules": [],
  "fallback_rules": [],
  "anti_patterns": [],
  "output_contract_templates": {},
  "examples": [],
  "change_log": []
}
```

## 2.5 Secções obrigatórias do resource

### `global_rules`
Regras universais de precedência.

### `scenario_taxonomy`
Lista de cenários classificados.

Exemplo:
```json
{
  "scenario_id": "feature-vague-crosscutting",
  "family": "feature",
  "signals": [
    "no_explicit_files",
    "cross_cutting_domain",
    "implementation_requested"
  ],
  "default_strategy": {
    "plan_first": true,
    "repo_tools_first": true,
    "mcp_required": true
  }
}
```

### `tool_routing_rules`
Regras declarativas de qual tool usar em qual condição.

Exemplo:
```json
{
  "rule_id": "use-currentfile-when-current-file-mentioned",
  "if": {
    "mentions_current_file": true
  },
  "then": {
    "prepend_tool": "get_currentfile"
  }
}
```

### `evidence_gate_rules`
Regras específicas para aplicar policies.

Exemplo:
```json
{
  "rule_id": "batch-required-before-policy",
  "if": {
    "uses_mcp_policy": true
  },
  "then": {
    "require_batch": true,
    "allow_policy_without_batch": false
  }
}
```

### `stop_rules`
Regras que exigem input humano.

### `fallback_rules`
Comportamento em lacuna de corpus ou de evidência.

### `anti_patterns`
Lista canónica de comportamentos proibidos.

### `output_contract_templates`
Templates esperados para:
- matriz mínima;
- BMAD;
- resumo machine-readable.

### `examples`
Exemplos de input/output de `get_context_triggers`.

### `change_log`
Histórico de evolução do catálogo.

## 2.6 Exemplo de `scenario_taxonomy`

```json
[
  {
    "scenario_id": "bug-current-file-local",
    "family": "bugfix",
    "signals": [
      "mentions_current_file",
      "local_scope",
      "no_cross_cutting_concern"
    ],
    "default_strategy": {
      "plan_first": true,
      "repo_tools_first": true,
      "mcp_required": false
    }
  },
  {
    "scenario_id": "plan-crosscutting-architecture",
    "family": "plan",
    "signals": [
      "cross_cutting_domain",
      "analysis_or_plan_only"
    ],
    "default_strategy": {
      "plan_first": true,
      "repo_tools_first": true,
      "mcp_required": true
    }
  },
  {
    "scenario_id": "feature-vague-repo-discovery",
    "family": "feature",
    "signals": [
      "no_explicit_files",
      "implementation_requested"
    ],
    "default_strategy": {
      "plan_first": true,
      "repo_tools_first": true,
      "mcp_required": "conditional"
    }
  }
]
```

## 2.7 Exemplo de `tool_routing_rules`

```json
[
  {
    "rule_id": "repo-discovery-for-vague-request",
    "priority": 100,
    "if": {
      "mentions_specific_files": false,
      "repo_known": false
    },
    "then": {
      "append_tools": [
        "get_projects_in_solution",
        "get_files_in_project"
      ]
    }
  },
  {
    "rule_id": "current-file-shortcut",
    "priority": 110,
    "if": {
      "mentions_current_file": true
    },
    "then": {
      "prepend_tools": [
        "get_currentfile"
      ]
    }
  },
  {
    "rule_id": "cross-cutting-needs-mcp",
    "priority": 120,
    "if": {
      "mentions_cross_cutting_concerns": true
    },
    "then": {
      "append_tools": [
        "corporate_instructions_search_instructions",
        "corporate_instructions_get_instructions_batch"
      ]
    }
  }
]
```

## 2.8 Exemplo de `evidence_gate_rules`

```json
[
  {
    "rule_id": "policy-needs-batch",
    "if": {
      "mcp_policy_candidate_found": true
    },
    "then": {
      "require_batch": true,
      "allow_policy_without_batch": false
    }
  },
  {
    "rule_id": "workspace-evidence-check",
    "if": {
      "workspace_evidence_required": true
    },
    "then": {
      "require_workspace_signals": true,
      "allow_stack_introduction_without_evidence": false
    }
  }
]
```

## 2.9 Recomendação de governança do resource

### Deve ter:
- `schema_version`
- `resource_id`
- `owner`
- `status`
- `last_reviewed`

### Deve ser validado por:
- JSON Schema
- teste de consistência semântica
- verificação de enums e regras contraditórias

### Deve evitar:
- narrativa longa
- explicações abertas
- texto promocional
- decisões implícitas

# 3. Versão minimalista do `copilot-instructions.md` para o novo cenário híbrido

Abaixo está a versão minimalista recomendada para o modelo:
**thin local + tool dinâmica + resource canónico**.

## Proposta de `copilot-instructions.md`

```markdown
# Instruções locais

- Responde em português.
- Nunca exponhas segredos, tokens ou PII.
- Não assumas serviços, infraestrutura ou integrações sem evidência no repo.

## Objetivo local

Ser um orquestrador **thin**, agnóstico à demanda, que monta contexto antes de agir e privilegia planeamento antes da execução.

## Ordem de decisão

1. Repo lido = facto.
2. MCP lido em batch = norma aplicável.
3. Inferência = hipótese rotulada.

## Protocolo local

1. **Entender**
   - Resume pedido, escopo, ambiguidades e risco de inferência.
   - Se a tarefa não for trivial, cria plano antes de executar.

2. **Montar contexto**
   - Usa tools locais para contexto do repo.
   - Usa a tool MCP `get_context_triggers` para decidir a sequência ideal de montagem de contexto e planeamento.
   - Se o tema for transversal, segue também os gatilhos normativos devolvidos pela tool.

3. **Aplicar evidence gate**
   - Sem batch lido, não apliques policy do corpus.
   - Se `workspace_evidence_required=true`, procura `workspace_signals` no repo antes de aplicar.
   - Sem evidência suficiente, trata como hipótese e não introduzas infraestrutura nova por inferência.

4. **Planear e executar**
   - Produz plano antes da execução quando houver múltiplos passos, ambiguidade, investigação ou impacto transversal.
   - Lê o alvo antes do patch.
   - Faz build/testes após alterações relevantes.
   - Declara ausência de testes quando aplicável.

## Stop rules

Pára e pede input humano se a lacuna tocar:
- contrato público;
- infraestrutura nova;
- observabilidade nova;
- endpoint técnico público;
- integração externa.

## Fallbacks

- Sem policy aplicável -> seguir o repo e declarar a lacuna.
- Apenas `reference` -> seguir o padrão do repo.
- Sem sinais para stack concreta -> não introduzir por inferência.

## Anti-padrões

- MCP por ritual.
- Overfetch sem ganho decisório.
- Citar ids não lidos.
- Implementar por conveniência em vez de pedido.
```

# 4. Fluxo operacional recomendado para outra IA

## 4.1 Fluxo ideal com o modelo híbrido

### Sequência de alto nível
1. Ler `copilot-instructions.md`
2. Interpretar o pedido
3. Chamar `get_context_triggers`
4. Executar a sequência devolvida pela tool
5. Se MCP normativo for exigido:
   - retrieve
   - select
   - batch
6. Aplicar evidence gate
7. Produzir plano
8. Executar ou responder

## 4.2 Fluxo em pseudo-algoritmo

```plaintext
INPUT: user_request, workspace_state, local_instructions

STEP 1: parse local_instructions
STEP 2: classify if task is trivial or non-trivial
STEP 3: call get_context_triggers(request, workspace_state, constraints)
STEP 4: execute tool_sequence in returned order
STEP 5: if should_use_mcp=true then ensure batch read before policy application
STEP 6: perform evidence gate
STEP 7: if stop_required=true then request human input
STEP 8: if should_plan_first=true then produce plan/BMAD
STEP 9: execute, validate, or answer according to recommended_execution_mode
```

# 5. Revisão crítica de cada ponto para leitura por outra IA

## 5.1 Revisão do contrato JSON da tool

### Pontos fortes
- estrutura explícita;
- separação clara entre input e output;
- enums fechados;
- regras de precedência explícitas;
- tool sequence ordenada;
- evita ambiguidade interpretativa.

### Riscos remanescentes
- `ambiguity_level` e `risk_level` podem variar entre classificadores;
- alguns cenários mistos podem cair entre `plan` e `analysis`;
- input demasiado livre em `user_goal` pode gerar classificação inconsistente.

### Mitigação
- manter `scenario_taxonomy` forte no resource;
- usar `scenario_confidence`;
- permitir `unknown` de forma explícita;
- preferir enum + sinais booleanos a análise puramente textual.

### Julgamento
**Adequado para leitura por IA**.

## 5.2 Revisão da estrutura do resource

### Pontos fortes
- centraliza taxonomia;
- permite governança multi-time;
- desacopla playbook canónico do repo local;
- permite versionamento e validação automática.

### Riscos remanescentes
- resource muito narrativo degrada consumo por IA;
- regras contraditórias entre `tool_routing_rules` e `fallback_rules` podem surgir;
- se o resource crescer demasiado, a tool pode ficar melhor do que o próprio resource como interface primária.

### Mitigação
- JSON canónico;
- schema validation;
- tests de consistência;
- change log explícito;
- examples versionados.

### Julgamento
**Altamente recomendado para IA** se o formato primário for JSON.

## 5.3 Revisão da versão minimalista do `copilot-instructions.md`

### Pontos fortes
- thin;
- distribuível;
- repo-specific apenas no essencial;
- mantém precedência;
- mantém stop rules;
- mantém fallback;
- delega dinâmica para o MCP.

### Riscos remanescentes
- depende da existência e qualidade da tool `get_context_triggers`;
- se a tool falhar ou não existir, o ficheiro local precisa ainda ser suficiente para fallback;
- `usa tools locais para contexto do repo` é correto, mas menos explícito do que listar todas as tools.

### Mitigação
- manter tool `get_context_triggers` estável e versionada;
- manter fallbacks locais;
- opcionalmente incluir uma linha com:
  - “na ausência da tool, usar `get_projects_in_solution`, `get_files_in_project`, `get_currentfile`, `find_symbol`, `code_search`, `get_file` conforme o caso”.

### Julgamento
**Boa versão minimalista para IA**, desde que o modelo híbrido exista de facto.

# 6. Recomendação final

## Recomendação principal
Implementar o modelo híbrido:

- **Tool**: `get_context_triggers`
- **Resource**: `context-orchestration-catalog.json`
- **Local**: `copilot-instructions.md` mínimo

## Prioridade de implementação
1. desenhar e fixar o contrato JSON da tool;
2. criar o resource canónico;
3. ajustar o `copilot-instructions.md` local para delegar gatilhos;
4. criar cenários de teste do roteamento;
5. validar contra múltiplos modelos.

## Veredito técnico
Este desenho é **mais governável, mais flexível e mais escalável** do que codificar todos os gatilhos diretamente no `copilot-instructions.md`.
