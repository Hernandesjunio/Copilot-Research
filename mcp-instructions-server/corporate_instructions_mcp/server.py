"""MCP stdio server exposing read-only tools over the instruction corpus."""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from corporate_instructions_mcp import telemetry
from corporate_instructions_mcp.indexing import (
    PRIORITY_RANK,
    InstructionRecord,
    build_index,
    excerpt_around_match,
    expand_query_with_metadata,
    score_record,
    score_record_breakdown,
    summarize_body,
    terms_with_positive_hits,
    tokenize_query,
)
from corporate_instructions_mcp.paths import require_existing_dir

mcp = FastMCP(
    "corporate-instructions",
    instructions=(
        "Read-only catalog of organizational Copilot instructions. "
        "Native repo instructions override this catalog when they conflict."
    ),
)

_index: dict[str, InstructionRecord] = {}
_index_root: Path | None = None
MAX_BATCH_TOTAL_CHARS = 120_000

# Documented absence: requires IDE/model-side instrumentation (see research methodology).
_SERVER_UNOBSERVABLE_METRICS = [
    "decisions_blocked_by_missing_evidence_count",
    "blocked_decision_types",
    "negative_evidence_search_count",
    "stage_plan_duration_ms",
    "stage_discovery_duration_ms",
    "stage_implementation_duration_ms",
    "stage_validation_duration_ms",
    "time_to_first_grounded_decision_ms",
    "instruction_utilization_rate",
    "calls_with_result_consumed",
    "precision_at_k_manual_label_source",
]

log = logging.getLogger(__name__)


