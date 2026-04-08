# BMAD — Lógica detalhada para montagem de contexto orientado à tarefa

## 1. Objetivo do documento

Este documento detalha a **lógica real** para montar contexto orientado à tarefa no MCP atual, sem uso de LLM e sem embeddings.

O foco aqui não é apenas explicar a arquitetura em alto nível, mas descrever:

- como o contexto deve ser montado na prática
- quais entradas são necessárias
- como selecionar candidatos
- como reranquear
- como deduplicar
- como montar o pacote final
- como detectar lacunas
- como preservar precedência entre instructions nativas e MCP
- pseudocódigo suficientemente preciso para implementação

---

## 2. Problema exato que a nova lógica resolve

Hoje o MCP já faz bem estas funções:

- indexar os arquivos Markdown com frontmatter
- pesquisar por palavras-chave
- devolver metadados e conteúdo
- recuperar instruções por `id` ou `path`

Isso resolve **descoberta documental**.

Mas não resolve completamente **execução orientada à tarefa**.

### Exemplo do problema

Se o pedido for:

> "Crie um endpoint GET paginado para consultar contas"

O agente ainda precisa decidir por conta própria:

- quais documentos do corpus importar
- quais são obrigatórios vs apenas úteis
- quais são redundantes
- o que resumir
- o que ignorar
- quais regras normativas precisam entrar no contexto mínimo

Esse esforço precisa sair do agente e entrar em uma tool específica de montagem de contexto.

---

## 3. Princípio central da solução

A nova tool não deve responder:

> "Aqui estão 8 documentos que talvez ajudem"

Ela deve responder:

> "Para esta tarefa, estes são os 3–5 itens mais relevantes, com justificativa, resumo e possíveis lacunas"

Em outras palavras:

- `search_instructions` encontra candidatos
- `build_task_context` monta um **pacote executável de contexto**

---

## 4. Conceitos principais

## 4.1 Tipos de conhecimento

### A. Regra sempre ativa
Conhecimento que deveria estar sempre presente no repositório local.

Exemplos:
- idioma
- segurança
- boundaries do serviço
- convenções obrigatórias do repo

### B. Referência sob demanda
Conhecimento que entra só quando a tarefa pede.

Exemplos:
- padrão Open Finance
- exemplos de Dapper
- padrão de DI
- ADRs
- guias de resiliência

A nova tool trabalha principalmente com o tipo **B**, mas precisa sempre lembrar que o tipo **A** prevalece se houver conflito.

---

## 4.2 Tipos de tarefa

A montagem do contexto depende do tipo de tarefa.

Sugestão inicial:

- `api_endpoint`
- `domain_rule`
- `repository_change`
- `integration_client`
- `worker_job`
- `observability`
- `security_hardening`
- `crosscutting_refactor`

A principal vantagem disso é que cada tipo de tarefa pode ter:

- tags preferidas
- kinds preferidos
- áreas esperadas de cobertura
- tamanho máximo de contexto recomendado

---

## 5. Estrutura da nova tool

## 5.1 Nome sugerido

`build_task_context`

---

## 5.2 Entrada sugerida

```json
{
  "task_type": "api_endpoint",
  "goal": "Criar endpoint GET paginado para consulta de contas",
  "repo_name": "accounts-api",
  "target_paths": [
    "src/Accounts.Api/Controllers",
    "src/Accounts.Domain"
  ],
  "language": "csharp",
  "framework": ".net",
  "keywords": [
    "pagination",
    "open finance",
    "controller",
    "validation"
  ],
  "native_topics": [
    "security",
    "language-ptbr",
    "service-boundaries"
  ],
  "max_instructions": 5
}
```

---

## 5.3 Saída sugerida

