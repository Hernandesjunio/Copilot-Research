---
id: instruction-authoring-standard
title: "Corpus — padrão de autoria de instructions"
tags: [governance, meta-governance, instructions, frontmatter, corpus, mcp]
scope: "**/*.md"
priority: medium
kind: policy
owner: platform-architecture
last_reviewed: 2026-05-10
status: active
---

# Objetivo

Garantir que novas ou alteradas instructions no corpus canónico sejam **recuperáveis**, **normativamente claras** e **fáceis de manter**, utilizáveis com ferramentas MCP típicas de catálogo e leitura de instructions (`list_instructions_index`, `search_instructions`, `get_instructions_batch`).

## Nomes das tools MCP (orientação ao agente assistido ou autónomo)

Os **identificadores exactos** das tools são parte do contrato entre o cliente (IDE, agente ou orquestrador) e o servidor MCP — use **literais** iguais aos do catálogo exposto pelo servidor (`tools/list`). Não abreviar nem substituir por descrições vagas («listar corpus», «fazer pesquisa») quando o fluxo depende da chamada correcta à API.

Fluxo típico de descoberta e leitura (ordem recomendada):

| Tool | Papel principal |
| --- | --- |
| `list_instructions_index` | Inventário do corpus, tags, estado do índice e diagnósticos úteis antes de pesquisas amplas. |
| `search_instructions` | Resolver temas ou linguagem natural a candidatos (`id`, scores, fragmentos contextuais). Suportar múltiplas queries quando a tarefa tiver vários eixos. |
| `get_instructions_batch` | Obter **corpo completo** e `frontmatter` de um conjunto de `id`s escolhidos — evita ler só títulos ou excertos da busca quando a decisão precisa do texto integral. |

O servidor pode expor **tools adicionais** além destas três (conformidade, triggers, sequências recomendadas, etc.). Para trabalho só sobre o catálogo e o conteúdo normativo, as três acima são a espinha dorsal; nomes completos e parâmetros vêm sempre do MCP em uso nesta sessão.

## TL;DR

- Cada ficheiro começa por **frontmatter YAML** com, no mínimo: `id`, `title`, `tags`, `scope`, `priority`, `kind`.
- Políticas (`kind: policy`) devem incluir **tabela de decisão** ou critérios explícitos, secções **Pode ser feito** / **Não pode ser feito**, e preferencialmente **anti-exemplos**.
- Manter `id` estável após publicação; mudanças incompatíveis → novo `id` e deprecar o anterior no texto.
- Campos recomendados para governança: `owner`, `last_reviewed`, `status` (`draft` | `active` | `deprecated`).
- Campos **opcionais** de aplicabilidade ao workspace (`workspace_evidence_required`, `workspace_signals`, `on_absence`): definidos na secção abaixo — **não** são obrigatórios em todo o corpus; a equipa proprietária do corpus pode torná-los obrigatórios por política própria.
- Existe também um **mapa modular de expansão de query** em YAML sob `metadata/corpus-query-expansion-map/` na raiz do corpus de instructions que o MCP está configurado para ler. Esse mapa é **distinto** do frontmatter Markdown; regras completas na secção homónima mais abaixo.
- Para navegar ou aplicar norms do corpus já publicado via MCP: seguir ordem típica `list_instructions_index` → `search_instructions` → `get_instructions_batch`, com nomes de tools literais conforme § **Nomes das tools MCP**.

## Valores de `kind`

| kind | Uso |
| --- | --- |
| `policy` | Norma mandatória; a IA não deve contradizer sem exceção aprovada. |
| `reference` | Guia, contexto, padrões técnicos sem força de lei total. |

Outros valores de `kind` (`adr`, `template`, `catalog`, `playbook`) podem ser adoptados quando o cliente MCP e políticas internas os suportarem; até lá, usar `reference` com `tags` descritivas.

## Aplicabilidade ao workspace (consumo por clientes MCP / assistentes)

Estes campos servem para o cliente combinar **norma do corpus** com **evidência no repositório de código do utilizador**. O servidor MCP que só lê instructions **não** inspecciona o repositório do utilizador por si; os campos são expostos (por exemplo) em metadados devolvidos ao pedir uma instruction em lote (`get_instructions_batch`).

### Obrigatoriedade por defeito

| Campo | Obrigatório em todas as `.md`? | Quem alinha valores |
| --- | --- | --- |
| `workspace_evidence_required` | **Não** | Equipa ou política do corpus |
| `workspace_signals` | **Não** | Equipa ou política do corpus |
| `on_absence` | **Não** | Equipa ou política do corpus |

**Norma recomendada:** estes três campos devem surgir onde fizer sentido (**SHOULD**), em políticas que **prescrevam infraestrutura, bibliotecas ou DI concretos** que o serviço alvo pode ainda não possuir (exemplos típicos: cache distribuído, mensageria, tolerância a falhas, fábrica de clientes HTTP, telemetria, opções e injecção de dependências, configuração operacional, acesso a dados com stack específica). Instructions puramente contratuais ou de processo (semântica HTTP, validação, camadas só conceptuais, meta-processo organizacional, catálogo interno de erros, etc.) **não precisam** destes campos; podem ganhá-los mais tarde se o risco for “norma concreta sem evidência no repositório”.

### Semântica sugerida

| Campo | Tipo | Uso |
| --- | --- | --- |
| `workspace_evidence_required` | boolean | Se `true`, o assistente deve procurar correspondência aos `workspace_signals` no código **antes** de impor o padrão normativo. |
| `workspace_signals` | lista de strings | Identificadores ou termos a procurar (grep, leitura de arranque da aplicação, DI, etc.). Curadoria manual — não substituir o corpo da policy. |
| `on_absence` | string | Comportamento quando não há correspondência; valor comum: `hypothesis_only` (não introduzir infra nova; documentar hipótese ou pedir confirmação). |

