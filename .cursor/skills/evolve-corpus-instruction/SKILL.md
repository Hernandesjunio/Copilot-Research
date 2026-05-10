---
name: evolve-corpus-instruction
description: >-
  Padroniza instruction files do corpus (.md sob fixtures/instructions/ ou pasta
  indicada pelo utilizador) e extrai propostas para o Corpus Query Expansion
  Map (YAML), alinhado a instruction-authoring-standard.md. Suporta Multitask:
  um agente por ficheiro elegível (exclui governança e metadata por defeito).
  Merge em YAML do mapa num único passo. Ao implementar frontmatter ou entradas
  YAML, usar os templates nesta pasta de skill. Use quando pedir standardize,
  auditar, evoluir instructions ou gerar/atualizar entradas do expansion map.
disable-model-invocation: true
---

# Evolve Corpus Instruction

Duas operações, usadas em conjunto ou separadamente:

1. **Standardize** — auditar e corrigir um instruction file contra `fixtures/instructions/instruction-authoring-standard.md`.
2. **Extract expansion** — derivar **propostas** YAML para o Corpus Query Expansion Map a partir do conteúdo e metadados da instruction, com evidência rastreável.

**Guias de implementação (uso obrigatório pelo agente ao escrever metadados ou entradas de mapa):**

- Frontmatter novo ou normalizado → seguir campo a campo e regras em [templates/frontmatter-template.md](templates/frontmatter-template.md).
- Snippets sob `terms:` no mapa → seguir estrutura, exemplos comentados e regras de schema em [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml) (consistente com ADR-002).

---

## Âmbito de trabalho por pasta

- **Raiz por defeito do corpus de exemplo neste repo:** `fixtures/instructions/`.
- O utilizador pode indicar **outra pasta** dentro do workspace (mantendo o mesmo propósito: ficheiros de instruction `.md`).
- **`fixtures/instructions/instruction-authoring-standard.md`** é **sempre** a fonte canónica de regras (ler antes de auditar/extrair). **Nunca** é ficheiro-alvo em lote paralelo nem “mais uma instruction” a standardizar pelo mesmo fluxo — é governança do corpus.

**Conjunto elegível para alvo de Standardize / Extract (por defeito neste repo):**

- Incluir: `fixtures/instructions/*.md`.
- **Excluir sempre:** `fixtures/instructions/instruction-authoring-standard.md`.
- **Excluir por defeito** (salvo pedido explícito do utilizador para incluir): `fixtures/instructions/metadata/**` (READMEs do mapa, etc.) — não são instructions do catálogo.

Se o utilizador disser apenas “corrige a pasta `fixtures/instructions/`”, aplicar estas exclusões automaticamente antes de paralelizar.

---

## Fonte canónica obrigatória (leitura)

Sempre alinhar com:

- `fixtures/instructions/instruction-authoring-standard.md`

Se houver discrepância entre esta skill e esse ficheiro **no repositório**, prevalece o standard.

---

## Operação 1: Standardize

### Fontes a ler antes de auditar

- `fixtures/instructions/instruction-authoring-standard.md`
- [templates/frontmatter-template.md](templates/frontmatter-template.md) — guia para completar/normalizar YAML do topo do `.md`.
- O ficheiro instruction alvo

### Valores de `kind` (alinhamento ao standard)

| kind | Uso |
|------|-----|
| `policy` | Norma mandatória; a IA não deve contradizer sem exceção aprovada. |
| `reference` | Guia ou contexto sem força normativa total. |

Outros valores (`adr`, `template`, `catalog`, `playbook`) **só** se o cliente MCP e políticas internas os suportarem; até lá preferir `reference` com `tags` descritivas — **perguntar ao utilizador** se encontrares `kind` fora da tabela antes de renomear.

### Auditoria de frontmatter

**Campos obrigatórios** — presentes e não vazios:

| Campo | Regra |
|-------|-------|
| `id` | Nome do ficheiro sem `.md`; kebab-case; estável após publicação (**nunca** mudar só para “alinhar texto”; tema diferente ⇒ novo `id` + deprecar o anterior **no texto**, conforme standard). |
| `title` | Legível por humanos; máx ~80 caracteres |
| `tags` | Lista YAML; **mínimo 2 tags substantivas** de domínio; evitar tags demasiado genéricas isoladas (`dotnet`, `code` sem substantivo de tema — ver anti‑exemplos no standard e template). |
| `scope` | Glob documental coerente (ex.: `"**/*.cs"`, `"**/Api/**/*.cs"`); usar `"**/*.md"` para meta/governança no corpus |
| `priority` | `low` \| `medium` \| `high` |
| `kind` | Ver tabela **Valores de kind** |

