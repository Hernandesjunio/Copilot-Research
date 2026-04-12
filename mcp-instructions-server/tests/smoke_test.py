"""Smoke tests: set INSTRUCTIONS_ROOT to fixtures before running."""

import json
from pathlib import Path

import pytest

# Project root = Copilot repo (parent of mcp-instructions-server)
_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch):
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    # Reset module-level index between tests
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    yield


def test_list_instructions_index_count():
    from corporate_instructions_mcp.server import list_instructions_index

    data = json.loads(list_instructions_index())
    assert data["count"] >= 3
    ids = {x["id"] for x in data["instructions"]}
    assert {"dns-retry-pattern", "security-baseline-secrets", "csharp-async-style"}.issubset(ids)


def test_search_instructions_finds_dns():
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"]
    assert data["results"][0]["id"] == "dns-retry-pattern"
    assert "composed_context" in data


def test_get_instruction_by_id():
    from corporate_instructions_mcp.server import get_instruction

    data = json.loads(get_instruction(id="dns-retry-pattern"))
    assert "Polly" in data["content"]


def test_search_tags_only():
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="", tags="security", max_results=5))
    assert any(r["id"] == "security-baseline-secrets" for r in data["results"])


def test_search_instructions_invalid_max_results_uses_default():
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="security secrets", max_results="not-a-number"))
    assert data["results"]


def test_get_instruction_errors():
    from corporate_instructions_mcp.server import get_instruction

    err = json.loads(get_instruction())
    assert err.get("error")

    missing = json.loads(get_instruction(id="does-not-exist"))
    assert "not found" in missing["error"].lower()


def test_get_instruction_rejects_path_traversal():
    from corporate_instructions_mcp.server import get_instruction

    bad = json.loads(get_instruction(path="../../etc/passwd"))
    assert bad.get("error") == "Invalid path argument."


def test_instructions_root_not_dir_raises(monkeypatch, tmp_path: Path) -> None:
    import corporate_instructions_mcp.server as srv

    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path / "missing"))
    srv._index = {}
    srv._index_root = None
    from corporate_instructions_mcp.server import list_instructions_index

    with pytest.raises(RuntimeError, match="not a directory"):
        list_instructions_index()