```json
{
  "task_type": "api_endpoint",
  "goal": "Criar endpoint GET paginado para consulta de contas",
  "selected_instructions": [
    {
      "id": "microservice-api-openfinance-patterns",
      "title": "Microservice API — Open Finance, erros globais e docs",
      "path": "microservice-api-openfinance-patterns.md",
      "kind": "policy",
      "priority": "high",
      "score_breakdown": {
        "textual": 8.75,
        "kind_boost": 2.0,
        "priority_boost": 1.5,
        "scope_boost": 3.0,
        "task_profile_boost": 2.0,
        "redundancy_penalty": 0.0,
        "final_score": 17.25
      },
      "reason": "Alta aderência a API endpoint, escopo compatível com camada Api e policy prioritária",
      "summary": "Endpoints devem seguir padrão Open Finance, documentação mínima e tratamento global de erro."
    }
  ],
  "context_summary": [
    "Controller deve permanecer fino",
    "Erros devem ser tratados globalmente",
    "Resposta deve seguir padrão Open Finance",
    "Regras de negócio não devem ficar na camada Api"
  ],
  "conflicts": [],
  "gaps": [
    "Não foi encontrada instrução específica de paginação"
  ],
  "precedence_note": "Native repository instructions override MCP guidance when conflicts exist."
}
```

---

## 6. Fluxo lógico da montagem de contexto

A lógica deve seguir esta sequência:

1. normalizar a entrada
2. obter perfil da tarefa
3. montar query expandida
4. gerar candidatos iniciais
5. aplicar reranking contextual
6. eliminar redundância
7. validar cobertura mínima
8. montar resumo consolidado
9. detectar conflitos e gaps
10. devolver pacote final

---

## 7. Detalhamento da lógica real

## 7.1 Passo 1 — Normalização da entrada

Objetivo:
- reduzir ruído
- padronizar campos
- garantir previsibilidade

### Regras

- converter `task_type` para lowercase
- remover keywords vazias
- deduplicar `keywords`
- normalizar `target_paths`
- aplicar defaults
- limitar `max_instructions` em um range seguro

### Exemplo de defaults

- `max_instructions`: default 5
- mínimo 1
- máximo 8 no MVP

### Pseudocódigo

```python
def normalize_request(request):
    task_type = (request.task_type or "").strip().lower()
    goal = (request.goal or "").strip()
    repo_name = (request.repo_name or "").strip()
    language = (request.language or "").strip().lower()
    framework = (request.framework or "").strip().lower()

    target_paths = []
    for p in request.target_paths or []:
        p = str(p).strip().replace("\\", "/")
        if p and p not in target_paths:
            target_paths.append(p)

    keywords = []
    for k in request.keywords or []:
        k = str(k).strip().lower()
        if k and k not in keywords:
            keywords.append(k)

    native_topics = []
    for t in request.native_topics or []:
        t = str(t).strip().lower()
        if t and t not in native_topics:
            native_topics.append(t)

    max_instructions = request.max_instructions or 5
    max_instructions = max(1, min(max_instructions, 8))

    return NormalizedRequest(
        task_type=task_type,
        goal=goal,
        repo_name=repo_name,
        language=language,
        framework=framework,
        target_paths=target_paths,
        keywords=keywords,
        native_topics=native_topics,
        max_instructions=max_instructions,
    )
```

---

## 7.2 Passo 2 — Carregar perfil da tarefa

Objetivo:
- aplicar heurísticas por tipo de tarefa

### Exemplo de perfil

```yaml
api_endpoint:
  preferred_tags:
    - api
    - openfinance
    - minimal-api
    - error-handling
    - xmldocs
    - validation
  preferred_kinds:
    - policy
    - reference
  expected_dimensions:
    - api_pattern
    - error_handling
    - documentation
    - validation
    - layer_separation
  default_max_results: 5
```

### O que o perfil ajuda a fazer

- aumentar score de documentos com tags aderentes
- validar se o contexto cobre dimensões mínimas
- controlar tamanho do pacote final

### Pseudocódigo

```python
def get_task_profile(task_type):
    return TASK_PROFILES.get(task_type, TASK_PROFILES["generic"])
```

---

## 7.3 Passo 3 — Montar query expandida

Objetivo:
- enriquecer a busca inicial
- não depender apenas do texto do usuário

### Estratégia

A query deve combinar:

- `goal`
- `keywords`
- `task_type`
- tags preferidas do perfil
- linguagem/framework, quando fizer sentido

