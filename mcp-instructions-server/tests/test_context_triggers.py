from __future__ import annotations

from copy import deepcopy

import pytest
from corporate_instructions_mcp.context_triggers import (
    ContractError,
    _validate_output_invariants,
    build_context_triggers,
    load_routing_catalog,
)


def _sample_payload() -> dict[str, object]:
    return {
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


def test_catalog_contains_required_sections() -> None:
    catalog = load_routing_catalog()
    assert catalog["schema_version"] == "1.0.0"
    assert catalog["resource_id"] == "context-orchestration-catalog"
    assert isinstance(catalog["scenario_taxonomy"], list)
    assert isinstance(catalog["tool_routing_rules"], list)
    assert isinstance(catalog["evidence_gate_rules"], list)
    assert isinstance(catalog["stop_rules"], list)
    assert isinstance(catalog["fallback_rules"], list)


def test_build_context_triggers_plan_cross_cutting_shape() -> None:
    output = build_context_triggers(_sample_payload())
    assert output["schema_version"] == "1.0.0"
    assert output["contract_metadata"]["published_schema_version"] == "1.0.0"
    assert output["contract_metadata"]["catalog_resource_id"] == "context-orchestration-catalog"
    assert output["advanced_signals"]["decision_stability"]["level"] in {"low", "medium", "high"}
    assert output["advanced_signals"]["plan_granularity"]["level"] in {"coarse", "balanced", "fine"}
    assert 0 <= output["advanced_signals"]["confidence_by_layer"]["scenario"] <= 1
    assert output["scenario"]["scenario_id"] == "plan-crosscutting-async-migration"
    assert output["scenario"]["scenario_family"] == "plan"
    assert output["strategy"]["recommended_execution_mode"] == "plan_only"
    assert output["strategy"]["should_plan_first"] is True
    assert output["strategy"]["should_use_mcp"] is True
    assert output["mcp_usage"]["level"] == "recommended"
    assert output["signal_sources"]["request_declared_signals"]
    assert "request_mentions_cross_cutting_concerns" in output["signal_sources"]["request_declared_signals"]
    assert output["tool_sequence_mode"] == "recommended_order"
    assert output["mcp_context_triggers"]["batch_required"] is True
    assert output["evidence_gate"]["phase"] == "preliminary"
    assert output["evidence_gate"]["must_reconcile_after_batch"] is True
    assert output["evidence_gate"]["reconciliation_status"] == "pending_batch"
    assert output["evidence_gate"]["apply_policy_without_batch"] is False
    assert output["decision_output_requirements"]["must_produce_bmad"] is True
    assert output["tool_sequence"]


def test_tool_sequence_ordered_and_contains_only_read_tools_for_plan_only() -> None:
    output = build_context_triggers(_sample_payload())
    sequence = output["tool_sequence"]
    orders = [step["order"] for step in sequence]
    assert orders == sorted(orders)
    tool_names = [step["tool"] for step in sequence]
    forbidden = {"apply_patch", "edit_file", "write_file", "run_build", "run_tests"}
    assert forbidden.isdisjoint(tool_names)
    for step in sequence:
        assert isinstance(step["failure_effect"], str) and step["failure_effect"]
        assert isinstance(step["fallback_on_failure"], str) and step["fallback_on_failure"]


def test_mentions_current_file_prepends_get_currentfile() -> None:
    payload = _sample_payload()
    payload["request"]["mentions_current_file"] = True
    output = build_context_triggers(payload)
    assert output["repo_context_triggers"]["must_read_current_file"] is True
    assert output["tool_sequence"][0]["tool"] == "get_currentfile"


def test_public_contract_without_workspace_signals_forces_human_stop() -> None:
    payload = _sample_payload()
    payload["request"]["mentions_public_contract"] = True
    output = build_context_triggers(payload)
    assert output["strategy"]["should_plan_first"] is True
    assert output["strategy"]["should_stop_for_human_input"] is True
    assert output["mcp_usage"]["level"] == "required"
    assert output["stop_rules"]["stop_required"] is True
    assert output["evidence_gate"]["must_verify_workspace_signals"] is True


def test_mentions_new_infrastructure_without_workspace_signals_sets_fallback() -> None:
    payload = _sample_payload()
    payload["request"]["mentions_new_infrastructure"] = True
    payload["workspace"]["workspace_signals_known"] = False
    output = build_context_triggers(payload)
    assert (
        output["fallbacks"]["when_workspace_evidence_missing"]
        == "do_not_introduce_stack_by_inference"
    )
    assert output["stop_rules"]["stop_required"] is True


def test_invalid_schema_version_raises_contract_error() -> None:
    payload = _sample_payload()
    payload["schema_version"] = "9.0.0"
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload)
    assert exc_info.value.code == "INVALID_SCHEMA_VERSION"


