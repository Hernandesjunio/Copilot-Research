# 🧠 Auditoria Técnica da Estratégia de Uso do GitHub Copilot com MCP

- **Data:** 2026-04-11
- **Papel:** Auditor técnico crítico e imparcial
- **Escopo:** Repositório `Copilot-Research` — código, experimentos, políticas, épicos e análises
- **Objetivo auditado:** Manter `.github/copilot-instructions.md` com regras específicas por repo; mover conhecimento global para MCP; reduzir duplicação em 100+ repositórios; melhorar orquestração de contexto sem violar políticas.

---

## 📌 Visão Geral

Este repositório documenta uma iniciativa real de governança para uso disciplinado do GitHub Copilot em ambiente corporativo (.NET 8, Open Finance, 100+ microsserviços). A tese central: substituir arquivos `copilot-instructions.md` grandes e duplicados por um modelo híbrido — instruções nativas "finas" (5–15 regras) + recuperação de contexto sob demanda via servidor MCP (Model Context Protocol).

O repositório contém:
- **Servidor MCP funcional** (Python, STDIO, 3 tools)
- **8 documentos de instrução** como corpus de exemplo
- **1 documento de experimento** em `experimentos-mcp/` com resultados (ensaio 2026-04-05)
- **4 documentos** em `analises/` (comparativo do template thin de 2026-04-07, duas peças de 2026-04-09 e esta auditoria)
- **4 épicos** de planejamento (BMAD)
- **6 documentos de governança/política**
- **5 prompts de pesquisa** com respostas arquivadas

**Julgamento preliminar:** A estratégia é fundamentalmente correta na direção, mas apresenta lacunas de validação empírica, dependência excessiva de inferência comportamental e ausência de testes A/B rigorosos.

---

## 1. 📊 Clareza Estratégica

### Formulação da proposta

A estratégia está formulada como **separação entre contexto local e conhecimento global**, e **não** como substituição completa das instruções locais. Isso é evidenciado por:

- `politica-camadas.md`: "Regra sempre ativa → `.github/instructions/`; Referência on-demand → MCP"
- `EPIC-01`: "Instructions nativas do repositório atual têm precedência ('lei')"
- `plano-execucao-bmad.md`: "se a instrução precisa estar **sempre presente** independentemente da tarefa, ela é nativa"
- `templates/copilot-instructions.thin.md`: "As regras **deste arquivo** prevalecem se houver conflito com o MCP"

### Veredito

| Aspecto | Avaliação |
|---------|-----------|
| Separação local vs. global | ✅ **Correta** — claramente formulada e consistente em todos os documentos |
| Hierarquia de precedência | ✅ **Correta** — nativas > MCP, explícita e repetida |
| Critério de classificação | ✅ **Correto** — "sempre ativa" vs. "condicional à tarefa" é um corte válido |
| Definição de "thin" | ⚠️ **Parcialmente correta** — bem definida, mas o template atual referencia `compose_context` (tool inexistente) |

### ❌ Falha identificada

O `templates/copilot-instructions.thin.md` menciona fluxo com 4 passos MCP, incluindo referência implícita a tools que não existem no servidor. A inconsistência I3 da [análise técnica de 2026-04-07](2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md) identificou isso mas **não foi corrigida** — o template canônico permanece desalinhado com o servidor real.

**Classificação:** FATO (verificável no código: `server.py` expõe 3 tools; o template sugere fluxo com "combinar múltiplas referências" que pressupõe capacidade não existente).

---

## 2. 📦 Separação de Responsabilidades

### Modelo proposto vs. modelo ideal

| Camada | Responsabilidade (proposta no repo) | Avaliação | Exemplos |
|--------|-------------------------------------|-----------|----------|
| `.github/copilot-instructions.md` | Regras sempre-ativas (idioma, segurança, escopo, limites) + orquestração MCP ("pseudo-hook") | ✅ Correto | "português", "nunca inclua segredos", "não assuma código de outros serviços" |
| MCP (tools) | Retrieval sob demanda de conhecimento transversal | ✅ Correto para MVP | `search_instructions`, `get_instruction`, `list_instructions_index` |
| MCP (resources) | Não implementado | ⚠️ Lacuna — análise técnica (2026-04-09) reconhece que resources seriam ideais para "base persistente" | Padrões REST, checklists de observabilidade |
| MCP (prompts) | Não implementado | ⚠️ Lacuna — análise reconhece valor para tarefas recorrentes | "Criar endpoint ponta a ponta" |
| Copilot Spaces | **Não mencionado** em nenhum documento | ❌ Lacuna significativa | Contexto compartilhado de projeto, documentação viva |
| Prompt files (`.github/prompts/`) | Mencionado apenas na análise técnica (seção 6.2) | ⚠️ Sub-explorado | Templates de tarefa reutilizáveis |

