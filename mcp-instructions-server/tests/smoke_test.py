"""Smoke tests: set INSTRUCTIONS_ROOT to fixtures before running."""

import json
from copy import deepcopy
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
    srv._expansion_map = None
    yield


def _assert_context_trigger_invariants(data: dict[str, object]) -> None:
    strategy = data["strategy"]
    mcp_usage = data["mcp_usage"]
    mcp_context = data["mcp_context_triggers"]
    stop_rules = data["stop_rules"]
    evidence_gate = data["evidence_gate"]

    assert isinstance(strategy, dict)
    assert isinstance(mcp_usage, dict)
    assert isinstance(mcp_context, dict)
    assert isinstance(stop_rules, dict)
    assert isinstance(evidence_gate, dict)

    if strategy["recommended_execution_mode"] == "plan_only":
        assert strategy["should_plan_first"] is True
        forbidden = {"apply_patch", "edit_file", "write_file", "run_build", "run_tests"}
        assert forbidden.isdisjoint({step["tool"] for step in data["tool_sequence"]})
    if mcp_usage["level"] == "not_needed":
        assert mcp_context["batch_required"] is False
    if stop_rules["stop_required"] is True:
        assert stop_rules["stop_reasons"]
    if evidence_gate["workspace_evidence_required_detected"] is True:
        assert evidence_gate["must_verify_workspace_signals"] is True
    if mcp_usage["level"] in {"required", "recommended"}:
        tools = [step["tool"] for step in data["tool_sequence"]]
        assert "corporate_instructions_list_instructions_index" in tools
        assert "corporate_instructions_search_instructions" in tools
        assert "corporate_instructions_get_instructions_batch" in tools


def test_list_instructions_index_count() -> None:
    from corporate_instructions_mcp.server import list_instructions_index

    data = json.loads(list_instructions_index())
    assert data["status"] == "ok"
    assert data["index_health"]["loaded"] is True
    assert isinstance(data["warnings"], list)
    assert isinstance(data["errors"], list)
    assert data["count"] >= 3
    assert "by_tag" in data
    assert isinstance(data["by_tag"], dict)
    ids = {x["id"] for x in data["instructions"]}
    assert {"dns-retry-pattern", "example-security-baseline", "csharp-async-style"}.issubset(ids)


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
    assert fm["last_reviewed"] == "2026-05-04"


def test_get_instructions_batch_frontmatter_round_trips_json() -> None:
    """Response must be json.dumps-safe (dates from YAML become ISO strings)."""
    from corporate_instructions_mcp.server import get_instructions_batch

    raw = get_instructions_batch(ids="dns-retry-pattern")
    parsed = json.loads(raw)
    json.dumps(parsed["instructions"][0]["frontmatter"])


def test_search_tags_only() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="", tags="security", max_results=5))
    assert any(r["id"] == "example-security-baseline" for r in data["results"])


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


def test_search_instructions_multi_query_consolidated_output() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(
        search_instructions(
            query="",
            queries=[
                "minimal api rest status codes",
                "response envelope global error handling",
            ],
            max_results_per_query=3,
            include_diagnostics=True,
        )
    )
    assert "queries" in data
    assert len(data["queries"]) == 2
    assert data["queries"][0]["query"] == "minimal api rest status codes"
    assert "consolidated" in data
    consolidated = data["consolidated"]
    assert set(consolidated.keys()) == {"top_policies", "top_references", "coverage_gaps"}
    assert isinstance(consolidated["top_policies"], list)
    assert isinstance(consolidated["top_references"], list)
    assert isinstance(consolidated["coverage_gaps"], list)


