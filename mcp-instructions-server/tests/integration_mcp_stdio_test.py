"""Integration test: spawn the real MCP server over stdio and call tools."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Repo root = Copilot-Research (parent of mcp-instructions-server)
_SERVER_DIR = Path(__file__).resolve().parents[1]
_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


def _corpus_root() -> Path:
    """Default: repo fixtures. Override with INSTRUCTIONS_ROOT to test your own corpus."""
    override = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _FIXTURES.resolve()


def _tool_text(result: Any) -> str:
    assert not result.isError, getattr(result, "content", result)
    assert result.content, "tool returned no content"
    block = result.content[0]
    assert hasattr(block, "text"), block
    return cast(str, block.text)


def _assert_context_trigger_invariants(data: dict[str, Any]) -> None:
    strategy = data["strategy"]
    mcp_usage = data["mcp_usage"]
    mcp_context = data["mcp_context_triggers"]
    stop_rules = data["stop_rules"]
    evidence_gate = data["evidence_gate"]

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


def test_mcp_stdio_list_search_get_instruction() -> None:
    """End-to-end: subprocess runs FastMCP; client exercises MCP tools."""

    corpus = _corpus_root()
    use_fixture_expectations = corpus == _FIXTURES.resolve()

    async def _run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "corporate_instructions_mcp"],
            cwd=str(_SERVER_DIR),
            env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            listed = await session.list_tools()
            names = {t.name for t in listed.tools}
            assert {
                "build_compliance_matrix",
                "get_context_triggers",
                "get_instructions_batch",
                "list_instructions_index",
                "search_instructions",
                "validate_applicability",
            }.issubset(names)

            raw = _tool_text(await session.call_tool("list_instructions_index", {}))
            index = json.loads(raw)
            assert index["count"] >= 1, f"no .md indexed under {corpus}"
            assert "by_tag" in index
            ids = {x["id"] for x in index["instructions"]}

            if use_fixture_expectations:
                assert index["count"] >= 3
                expected_ids = {"dns-retry-pattern", "security-baseline-secrets", "csharp-async-style"}
                assert expected_ids.issubset(ids)

            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "retry DNS polly", "max_results": 3},
                )
            )
            search = json.loads(raw)
            assert "composed_context" in search
            if use_fixture_expectations:
                assert search["results"]
                assert search["results"][0]["id"] == "dns-retry-pattern"

            fetch_id = (
                "dns-retry-pattern"
                if use_fixture_expectations and "dns-retry-pattern" in ids
                else index["instructions"][0]["id"]
            )
            batch_ids = ",".join(
                [
                    fetch_id,
                    "microservice-rest-http-semantics-and-status-codes" if use_fixture_expectations else fetch_id,
                ]
            )
            raw = _tool_text(await session.call_tool("get_instructions_batch", {"ids": batch_ids}))
            batch = json.loads(raw)
            assert batch["found_count"] >= 1
            assert isinstance(batch["instructions"], list)
            first = batch["instructions"][0]
            assert first.get("id") == fetch_id
            assert isinstance(first.get("content"), str) and len(first["content"]) > 0
            assert isinstance(first.get("frontmatter"), dict) and first["frontmatter"]
            if use_fixture_expectations and fetch_id == "dns-retry-pattern":
                assert "Polly" in first["content"]
                assert first["frontmatter"].get("id") == "dns-retry-pattern"

    asyncio.run(_run())


def test_mcp_stdio_search_default_max_persistencia_sql_and_related_ids() -> None:
    """M4, I1, I2: STDIO path matches smoke — default max_results=10, persistência SQL hit, related_ids present."""

    corpus = _corpus_root()
    use_fixture_expectations = corpus == _FIXTURES.resolve()
    if not use_fixture_expectations:
        pytest.skip("fixture-only expectations (INSTRUCTIONS_ROOT override)")

    async def _run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "corporate_instructions_mcp"],
            cwd=str(_SERVER_DIR),
            env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            raw = _tool_text(await session.call_tool("list_instructions_index", {}))
            index = json.loads(raw)
            assert index["count"] >= 3
            assert "by_tag" in index

            # M4: omit max_results → default 10
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "microservice"},
                )
            )
            micro = json.loads(raw)
            assert len(micro["results"]) == 10

            # I1: synonym / domain query finds data-access (same as smoke)
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "persistência SQL"},
                )
            )
            persist = json.loads(raw)
            ids = {r["id"] for r in persist["results"]}
            assert "microservice-data-access-and-sql-security" in ids
            assert persist.get("composed_context", "").strip() != ""

            # I2: multi-hit search; top result carries related_ids (discoverability contract)
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "retry DNS polly", "max_results": 3},
                )
            )
            dns = json.loads(raw)
            assert dns["results"]
            first = dns["results"][0]
            assert first["id"] == "dns-retry-pattern"
            assert "related_ids" in first
            assert isinstance(first["related_ids"], list)
            assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in first["related_ids"]

    asyncio.run(_run())


def test_mcp_stdio_composite_tools_expose_actionable_outputs() -> None:
    """Composite tools should expose structured context, checklist evidence and precedence guidance over stdio."""

    corpus = _corpus_root()
    use_fixture_expectations = corpus == _FIXTURES.resolve()
    if not use_fixture_expectations:
        pytest.skip("fixture-only expectations (INSTRUCTIONS_ROOT override)")

    async def _run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "corporate_instructions_mcp"],
            cwd=str(_SERVER_DIR),
            env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            raw = _tool_text(
                await session.call_tool(
                    "resolve_instruction_context",
                    {"query": "retry DNS polly", "max_results": 3, "include_diagnostics": True},
                )
            )
            resolved = json.loads(raw)
            assert resolved["selected_ids"]
            assert resolved["resolution"]["actionable_context"]["normative_ids"]
            assert resolved["resolution"]["selection"]["strategy"]
            assert isinstance(resolved["resolution"].get("selection_rationale"), list)
            assert isinstance(resolved["resolution"].get("pending_evidence"), list)
            assert isinstance(resolved["resolution"].get("required_workspace_signals"), dict)
            assert isinstance(resolved["resolution"].get("next_repo_evidence_actions"), list)

            raw = _tool_text(await session.call_tool("get_normative_checklist", {"scenario": "mensageria_outbox"}))
            checklist = json.loads(raw)
            assert checklist["summary"]["required_items"] >= 3
            assert any(item["verification"] for item in checklist["items"])

            raw = _tool_text(
                await session.call_tool(
                    "detect_instruction_conflicts",
                    {"ids": "dns-retry-pattern,microservice-resilience-polly-timeouts-and-circuit-breaker"},
                )
            )
            conflicts = json.loads(raw)
            assert conflicts["relationships"]
            relationship = conflicts["relationships"][0]
            assert (
                relationship["precedence"]["winner_id"]
                == "microservice-resilience-polly-timeouts-and-circuit-breaker"
            )
            assert relationship["agent_guidance"]

            raw = _tool_text(
                await session.call_tool(
                    "validate_applicability",
                    {
                        "instruction_ids": ["microservice-authorization-resource-scope-and-audit"],
                        "target_artifact": {"path": "Api/Endpoints/ClienteEndpoints.cs"},
                        "workspace_evidence": ["HttpContext.User"],
                    },
                )
            )
            applicability = json.loads(raw)
            assert applicability["results"][0]["applicability"] == "applicable"

            raw = _tool_text(
                await session.call_tool(
                    "build_compliance_matrix",
                    {
                        "target_artifact": {"path": "Api/Endpoints/ClienteEndpoints.cs"},
                        "instruction_results": [
                            {
                                "instruction_id": "microservice-authorization-resource-scope-and-audit",
                                "kind": "policy",
                                "applicability": "applicable",
                            }
                        ],
                        "artifact_observations": [
                            {
                                "instruction_id": "microservice-authorization-resource-scope-and-audit",
                                "observation_type": "positive",
                                "value": "Authorization requirement found",
                            }
                        ],
                    },
                )
            )
            matrix = json.loads(raw)
            assert matrix["matrix"][0]["status"] == "conformant"

    asyncio.run(_run())


def test_mcp_stdio_get_context_triggers_contract_output() -> None:
    """STDIO contract: get_context_triggers returns deterministic plan-first orchestration output."""

    corpus = _corpus_root()

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

    async def _run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "corporate_instructions_mcp"],
            cwd=str(_SERVER_DIR),
            env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(payload, ensure_ascii=False)},
                )
            )
            data = json.loads(raw)
            assert data["schema_version"] == "1.0.0"
            assert data["contract_metadata"]["published_schema_version"] == "1.0.0"
            assert data["advanced_signals"]["decision_stability"]["level"] in {"low", "medium", "high"}
            assert data["scenario"]["scenario_id"] == "plan-crosscutting-async-migration"
            assert data["strategy"]["recommended_execution_mode"] == "plan_only"
            assert data["mcp_usage"]["level"] == "recommended"
            assert data["tool_sequence_mode"] == "recommended_order"
            assert "request_mentions_cross_cutting_concerns" in data["signal_sources"]["request_declared_signals"]
            assert data["fallbacks"]["when_no_policy_found"] == "follow_repo_and_label_gap"
            assert data["mcp_context_triggers"]["batch_required"] is True
            assert data["evidence_gate"]["phase"] == "preliminary"
            assert data["evidence_gate"]["reconciliation_status"] == "pending_batch"
            assert data["tool_sequence"]
            _assert_context_trigger_invariants(data)

    asyncio.run(_run())


def test_mcp_stdio_get_context_triggers_functional_scenarios_matrix() -> None:
    """STDIO functional matrix for canonical get_context_triggers scenarios."""

    corpus = _corpus_root()

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

    async def _run() -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "corporate_instructions_mcp"],
            cwd=str(_SERVER_DIR),
            env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()

            scenario_a_raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(base_payload, ensure_ascii=False)},
                )
            )
            scenario_a = json.loads(scenario_a_raw)
            assert scenario_a["strategy"]["recommended_execution_mode"] == "plan_only"
            assert scenario_a["contract_metadata"]["catalog_resource_id"] == "context-orchestration-catalog"
            assert scenario_a["mcp_usage"]["level"] == "recommended"
            assert scenario_a["tool_sequence_mode"] == "recommended_order"
            assert "request_mentions_cross_cutting_concerns" in scenario_a["signal_sources"]["request_declared_signals"]
            assert scenario_a["mcp_context_triggers"]["batch_required"] is True
            assert scenario_a["evidence_gate"]["phase"] == "preliminary"
            assert scenario_a["evidence_gate"]["must_reconcile_after_batch"] is True
            assert scenario_a["tool_sequence"]
            assert all(
                "failure_effect" in step and "fallback_on_failure" in step for step in scenario_a["tool_sequence"]
            )
            _assert_context_trigger_invariants(scenario_a)

            scenario_b_payload = json.loads(json.dumps(base_payload))
            scenario_b_payload["request"]["operation_mode"] = "debug"
            scenario_b_payload["request"]["wants_only_plan"] = False
            scenario_b_payload["request"]["mentions_cross_cutting_concerns"] = False
            scenario_b_payload["request"]["mentions_specific_files"] = True
            scenario_b_payload["request"]["mentions_current_file"] = True
            scenario_b_payload["workspace"]["repo_known"] = True
            scenario_b_raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(scenario_b_payload, ensure_ascii=False)},
                )
            )
            scenario_b = json.loads(scenario_b_raw)
            assert scenario_b["mcp_usage"]["level"] == "not_needed"
            assert scenario_b["strategy"]["should_use_mcp"] is False
            assert scenario_b["mcp_context_triggers"]["batch_required"] is False
            assert scenario_b["evidence_gate"]["reconciliation_status"] == "not_required"
            assert "repo_structure_known" in scenario_b["signal_sources"]["repo_observed_signals"]
            assert scenario_b["advanced_signals"]["plan_granularity"]["level"] == "coarse"
            _assert_context_trigger_invariants(scenario_b)

            scenario_c_payload = json.loads(json.dumps(base_payload))
            scenario_c_payload["request"]["mentions_public_contract"] = True
            scenario_c_payload["workspace"]["workspace_signals_known"] = False
            scenario_c_raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(scenario_c_payload, ensure_ascii=False)},
                )
            )
            scenario_c = json.loads(scenario_c_raw)
            assert scenario_c["mcp_usage"]["level"] == "required"
            assert scenario_c["strategy"]["should_stop_for_human_input"] is True
            assert scenario_c["stop_rules"]["stop_required"] is True
            assert scenario_c["evidence_gate"]["must_verify_workspace_signals"] is True
            _assert_context_trigger_invariants(scenario_c)

            scenario_d_payload = json.loads(json.dumps(base_payload))
            scenario_d_payload["workspace"]["has_mcp"] = False
            scenario_d_raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(scenario_d_payload, ensure_ascii=False)},
                )
            )
            scenario_d = json.loads(scenario_d_raw)
            assert scenario_d["mcp_usage"]["level"] == "not_needed"
            assert scenario_d["strategy"]["should_use_mcp"] is False
            assert scenario_d["mcp_context_triggers"]["batch_required"] is False
            assert scenario_d["evidence_gate"]["reconciliation_status"] == "not_required"
            _assert_context_trigger_invariants(scenario_d)

            scenario_e_payload = json.loads(json.dumps(base_payload))
            scenario_e_payload["context_state"]["mcp_batch_loaded"] = True
            scenario_e_raw = _tool_text(
                await session.call_tool(
                    "get_context_triggers",
                    {"input_payload": json.dumps(scenario_e_payload, ensure_ascii=False)},
                )
            )
            scenario_e = json.loads(scenario_e_raw)
            assert scenario_e["mcp_usage"]["level"] == "recommended"
            assert scenario_e["evidence_gate"]["phase"] == "reconciled"
            assert scenario_e["evidence_gate"]["reconciliation_status"] == "reconciled"
            assert "normative_batch_loaded" in scenario_e["signal_sources"]["batch_discovered_signals"]
            _assert_context_trigger_invariants(scenario_e)

    asyncio.run(_run())
