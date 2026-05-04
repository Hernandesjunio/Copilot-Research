# Especificação Final — Evolução Incremental do MCP Normativo `corporate_instructions*`

## 1. Objetivo

Este documento define a especificação final, incremental e implementável para evoluir o MCP normativo do projeto, com foco em:

- aumentar a utilidade do MCP para orquestração por outra IA/orquestrador;
- reduzir ambiguidades e risco de alucinação;
- preservar compatibilidade com o servidor atual;
- concentrar o esforço apenas no domínio `corporate_instructions*`;
- entregar rapidamente mecanismos testáveis para validar se os pontos levantados realmente melhoram a orquestração.

O objetivo principal desta evolução e desta especificação e:

> fortalecer o MCP atual com um evidence gate formal e uma matrix operacional mínima, sem regressão das capacidades já existentes, para permitir nova validação prática pela outra IA.

---

## 2. Escopo e premissas

### 2.1 Escopo implementável

Apenas o domínio lógico `corporate_instructions*` está sob controle de evolução.

Estão fora de escopo:

- tools sistêmicas/plataforma;
- IDE/UI;
- leitura nativa de ficheiros do host;
- busca semântica sistêmica;
- build/run/test tools do host;
- alterações profundas no corpus para introduzir templates complexos.

### 2.2 Convenção de prefixo

O prefixo `corporate_instructions_*` deve ser tratado como convenção operacional do cliente/orquestrador.

Exemplo:

- chamada externa: `corporate_instructions_search_instructions`
- implementação real do servidor: `search_instructions`

Isso **não** é, por si só, um bug confirmado do servidor MCP.

### 2.3 Tipo de evolução desejada

Na primeira entrega, as mudanças devem ser:

- aditivas;
- retrocompatíveis;
- incrementalmente verificáveis;
- conservadoras na inferência;
- suficientes para teste com a outra IA.

### 2.4 Regra geral anti-alucinação

Na dúvida:

- preferir incerteza explícita;
- não promover hipótese a conformidade;
- não promover ausência de evidência a não conformidade;
- não misturar aplicabilidade com conformidade.

---

## 3. Estado atual confirmado do servidor

O servidor já expõe as seguintes tools MCP reais:

- `list_instructions_index`
- `search_instructions`
- `get_instructions_batch`
- `resolve_instruction_context`
- `get_context_triggers`
- `get_normative_checklist`
- `detect_instruction_conflicts`

### 3.1 Capacidades já existentes

#### `list_instructions_index`

Já retorna:

- instruções indexadas;
- `count`;
- `by_tag`;
- `corpus_version`.

#### `search_instructions`

Já retorna:

- busca textual com expansão por sinônimos;
- filtros por `tags`, `kind`, `priority`, `scope`, `workspace_evidence_required`;
- ranking com explicabilidade;
- `related_ids`;
- `diagnostics` opcionais;
- `fallback_suggestions`.

#### `get_instructions_batch`

Já retorna:

- múltiplos documentos por ID;
- conteúdo;
- `frontmatter` parseado;
- filtros por seção;
- informação de truncamento;
- `missing_ids`.

#### `resolve_instruction_context`

Já retorna:

- seleção consolidada;
- `selected_ids`;
- distinção entre `normative_ids` e `supporting_ids`;
- awareness de `workspace_evidence_required`;
- `next_actions`;
- `gaps`.

#### `get_normative_checklist`

Já retorna checklist por cenário com:

- itens;
- gaps;
- suporte requerido/recomendado;
- `verification`.

#### `detect_instruction_conflicts`

Já retorna:

- relações entre instruções;
- conflito potencial;
- precedência;
- guidance textual.

### 3.2 Base já existente no corpus

O corpus já contém, em várias policies:

- `workspace_evidence_required: true`
- `workspace_signals: [...]`
- `on_absence: hypothesis_only`

Logo, já existe base suficiente para um evidence gate formal sem alterar tools sistêmicas.

---

## 4. Problema real a resolver

O problema desta etapa não é desenhar o MCP ideal final.

O problema correto é:

> como aumentar rapidamente a utilidade normativa do MCP atual, sem regressão, reaproveitando o que já existe e fechando apenas as lacunas de maior valor operacional?

As lacunas reais desta fase são:

1. ausência de tool dedicada para **aplicabilidade**;
2. ausência de tool dedicada para **matrix de conformidade operacional**;
3. necessidade de fortalecer `resolve_instruction_context` como camada preparatória;
4. melhoria posterior do estado operacional do corpus;
5. melhoria posterior do discovery normativo;
6. evitar heurísticas frágeis de parsing estrutural do markdown nesta fase.

---

## 5. Princípios obrigatórios de desenho

### 5.1 Separação de responsabilidades

As novas tools **não devem** misturar responsabilidades principais:

- `validate_applicability` decide apenas aplicabilidade;
- `build_compliance_matrix` decide apenas o estado operacional da análise/conformidade.

### 5.2 Fonte principal de decisão

Na primeira fase, a decisão automática deve considerar prioritariamente:

1. `frontmatter`;
2. contexto do artefato;
3. evidência fornecida.

O corpo textual da instruction pode ser usado apenas como apoio leve, não como base principal de decisão automática.

### 5.3 Evolução aditiva

As evoluções em tools já existentes devem ser estritamente aditivas na primeira entrega:

- permitido adicionar novos campos e blocos opcionais;
- não permitido remover campos;
- não permitido alterar silenciosamente a semântica de campos atuais.

### 5.4 Regra de prudência

Sem evidência suficiente:

- não afirmar `conformant`;
- não afirmar `partial_conformance`;
- não afirmar `non_conformance`.

### 5.5 Fora de escopo da primeira fase

Ficam explicitamente fora de escopo nesta rodada:

- extração rígida de `must`, `must_not`, `decision_rules`, `stop_rules`;
- auditoria formal completa;
- reescrita total de `search_instructions`;
- reescrita total de `resolve_instruction_context`;
- aumento forte da complexidade do corpus.

---

## 6. Pipeline funcional alvo

### 6.1 Pipeline alvo por etapas

Fluxo desejado ao fim de P2:

1. `list_instructions_index` ou `search_instructions`
2. `resolve_instruction_context`
3. `get_instructions_batch`
4. `validate_applicability`
5. `build_compliance_matrix`

### 6.2 Papel de cada etapa

#### `list_instructions_index`

Inventário do corpus disponível.

#### `search_instructions`

Discovery normativo.

#### `resolve_instruction_context`

Seleção consolidada e preparação de evidências a coletar.

#### `get_instructions_batch`

Leitura normativa.

#### `validate_applicability`

Evidence gate formal.

#### `build_compliance_matrix`

Saída operacional consolidada.

---

## 7. Estados oficiais

## 7.1 Estados oficiais de `validate_applicability`

Conjunto oficial:

- `applicable`
- `non_applicable`
- `hypothesis_only`
- `blocked_by_missing_evidence`

### Significado

#### `applicable`

A instruction está em escopo e há base suficiente para tratá-la como aplicável.

#### `non_applicable`

A instruction não se aplica ao artefato/contexto informado.

#### `hypothesis_only`

Há indícios de relevância, mas sem base suficiente para enforcement.

#### `blocked_by_missing_evidence`

A instruction depende explicitamente de evidência e essa evidência não foi fornecida em nível suficiente.

### Importante

`pending_evidence` **não** deve ser estado final de `validate_applicability` na primeira entrega.

Ele só pode existir como hint intermediário em `resolve_instruction_context`.

## 7.2 Estados oficiais de `build_compliance_matrix`

Conjunto oficial mínimo:

- `conformant`
- `partial_conformance`
- `non_conformance`
- `not_enforceable`
- `not_applicable`
- `insufficient_evidence`

### Significado

#### `conformant`

Há base suficiente para afirmar conformidade operacional.

#### `partial_conformance`

Há base suficiente para afirmar aderência parcial com gap identificável.

#### `non_conformance`

Há base suficiente para afirmar desvio relevante face à instruction aplicável.

#### `not_enforceable`

A instruction até pode ser relevante, mas não pode ser exigida por falta de base suficiente de enforcement.

#### `not_applicable`

A instruction não se aplica ao artefato.

#### `insufficient_evidence`

Não há evidência suficiente para afirmar conformidade nem não conformidade.

### Importante

Os seguintes valores **não** devem ser status finais da matrix:

- `applicable`
- `non_applicable`
- `hypothesis_only`
- `blocked_by_missing_evidence`

Esses valores pertencem ao domínio de aplicabilidade, não ao da matrix.