def test_conflicting_plan_only_flags_raise_contract_error() -> None:
    payload = _sample_payload()
    payload["request"]["operation_mode"] = "implement"
    payload["request"]["wants_only_plan"] = True
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload)
    assert exc_info.value.code == "CONFLICTING_INPUT_FLAGS"


def test_missing_required_section_raises_contract_error() -> None:
    payload = _sample_payload()
    payload_no_constraints = deepcopy(payload)
    payload_no_constraints.pop("constraints")
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload_no_constraints)
    assert exc_info.value.code == "INVALID_REQUEST_PAYLOAD"


def test_optional_fields_can_be_omitted_with_defaults() -> None:
    payload = _sample_payload()
    payload["request"].pop("user_goal")
    payload["request"].pop("explicit_deliverable")
    payload["request"].pop("wants_tests")
    payload["workspace"].pop("tech_stack_signals")
    payload["constraints"].pop("prefer_minimal_context")

    output = build_context_triggers(payload)
    assert output["schema_version"] == "1.0.0"
    assert output["strategy"]["recommended_execution_mode"] == "plan_only"


def test_invalid_request_operation_mode_raises_contract_error() -> None:
    payload = _sample_payload()
    payload["request"]["operation_mode"] = "ship_it_now"
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload)
    assert exc_info.value.code == "INVALID_REQUEST_PAYLOAD"


def test_invalid_workspace_shape_raises_contract_error() -> None:
    payload = _sample_payload()
    payload["workspace"] = "not-an-object"
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload)
    assert exc_info.value.code == "INVALID_REQUEST_PAYLOAD"


def test_invalid_constraints_integer_type_raises_contract_error() -> None:
    payload = _sample_payload()
    payload["constraints"]["max_search_iterations"] = "5"
    with pytest.raises(ContractError) as exc_info:
        build_context_triggers(payload)
    assert exc_info.value.code == "INVALID_REQUEST_PAYLOAD"


def test_local_case_without_cross_cutting_marks_mcp_not_needed() -> None:
    payload = _sample_payload()
    payload["request"]["operation_mode"] = "debug"
    payload["request"]["wants_only_plan"] = False
    payload["request"]["mentions_cross_cutting_concerns"] = False
    payload["workspace"]["repo_known"] = True

    output = build_context_triggers(payload)
    assert output["mcp_usage"]["level"] == "not_needed"
    assert output["strategy"]["should_use_mcp"] is False
    assert output["mcp_context_triggers"]["batch_required"] is False
    assert output["evidence_gate"]["must_reconcile_after_batch"] is False
    assert output["evidence_gate"]["reconciliation_status"] == "not_required"
    assert output["evidence_gate"]["apply_policy_without_batch"] is True


@pytest.mark.parametrize(
    "user_goal",
    [
        "quero um plano detalhado para migrar este fluxo para processamento assíncrono",
        "preciso de um plano para migrar este fluxo para async",
        "elabore um plano para migração assíncrona desse fluxo",
    ],
)
def test_cross_cutting_plan_classification_is_stable_for_lexical_variations(user_goal: str) -> None:
    payload = _sample_payload()
    payload["request"]["user_goal"] = user_goal
    output = build_context_triggers(payload)
    assert output["scenario"]["scenario_family"] == "plan"
    assert output["strategy"]["recommended_execution_mode"] == "plan_only"
    assert output["mcp_usage"]["level"] == "recommended"


def test_evidence_gate_reconciles_after_batch_load() -> None:
    payload = _sample_payload()
    payload["context_state"]["mcp_batch_loaded"] = True

    output = build_context_triggers(payload)
    assert output["evidence_gate"]["phase"] == "reconciled"
    assert output["evidence_gate"]["reconciliation_status"] == "reconciled"
    assert "normative_batch_loaded" in output["evidence_gate"]["reconciliation_reasons"]


def test_invariant_mcp_not_needed_requires_batch_not_required() -> None:
    payload = _sample_payload()
    payload["request"]["operation_mode"] = "debug"
    payload["request"]["wants_only_plan"] = False
    payload["request"]["mentions_cross_cutting_concerns"] = False

    output = build_context_triggers(payload)
    assert output["mcp_usage"]["level"] == "not_needed"
    assert output["mcp_context_triggers"]["batch_required"] is False


def test_invariant_stop_required_has_non_empty_reasons() -> None:
    payload = _sample_payload()
    payload["request"]["mentions_public_contract"] = True
    payload["workspace"]["workspace_signals_known"] = False

    output = build_context_triggers(payload)
    assert output["stop_rules"]["stop_required"] is True
    assert output["stop_rules"]["stop_reasons"]


