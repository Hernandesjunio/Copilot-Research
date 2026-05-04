# Revisão Técnica Detalhada do Fechamento Ponto a Ponto

## Resumo Executivo

O fechamento da outra IA está **tecnicamente forte**, **bem priorizado** e **muito mais próximo de um backlog implementável** do que de uma análise apenas conceitual.

Eu concordo com a maior parte dos pontos, especialmente com:

- a centralidade da **classificação de cenário**;
- a necessidade de um **contrato estruturado publicado ao host**;
- a importância de um **evidence gate em duas fases**;
- a utilidade da **tricotomia do uso de MCP**;
- a evolução gradual para um **motor mais orientado por catálogo**;
- a divisão em fases **P0 / P1 / P2**.

Os pontos em que concordo parcialmente **não estão errados**. O problema neles é outro:

- podem introduzir **subjetividade** se forem definidos cedo demais;
- podem gerar **contrato pesado demais**;
- podem virar **fonte de ambiguidade operacional** se não houver definição formal e testável.

Abaixo segue a análise detalhada, com exemplos de contrato e definições mais explícitas para reduzir risco de interpretação ambígua ou alucinação por outra IA.

---

# 1. Pontos com os quais concordo fortemente

## 1.1 Classificação de cenário como pivô de qualidade

**Concordo fortemente.**

A classificação de cenário é o primeiro ponto de estabilidade do sistema porque dela derivam:

- o modo de execução;
- a necessidade de plano;
- a necessidade de MCP;
- a escolha das tools locais;
- a necessidade de `stop_rules`.

### Risco se isso falhar
Se o sistema classifica errado um caso de `plan_only` como `implement`, o agente pode:

- montar contexto excessivo;
- chamar tools de patch cedo demais;
- tentar editar quando o utilizador pediu apenas análise.

### Exemplo de definição não ambígua

```json
{
  "scenario": {
    "scenario_id": "plan-crosscutting-async-migration",
    "scenario_family": "plan",
    "scenario_confidence": 0.96
  }
}
```

### Regra operacional clara
- `scenario_family = "plan"` **não implica automaticamente** ausência de MCP.
- `scenario_family = "plan"` implica apenas:
  - não executar patch;
  - priorizar descoberta e síntese;
  - produzir plano como saída principal.

---

## 1.2 Estratégia macro como núcleo da utilidade

**Concordo fortemente.**

A tool só tem valor real se devolver uma decisão macro coerente, por exemplo:

- `should_plan_first`
- `should_use_repo_tools_first`
- `should_use_mcp`
- `recommended_execution_mode`

### Exemplo de bloco estratégico

```json
{
  "strategy": {
    "should_plan_first": true,
    "should_use_repo_tools_first": true,
    "should_use_mcp": "required",
    "should_stop_for_human_input": false,
    "recommended_execution_mode": "plan_only"
  }
}
```

### Conceito importante
A estratégia macro deve ser entendida como:

> **a menor decisão suficiente para orientar o comportamento seguinte do agente**

Ela **não** deve:
- executar;
- inferir solução;
- substituir o plano.

---

## 1.3 Tool read-only como requisito arquitetural

**Concordo fortemente.**

A tool `get_context_triggers` deve ser um **decisor de orquestração**, não um executor.

### Não deve fazer
- editar ficheiros;
- chamar build;
- criar plano automaticamente;
- ler batch internamente sem explicitar isso no contrato;
- disparar side effects.

### Deve fazer
- classificar;
- recomendar;
- priorizar;
- sinalizar riscos;
- definir sequenciamento;
- explicitar condições de paragem.

### Conceito explícito para evitar ambiguidade
Adicionar no contrato um campo como:

```json
{
  "tool_contract": {
    "mode": "read_only_decision_support",
    "has_side_effects": false
  }
}
```

Isso reduz risco de outra IA interpretar a tool como um mini-agente executor.

---

## 1.4 Contrato estruturado publicado ao host

**Concordo fortemente.**

Este é um ponto crítico.

Se o host expõe apenas algo como:

```json
{
  "payload": "{...json inteiro em string...}"
}
```

perdes:

- validação nativa de shape;
- melhor completion e discoverability;
- melhor consumo por outra IA;
- melhor documentação operacional;
- maior capacidade de testes automáticos.

### Forma preferível
Expor o contrato com objetos reais:

```json
{
  "request": { "...": "..." },
  "workspace": { "...": "..." },
  "context_state": { "...": "..." },
  "constraints": { "...": "..." }
}
```

### Benefício prático
Outra IA consegue inferir:
- o que precisa preencher;
- o que é opcional;
- o que é booleano;
- o que é enum;
- o que é responsabilidade do chamador.