---

## 8. Regras obrigatórias de decisão

## 8.1 Regra default sem `on_absence`

Se:

- `workspace_evidence_required = true`
- e faltarem sinais mínimos esperados
- e não houver `on_absence`

o comportamento default oficial deve ser:

- `blocked_by_missing_evidence`

### Justificativa

Esse é o comportamento mais conservador e menos sujeito a extrapolação.

## 8.2 Regra oficial de `scope`

A comparação de `target_artifact.path` com `scope` deve usar:

- glob real normalizado;
- path relativo ao workspace/repositório quando possível;
- case-insensitive em Windows.

### O que não deve ser regra principal

- substring simples;
- heurística por segmentos sem glob real.

### Fallback permitido

Se houver limitação técnica temporária:

- pode existir fallback controlado;
- deve ser diagnosticado;
- não substitui a regra oficial.

## 8.3 Contrato oficial de `workspace_evidence`

### Formato rico recomendado

```json
{
  "workspace_evidence": [
    {
      "value": "HttpContext.User",
      "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
      "symbol": "ObterCliente",
      "source": "code_search",
      "evidence_type": "positive"
    }
  ]
}
```

### Campos recomendados

- `value`
- `path`
- `symbol`
- `source`
- `evidence_type`

### Compatibilidade mínima

Também deve ser aceito:

```json
{
  "workspace_evidence": [
    "HttpContext.User",
    "OpenFinanceResponse<T>"
  ]
}
```

### Regra de interpretação

- string simples = evidência positiva sem metadados;
- objeto estruturado = evidência com contexto adicional.

## 8.4 Evidência positiva e negativa

Deve haver suporte a:

- `positive`
- `negative`
- `absence_observed`

### Regra de prudência

Evidência negativa não deve, sozinha, virar não conformidade.

Ela serve principalmente para:

- bloquear enforcement;
- sustentar `blocked_by_missing_evidence`;
- justificar `insufficient_evidence`;
- reforçar `hypothesis_only`.

---

## 9. Fase 0 — Congelamento semântico e baseline técnico

### Objetivo

Fechar contratos e reduzir risco de ambiguidade antes de implementar.

### Entregas

1. congelar estados oficiais de aplicabilidade;
2. congelar estados oficiais da matrix;
3. congelar default de `on_absence`;
4. congelar regra de `scope`;
5. congelar contrato de `workspace_evidence`;
6. congelar política de retrocompatibilidade;
7. congelar critérios mínimos de suficiência de evidência.

### Justificativa

Sem essa fase, diferentes implementações podem parecer corretas e ainda assim divergir semanticamente.

### Critérios de aceite

- estados e contratos aprovados;
- nenhuma ambiguidade residual sobre aplicabilidade vs conformidade;
- ready para P0.

---

## 10. Fase 1 — Evidence Gate formal (P0)

### Objetivo

Entregar as duas novas tools centrais:

- `validate_applicability`
- `build_compliance_matrix`

Esta é a fase de maior valor imediato.

## 10.1 Tool nova: `validate_applicability`

### Objetivo

Formalizar a aplicabilidade normativa de uma ou mais instructions a um artefato/contexto, usando principalmente `frontmatter` e evidência fornecida.

### Contrato de entrada

```json
{
  "instruction_ids": [
    "microservice-api-openfinance-patterns",
    "microservice-authorization-resource-scope-and-audit"
  ],
  "target_artifact": {
    "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
    "symbol": "ClienteEndpoints",
    "artifact_type": "endpoint-class",
    "workspace_root_hint": "ClientesAPI"
  },
  "workspace_evidence": [
    {
      "value": "HttpContext.User",
      "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
      "symbol": "ObterCliente",
      "source": "code_search",
      "evidence_type": "positive"
    },
    {
      "value": "IAuthorizationRequirement",
      "path": "ClientesAPI.Api/Security/OwnerRequirement.cs",
      "symbol": "OwnerRequirement",
      "source": "find_symbol",
      "evidence_type": "positive"
    }
  ]
}
```

### Compatibilidade backward-compatible

Também deve ser aceito:

```json
{
  "instruction_ids": [
    "microservice-authorization-resource-scope-and-audit"
  ],
  "target_artifact": {
    "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs"
  },
  "workspace_evidence": [
    "HttpContext.User",
    "IAuthorizationRequirement"
  ]
}
```

