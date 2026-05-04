"""Deterministic contract and routing engine for get_context_triggers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATALOG_FILE = "context-orchestration-catalog.json"
SUPPORTED_SCHEMA_VERSION = "1.0.0"

_OPERATION_MODE = {"analyze_only", "plan_only", "implement", "refactor", "debug", "review", "unknown"}
_AMBIGUITY_RISK = {"low", "medium", "high", "unknown"}
_SCENARIO_FAMILY = {"feature", "bugfix", "analysis", "plan", "review", "migration", "debug", "refactor", "unknown"}
_RECOMMENDED_MODE = {
    "plan_then_context_then_decide_then_execute",
    "context_then_plan_then_execute",
    "context_then_answer",
    "plan_only",
    "analysis_only",
    "stop_and_request_human_input",
}
_MCP_USAGE_LEVEL = {"required", "recommended", "not_needed"}
_REQUEST_REQUIRED_BOOL_FIELDS = (
    "mentions_current_file",
    "mentions_specific_files",
    "mentions_symbols",
    "mentions_cross_cutting_concerns",
    "mentions_public_contract",
    "mentions_new_infrastructure",
    "mentions_external_integration",
    "wants_only_plan",
)
_REQUEST_OPTIONAL_FIELDS: dict[str, Any] = {
    "user_goal": "",
    "explicit_deliverable": "",
    "wants_tests": False,
}
_WORKSPACE_REQUIRED_BOOL_FIELDS = (
    "repo_known",
    "current_file_available",
    "solution_available",
    "project_count_known",
    "has_mcp",
    "workspace_signals_known",
)
_WORKSPACE_OPTIONAL_FIELDS: dict[str, Any] = {"tech_stack_signals": []}
_CONSTRAINTS_REQUIRED_BOOL_FIELDS = ("prefer_plan_first", "allow_mcp_usage", "allow_repo_scan")
_CONSTRAINTS_REQUIRED_INT_FIELDS = ("max_search_iterations", "max_instruction_ids")
_CONSTRAINTS_OPTIONAL_FIELDS: dict[str, Any] = {"prefer_minimal_context": True}
_CONTEXT_STATE_ALLOWED_BOOL_FIELDS = (
    "repo_structure_loaded",
    "current_file_loaded",
    "target_files_loaded",
    "symbols_loaded",
    "mcp_index_loaded",
    "mcp_batch_loaded",
    "plan_already_created",
)


@dataclass
class ContractError(Exception):
    code: str
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


def load_routing_catalog() -> dict[str, Any]:
    path = Path(__file__).with_name(CATALOG_FILE)
    try:
        raw = path.read_text(encoding="utf-8")
        catalog = json.loads(raw)
    except FileNotFoundError as exc:
        raise ContractError("CATALOG_UNAVAILABLE", "Routing catalog file not found.", {"path": str(path)}) from exc
    except json.JSONDecodeError as exc:
        raise ContractError("CATALOG_UNAVAILABLE", "Routing catalog is not valid JSON.", {"path": str(path)}) from exc
    _validate_catalog(catalog)
    return catalog


def build_context_triggers(payload: dict[str, Any], *, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    cat = catalog or load_routing_catalog()
    req, workspace, context_state, constraints = _validate_input_payload(payload)

    scenario = _classify_scenario(req, cat)
    mcp_usage = _determine_mcp_usage(req, workspace, constraints, cat)
    should_use_mcp = bool(mcp_usage["level"] in {"required", "recommended"})
    signal_sources = _build_signal_sources(req, workspace, context_state, should_use_mcp)
    internal_derivations = {
        "should_use_mcp": should_use_mcp,
    }
    should_stop = bool(
        (req["mentions_public_contract"] and not workspace["workspace_signals_known"])
        or (req["mentions_new_infrastructure"] and not workspace["workspace_signals_known"])
        or (req["mentions_external_integration"] and not workspace["workspace_signals_known"])
    )
    should_plan_first = bool(
        req["wants_only_plan"]
        or constraints["prefer_plan_first"]
        or req["mentions_cross_cutting_concerns"]
        or req["mentions_public_contract"]
        or req["mentions_new_infrastructure"]
        or req["mentions_external_integration"]
        or req["ambiguity_level"] in {"medium", "high"}
        or req["risk_level"] in {"medium", "high"}
    )
    if should_stop:
        recommended_execution_mode = "stop_and_request_human_input"
    elif req["wants_only_plan"] or req["operation_mode"] == "plan_only":
        recommended_execution_mode = "plan_only"
    elif req["operation_mode"] == "analyze_only":
        recommended_execution_mode = "analysis_only"
    elif should_plan_first:
        recommended_execution_mode = "plan_then_context_then_decide_then_execute"
    else:
        recommended_execution_mode = "context_then_answer"

    if recommended_execution_mode not in _RECOMMENDED_MODE:
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            "Internal recommended execution mode is invalid.",
            {"recommended_execution_mode": recommended_execution_mode},
        )

    repo_context_triggers = {
        "must_read_current_file": bool(req["mentions_current_file"]),
        "must_scan_solution": bool(not workspace["repo_known"]),
        "must_scan_projects": bool(not req["mentions_specific_files"]),
        "must_search_symbols": bool(req["mentions_symbols"]),
        "must_search_concepts": bool(req["mentions_cross_cutting_concerns"] or not req["mentions_specific_files"]),
    }

    mcp_context_triggers = {
        "triggered": should_use_mcp,
        "reasons": list(mcp_usage["reasons"]),
        "retrieve_mode": "resolve_or_search",
        "search_query_count_min": 3 if should_use_mcp else 0,
        "search_query_count_max": constraints["max_search_iterations"] if should_use_mcp else 0,
        "max_instruction_ids": constraints["max_instruction_ids"] if should_use_mcp else 0,
        "batch_required": should_use_mcp,
    }

    evidence_gate = _build_evidence_gate(req, context_state, should_use_mcp)
    advanced_signals = _build_advanced_signals(req, scenario, should_use_mcp, should_stop, evidence_gate)

    tool_sequence = _build_tool_sequence(req, workspace, should_use_mcp)
    if req["wants_only_plan"]:
        forbidden_tools = {"apply_patch", "edit_file", "write_file", "run_build", "run_tests"}
        if any(step["tool"] in forbidden_tools for step in tool_sequence):
            raise ContractError(
                "INVALID_REQUEST_PAYLOAD",
                "Plan-only flow cannot contain execution tools.",
                {"forbidden_tool_detected": True},
            )

    output = {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "scenario": scenario,
        "strategy": {
            "should_plan_first": should_plan_first,
            "should_use_repo_tools_first": bool(constraints["allow_repo_scan"]),
            "should_use_mcp": internal_derivations["should_use_mcp"],
            "should_stop_for_human_input": should_stop,
            "should_ask_for_clarification_before_patch": False,
            "recommended_execution_mode": recommended_execution_mode,
        },
        "contract_metadata": {
            "published_schema_version": SUPPORTED_SCHEMA_VERSION,
            "catalog_resource_id": str(cat.get("resource_id", "")),
            "catalog_schema_version": str(cat.get("schema_version", "")),
        },
        "mcp_usage": mcp_usage,
        "signal_sources": signal_sources,
        "tool_sequence_mode": "recommended_order",
        "tool_sequence": tool_sequence,
        "repo_context_triggers": repo_context_triggers,
        "mcp_context_triggers": mcp_context_triggers,
        "evidence_gate": evidence_gate,
        "decision_output_requirements": {
            "must_label_fact_vs_hypothesis": True,
            "must_produce_bmad": True,
            "must_build_evidence_matrix": True,
            "must_cite_instruction_ids": True,
        },
        "stop_rules": {
            "stop_required": should_stop,
            "stop_reasons": _stop_reasons(req, should_stop),
            "human_input_required_if": list(cat["stop_rules"]),
        },
        "fallbacks": _build_fallbacks(cat),
        "advanced_signals": advanced_signals,
        "anti_patterns": list(cat["anti_patterns"]),
        "explanation": {
            "short_rationale": _short_rationale(req, should_use_mcp),
            "machine_summary": (
                f"plan_first={str(should_plan_first).lower()}; "
                f"repo_tools_first={str(constraints['allow_repo_scan']).lower()}; "
                f"mcp_usage_level={mcp_usage['level']}; "
                f"batch_required={str(mcp_context_triggers['batch_required']).lower()}; "
                f"stop_required={str(should_stop).lower()}"
            ),
        },
    }
    _validate_output_invariants(output)
    return output


def _validate_catalog(catalog: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "resource_id",
        "scenario_taxonomy",
        "tool_routing_rules",
        "evidence_gate_rules",
        "stop_rules",
        "fallback_rules",
        "anti_patterns",
    }
    missing = sorted(required - set(catalog))
    if missing:
        raise ContractError(
            "CATALOG_UNAVAILABLE",
            "Routing catalog is missing required sections.",
            {"missing": missing},
        )
    if catalog.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ContractError(
            "CATALOG_UNAVAILABLE",
            "Routing catalog schema_version is unsupported.",
            {"schema_version": catalog.get("schema_version")},
        )


def _validate_input_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    required_sections = {"schema_version", "request", "workspace", "context_state", "constraints"}
    if not isinstance(payload, dict):
        raise ContractError("INVALID_REQUEST_PAYLOAD", "Payload must be a JSON object.")
    missing = sorted(required_sections - set(payload))
    if missing:
        raise ContractError("INVALID_REQUEST_PAYLOAD", "Payload is missing required sections.", {"missing": missing})

    if payload["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        raise ContractError(
            "INVALID_SCHEMA_VERSION",
            "Unsupported schema_version for get_context_triggers.",
            {"schema_version": payload["schema_version"]},
        )

    request = _normalize_request(_require_dict(payload, "request"))
    workspace = _normalize_workspace(_require_dict(payload, "workspace"))
    context_state = _normalize_context_state(_require_dict(payload, "context_state"))
    constraints = _normalize_constraints(_require_dict(payload, "constraints"))

    if request["operation_mode"] not in _OPERATION_MODE:
        raise ContractError("INVALID_REQUEST_PAYLOAD", "Invalid request.operation_mode.")
    if request["ambiguity_level"] not in _AMBIGUITY_RISK:
        raise ContractError("INVALID_REQUEST_PAYLOAD", "Invalid request.ambiguity_level.")
    if request["risk_level"] not in _AMBIGUITY_RISK:
        raise ContractError("INVALID_REQUEST_PAYLOAD", "Invalid request.risk_level.")

    incompatible_plan_mode = bool(request["wants_only_plan"]) and request["operation_mode"] not in {
        "plan_only",
        "analyze_only",
        "unknown",
    }
    if incompatible_plan_mode:
        raise ContractError(
            "CONFLICTING_INPUT_FLAGS",
            "wants_only_plan=true conflicts with an execution-oriented operation_mode.",
            {"operation_mode": request["operation_mode"]},
        )

    return request, workspace, context_state, constraints


def _normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    normalized = _merge_optional(request, _REQUEST_OPTIONAL_FIELDS)
    _require_str_field(normalized, "operation_mode", section="request")
    _require_str_field(normalized, "ambiguity_level", section="request")
    _require_str_field(normalized, "risk_level", section="request")
    for key in _REQUEST_REQUIRED_BOOL_FIELDS:
        _require_bool_field(normalized, key, section="request")
    _require_str_field(normalized, "user_goal", section="request")
    _require_str_field(normalized, "explicit_deliverable", section="request")
    _require_bool_field(normalized, "wants_tests", section="request")
    return normalized


def _normalize_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    normalized = _merge_optional(workspace, _WORKSPACE_OPTIONAL_FIELDS)
    for key in _WORKSPACE_REQUIRED_BOOL_FIELDS:
        _require_bool_field(normalized, key, section="workspace")
    tech_stack_signals = normalized["tech_stack_signals"]
    if not isinstance(tech_stack_signals, list) or any(not isinstance(item, str) for item in tech_stack_signals):
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            "Field 'workspace.tech_stack_signals' must be an array of strings.",
        )
    return normalized


def _normalize_context_state(context_state: dict[str, Any]) -> dict[str, Any]:
    for key, value in context_state.items():
        if key in _CONTEXT_STATE_ALLOWED_BOOL_FIELDS and not isinstance(value, bool):
            raise ContractError(
                "INVALID_REQUEST_PAYLOAD",
                f"Field 'context_state.{key}' must be a boolean.",
            )
    return context_state


def _normalize_constraints(constraints: dict[str, Any]) -> dict[str, Any]:
    normalized = _merge_optional(constraints, _CONSTRAINTS_OPTIONAL_FIELDS)
    for key in _CONSTRAINTS_REQUIRED_BOOL_FIELDS:
        _require_bool_field(normalized, key, section="constraints")
    for key in _CONSTRAINTS_REQUIRED_INT_FIELDS:
        _require_positive_int_field(normalized, key, section="constraints")
    _require_bool_field(normalized, "prefer_minimal_context", section="constraints")
    return normalized


def _merge_optional(section: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(section)
    for key, default in defaults.items():
        if key not in normalized:
            normalized[key] = default
    return normalized


def _require_str_field(data: dict[str, Any], key: str, *, section: str) -> None:
    if key not in data or not isinstance(data[key], str):
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            f"Field '{section}.{key}' must be a string.",
        )


def _require_bool_field(data: dict[str, Any], key: str, *, section: str) -> None:
    if key not in data or not isinstance(data[key], bool):
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            f"Field '{section}.{key}' must be a boolean.",
        )


def _require_positive_int_field(data: dict[str, Any], key: str, *, section: str) -> None:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            f"Field '{section}.{key}' must be a positive integer.",
        )


def _require_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ContractError("INVALID_REQUEST_PAYLOAD", f"Section '{key}' must be an object.")
    return value


def _classify_scenario(req: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    catalog_scenarios = _scenario_id_by_signals(catalog)
    if req["wants_only_plan"] and req["mentions_cross_cutting_concerns"]:
        return {
            "scenario_id": catalog_scenarios.get(
                frozenset({"analysis_or_plan_only", "cross_cutting_domain"}),
                "plan-crosscutting-async-migration",
            ),
            "scenario_family": "plan",
            "scenario_confidence": 0.96,
        }
    if req["mentions_current_file"] and not req["mentions_cross_cutting_concerns"]:
        return {
            "scenario_id": catalog_scenarios.get(frozenset({"mentions_current_file", "local_scope"}), "bug-current-file-local"),
            "scenario_family": "bugfix",
            "scenario_confidence": 0.9,
        }
    if req["mentions_public_contract"]:
        return {
            "scenario_id": catalog_scenarios.get(frozenset({"public_contract_risk"}), "plan-public-contract-risk"),
            "scenario_family": "plan",
            "scenario_confidence": 0.91,
        }
    if req["mentions_new_infrastructure"]:
        return {
            "scenario_id": catalog_scenarios.get(frozenset({"new_infrastructure_risk"}), "plan-new-infrastructure-risk"),
            "scenario_family": "plan",
            "scenario_confidence": 0.9,
        }
    family = "analysis" if req["operation_mode"] == "analyze_only" else "unknown"
    if family not in _SCENARIO_FAMILY:
        family = "unknown"
    return {"scenario_id": "general-unknown", "scenario_family": family, "scenario_confidence": 0.6}


def _build_tool_sequence(req: dict[str, Any], workspace: dict[str, Any], should_use_mcp: bool) -> list[dict[str, Any]]:
    tools: list[tuple[str, str, str, str, str, str]] = []
    if req["mentions_current_file"]:
        tools.append(
            (
                "repo_read",
                "get_currentfile",
                "current file was explicitly mentioned",
                "current file content",
                "insufficient_file_context",
                "scan_repo_for_alternative_targets",
            )
        )

    if not req["mentions_specific_files"] and not workspace["repo_known"]:
        tools.append(
            (
                "repo_discovery",
                "get_projects_in_solution",
                "repo structure unknown and no explicit target files",
                "project list",
                "unknown_project_scope",
                "request_explicit_target_or_try_project_file_scan",
            )
        )
        tools.append(
            (
                "repo_discovery",
                "get_files_in_project",
                "enumerate likely target areas",
                "file list in selected project",
                "unable_to_identify_candidate_files",
                "switch_to_symbol_or_concept_search",
            )
        )

    if should_use_mcp:
        tools.append(
            (
                "normative_discovery",
                "corporate_instructions_search_instructions",
                "cross-cutting concern detected",
                "candidate instruction ids",
                "no_normative_candidates_found",
                "proceed_with_repo_evidence_and_mark_policy_gap",
            )
        )
        tools.append(
            (
                "normative_read",
                "corporate_instructions_get_instructions_batch",
                "policy cannot be applied from search results alone",
                "instruction bodies and frontmatter",
                "normative_evidence_incomplete",
                "defer_policy_application_and_request_additional_evidence",
            )
        )

    sequence: list[dict[str, Any]] = []
    for idx, (phase, tool, why, expected_output, failure_effect, fallback_on_failure) in enumerate(tools, start=1):
        sequence.append(
            {
                "order": idx,
                "phase": phase,
                "tool": tool,
                "required": True,
                "why": why,
                "expected_output": expected_output,
                "success_condition": "non-empty output",
                "failure_effect": failure_effect,
                "fallback_on_failure": fallback_on_failure,
            }
        )
    return sequence


def _scenario_id_by_signals(catalog: dict[str, Any]) -> dict[frozenset[str], str]:
    entries = catalog.get("scenario_taxonomy", [])
    if not isinstance(entries, list):
        return {}
    by_signals: dict[frozenset[str], str] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        scenario_id = item.get("scenario_id")
        signals = item.get("signals")
        if (
            isinstance(scenario_id, str)
            and scenario_id
            and isinstance(signals, list)
            and all(isinstance(signal, str) for signal in signals)
        ):
            by_signals[frozenset(signals)] = scenario_id
    return by_signals


def _build_evidence_gate(req: dict[str, Any], context_state: dict[str, Any], should_use_mcp: bool) -> dict[str, Any]:
    evidence_required_risk = bool(
        req["mentions_public_contract"]
        or req["mentions_new_infrastructure"]
        or req["mentions_external_integration"]
    )
    mcp_batch_loaded = bool(context_state.get("mcp_batch_loaded", False))
    must_reconcile_after_batch = should_use_mcp
    reconciled = bool(must_reconcile_after_batch and mcp_batch_loaded)

    if not must_reconcile_after_batch:
        phase = "preliminary"
        reconciliation_status = "not_required"
        reconciliation_reasons = ["no_normative_batch_required_for_scenario"]
    elif reconciled:
        phase = "reconciled"
        reconciliation_status = "reconciled"
        reconciliation_reasons = ["normative_batch_loaded", "policy_decision_reconciled_with_batch_evidence"]
    else:
        phase = "preliminary"
        reconciliation_status = "pending_batch"
        reconciliation_reasons = ["normative_batch_not_loaded_yet"]

    return {
        "required": should_use_mcp,
        "phase": phase,
        "must_verify_frontmatter": should_use_mcp,
        "must_verify_workspace_signals": evidence_required_risk,
        "must_reconcile_after_batch": must_reconcile_after_batch,
        "workspace_evidence_required_detected": evidence_required_risk,
        "reconciliation_status": reconciliation_status,
        "reconciliation_reasons": reconciliation_reasons,
        "apply_policy_without_batch": not must_reconcile_after_batch,
        "apply_policy_without_repo_evidence": not evidence_required_risk,
    }


def _build_fallbacks(catalog: dict[str, Any]) -> dict[str, str]:
    rules = catalog.get("fallback_rules", [])
    if not isinstance(rules, list):
        rules = []
    fallback_rules = [item for item in rules if isinstance(item, str)]
    return {
        "when_no_policy_found": fallback_rules[0] if len(fallback_rules) > 0 else "follow_repo_and_label_gap",
        "when_only_reference_found": fallback_rules[1] if len(fallback_rules) > 1 else "follow_repo_pattern_with_caveat",
        "when_workspace_evidence_missing": fallback_rules[2]
        if len(fallback_rules) > 2
        else "do_not_introduce_stack_by_inference",
    }


def _build_advanced_signals(
    req: dict[str, Any],
    scenario: dict[str, Any],
    should_use_mcp: bool,
    should_stop: bool,
    evidence_gate: dict[str, Any],
) -> dict[str, Any]:
    ambiguity = req["ambiguity_level"]
    risk = req["risk_level"]

    if should_stop:
        decision_stability_level = "low"
    elif ambiguity == "low" and risk == "low":
        decision_stability_level = "high"
    elif ambiguity == "high" or risk == "high":
        decision_stability_level = "low"
    else:
        decision_stability_level = "medium"

    if req["mentions_cross_cutting_concerns"] or should_use_mcp:
        plan_granularity_level = "fine"
    elif req["mentions_specific_files"] or req["mentions_current_file"]:
        plan_granularity_level = "coarse"
    else:
        plan_granularity_level = "balanced"

    scenario_conf = float(scenario.get("scenario_confidence", 0.0))
    strategy_conf = 0.75 if decision_stability_level == "medium" else (0.9 if decision_stability_level == "high" else 0.55)
    evidence_conf = 0.85 if evidence_gate.get("phase") == "reconciled" else 0.65
    stop_conf = 0.9 if should_stop else 0.7

    return {
        "decision_stability": {
            "level": decision_stability_level,
            "rubric": "derived_from_ambiguity_and_risk_levels_with_stop_override",
        },
        "plan_granularity": {
            "level": plan_granularity_level,
            "rubric": "fine_for_cross_cutting_or_mcp_flows_coarse_for_local_targeted_requests",
        },
        "confidence_by_layer": {
            "scenario": round(max(0.0, min(1.0, scenario_conf)), 2),
            "strategy": round(max(0.0, min(1.0, strategy_conf)), 2),
            "evidence_gate": round(max(0.0, min(1.0, evidence_conf)), 2),
            "stop_rules": round(max(0.0, min(1.0, stop_conf)), 2),
            "rubric": "layered_confidence_is_independent_and_not_transitive",
        },
    }


def _build_signal_sources(
    req: dict[str, Any],
    workspace: dict[str, Any],
    context_state: dict[str, Any],
    should_use_mcp: bool,
) -> dict[str, list[str]]:
    request_declared_signals: list[str] = []
    if req["mentions_current_file"]:
        request_declared_signals.append("request_mentions_current_file")
    if req["mentions_specific_files"]:
        request_declared_signals.append("request_mentions_specific_files")
    if req["mentions_symbols"]:
        request_declared_signals.append("request_mentions_symbols")
    if req["mentions_cross_cutting_concerns"]:
        request_declared_signals.append("request_mentions_cross_cutting_concerns")
    if req["mentions_public_contract"]:
        request_declared_signals.append("request_mentions_public_contract")
    if req["mentions_new_infrastructure"]:
        request_declared_signals.append("request_mentions_new_infrastructure")
    if req["mentions_external_integration"]:
        request_declared_signals.append("request_mentions_external_integration")

    repo_observed_signals: list[str] = []
    if workspace["repo_known"]:
        repo_observed_signals.append("repo_structure_known")
    if workspace["current_file_available"]:
        repo_observed_signals.append("current_file_available")
    if workspace["workspace_signals_known"]:
        repo_observed_signals.append("workspace_signals_known")
    if workspace["tech_stack_signals"]:
        repo_observed_signals.append("tech_stack_signals_present")
    if workspace["has_mcp"]:
        repo_observed_signals.append("mcp_available_in_workspace")

    batch_discovered_signals: list[str] = []
    if should_use_mcp and context_state.get("mcp_batch_loaded"):
        batch_discovered_signals.append("normative_batch_loaded")
        if req["mentions_cross_cutting_concerns"]:
            batch_discovered_signals.append("batch_confirms_cross_cutting_domain")
        if req["mentions_public_contract"] or req["mentions_new_infrastructure"] or req["mentions_external_integration"]:
            batch_discovered_signals.append("batch_confirms_policy_sensitive_change")

    return {
        "request_declared_signals": request_declared_signals,
        "repo_observed_signals": repo_observed_signals,
        "batch_discovered_signals": batch_discovered_signals,
    }


def _validate_output_invariants(output: dict[str, Any]) -> None:
    strategy = output.get("strategy", {})
    mcp_usage = output.get("mcp_usage", {})
    contract_metadata = output.get("contract_metadata", {})
    advanced_signals = output.get("advanced_signals", {})
    mcp_context = output.get("mcp_context_triggers", {})
    stop_rules = output.get("stop_rules", {})
    evidence_gate = output.get("evidence_gate", {})
    signal_sources = output.get("signal_sources", {})
    tool_sequence = output.get("tool_sequence", [])

    if not isinstance(strategy, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: strategy must be an object.")
    if not isinstance(mcp_usage, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: mcp_usage must be an object.")
    if not isinstance(contract_metadata, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: contract_metadata must be an object.")
    if not isinstance(advanced_signals, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: advanced_signals must be an object.")
    if not isinstance(mcp_context, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: mcp_context_triggers must be an object.")
    if not isinstance(stop_rules, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: stop_rules must be an object.")
    if not isinstance(evidence_gate, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: evidence_gate must be an object.")
    if not isinstance(signal_sources, dict):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: signal_sources must be an object.")
    if not isinstance(tool_sequence, list):
        raise ContractError("INVARIANT_VIOLATION", "Output invariant failed: tool_sequence must be an array.")
    for key in ("published_schema_version", "catalog_resource_id", "catalog_schema_version"):
        value = contract_metadata.get(key, "")
        if not isinstance(value, str) or not value:
            raise ContractError(
                "INVARIANT_VIOLATION",
                f"Output invariant failed: contract_metadata.{key} must be a non-empty string.",
            )
    decision_stability = advanced_signals.get("decision_stability", {})
    plan_granularity = advanced_signals.get("plan_granularity", {})
    confidence_by_layer = advanced_signals.get("confidence_by_layer", {})
    if not isinstance(decision_stability, dict) or decision_stability.get("level") not in {"low", "medium", "high"}:
        raise ContractError(
            "INVARIANT_VIOLATION",
            "Output invariant failed: advanced_signals.decision_stability.level is invalid.",
        )
    if not isinstance(plan_granularity, dict) or plan_granularity.get("level") not in {"coarse", "balanced", "fine"}:
        raise ContractError(
            "INVARIANT_VIOLATION",
            "Output invariant failed: advanced_signals.plan_granularity.level is invalid.",
        )
    if not isinstance(confidence_by_layer, dict):
        raise ContractError(
            "INVARIANT_VIOLATION",
            "Output invariant failed: advanced_signals.confidence_by_layer must be an object.",
        )
    for key in ("scenario", "strategy", "evidence_gate", "stop_rules"):
        value = confidence_by_layer.get(key)
        if not isinstance(value, float | int) or value < 0 or value > 1:
            raise ContractError(
                "INVARIANT_VIOLATION",
                f"Output invariant failed: advanced_signals.confidence_by_layer.{key} must be in [0,1].",
            )
    for key in ("request_declared_signals", "repo_observed_signals", "batch_discovered_signals"):
        values = signal_sources.get(key, [])
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise ContractError(
                "INVARIANT_VIOLATION",
                f"Output invariant failed: signal_sources.{key} must be an array of strings.",
            )

    # Invariant 1: plan-only cannot contain mutable tools and must plan first.
    if strategy.get("recommended_execution_mode") == "plan_only":
        if strategy.get("should_plan_first") is not True:
            raise ContractError(
                "INVARIANT_VIOLATION",
                "Output invariant failed: plan_only mode requires should_plan_first=true.",
            )
        forbidden_tools = {"apply_patch", "edit_file", "write_file", "run_build", "run_tests"}
        if any(isinstance(step, dict) and step.get("tool") in forbidden_tools for step in tool_sequence):
            raise ContractError(
                "INVARIANT_VIOLATION",
                "Output invariant failed: plan_only mode cannot include mutable tools.",
            )

    # Invariant 2: if MCP is not needed, batch cannot be required.
    if mcp_usage.get("level") == "not_needed" and mcp_context.get("batch_required") is not False:
        raise ContractError(
            "INVARIANT_VIOLATION",
            "Output invariant failed: mcp_usage.level=not_needed requires batch_required=false.",
        )

    # Invariant 3: if stop is required, reasons cannot be empty.
    if stop_rules.get("stop_required") is True:
        stop_reasons = stop_rules.get("stop_reasons", [])
        if not isinstance(stop_reasons, list) or not stop_reasons:
            raise ContractError(
                "INVARIANT_VIOLATION",
                "Output invariant failed: stop_required=true requires non-empty stop_reasons.",
            )

    # Invariant 4: workspace evidence detection requires workspace verification.
    if evidence_gate.get("workspace_evidence_required_detected") is True and evidence_gate.get(
        "must_verify_workspace_signals"
    ) is not True:
        raise ContractError(
            "INVARIANT_VIOLATION",
            "Output invariant failed: workspace evidence detection requires workspace verification.",
        )


def _determine_mcp_usage(
    req: dict[str, Any], workspace: dict[str, Any], constraints: dict[str, Any], catalog: dict[str, Any]
) -> dict[str, Any]:
    if not constraints["allow_mcp_usage"]:
        usage = {"level": "not_needed", "reasons": ["mcp_usage_disabled_by_constraint"]}
    elif not workspace["has_mcp"]:
        usage = {"level": "not_needed", "reasons": ["mcp_unavailable_in_workspace"]}
    elif req["mentions_public_contract"] or req["mentions_new_infrastructure"] or req["mentions_external_integration"]:
        usage = {"level": "required", "reasons": ["normative_risk_requires_mcp_evidence"]}
    elif _catalog_indicates_cross_cutting_requires_mcp(req, catalog):
        usage = {"level": "recommended", "reasons": ["cross_cutting_policy_domain_detected"]}
    else:
        usage = {"level": "not_needed", "reasons": []}

    if usage["level"] not in _MCP_USAGE_LEVEL:
        raise ContractError(
            "INVALID_REQUEST_PAYLOAD",
            "Internal MCP usage level is invalid.",
            {"mcp_usage_level": usage["level"]},
        )

    if usage["level"] in {"required", "recommended"}:
        if req["mentions_public_contract"]:
            usage["reasons"].append("public_contract_risk")
        if req["mentions_new_infrastructure"]:
            usage["reasons"].append("new_infrastructure_risk")
        if req["mentions_external_integration"]:
            usage["reasons"].append("external_integration_risk")
    return usage


def _catalog_indicates_cross_cutting_requires_mcp(req: dict[str, Any], catalog: dict[str, Any]) -> bool:
    if not req["mentions_cross_cutting_concerns"]:
        return False
    rules = catalog.get("tool_routing_rules", [])
    if not isinstance(rules, list):
        return True
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_if = rule.get("if", {})
        rule_then = rule.get("then", {})
        if (
            isinstance(rule_if, dict)
            and rule_if.get("mentions_cross_cutting_concerns") is True
            and isinstance(rule_then, dict)
            and isinstance(rule_then.get("append_tools"), list)
            and "corporate_instructions_get_instructions_batch" in rule_then["append_tools"]
        ):
            return True
    return False


def _stop_reasons(req: dict[str, Any], should_stop: bool) -> list[str]:
    if not should_stop:
        return []
    reasons: list[str] = []
    if req["mentions_public_contract"]:
        reasons.append("public_contract_change_without_evidence")
    if req["mentions_new_infrastructure"]:
        reasons.append("new_infrastructure_without_evidence")
    if req["mentions_external_integration"]:
        reasons.append("external_integration_without_evidence")
    return reasons


def _short_rationale(req: dict[str, Any], should_use_mcp: bool) -> str:
    if req["wants_only_plan"] and should_use_mcp:
        return "Cross-cutting plan request requires repo discovery, MCP retrieval and evidence gate before planning."
    if req["wants_only_plan"]:
        return "Plan-only request requires context discovery before defining execution steps."
    if should_use_mcp:
        return "Cross-cutting execution request requires MCP retrieval and evidence gate."
    return "Local request can be handled by repository context without normative retrieval."