**Separação explícita (standard):** `scope` está **só** no frontmatter Markdown. **`applies_to` não existe nem pode ser introduzido** no frontmatter — pertence apenas aos YAML do mapa sob `metadata/corpus-query-expansion-map/`.

**Campos recomendados** — adicionar se ausentes:

| Campo | Valor |
|-------|-------|
| `owner` | Equipa ou pessoa responsável |
| `last_reviewed` | Data ISO `YYYY-MM-DD` |
| `status` | `draft` \| `active` \| `deprecated` |

**Campos opcionais de aplicabilidade ao workspace** — **norma SHOULD** onde fizer sentido (standard): políticas que **prescrevem infra, bibliotecas ou DI concretos** cuja adoção pode não existir no repo alvo.

| Campo | Tipo | Regra |
|-------|------|-------|
| `workspace_evidence_required` | boolean | `true` quando o cliente deve verificar correspondência a `workspace_signals` **antes** de impor a norma |
| `workspace_signals` | lista de strings | Termos/classes a procurar (grep arranque, DI…); curadoria manual |
| `on_absence` | string | Comum `hypothesis_only`; a equipa pode definir outros (`confirm_with_user`, `do_not_implement`, …) |

**Não** acrescentar estes três campos em instructions puramente contratuais ou de processo (semântica HTTP, validação, layering só conceptual, meta-processo, catálogo de erros, BMAD só processual, etc.), salvo revisão explícita com o utilizador.

### Políticas `kind: policy` — critérios verificáveis

Conforme standard: **não** pode publicar-se `policy` **sem qualquer critério verificável** (apenas narrativa vaga).

Na auditoria:

- Confirmar existência de **tabela de decisão** OU **Critérios** explícitos quando há ramos de comportamento, e limites claros (**Pode ser feito** / **Não pode ser feito**).
- Se faltar ambos estrutura mínima e critérios, **adicionar** secções com `<!-- TODO -->` e registar no relatório — não inventar norma nova sem base no corpo existente.

### Conteúdo orientado a agentes MCP (quando aplicável)

Se a instruction orienta uso do catálogo MCP (fluxo típico de descoberta e leitura), o standard exige referência aos **nomes literais** das tools (`list_instructions_index`, `search_instructions`, `get_instructions_batch`) — não substituir por descrições vagas quando o fluxo depende da API.

- **Verificar** documentos de governança/meta quando o tema for “como navegar o corpus”.
- Para instructions de domínio que **não** falam de MCP, não forçar bloco inteiro de tools.

### Estrutura mínima sugerida (Markdown) — checklist

Ordem alinhada ao standard **§ Estrutura mínima sugerida**:

1. `# Objetivo` — uma frase
2. `## TL;DR` — bullets acionáveis
3. `## Tabela de decisão` ou critérios explícitos — quando há ramos (**policy**: obrigatório quando há ramos)
4. `## Snippet` (opcional)
5. `## Pode ser feito` / `## Não pode ser feito` — (**policy**: obrigatório)
6. `## Anti-exemplos` — onde `policy` for prescritiva ampla
7. `## Impacto esperado na resposta da IA` ou `## Quando explicitar incerteza` — quando orienta assistentes e a secção falta

Para `kind: reference`: flexível; **mínimo** `# Objetivo` e `## TL;DR`.

### Lembranças “Pode ser feito” / “Não pode ser feito” (standard)

- Referenciar outras instructions pelo `id` em texto contínuo; preferir canónico + referências.
- Manter vocabulário alinhado às fontes de evidência do mapa (tags, TL;DR, headings, corpo, secções de recuperação).

Proibições na edição:

- Reutilizar o mesmo `id` para tema diferente.
- Regras exclusivas de produto sem `scope` explícito para quem deve seguir.
- Introduzir `applies_to` no frontmatter Markdown.

### Aplicar correções

- **Nunca** remover conteúdo existente (adicionar, clarificar ou corrigir inconsistências com o standard).
- **Nunca** alterar `id` publicado sem fluxo de deprecação acordado.
- `owner` desconhecido ⇒ **perguntar**.
- Secções em falta: placeholders com `<!-- TODO -->` quando não inferível.

### Relatório de alterações

- Frontmatter e secções alteradas; omissões intencionais com citação ao standard; TODOs deixados.

---

## Operação 2: Extract Corpus Query Expansion Map

### Princípios do standard (obrigatórios)