Outros valores de `on_absence` podem ser definidos pela equipa (`confirm_with_user`, `do_not_implement`, etc.).

## Mapa de expansão de query (YAML em `metadata/corpus-query-expansion-map/`)

Esta secção define a relação entre **instructions Markdown** e o **mapa de expansão de query**. Nenhum hyperlink externo é necessário para aplicar estas regras.

### Separar conceitos: `scope` (frontmatter) e `applies_to` (mapa)

| Onde está | Campo | Significado |
| --- | --- | --- |
| Frontmatter YAML de cada `.md` | `scope` | Indica **a que ficheiros ou áreas documentais da vida do software** esta instruction diz respeito (glob escolhido pela equipa, ex.: `**/*.cs`, `**/Api/**/*.cs`, `**/*.md` para texto só de governação interna ao corpus). |
| Ficheiros YAML do mapa, por entrada de termo | `applies_to` (opcional) | Lista de **globs genéricos** (extensão ou padrões de nome de artefato, não pastas próprias de um produto) usada pelo mecanismo de **expansão de query** quando o cliente envia um **caminho de ficheiro actual** junto à busca (`current_file_path`). Se esse caminho não for enviado, `applies_to` **no mapa não deve** causar falsos negativos em queries gerais (regra de comportamento esperada da implementação). |

O campo `applies_to` **não** existe nem deve ser introduzido no frontmatter Markdown da instruction — só nos YAML do mapa.

### Curadoria e evidência

- O mapa **não** se gera sozinho a partir do corpus; **curadoria humana** é obrigatória para o conteúdo útil do mapa.
- Cada relação numa entrada do mapa (`aliases`, `strong_terms`, `weak_terms`, `activation_terms`, e cada padrão em `applies_to`) deve poder ser **justificada** pelo texto e metadados da instruction ou instructions de origem, usando pelo menos uma destas fontes quando existirem: `id`, `title`, `summary`, `tags`, títulos e rubricas Markdown (headings), bloco **`TL;DR`**, corpo Markdown, e **secções explícitas sobre aplicabilidade ao workspace ou sobre vocabulário que ajude a recuperar o documento** (quando existirem).
- **Rastreabilidade:** sobre cada entrada no YAML recomenda-se um comentário iniciado por `# source:` com o ou os `id` das instructions que sustentam a entrada — é convenção para humanos e revisão; não confundir com campo obrigatório de schema até ser formalizado noutra versão da política.
- **`weak_terms`:** usar com parcimónia — listas grandes aumentam recall e **diminuem precisão** na busca por sobreposição; a equipa que opera o MCP deve prever critérios de aceite e testes do tipo *must-not-expand* para termos sensíveis.
- Para **reduzir ambiguidade entre contextos** no mesmo termo canónico, evitar `activation_terms` **genéricos demais** partilhados por vários ramos (ex.: um token vago comum a duas tecnologias distintas).
- Ao curar uma entrada ligada a uma instruction neste padrão, poderá ajudar alinhar ideias aos bullets de **Pode ser feito** / **Não pode ser feito** dessa instruction — isto é **opcional**, não obrigatório para publicar no mapa.

### Regra de unicidade entre ficheiros do mapa

O mesmo termo canónico **não** pode aparecer em dois ficheiros YAML de namespace distintos **sem** substituição explícita da definição anterior (quando o schema do mapa previr `override` e justificativa). Em caso de duplicidade não resolvida, o mapa deve ser tratado como **inválido** até o conflito ser corrigido.

## Estrutura mínima sugerida (Markdown)

1. **Objetivo** — uma frase.
2. **TL;DR** — bullets acionáveis.
3. **Tabela de decisão** ou **Critérios** — quando houver ramos de comportamento.
4. **Snippet** (opcional) — exemplo curto e anónimo.
5. **Pode ser feito** / **Não pode ser feito** — limites claros.
6. **Anti-exemplos** — para políticas sensíveis a extrapolação.
7. **Impacto esperado na resposta da IA** ou **Quando explicitar incerteza** — quando a instruction orienta assistentes.

## Pode ser feito

- Referenciar outras instructions pelo `id` em texto de corrido (ex.: «ver `microservice-rest-http-semantics-and-status-codes`»).
- Duplicar apenas o estritamente necessário; preferir um documento canónico e referências internas por `id`.
- Definir `scope` como glob documental coerente com o repositório alvo (ex.: `**/Api/**/*.cs`); ajustar quando o corpus for servido a partir de outra raiz.
- Manter `tags`, `TL;DR`, headings e corpo com vocabulário que suporte a **lista de evidência** descrita na secção **Mapa de expansão de query** (mesma enumeração de fontes: `id`, `title`, `summary`, `tags`, headings, `TL;DR`, corpo, secções explícitas de aplicabilidade ou termos de recuperação quando existirem).

## Não pode ser feito

- Publicar `policy` sem qualquer critério verificável (só narrativa vaga).
- Reutilizar o mesmo `id` para um tema diferente do original.
- Colocar regras exclusivas de um produto ou entidade de negócio num documento pensado para **vários** repositórios sem deixar o **scope** documental explícito quanto a quem deve seguir a norma.
- Declarar `applies_to` no frontmatter de uma instruction `.md` — esse campo pertence **só** aos YAML em `metadata/corpus-query-expansion-map/`, separado do Markdown.

## Anti-exemplos

- Instruction muito longa sem `TL;DR` nem critérios de decisão — dificulta recuperação por palavras-chave.
- Tags demasiado genéricas (`dotnet`, `code`) sem substantivos de domínio (`rest`, `validation`, mensageria, etc.).