### Críticas à separação atual

1. **Copilot Spaces é ignorado.** A documentação oficial do GitHub Copilot posiciona Spaces como mecanismo para compartilhar contexto de projeto entre membros da equipe. Para o cenário de 100+ repos com conhecimento transversal, Spaces poderia complementar ou até competir com parte da proposta MCP. A ausência de qualquer menção é uma lacuna de pesquisa.

2. **Resources MCP não são usados.** A análise técnica (seção 11) argumenta corretamente que resources seriam ideais para "base persistente" — mas o servidor implementa **apenas tools**. Isso força o Copilot a fazer uma chamada ativa de tool para cada consulta, quando parte do conhecimento poderia ser exposto como resource endereçável.

3. **Prompt files são sub-explorados.** O diretório `prompts/` contém prompts de pesquisa, não prompts reutilizáveis para tarefas de desenvolvimento. A análise técnica reconhece o valor, mas nenhum experimento testa a eficácia de prompt files vs. MCP tools para padronização de tarefas.

### Classificação

| Ponto | Tipo |
|-------|------|
| Separação nativas vs. MCP funciona | FATO (testado nos experimentos) |
| Resources MCP seriam melhores para base persistente | HIPÓTESE (argumentada, não testada) |
| Copilot Spaces poderia complementar a estratégia | HIPÓTESE (não investigada) |
| Prompt files reduziriam carga do MCP para tarefas recorrentes | HIPÓTESE (não testada) |

---

## 3. 🧪 Análise dos Experimentos

### Experimento 1 (2026-04-05): Avaliação de Tools MCP

| Dimensão | Conteúdo |
|----------|----------|
| **Hipótese** | O servidor MCP com 3 tools (list/search/get) centraliza instruções de forma funcional para um projeto .NET 8 real |
| **Evidência** | Execução real em `ClientesAPI` com Visual Studio 2026; o Copilot invocou as tools e produziu código aderente ao corpus |
| **Conclusão original** | "Resultado sensacional, muito além do que eu esperava" — MCP funciona de forma análoga a custom instructions nativas, mas centralizada |
| **Minha crítica** | A evidência é **qualitativa e de caso único**. Não há grupo de controle (mesma tarefa sem MCP), não há métricas quantitativas (tokens, acurácia, tempo), não há repetição. O entusiasmo do autor pode enviesar a avaliação. |
| **Nível de confiança** | 🟡 Médio — demonstra viabilidade técnica, mas não valida superioridade ou equivalência |

**Classificações:**

| Afirmação | Tipo |
|-----------|------|
| O MCP funciona tecnicamente (tools são invocadas, retornam JSON válido) | ✅ FATO |
| O resultado é "sensacional" e equivale às instruções nativas | ⚠️ RISCO DE INTERPRETAÇÃO — sem comparação controlada |
| 6 tools adicionais melhorariam a eficiência | HIPÓTESE — fundamentada em análise de gaps, não testada |
| Descrições "Use when…" aumentam a taxa de invocação | HIPÓTESE — mencionada como insight, sem teste A/B (previsto em E2) |

### Sub-experimento 2 (Comportamento agêntico)

| Dimensão | Conteúdo |
|----------|----------|
| **Hipótese** | As tools propostas tornam o Copilot "mais agêntico" |
| **Evidência** | Análise teórica em duas dimensões (eficiência agêntica vs. proatividade autônoma) |
| **Conclusão original** | Tools melhoram eficiência quando agem, mas não proatividade — limitação arquitetural |
| **Minha crítica** | A análise é **logicamente sólida** mas **inteiramente teórica**. Nenhuma das 6 tools propostas foi implementada ou testada. A classificação por estrelas (★) é arbitrária. |
| **Nível de confiança** | 🟡 Médio para a conclusão geral; 🔴 Baixo para as classificações numéricas |

**Classificações:**