def test_new_composite_tools() -> None:
    from corporate_instructions_mcp.server import (
        detect_instruction_conflicts,
        get_context_triggers,
        get_normative_checklist,
        resolve_instruction_context,
    )

    resolved = json.loads(resolve_instruction_context(query="retry DNS polly"))
    assert "selected_ids" in resolved
    assert resolved["selected_ids"]
    assert "resolution" in resolved
    assert resolved["resolution"]["actionable_context"]["normative_ids"]
    assert any(
        item["id"] == "microservice-resilience-polly-timeouts-and-circuit-breaker"
        for item in resolved["resolution"]["evidence_bundle"]
    )
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

    payload = {
        "schema_version": "1.0.0",
        "request": {
            "user_goal": "quero um plano detalhado para migrar este fluxo para processamento assíncrono",
            "operation_mode": "plan_only",
            "explicit_deliverable": "detailed plan",
            "ambiguity_level": "medium",
            "risk_level": "medium",
            "mentions_current_file": False,
            "mentions_specific_files": False,
            "mentions_symbols": False,
            "mentions_cross_cutting_concerns": True,
            "mentions_public_contract": False,
            "mentions_new_infrastructure": False,
            "mentions_external_integration": False,
            "wants_tests": False,
            "wants_only_plan": True,
        },
        "workspace": {
            "repo_known": False,
            "current_file_available": False,
            "solution_available": True,
            "project_count_known": False,
            "has_mcp": True,
            "tech_stack_signals": [".NET 8"],
            "workspace_signals_known": False,
        },
        "context_state": {
            "repo_structure_loaded": False,
            "current_file_loaded": False,
            "target_files_loaded": False,
            "symbols_loaded": False,
            "mcp_index_loaded": False,
            "mcp_batch_loaded": False,
            "plan_already_created": False,
        },
        "constraints": {
            "prefer_plan_first": True,
            "prefer_minimal_context": True,
            "allow_mcp_usage": True,
            "allow_repo_scan": True,
            "max_search_iterations": 5,
            "max_instruction_ids": 6,
        },
    }
    triggers = json.loads(get_context_triggers(input_payload=json.dumps(payload, ensure_ascii=False)))
    assert triggers["contract_metadata"]["published_schema_version"] == "1.0.0"
    assert triggers["advanced_signals"]["decision_stability"]["level"] in {"low", "medium", "high"}
    assert triggers["scenario"]["scenario_id"] == "plan-crosscutting-async-migration"
    assert triggers["strategy"]["recommended_execution_mode"] == "plan_only"
    assert triggers["mcp_usage"]["level"] == "recommended"
    assert triggers["tool_sequence_mode"] == "recommended_order"
    assert "request_mentions_cross_cutting_concerns" in triggers["signal_sources"]["request_declared_signals"]
    assert triggers["fallbacks"]["when_no_policy_found"] == "follow_repo_and_label_gap"
    assert triggers["mcp_context_triggers"]["batch_required"] is True
    assert triggers["evidence_gate"]["phase"] == "preliminary"
    assert triggers["evidence_gate"]["reconciliation_status"] == "pending_batch"
    assert all("failure_effect" in step and "fallback_on_failure" in step for step in triggers["tool_sequence"])
    _assert_context_trigger_invariants(triggers)


