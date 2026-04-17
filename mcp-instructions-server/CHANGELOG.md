# Changelog

All notable changes to **corporate-instructions-mcp** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- README: guia de registo no Visual Studio com `command`/`INSTRUCTIONS_ROOT` absolutos, `PYTHONPATH` opcional para monorepo, e resolução de problemas quando o catálogo de tools diverge do chat; nota de que `pip install -e` global é válido desde que o `command` aponte para esse `python.exe`; lembrete de activar cada tool no painel MCP do VS após renomear servidor/tools.
- `get_instructions_batch`: docstring MCP simplificada (menos marcação) para reduzir ruído em clientes sensíveis à descrição da tool.

### Added

- `scripts/print_mcp_tools_list.py`: imprime `tools/list` em JSON (stdio real) para anexar a tickets de IDE quando o chat não espelha o catálogo MCP.
- `get_instructions_batch`: each instruction item now includes `frontmatter`, the full parsed YAML header (with extra keys beyond id/title/tags), JSON-safe for dates and decimals.

### Tests

- Smoke and integration assertions for `frontmatter`; unit tests for `_json_safe_frontmatter` in `tests/test_server_frontmatter.py`.

## [0.3.0] - 2026-04-16

### Added

- `docs/TESTS.md` describing how to run and what the suite covers; expanded smoke and stdio integration tests for `related_ids`, `max_results` defaults/caps, and end-to-end STDIO behaviour.
- Package `README.md` cross-links to monorepo agent orientation (`AGENTS.md`).

### Changed

- Retrieval contract simplified to batch-only content fetch: removed `get_instruction` and standardized full-text reads on `get_instructions_batch` (single or multiple IDs).
- `search_instructions` now defaults to `max_results=10` with cap 20, includes `related_ids`, and uses synonym expansion to reduce false negatives in keyword overlap.
- `list_instructions_index` now returns `by_tag` grouping in addition to flat metadata.
- Tests, smoke and stdio integration flows updated to reflect the new tool contract.

### Fixed

- CI: Ruff format applied to `indexing.py` and `integration_mcp_stdio_test.py` so `ruff format --check` passes.

## [0.2.0] - 2026-04-12

### Added

- Repository governance at monorepo root: `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`, Dependabot, issue template.
- CI quality gates: Ruff (lint + format), mypy, Bandit, `pip-audit` (with upgraded `pip` in CI).
- Corpus hardening: max file size and frontmatter size before YAML parse; skip paths resolved outside `INSTRUCTIONS_ROOT` (symlink escapes); historical `get_instruction` rejected unsafe `path` arguments (`..`, absolute).
- Fail-fast when `INSTRUCTIONS_ROOT` is unset or not a directory; operational logging on **stderr** (stdio-safe).
- `corporate_instructions_mcp.paths` helpers for root validation and path safety.
- Expanded package README: versioning matrix, runbook, limits, security pointers; `docs/ROADMAP-TRANSPORT-HTTP.md`.
- This changelog file; extra unit and smoke tests (indexing edges, path rules, invalid root).

### Changed

- `requirements.txt` defers to `pyproject.toml` as the canonical dependency source to reduce drift.

## [0.1.0] - 2026-04-06

First published release of the **corporate-instructions-mcp** read-only MCP server.

### Added

- **stdio** MCP server (FastMCP) exposing an organizational Markdown instruction corpus to compatible hosts (e.g. GitHub Copilot in Visual Studio).
- Configuration via environment variable **`INSTRUCTIONS_ROOT`** pointing at the corpus root directory.
- **Tools:** `list_instructions_index` (metadata for all indexed `.md`), `search_instructions` (keyword-style search with optional tag filter and capped `max_results`), historical `get_instruction` (today replaced by `get_instructions_batch`).
- **Indexing:** recursive discovery of `*.md` under the corpus root; YAML frontmatter parsing (`id`, `title`, `tags`, `scope`, `priority`, `kind`); duplicate `id` detection; simple relevance scoring for search.
- **Distribution:** Python package built with Hatchling; console script `corporate-instructions-mcp` and module entry `python -m corporate_instructions_mcp`.
- **Runtime dependencies:** `mcp`, `pyyaml` (declared in `pyproject.toml`).
- **Tests:** unit tests for indexing helpers; integration test driving the real server over stdio against the repo fixtures.
- **CI:** GitHub Actions workflow running `pytest` on Python 3.10, 3.11, and 3.12 for changes under `mcp-instructions-server/`.