### Validações obrigatórias de entrada

- `instruction_ids`: lista não vazia de strings distintas;
- `target_artifact.path`: obrigatório e não vazio;
- `workspace_evidence`: opcional; se existir:
  - lista de strings, ou
  - lista de objetos com ao menos `value`.

### Contrato de saída

```json
{
  "results": [
    {
      "instruction_id": "microservice-authorization-resource-scope-and-audit",
      "kind": "policy",
      "scope_match": true,
      "workspace_evidence_required": true,
      "required_workspace_signals": [
        "IAuthorizationHandler",
        "AuthorizationHandlerContext",
        "IAuthorizationRequirement",
        "ResourceAuthorizationRequirement",
        "HttpContext.User"
      ],
      "matched_workspace_signals": [
        "IAuthorizationRequirement",
        "HttpContext.User"
      ],
      "missing_workspace_signals": [
        "IAuthorizationHandler",
        "AuthorizationHandlerContext",
        "ResourceAuthorizationRequirement"
      ],
      "applicability": "hypothesis_only",
      "reason": "Instruction is in scope, but evidence is only partial and insufficient for strong enforcement.",
      "diagnostics": {
        "scope_match_strategy": "glob",
        "evidence_positive_count": 2,
        "evidence_negative_count": 0,
        "used_on_absence": "hypothesis_only"
      }
    }
  ],
  "summary": {
    "requested_count": 1,
    "resolved_count": 1
  }
}
```

### Regras obrigatórias de decisão

1. Se a instruction não existir no índice:
   - retornar erro estruturado.
2. Se `scope` não casar com `target_artifact.path`:
   - `applicability = non_applicable`
3. Se `kind = reference`:
   - não produzir obrigação forte;
   - na primeira entrega, preferir `hypothesis_only` quando em escopo.
4. Se `workspace_evidence_required = false`:
   - em escopo -> `applicable`
5. Se `workspace_evidence_required = true`:
   - com evidência suficiente -> `applicable`
   - com `on_absence` explícito -> usar `on_absence`
   - sem `on_absence` -> `blocked_by_missing_evidence`

### Regra de suficiência de evidência para P0

Para manter a implementação conservadora e previsível:

- se `workspace_evidence_required = true` e `workspace_signals` estiver ausente ou vazio:
  - devolver `blocked_by_missing_evidence` com diagnóstico;
- se `workspace_signals` existir:
  - ao menos um sinal positivo forte e nenhum bloqueio explícito -> `applicable`
  - proximidade parcial sem força suficiente -> `hypothesis_only`
  - sem sinal suficiente -> `on_absence` ou `blocked_by_missing_evidence`

### Pseudocódigo de referência

```python
def decide_applicability(instruction, target_artifact, evidence_items):
    scope_match = match_scope(instruction.scope, target_artifact.path)
    if not scope_match:
        return "non_applicable", "Artifact path is out of declared scope."

    if instruction.kind == "reference":
        return "hypothesis_only", "Reference can inform analysis, but is not enforceable as strong policy."

    if not instruction.workspace_evidence_required:
        return "applicable", "Instruction is in scope and does not require workspace evidence."

    signals = instruction.workspace_signals or []
    if not signals:
        return "blocked_by_missing_evidence", (
            "Policy requires workspace evidence but declares no usable workspace_signals."
        )

    matched = positive_matches(signals, evidence_items)

    if matched:
        return "applicable", f"Found required workspace signals: {matched}"

    if instruction.on_absence:
        return instruction.on_absence, "Policy declares explicit absence behavior."

    return "blocked_by_missing_evidence", "Required workspace evidence is missing."
```

### Exemplo de helper de `scope`

```python
from fnmatch import fnmatch


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def match_scope(scope: str | None, artifact_path: str) -> bool:
    if not scope:
        return True
    normalized_scope = normalize_path(scope)
    normalized_path = normalize_path(artifact_path)
    return fnmatch(normalized_path, normalized_scope)
```

### Critérios de aceite

1. `scope` fora -> `non_applicable`
2. policy em escopo sem `workspace_evidence_required` -> `applicable`
3. policy com evidência suficiente -> `applicable`
4. policy com `on_absence = hypothesis_only` -> `hypothesis_only`
5. policy com `workspace_evidence_required = true` e sem `on_absence` -> `blocked_by_missing_evidence`
6. `reference` em escopo -> `hypothesis_only`
7. aceita lista simples de strings
8. aceita evidência estruturada
9. aceita evidência negativa
10. normaliza path Windows

