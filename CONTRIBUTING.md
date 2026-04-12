# Contributing

Thank you for helping improve this project.

## Scope

This repository combines **research documentation** and the **`mcp-instructions-server`** Python package (`corporate-instructions-mcp`). Code changes to the MCP server should stay focused and include tests.

## Development setup (MCP server)

```bash
cd mcp-instructions-server
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export INSTRUCTIONS_ROOT=/absolute/path/to/fixtures/instructions   # or repo: ../fixtures/instructions
pytest -q
ruff check .
ruff format --check .
mypy corporate_instructions_mcp
```

Canonical dependency declarations live in [`mcp-instructions-server/pyproject.toml`](mcp-instructions-server/pyproject.toml). Prefer `pip install -e ".[dev]"` over ad-hoc `pip install` lists.

Run `pip-audit` inside a **fresh virtual environment** that only contains this package and its dependencies (for example `python -m venv .venv && source .venv/bin/activate`, then `python -m pip install --upgrade "pip>=25.3"`, then `pip install -e ".[dev]" pip-audit`, then `pip-audit`). Otherwise globally installed packages may produce false positives.

## Pull requests

- Keep commits readable; prefer **one logical change** per PR when practical.
- Ensure **CI is green** (tests, Ruff, mypy, `pip-audit` as configured in [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- For user-visible behavior, update [`mcp-instructions-server/README.md`](mcp-instructions-server/README.md) and [`mcp-instructions-server/CHANGELOG.md`](mcp-instructions-server/CHANGELOG.md).

## Versioning

The MCP package follows **Semantic Versioning** (MAJOR.MINOR.PATCH). Release tagging is automated from [`mcp-instructions-server/pyproject.toml`](mcp-instructions-server/pyproject.toml); see repository workflows under `.github/workflows/`.

## Code of conduct

Be respectful and professional in issues and pull requests. Maintainers may close or lock threads that violate that standard.