def test_invariant_workspace_evidence_requires_workspace_verification() -> None:
    payload = _sample_payload()
    payload["request"]["mentions_public_contract"] = True

    output = build_context_triggers(payload)
    assert output["evidence_gate"]["workspace_evidence_required_detected"] is True
    assert output["evidence_gate"]["must_verify_workspace_signals"] is True


def test_validate_output_invariants_raises_for_invalid_payload() -> None:
    with pytest.raises(ContractError) as exc_info:
        _validate_output_invariants(
            {
                "strategy": {"recommended_execution_mode": "plan_only", "should_plan_first": False},
                "mcp_usage": {"level": "not_needed"},
                "contract_metadata": {
                    "published_schema_version": "1.0.0",
                    "catalog_resource_id": "context-orchestration-catalog",
                    "catalog_schema_version": "1.0.0",
                },
                "advanced_signals": {
                    "decision_stability": {"level": "low"},
                    "plan_granularity": {"level": "fine"},
                    "confidence_by_layer": {
                        "scenario": 0.8,
                        "strategy": 0.8,
                        "evidence_gate": 0.8,
                        "stop_rules": 0.8,
                    },
                },
                "mcp_context_triggers": {"batch_required": True},
                "stop_rules": {"stop_required": True, "stop_reasons": []},
                "evidence_gate": {
                    "workspace_evidence_required_detected": True,
                    "must_verify_workspace_signals": False,
                },
                "signal_sources": {
                    "request_declared_signals": [],
                    "repo_observed_signals": [],
                    "batch_discovered_signals": [],
                },
                "tool_sequence": [],
            }
        )
    assert exc_info.value.code == "INVARIANT_VIOLATION"


def test_signal_sources_keep_request_stable_when_workspace_changes() -> None:
    payload_a = _sample_payload()
    payload_b = deepcopy(payload_a)
    payload_b["workspace"]["repo_known"] = True
    payload_b["workspace"]["current_file_available"] = True

    out_a = build_context_triggers(payload_a)
    out_b = build_context_triggers(payload_b)

    assert out_a["signal_sources"]["request_declared_signals"] == out_b["signal_sources"]["request_declared_signals"]
    assert out_a["signal_sources"]["batch_discovered_signals"] == out_b["signal_sources"]["batch_discovered_signals"]
    assert out_a["signal_sources"]["repo_observed_signals"] != out_b["signal_sources"]["repo_observed_signals"]


def test_signal_sources_batch_discovered_only_after_batch_load() -> None:
    payload = _sample_payload()
    out_pre = build_context_triggers(payload)
    assert out_pre["signal_sources"]["batch_discovered_signals"] == []

    payload["context_state"]["mcp_batch_loaded"] = True
    out_post = build_context_triggers(payload)
    assert "normative_batch_loaded" in out_post["signal_sources"]["batch_discovered_signals"]


def test_fallbacks_are_sourced_from_catalog() -> None:
    payload = _sample_payload()
    output = build_context_triggers(payload)
    assert output["fallbacks"]["when_no_policy_found"] == "follow_repo_and_label_gap"
    assert output["fallbacks"]["when_only_reference_found"] == "follow_repo_pattern_with_caveat"
    assert output["fallbacks"]["when_workspace_evidence_missing"] == "do_not_introduce_stack_by_inference"


def test_scenario_can_be_driven_by_catalog_taxonomy() -> None:
    payload = _sample_payload()
    catalog = load_routing_catalog()
    custom_catalog = deepcopy(catalog)
    taxonomy = list(custom_catalog["scenario_taxonomy"])
    taxonomy.append(
        {
            "scenario_id": "plan-crosscutting-from-catalog",
            "family": "plan",
            "signals": ["analysis_or_plan_only", "cross_cutting_domain"],
        }
    )
    custom_catalog["scenario_taxonomy"] = taxonomy

    output = build_context_triggers(payload, catalog=custom_catalog)
    assert output["scenario"]["scenario_id"] == "plan-crosscutting-from-catalog"


def test_advanced_signals_reflect_local_low_risk_case() -> None:
    payload = _sample_payload()
    payload["request"]["operation_mode"] = "debug"
    payload["request"]["wants_only_plan"] = False
    payload["request"]["mentions_cross_cutting_concerns"] = False
    payload["request"]["mentions_current_file"] = True
    payload["request"]["mentions_specific_files"] = True
    payload["request"]["ambiguity_level"] = "low"
    payload["request"]["risk_level"] = "low"

    output = build_context_triggers(payload)
    assert output["advanced_signals"]["decision_stability"]["level"] == "high"
    assert output["advanced_signals"]["plan_granularity"]["level"] == "coarse"