## 10.2 Tool nova: `build_compliance_matrix`

### Objetivo

Consolidar o estado operacional da análise normativa usando:

- resultado de aplicabilidade;
- observações do artefato;
- evidências relevantes;
- contexto do artefato.

### Importante

A matrix **não decide aplicabilidade**.

### Contrato de entrada

```json
{
  "target_artifact": {
    "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
    "symbol": "ClienteEndpoints",
    "artifact_type": "endpoint-class"
  },
  "instruction_results": [
    {
      "instruction_id": "microservice-api-openfinance-patterns",
      "kind": "policy",
      "applicability": "applicable",
      "reason": "Artifact matches scope and evidence is sufficient."
    },
    {
      "instruction_id": "microservice-authorization-resource-scope-and-audit",
      "kind": "policy",
      "applicability": "hypothesis_only",
      "reason": "Relevant topic but insufficient evidence for strong enforcement."
    }
  ],
  "artifact_observations": [
    {
      "instruction_id": "microservice-api-openfinance-patterns",
      "observation_type": "positive",
      "value": "OpenFinanceResponse<T> found in endpoint return",
      "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
      "source": "code_read"
    },
    {
      "instruction_id": "microservice-api-openfinance-patterns",
      "observation_type": "gap",
      "value": "No explicit global error handling evidence in analyzed artifact",
      "path": "ClientesAPI.Api/Endpoints/ClienteEndpoints.cs",
      "source": "code_read"
    }
  ]
}
```

### Validações obrigatórias

- `instruction_results` lista não vazia;
- cada item contendo:
  - `instruction_id`
  - `kind`
  - `applicability`
- `artifact_observations` opcional, mas sua ausência deve puxar a matrix para estados conservadores.

### Contrato de saída

```json
{
  "matrix": [
    {
      "instruction_id": "microservice-api-openfinance-patterns",
      "kind": "policy",
      "decision": "applicable",
      "evidence": [
        "OpenFinanceResponse<T> found in endpoint return",
        "No explicit global error handling evidence in analyzed artifact"
      ],
      "status": "partial_conformance",
      "allowed_action": "Preserve existing response envelope and inspect global error handling before asserting full conformance.",
      "reason": "Applicable policy with at least one positive adherence sign and at least one identified gap."
    },
    {
      "instruction_id": "microservice-authorization-resource-scope-and-audit",
      "kind": "policy",
      "decision": "hypothesis_only",
      "evidence": [
        "Relevant topic but insufficient evidence for strong enforcement."
      ],
      "status": "not_enforceable",
      "allowed_action": "Search for authorization handlers or request human confirmation before enforcing."
    }
  ],
  "summary": {
    "conformant": 0,
    "partial_conformance": 1,
    "non_conformance": 0,
    "not_enforceable": 1,
    "not_applicable": 0,
    "insufficient_evidence": 0
  }
}
```

### Regras obrigatórias de mapeamento

#### Se `applicability = non_applicable`

- `status = not_applicable`

#### Se `applicability = hypothesis_only`

- `status = not_enforceable`

#### Se `applicability = blocked_by_missing_evidence`

- `status = not_enforceable`

#### Se `applicability = applicable`

Usar `artifact_observations`:

- positivos suficientes e sem gaps -> `conformant`
- positivos + gap -> `partial_conformance`
- desvio forte e objetivo -> `non_conformance`
- observação insuficiente -> `insufficient_evidence`

### Regras de suficiência

#### `conformant`

Exigir:

- `applicable`
- ao menos uma observação positiva relevante
- nenhuma observação de gap ou desvio relevante

#### `partial_conformance`

Exigir:

- `applicable`
- ao menos uma observação positiva relevante
- ao menos um gap identificável

#### `non_conformance`

Exigir:

- `applicable`
- ao menos uma observação de desvio forte, direta e objetiva

#### `insufficient_evidence`

Usar quando:

- `applicable`, mas o artefato ainda não foi suficientemente observado.

### Pseudocódigo de referência