### Exemplo

Entrada:
- `goal`: "Criar endpoint GET paginado"
- `task_type`: `api_endpoint`
- `keywords`: `["pagination", "open finance"]`

Query expandida:
- `"Criar endpoint GET paginado pagination open finance api openfinance minimal-api error-handling"`

### Pseudocódigo

```python
def build_expanded_query(req, profile):
    parts = []

    if req.goal:
        parts.append(req.goal)

    parts.extend(req.keywords)

    if req.task_type:
        parts.append(req.task_type.replace("_", " "))

    parts.extend(profile.preferred_tags[:4])

    if req.language:
        parts.append(req.language)

    if req.framework:
        parts.append(req.framework)

    return " ".join(parts).strip()
```

---

## 7.4 Passo 4 — Geração de candidatos iniciais

Objetivo:
- obter um conjunto mais amplo de documentos que podem competir entre si

### Estratégia recomendada

Não selecionar diretamente o top 5 da busca atual.  
Primeiro selecionar um conjunto mais amplo, por exemplo:

- top 12
- top 15

Depois fazer reranking contextual.

### Por quê?

Porque a busca textual sozinha pode:
- supervalorizar termos genéricos
- ignorar `scope`
- ignorar `kind`
- ignorar o tipo de tarefa

### Pseudocódigo

```python
def fetch_initial_candidates(index, expanded_query, profile):
    tokens = tokenize_query(expanded_query)
    candidates = []

    for rec in index.values():
        textual_score = score_record(rec, tokens, None)
        if textual_score <= 0:
            continue
        candidates.append(
            Candidate(
                record=rec,
                textual_score=textual_score
            )
        )

    candidates.sort(key=lambda c: c.textual_score, reverse=True)

    # pool maior para reranking posterior
    return candidates[:15]
```

---

## 7.5 Passo 5 — Reranking contextual

Esse é o núcleo real da inteligência do MCP sem LLM.

O reranking deve considerar:

- score textual
- `kind`
- `priority`
- `scope`
- afinidade com o perfil da tarefa
- redundância
- overlap com temas nativos

### 7.5.1 Score textual
É o score atual do sistema. Ele continua sendo a base.

### 7.5.2 Boost por `kind`

Sugestão:

- `policy`: +2.0
- `reference`: +0.5
- ausente: +0.0

Motivo:
- policy tende a ser mais normativa
- reference tende a ser mais explicativa

### Pseudocódigo

```python
def kind_boost(rec):
    if rec.kind == "policy":
        return 2.0
    if rec.kind == "reference":
        return 0.5
    return 0.0
```

---

### 7.5.3 Boost por `priority`

Sugestão:

- high: +1.5
- medium: +0.7
- low: +0.2
- none: +0.0

### Pseudocódigo

```python
def priority_boost(rec):
    if rec.priority == "high":
        return 1.5
    if rec.priority == "medium":
        return 0.7
    if rec.priority == "low":
        return 0.2
    return 0.0
```

---

### 7.5.4 Boost por `scope`

Esse é um dos fatores mais importantes.

Se o documento declara `scope` compatível com o path da tarefa, ele deve subir bastante.

### Regras práticas

- match forte: +3.0
- match parcial: +1.0
- sem match: +0.0

### O que é match forte

Exemplo:
- documento com scope `**/Api/**/*.cs`
- path alvo contém `Accounts.Api`

### O que é match parcial

Exemplo:
- documento sem scope exato, mas com tags e título fortemente relacionados ao path

### Pseudocódigo simplificado

```python
from fnmatch import fnmatch

def scope_boost(rec, target_paths):
    if not rec.scope:
        return 0.0

    rec_scope = rec.scope.replace("\\", "/")

    for path in target_paths:
        fake_file = path
        if not fake_file.endswith(".cs"):
            fake_file = f"{fake_file}/dummy.cs"

        if fnmatch(fake_file, rec_scope):
            return 3.0

        if any(fragment.lower() in path.lower() for fragment in rec_scope.split("/") if fragment not in ("**", "*", "*.cs")):
            return 1.0

    return 0.0
```