def test_get_context_triggers_functional_scenarios_matrix() -> None:
    """Functional smoke: validate routing behavior across canonical scenarios."""
    from corporate_instructions_mcp.server import get_context_triggers

    base_payload = {
        "schema_version": "1.0.0",
        "request": {
            "user_goal": "quero um plano detalhado para migrar este fluxo para processamento assíncrono",
            "operation_mode": "plan_only",
            "explicit_deliverable": "detailed plan",
            "ambiguity_level": "medium",
            "risk_level": "medium",
            "mentions_current_file": False,
            "mentions_specific_files": False,
            "mentions_symbols": False,
            "mentions_cross_cutting_concerns": True,
            "mentions_public_contract": False,
            "mentions_new_infrastructure": False,
            "mentions_external_integration": False,
            "wants_tests": False,
            "wants_only_plan": True,
        },
        "workspace": {
            "repo_known": False,
            "current_file_available": False,
            "solution_available": True,
            "project_count_known": False,
            "has_mcp": True,
            "tech_stack_signals": [".NET 8"],
            "workspace_signals_known": False,
        },
        "context_state": {
            "repo_structure_loaded": False,
            "current_file_loaded": False,
            "target_files_loaded": False,
            "symbols_loaded": False,
            "mcp_index_loaded": False,
            "mcp_batch_loaded": False,
            "plan_already_created": False,
        },
        "constraints": {
            "prefer_plan_first": True,
            "prefer_minimal_context": True,
            "allow_mcp_usage": True,
            "allow_repo_scan": True,
            "max_search_iterations": 5,
            "max_instruction_ids": 6,
        },
    }

    # Scenario A: cross-cutting plan request -> MCP recommended and batch required.
    scenario_a = deepcopy(base_payload)
    out_a = json.loads(get_context_triggers(input_payload=json.dumps(scenario_a, ensure_ascii=False)))
    assert out_a["contract_metadata"]["catalog_resource_id"] == "context-orchestration-catalog"
    assert out_a["strategy"]["recommended_execution_mode"] == "plan_only"
    assert out_a["mcp_usage"]["level"] == "recommended"
    assert out_a["tool_sequence_mode"] == "recommended_order"
    assert "request_mentions_cross_cutting_concerns" in out_a["signal_sources"]["request_declared_signals"]
    assert out_a["mcp_context_triggers"]["batch_required"] is True
    assert out_a["evidence_gate"]["phase"] == "preliminary"
    assert out_a["evidence_gate"]["must_reconcile_after_batch"] is True
    assert out_a["tool_sequence"]
    assert all("failure_effect" in step and "fallback_on_failure" in step for step in out_a["tool_sequence"])
    _assert_context_trigger_invariants(out_a)

    # Scenario B: local debug request -> MCP not needed and no batch required.
    scenario_b = deepcopy(base_payload)
    scenario_b["request"]["operation_mode"] = "debug"
    scenario_b["request"]["wants_only_plan"] = False
    scenario_b["request"]["mentions_cross_cutting_concerns"] = False
    scenario_b["request"]["mentions_specific_files"] = True
    scenario_b["request"]["mentions_current_file"] = True
    scenario_b["workspace"]["repo_known"] = True
    out_b = json.loads(get_context_triggers(input_payload=json.dumps(scenario_b, ensure_ascii=False)))
    assert out_b["mcp_usage"]["level"] == "not_needed"
    assert out_b["strategy"]["should_use_mcp"] is False
    assert out_b["mcp_context_triggers"]["batch_required"] is False
    assert out_b["evidence_gate"]["reconciliation_status"] == "not_required"
    assert "repo_structure_known" in out_b["signal_sources"]["repo_observed_signals"]
    assert out_b["advanced_signals"]["plan_granularity"]["level"] == "coarse"
    _assert_context_trigger_invariants(out_b)

    # Scenario C: public contract risk without workspace evidence -> stop + MCP required.
    scenario_c = deepcopy(base_payload)
    scenario_c["request"]["mentions_public_contract"] = True
    scenario_c["workspace"]["workspace_signals_known"] = False
    out_c = json.loads(get_context_triggers(input_payload=json.dumps(scenario_c, ensure_ascii=False)))
    assert out_c["mcp_usage"]["level"] == "required"
    assert out_c["strategy"]["should_stop_for_human_input"] is True
    assert out_c["stop_rules"]["stop_required"] is True
    assert out_c["evidence_gate"]["must_verify_workspace_signals"] is True
    _assert_context_trigger_invariants(out_c)

    # Scenario D: cross-cutting request with MCP unavailable -> not needed (availability bound).
    scenario_d = deepcopy(base_payload)
    scenario_d["workspace"]["has_mcp"] = False
    out_d = json.loads(get_context_triggers(input_payload=json.dumps(scenario_d, ensure_ascii=False)))
    assert out_d["mcp_usage"]["level"] == "not_needed"
    assert out_d["strategy"]["should_use_mcp"] is False
    assert out_d["mcp_context_triggers"]["batch_required"] is False
    assert out_d["evidence_gate"]["reconciliation_status"] == "not_required"
    _assert_context_trigger_invariants(out_d)

    # Scenario E: when batch is already loaded, gate transitions to reconciled.
    scenario_e = deepcopy(base_payload)
    scenario_e["context_state"]["mcp_batch_loaded"] = True
    out_e = json.loads(get_context_triggers(input_payload=json.dumps(scenario_e, ensure_ascii=False)))
    assert out_e["mcp_usage"]["level"] == "recommended"
    assert out_e["evidence_gate"]["phase"] == "reconciled"
    assert out_e["evidence_gate"]["reconciliation_status"] == "reconciled"
    assert "normative_batch_loaded" in out_e["signal_sources"]["batch_discovered_signals"]
    _assert_context_trigger_invariants(out_e)