```python
def build_matrix_row(instruction_result, observations):
    applicability = instruction_result["applicability"]

    if applicability == "non_applicable":
        return "not_applicable"

    if applicability in {"hypothesis_only", "blocked_by_missing_evidence"}:
        return "not_enforceable"

    positives = [o for o in observations if o["observation_type"] == "positive"]
    gaps = [o for o in observations if o["observation_type"] == "gap"]
    deviations = [o for o in observations if o["observation_type"] == "deviation"]

    if deviations:
        return "non_conformance"

    if positives and gaps:
        return "partial_conformance"

    if positives and not gaps:
        return "conformant"

    return "insufficient_evidence"
```

### Regra anti-alucinação

A matrix não deve produzir `non_conformance` apenas por ausência genérica de evidência.

### Critérios de aceite

1. `non_applicable` -> `not_applicable`
2. `hypothesis_only` -> `not_enforceable`
3. `blocked_by_missing_evidence` -> `not_enforceable`
4. `applicable` + positivos suficientes -> `conformant`
5. `applicable` + positivos + gap -> `partial_conformance`
6. `applicable` + desvio forte -> `non_conformance`
7. `applicable` sem observação suficiente -> `insufficient_evidence`

---

## 11. Fase 2 — Fortalecer o resolvedor existente (P1)

### Objetivo

Evoluir `resolve_instruction_context` para atuar como camada preparatória, sem substituir as novas tools.

### Novos campos aditivos

- `selection_rationale`
- `pending_evidence`
- `required_workspace_signals`
- `next_repo_evidence_actions`

### Exemplo de payload desejado

```json
{
  "query": "authorization owner audit endpoint",
  "selected_ids": [
    "microservice-authorization-resource-scope-and-audit"
  ],
  "resolution": {
    "selection_rationale": [
      {
        "instruction_id": "microservice-authorization-resource-scope-and-audit",
        "why_selected": "Top policy match with strong security and ownership overlap."
      }
    ],
    "pending_evidence": [
      {
        "instruction_id": "microservice-authorization-resource-scope-and-audit",
        "reason": "Policy requires workspace evidence before enforcement."
      }
    ],
    "required_workspace_signals": {
      "microservice-authorization-resource-scope-and-audit": [
        "IAuthorizationHandler",
        "AuthorizationHandlerContext",
        "IAuthorizationRequirement",
        "ResourceAuthorizationRequirement",
        "HttpContext.User"
      ]
    },
    "next_repo_evidence_actions": [
      "search for IAuthorizationHandler",
      "search for IAuthorizationRequirement",
      "search for HttpContext.User"
    ]
  }
}
```

### O que não fazer nesta fase

- não transformar `resolve_instruction_context` em substituta de applicability;
- não tornar `preliminary_matrix` obrigatória;
- não misturar estados finais de compliance nela.

### Critérios de aceite

1. nenhum campo atual muda de significado;
2. os novos campos são opcionais e aditivos;
3. a tool passa a orientar explicitamente coleta de evidência.

---

## 12. Fase 3 — Discovery e saúde do corpus (P2)

### Objetivo

Melhorar discovery e observabilidade do corpus depois que P0/P1 estiverem estáveis.

## 12.1 Evolução de `list_instructions_index`

### Novos campos aditivos desejados

- `status`
- `index_health`
- `warnings`
- `errors`

### Exemplo de payload

```json
{
  "status": "ok",
  "index_health": {
    "loaded": true,
    "documents_total": 27,
    "documents_usable": 25,
    "documents_with_warnings": 2,
    "loaded_at_utc": "2026-05-04T13:10:00Z"
  },
  "instructions": [],
  "count": 25,
  "by_tag": {},
  "corpus_version": "abc123",
  "warnings": [
    {
      "code": "SKIPPED_LARGE_FILE",
      "path": "legacy/big.md"
    }
  ],
  "errors": []
}
```

### Justificativa

Warnings de indexação hoje existem principalmente em log; a evolução desejada é torná-los auditáveis no payload.

## 12.2 Evolução de `search_instructions`

### Entrega opcional aditiva

Suporte a multi-query:

```json
{
  "queries": [
    "minimal api rest status codes",
    "response envelope global error handling"
  ],
  "max_results_per_query": 5,
  "include_diagnostics": true
}
```

### Saída desejada

```json
{
  "queries": [
    {
      "query": "minimal api rest status codes",
      "results": []
    },
    {
      "query": "response envelope global error handling",
      "results": []
    }
  ],
  "consolidated": {
    "top_policies": [],
    "top_references": [],
    "coverage_gaps": []
  }
}
```