---

### 7.5.5 Boost por perfil da tarefa

Se o documento possui tags alinhadas ao `task_type`, deve receber boost.

### Exemplo
Para `api_endpoint`, se o doc tem tags:
- `api`
- `openfinance`
- `error-handling`

Isso sugere alta aderência.

### Sugestão de regra
- +0.75 por tag preferida encontrada
- cap em +2.0

### Pseudocódigo

```python
def task_profile_boost(rec, profile):
    matches = 0
    rec_tags = set(rec.tags or [])
    for tag in profile.preferred_tags:
        if tag in rec_tags:
            matches += 1

    return min(2.0, matches * 0.75)
```

---

### 7.5.6 Penalidade por overlap com instructions nativas

No MVP, a tool não precisa ler diretamente as instructions nativas, mas pode receber `native_topics`.

Se o documento do MCP for claramente equivalente a um tema já coberto no repo local, você pode:

- reduzir score
- ou pelo menos marcar como redundância

### Sugestão de regra
- penalidade leve: -0.75 por overlap relevante
- cap em -1.5

### Pseudocódigo

```python
def native_overlap_penalty(rec, native_topics):
    if not native_topics:
        return 0.0

    penalty = 0.0
    blob = f"{rec.title} {' '.join(rec.tags)}".lower()

    for topic in native_topics:
        if topic in blob:
            penalty += 0.75

    return min(1.5, penalty)
```

---

### 7.5.7 Fórmula final

```python
def compute_final_score(candidate, req, profile):
    rec = candidate.record

    textual = candidate.textual_score
    k_boost = kind_boost(rec)
    p_boost = priority_boost(rec)
    s_boost = scope_boost(rec, req.target_paths)
    t_boost = task_profile_boost(rec, profile)
    n_penalty = native_overlap_penalty(rec, req.native_topics)

    final_score = textual + k_boost + p_boost + s_boost + t_boost - n_penalty

    return ScoreBreakdown(
        textual=textual,
        kind_boost=k_boost,
        priority_boost=p_boost,
        scope_boost=s_boost,
        task_profile_boost=t_boost,
        native_overlap_penalty=n_penalty,
        final_score=final_score,
    )
```

---

## 7.6 Passo 6 — Deduplicação e corte de redundância

Esse passo é essencial.  
Sem isso, a tool pode devolver 4 documentos dizendo quase a mesma coisa.

### Estratégia simples para MVP

Considere redundantes documentos que tenham:
- mesmo `kind`
- grande overlap de tags
- títulos muito próximos
- summaries muito parecidos

### Regra simples
Ao iterar pelos candidatos ordenados:

- se o candidato novo tiver overlap de tags muito alto com um já selecionado
- e não trouxer `kind` novo nem `scope` novo relevante
- então descarte

### Pseudocódigo

```python
def is_redundant(candidate, selected):
    cand_tags = set(candidate.record.tags or [])

    for sel in selected:
        sel_tags = set(sel.record.tags or [])

        if not cand_tags or not sel_tags:
            continue

        intersection = len(cand_tags & sel_tags)
        union = len(cand_tags | sel_tags)

        if union == 0:
            continue

        jaccard = intersection / union

        same_kind = candidate.record.kind == sel.record.kind

        if jaccard >= 0.70 and same_kind:
            return True

    return False
```

### Seleção final com deduplicação

```python
def select_top_candidates(scored_candidates, limit):
    selected = []

    for candidate in scored_candidates:
        if is_redundant(candidate, selected):
            continue

        selected.append(candidate)

        if len(selected) >= limit:
            break

    return selected
```

---

## 7.7 Passo 7 — Cobertura mínima

A tool não deve só escolher documentos com score alto.  
Ela também precisa verificar se a seleção cobre as dimensões mínimas esperadas.

### Exemplo para `api_endpoint`

Dimensões esperadas:
- api_pattern
- error_handling
- documentation
- layer_separation
- validation

### Como detectar cobertura sem LLM

Você pode mapear tags para dimensões.

Exemplo:

