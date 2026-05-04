"""Applicability and compliance-matrix helpers for evidence-gated normative analysis."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any

from corporate_instructions_mcp.indexing import InstructionRecord, normalize_text

APPLICABILITY_STATES = {
    "applicable",
    "non_applicable",
    "hypothesis_only",
    "blocked_by_missing_evidence",
}

MATRIX_STATUSES = {
    "conformant",
    "partial_conformance",
    "non_conformance",
    "not_enforceable",
    "not_applicable",
    "insufficient_evidence",
}

_EVIDENCE_TYPES = {"positive", "negative", "absence_observed"}


@dataclass(frozen=True)
class EvidenceItem:
    value: str
    normalized_value: str
    evidence_type: str
    path: str | None = None
    symbol: str | None = None
    source: str | None = None


def normalize_path(value: str) -> str:
    """Normalize path for deterministic, cross-platform matching."""
    return value.replace("\\", "/").strip().lower()


def match_scope(scope: str | None, artifact_path: str) -> tuple[bool, str]:
    """Return (is_match, strategy) for scope matching."""
    if not scope:
        return True, "no_scope"
    normalized_scope = normalize_path(scope)
    normalized_path = normalize_path(artifact_path)
    return fnmatch(normalized_path, normalized_scope), "glob"


def parse_workspace_evidence(workspace_evidence: list[Any] | None) -> list[EvidenceItem]:
    """Parse accepted evidence payloads (string and object forms)."""
    if workspace_evidence is None:
        return []
    if not isinstance(workspace_evidence, list):
        raise ValueError("workspace_evidence must be an array when provided.")

    out: list[EvidenceItem] = []
    for entry in workspace_evidence:
        if isinstance(entry, str):
            value = entry.strip()
            if not value:
                continue
            out.append(EvidenceItem(value=value, normalized_value=normalize_text(value), evidence_type="positive"))
            continue
        if isinstance(entry, dict):
            value_raw = entry.get("value")
            value = str(value_raw).strip() if value_raw is not None else ""
            if not value:
                raise ValueError("workspace_evidence object entries require a non-empty 'value'.")
            evidence_type = str(entry.get("evidence_type", "positive")).strip().lower()
            if evidence_type not in _EVIDENCE_TYPES:
                raise ValueError(
                    "workspace_evidence evidence_type must be one of: positive, negative, absence_observed."
                )
            out.append(
                EvidenceItem(
                    value=value,
                    normalized_value=normalize_text(value),
                    evidence_type=evidence_type,
                    path=str(entry.get("path")).strip() if entry.get("path") else None,
                    symbol=str(entry.get("symbol")).strip() if entry.get("symbol") else None,
                    source=str(entry.get("source")).strip() if entry.get("source") else None,
                )
            )
            continue
        raise ValueError("workspace_evidence items must be strings or objects with 'value'.")
    return out


def _normalize_signals(raw_signals: object) -> list[str]:
    if isinstance(raw_signals, list):
        out = [str(item).strip() for item in raw_signals if str(item).strip()]
    else:
        out = []
    return out


def _signal_matches_signal_value(signal_norm: str, evidence_norm: str) -> bool:
    if not signal_norm or not evidence_norm:
        return False
    return signal_norm == evidence_norm or signal_norm in evidence_norm or evidence_norm in signal_norm


def _match_signals_by_type(signals: list[str], evidence_items: list[EvidenceItem], evidence_type: str) -> list[str]:
    normalized_signals = [(signal, normalize_text(signal)) for signal in signals]
    matched: set[str] = set()
    for signal, signal_norm in normalized_signals:
        for item in evidence_items:
            if item.evidence_type != evidence_type:
                continue
            if _signal_matches_signal_value(signal_norm, item.normalized_value):
                matched.add(signal)
                break
    return sorted(matched)


def _on_absence_state(meta: dict[str, Any]) -> str | None:
    value = str(meta.get("on_absence", "")).strip().lower()
    if value in APPLICABILITY_STATES:
        return value
    return None


def decide_applicability(
    rec: InstructionRecord,
    *,
    target_path: str,
    evidence_items: list[EvidenceItem],
) -> dict[str, Any]:
    """Decide applicability with conservative, evidence-gated behavior."""
    scope_match, scope_strategy = match_scope(rec.scope, target_path)
    workspace_evidence_required = bool(rec.raw_frontmatter.get("workspace_evidence_required"))
    required_workspace_signals = _normalize_signals(rec.raw_frontmatter.get("workspace_signals"))
    on_absence = _on_absence_state(rec.raw_frontmatter)

    matched_positive = _match_signals_by_type(required_workspace_signals, evidence_items, "positive")
    matched_negative = _match_signals_by_type(required_workspace_signals, evidence_items, "negative")
    matched_absence = _match_signals_by_type(required_workspace_signals, evidence_items, "absence_observed")
    matched_workspace_signals = sorted(set(matched_positive))
    missing_workspace_signals = [sig for sig in required_workspace_signals if sig not in matched_workspace_signals]

    applicability = "blocked_by_missing_evidence"
    reason = "Required workspace evidence is missing."

    if not scope_match:
        applicability = "non_applicable"
        reason = "Artifact path is out of declared scope."
    elif (rec.kind or "").lower() == "reference":
        applicability = "hypothesis_only"
        reason = "Reference can inform analysis, but is not enforceable as strong policy."
    elif not workspace_evidence_required:
        applicability = "applicable"
        reason = "Instruction is in scope and does not require workspace evidence."
    elif not required_workspace_signals:
        applicability = "blocked_by_missing_evidence"
        reason = "Policy requires workspace evidence but declares no usable workspace_signals."
    elif matched_positive and not (matched_negative or matched_absence):
        applicability = "applicable"
        reason = "Found positive workspace signals with no explicit contradictory evidence."
    elif matched_positive and (matched_negative or matched_absence):
        applicability = "hypothesis_only"
        reason = "Evidence is mixed (positive and blocking), so enforcement remains conservative."
    elif on_absence:
        applicability = on_absence
        reason = "No sufficient positive signal found; using instruction on_absence behavior."
    else:
        applicability = "blocked_by_missing_evidence"
        reason = "Required workspace evidence is missing."

    return {
        "instruction_id": rec.id,
        "kind": rec.kind,
        "scope_match": scope_match,
        "workspace_evidence_required": workspace_evidence_required,
        "required_workspace_signals": required_workspace_signals,
        "matched_workspace_signals": matched_workspace_signals,
        "missing_workspace_signals": missing_workspace_signals,
        "applicability": applicability,
        "reason": reason,
        "diagnostics": {
            "scope_match_strategy": scope_strategy,
            "evidence_positive_count": sum(1 for item in evidence_items if item.evidence_type == "positive"),
            "evidence_negative_count": sum(
                1 for item in evidence_items if item.evidence_type in {"negative", "absence_observed"}
            ),
            "used_on_absence": on_absence,
            "matched_negative_signals": matched_negative,
            "matched_absence_observed_signals": matched_absence,
        },
    }


def build_compliance_row(
    instruction_result: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one matrix row from applicability + observations."""
    applicability = str(instruction_result.get("applicability", "")).strip().lower()
    instruction_id = str(instruction_result.get("instruction_id", "")).strip()
    kind = str(instruction_result.get("kind", "")).strip()
    base_reason = str(instruction_result.get("reason", "")).strip()

    positives = [item for item in observations if str(item.get("observation_type", "")).strip().lower() == "positive"]
    gaps = [item for item in observations if str(item.get("observation_type", "")).strip().lower() == "gap"]
    deviations = [item for item in observations if str(item.get("observation_type", "")).strip().lower() == "deviation"]

    status = "insufficient_evidence"
    reason = "Applicable instruction without enough artifact observation."
    allowed_action = "Collect more direct observations before asserting conformance."

    if applicability == "non_applicable":
        status = "not_applicable"
        reason = "Instruction does not apply to the target artifact."
        allowed_action = "Skip enforcement for this artifact."
    elif applicability in {"hypothesis_only", "blocked_by_missing_evidence"}:
        status = "not_enforceable"
        reason = "Instruction relevance exists, but enforcement is blocked by applicability state."
        allowed_action = "Collect additional workspace evidence before enforcing."
    elif applicability == "applicable":
        if deviations:
            status = "non_conformance"
            reason = "Applicable instruction has at least one direct deviation observation."
            allowed_action = "Address the deviation before claiming conformance."
        elif positives and gaps:
            status = "partial_conformance"
            reason = "Applicable instruction has positive adherence signals and identified gaps."
            allowed_action = "Preserve positives and close identified gaps."
        elif positives and not gaps:
            status = "conformant"
            reason = "Applicable instruction has positive evidence with no identified gaps."
            allowed_action = "Keep current implementation and guard with tests."

    evidence: list[str] = []
    if base_reason:
        evidence.append(base_reason)
    for item in observations:
        value = str(item.get("value", "")).strip()
        if value:
            evidence.append(value)

    return {
        "instruction_id": instruction_id,
        "kind": kind,
        "decision": applicability,
        "evidence": evidence,
        "status": status,
        "allowed_action": allowed_action,
        "reason": reason,
    }