### Justificativa

Melhora discovery, mas não é bloqueador para a primeira validação com a outra IA.

---

## 13. Fase 4 — Refinamentos não críticos (P3)

### 13.1 Evolução de `get_normative_checklist`

Adicionar classificação posterior:

- `mandatory`
- `recommended`
- `conditional_on_evidence`

### 13.2 Evolução de `detect_instruction_conflicts`

Refinar posteriormente:

- severidade;
- explicação;
- impacto em contrato público;
- necessidade de decisão humana.

### Justificativa

Esses itens têm valor, mas não devem competir com applicability + matrix.

---

## 14. Fase 5 — Expansões futuras explicitamente fora da primeira fase (P4)

Ficam registrados como fora do escopo imediato:

- parsing estrutural de `must`, `must_not`, `decision_rules`, `stop_rules`;
- scoring avançado de auditoria;
- auditoria formal completa;
- mudanças profundas de autoria do corpus;
- reestruturações grandes de tools existentes.

---

## 15. Contratos JSON resumidos

## 15.1 JSON contract resumido de `validate_applicability`

```json
{
  "type": "object",
  "required": ["instruction_ids", "target_artifact"],
  "properties": {
    "instruction_ids": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "target_artifact": {
      "type": "object",
      "required": ["path"],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1
        },
        "symbol": {
          "type": "string"
        },
        "artifact_type": {
          "type": "string"
        },
        "workspace_root_hint": {
          "type": "string"
        }
      }
    },
    "workspace_evidence": {
      "type": "array",
      "items": {
        "anyOf": [
          {
            "type": "string",
            "minLength": 1
          },
          {
            "type": "object",
            "required": ["value"],
            "properties": {
              "value": {
                "type": "string",
                "minLength": 1
              },
              "path": {
                "type": "string"
              },
              "symbol": {
                "type": "string"
              },
              "source": {
                "type": "string"
              },
              "evidence_type": {
                "type": "string",
                "enum": ["positive", "negative", "absence_observed"]
              }
            }
          }
        ]
      }
    }
  }
}
```

## 15.2 JSON contract resumido de `build_compliance_matrix`

