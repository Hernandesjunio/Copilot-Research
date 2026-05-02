"""Response helpers for MCP tool contracts."""

from __future__ import annotations

from typing import Any


def build_error(
    *,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    suggested_next_call: dict[str, Any] | None = None,
    include_legacy_error_field: bool = True,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": False,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "suggested_next_call": suggested_next_call or {},
    }
    if include_legacy_error_field:
        out["error"] = message
    return out


def search_confidence(top_score_gap_1_2: float | None, top_relevance: float | None, result_count: int) -> float:
    if result_count <= 0:
        return 0.0
    relevance = 0.0 if top_relevance is None else max(0.0, min(1.0, top_relevance))
    gap_component = 0.0 if top_score_gap_1_2 is None else max(0.0, min(1.0, top_score_gap_1_2 / 5.0))
    return round((0.7 * relevance) + (0.3 * gap_component), 4)


def build_fallback_suggestions(
    *,
    zero_results: bool,
    low_confidence: bool,
    ambiguous_gap: bool,
    expansion_only_results: int,
    has_tags_filter: bool,
    max_results: int,
) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    if zero_results:
        suggestions.append(
            {
                "reason": "zero_results",
                "tool": "search_instructions",
                "args_patch": {"max_results": min(max_results + 5, 50), "include_diagnostics": True},
            }
        )
        if not has_tags_filter:
            suggestions.append(
                {
                    "reason": "zero_results_try_tags",
                    "tool": "search_instructions",
                    "args_patch": {"tags": "mensageria,resiliencia,security,api", "tags_mode": "any"},
                }
            )
    if low_confidence:
        suggestions.append(
            {
                "reason": "low_confidence_top_result",
                "tool": "search_instructions",
                "args_patch": {"max_results": min(max_results + 5, 50), "include_diagnostics": True},
            }
        )
        if not has_tags_filter:
            suggestions.append(
                {
                    "reason": "narrow_by_metadata",
                    "tool": "search_instructions",
                    "args_patch": {"tags": "security,api", "tags_mode": "any"},
                }
            )
        suggestions.append(
            {
                "reason": "fetch_top_ids_for_disambiguation",
                "tool": "get_instructions_batch",
                "args_patch": {"ids": "<top_result_ids>"},
            }
        )
    if ambiguous_gap:
        suggestions.append(
            {
                "reason": "ambiguous_top_scores",
                "tool": "get_instructions_batch",
                "args_patch": {"ids": "<top_3_result_ids>", "section_contains": "<query_terms>"},
            }
        )
    if expansion_only_results > 0:
        suggestions.append(
            {
                "reason": "results_dominated_by_synonym_expansion",
                "tool": "search_instructions",
                "args_patch": {"include_diagnostics": True, "tags_mode": "all"},
            }
        )
    return suggestions

