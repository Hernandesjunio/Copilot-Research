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


def test_get_instructions_batch_includes_frontmatter_with_extra_keys() -> None:
    """Batch items expose full parsed YAML; extra keys (e.g. owner) are JSON-serializable."""
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(get_instructions_batch(ids="dns-retry-pattern"))
    assert data["found_count"] == 1
    fm = data["instructions"][0]["frontmatter"]
    assert isinstance(fm, dict)
    assert fm["id"] == "dns-retry-pattern"
    assert fm["owner"] == "platform-architecture"
    assert fm["status"] == "active"
    assert fm["last_reviewed"] == "2026-04-12"


def test_get_instructions_batch_frontmatter_round_trips_json() -> None:
    """Response must be json.dumps-safe (dates from YAML become ISO strings)."""
    from corporate_instructions_mcp.server import get_instructions_batch

    raw = get_instructions_batch(ids="dns-retry-pattern")
    parsed = json.loads(raw)
    json.dumps(parsed["instructions"][0]["frontmatter"])


def test_search_tags_only() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="", tags="security", max_results=5))
    assert any(r["id"] == "security-baseline-secrets" for r in data["results"])


def test_search_instructions_invalid_max_results_uses_default() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="security secrets", max_results="not-a-number"))
    assert data["results"]


def test_search_instructions_include_diagnostics() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", include_diagnostics=True))
    assert "diagnostics" in data
    assert "search_confidence" in data["diagnostics"]
    assert "results_only_from_expansion_count" in data["diagnostics"]


def test_search_instructions_tags_mode_all() -> None:
    from corporate_instructions_mcp.server import search_instructions

    any_mode = json.loads(search_instructions(query="microservice", tags="security,microservice", tags_mode="any"))
    all_mode = json.loads(search_instructions(query="microservice", tags="security,microservice", tags_mode="all"))
    assert len(all_mode["results"]) <= len(any_mode["results"])


def test_search_instructions_metadata_filters() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(
        search_instructions(
            query="secrets",
            kind="policy",
            priority="high,medium",
        )
    )
    assert isinstance(data["results"], list)


def test_get_instructions_batch_section_contains() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(
        get_instructions_batch(
            ids="dns-retry-pattern",
            section_contains="retry",
            include_headings=True,
        )
    )
    assert data["found_count"] == 1
    assert "retry" in data["instructions"][0]["content"].lower()
    assert data["instructions"][0]["section_match_count"] >= 1
    assert isinstance(data["instructions"][0]["included_headings"], list)


def test_search_instructions_zero_results_has_fallback_suggestions() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="qvwxzplm", include_diagnostics=True))
    assert data["results"] == []
    assert data["fallback_suggestions"]


def test_new_composite_tools() -> None:
    from corporate_instructions_mcp.server import (
        detect_instruction_conflicts,
        get_normative_checklist,
        resolve_instruction_context,
    )

    resolved = json.loads(resolve_instruction_context(query="retry DNS polly"))
    assert "selected_ids" in resolved
    assert resolved["selected_ids"]
    assert "resolution" in resolved
    assert resolved["resolution"]["actionable_context"]["normative_ids"]
    assert any(item["id"] == "microservice-resilience-polly-timeouts-and-circuit-breaker" for item in resolved["resolution"]["evidence_bundle"])
    assert resolved["resolution"]["selection"]["strategy"]

    checklist = json.loads(get_normative_checklist(scenario="security_baseline"))
    assert "items" in checklist
    assert checklist["summary"]["required_items"] >= 2
    assert checklist["summary"]["implementation_readiness"] in {"ready", "partial"}
    first_required = next(item for item in checklist["items"] if item["requirement_level"] == "required")
    assert first_required["evidence_ids"]
    assert first_required["verification"]

    conflicts = json.loads(
        detect_instruction_conflicts(ids="dns-retry-pattern,microservice-resilience-polly-timeouts-and-circuit-breaker")
    )
    assert "conflicts" in conflicts
    assert conflicts["relationships"]
    pair = conflicts["relationships"][0]
    assert pair["precedence"]["winner_id"] == "microservice-resilience-polly-timeouts-and-circuit-breaker"
    assert "stronger_kind" in pair["precedence"]["reasons"]


def test_search_instructions_persistencia_sql_returns_data_access() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="persistência SQL"))
    ids = {result["id"] for result in data["results"]}
    assert "microservice-data-access-and-sql-security" in ids


def test_search_instructions_cep_viacep_returns_relevant_bundle() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="cep viacep retry timeout cache", max_results=5))
    ids = [result["id"] for result in data["results"]]
    assert set(ids[:3]) == {
        "microservice-resilience-polly-timeouts-and-circuit-breaker",
        "microservice-caching-imemorycache-policy",
        "microservice-integration-httpclientfactory-contracts",
    }


def test_resolve_instruction_context_cep_viacep_surfaces_normative_bundle() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(query="cep viacep retry timeout cache", max_results=5))
    normative = set(data["resolution"]["actionable_context"]["normative_ids"])
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in normative
    assert "microservice-caching-imemorycache-policy" in normative
    assert "microservice-integration-httpclientfactory-contracts" in normative


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

    payload = json.loads(list_instructions_index())
    assert payload["ok"] is False
    assert payload["error_code"] == "INDEX_LOAD_FAILED"