---

## 1.5 Evidence gate em duas fases

**Concordo fortemente.**

Este é um dos pontos mais importantes do desenho.

### Estrutura correta
O evidence gate deve ser modelado explicitamente em duas fases:

#### Fase 1 — preliminar
Baseada em:
- pedido;
- sinais já conhecidos do repo;
- tipo de operação.

#### Fase 2 — reconciliada
Baseada em:
- `frontmatter`;
- `workspace_evidence_required`;
- `workspace_signals`;
- kind real das instructions lidas em batch.

### Exemplo de contrato melhorado

```json
{
  "evidence_gate": {
    "required": true,
    "phase": "preliminary",
    "workspace_evidence_required_detected": false,
    "must_verify_frontmatter": true,
    "must_verify_workspace_signals": false,
    "must_reconcile_after_batch": true,
    "reconciliation_status": "not_started",
    "reconciliation_reasons": []
  }
}
```

Depois do batch:

```json
{
  "evidence_gate": {
    "required": true,
    "phase": "reconciled",
    "workspace_evidence_required_detected": true,
    "must_verify_frontmatter": true,
    "must_verify_workspace_signals": true,
    "must_reconcile_after_batch": true,
    "reconciliation_status": "completed",
    "reconciliation_reasons": [
      "policy_requires_workspace_evidence",
      "workspace_signals_must_be_checked_before_policy_application"
    ]
  }
}
```

### Regra sem ambiguidade
- `must_reconcile_after_batch = true` significa:
  - o evidence gate preliminar **não é suficiente como decisão final**;
  - a aplicabilidade normativa ainda pode mudar.

---

## 1.6 Tricotomia do uso de MCP

**Concordo fortemente.**

Em vez de:
- `should_use_mcp: true|false`

o melhor é:

```json
{
  "mcp_usage": {
    "level": "required"
  }
}
```

### Valores recomendados
- `required`
- `recommended`
- `not_needed`

### Semântica precisa

#### `required`
Sem MCP a decisão fica normativamente incompleta.

#### `recommended`
MCP melhora segurança/consistência, mas não é estritamente necessário.

#### `not_needed`
A decisão pode ser tomada com contexto local já suficiente.

### Exemplo concreto
#### Caso 1
“corrige esta mensagem no ficheiro atual”
```json
{ "level": "not_needed" }
```

#### Caso 2
“quero um plano para processamento assíncrono”
```json
{ "level": "recommended" }
```

#### Caso 3
“quero alterar política de retry e timeout em integração crítica”
```json
{ "level": "required" }
```

---

## 1.7 `tool_sequence` como recomendação e não workflow engine

**Concordo fortemente.**

A sequência devolvida deve ser entendida como:

> ordem recomendada para recolha de contexto e tomada de decisão

e não como:

> lista de ações obrigatórias executadas cegamente

### Exemplo de contrato mais explícito

```json
{
  "tool_sequence_mode": "recommended_order",
  "tool_sequence": [
    {
      "order": 1,
      "phase": "repo_discovery",
      "tool": "get_projects_in_solution",
      "required": true
    }
  ]
}
```

### Regra importante
- `required=true` não significa “executar mesmo se já tens esse dado”.
- significa “este passo é necessário se a condição contextual ainda não tiver sido satisfeita”.

---

# 2. Pontos com os quais concordo parcialmente

Aqui não há erro conceitual. O ponto é que **precisam de definição operacional mais forte** para não gerar interpretação subjetiva.

---

## 2.1 `success_condition` mais específico

**Concordo com ressalvas.**

### Problema real
Se `success_condition` for genérico demais, por exemplo:
- `returned data`

isso não ajuda.

Se for detalhado demais:
- vira um pseudo-workflow engine;
- aumenta acoplamento;
- dificulta manutenção.

### Melhor formato
Usar condição semântica e observável.

#### Mau exemplo
```json
{
  "success_condition": "tool returned something"
}
```

#### Bom exemplo
```json
{
  "success_condition": "at least one project identified"
}
```

#### Outro bom exemplo
```json
{
  "success_condition": "3 to 6 relevant instruction ids selected"
}
```

### Proposta de contrato não ambíguo

```json
{
  "tool_sequence": [
    {
      "tool": "corporate_instructions_get_instructions_batch",
      "success_condition": "policy kind and evidence requirements known",
      "failure_effect": "policy_cannot_be_applied_yet",
      "fallback_on_failure": "request_additional_batch_or_stop"
    }
  ]
}
```