def test_get_context_triggers_accepts_partial_payload_with_defaults() -> None:
    from corporate_instructions_mcp.server import get_context_triggers

    partial_payload = {
        "request": {
            "operation_mode": "implement",
            "mentions_cross_cutting_concerns": True,
            "mentions_external_integration": True,
            "ambiguity_level": "medium",
            "risk_level": "medium",
        },
        "workspace": {"has_mcp": True},
    }
    output = json.loads(get_context_triggers(input_payload=json.dumps(partial_payload, ensure_ascii=False)))
    assert output["schema_version"] == "1.0.0"
    assert output["mcp_usage"]["level"] in {"required", "recommended"}
    assert output["tool_sequence"]


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


def test_resolve_instruction_context_exposes_p1_evidence_fields() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(query="authorization owner audit endpoint", max_results=3))
    resolution = data["resolution"]
    assert "selection_rationale" in resolution
    assert isinstance(resolution["selection_rationale"], list)
    assert "pending_evidence" in resolution
    assert isinstance(resolution["pending_evidence"], list)
    assert "required_workspace_signals" in resolution
    assert isinstance(resolution["required_workspace_signals"], dict)
    assert "next_repo_evidence_actions" in resolution
    assert isinstance(resolution["next_repo_evidence_actions"], list)


def test_resolve_instruction_context_requires_applicability_gate_for_normative_ids() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(query="authorization owner audit endpoint", max_results=3))
    actionable = data["resolution"]["actionable_context"]
    assert actionable["normative_ids"]
    assert actionable["requires_applicability_gate"] is True
    assert any(
        "get_instructions_batch" in step.lower() or "verify selected normative" in step.lower()
        for step in actionable["next_actions"]
    )


def test_resolve_instruction_context_next_actions_do_not_apply_before_gate() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(query="cep viacep retry timeout cache", max_results=5))
    next_actions = data["resolution"]["actionable_context"]["next_actions"]
    lower_actions = [action.lower() for action in next_actions]
    gate_idx = next(
        (idx for idx, action in enumerate(lower_actions) if "verify selected normative" in action),
        None,
    )
    assert gate_idx is not None
    for idx, action in enumerate(lower_actions):
        if "treat `" in action:
            assert gate_idx < idx


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
    assert payload["status"] == "error"
    assert payload["error_code"] == "INDEX_LOAD_FAILED"


def test_list_instructions_index_status_partial_when_warnings_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import corporate_instructions_mcp.server as srv
    from corporate_instructions_mcp.indexing import MAX_INSTRUCTION_FILE_BYTES
    from corporate_instructions_mcp.server import list_instructions_index

    valid = """---
id: tiny-policy
title: Tiny Policy
scope: "**/*.cs"
kind: policy
---
Body.
"""
    (tmp_path / "tiny-policy.md").write_text(valid, encoding="utf-8")
    (tmp_path / "huge.md").write_text("x" * (MAX_INSTRUCTION_FILE_BYTES + 32), encoding="utf-8")
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path))
    srv._index = {}
    srv._index_root = None

    payload = json.loads(list_instructions_index())
    assert payload["status"] == "partial"
    assert payload["index_health"]["documents_with_warnings"] >= 1
    assert payload["warnings"]