```python
DIMENSION_TAG_MAP = {
    "api_pattern": {"api", "minimal-api", "openfinance"},
    "error_handling": {"error-handling", "problem-details"},
    "documentation": {"xmldocs", "docs"},
    "layer_separation": {"architecture", "layering", "clean-architecture"},
    "validation": {"validation"}
}
```

### Pseudocódigo

```python
def compute_covered_dimensions(selected, profile):
    covered = set()

    for item in selected:
        tags = set(item.record.tags or [])

        for dimension in profile.expected_dimensions:
            if tags & DIMENSION_TAG_MAP.get(dimension, set()):
                covered.add(dimension)

    return covered
```

---

## 7.8 Passo 8 — Construção de `context_summary`

Esse é o material que realmente deveria ser consumido primeiro pelo agente.

### Objetivo
Gerar um resumo curto, objetivo e acionável.

### Estratégias

#### Estratégia A — extrair seção TL;DR
Se o documento tiver `## TL;DR`, use os bullets dali.

#### Estratégia B — primeiras bullets relevantes
Se não houver `TL;DR`, pegue as primeiras bullets do corpo.

#### Estratégia C — fallback
Use `summary` já gerado a partir do corpo.

### Regras do resumo consolidado

- máximo 8 bullets
- ideal entre 4 e 6
- remover duplicatas semânticas simples
- linguagem objetiva

### Pseudocódigo

```python
import re

def extract_tldr_bullets(body):
    lines = body.splitlines()
    bullets = []
    in_tldr = False

    for line in lines:
        raw = line.strip()

        if raw.lower().startswith("## tl;dr"):
            in_tldr = True
            continue

        if in_tldr and raw.startswith("## "):
            break

        if in_tldr and raw.startswith("- "):
            bullets.append(raw[2:].strip())

    return bullets
```

```python
def extract_first_bullets(body, max_items=3):
    bullets = []
    for line in body.splitlines():
        raw = line.strip()
        if raw.startswith("- "):
            bullets.append(raw[2:].strip())
        if len(bullets) >= max_items:
            break
    return bullets
```

```python
def build_context_summary(selected):
    bullets = []

    for item in selected:
        tldr = extract_tldr_bullets(item.record.body)
        if tldr:
            bullets.extend(tldr[:2])
            continue

        body_bullets = extract_first_bullets(item.record.body, max_items=2)
        if body_bullets:
            bullets.extend(body_bullets)
            continue

        bullets.append(item.short_summary)

    cleaned = []
    seen = set()

    for bullet in bullets:
        normalized = re.sub(r"\s+", " ", bullet.strip().lower())
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(bullet.strip())

    return cleaned[:8]
```

---

## 7.9 Passo 9 — Detecção de gaps

A tool deve conseguir apontar o que está faltando.

### Por que isso importa

Porque o objetivo do MCP não é fingir completude.  
É montar o melhor pacote possível e apontar limitações reais do corpus.

### Regras simples para gaps

Adicionar gaps quando:

- nenhum documento selecionado tiver score alto o suficiente
- cobertura de dimensões esperadas estiver incompleta
- só houver `reference` e nenhuma `policy`
- keywords importantes do request não aparecerem nos documentos finais

### Pseudocódigo

```python
def detect_gaps(selected, profile, req):
    gaps = []

    if not selected:
        gaps.append("Nenhuma instrução relevante foi encontrada para a tarefa.")
        return gaps

    highest = max(x.score_breakdown.final_score for x in selected)
    if highest < 5.0:
        gaps.append("Os documentos encontrados têm baixa aderência geral à tarefa.")

    covered = compute_covered_dimensions(selected, profile)
    missing = [d for d in profile.expected_dimensions if d not in covered]

    for d in missing:
        gaps.append(f"Não há cobertura clara para a dimensão esperada: {d}")

    has_policy = any(x.record.kind == "policy" for x in selected)
    if not has_policy:
        gaps.append("Nenhuma policy relevante foi encontrada; apenas referências foram selecionadas.")

    return gaps
```

---

## 7.10 Passo 10 — Montagem do pacote final

