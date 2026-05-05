# 2026-05-05 — Redirecionamento: MCP Instruction Retrieval v1 (pausa do compositor)

## Contexto

Durante a evolução do servidor MCP de *instruction retrieval* para um **compositor automático de contexto**, foram observados sinais de **acoplamento ao corpus atual** (fixtures) e risco de **overfitting**: o sistema começou a “aprender o conjunto” (IDs, padrões e exceções) em vez de melhorar a capacidade geral de recuperação e aplicabilidade de instruções normativas.

Essa experiência é comum em projetos de retrieval + agentes: quando a base de recuperação ainda não está estável, um compositor tende a compensar falhas com heurísticas cada vez mais específicas, o que prejudica generalização para novos domínios/corpus.

## Sintoma / problema observado

- O MCP passou a tentar fazer coisas demais simultaneamente (classificar intenção, ranquear, selecionar primários e supporting, deduplicar, evitar meta/governance, montar bundle final).
- As correções tenderam a virar *tuning* para a suíte e para o corpus do momento (regras, boosts/demotions, caminhos de sinônimos).
- O foco saiu do objetivo principal: **tornar a instrução normativa correta fácil de encontrar e carregar** para que o agente decida a aplicação.

## Decisão

**Pausar a evolução do compositor** e consolidar a fase **MCP Instruction Retrieval v1**:

- Manter e fortalecer as **3 tools básicas**:
  - `list_instructions_index`
  - `search_instructions`
  - `get_instruction` / `get_instructions_batch`
- O MCP **não** monta contexto final nesta fase.
- O MCP retorna **candidatas** com metadados + sinais de **aplicabilidade** (explicáveis).
- O agente (IDE/LLM) continua responsável por decidir o que carregar e aplicar.

## Direção técnica (v1)

O eixo muda de “similaridade semântica” para “**aplicabilidade normativa**”:

- **Frontmatter consistente** (metadados mínimos) para permitir filtros e decisão:
  - `id`, `title`, `summary`
  - `domains`, `technologies`, `layers`
  - `applies_to`, `kind`, `scope`, `priority`, `tags`
  - (opcional) `file_patterns`, `deprecated`, `supersedes`, `conflicts_with`
- `list_instructions_index` deve suportar filtros estruturados e retornar **somente metadados** (não o corpo).
- `search_instructions` deve combinar query textual + match de metadados + match por `file_path/file_patterns` e retornar **explicação de match** (o “por quê” do ranking), evitando heurísticas orientadas a IDs específicos.
- `get_instruction/get_batch` deve fornecer conteúdo por ID com:
  - `max_chars_per_instruction`
  - `include_metadata`
  - `truncated`
  - `content_hash` (rastreabilidade)

## Métricas / critérios de avaliação

Medir a recuperação por cenários (arquivo + tarefa), com métricas simples:

- **Hit@1/3/5** (instruction correta aparece no top-k?)
- **Wrong Domain Rate** (domínio errado no top-k)
- **Wrong Layer Rate** (camada errada no top-k)
- **Wrong File Applicability Rate**
- **Agent Load Rate** (o agente carrega quando aparece)
- **Agent Correct Use Rate** (o agente aplica corretamente após carregar)
- **Token Waste Rate**

## Onde está o plano detalhado desta decisão

- Plano consolidado (externo, para reduzir vieses de implementação):  
  - `research/nucleo-pesquisa/instruction-retrieval-v1/plano_mcp_instruction_retrieval_v1.md`

## Referências no repositório

- Experimento (tentativa de compositor e artefatos):  
  - `research/experimentos-mcp/2026-05-03-mcp-compositor-contexto-implementacao/README.md`
- Planejamento BMAD (ranking/stopwords/sinônimos como *hardening* do retrieval):  
  - `planning/bmad/epicos/EPIC-07-search-ranking-quality-and-corpus-integrity.md`
  - `planning/bmad/epicos/EPIC-08-stopwords-pt-first-pass-and-rebaseline.md`
  - `planning/bmad/epicos/EPIC-09-i04-observability-readiness-cross-domain-coverage.md`

## Implicação para organização do repo

Este documento vive em `research/analises/` porque é uma **síntese datada citável** (decisão e rationale).
O plano detalhado (com schema e exemplos) vive no `research/nucleo-pesquisa/` como **tema reutilizável**, junto de prompts e artefatos de design.