### Ponto de atenção
`success_condition` deve medir:
- **objetivo da etapa**,
não
- microdetalhe de implementação.

---

## 2.2 `decision_stability`

**Concordo com ressalvas.**

A ideia é boa, mas sem definição vira opinião.

### Definição operacional recomendada
`decision_stability` deve medir **repetibilidade observada** da saída em variações lexicais equivalentes do mesmo pedido.

### Exemplo de contrato

```json
{
  "decision_stability": {
    "level": "medium",
    "basis": "observed_repeatability",
    "measured_on": 5,
    "stable_fields": [
      "scenario.scenario_family",
      "strategy.recommended_execution_mode",
      "mcp_usage.level"
    ],
    "unstable_fields": [
      "tool_sequence"
    ]
  }
}
```

### Escala sugerida
- `high`
  - campos centrais repetem de forma estável
- `medium`
  - classificação e estratégia repetem, mas sequência oscila
- `low`
  - classificação ou estratégia oscilam demais

### Ponto de atenção
Não usar `decision_stability` como intuição do modelo.  
Usar apenas como resultado de bateria de teste.

---

## 2.3 `plan_granularity`

**Concordo com ressalvas.**

É útil, mas só com rubrica fechada.

### Definição recomendada

```json
{
  "plan_granularity": "minimal"
}
```

### Semântica proposta

#### `minimal`
- bug local;
- ajuste pequeno;
- baixo risco;
- poucos ficheiros.

#### `standard`
- feature média;
- algum impacto transversal;
- necessidade de validação intermediária.

#### `detailed`
- arquitetura;
- migração;
- refatoração multi-step;
- contrato público;
- múltiplos sistemas;
- risco elevado.

### Regra não ambígua

```json
{
  "plan_granularity_rule": {
    "if": {
      "operation_mode": "plan_only",
      "risk_level": "high"
    },
    "then": "detailed"
  }
}
```

### Ponto de atenção
Não introduzir antes de estabilizar:
- classificação;
- strategy;
- evidence gate.

---

## 2.4 Priorização por objetivo da rodada

**Concordo com ressalvas positivas.**

Isto é correto, mas precisa ficar explícito.

### Exemplo de contrato da rodada experimental

```json
{
  "evaluation_profile": {
    "primary_goal": "interoperability",
    "secondary_goal": "safety"
  }
}
```

Ou:

```json
{
  "evaluation_profile": {
    "primary_goal": "safety",
    "secondary_goal": "interoperability"
  }
}
```

### Por quê
Sem isso, duas avaliações podem divergir sem que nenhuma esteja errada.

### Ponto de atenção
A rodada precisa declarar formalmente:
- o que está sendo otimizado.

---

# 3. Pontos de atenção que merecem reforço adicional

---

## 3.1 Separar claramente três níveis de verdade

Este ponto não está suficientemente explícito no fechamento.

### Recomendo separar:

#### 1. Contrato publicado ao host
O que outra IA consegue chamar e validar.

#### 2. Lógica interna da tool
Heurísticas, normalização, defaults, resolução de conflitos.

#### 3. Catálogo declarativo
Fonte canónica de cenários, roteamento, stop rules, fallback e evidence gate declarativo.

### Exemplo de decomposição

```json
{
  "published_contract": {
    "request": {},
    "workspace": {},
    "context_state": {},
    "constraints": {}
  },
  "internal_derivations": {
    "normalized_request": {},
    "derived_signals": {}
  },
  "catalog_rules_applied": [
    "repo-discovery-for-vague-request",
    "cross-cutting-needs-mcp"
  ]
}
```

### Ganho
Isto reduz ambiguidade em:
- testes;
- debugging;
- governança.

---

## 3.2 Separar origem dos sinais

Isto é muito importante para evitar alucinação e melhorar explainability.

### Tipos de sinal

#### `request_declared_signals`
Sinais inferidos a partir do pedido do utilizador.

#### `repo_observed_signals`
Sinais extraídos do workspace.

#### `batch_discovered_signals`
Sinais que só aparecem após leitura normativa.

### Exemplo de contrato

```json
{
  "signal_sources": {
    "request_declared_signals": [
      "cross_cutting_concern",
      "plan_only"
    ],
    "repo_observed_signals": [
      "solution_available",
      "current_file_unavailable"
    ],
    "batch_discovered_signals": [
      "workspace_evidence_required",
      "policy_kind_detected"
    ]
  }
}
```

### Ganho
Permite saber:
- o que veio do utilizador;
- o que veio do repo;
- o que veio do corpus.

---

## 3.3 Adicionar invariantes negativas no contrato dos testes

Isto precisa de maior ênfase.