| Afirmação | Tipo |
|-----------|------|
| Copilot não tem hooks proativos (on_session_start, on_file_open) | ✅ FATO |
| Copilot não persiste estado entre sessões | ✅ FATO |
| `validate_compliance` habilitaria feedback loop generate→eval→fix | HIPÓTESE (plausível, não testada) |
| copilot-instructions.md funciona como "pseudo-hook" | ✅ FATO (é injetado em toda interação) |

### Sub-experimento 3 (Janela de contexto)

| Dimensão | Conteúdo |
|----------|----------|
| **Hipótese** | Estimativas qualitativas (low/medium/high) são superiores a percentuais exatos |
| **Evidência** | Observação de comportamento emergente — o Copilot reportou percentuais espontaneamente quando "Token Economy Pattern" apareceu nas instruções |
| **Conclusão original** | Percentuais são falsa precisão; qualitativo é suficiente |
| **Minha crítica** | A conclusão é **razoável** mas baseada em **uma única observação anedótica**. Não há teste comparativo entre sessões com percentual vs. qualitativo vs. nenhuma instrução. A decisão foi tomada com base em inferência, não evidência. |
| **Nível de confiança** | 🟡 Médio — a premissa "Copilot não expõe API de tokens" é fato; a conclusão prática é inferência razoável |

**Classificações:**

| Afirmação | Tipo |
|-----------|------|
| Copilot não expõe contagem interna de tokens | ✅ FATO |
| Percentuais reportados são heurísticas | ✅ FATO |
| Qualitativo é "suficiente" | HIPÓTESE (razoável, não validada comparativamente) |
| O comportamento emergiu do termo "Token Economy Pattern" | ⚠️ RISCO DE INTERPRETAÇÃO — correlação observada, causalidade inferida |

### Análise técnica (2026-04-07): Reestruturação do template thin

| Dimensão | Conteúdo |
|----------|----------|
| **Hipótese** | O template thin pode ser otimizado comparando versão atual vs. recomendação do Copilot Chat |
| **Evidência** | 7 inconsistências identificadas (I1–I7) entre template atual e recomendação |
| **Conclusão original** | "Iterar" — fechar decisão explícito vs. genérico e alinhar um único arquivo |
| **Minha crítica** | Documento **bem estruturado** e **acionável**. Porém, a decisão "iterar" resultou em **nenhuma ação** — o template permanece desalinhado (I3: `compose_context` inexistente ainda está implícita no fluxo). Isso é um risco de governança real. |
| **Nível de confiança** | 🟢 Alto para as inconsistências identificadas; 🔴 Baixo para a efetividade (nenhuma correção aplicada) |

---

## 4. 📋 Aderência à Documentação Oficial do GitHub Copilot

### Repository Custom Instructions

| Conceito oficial | Uso no repositório | Avaliação |
|------------------|-------------------|-----------|
| `.github/copilot-instructions.md` fornece contexto persistente ao Copilot | Usado como "thin" com 5–15 regras + orquestração MCP | ✅ **Alinhado** |
| Arquivos em `.github/instructions/` com `applyTo` para escopo por arquivo | Mencionado mas não explorado nos experimentos | ⚠️ **Parcialmente alinhado** — o mecanismo nativo de `applyTo` poderia ser combinado com a proposta MCP, mas não há experimento testando essa interação |
| Custom instructions influenciam toda interação | Usado corretamente como "pseudo-hook" | ✅ **Alinhado** |

### Custom Instructions (pessoais/organização)

| Conceito oficial | Uso no repositório | Avaliação |
|------------------|-------------------|-----------|
| Custom instructions pessoais do usuário | Não mencionadas | ⚠️ **Parcialmente alinhado** — a interação entre instruções pessoais, repo-level e MCP não é analisada |
| Organização pode definir instruções globais | Não mencionado | ⚠️ **Parcialmente alinhado** — poderia ser uma alternativa (ou complemento) ao MCP para parte do problema |

### Copilot Spaces

| Conceito oficial | Uso no repositório | Avaliação |
|------------------|-------------------|-----------|
| Spaces permite compartilhar contexto de projeto | **Completamente ausente** da pesquisa | ❌ **Não sustentado** — Spaces é o mecanismo oficial do GitHub para contexto compartilhado e não foi sequer avaliado como alternativa ou complemento |

### MCP (Model Context Protocol)

