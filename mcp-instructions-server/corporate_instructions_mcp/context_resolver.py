"""Composite deterministic resolvers for context/checklist/conflict workflows."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from corporate_instructions_mcp.indexing import PRIORITY_RANK, InstructionRecord, normalize_text, summarize_body, tokenize_query

_KIND_RANK = {
    "policy": 3,
    "standard": 2,
    "guideline": 2,
    "reference": 1,
}

_LOW_SIGNAL_REFERENCE_TERMS = {
    "api",
    "cache",
    "circuit",
    "breaker",
    "correlation",
    "details",
    "http",
    "httpclient",
    "integration",
    "problem",
    "resiliencia",
    "retry",
    "timeout",
    "validacao",
    "validation",
}

_THEME_QUERY_HINTS: dict[str, set[str]] = {
    "architecture": {"arquitetura", "architecture", "estruturar", "camadas", "layering", "dominio", "projeto"},
    "observability": {"observabilidade", "observability", "instrumentar", "opentelemetry", "tracing", "metrics"},
    "integration": {"integracao", "integration", "externa", "api", "httpclient", "resiliencia", "resilience"},
}

_THEME_TAG_HINTS: dict[str, set[str]] = {
    "architecture": {"architecture", "layering", "clean-architecture", "domain", "repository", "interfaces"},
    "observability": {"observability", "opentelemetry", "tracing", "metrics", "health", "logging"},
    "integration": {"integration", "httpclient", "api", "contracts", "resilience", "serialization"},
}

_THEME_MIN_STRENGTH = 2


@dataclass(frozen=True)
class ChecklistScenarioItem:
    key: str
    title: str
    requirement_level: str
    why: str
    instruction_ids: list[str]
    verification: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChecklistScenario:
    key: str
    title: str
    objective: str
    checklist: list[ChecklistScenarioItem]


def _brief(rec: InstructionRecord) -> dict[str, Any]:
    return {
        "id": rec.id,
        "title": rec.title,
        "kind": rec.kind,
        "priority": rec.priority,
        "scope": rec.scope,
        "tags": rec.tags,
        "workspace_evidence_required": bool(rec.raw_frontmatter.get("workspace_evidence_required")),
        "workspace_signals": rec.raw_frontmatter.get("workspace_signals", []),
        "summary": summarize_body(rec.body, 220),
    }


def _has_specific_reference_signal(row: dict[str, Any]) -> bool:
    matched = row.get("match_explanation", {}).get("matched_user_terms") or []
    return any(isinstance(term, str) and term not in _LOW_SIGNAL_REFERENCE_TERMS for term in matched)


def _quoted_phrases(text: str) -> list[str]:
    return [p.strip() for p in re.findall(r'"([^"]{3,80})"', text) if p.strip()]


def _query_themes(query: str) -> set[str]:
    query_tokens = {normalize_text(token) for token in tokenize_query(query)}
    return {theme for theme, hints in _THEME_QUERY_HINTS.items() if query_tokens & hints}


def _row_theme_strength(row: dict[str, Any], theme: str) -> int:
    hints = _THEME_TAG_HINTS.get(theme, set())
    if not hints:
        return 0
    tags = {normalize_text(str(tag)) for tag in (row.get("tags") or []) if isinstance(tag, str)}
    title = str(row.get("title") or row.get("source_title") or "")
    title_tokens = {normalize_text(token) for token in tokenize_query(title)}
    return len(tags & hints) + len(title_tokens & hints)


def _literal_scope_segments(scope: str | None) -> list[str]:
    if not scope:
        return []
    parts = str(scope).replace("\\", "/").lower().split("/")
    out: list[str] = []
    for part in parts:
        literal = re.sub(r"[\*\?\[\]\{\}]", "", part).strip()
        if literal:
            out.append(literal)
    return out


def _scope_specificity(scope: str | None) -> int:
    return sum(len(part) for part in _literal_scope_segments(scope))


def _is_subsequence(parts: list[str], candidate: list[str]) -> bool:
    if not parts:
        return False
    pos = 0
    for item in candidate:
        if item == parts[pos]:
            pos += 1
            if pos == len(parts):
                return True
    return False


def _scope_relation(a_scope: str | None, b_scope: str | None) -> str:
    if not a_scope or not b_scope:
        return "unknown"
    if a_scope == b_scope:
        return "same"
    a_parts = _literal_scope_segments(a_scope)
    b_parts = _literal_scope_segments(b_scope)
    if not a_parts or not b_parts:
        return "unknown"
    if _is_subsequence(a_parts, b_parts):
        return "a_broader_than_b"
    if _is_subsequence(b_parts, a_parts):
        return "b_broader_than_a"
    return "overlap"


def _compare_scope(a: InstructionRecord, b: InstructionRecord) -> dict[str, Any]:
    relation = _scope_relation(a.scope, b.scope)
    if relation == "b_broader_than_a":
        return {"winner_id": a.id, "reason": "more_specific_scope", "relation": relation}
    if relation == "a_broader_than_b":
        return {"winner_id": b.id, "reason": "more_specific_scope", "relation": relation}
    return {"winner_id": None, "reason": None, "relation": relation}


def _compare_kind(a: InstructionRecord, b: InstructionRecord) -> dict[str, Any]:
    a_rank = _KIND_RANK.get((a.kind or "").lower(), 0)
    b_rank = _KIND_RANK.get((b.kind or "").lower(), 0)
    if a_rank > b_rank:
        return {"winner_id": a.id, "reason": "stronger_kind", "a_rank": a_rank, "b_rank": b_rank}
    if b_rank > a_rank:
        return {"winner_id": b.id, "reason": "stronger_kind", "a_rank": a_rank, "b_rank": b_rank}
    return {"winner_id": None, "reason": None, "a_rank": a_rank, "b_rank": b_rank}


def _compare_priority(a: InstructionRecord, b: InstructionRecord) -> dict[str, Any]:
    a_rank = PRIORITY_RANK.get(a.priority or "", 0)
    b_rank = PRIORITY_RANK.get(b.priority or "", 0)
    if a_rank > b_rank:
        return {"winner_id": a.id, "reason": "higher_priority", "a_rank": a_rank, "b_rank": b_rank}
    if b_rank > a_rank:
        return {"winner_id": b.id, "reason": "higher_priority", "a_rank": a_rank, "b_rank": b_rank}
    return {"winner_id": None, "reason": None, "a_rank": a_rank, "b_rank": b_rank}


def _topic_overlap(a: InstructionRecord, b: InstructionRecord) -> dict[str, Any]:
    shared_tags = sorted(set(a.tags) & set(b.tags))
    title_a = set(tokenize_query(a.title))
    title_b = set(tokenize_query(b.title))
    shared_title_terms = sorted(title_a & title_b)
    score = len(shared_tags) + (0.5 * len(shared_title_terms))
    return {
        "shared_tags": shared_tags,
        "shared_title_terms": shared_title_terms,
        "score": score,
    }


def _precedence(a: InstructionRecord, b: InstructionRecord) -> dict[str, Any]:
    scope_cmp = _compare_scope(a, b)
    kind_cmp = _compare_kind(a, b)
    priority_cmp = _compare_priority(a, b)

    winner_id = scope_cmp["winner_id"] or kind_cmp["winner_id"] or priority_cmp["winner_id"]
    loser_id = None
    if winner_id == a.id:
        loser_id = b.id
    elif winner_id == b.id:
        loser_id = a.id

    reasons = [x["reason"] for x in (scope_cmp, kind_cmp, priority_cmp) if x.get("reason")]
    explanation: list[str] = []
    if scope_cmp["reason"]:
        explanation.append(f"{scope_cmp['winner_id']} wins by more specific scope")
    if kind_cmp["reason"]:
        explanation.append(f"{kind_cmp['winner_id']} wins by stronger kind")
    if priority_cmp["reason"]:
        explanation.append(f"{priority_cmp['winner_id']} wins by higher priority")
    if not explanation:
        explanation.append("No decisive precedence axis; documents should be combined carefully.")

    return {
        "winner_id": winner_id,
        "loser_id": loser_id,
        "reasons": reasons,
        "explanation": "; ".join(explanation),
        "dimensions": {
            "scope": {
                "a_scope": a.scope,
                "b_scope": b.scope,
                "relation": scope_cmp["relation"],
                "winner_id": scope_cmp["winner_id"],
            },
            "kind": {
                "a_kind": a.kind,
                "b_kind": b.kind,
                "winner_id": kind_cmp["winner_id"],
            },
            "priority": {
                "a_priority": a.priority,
                "b_priority": b.priority,
                "winner_id": priority_cmp["winner_id"],
            },
        },
    }


def _conflict_severity(
    overlap: dict[str, Any],
    precedence: dict[str, Any],
    a: InstructionRecord,
    b: InstructionRecord,
) -> tuple[bool, str, str]:
    shared_score = float(overlap["score"])
    relation = precedence["dimensions"]["scope"]["relation"]
    same_kind = (a.kind or "").lower() == (b.kind or "").lower()
    same_priority = (a.priority or "").lower() == (b.priority or "").lower()
    if shared_score < 1 and relation == "unknown":
        return False, "none", "insufficient_overlap"
    if relation in {"same", "a_broader_than_b", "b_broader_than_a"} and shared_score >= 1 and same_kind:
        if same_priority:
            return True, "medium", "same_scope_same_kind"
        return True, "medium", "same_scope_priority_split"
    if relation in {"same", "a_broader_than_b", "b_broader_than_a"} and shared_score >= 1 and precedence["winner_id"]:
        return True, "low", "scope_overlap_with_precedence"
    if shared_score >= 2:
        return True, "low", "shared_topic_overlap"
    return False, "none", "complementary"


def _agent_guidance(a: InstructionRecord, b: InstructionRecord, precedence: dict[str, Any]) -> str:
    winner_id = precedence.get("winner_id")
    if winner_id == a.id:
        other = b.id
    elif winner_id == b.id:
        other = a.id
    else:
        return "Combine both documents and escalate to local instructions if a concrete directive still feels ambiguous."
    return f"Use `{winner_id}` as the normative baseline and keep `{other}` only as supporting context where it does not contradict the winner."


def _normalize_requirement_level(raw: object) -> str:
    value = normalize_text(str(raw or "recommended"))
    return "required" if value == "required" else "recommended"


def load_checklists() -> dict[str, ChecklistScenario]:
    file_path = Path(__file__).with_name("checklists.yaml")
    if not file_path.exists():
        return {}
    loaded = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}
    out: dict[str, ChecklistScenario] = {}
    for scenario, raw_scenario in loaded.items():
        if not isinstance(scenario, str):
            continue
        key = scenario.strip().lower()
        if isinstance(raw_scenario, list):
            rows = raw_scenario
            title = scenario.replace("_", " ").strip()
            objective = ""
        elif isinstance(raw_scenario, dict):
            rows = raw_scenario.get("checklist", [])
            title = str(raw_scenario.get("title", scenario.replace("_", " "))).strip()
            objective = str(raw_scenario.get("objective", "")).strip()
        else:
            continue
        if not isinstance(rows, list):
            continue
        items: list[ChecklistScenarioItem] = []
        for idx_row, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            legacy_id = str(row.get("id", "")).strip()
            instruction_ids = row.get("instruction_ids")
            if isinstance(instruction_ids, list):
                support_ids = [str(item).strip() for item in instruction_ids if str(item).strip()]
            elif legacy_id:
                support_ids = [legacy_id]
            else:
                support_ids = []
            if not support_ids:
                continue
            key_value = str(row.get("key", legacy_id or f"item_{idx_row}")).strip()
            title_value = str(row.get("title", key_value.replace("_", " "))).strip()
            why = str(row.get("why", row.get("reason", "scenario reference"))).strip()
            verification_raw = row.get("verification", [])
            verification = (
                [str(item).strip() for item in verification_raw if str(item).strip()]
                if isinstance(verification_raw, list)
                else []
            )
            requirement_level = (
                _normalize_requirement_level(row.get("requirement_level"))
                if "requirement_level" in row
                else ("required" if bool(row.get("required", False)) else "recommended")
            )
            items.append(
                ChecklistScenarioItem(
                    key=key_value,
                    title=title_value,
                    requirement_level=requirement_level,
                    why=why,
                    instruction_ids=support_ids,
                    verification=verification,
                )
            )
        if items:
            out[key] = ChecklistScenario(key=key, title=title, objective=objective, checklist=items)
    return out


def build_normative_checklist(idx: dict[str, InstructionRecord], scenario: str) -> dict[str, Any]:
    checklists = load_checklists()
    key = scenario.strip().lower()
    configured = checklists.get(key)
    if not configured:
        return {
            "scenario": scenario,
            "available_scenarios": sorted(checklists),
            "items": [],
            "missing_instruction_ids": [],
            "note": "No checklist configured for this scenario.",
        }

    items_out: list[dict[str, Any]] = []
    missing_instruction_ids: list[str] = []
    support_index: dict[str, dict[str, Any]] = {}
    required_total = 0
    required_covered = 0
    recommended_total = 0

    for item in configured.checklist:
        found_ids = [instruction_id for instruction_id in item.instruction_ids if instruction_id in idx]
        missing_ids = [instruction_id for instruction_id in item.instruction_ids if instruction_id not in idx]
        evidence = [_brief(idx[instruction_id]) for instruction_id in found_ids]
        gap_status = "covered" if found_ids and not missing_ids else ("partial" if found_ids else "missing")
        if item.requirement_level == "required":
            required_total += 1
            if gap_status == "covered":
                required_covered += 1
        else:
            recommended_total += 1
        missing_instruction_ids.extend(missing_ids)
        for evidence_row in evidence:
            support_index[evidence_row["id"]] = evidence_row
        items_out.append(
            {
                "key": item.key,
                "title": item.title,
                "requirement_level": item.requirement_level,
                "why": item.why,
                "support_ids": item.instruction_ids,
                "evidence_ids": found_ids,
                "missing_support_ids": missing_ids,
                "gap_status": gap_status,
                "evidence": evidence,
                "verification": item.verification,
                "implementation_note": (
                    "Ready to implement from indexed support."
                    if gap_status == "covered"
                    else "Needs follow-up because support instructions are missing or partial."
                ),
            }
        )

    readiness = "ready" if required_total == required_covered else "partial"
    next_actions: list[str] = []
    for item in items_out:
        if item["gap_status"] != "covered":
            next_actions.append(f"Review `{item['key']}` because support ids are incomplete: {', '.join(item['missing_support_ids'])}.")
        elif item["requirement_level"] == "required":
            next_actions.append(f"Implement `{item['key']}` using support ids: {', '.join(item['evidence_ids'])}.")

    return {
        "scenario": scenario,
        "scenario_key": configured.key,
        "title": configured.title,
        "objective": configured.objective,
        "summary": {
            "total_items": len(items_out),
            "required_items": required_total,
            "recommended_items": recommended_total,
            "required_items_covered": required_covered,
            "missing_instruction_ids_count": len(missing_instruction_ids),
            "implementation_readiness": readiness,
        },
        "items": items_out,
        "support_index": support_index,
        "missing_instruction_ids": sorted(set(missing_instruction_ids)),
        "next_actions": next_actions,
        "available_scenarios": sorted(checklists),
    }


def build_resolved_context(
    *,
    query: str,
    max_results: int,
    search_payload: dict[str, Any],
    batch_payload: dict[str, Any],
) -> dict[str, Any]:
    search_results = [row for row in search_payload.get("results", []) if isinstance(row, dict)]
    if not search_results:
        return {
            "selected_ids": [],
            "selection": {"strategy": [], "pool_size": 0, "section_focus": None},
            "criteria": {
                "requested_max_results": max_results,
                "search_confidence": 0.0,
                "search_zero_results": True,
                "fallback_suggestions": search_payload.get("fallback_suggestions", []),
            },
            "evidence_bundle": [],
            "actionable_context": {
                "normative_ids": [],
                "supporting_ids": [],
                "implementation_brief": "No context candidates were selected.",
                "next_actions": ["Refine the query or use metadata filters before batching full documents."],
                "gaps": ["Search returned no results."],
            },
        }

    diagnostics = search_payload.get("diagnostics", {})
    matched_terms = diagnostics.get("matched_user_terms") if isinstance(diagnostics, dict) else None
    confidence_value = diagnostics.get("search_confidence") if isinstance(diagnostics, dict) else None
    gap_value = diagnostics.get("top_score_gap_1_2") if isinstance(diagnostics, dict) else None
    low_confidence = bool(isinstance(confidence_value, (int, float)) and float(confidence_value) < 0.65)
    ambiguous_gap = bool(isinstance(gap_value, (int, float)) and float(gap_value) <= 1.5)
    target = min(len(search_results), max_results + 1) if (low_confidence or ambiguous_gap) else min(len(search_results), max_results)
    target = max(1, target)
    pool_size = min(len(search_results), max(max_results * 2, 6))
    pool = search_results[:pool_size]

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    strategy: list[str] = []

    def add(row: dict[str, Any], reason: str) -> None:
        row_id = str(row.get("id") or "")
        if not row_id or row_id in selected_ids:
            return
        selected.append(row)
        selected_ids.add(row_id)
        strategy.append(f"{row_id}:{reason}")

    add(pool[0], "top_relevance_anchor")

    policy_candidate = next(
        (
            row
            for row in pool
            if str(row.get("kind") or "").lower() == "policy"
            and row.get("id") not in selected_ids
            and (row.get("match_explanation", {}).get("matched_user_terms") or row.get("score", 0) > 0)
        ),
        None,
    )
    if policy_candidate:
        add(policy_candidate, "ensure_normative_policy")

    reference_candidate = next(
        (
            row
            for row in pool
            if str(row.get("kind") or "").lower() == "reference"
            and row.get("id") not in selected_ids
            and (
                (
                    len(row.get("match_explanation", {}).get("matched_user_terms") or []) >= 2
                    and _has_specific_reference_signal(row)
                )
                or pool[0].get("id") in (row.get("related_ids") or [])
                and len(row.get("match_explanation", {}).get("matched_expansion_only_terms") or []) >= 2
            )
        ),
        None,
    )
    if reference_candidate:
        add(reference_candidate, "ensure_supporting_reference")

    requested_themes = _query_themes(query)
    if len(requested_themes) >= 3:
        for theme in sorted(requested_themes):
            top5_strength = max((_row_theme_strength(row, theme) for row in selected[:5]), default=0)
            if top5_strength >= _THEME_MIN_STRENGTH:
                continue
            candidates = [
                row
                for row in pool
                if row.get("id") not in selected_ids and _row_theme_strength(row, theme) > 0
            ]
            if not candidates:
                continue
            candidates.sort(
                key=lambda row: (
                    -_row_theme_strength(row, theme),
                    -float(row.get("score", 0.0)),
                    str(row.get("id", "")),
                )
            )
            add(candidates[0], f"ensure_theme_diversity_{theme}")

    for row in pool:
        if len(selected) >= target:
            break
        matched = row.get("match_explanation", {}).get("matched_user_terms") or []
        if matched:
            add(row, "fill_direct_match")

    for row in pool:
        if len(selected) >= target:
            break
        add(row, "fill_ranked_candidate")

    term_counter: Counter[str] = Counter()
    for row in selected:
        matched = row.get("match_explanation", {}).get("matched_user_terms") or []
        for term in matched:
            if isinstance(term, str) and len(term) >= 4:
                term_counter[term] += 1
    section_focus = None
    quoted = _quoted_phrases(query)
    if quoted:
        section_focus = quoted[0]
    elif term_counter:
        section_focus = sorted(term_counter.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))[0][0]
    elif isinstance(matched_terms, list) and matched_terms:
        section_focus = str(matched_terms[0])

    batch_map = {
        str(item.get("id")): item
        for item in batch_payload.get("instructions", [])
        if isinstance(item, dict) and item.get("id")
    }
    evidence_bundle: list[dict[str, Any]] = []
    normative_ids: list[str] = []
    supporting_ids: list[str] = []
    workspace_gap_ids: list[str] = []
    for row in selected:
        row_id = str(row.get("id"))
        batch_item = batch_map.get(row_id, {})
        frontmatter = batch_item.get("frontmatter", {}) if isinstance(batch_item, dict) else {}
        if str(row.get("kind") or "").lower() == "policy":
            normative_ids.append(row_id)
        else:
            supporting_ids.append(row_id)
        if isinstance(frontmatter, dict) and frontmatter.get("workspace_evidence_required"):
            workspace_gap_ids.append(row_id)
        evidence_bundle.append(
            {
                "id": row_id,
                "title": row.get("source_title", row.get("title")),
                "kind": row.get("kind"),
                "priority": batch_item.get("priority") or row.get("priority"),
                "relevance": row.get("relevance"),
                "score": row.get("score"),
                "selection_reason": next(
                    (entry.split(":", 1)[1] for entry in strategy if entry.startswith(f"{row_id}:")),
                    "selected",
                ),
                "summary": row.get("summary"),
                "key_excerpt": row.get("key_excerpt"),
                "matched_user_terms": row.get("match_explanation", {}).get("matched_user_terms", []),
                "matched_expansion_only_terms": row.get("match_explanation", {}).get("matched_expansion_only_terms", []),
                "related_ids": row.get("related_ids", []),
                "workspace_evidence_required": bool(frontmatter.get("workspace_evidence_required"))
                if isinstance(frontmatter, dict)
                else False,
                "workspace_signals": frontmatter.get("workspace_signals", []) if isinstance(frontmatter, dict) else [],
                "section_match_count": batch_item.get("section_match_count"),
                "included_headings": batch_item.get("included_headings", []),
                "content_excerpt": summarize_body(str(batch_item.get("content", "")), 260),
            }
        )

    requires_applicability_gate = bool(normative_ids)
    next_actions: list[str] = []
    if requires_applicability_gate:
        next_actions.append(
            "Run `validate_applicability` for selected normative ids before asserting or applying any policy."
        )
    next_actions.extend(
        f"After applicability is reconciled, apply `{instruction_id}` as normative baseline."
        for instruction_id in normative_ids
    )
    next_actions.extend(
        f"Use `{instruction_id}` as supporting reference after normative applicability is confirmed."
        for instruction_id in supporting_ids
    )
    if section_focus:
        next_actions.append(f"Inspect the batched sections focused on `{section_focus}` first.")
    if low_confidence or ambiguous_gap:
        next_actions.append("Review fallback suggestions because the search confidence is not fully decisive.")

    gaps: list[str] = []
    if low_confidence:
        gaps.append("Search confidence is low; a narrower query or metadata filter may improve precision.")
    if ambiguous_gap:
        gaps.append("Top ranked results are close to each other; treat the selected set as a bundle, not a single winner.")
    if workspace_gap_ids:
        gaps.append(
            "Some selected policies require workspace evidence before being asserted strongly: "
            + ", ".join(sorted(workspace_gap_ids))
            + "."
        )

    implementation_brief = (
        "Normative baseline: "
        + (", ".join(f"`{instruction_id}`" for instruction_id in normative_ids) or "none")
        + ". Supporting references: "
        + (", ".join(f"`{instruction_id}`" for instruction_id in supporting_ids) or "none")
        + ". Applicability gate required: "
        + ("yes." if requires_applicability_gate else "no.")
    )

    selection_rationale = [
        {
            "instruction_id": str(row.get("id")),
            "why_selected": next(
                (entry.split(":", 1)[1] for entry in strategy if entry.startswith(f"{str(row.get('id'))}:")),
                "ranked_candidate",
            ),
        }
        for row in selected
        if row.get("id")
    ]

    required_workspace_signals: dict[str, list[str]] = {}
    pending_evidence: list[dict[str, str]] = []
    next_repo_evidence_actions: list[str] = []
    seen_actions: set[str] = set()
    for bundle_item in evidence_bundle:
        instruction_id = str(bundle_item.get("id", "")).strip()
        if not instruction_id:
            continue
        signals = [str(signal).strip() for signal in (bundle_item.get("workspace_signals") or []) if str(signal).strip()]
        if not signals:
            continue
        required_workspace_signals[instruction_id] = signals
        if bool(bundle_item.get("workspace_evidence_required")):
            pending_evidence.append(
                {
                    "instruction_id": instruction_id,
                    "reason": "Instruction requires workspace evidence before strong enforcement.",
                }
            )
        for signal in signals[:5]:
            action = f"search for {signal}"
            if action not in seen_actions:
                seen_actions.add(action)
                next_repo_evidence_actions.append(action)

    return {
        "selected_ids": [str(row.get("id")) for row in selected],
        "selection": {
            "pool_size": pool_size,
            "target_count": target,
            "strategy": strategy,
            "section_focus": section_focus,
        },
        "criteria": {
            "requested_max_results": max_results,
            "search_confidence": (diagnostics or {}).get("search_confidence") if isinstance(diagnostics, dict) else None,
            "top_score_gap_1_2": (diagnostics or {}).get("top_score_gap_1_2") if isinstance(diagnostics, dict) else None,
            "matched_user_terms": matched_terms if isinstance(matched_terms, list) else [],
            "matched_expansion_only_terms": (
                diagnostics.get("matched_expansion_only_terms", []) if isinstance(diagnostics, dict) else []
            ),
            "results_only_from_expansion_count": (
                diagnostics.get("results_only_from_expansion_count", 0) if isinstance(diagnostics, dict) else 0
            ),
            "fallback_suggestions": search_payload.get("fallback_suggestions", []),
            "low_confidence": low_confidence,
            "ambiguous_top_scores": ambiguous_gap,
        },
        "evidence_bundle": evidence_bundle,
        "selection_rationale": selection_rationale,
        "pending_evidence": pending_evidence,
        "required_workspace_signals": required_workspace_signals,
        "next_repo_evidence_actions": next_repo_evidence_actions,
        "actionable_context": {
            "normative_ids": normative_ids,
            "supporting_ids": supporting_ids,
            "requires_applicability_gate": requires_applicability_gate,
            "implementation_brief": implementation_brief,
            "next_actions": next_actions,
            "gaps": gaps,
        },
    }


def resolve_conflicts(idx: dict[str, InstructionRecord], ids: list[str]) -> dict[str, Any]:
    seen: set[str] = set()
    ordered_ids: list[str] = []
    for candidate in ids:
        norm = candidate.strip()
        if norm and norm not in seen:
            seen.add(norm)
            ordered_ids.append(norm)

    docs = [idx[instruction_id] for instruction_id in ordered_ids if instruction_id in idx]
    missing_ids = [instruction_id for instruction_id in ordered_ids if instruction_id not in idx]
    relationships: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            a = docs[i]
            b = docs[j]
            overlap = _topic_overlap(a, b)
            precedence = _precedence(a, b)
            has_conflict, severity, reason = _conflict_severity(overlap, precedence, a, b)
            relationship = {
                "ids": [a.id, b.id],
                "potential_conflict": has_conflict,
                "severity": severity,
                "relationship_reason": reason,
                "shared_tags": overlap["shared_tags"],
                "shared_title_terms": overlap["shared_title_terms"],
                "topic_overlap_score": round(float(overlap["score"]), 4),
                "precedence": precedence,
                "agent_guidance": _agent_guidance(a, b, precedence),
                "documents": {
                    a.id: _brief(a),
                    b.id: _brief(b),
                },
            }
            relationships.append(relationship)
            if has_conflict:
                conflicts.append(relationship)

    return {
        "input_ids": ordered_ids,
        "checked_ids": [d.id for d in docs],
        "missing_ids": missing_ids,
        "summary": {
            "checked_count": len(docs),
            "missing_count": len(missing_ids),
            "relationships_count": len(relationships),
            "potential_conflicts_count": len(conflicts),
        },
        "precedence_rules": [
            "More specific scope wins when two instructions overlap.",
            "If scope does not decide, stronger kind wins (`policy` over `reference`).",
            "If scope and kind still tie, higher priority wins.",
        ],
        "relationships": relationships,
        "conflicts": conflicts,
    }

