"""Smoke tests: set INSTRUCTIONS_ROOT to fixtures before running."""

import json
from collections.abc import Generator
from pathlib import Path

import pytest

# Project root = Copilot repo (parent of mcp-instructions-server)
_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    # Reset module-level index between tests
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    yield


def test_list_instructions_index_count() -> None:
    from corporate_instructions_mcp.server import list_instructions_index

    data = json.loads(list_instructions_index())
    assert data["count"] >= 3
    assert "by_tag" in data
    assert isinstance(data["by_tag"], dict)
    ids = {x["id"] for x in data["instructions"]}
    assert {"dns-retry-pattern", "security-baseline-secrets", "csharp-async-style"}.issubset(ids)


def test_search_instructions_finds_dns() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"]
    assert data["results"][0]["id"] == "dns-retry-pattern"
    assert "composed_context" in data


def test_search_results_have_related_ids_shape() -> None:
    """R1: each hit includes related_ids (list of str), never self."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    for r in data["results"]:
        assert "related_ids" in r
        assert isinstance(r["related_ids"], list)
        assert all(isinstance(x, str) for x in r["related_ids"])
        assert r["id"] not in r["related_ids"]


def test_search_dns_top_result_related_ids_include_resilience_policy() -> None:
    """R2: shared tags (resilience, polly) link dns-retry to the Polly policy doc."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    top = next(r for r in data["results"] if r["id"] == "dns-retry-pattern")
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in top["related_ids"]


def test_search_persistencia_sql_data_access_related_ids_include_dapper_neighbor() -> None:
    """R3: tag overlap (microservice, dapper) surfaces a close neighbor via related_ids."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="persistência SQL"))
    row = next(r for r in data["results"] if r["id"] == "microservice-data-access-and-sql-security")
    assert "microservice-domain-interfaces-models-repository" in row["related_ids"]


def test_search_instructions_default_max_results_is_ten() -> None:
    """M1: omit max_results → default 10 (corpus has >10 microservice-tagged matches)."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="microservice"))
    assert len(data["results"]) == 10


def test_search_instructions_max_results_clamped_to_twenty() -> None:
    """M2: values above 20 are clamped."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="microservice", max_results=100))
    assert len(data["results"]) <= 20
    assert len(data["results"]) == 20


def test_search_instructions_max_results_one() -> None:
    """M3: explicit max_results=1 returns at most one row."""
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="microservice", max_results=1))
    assert len(data["results"]) == 1


def test_get_instructions_batch_single_document() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(get_instructions_batch(ids="dns-retry-pattern"))
    assert data["found_count"] == 1
    assert "Polly" in data["instructions"][0]["content"]


def test_search_tags_only() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="", tags="security", max_results=5))
    assert any(r["id"] == "security-baseline-secrets" for r in data["results"])


def test_search_instructions_invalid_max_results_uses_default() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="security secrets", max_results="not-a-number"))
    assert data["results"]


def test_search_instructions_persistencia_sql_returns_data_access() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="persistência SQL"))
    ids = {result["id"] for result in data["results"]}
    assert "microservice-data-access-and-sql-security" in ids


def test_get_instructions_batch_returns_multiple_documents() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(
        get_instructions_batch(
            ids="microservice-architecture-layering,microservice-rest-http-semantics-and-status-codes",
        )
    )
    assert data["found_count"] == 2
    assert len(data["instructions"]) == 2
    assert data["missing_ids"] == []


def test_get_instructions_batch_errors() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    empty = json.loads(get_instructions_batch(ids=""))
    assert empty.get("error")

    missing = json.loads(get_instructions_batch(ids="does-not-exist"))
    assert missing["found_count"] == 0
    assert "does-not-exist" in missing["missing_ids"]


def test_instructions_root_not_dir_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import corporate_instructions_mcp.server as srv

    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path / "missing"))
    srv._index = {}
    srv._index_root = None
    from corporate_instructions_mcp.server import list_instructions_index

    with pytest.raises(RuntimeError, match="not a directory"):
        list_instructions_index()