```json
{
  "type": "object",
  "required": ["target_artifact", "instruction_results"],
  "properties": {
    "target_artifact": {
      "type": "object",
      "required": ["path"],
      "properties": {
        "path": {
          "type": "string",
          "minLength": 1
        },
        "symbol": {
          "type": "string"
        },
        "artifact_type": {
          "type": "string"
        }
      }
    },
    "instruction_results": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["instruction_id", "kind", "applicability"],
        "properties": {
          "instruction_id": {
            "type": "string",
            "minLength": 1
          },
          "kind": {
            "type": "string",
            "minLength": 1
          },
          "applicability": {
            "type": "string",
            "enum": [
              "applicable",
              "non_applicable",
              "hypothesis_only",
              "blocked_by_missing_evidence"
            ]
          },
          "reason": {
            "type": "string"
          }
        }
      }
    },
    "artifact_observations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["instruction_id", "observation_type", "value"],
        "properties": {
          "instruction_id": {
            "type": "string",
            "minLength": 1
          },
          "observation_type": {
            "type": "string",
            "enum": ["positive", "gap", "deviation", "unknown"]
          },
          "value": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string"
          },
          "source": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

---

## 16. Estratégia de testes por fase

## 16.1 Testes obrigatórios de P0

### `validate_applicability`

1. scope não casa -> `non_applicable`
2. policy em escopo sem `workspace_evidence_required` -> `applicable`
3. policy com evidência suficiente -> `applicable`
4. policy com `on_absence = hypothesis_only` -> `hypothesis_only`
5. policy com `workspace_evidence_required = true` e sem `on_absence` -> `blocked_by_missing_evidence`
6. `reference` em escopo -> `hypothesis_only`
7. aceita lista simples de strings
8. aceita evidência estruturada
9. aceita evidência negativa
10. normalização Windows

### `build_compliance_matrix`

1. `non_applicable` -> `not_applicable`
2. `hypothesis_only` -> `not_enforceable`
3. `blocked_by_missing_evidence` -> `not_enforceable`
4. `applicable` + positivos suficientes -> `conformant`
5. `applicable` + positivos + gap -> `partial_conformance`
6. `applicable` + desvio forte -> `non_conformance`
7. `applicable` sem observação suficiente -> `insufficient_evidence`

## 16.2 Testes obrigatórios de P1

### `resolve_instruction_context`

1. devolve `selection_rationale`
2. devolve `pending_evidence`
3. devolve `required_workspace_signals`
4. devolve `next_repo_evidence_actions`
5. não quebra payload atual

## 16.3 Testes obrigatórios de P2

### `list_instructions_index`

1. `status = ok`
2. `status = partial` quando houver warnings
3. `status = error` se corpus indisponível

### `search_instructions`

1. query única continua funcionando
2. multi-query opcional funciona
3. saída consolidada estável

---

## 17. Regras anti-ambiguidade e anti-alucinação

1. Ausência de evidência não é não conformidade.
2. `reference` não vira obrigação forte na primeira fase.
3. `resolve_instruction_context` não substitui applicability nem matrix final.
4. O corpo textual da instruction não deve ser usado para inventar estrutura normativa.
5. Sem `scope_match`, não há `applicable`.
6. Sem observação suficiente do artefato, não há `non_conformance`.
7. O default sem `on_absence` é sempre conservador.
8. Todo resultado deve explicar a decisão em frase curta e objetiva.
9. As novas tools devem ser auditáveis sem repetir o corpo integral da instruction.
10. Qualquer fallback heurístico deve ser explicitamente diagnosticado.

---

## 18. Mudanças mínimas necessárias no corpus

O objetivo do corpus continua sendo um template enxuto.

### Necessário apenas para policies com evidence gate

Garantir, quando fizer sentido:

```yaml
id: microservice-authorization-resource-scope-and-audit
title: "Autorização — âmbito de recurso, propriedade e auditoria"
tags: [microservice, security, authorization]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals:
  - IAuthorizationHandler
  - AuthorizationHandlerContext
  - IAuthorizationRequirement
  - ResourceAuthorizationRequirement
  - HttpContext.User
on_absence: hypothesis_only
```

### O que não exigir agora

- `must`
- `must_not`
- `decision_rules`
- `stop_rules`
- taxonomias grandes
- YAML complexo
- corpo altamente estruturado

### Template enxuto recomendado

```md
---
id: example-policy-id
title: "Título claro da policy"
tags: [tema1, tema2]
scope: "**/*.cs"
priority: high
kind: policy
workspace_evidence_required: true
workspace_signals:
  - ExampleSignal
on_absence: hypothesis_only
---

# Objetivo

Uma frase.

## TL;DR

- Regra principal
- Limite principal
- O que evitar

## Critérios

- Quando aplicar
- Quando não aplicar

## Pode ser feito

- Exemplo permitido

## Não pode ser feito

- Exemplo proibido
```

### Justificativa

Esse template mantém o corpus simples para outros desenvolvedores e já fornece o mínimo necessário para:

- busca;
- batch;
- evidence gate;
- matrix operacional.

---

## 19. Backlog final recomendado

## P0

- criar `validate_applicability`
- criar `build_compliance_matrix`

## P1

- evoluir `resolve_instruction_context`
  - `selection_rationale`
  - `pending_evidence`
  - `required_workspace_signals`
  - `next_repo_evidence_actions`

## P2

- evoluir `list_instructions_index`
  - `status`
  - `index_health`
  - `warnings`
  - `errors`
- evoluir `search_instructions`
  - multi-query opcional
  - consolidação temática

## P3

- evoluir `get_normative_checklist`
- refinar `detect_instruction_conflicts`

## P4

- registrar futuras expansões fora da primeira fase

---

## 20. Conclusão

Se o objetivo é testar rapidamente o MCP com a outra IA para verificar se esses mecanismos são realmente relevantes para a orquestração, o caminho com melhor relação valor/risco é:

1. formalizar aplicabilidade com `validate_applicability`;
2. formalizar a saída operacional com `build_compliance_matrix`;
3. fortalecer o resolvedor apenas como camada preparatória;
4. adiar parsing estrutural do markdown e refinamentos menos críticos.

Essa ordem:

- minimiza regressão;
- reduz ambiguidade;
- evita inferência excessiva;
- entrega exatamente o que é mais útil para a próxima rodada de validação.