### Exemplos importantes

#### Invariante 1
Se `recommended_execution_mode = "plan_only"`, então:
- `tool_sequence` não pode conter tool mutável;
- `strategy.should_plan_first = true`

#### Invariante 2
Se `mcp_usage.level = "not_needed"`, então:
- `mcp_context_triggers.batch_required = false`

#### Invariante 3
Se `stop_rules.stop_required = true`, então:
- `stop_rules.stop_reasons.length > 0`

#### Invariante 4
Se `evidence_gate.workspace_evidence_required_detected = true`, então:
- após reconciliação:
  - `must_verify_workspace_signals = true`

### Exemplo em JSON de contrato de teste

```json
{
  "negative_invariants": [
    {
      "if": {
        "strategy.recommended_execution_mode": "plan_only"
      },
      "then_not": [
        "tool_sequence_contains_mutating_tool"
      ]
    },
    {
      "if": {
        "mcp_usage.level": "not_needed"
      },
      "then": {
        "mcp_context_triggers.batch_required": false
      }
    }
  ]
}
```

---

## 3.4 Diferenciar confidence por camada

Hoje `scenario_confidence` é útil, mas insuficiente.

### Melhor estrutura

```json
{
  "confidence": {
    "scenario_confidence": 0.96,
    "strategy_confidence": 0.90,
    "evidence_gate_confidence": 0.72,
    "stop_rule_confidence": 0.88
  }
}
```

### Ganho
Evita conclusões erradas como:
- “o cenário foi classificado com alta confiança, então a aplicabilidade normativa também é alta”.

Nem sempre isso é verdade.

---

# 4. Proposta de contrato mais robusto e menos ambíguo

Abaixo está um exemplo consolidado com vários refinamentos discutidos.

```json
{
  "schema_version": "1.1.0",
  "scenario": {
    "scenario_id": "feature-vague-crosscutting",
    "scenario_family": "feature",
    "scenario_confidence": 0.94
  },
  "strategy": {
    "should_plan_first": true,
    "should_use_repo_tools_first": true,
    "should_stop_for_human_input": false,
    "recommended_execution_mode": "plan_then_context_then_decide_then_execute",
    "plan_granularity": "standard"
  },
  "mcp_usage": {
    "level": "required",
    "reason_codes": [
      "cross_cutting_policy_domain_detected",
      "public_contract_risk"
    ]
  },
  "tool_sequence_mode": "recommended_order",
  "tool_sequence": [
    {
      "order": 1,
      "phase": "repo_discovery",
      "tool": "get_projects_in_solution",
      "required": true,
      "why": "repo structure unknown and no explicit target files",
      "expected_output": "project list",
      "success_condition": "at least one project identified",
      "failure_effect": "repo_scope_unknown",
      "fallback_on_failure": "request_repo_context_or_stop"
    }
  ],
  "evidence_gate": {
    "required": true,
    "phase": "preliminary",
    "workspace_evidence_required_detected": false,
    "must_verify_frontmatter": true,
    "must_verify_workspace_signals": false,
    "must_reconcile_after_batch": true,
    "reconciliation_status": "not_started",
    "reconciliation_reasons": [],
    "apply_policy_without_batch": false,
    "apply_policy_without_repo_evidence": false
  },
  "signal_sources": {
    "request_declared_signals": [
      "cross_cutting_concern",
      "public_contract_risk"
    ],
    "repo_observed_signals": [
      "solution_available"
    ],
    "batch_discovered_signals": []
  },
  "confidence": {
    "scenario_confidence": 0.94,
    "strategy_confidence": 0.90,
    "evidence_gate_confidence": 0.70,
    "stop_rule_confidence": 0.88
  }
}
```

---

# 5. Julgamento final

## Veredito técnico
O fechamento da outra IA é **tecnicamente sólido, útil e acionável**.

## O que está melhor nele
- melhor faseamento;
- melhor foco em implementabilidade;
- boa priorização entre contrato, safety e governança;
- cautela correta com métricas subjetivas.

## O que eu reforçaria antes de implementar
1. separar melhor:
   - contrato publicado;
   - lógica interna;
   - catálogo declarativo;

2. explicitar origem dos sinais;

3. formalizar invariantes negativas;

4. adicionar confidence por camada;

5. tratar `plan_granularity` e `decision_stability` como evoluções controladas, não como base inicial.

## Conclusão final
**Sim, o documento faz sentido e pode servir como base real para backlog de implementação e testes.**  
Com os refinamentos acima, ele fica ainda mais adequado para leitura por outra IA e menos sujeito a interpretações ambíguas ou alucinação.