Finalmente, a tool precisa devolver uma estrutura consistente, explicável e auditável.

### Campos finais recomendados

- task_type
- goal
- selected_instructions
- context_summary
- conflicts
- gaps
- precedence_note

### Pseudocódigo

```python
def build_response(req, selected, gaps):
    selected_payload = []

    for item in selected:
        rec = item.record
        selected_payload.append({
            "id": rec.id,
            "title": rec.title,
            "path": rec.rel_path,
            "kind": rec.kind,
            "priority": rec.priority,
            "reason": item.reason,
            "summary": item.short_summary,
            "score_breakdown": {
                "textual": item.score_breakdown.textual,
                "kind_boost": item.score_breakdown.kind_boost,
                "priority_boost": item.score_breakdown.priority_boost,
                "scope_boost": item.score_breakdown.scope_boost,
                "task_profile_boost": item.score_breakdown.task_profile_boost,
                "native_overlap_penalty": item.score_breakdown.native_overlap_penalty,
                "final_score": item.score_breakdown.final_score,
            }
        })

    return {
        "task_type": req.task_type,
        "goal": req.goal,
        "selected_instructions": selected_payload,
        "context_summary": build_context_summary(selected),
        "conflicts": [],
        "gaps": gaps,
        "precedence_note": "Native repository instructions override MCP guidance when conflicts exist."
    }
```

---

## 8. Fluxo completo em pseudocódigo

```python
def build_task_context(request):
    # 1. normalizar request
    req = normalize_request(request)

    # 2. carregar índice
    idx = ensure_index()

    # 3. obter perfil da tarefa
    profile = get_task_profile(req.task_type)

    # 4. montar query expandida
    expanded_query = build_expanded_query(req, profile)

    # 5. buscar candidatos iniciais
    candidates = fetch_initial_candidates(idx, expanded_query, profile)

    # 6. reranquear com heurísticas contextuais
    scored_candidates = []
    for candidate in candidates:
        breakdown = compute_final_score(candidate, req, profile)
        candidate.score_breakdown = breakdown
        candidate.short_summary = summarize_body(candidate.record.body, 220)
        candidate.reason = explain_candidate_selection(candidate, req, profile)
        scored_candidates.append(candidate)

    scored_candidates.sort(
        key=lambda c: c.score_breakdown.final_score,
        reverse=True
    )

    # 7. deduplicar e limitar
    selected = select_top_candidates(scored_candidates, req.max_instructions)

    # 8. detectar gaps
    gaps = detect_gaps(selected, profile, req)

    # 9. montar resposta final
    return build_response(req, selected, gaps)
```

---

## 9. Explicação do campo `reason`

Esse campo é muito importante para observabilidade da tool.

A seleção não deve parecer mágica.  
Ela deve ser explicável.

### Estratégia
Monte uma frase simples combinando os fatores relevantes.

### Pseudocódigo

```python
def explain_candidate_selection(candidate, req, profile):
    rec = candidate.record
    reasons = []

    if candidate.score_breakdown.scope_boost > 0:
        reasons.append("escopo compatível com os paths alvo")

    if candidate.score_breakdown.kind_boost > 0:
        reasons.append(f"documento do tipo {rec.kind}")

    if candidate.score_breakdown.task_profile_boost > 0:
        reasons.append("alta aderência ao perfil da tarefa")

    if rec.priority == "high":
        reasons.append("prioridade alta no corpus")

    if not reasons:
        reasons.append("boa aderência textual à query")

    return ", ".join(reasons)
```

---

## 10. Estruturas de dados sugeridas

```python
from dataclasses import dataclass, field

@dataclass
class NormalizedRequest:
    task_type: str
    goal: str
    repo_name: str
    language: str
    framework: str
    target_paths: list[str]
    keywords: list[str]
    native_topics: list[str]
    max_instructions: int

@dataclass
class TaskProfile:
    preferred_tags: list[str]
    preferred_kinds: list[str]
    expected_dimensions: list[str]
    default_max_results: int

@dataclass
class ScoreBreakdown:
    textual: float
    kind_boost: float
    priority_boost: float
    scope_boost: float
    task_profile_boost: float
    native_overlap_penalty: float
    final_score: float

@dataclass
class Candidate:
    record: object
    textual_score: float
    score_breakdown: ScoreBreakdown | None = None
    short_summary: str = ""
    reason: str = ""
```

