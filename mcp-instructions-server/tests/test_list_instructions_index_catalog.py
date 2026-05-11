"""Contract tests for list_instructions_index catalog filters/pagination/facets."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

from corporate_instructions_mcp.applicability import match_scope

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None
    yield


def _list(**kwargs: object) -> dict[str, object]:
    from corporate_instructions_mcp.server import list_instructions_index

    return json.loads(list_instructions_index(**kwargs))


def test_list_catalog_default_contract() -> None:
    data = _list()
    assert data["index_status"] in {"ok", "partial"}
    assert data["total_indexed"] >= 3
    assert data["total_matched"] >= 3
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert isinstance(data["items"], list)
    assert "facets" not in data
    assert "diagnostics" not in data
    first = data["items"][0]
    assert "status" in first
    assert "owner" in first
    assert "workspace_evidence_required" in first
    assert "summary" in first


def test_list_catalog_filter_kind_policy_only() -> None:
    data = _list(kind="policy")
    assert data["items"]
    assert all(item.get("kind") == "policy" for item in data["items"])


def test_list_catalog_filter_priority_high_only() -> None:
    data = _list(priority="high")
    assert data["items"]
    assert all(item.get("priority") == "high" for item in data["items"])


def test_list_catalog_filter_status_active_only() -> None:
    data = _list(status="active")
    assert data["items"]
    assert all(item.get("status") == "active" for item in data["items"])


def test_list_catalog_filter_scope_exact() -> None:
    data = _list(scope="**/Api/**/*.cs")
    assert data["items"]
    assert all(item.get("scope") == "**/Api/**/*.cs" for item in data["items"])


def test_list_catalog_filter_tags_any_and_all() -> None:
    any_mode = _list(tags="security,microservice", tags_mode="any")
    all_mode = _list(tags="security,microservice", tags_mode="all")
    assert any_mode["total_matched"] >= all_mode["total_matched"]
    assert all_mode["items"]
    assert all(
        {"security", "microservice"}.issubset(set(item.get("tags") or []))
        for item in all_mode["items"]
    )


def test_list_catalog_filter_owner() -> None:
    data = _list(owner="platform-architecture")
    assert data["items"]
    assert all(item.get("owner") == "platform-architecture" for item in data["items"])


def test_list_catalog_filter_workspace_evidence_required() -> None:
    data = _list(workspace_evidence_required=True)
    assert data["items"]
    assert all(item.get("workspace_evidence_required") is True for item in data["items"])


def test_list_catalog_pagination_limit_offset_has_more() -> None:
    page1 = _list(limit=2, offset=0)
    page2 = _list(limit=2, offset=2)
    assert len(page1["items"]) == 2
    assert page1["has_more"] is True
    assert len(page2["items"]) <= 2
    assert page2["total_matched"] == page1["total_matched"]
    ids_1 = {item["id"] for item in page1["items"]}
    ids_2 = {item["id"] for item in page2["items"]}
    assert ids_1.isdisjoint(ids_2)


def test_list_catalog_facets_and_limit_zero_policy() -> None:
    invalid = _list(limit=0, include_facets=False)
    assert invalid["ok"] is False
    assert invalid["error_code"] == "LIST_INVALID_LIMIT"

    valid = _list(limit=0, include_facets=True)
    assert valid["items"] == []
    assert valid["total_matched"] >= 1
    assert "facets" in valid
    assert "tags" in valid["facets"]
    assert "scope" in valid["facets"]


def test_list_catalog_current_file_path_matches_scope() -> None:
    data = _list(current_file_path="docs/README.md")
    assert data["items"]
    for item in data["items"]:
        matched, _ = match_scope(str(item.get("scope") or ""), "docs/README.md")
        assert matched is True
        assert item.get("match_reason") == "scope matched current_file_path"


def test_list_catalog_include_non_matching_global_keeps_explicit_filters() -> None:
    data = _list(
        kind="policy",
        current_file_path="docs/README.md",
        include_non_matching_global=True,
        include_diagnostics=True,
    )
    assert data["items"]
    assert any(item.get("match_reason") != "scope matched current_file_path" for item in data["items"])
    diagnostics = data["diagnostics"]
    assert diagnostics["scope_match"]["matched"] is not None
    assert diagnostics["scope_match"]["unmatched"] is not None


def test_list_catalog_combined_filters_with_specific_rules() -> None:
    data = _list(
        tags="microservice,security",
        tags_mode="all",
        kind="policy",
        scope="**/*.cs",
        status="active",
        owner="platform-architecture",
        workspace_evidence_required=True,
        current_file_path="src/Api/Endpoints/ClienteEndpoints.cs",
        include_non_matching_global=False,
    )
    assert data["items"]
    for item in data["items"]:
        assert item["kind"] == "policy"
        assert item["scope"] == "**/*.cs"
        assert item["status"] == "active"
        assert item["owner"] == "platform-architecture"
        assert item["workspace_evidence_required"] is True
        assert {"microservice", "security"}.issubset(set(item["tags"]))
        assert item["match_reason"] == "scope matched current_file_path"


def test_list_catalog_has_no_query_parameter() -> None:
    from corporate_instructions_mcp.server import list_instructions_index

    with pytest.raises(TypeError):
        list_instructions_index(query="dns retry")  # type: ignore[call-arg]


def test_list_catalog_scale_100_plus_entries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import corporate_instructions_mcp.server as srv

    for n in range(120):
        kind = "policy" if (n % 2 == 0) else "reference"
        priority = "high" if (n % 3 == 0) else "medium"
        tag = "security" if (n % 5 == 0) else "api"
        body = f"""---
id: synthetic-{n}
title: Synthetic {n}
tags: [{tag}, synthetic]
scope: "**/*.cs"
priority: {priority}
kind: {kind}
owner: platform-architecture
status: active
workspace_evidence_required: {"true" if (n % 4 == 0) else "false"}
---
Synthetic body {n}.
"""
        (tmp_path / f"synthetic-{n}.md").write_text(body, encoding="utf-8")

    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path))
    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None

    data = _list(limit=25, offset=25, include_facets=True, kind="policy", tags="synthetic")
    assert data["total_indexed"] == 120
    assert data["total_matched"] == 60
    assert len(data["items"]) == 25
    assert data["has_more"] is True
    assert data["facets"]["kind"]["policy"] == 60
