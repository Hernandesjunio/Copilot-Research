# Changelog

All notable changes to **corporate-instructions-mcp** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-04-12

### Added

- Repository governance at monorepo root: `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`, Dependabot, issue template.
- CI quality gates: Ruff (lint + format), mypy, Bandit, `pip-audit` (with upgraded `pip` in CI).
- Corpus hardening: max file size and frontmatter size before YAML parse; skip paths resolved outside `INSTRUCTIONS_ROOT` (symlink escapes); `get_instruction` rejects unsafe `path` arguments (`..`, absolute).
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
- **Tools:** `list_instructions_index` (metadata for all indexed `.md`), `search_instructions` (keyword-style search with optional tag filter and capped `max_results`), `get_instruction` (full body by `id` or relative `path`, with `max_chars` truncation).
- **Indexing:** recursive discovery of `*.md` under the corpus root; YAML frontmatter parsing (`id`, `title`, `tags`, `scope`, `priority`, `kind`); duplicate `id` detection; simple relevance scoring for search.
- **Distribution:** Python package built with Hatchling; console script `corporate-instructions-mcp` and module entry `python -m corporate_instructions_mcp`.
- **Runtime dependencies:** `mcp`, `pyyaml` (declared in `pyproject.toml`).
- **Tests:** unit tests for indexing helpers; integration test driving the real server over stdio against the repo fixtures.
- **CI:** GitHub Actions workflow running `pytest` on Python 3.10, 3.11, and 3.12 for changes under `mcp-instructions-server/`.
