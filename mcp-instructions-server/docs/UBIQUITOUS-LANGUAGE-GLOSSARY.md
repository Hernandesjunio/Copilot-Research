# Ubiquitous Language Glossary for `mcp-instructions-server`

## Purpose

This glossary defines the **canonical vocabulary** shared by `list_instructions_index`,
`search_instructions`, and `get_instructions_batch`.

Normative rule:

> If two or three tools expose the same field name, that field must keep the same type,
> normalization rules, and meaning.

Different tools may have different goals, but they must not redefine the same term.

## Scope of this glossary

This glossary governs:

- MCP tool arguments
- MCP tool response fields
- code comments and docstrings
- tests and fixtures
- documentation in `README.md` and `docs/`

It does not require every tool to expose every field. It requires **semantic consistency**
whenever a field exists.

## Core concepts

### Instruction

A normative Markdown document in the corpus, with YAML frontmatter plus body content.

### Corpus

The set of instruction files currently loaded from `INSTRUCTIONS_ROOT`.

### Frontmatter

The YAML metadata header of one instruction document.

### Metadata

Structured information derived from frontmatter and exposed consistently across tools.

### Catalog

The metadata-only view of the corpus. The catalog is the primary concern of
`list_instructions_index`.

### Search

Intent-based retrieval over the corpus using a textual query and, when configured,
query expansion and ranking logic. Search is the primary concern of `search_instructions`.

### Batch

Content retrieval by explicit instruction ids. Batch is the primary concern of
`get_instructions_batch`.

## Canonical field definitions

### `id`

Stable instruction identifier. Unique within the corpus.

### `path`

Instruction path relative to `INSTRUCTIONS_ROOT`.

### `title`

Human-readable instruction title.

### `summary`

Optional short summary of the instruction when present in frontmatter or explicitly derived
by contract. It is metadata, not content body.

### `tags`

Structured categorical labels from frontmatter.

When accepted as input, `tags` is a comma-separated string.
When returned as metadata, `tags` is an array of strings.

### `tags_mode`

Interpretation mode for tag filters:

- `any`: at least one requested tag is present in the instruction
- `all`: all requested tags are present in the instruction

### `kind`

Instruction classification from frontmatter, such as `policy` or `reference`.

### `scope`

The **declared frontmatter value** that describes documentary applicability, usually a glob
such as `**/*.cs` or `**/Api/**/*.cs`.

`scope` never means "current file path". It always means the instruction's declared scope.

### `current_file_path`

The runtime file path provided by the client/agent to evaluate whether an instruction's
declared `scope` applies to the current file.

`current_file_path` is contextual input. It is not persisted instruction metadata.

### `scope match`

A deterministic evaluation between one instruction's declared `scope` and a provided
`current_file_path`.

It is not textual search, semantic inference, or ranking.

### `priority`

Instruction priority from frontmatter, typically `high`, `medium`, or `low`.

### `status`

Instruction lifecycle status from frontmatter, such as `active`, `draft`, or `deprecated`.

This term refers to the **document status**, never to index health.

### `index_status`

Top-level response field describing catalog/index health, such as `ok`, `partial`, or `error`.

This term must be used instead of top-level `status` when the payload also includes document
metadata with a `status` field.

### `owner`

Declared owner of the instruction from frontmatter.

### `workspace_evidence_required`

Boolean metadata indicating that safe applicability depends on evidence from the target
workspace or repository state.

If exposed in any tool, it must keep this exact meaning in every tool.

### `content_sha256`

Stable content hash of the instruction body/content snapshot used by the server.

### `frontmatter`

JSON-safe rendering of the parsed YAML frontmatter for one instruction. It may include
additional keys beyond the canonical metadata fields.

The canonical metadata fields remain preferred for stable contracts.

### `query`

Natural-language textual search input used only for intent-based retrieval.

`query` belongs to `search_instructions`. It must not be added to `list_instructions_index`
or `get_instructions_batch`.

### `ids`

Comma-separated list of instruction ids used by `get_instructions_batch`.

### `limit`

Maximum number of catalog items returned in one paginated listing.

### `offset`

Starting position within the matched catalog set for pagination.

### `max_results`

Maximum number of ranked search results returned by `search_instructions`.

### `include_facets`

Boolean flag requesting aggregate catalog counts for the matched set.

### `facets`

Aggregated counts derived from the matched catalog set, such as counts by `kind`, `priority`,
`tags`, `scope`, or `status`.

### `include_diagnostics`

Boolean flag requesting technical execution details such as applied filters, pagination,
matching behavior, and selected execution mode.

Diagnostics must explain system behavior, not hidden chain-of-thought.

### `match_reason`

Human-readable explanation of why an instruction was included by deterministic filters
or scope applicability.

It is explanatory metadata, not a textual relevance score.

### `relevance`

Normalized or comparative search ranking signal returned by `search_instructions`.

`relevance` is search-specific and must not appear in catalog-only responses unless a future
ADR explicitly changes that rule.

### `content`

Instruction body content returned by `get_instructions_batch`, possibly truncated or section-
filtered according to batch arguments.

## Shared semantics matrix

| Term | `list_instructions_index` | `search_instructions` | `get_instructions_batch` |
|------|----------------------------|------------------------|--------------------------|
| `id` | returned | returned | returned |
| `path` | returned | returned | returned |
| `title` | returned | returned | returned |
| `tags` | filter + returned | filter + returned | returned |
| `tags_mode` | filter | filter | not used |
| `kind` | filter + returned | filter + returned | returned |
| `scope` | filter + returned | filter + returned | returned |
| `current_file_path` | optional filter | optional contextual input for declarative applicability filters | not used |
| `priority` | filter + returned | filter + returned | returned |
| `status` | filter + returned | recommended shared filter/return when exposed | may be derived from `frontmatter` or promoted to canonical field |
| `owner` | filter + returned | recommended shared filter/return when exposed | may be derived from `frontmatter` or promoted to canonical field |
| `workspace_evidence_required` | filter + optional returned | filter + returned when exposed | may be derived from `frontmatter` or promoted to canonical field |
| `content_sha256` | returned | returned | returned |
| `include_diagnostics` | supported | supported | not currently supported |
| `query` | forbidden | required or paired with `queries` | forbidden |
| `ids` | forbidden | forbidden | required |
| `content` | forbidden | forbidden | returned |

## Naming guardrails

1. Same name, same meaning.
2. Envelope health fields must not collide with document metadata names.
3. `scope` is declared metadata; `current_file_path` is runtime context.
4. `query` is search-only.
5. `content` is batch-only.
6. When a metadata field is not yet promoted to a top-level item field, `frontmatter` may carry
   it temporarily, but the meaning must remain identical.

## Operational recommendations

### For `list_instructions_index`

- Prefer metadata filters over large unfiltered dumps.
- Use `index_status` for top-level health.
- Keep item metadata aligned with batch and search fields.

### For `search_instructions`

- Reuse the same metadata filter semantics as the catalog.
- Keep ranking-only fields (`score`, `relevance`) search-specific.
- Do not overload metadata names with search-specific meanings.

### For `get_instructions_batch`

- Return canonical metadata fields alongside content whenever possible.
- Keep `frontmatter` as an extensibility container, not as a reason to rename known fields.

## Change management

Any change to the meaning of a canonical term should require:

1. ADR update
2. tool contract update
3. tests update
4. README/docs update

Without these four steps, the term should be treated as unchanged.