- Curadoria humana obrigatória para merge útil; o agente **prepara** snippets e justificativas.
- Cada relação deve ser **justificável** por: `id`, `title`, `summary` (se existir), `tags`, headings, `## TL;DR`, corpo, secções de aplicabilidade ou recuperação.
- **`weak_terms`:** parcimônia; **`activation_terms`:** evitar tokens genéricos partilhados entre ramos.
- **Rastreabilidade:** comentário YAML `# source: <id>` por entrada (ver comentários no [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml)).
- **Unicidade:** o mesmo termo canónico **não** pode existir em dois ficheiros de namespace sem `override` explícito; reportar duplicados.

### Fontes a ler antes de extrair

- Instruction alvo + [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml) como guia de shape e regras de `contexts` / `applies_to`.
- `fixtures/instructions/metadata/corpus-query-expansion-map/README.md`
- Ficheiro YAML de namespace provável e **todos** os `*.yml` do mapa (leitura) para unicidade

### Identificar termos canónicos

Candidatos: `tags`, partes do `id` (stop words: `microservice`, `and`, `or`), `summary` se existir, nomes técnicos no corpo, substantivos do TL;DR/headings.

### Mapear relações, `expansion_mode`, namespaces

Seguir tabelas e regras já definidas no standard, ADR-002, README do mapa, e exemplos em [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml).

| Prefixo | Namespace | Usar para |
|---------|-----------|-----------|
| `00-core.yml` | `core` | Termos transversais |
| `10-dotnet.yml` | `dotnet` | .NET runtime, C#, SDK |
| `20-api.yml` | `api` | REST, HTTP, contratos |
| `30-data.yml` | `data` | SQL, repositórios, ORM |
| `40-messaging.yml` | `messaging` | Filas, eventos, async |
| `50-observability.yml` | `observability` | Telemetria, health, logs |
| `60-security.yml` | `security` | Auth, authz, segredos |
| `70-architecture.yml` | `architecture` | Camadas, padrões, SOLID |
| `80-governance.yml` | `governance` | Meta, planeamento, processo |
| `90-project-specific.yml` | `project` | Termos específicos deste corpus |

### Output da extração

1. Snippet YAML para fusão sob `terms:` usando o template como referência estrutural, com `# source:`.
2. Relatório: ficheiro alvo, novos vs existentes, duplicidades entre YAMLs.
3. Termo já existente: diff sugerido e **parar** para decisão de merge.

---

## Paralelização (Multitask / vários agentes)

**Compatível com Multitask** quando cada subagente recebe **um único caminho** `.md` do **conjunto elegível** (secção **Âmbito de trabalho por pasta**): assim manténs contexto isolado por ficheiro, evitas corrida ao escrever o mesmo Markdown e aplicás a exclusão obrigatória de `instruction-authoring-standard.md` como alvo.

| Fase | Paralelo? | Regra |
|------|-----------|--------|
| **Standardize** | **Sim** | Um `.md` por agente; caminho dentro da pasta indicada; **proibido** editar `instruction-authoring-standard.md` como alvo; **não** editar YAML do mapa nesta fase sem consolidação. |
| **Extract** (só snippets) | **Sim** | Igual âmbito; ler YAMLs do mapa em modo read-only para duplicados; **não** gravar `metadata/corpus-query-expansion-map/*.yml` no paralelo. |
| **Merge no mapa** | **Não em paralelo** | Um passo único (ou sequência explícita por ficheiro YAML) após rever `# source:` e unicidade. |

**Prompt sugerido (por agente, com Multitask):** “Segue a skill `evolve-corpus-instruction`. Pasta de trabalho: `<pasta>`. Alvo **único**: `<ficheiro.md>`. Excluir governança e metadata conforme a skill. Operações: [Standardize | Extract | ambas]. Não modificar `metadata/corpus-query-expansion-map/*.yml` se Extract estiver a correr em paralelo — apenas entregar snippets.”

**Fluxo combinado:** (1) N agentes Standardize em paralelo, um por ficheiro elegível; (2) N agentes Extract em paralelo; (3) **um** consolidador aplica merges ao YAML.

---

## Referências

- Padrão de autoria: `fixtures/instructions/instruction-authoring-standard.md`
- Guia frontmatter: [templates/frontmatter-template.md](templates/frontmatter-template.md)
- Guia entradas do mapa: [templates/expansion-entry-template.yml](templates/expansion-entry-template.yml)
- Convenções do expansion map: `fixtures/instructions/metadata/corpus-query-expansion-map/README.md`
- ADR do mapa: `planning/adr/ADR-002-corpus-query-expansion-map.md`