def _json_safe_frontmatter(meta: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of frontmatter suitable for json.dumps (YAML may load dates, decimals, etc.)."""

    def _convert(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_convert(v) for v in value]
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, datetime.date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    return cast(dict[str, Any], _convert(meta))


def _configure_logging() -> None:
    """Emit operational messages to stderr so stdio JSON-RPC on stdout stays clean."""
    pkg = logging.getLogger("corporate_instructions_mcp")
    if pkg.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    pkg.addHandler(handler)
    pkg.setLevel(logging.INFO)


def _root() -> Path:
    raw = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if not raw:
        msg = "INSTRUCTIONS_ROOT is not set. Point it to the canonical folder of .md instructions."
        raise RuntimeError(msg)
    try:
        root = require_existing_dir(raw)
    except ValueError as exc:
        msg = str(exc)
        raise RuntimeError(msg) from exc
    return root


def _workspace_evidence_required(meta: dict[str, Any]) -> bool:
    v = meta.get("workspace_evidence_required")
    if v is True:
        return True
    if isinstance(v, str) and v.strip().lower() in ("true", "1", "yes"):
        return True
    return False


def _ensure_index() -> tuple[dict[str, InstructionRecord], dict[str, Any]]:
    """Load corpus; second return value describes whether this call rebuilt the in-memory index."""
    global _index, _index_root
    root = _root()
    call_meta: dict[str, Any] = {
        "index_build_triggered": False,
        "index_build_duration_ms": 0,
        "cold_start": False,
    }
    if _index_root != root or not _index:
        log.info("rebuilding_index root=%s", root)
        rebuild_start = time.perf_counter()
        _index = build_index(root)
        rebuild_ms = int((time.perf_counter() - rebuild_start) * 1000)
        _index_root = root
        size_b = sum(len(r.body.encode("utf-8", errors="replace")) for r in _index.values())
        gov = sum(1 for r in _index.values() if _workspace_evidence_required(r.raw_frontmatter))
        telemetry.set_corpus_governance_snapshot(gov, len(_index))
        telemetry.emit_index_rebuilt(
            root,
            len(_index),
            rebuild_ms,
            index_size_estimate_bytes=size_b,
            policies_workspace_evidence_required_count=gov,
        )
        call_meta["index_build_triggered"] = True
        call_meta["index_build_duration_ms"] = rebuild_ms
        call_meta["cold_start"] = telemetry.index_rebuild_count() == 1
    return _index, call_meta


def _parse_tags(tags: str | None) -> set[str] | None:
    if not tags or not str(tags).strip():
        return None
    return {t.strip().lower() for t in str(tags).split(",") if t.strip()}


def _clamp_int(value: object, default: int, lo: int, hi: int) -> int:
    """Coerce MCP tool arguments to int; fall back to default on invalid input."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        n = value
    elif isinstance(value, float):
        n = int(value)
    else:
        try:
            n = int(str(value).strip(), 10)
        except (TypeError, ValueError):
            return default
    return max(lo, min(n, hi))


def _emit_tool_completed(
    event: str,
    duration_ms: int,
    *,
    failure: bool,
    args_key_payload: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    if telemetry.telemetry_level() == "off":
        return
    tool_name = event.split(".", 1)[0] if "." in event else event
    sess = telemetry.register_tool_completion(
        tool_name,
        duration_ms,
        failure=failure,
        args_key=telemetry.args_fingerprint(args_key_payload),
    )
    telemetry.emit_event(event, {**sess, **payload})


def _shrink_search_telemetry(full: dict[str, Any]) -> dict[str, Any]:
    if telemetry.telemetry_level() == "full":
        return full
    out = dict(full)
    out.pop("query_original", None)
    out.pop("query_tokens", None)
    out.pop("expanded_terms", None)
    br = out.get("score_breakdown_top_results")
    if isinstance(br, list) and len(br) > 3:
        out["score_breakdown_top_results"] = br[:3]
    out["telemetry_detail"] = "minimal"
    return out


def _related_instruction_ids(
    rec: InstructionRecord,
    idx: dict[str, InstructionRecord],
    max_related: int = 10,
) -> list[str]:
    tags = set(rec.tags)
    if not tags:
        return []
    related: list[tuple[int, str, str]] = []
    for candidate in idx.values():
        if candidate.id == rec.id:
            continue
        overlap = len(tags & set(candidate.tags))
        if overlap <= 0:
            continue
        related.append((overlap, candidate.id, candidate.rel_path))
    related.sort(key=lambda item: (-item[0], item[2], item[1]))
    return [candidate_id for _, candidate_id, _ in related[:max_related]]


@mcp.tool()
def list_instructions_index() -> str:
    """Use when you need an overview of all available organizational instruction documents (ids, titles, tags).

    Returns lightweight metadata for every indexed .md file under INSTRUCTIONS_ROOT. Restart the server or
    set INSTRUCTIONS_ROOT to a new path to refresh. JSON array of objects.
    """
    call_start = time.perf_counter()
    idx, index_meta = _ensure_index()
    out = []
    by_tag: dict[str, list[str]] = {}
    kind_counts: dict[str, int] = {}
    for rec in sorted(idx.values(), key=lambda r: r.rel_path):
        out.append(
            {
                "id": rec.id,
                "path": rec.rel_path,
                "title": rec.title,
                "tags": rec.tags,
                "scope": rec.scope,
                "priority": rec.priority,
                "kind": rec.kind,
                "content_sha256": rec.content_hash,
            }
        )
        k = rec.kind or "unknown"
        kind_counts[k] = kind_counts.get(k, 0) + 1
        for tag in rec.tags:
            by_tag.setdefault(tag, []).append(rec.id)
    by_tag = {tag: sorted(ids) for tag, ids in sorted(by_tag.items())}
    raw = json.dumps({"instructions": out, "count": len(out), "by_tag": by_tag}, ensure_ascii=False)
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    payload = {
        "unique_instruction_ids_count": len(out),
        "instructions_consulted_count": len(out),
        "instructions_by_kind": kind_counts,
        "instructions_by_tag": {t: len(ids) for t, ids in by_tag.items()},
        "by_tag_count": len(by_tag),
        "response_chars": len(raw),
        "response_bytes": len(raw.encode("utf-8", errors="replace")),
        "calls_with_non_empty_result": 1 if out else 0,
        "empty_result_rate": 0.0 if out else 1.0,
        **index_meta,
        "metrics_not_measurable_server_side": _SERVER_UNOBSERVABLE_METRICS,
    }
    _emit_tool_completed(
        "list_instructions_index.completed",
        duration_ms,
        failure=False,
        args_key_payload={},
        payload=payload,
    )
    return raw


@mcp.tool()
def search_instructions(
    query: str,
    tags: str | None = None,
    max_results: int = 10,
    telemetry_expected_instruction_id: str | None = None,
) -> str:
    """Use when the user asks about architecture, patterns, DNS, security, style, or any org-specific guideline.

    Full-text style search (keyword overlap) over the instruction corpus. Prefer calling this before
    proposing cross-cutting design. Parameters: query (natural language), optional comma-separated tags
    filter, max_results (default 10, cap 20). Optional telemetry_expected_instruction_id for offline
    ranking evaluation (expected instruction id).
    """
    call_start = time.perf_counter()
    args_summary = telemetry.search_args_summary(query, tags, max_results)
    idx, index_meta = _ensure_index()
    tokens = tokenize_query(query)
    tag_filter = _parse_tags(tags)
    cap = _clamp_int(max_results, default=10, lo=1, hi=20)
    expanded_info = expand_query_with_metadata(tokens) if tokens else None

    def _finish(
        *,
        failure: bool,
        payload: dict[str, Any],
        search_mode: str,
        ranked_full: list[tuple[float, InstructionRecord]],
        results: list[dict[str, Any]],
        expanded_for_telemetry: dict[str, Any] | None,
    ) -> str:
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        composed = payload.get("composed_context", "") or ""
        out_raw = json.dumps(payload, ensure_ascii=False)
        result_count = len(results)
        zero_rate = 1.0 if result_count == 0 else 0.0
        if result_count > 0:
            t_first = telemetry.commit_first_relevant_search_if_needed()
        else:
            t_first = {}

        top_scores = [float(r.get("score", 0.0)) for r in results[:5]]
        top_rel = [float(r.get("relevance", 0.0)) for r in results[:5] if r.get("relevance") is not None]
        top1 = top_scores[0] if top_scores else None
        top2 = top_scores[1] if len(top_scores) > 1 else None
        gap_1_2 = (top1 - top2) if top1 is not None and top2 is not None else None

        low_conf = bool(top_rel and top_rel[0] < 0.2)

        eval_extra: dict[str, Any] = {}
        exp_id = (telemetry_expected_instruction_id or "").strip()
        if exp_id and ranked_full:
            pos = next((i + 1 for i, (_, r) in enumerate(ranked_full) if r.id == exp_id), None)
            eval_extra["expected_instruction_rank"] = pos
            eval_extra["mrr"] = round(1.0 / pos, 6) if pos else 0.0
            eval_extra["precision_at_1"] = 1 if pos == 1 else 0
            eval_extra["precision_at_3"] = 1 if pos is not None and pos <= 3 else 0
            eval_extra["precision_at_5"] = 1 if pos is not None and pos <= 5 else 0

        instr_by_kind: dict[str, int] = {}
        instr_by_tag: dict[str, int] = {}
        gov_in_results = 0
        for r in results:
            kd = (r.get("kind") or "unknown") if isinstance(r.get("kind"), str) else "unknown"
            instr_by_kind[kd] = instr_by_kind.get(kd, 0) + 1
            for tg in r.get("tags") or []:
                if isinstance(tg, str):
                    instr_by_tag[tg] = instr_by_tag.get(tg, 0) + 1
            rid = r.get("id")
            if isinstance(rid, str) and rid in idx and _workspace_evidence_required(idx[rid].raw_frontmatter):
                gov_in_results += 1

        breakdown_rows: list[dict[str, Any]] = []
        only_expansion = 0
        results_only_expansion_no_user_match = 0
        if expanded_for_telemetry and tokens:
            ei = expanded_for_telemetry.get("expanded_info_ref")
            if ei is not None:
                for row in results[: min(10, len(results))]:
                    rid = row.get("id")
                    rec = idx.get(str(rid)) if rid else None
                    if not rec:
                        continue
                    bd = score_record_breakdown(rec, tokens, tag_filter, ei)
                    mu, md = terms_with_positive_hits(rec, ei, tag_filter)
                    breakdown_rows.append(
                        {
                            "id": rec.id,
                            "score_total": round(bd.total, 4),
                            "score_title": round(bd.score_title, 4),
                            "score_tags": round(bd.score_tags, 4),
                            "score_body": round(bd.score_body_blob, 4),
                            "score_priority": round(bd.score_priority, 4),
                            "score_synonym_bonus": round(bd.score_from_expansion_terms, 4),
                            "matched_user_terms": sorted(mu),
                            "matched_expansion_only_terms": sorted(md),
                        }
                    )
                    if bd.total > 0 and bd.score_from_user_terms < 1e-9 and bd.score_from_expansion_terms > 1e-9:
                        only_expansion += 1
                    if not mu and md and bd.score_title + bd.score_body_blob + bd.score_tags > 1e-9:
                        results_only_expansion_no_user_match += 1

        top1_hit = breakdown_rows[0] if breakdown_rows else None
        top1_mu = len(top1_hit["matched_user_terms"]) if top1_hit else 0
        top1_me = len(top1_hit["matched_expansion_only_terms"]) if top1_hit else 0

        base_payload: dict[str, Any] = {
            "args_summary": args_summary,
            "top_result_id": str(results[0]["id"]) if results else None,
            "search_mode": search_mode,
            "search_results_count": result_count,
            "results_returned": result_count,
            "search_with_zero_results_rate": zero_rate,
            "search_zero_results": result_count == 0,
            "search_with_low_confidence_rate": 1.0 if low_conf else 0.0,
            "top1_score": top1,
            "top3_scores": top_scores[:3],
            "top_score_gap_1_2": gap_1_2,
            "topN_score_distribution": top_scores,
            "candidate_count_before_ranking": len(idx),
            "candidate_count_after_filtering": len(ranked_full),
            "top_k_returned": min(cap, len(ranked_full)),
            "composed_context_chars": len(composed),
            "response_chars": len(out_raw),
            "response_bytes": len(out_raw.encode("utf-8", errors="replace")),
            "unique_instruction_ids_count": len({str(r.get("id")) for r in results if r.get("id")}),
            "instructions_consulted_count": result_count,
            "instructions_by_kind": instr_by_kind,
            "instructions_by_tag": instr_by_tag,
            "policies_with_workspace_evidence_required_in_results_count": gov_in_results,
            "score_breakdown_top_results": breakdown_rows,
            "results_only_from_expansion_count": only_expansion,
            "results_only_from_expansion_no_user_term_overlap_count": results_only_expansion_no_user_match,
            "top_result_matched_original_terms_count": top1_mu,
            "top_result_matched_expanded_terms_count": top1_me,
            **index_meta,
            **eval_extra,
            **t_first,
            "metrics_not_measurable_server_side": _SERVER_UNOBSERVABLE_METRICS,
        }

        if expanded_for_telemetry:
            base_payload.update(expanded_for_telemetry["fields"])

        args_key_payload = {
            "query_fp": args_summary.get("query_sha256"),
            "tags_filter_present": args_summary.get("tags_filter_present"),
            "max_results": cap,
            "eval_expected": bool(exp_id),
        }
        full_line = {**base_payload, "failure": failure}
        emitted = _shrink_search_telemetry(full_line)
        _emit_tool_completed(
            "search_instructions.completed",
            duration_ms,
            failure=failure,
            args_key_payload=args_key_payload,
            payload=emitted,
        )
        return out_raw

    if not tokens:
        if not tag_filter:
            return _finish(
                failure=False,
                search_mode="empty",
                ranked_full=[],
                results=[],
                expanded_for_telemetry=None,
                payload={
                    "results": [],
                    "composed_context": "",
                    "note": "Provide a non-empty query or use tags= to filter by comma-separated tags.",
                },
            )
        ranked = []
        for rec in idx.values():
            if not (tag_filter & set(rec.tags)):
                continue
            pr = float(PRIORITY_RANK.get(rec.priority, 0))
            ranked.append((pr, rec))
        ranked.sort(key=lambda x: (-x[0], x[1].rel_path))
    else:
        ranked = [(score_record(rec, tokens, tag_filter), rec) for rec in idx.values()]
        ranked = [(s, r) for s, r in ranked if s > 0.0]
        ranked.sort(key=lambda x: x[0], reverse=True)

    if not ranked:
        return _finish(
            failure=False,
            search_mode="tags_only" if not tokens else "token_search",
            ranked_full=[],
            results=[],
            expanded_for_telemetry=(
                {
                    "expanded_info_ref": expanded_info,
                    "fields": {
                        "query_original": query.strip(),
                        "query_tokens": tokens,
                        "query_token_count": len(tokens),
                        "expanded_terms_total": len(expanded_info.weights) if expanded_info else 0,
                        "expanded_terms": sorted(expanded_info.weights.keys()) if expanded_info else [],
                        "expanded_from_token": expanded_info.user_tokens if expanded_info else [],
                        "synonym_expansion_count": expanded_info.synonym_expansion_count if expanded_info else 0,
                        "expansion_truncated": expanded_info.expansion_truncated if expanded_info else False,
                        "terms_from_user": len(tokens),
                        "terms_added_by_dictionary": len(expanded_info.terms_added_by_dictionary) if expanded_info else 0,
                    },
                }
                if expanded_info
                else None
            ),
            payload={
                "results": [],
                "composed_context": "",
                "note": "No matches; refine query or use list_instructions_index.",
            },
        )

    results = []
    composed_parts: list[str] = []
    for score, rec in ranked[:cap]:
        excerpt = excerpt_around_match(rec.body, tokens) if tokens else summarize_body(rec.body, 400)
        results.append(
            {
                "source": rec.rel_path,
                "id": rec.id,
                "relevance": round(min(1.0, score / 10.0), 4),
                "score": round(score, 4),
                "summary": summarize_body(rec.body),
                "key_excerpt": excerpt,
                "full_available": True,
                "tags": rec.tags,
                "kind": rec.kind,
                "related_ids": _related_instruction_ids(rec, idx),
            }
        )
        composed_parts.append(f"### {rec.title} ({rec.id})\n{summarize_body(rec.body, 280)}")

    expanded_payload: dict[str, Any] | None = None
    if expanded_info:
        expanded_payload = {
            "expanded_info_ref": expanded_info,
            "fields": {
                "query_original": query.strip(),
                "query_tokens": tokens,
                "query_token_count": len(tokens),
                "expanded_terms_total": len(expanded_info.weights),
                "expanded_terms": sorted(expanded_info.weights.keys()),
                "expanded_from_token": expanded_info.user_tokens,
                "synonym_expansion_count": expanded_info.synonym_expansion_count,
                "expansion_truncated": expanded_info.expansion_truncated,
                "terms_from_user": len(tokens),
                "terms_added_by_dictionary": len(expanded_info.terms_added_by_dictionary),
            },
        }

    return _finish(
        failure=False,
        search_mode="tags_only" if not tokens else "token_search",
        ranked_full=ranked,
        results=results,
        expanded_for_telemetry=expanded_payload,
        payload={
            "results": results,
            "composed_context": "\n\n".join(composed_parts),
        },
    )


@mcp.tool()
def get_instructions_batch(
    ids: str,
    max_chars_per_instruction: int = 8000,
) -> str:
    """Fetch multiple instructions in one call. Parameter ids: comma-separated instruction ids.

    Call after list_instructions_index or search_instructions when full bodies are needed.
    Each returned item includes a frontmatter object (parsed YAML header, JSON-safe).
    """
    call_start = time.perf_counter()
    args_summary = telemetry.get_batch_args_summary(ids, max_chars_per_instruction)
    idx, index_meta = _ensure_index()
    requested_ids = [candidate.strip() for candidate in str(ids).split(",") if candidate.strip()]
    if not requested_ids:
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        raw = json.dumps({"error": "Provide at least one instruction id."}, ensure_ascii=False)
        _emit_tool_completed(
            "get_instructions_batch.completed",
            duration_ms,
            failure=True,
            args_key_payload=dict(args_summary),
            payload={
                "requested_ids_count": 0,
                "returned_ids_count": 0,
                "missing_ids_count": 0,
                "truncated_items_count": 0,
                "batch_chars_total": len(raw),
                "error": "no_ids",
                **index_meta,
                "metrics_not_measurable_server_side": _SERVER_UNOBSERVABLE_METRICS,
            },
        )
        return raw

    per_instruction_limit = _clamp_int(max_chars_per_instruction, default=8000, lo=500, hi=200_000)
    total_remaining = MAX_BATCH_TOTAL_CHARS
    items: list[dict[str, object]] = []
    missing_ids: list[str] = []
    skipped_ids_due_to_total_cap: list[str] = []

    for requested_id in requested_ids:
        rec = idx.get(requested_id)
        if rec is None:
            missing_ids.append(requested_id)
            continue
        if total_remaining <= 0:
            skipped_ids_due_to_total_cap.append(requested_id)
            continue

        effective_limit = min(per_instruction_limit, total_remaining)
        body = rec.body
        truncated = len(body) > effective_limit
        if truncated:
            body = body[: max(0, effective_limit - 20)] + "\n\n… [truncated]"
        total_remaining -= len(body)
        items.append(
            {
                "id": rec.id,
                "path": rec.rel_path,
                "title": rec.title,
                "tags": rec.tags,
                "scope": rec.scope,
                "priority": rec.priority,
                "kind": rec.kind,
                "content_sha256": rec.content_hash,
                "truncated": truncated,
                "content": body,
                "frontmatter": _json_safe_frontmatter(rec.raw_frontmatter),
            }
        )

    approx_chars = sum(len(str(item.get("content", ""))) for item in items)
    truncated_items = sum(1 for item in items if item.get("truncated") is True)
    returned_ids = [str(it.get("id")) for it in items if it.get("id")]
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    out_obj = {
        "instructions": items,
        "requested_count": len(requested_ids),
        "found_count": len(items),
        "missing_ids": missing_ids,
        "skipped_ids_due_to_total_cap": skipped_ids_due_to_total_cap,
        "max_chars_per_instruction": per_instruction_limit,
        "max_total_chars": MAX_BATCH_TOTAL_CHARS,
    }
    raw = json.dumps(out_obj, ensure_ascii=False)
    gov_batch = sum(1 for it in items if _workspace_evidence_required(cast(dict[str, Any], it.get("frontmatter") or {})))
    kind_b: dict[str, int] = {}
    for it in items:
        kd = it.get("kind") or "unknown"
        if isinstance(kd, str):
            kind_b[kd] = kind_b.get(kd, 0) + 1
    avg_chars = approx_chars / max(1, len(items))
    _emit_tool_completed(
        "get_instructions_batch.completed",
        duration_ms,
        failure=False,
        args_key_payload=dict(args_summary),
        payload={
            "requested_ids_count": len(requested_ids),
            "returned_ids_count": len(items),
            "missing_ids_count": len(missing_ids),
            "skipped_due_to_total_cap_count": len(skipped_ids_due_to_total_cap),
            "truncated_items_count": truncated_items,
            "batch_chars_total": approx_chars,
            "batch_total_chars": approx_chars,
            "avg_chars_per_instruction": round(avg_chars, 2),
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
            "instructions_retrieved_count": len(items),
            "unique_instruction_ids_count": len(set(returned_ids)),
            "instructions_by_kind": kind_b,
            "policies_with_workspace_evidence_required_in_batch_count": gov_batch,
            "calls_with_non_empty_result": 1 if items else 0,
            "empty_result_rate": 0.0 if items else 1.0,
            **index_meta,
            "metrics_not_measurable_server_side": _SERVER_UNOBSERVABLE_METRICS,
        },
    )

    return raw


def main() -> None:
    _configure_logging()
    telemetry.emit_server_start(os.environ.get("INSTRUCTIONS_ROOT", ""))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