| Conceito oficial | Uso no repositório | Avaliação |
|------------------|-------------------|-----------|
| MCP conecta IA a data sources, tools e workflows | Usado exclusivamente para tools | ⚠️ **Parcialmente alinhado** — resources e prompts do MCP não são explorados |
| STDIO como transporte preferido para integração local | ✅ Implementado corretamente | ✅ **Alinhado** |
| Tools executam ações parametrizadas | ✅ 3 tools implementadas com contratos claros | ✅ **Alinhado** |
| Resources expõem dados endereçáveis | Não implementado | ⚠️ **Parcialmente alinhado** — análise técnica reconhece, mas não implementa |
| Prompts expõem templates reutilizáveis | Não implementado | ⚠️ **Parcialmente alinhado** |

### Resumo de aderência

| Conceito | Status |
|----------|--------|
| Repository custom instructions | ✅ Alinhado |
| Custom instructions (organização) | ⚠️ Parcialmente alinhado |
| Copilot Spaces | ❌ Não sustentado |
| MCP tools | ✅ Alinhado |
| MCP resources | ⚠️ Parcialmente alinhado |
| MCP prompts | ⚠️ Parcialmente alinhado |

---

## 5. 🏢 Viabilidade para Escala Organizacional (100+ repos)

### Avaliação por dimensão

| Dimensão | Avaliação | Justificativa |
|----------|-----------|---------------|
| **Manutenção** | 🟢 **Viável** | O modelo centraliza o corpus em um único local; mudanças propagam via MCP sem editar 100+ repos. Custo: manter thin por repo (~10 linhas) + corpus central. |
| **Consistência** | 🟡 **Parcialmente viável** | O corpus é único, mas a busca por keywords pode retornar resultados diferentes conforme a query. Sem embeddings, queries vagas produzem resultados inconsistentes entre devs. |
| **Risco de drift** | 🟡 **Risco moderado** | O servidor não monitora arquivos em tempo real (sem file-watching); requer restart. `content_sha256` existe para detecção futura, mas `check_instruction_updates` não está implementada. Clone local pode ficar desatualizado sem disciplina de `git pull`. |
| **Precisão contextual** | 🔴 **Risco alto** | Busca por keywords (sem embeddings) com corpus de 8 docs funciona; com 100+ docs, a degradação da precisão é previsível. O experimento E4 (embeddings vs. fulltext) reconhece isso mas não foi executado. |
| **Risco de respostas genéricas** | 🟡 **Risco moderado** | Sem `resolve_instructions_for_file` (proposta mas não implementada), o Copilot precisa inferir mentalmente quais instruções aplicam-se ao arquivo atual — custo de tokens e risco de erro. |
| **Governança** | 🟢 **Bem endereçada** | Schema de frontmatter (EPIC-01), hierarquia nativas > MCP, checklist de onboarding, política de camadas. Falta: pipeline de validação automática do corpus. |

### ⚠️ Riscos críticos para escala