---

## 11. Organização recomendada de arquivos

```text
mcp-instructions-server/
  corporate_instructions_mcp/
    __init__.py
    __main__.py
    indexing.py
    server.py
    task_profiles.py
    context_builder.py
    policy_engine.py
    scope_matching.py
```

### Responsabilidades

#### `task_profiles.py`
Contém perfis por tipo de tarefa.

#### `context_builder.py`
Orquestra:
- normalização
- query expandida
- candidatos
- resumo
- gaps
- resposta

#### `policy_engine.py`
Contém:
- boosts
- penalidades
- score final
- explicação da seleção
- deduplicação

#### `scope_matching.py`
Centraliza lógica de match entre `scope` e `target_paths`.

---

## 12. Exemplo concreto ponta a ponta

### Entrada

```json
{
  "task_type": "api_endpoint",
  "goal": "Criar endpoint GET paginado para consultar contas",
  "repo_name": "accounts-api",
  "target_paths": ["src/Accounts.Api/Controllers"],
  "language": "csharp",
  "framework": ".net",
  "keywords": ["pagination", "open finance", "controller"],
  "native_topics": ["security", "language-ptbr"],
  "max_instructions": 4
}
```

### Candidatos iniciais possíveis
- `microservice-api-openfinance-patterns`
- `microservice-architecture-layering`
- `microservice-clean-architecture-guardrails`
- `microservice-di-options-extensions`
- `csharp-async-style`

### Resultado esperado da seleção
1. `microservice-api-openfinance-patterns`
2. `microservice-architecture-layering`
3. `microservice-clean-architecture-guardrails`

Possivelmente excluir:
- `csharp-async-style` se não trouxer contexto suficiente para a tarefa principal
- `di-options` se estiver fora do escopo imediato do endpoint

### Context summary esperado
- Controller deve permanecer fino
- Resposta deve seguir padrão Open Finance
- Tratamento de erro deve ser global
- Regras de negócio devem ficar no domínio
- Observabilidade e segurança continuam obrigatórias

### Gap esperado
- Não há guidance específico de paginação, caso o corpus realmente não tenha isso

---

## 13. Critérios de qualidade da nova tool

A tool será considerada boa se:

- devolver no máximo 3–5 instruções úteis na maioria dos casos
- evitar duplicidade
- conseguir explicar por que selecionou cada instrução
- apontar gaps reais
- melhorar o tempo até contexto útil
- preservar precedência das instructions nativas

---

## 14. O que não deve entrar neste momento

Para preservar simplicidade:

- não usar LLM
- não usar embeddings
- não tentar resumir semanticamente além de heurísticas locais
- não ler automaticamente todo o repositório atual
- não criar auto-refresh complexo

---

## 15. MVP recomendado

### Deve entrar no MVP
- `build_task_context`
- perfis de tarefa
- boost por `kind`
- boost por `priority`
- boost por `scope`
- boost por `task_type`
- penalidade por overlap com temas nativos
- deduplicação por tags/kind
- `context_summary`
- `gaps`

### Pode esperar
- leitura automática de instructions nativas do repo local
- inferência semântica
- embeddings
- LLM
- feedback loop histórico

---

## 16. Conclusão

A lógica real para montar contexto não é apenas "buscar por palavra-chave".

Ela precisa:

- entender o tipo de tarefa
- considerar o path afetado
- respeitar a natureza normativa do corpus
- evitar redundância
- verificar cobertura mínima
- montar um resumo pequeno e acionável
- apontar lacunas

Essa abordagem permite evoluir o MCP de um:

> catálogo consultável

para um:

> montador de contexto corporativo orientado à execução

Esse é o salto mais importante para tornar a solução realmente útil em um ambiente com muitos repositórios e forte necessidade de padronização.