1. **Busca por keywords não escala para 100+ documentos.** Com 8 docs, a sobreposição de keywords funciona razoavelmente. Com 100+ docs sobre temas correlatos (.NET, C#, microserviços), a precisão do ranking tende a degradar significativamente. O repo reconhece isso (E4) mas não tem plano de implementação.

2. **Sem mecanismo de atualização automática do corpus local.** O EPIC-03 propõe "clone único + variável de ambiente" como distribuição. Com 100+ devs, confiar em `git pull` manual é frágil. A análise de distribuição central (2026-04-09) propõe solução completa, mas nenhuma parte está implementada.

3. **Sem validação de conformidade do corpus.** Não há pipeline CI que valide que todos os `.md` do corpus têm frontmatter válido, `id` único, e campos obrigatórios. O `ci.yml` roda apenas `pytest` no servidor Python.

4. **`resolve_instructions_for_file` é classificada como "CRÍTICO" mas não está implementada.** Essa é a tool que mais impactaria a precisão contextual em escala — sem ela, cada dev recebe os mesmos 5 resultados genéricos independentemente do arquivo que está editando.

---

## 6. 🏗️ Arquitetura Recomendada

### 🔹 Visão Alto Nível

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA RECOMENDADA                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────┐                               │
│  │  Copilot Spaces (se disponível)  │  ← Contexto compartilhado    │
│  │  • Documentação de projeto       │    de alto nível por time     │
│  │  • ADRs, diagramas, glossário    │                               │
│  └──────────────────┬───────────────┘                               │
│                     │                                               │
│  ┌──────────────────▼───────────────┐                               │
│  │  .github/copilot-instructions.md │  ← Pseudo-hook (5–15 regras) │
│  │  • Idioma, segurança, escopo     │    SEMPRE no contexto         │
│  │  • Orquestração genérica MCP     │                               │
│  │  • Gestão de sessão (opcional)   │                               │
│  └──────────────────┬───────────────┘                               │
│                     │                                               │
│  ┌──────────────────▼───────────────┐                               │
│  │  .github/instructions/*.md       │  ← applyTo por arquivo/glob  │
│  │  • Regras específicas por área   │    (mecanismo nativo)         │
│  │  • Ex: "Api/**" → padrões REST   │                               │
│  └──────────────────┬───────────────┘                               │
│                     │                                               │
│  ┌──────────────────▼───────────────┐                               │
│  │  MCP Server (STDIO local)        │  ← Retrieval sob demanda     │
│  │                                  │                               │
│  │  TOOLS:                          │                               │
│  │  • search_instructions           │                               │
│  │  • get_instruction               │                               │
│  │  • resolve_instructions_for_file │  ← PRIORIDADE 1              │
│  │  • list_instructions_index       │                               │
│  │                                  │                               │
│  │  RESOURCES:                      │                               │
│  │  • Padrões categorizados         │  ← Base persistente           │
│  │  • Glossário de domínio          │    endereçável                │
│  │                                  │                               │
│  │  PROMPTS:                        │                               │
│  │  • Templates de tarefa           │  ← Workflows padronizados    │
│  │  • "Criar endpoint ponta a ponta"│                               │
│  └──────────────────┬───────────────┘                               │
│                     │                                               │
│  ┌──────────────────▼───────────────┐                               │
│  │  Corpus Central Versionado       │  ← Fonte da verdade          │
│  │  • .md com frontmatter YAML      │    (repo Git dedicado)       │
│  │  • Pipeline CI de validação      │                               │
│  │  • Distribuição via release/zip  │                               │
│  └──────────────────────────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 🔹 Camada Tática — O que mudar no repositório atual

1. **Corrigir o template thin** — remover referências a tools inexistentes; decidir entre estilo explícito ou genérico:

```markdown
# Instruções locais (camada mínima)

- **Idioma**: português.
- **Segurança**: nunca inclua segredos/tokens/dados pessoais.
- **Escopo**: não assuma código/infra de outros serviços.
- **Limites**: se faltar dado decisivo, explicite a inferência e ofereça 2–3 opções.

## Contexto do repositório

- **Descrição:** {{DESCRIÇÃO_DO_PROJETO}}
- **Stack:** {{STACK_COMPLETA}}

## Padrões organizacionais (via MCP)

Para padrões de arquitetura, convenções, segurança, resiliência ou dúvida sobre
convenções: consulte o MCP `corporate-instructions` antes de propor código.

As regras **deste arquivo** prevalecem se houver conflito com o MCP.

## Fluxo de trabalho

- Antes de editar arquivos críticos: leia o arquivo alvo.
- Após mudanças substanciais: rode build/testes.
```

2. **Implementar `resolve_instructions_for_file`** — tool classificada como CRÍTICO no roadmap; usa `fnmatch`/`pathlib` para matching de glob contra `scope` do frontmatter.

3. **Adicionar pipeline de validação do corpus** — CI que verifica frontmatter, `id` único, campos obrigatórios em todos os `.md`.

4. **Avaliar Copilot Spaces** — investigar se resolve parte do problema de contexto compartilhado sem precisar de MCP para tudo.

### 🔹 Camada Baixo Nível — Pseudocódigo para melhorias prioritárias

**`resolve_instructions_for_file` (prioridade 1):**

```python
@mcp.tool()
def resolve_instructions_for_file(file_path: str) -> str:
    """Use when editing or creating a file to discover which organizational
    rules apply to it. Returns instructions whose scope matches the file path,
    ordered by priority (high > medium > low)."""
    idx = _ensure_index()
    matches = []
    for rec in idx.values():
        if rec.scope and _glob_match(file_path, rec.scope):
            matches.append(rec)
    matches.sort(key=lambda r: -PRIORITY_RANK.get(r.priority, 0))
    # retornar metadados + resumo de cada instrução aplicável
    return json.dumps({"file": file_path, "applicable": [...]})
```

**Pipeline de validação do corpus (CI):**

```yaml
# .github/workflows/validate-corpus.yml
- name: Validate corpus frontmatter
  run: |
    python -c "
    from corporate_instructions_mcp.indexing import build_index
    from pathlib import Path
    idx = build_index(Path('fixtures/instructions'))
    for rec in idx.values():
        assert rec.id, f'Missing id: {rec.rel_path}'
        assert rec.title, f'Missing title: {rec.rel_path}'
    print(f'Validated {len(idx)} documents')
    "
```

---

## ⚙️ Modelo de Comportamento do Copilot (Padrões Identificados)

Com base nos experimentos e análises do repositório, os seguintes padrões de comportamento do Copilot foram identificados ou inferidos:

| Padrão | Tipo | Descrição |
|--------|------|-----------|
| Injeção do system prompt | ✅ FATO | `copilot-instructions.md` é injetado em toda interação |
| Tool invocation baseada em `description` | ✅ FATO | Descrições "Use when…" orientam quando o Copilot chama tools |
| Reatividade (sem proatividade) | ✅ FATO | Copilot não tem hooks proativos; toda ação requer prompt |
| Matching mental de scope | ⚠️ RISCO | Copilot tenta inferir quais instruções aplicam sem tool dedicada — gasta tokens e erra |
| Hierarquia nativas > MCP | HIPÓTESE | A instrução "nativas prevalecem" é respeitada porque está no system prompt, mas não há teste de stress |
| Comportamento emergente com "Token Economy" | ⚠️ RISCO | Correlação observada; causalidade não confirmada |
| Encadeamento de tools | HIPÓTESE | O Copilot consegue encadear list → search → get, mas a taxa de sucesso não é medida |

---

## ⚠️ Falhas e Riscos Identificados

### ❌ Falhas concretas

1. **Template thin desalinhado com o servidor** — I3 da [análise técnica de 2026-04-07](2026-04-07-analise-tecnica-reestruturacao-copilot-instructions-thin.md) identificou referência a `compose_context` (tool inexistente); decisão "iterar" não resultou em correção. O template canônico pode induzir o Copilot a tentar chamar uma tool que não existe.

2. **Nenhum experimento A/B executado** — Os 5 experimentos propostos no EPIC-04 (E1–E5) não foram executados. As conclusões são baseadas em observação qualitativa de caso único.

3. **Busca por keywords sem avaliação de precisão** — O `score_record` usa contagem de tokens + boost por título/tags/priority. Não há benchmark de Precision@K nem avaliação de recall com queries reais.

4. **Ausência de Copilot Spaces na análise** — Mecanismo oficial do GitHub para contexto compartilhado é completamente ignorado.

5. **Corpus de teste muito pequeno (8 docs)** — Todos os testes e experimentos usam 8 documentos. A viabilidade para 100+ docs é extrapolada, não demonstrada.

### ⚠️ Riscos estratégicos

| Risco | Impacto | Probabilidade | Mitigação proposta no repo |
|-------|---------|---------------|---------------------------|
| Degradação de precisão com corpus grande | Alto | Alta | E4 (embeddings) — **não executado** |
| Drift de corpus entre devs | Alto | Alta | `check_instruction_updates` — **não implementado** |
| Tool não invocada pelo Copilot | Médio | Média | Descrições "Use when…" — implementado, não medido |
| Conflito nativas vs. MCP | Médio | Média | Hierarquia documentada — **não testado em stress** |
| Saturação da janela de contexto | Médio | Média | Gestão qualitativa — **não validada comparativamente** |
| Falsa sensação de completude | Alto | Média | — **sem mitigação** — o entusiasmo nos experimentos pode mascarar lacunas |

---

## 🚀 Recomendações (priorizadas)

### Prioridade Alta (fazer agora)

1. **Corrigir o template thin** — Remover referências a tools inexistentes. Decidir explícito vs. genérico e alinhar. Isso é dívida de governança aberta.

2. **Implementar `resolve_instructions_for_file`** — A tool mais impactante do roadmap. Sem ela, a precisão contextual é limitada e o Copilot gasta tokens inferindo escopo.

3. **Executar E1 (nativas reduzidas + MCP vs. só nativas)** — Sem esse experimento, a tese central do repositório permanece hipótese. Usar os mesmos 5–10 prompts com e sem MCP, medir aderência a padrões.

4. **Adicionar pipeline de validação do corpus** — CI simples: verificar frontmatter, `id` único, campos obrigatórios. Previne drift de qualidade do corpus.

### Prioridade Média (próximo ciclo)

5. **Investigar Copilot Spaces** — Avaliar se resolve parte do problema sem complexidade do MCP. Pode ser complementar (Spaces para ADRs/glossário, MCP para retrieval parametrizado).

6. **Aumentar corpus para 30–50 documentos** — Testar degradação de precisão da busca por keywords antes de escalar para 100+. Medir Precision@5.

7. **Executar E2 (descrições "Use when…" vs. genéricas)** — Medir taxa real de invocação de tools. Isso é premissa fundamental da estratégia.

8. **Implementar MCP resources** — Expor categorias de instrução como resources endereçáveis, não apenas tools de busca.

### Prioridade Baixa (futuro)

9. **Prototipar busca semântica (E4)** — Embeddings para queries vagas. Só vale após validar que keyword search é insuficiente com corpus maior.

10. **Prototipar distribuição central** — A análise de 2026-04-09 propõe arquitetura completa com manifesto/staging/swap. Implementar MVP quando houver 10+ devs consumindo o corpus.

---

## 🧾 Veredito Final

- **Veredito geral:** A estratégia está **fundamentalmente correta na direção**, mas **insuficientemente validada na prática**. O modelo híbrido (nativas finas + MCP centralizado) é uma abordagem tecnicamente sólida para o problema de 100+ repos. Porém, as conclusões do repositório são predominantemente baseadas em **inferência e observação qualitativa**, não em **evidência empírica controlada**. A distância entre "demonstrou viabilidade técnica" e "validou superioridade para escala" ainda é grande.

- **O que está certo:**
  - ✅ Separação nativo (sempre-ativo) vs. MCP (sob demanda) é correta e bem fundamentada
  - ✅ Hierarquia de precedência (nativas > MCP) é clara e consistente
  - ✅ Servidor MCP funcional com 3 tools e contratos bem definidos
  - ✅ Schema de frontmatter (EPIC-01) com id/title/tags/scope/priority/kind é sólido
  - ✅ Conceito de "pseudo-hook" via `copilot-instructions.md` é criativo e prático
  - ✅ Análise técnica comparativa (STDIO vs. HTTP vs. Híbrido) é neutra e bem estruturada
  - ✅ Roadmap de 6 tools adicionais é coerente com os gaps identificados

- **O que está errado:**
  - ❌ Template thin desalinhado com servidor real (tool inexistente referenciada)
  - ❌ Nenhum experimento A/B executado — tese central permanece hipótese
  - ❌ Copilot Spaces completamente ignorado como mecanismo oficial
  - ❌ Corpus de teste (8 docs) é insuficiente para validar escala (100+ docs)
  - ❌ Resources e Prompts MCP não explorados apesar de reconhecidos na análise

- **O que ajustar:**
  - 🔧 Corrigir template thin imediatamente
  - 🔧 Implementar `resolve_instructions_for_file` (classificada como CRÍTICO pelo próprio repo)
  - 🔧 Executar ao menos E1 e E2 do EPIC-04 antes de adotar em produção
  - 🔧 Adicionar validação CI do corpus
  - 🔧 Investigar Copilot Spaces como complemento
  - 🔧 Testar com corpus de 30–50 docs para validar busca por keywords

- **Próximos passos:**
  1. Sprint de correção: template thin + `resolve_instructions_for_file` + CI de validação
  2. Sprint de validação: executar E1 e E2 com métricas quantitativas
  3. Sprint de expansão: corpus para 30–50 docs + avaliar Copilot Spaces
  4. Decisão: com dados de E1/E2/precisão com corpus maior, decidir se escala ou pivota

---

> **Nota do auditor:** Este repositório representa um esforço de pesquisa **acima da média** para o ecossistema Copilot. O problema é real, a abordagem é fundamentada, e a documentação é exemplar. As críticas acima não diminuem o valor do trabalho — elas apontam o caminho para transformar uma **prova de conceito promissora** em uma **solução validada para escala organizacional**.
