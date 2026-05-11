"""MCP stdio server exposing read-only tools over the instruction corpus."""

from __future__ import annotations

import datetime
from collections import Counter
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
from corporate_instructions_mcp.applicability import (
    APPLICABILITY_STATES,
    build_compliance_row,
    decide_applicability,
    match_scope,
    normalize_path,
    parse_workspace_evidence,
)
from corporate_instructions_mcp.config import RuntimeConfig, load_runtime_config
from corporate_instructions_mcp.expansion import ExpansionMap, load_corpus_expansion_map
from corporate_instructions_mcp.context_resolver import (
    build_normative_checklist,
    build_resolved_context,
    resolve_conflicts,
)
from corporate_instructions_mcp.context_triggers import ContractError, SUPPORTED_SCHEMA_VERSION, build_context_triggers
from corporate_instructions_mcp.indexing import (
    PRIORITY_RANK,
    CorpusSignature,
    InstructionRecord,
    build_index,
    corpus_signature,
    excerpt_around_match,
    expand_query_with_metadata,
    extract_exact_phrases,
    get_index_warnings,
    normalize_text,
    score_record,
    score_record_breakdown,
    summarize_body,
    terms_with_positive_hits,
    tokenize_query,
)
from corporate_instructions_mcp.markdown_sections import (
    compose_section_payload,
    filter_sections,
    split_markdown_sections,
)
from corporate_instructions_mcp.paths import require_existing_dir
from corporate_instructions_mcp.search_contract import build_error, build_fallback_suggestions, search_confidence

mcp = FastMCP(
    "corporate-instructions",
    instructions=(
        "Read-only catalog of organizational Copilot instructions. "
        "Native repo instructions override this catalog when they conflict."
    ),
)

_index: dict[str, InstructionRecord] = {}
_index_root: Path | None = None
_index_signature: CorpusSignature | None = None
_last_signature_check_mono = 0.0
_config: RuntimeConfig | None = None
_index_warnings: list[dict[str, Any]] = []
_index_loaded_at_utc: str | None = None
_expansion_map: ExpansionMap | None = None

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
_LIST_FACET_TOP_N = 50
_KIND_SORT_ORDER = {"policy": 0, "reference": 1}


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


def _cfg() -> RuntimeConfig:
    global _config
    if _config is None:
        _config = load_runtime_config()
    return _config


def _workspace_evidence_required(meta: dict[str, Any]) -> bool:
    v = meta.get("workspace_evidence_required")
    if v is True:
        return True
    if isinstance(v, str) and v.strip().lower() in ("true", "1", "yes"):
        return True
    return False


def _ensure_index() -> tuple[dict[str, InstructionRecord], dict[str, Any], ExpansionMap]:
    """Load corpus; second return value describes whether this call rebuilt the in-memory index."""
    global _index, _index_root, _index_signature, _last_signature_check_mono, _index_warnings, _index_loaded_at_utc
    global _expansion_map
    root = _root()
    cfg = _cfg()
    call_meta: dict[str, Any] = {
        "index_build_triggered": False,
        "index_build_duration_ms": 0,
        "cold_start": False,
    }
    rebuild = _index_root != root or not _index
    now = time.perf_counter()
    if (
        not rebuild
        and cfg.index_staleness_check_seconds > 0
        and (now - _last_signature_check_mono) >= cfg.index_staleness_check_seconds
    ):
        _last_signature_check_mono = now
        latest_signature = corpus_signature(root)
        if _index_signature is None or latest_signature.signature != _index_signature.signature:
            rebuild = True
            call_meta["index_stale_detected"] = True

    if rebuild:
        log.info("rebuilding_index root=%s", root)
        rebuild_start = time.perf_counter()
        _index = build_index(root)
        _index_warnings = get_index_warnings()
        _index_signature = corpus_signature(root)
        rebuild_ms = int((time.perf_counter() - rebuild_start) * 1000)
        _index_root = root
        _index_loaded_at_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _expansion_map = load_corpus_expansion_map(root)
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
    call_meta["corpus_version"] = _index_signature.signature if _index_signature else ""
    call_meta["corpus_file_count"] = _index_signature.file_count if _index_signature else 0
    if _expansion_map is None:
        _expansion_map = load_corpus_expansion_map(root)
    return _index, call_meta, _expansion_map


def _parse_tags(tags: str | None) -> set[str] | None:
    if not tags or not str(tags).strip():
        return None
    return {t.strip().lower() for t in str(tags).split(",") if t.strip()}


def _parse_bool(value: object | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


def _normalize_current_file_path_input(value: str | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, "not_provided"
    raw = value.strip()
    if not raw:
        return None, "empty"
    normalized = normalize_path(raw)
    if normalized in {"", ".", "/"}:
        return None, "syntactically_unusable"
    return normalized, None


def _normalize_list_filter(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    values = {normalize_text(part.strip()) for part in raw.split(",") if part.strip()}
    return values or None


def _parse_instruction_ids(raw_ids: list[Any]) -> list[str]:
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("instruction_ids must be a non-empty array.")
    out: list[str] = []
    seen: set[str] = set()
    for candidate in raw_ids:
        if not isinstance(candidate, str) or not candidate.strip():
            raise ValueError("instruction_ids must contain non-empty strings.")
        norm = candidate.strip()
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    if not out:
        raise ValueError("instruction_ids must contain at least one distinct id.")
    return out


def _parse_target_path(target_artifact: dict[str, Any]) -> str:
    if not isinstance(target_artifact, dict):
        raise ValueError("target_artifact must be an object with path.")
    path = str(target_artifact.get("path", "")).strip()
    if not path:
        raise ValueError("target_artifact.path is required.")
    return path


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


def _legacy_error_enabled() -> bool:
    return _cfg().include_legacy_error_field


def _format_error(
    *,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    suggested_next_call: dict[str, Any] | None = None,
) -> str:
    return json.dumps(
        build_error(
            error_code=error_code,
            message=message,
            details=details,
            suggested_next_call=suggested_next_call,
            include_legacy_error_field=_legacy_error_enabled(),
        ),
        ensure_ascii=False,
    )


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
    related: list[tuple[float, str, str]] = []
    title_tokens = set(tokenize_query(rec.title))
    for candidate in idx.values():
        if candidate.id == rec.id:
            continue
        overlap = len(tags & set(candidate.tags))
        kind_bonus = 1.0 if rec.kind and candidate.kind and rec.kind == candidate.kind else 0.0
        priority_delta = abs(PRIORITY_RANK.get(rec.priority, 0) - PRIORITY_RANK.get(candidate.priority, 0))
        priority_bonus = 1.0 - min(1.0, priority_delta / 3.0)
        lexical_overlap = len(title_tokens & set(tokenize_query(candidate.title)))
        combined = (overlap * 3.0) + kind_bonus + priority_bonus + (lexical_overlap * 0.5)
        if combined <= 0:
            continue
        related.append((combined, candidate.id, candidate.rel_path))
    related.sort(key=lambda item: (-item[0], item[2], item[1]))
    return [candidate_id for _, candidate_id, _ in related[:max_related]]


def _metadata_filter_match(
    rec: InstructionRecord,
    *,
    kind_filter: set[str] | None,
    priority_filter: set[str] | None,
    scope_filter: str | None,
    workspace_evidence_required: bool | None,
) -> bool:
    if kind_filter and normalize_text(rec.kind or "") not in kind_filter:
        return False
    if priority_filter and normalize_text(rec.priority or "") not in priority_filter:
        return False
    if scope_filter:
        scope_norm = normalize_text(rec.scope or "")
        if scope_filter not in scope_norm:
            return False
    if workspace_evidence_required is not None:
        if _workspace_evidence_required(rec.raw_frontmatter) != workspace_evidence_required:
            return False
    return True


def _frontmatter_string(meta: dict[str, Any], key: str) -> str | None:
    raw = meta.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _build_catalog_item(
    rec: InstructionRecord,
    *,
    scope_match: bool | None = None,
    include_match_reason: bool = False,
    include_summary: bool = True,
) -> dict[str, Any]:
    summary = _frontmatter_string(rec.raw_frontmatter, "summary")
    item: dict[str, Any] = {
        "id": rec.id,
        "path": rec.rel_path,
        "title": rec.title,
        "tags": rec.tags,
        "scope": rec.scope,
        "priority": rec.priority,
        "kind": rec.kind,
        "status": _frontmatter_string(rec.raw_frontmatter, "status"),
        "owner": _frontmatter_string(rec.raw_frontmatter, "owner"),
        "workspace_evidence_required": _workspace_evidence_required(rec.raw_frontmatter),
        "content_sha256": rec.content_hash,
    }
    if include_summary:
        item["summary"] = summary if summary else summarize_body(rec.body)
    if include_match_reason and scope_match is not None:
        if scope_match:
            item["match_reason"] = "scope matched current_file_path"
        else:
            item["match_reason"] = "included despite scope mismatch because include_non_matching_global=true"
    return item


def _facet_counts(values: list[str], *, top_n: int = _LIST_FACET_TOP_N) -> tuple[dict[str, int], bool]:
    counter = Counter(v for v in values if v)
    ordered = sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))
    truncated = len(ordered) > top_n
    return dict(ordered[:top_n]), truncated


@mcp.tool()
def list_instructions_index(
    tags: str | None = None,
    tags_mode: str = "any",
    kind: str | None = None,
    scope: str | None = None,
    priority: str | None = None,
    status: str | None = "active",
    owner: str | None = None,
    workspace_evidence_required: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    include_facets: bool = False,
    include_diagnostics: bool = False,
    current_file_path: str | None = None,
    include_non_matching_global: bool = False,
) -> str:
    """Use this tool to inspect and filter the metadata catalog of available instruction documents.

    This tool is for catalog discovery and metadata filtering only. It does not search instruction content
    and does not expand query terms.

    Prefer search_instructions when the task has a specific intent, topic, technology, error, implementation
    goal, or natural-language query.

    Use filters such as tags, kind, scope, priority, status, owner, or current_file_path whenever possible
    to avoid listing unrelated instructions. Use pagination for large catalogs.
    """
    call_start = time.perf_counter()
    tag_filter = _parse_tags(tags)
    tags_mode_normalized = "all" if str(tags_mode).strip().lower() == "all" else "any"
    kind_filter = _normalize_list_filter(kind)
    priority_filter = _normalize_list_filter(priority)
    scope_filter = normalize_text(scope) if scope else None
    status_filter = _normalize_list_filter(status)
    owner_filter = _normalize_list_filter(owner)
    evidence_filter = _parse_bool(workspace_evidence_required)
    page_limit = _clamp_int(limit, default=50, lo=0, hi=200)
    page_offset = _clamp_int(offset, default=0, lo=0, hi=1_000_000)
    normalized_current_file_path = normalize_path(current_file_path) if current_file_path else None

    if page_limit == 0 and not include_facets:
        return _format_error(
            error_code="LIST_INVALID_LIMIT",
            message="limit=0 is only allowed when include_facets=true.",
            details={"limit": limit, "include_facets": include_facets},
            suggested_next_call={"tool": "list_instructions_index", "args": {"include_facets": True, "limit": 0}},
        )

    try:
        idx, index_meta, _ = _ensure_index()
    except Exception as exc:
        return json.dumps(
            {
                "ok": False,
                "index_status": "error",
                "status": "error",
                "index_health": {
                    "loaded": False,
                    "documents_total": 0,
                    "documents_usable": 0,
                    "documents_with_warnings": 0,
                    "loaded_at_utc": None,
                },
                "items": [],
                "total_indexed": 0,
                "total_matched": 0,
                "limit": page_limit,
                "offset": page_offset,
                "has_more": False,
                "by_tag": {},
                "corpus_version": "",
                "warnings": [],
                "errors": [{"code": "INDEX_LOAD_FAILED", "reason": str(exc)}],
                "error": "Unable to load instructions index.",
                "error_code": "INDEX_LOAD_FAILED",
            },
            ensure_ascii=False,
        )

    records = list(idx.values())
    total_indexed = len(records)
    filtered: list[tuple[InstructionRecord, bool]] = []
    by_tag: dict[str, list[str]] = {}
    kind_counts: dict[str, int] = {}
    for rec in records:
        rec_tags = {tag.lower() for tag in rec.tags}
        if tags_mode_normalized == "all":
            if tag_filter and not tag_filter.issubset(rec_tags):
                continue
        elif tag_filter and not (tag_filter & rec_tags):
            continue
        if kind_filter and normalize_text(rec.kind or "") not in kind_filter:
            continue
        if priority_filter and normalize_text(rec.priority or "") not in priority_filter:
            continue
        if scope_filter and normalize_text(rec.scope or "") != scope_filter:
            continue
        if status_filter and normalize_text(_frontmatter_string(rec.raw_frontmatter, "status") or "") not in status_filter:
            continue
        if owner_filter and normalize_text(_frontmatter_string(rec.raw_frontmatter, "owner") or "") not in owner_filter:
            continue
        if evidence_filter is not None and _workspace_evidence_required(rec.raw_frontmatter) != evidence_filter:
            continue
        scope_match = True
        if normalized_current_file_path:
            scope_match, _ = match_scope(rec.scope, normalized_current_file_path)
            if not scope_match and not include_non_matching_global:
                continue
        filtered.append((rec, scope_match))
        k = rec.kind or "unknown"
        kind_counts[k] = kind_counts.get(k, 0) + 1
        for tag in rec.tags:
            by_tag.setdefault(tag, []).append(rec.id)

    filtered.sort(
        key=lambda item: (
            0 if (normalized_current_file_path and item[1]) else 1 if normalized_current_file_path else 0,
            -PRIORITY_RANK.get(item[0].priority, 0),
            _KIND_SORT_ORDER.get(normalize_text(item[0].kind or ""), 99),
            normalize_text(item[0].kind or ""),
            item[0].id,
            item[0].rel_path,
        )
    )

    total_matched = len(filtered)
    page_slice = filtered[page_offset : page_offset + page_limit] if page_limit > 0 else []
    items = [
        _build_catalog_item(
            rec,
            scope_match=scope_match,
            include_match_reason=bool(normalized_current_file_path),
            include_summary=True,
        )
        for rec, scope_match in page_slice
    ]

    by_tag = {tag: sorted(ids) for tag, ids in sorted(by_tag.items())}
    has_more = (page_offset + len(items)) < total_matched

    facets: dict[str, Any] | None = None
    if include_facets:
        kinds = Counter((rec.kind or "unknown") for rec, _ in filtered)
        priorities = Counter((rec.priority or "unknown") for rec, _ in filtered)
        statuses = Counter((_frontmatter_string(rec.raw_frontmatter, "status") or "unknown") for rec, _ in filtered)
        scopes, scopes_truncated = _facet_counts([str(rec.scope or "none") for rec, _ in filtered])
        tags_values: list[str] = []
        for rec, _ in filtered:
            tags_values.extend(rec.tags)
        tags_counts, tags_truncated = _facet_counts(tags_values)
        facets = {
            "kind": dict(sorted(kinds.items(), key=lambda pair: (-pair[1], pair[0]))),
            "priority": dict(sorted(priorities.items(), key=lambda pair: (-pair[1], pair[0]))),
            "status": dict(sorted(statuses.items(), key=lambda pair: (-pair[1], pair[0]))),
            "scope": scopes,
            "tags": tags_counts,
            "truncated": {
                "scope": scopes_truncated,
                "tags": tags_truncated,
            },
        }

    index_warnings = list(_index_warnings)
    index_status = "partial" if index_warnings else "ok"
    diagnostics: dict[str, Any] | None = None
    if include_diagnostics:
        scope_matches = sum(1 for _, scope_match in filtered if scope_match)
        scope_mismatches = total_matched - scope_matches
        diagnostics = {
            "applied_filters": {
                "tags": sorted(tag_filter) if tag_filter else None,
                "tags_mode": tags_mode_normalized,
                "kind": sorted(kind_filter) if kind_filter else None,
                "scope": scope_filter,
                "priority": sorted(priority_filter) if priority_filter else None,
                "status": sorted(status_filter) if status_filter else None,
                "owner": sorted(owner_filter) if owner_filter else None,
                "workspace_evidence_required": evidence_filter,
                "current_file_path": normalized_current_file_path,
                "include_non_matching_global": bool(include_non_matching_global),
            },
            "pagination": {
                "total_indexed": total_indexed,
                "total_matched": total_matched,
                "returned": len(items),
                "limit": page_limit,
                "offset": page_offset,
                "has_more": has_more,
            },
            "scope_match": {
                "matched": scope_matches if normalized_current_file_path else None,
                "unmatched": scope_mismatches if normalized_current_file_path else None,
            },
        }

    raw = json.dumps(
        {
            "index_status": index_status,
            "status": index_status,
            "index_health": {
                "loaded": True,
                "documents_total": index_meta.get("corpus_file_count", total_indexed),
                "documents_usable": total_indexed,
                "documents_with_warnings": len(index_warnings),
                "loaded_at_utc": _index_loaded_at_utc,
            },
            "items": items,
            "total_indexed": total_indexed,
            "total_matched": total_matched,
            "limit": page_limit,
            "offset": page_offset,
            "has_more": has_more,
            "by_tag": by_tag,
            "corpus_version": index_meta.get("corpus_version"),
            "corpus_file_count": index_meta.get("corpus_file_count"),
            "warnings": index_warnings,
            "errors": [],
            **({"facets": facets} if facets is not None else {}),
            **({"diagnostics": diagnostics} if diagnostics is not None else {}),
        },
        ensure_ascii=False,
    )
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    payload = {
        "unique_instruction_ids_count": total_matched,
        "instructions_consulted_count": total_indexed,
        "total_indexed": total_indexed,
        "total_matched": total_matched,
        "returned_page_size": len(items),
        "instructions_by_kind": kind_counts,
        "instructions_by_tag": {t: len(ids) for t, ids in by_tag.items()},
        "by_tag_count": len(by_tag),
        "response_chars": len(raw),
        "response_bytes": len(raw.encode("utf-8", errors="replace")),
        "calls_with_non_empty_result": 1 if items else 0,
        "empty_result_rate": 0.0 if items else 1.0,
        **index_meta,
        "metrics_not_measurable_server_side": _SERVER_UNOBSERVABLE_METRICS,
    }
    _emit_tool_completed(
        "list_instructions_index.completed",
        duration_ms,
        failure=False,
        args_key_payload={
            "tags": tags,
            "tags_mode": tags_mode_normalized,
            "kind": kind,
            "scope": scope,
            "priority": priority,
            "status": status,
            "owner": owner,
            "workspace_evidence_required": evidence_filter,
            "limit": page_limit,
            "offset": page_offset,
            "include_facets": include_facets,
            "include_diagnostics": include_diagnostics,
            "current_file_path": normalized_current_file_path,
            "include_non_matching_global": include_non_matching_global,
        },
        payload=payload,
    )
    return raw


@mcp.tool()
def search_instructions(
    query: str,
    tags: str | None = None,
    max_results: int = 10,
    include_diagnostics: bool = False,
    tags_mode: str = "any",
    kind: str | None = None,
    scope: str | None = None,
    priority: str | None = None,
    workspace_evidence_required: bool | None = None,
    telemetry_expected_instruction_id: str | None = None,
    queries: list[str] | None = None,
    max_results_per_query: int = 5,
    current_file_path: str | None = None,
) -> str:
    """Use when the user asks about architecture, patterns, DNS, security, style, or any org-specific guideline.

    Full-text style search (keyword overlap) over the instruction corpus. Prefer calling this before
    proposing cross-cutting design. Parameters: query (natural language), optional comma-separated tags
    filter, max_results (default 10, cap 20), and optional current_file_path when the task is tied to
    a specific file. current_file_path is contextual evidence for declarative filters such as applies_to;
    it does not make the server read the user's workspace. Optional telemetry_expected_instruction_id is
    for offline ranking evaluation (expected instruction id).
    """
    call_start = time.perf_counter()
    current_file_path_provided = current_file_path is not None
    normalized_current_file_path, current_file_path_ignored_reason = _normalize_current_file_path_input(
        current_file_path
    )
    if isinstance(queries, list) and queries:
        cleaned_queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        if not cleaned_queries:
            return _format_error(
                error_code="INVALID_MULTI_QUERY_INPUT",
                message="queries must include at least one non-empty string.",
                details={"queries": queries},
            )
        per_query = _clamp_int(
            max_results_per_query,
            default=5,
            lo=1,
            hi=20,
        )
        rows: list[dict[str, Any]] = []
        grouped: dict[str, dict[str, dict[str, Any]]] = {
            "policy": {},
            "reference": {},
        }
        coverage_gaps: list[str] = []
        for q in cleaned_queries:
            payload = json.loads(
                search_instructions(
                    query=q,
                    tags=tags,
                    max_results=per_query,
                    include_diagnostics=include_diagnostics,
                    tags_mode=tags_mode,
                    kind=kind,
                    scope=scope,
                    priority=priority,
                    workspace_evidence_required=workspace_evidence_required,
                    telemetry_expected_instruction_id=telemetry_expected_instruction_id,
                    queries=None,
                    max_results_per_query=per_query,
                    current_file_path=current_file_path,
                )
            )
            query_results = payload.get("results", [])
            rows.append(
                {
                    "query": q,
                    "results": query_results,
                }
            )
            if not query_results:
                coverage_gaps.append(f"No matches for query: {q}")
            for result in query_results:
                if not isinstance(result, dict):
                    continue
                rec_id = str(result.get("id", "")).strip()
                rec_kind = str(result.get("kind", "")).strip().lower()
                if rec_kind not in grouped:
                    continue
                relevance = float(result.get("relevance", 0.0))
                current = grouped[rec_kind].get(rec_id)
                if current is None or float(current.get("relevance", 0.0)) < relevance:
                    grouped[rec_kind][rec_id] = result
        top_policies = sorted(
            grouped["policy"].values(),
            key=lambda item: (-float(item.get("relevance", 0.0)), str(item.get("id", ""))),
        )[:per_query]
        top_references = sorted(
            grouped["reference"].values(),
            key=lambda item: (-float(item.get("relevance", 0.0)), str(item.get("id", ""))),
        )[:per_query]
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        raw = json.dumps(
            {
                "queries": rows,
                "consolidated": {
                    "top_policies": top_policies,
                    "top_references": top_references,
                    "coverage_gaps": coverage_gaps,
                },
                **(
                    {
                        "diagnostics": {
                            "current_file_path": {
                                "provided": current_file_path_provided,
                                "normalized": normalized_current_file_path,
                                "used_for_expansion": normalized_current_file_path is not None,
                                "ignored_reason": current_file_path_ignored_reason,
                            }
                        }
                    }
                    if include_diagnostics
                    else {}
                ),
            },
            ensure_ascii=False,
        )
        _emit_tool_completed(
            "search_instructions.completed",
            duration_ms,
            failure=False,
            args_key_payload={"queries_count": len(cleaned_queries), "multi_query": True},
            payload={
                "search_mode": "multi_query",
                "search_results_count": sum(len(row["results"]) for row in rows),
                "queries_count": len(cleaned_queries),
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
            },
        )
        return raw

    cfg = _cfg()
    args_summary = telemetry.search_args_summary(query, tags, max_results)
    args_summary["current_file_path_present"] = normalized_current_file_path is not None
    try:
        idx, index_meta, expansion_map = _ensure_index()
    except Exception as exc:
        return _format_error(
            error_code="SEARCH_INDEX_UNAVAILABLE",
            message="Unable to search because index is unavailable.",
            details={"reason": str(exc)},
            suggested_next_call={"tool": "list_instructions_index", "args": {}},
        )
    tokens = tokenize_query(query)
    exact_phrases = extract_exact_phrases(query)
    tag_filter = _parse_tags(tags)
    tags_mode_normalized = "all" if str(tags_mode).strip().lower() == "all" else "any"
    kind_filter = _normalize_list_filter(kind)
    priority_filter = _normalize_list_filter(priority)
    scope_filter = normalize_text(scope) if scope else None
    evidence_filter = _parse_bool(workspace_evidence_required)
    cap = _clamp_int(
        max_results,
        default=cfg.search_default_max_results,
        lo=1,
        hi=cfg.search_max_results_cap,
    )
    expanded_info = (
        expand_query_with_metadata(
            tokens,
            expansion_map=expansion_map,
            current_file_path=normalized_current_file_path,
        )
        if tokens
        else None
    )

    def _finish(
        *,
        failure: bool,
        payload: dict[str, Any],
        search_mode: str,
        ranked_full: list[tuple[float, InstructionRecord]],
        results: list[dict[str, Any]],
        expanded_for_telemetry: dict[str, Any] | None,
    ) -> str:
        if include_diagnostics:
            diagnostics = payload.get("diagnostics")
            if not isinstance(diagnostics, dict):
                diagnostics = {}
                payload["diagnostics"] = diagnostics
            diagnostics["current_file_path"] = {
                "provided": current_file_path_provided,
                "normalized": normalized_current_file_path,
                "used_for_expansion": normalized_current_file_path is not None,
                "ignored_reason": current_file_path_ignored_reason,
            }
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

        low_conf = bool(top_rel and top_rel[0] < cfg.low_confidence_relevance_threshold)
        confidence = search_confidence(gap_1_2, top_rel[0] if top_rel else None, result_count)
        ambiguous_gap = bool(gap_1_2 is not None and gap_1_2 <= cfg.ambiguous_score_gap_threshold)

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
                    bd = score_record_breakdown(
                        rec,
                        tokens,
                        tag_filter,
                        ei,
                        tags_mode=tags_mode_normalized,
                        exact_phrases=exact_phrases,
                        expansion_penalty_ratio=cfg.expansion_only_penalty_ratio,
                    )
                    mu, md = terms_with_positive_hits(rec, ei, tag_filter, tags_mode=tags_mode_normalized)
                    breakdown_rows.append(
                        {
                            "id": rec.id,
                            "score_total": round(bd.total, 4),
                            "score_title": round(bd.score_title, 4),
                            "score_tags": round(bd.score_tags, 4),
                            "score_body": round(bd.score_body_blob, 4),
                            "score_priority": round(bd.score_priority, 4),
                            "expansion_score_bonus": round(bd.score_from_expansion_terms, 4),
                            "score_exact_phrase": round(bd.score_exact_phrase, 4),
                            "score_proximity": round(bd.score_proximity, 4),
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
            "search_confidence": confidence,
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
            "corpus_version": index_meta.get("corpus_version"),
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
        if (
            not tag_filter
            and not kind_filter
            and not priority_filter
            and not scope_filter
            and evidence_filter is None
        ):
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
            if not _metadata_filter_match(
                rec,
                kind_filter=kind_filter,
                priority_filter=priority_filter,
                scope_filter=scope_filter,
                workspace_evidence_required=evidence_filter,
            ):
                continue
            if tags_mode_normalized == "all":
                if tag_filter and not tag_filter.issubset(set(rec.tags)):
                    continue
            elif tag_filter and not (tag_filter & set(rec.tags)):
                continue
            pr = float(PRIORITY_RANK.get(rec.priority, 0))
            ranked.append((pr, rec))
        ranked.sort(key=lambda x: (-x[0], x[1].rel_path))
    else:
        ranked = []
        normalized_query = normalize_text(query).strip()
        for rec in idx.values():
            if not _metadata_filter_match(
                rec,
                kind_filter=kind_filter,
                priority_filter=priority_filter,
                scope_filter=scope_filter,
                workspace_evidence_required=evidence_filter,
            ):
                continue
            score = score_record(
                rec,
                tokens,
                tag_filter,
                tags_mode=tags_mode_normalized,
                exact_phrases=exact_phrases,
                expansion_penalty_ratio=cfg.expansion_only_penalty_ratio,
                expanded_info=expanded_info,
            )
            if normalized_query:
                if normalized_query == normalize_text(rec.id):
                    score += 5.0
                if normalized_query == normalize_text(rec.title):
                    score += 4.0
                if normalize_text(rec.id) in normalized_query:
                    score += 2.0
            ranked.append((score, rec))
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
                        "expansion_count": expanded_info.expansion_count if expanded_info else 0,
                        "expansion_truncated": expanded_info.expansion_truncated if expanded_info else False,
                        "terms_from_user": len(tokens),
                        "expansion_added_terms_count": len(expanded_info.expansion_added_terms) if expanded_info else 0,
                    },
                }
                if expanded_info
                else None
            ),
            payload={
                "results": [],
                "composed_context": "",
                "note": "No matches; refine query or use list_instructions_index.",
                "fallback_suggestions": build_fallback_suggestions(
                    zero_results=True,
                    low_confidence=False,
                    ambiguous_gap=False,
                    expansion_only_results=0,
                    has_tags_filter=bool(tag_filter),
                    max_results=cap,
                ),
            },
        )

    results = []
    composed_parts: list[str] = []
    for score, rec in ranked[:cap]:
        excerpt = excerpt_around_match(rec.body, tokens) if tokens else summarize_body(rec.body, 400)
        breakdown = score_record_breakdown(
            rec,
            tokens,
            tag_filter,
            expanded_info,
            tags_mode=tags_mode_normalized,
            exact_phrases=exact_phrases,
            expansion_penalty_ratio=cfg.expansion_only_penalty_ratio,
        )
        matched_user, matched_expansion = (
            terms_with_positive_hits(rec, expanded_info, tag_filter, tags_mode=tags_mode_normalized)
            if expanded_info
            else (set(), set())
        )
        results.append(
            {
                "source": rec.rel_path,
                "id": rec.id,
                "title": rec.title,
                "scope": rec.scope,
                "priority": rec.priority,
                "relevance": round(min(1.0, score / 10.0), 4),
                "score": round(score, 4),
                "summary": summarize_body(rec.body),
                "key_excerpt": excerpt,
                "full_available": True,
                "tags": rec.tags,
                "kind": rec.kind,
                "related_ids": _related_instruction_ids(rec, idx),
                "match_explanation": {
                    "score_title": round(breakdown.score_title, 4),
                    "score_tags": round(breakdown.score_tags, 4),
                    "score_body": round(breakdown.score_body_blob, 4),
                    "score_priority": round(breakdown.score_priority, 4),
                    "score_exact_phrase": round(breakdown.score_exact_phrase, 4),
                    "score_proximity": round(breakdown.score_proximity, 4),
                    "matched_user_terms": sorted(matched_user),
                    "matched_expansion_only_terms": sorted(matched_expansion),
                },
            }
        )
        composed_parts.append(f"- **{rec.title}** (`{rec.id}`): {summarize_body(rec.body, 220)}")

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
                "expansion_count": expanded_info.expansion_count,
                "expansion_truncated": expanded_info.expansion_truncated,
                "terms_from_user": len(tokens),
                "expansion_added_terms_count": len(expanded_info.expansion_added_terms),
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
            "composed_context": (
                "## Regras obrigatórias\n"
                + "\n".join(composed_parts[:3])
                + "\n\n## Recomendações\n"
                + ("\n".join(composed_parts[3:6]) if len(composed_parts) > 3 else "- Nenhuma recomendação adicional.")
                + "\n\n## Riscos comuns\n"
                + ("- Resultado com baixa confiança, execute fallback." if results and results[0]["relevance"] < cfg.low_confidence_relevance_threshold else "- Sem riscos críticos no top result.")
                + "\n\n## Lacunas detectadas\n"
                + ("- Refine a consulta com filtros de metadado." if len(results) < 2 else "- Sem lacunas críticas iniciais.")
            ),
            "corpus_version": index_meta.get("corpus_version"),
            **(
                {
                    "diagnostics": {
                        "search_confidence": search_confidence(
                            (results[0]["score"] - results[1]["score"]) if len(results) > 1 else None,
                            results[0]["relevance"] if results else None,
                            len(results),
                        ),
                        "top_score_gap_1_2": (results[0]["score"] - results[1]["score"]) if len(results) > 1 else None,
                        "top3_scores": [r["score"] for r in results[:3]],
                        "matched_user_terms": sorted(
                            set().union(*[set(r["match_explanation"]["matched_user_terms"]) for r in results[:3]])
                        )
                        if results
                        else [],
                        "matched_expansion_only_terms": sorted(
                            set().union(
                                *[set(r["match_explanation"]["matched_expansion_only_terms"]) for r in results[:3]]
                            )
                        )
                        if results
                        else [],
                        "results_only_from_expansion_count": sum(
                            1
                            for r in results
                            if not r["match_explanation"]["matched_user_terms"]
                            and r["match_explanation"]["matched_expansion_only_terms"]
                        ),
                    }
                }
                if include_diagnostics
                else {}
            ),
            **(
                {
                    "fallback_suggestions": build_fallback_suggestions(
                        zero_results=False,
                        low_confidence=(
                            bool(results) and float(results[0].get("relevance", 0.0)) < cfg.low_confidence_relevance_threshold
                        ),
                        ambiguous_gap=(
                            len(results) > 1
                            and (results[0]["score"] - results[1]["score"]) <= cfg.ambiguous_score_gap_threshold
                        ),
                        expansion_only_results=sum(
                            1
                            for r in results
                            if not r["match_explanation"]["matched_user_terms"]
                            and r["match_explanation"]["matched_expansion_only_terms"]
                        ),
                        has_tags_filter=bool(tag_filter),
                        max_results=cap,
                    )
                }
                if include_diagnostics
                else {}
            ),
        },
    )


@mcp.tool()
def get_instructions_batch(
    ids: str,
    max_chars_per_instruction: int = 8000,
    section_contains: str | None = None,
    include_headings: bool = True,
    headings_only: bool = False,
) -> str:
    """Fetch multiple instructions in one call. Parameter ids: comma-separated instruction ids.

    Call after list_instructions_index or search_instructions when full bodies are needed.
    Each returned item includes a frontmatter object (parsed YAML header, JSON-safe).
    """
    call_start = time.perf_counter()
    cfg = _cfg()
    args_summary = telemetry.get_batch_args_summary(ids, max_chars_per_instruction)
    try:
        idx, index_meta, _ = _ensure_index()
    except Exception as exc:
        return _format_error(
            error_code="BATCH_INDEX_UNAVAILABLE",
            message="Unable to fetch instructions because index is unavailable.",
            details={"reason": str(exc)},
            suggested_next_call={"tool": "list_instructions_index", "args": {}},
        )
    requested_ids = [candidate.strip() for candidate in str(ids).split(",") if candidate.strip()]
    if not requested_ids:
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        raw = _format_error(
            error_code="BATCH_EMPTY_IDS",
            message="Provide at least one instruction id.",
            details={"ids": ids},
            suggested_next_call={"tool": "search_instructions", "args": {"query": "architecture patterns"}},
        )
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

    per_instruction_limit = _clamp_int(
        max_chars_per_instruction,
        default=cfg.batch_default_max_chars_per_instruction,
        lo=cfg.batch_min_chars_per_instruction,
        hi=cfg.batch_max_chars_per_instruction,
    )
    total_remaining = cfg.batch_max_total_chars
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
        sections = split_markdown_sections(rec.body)
        filtered_sections, matched_section_count = filter_sections(sections, section_contains)
        selected_sections = filtered_sections if filtered_sections else sections
        body, truncated, included_headings = compose_section_payload(
            selected_sections,
            include_headings=include_headings,
            headings_only=headings_only,
            max_chars=effective_limit,
        )
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
                "status": _frontmatter_string(rec.raw_frontmatter, "status"),
                "owner": _frontmatter_string(rec.raw_frontmatter, "owner"),
                "workspace_evidence_required": _workspace_evidence_required(rec.raw_frontmatter),
                "summary": _frontmatter_string(rec.raw_frontmatter, "summary") or summarize_body(rec.body),
                "content_sha256": rec.content_hash,
                "truncated": truncated,
                "content": body,
                "section_filter_applied": bool(section_contains),
                "section_match_count": matched_section_count,
                "included_headings": included_headings,
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
        "max_total_chars": cfg.batch_max_total_chars,
        "corpus_version": index_meta.get("corpus_version"),
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


def resolve_instruction_context(
    query: str,
    max_results: int = 5,
    include_diagnostics: bool = True,
) -> str:
    """Run deterministic search + batch in one tool call."""
    call_start = time.perf_counter()
    search_raw = search_instructions(
        query=query,
        max_results=max_results,
        include_diagnostics=include_diagnostics,
    )
    parsed = json.loads(search_raw)
    if parsed.get("ok") is False:
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "resolve_instruction_context.completed",
            duration_ms,
            failure=True,
            args_key_payload={"query": telemetry.query_fingerprint(query), "max_results": max_results},
            payload={
                "selected_ids_count": 0,
                "response_chars": len(search_raw),
                "response_bytes": len(search_raw.encode("utf-8", errors="replace")),
                "error_code": parsed.get("error_code"),
            },
        )
        return search_raw
    preliminary = build_resolved_context(
        query=query,
        max_results=max_results,
        search_payload=parsed,
        batch_payload={"instructions": []},
    )
    top_ids = [instruction_id for instruction_id in preliminary.get("selected_ids", []) if isinstance(instruction_id, str)]
    if not top_ids:
        raw = json.dumps(
            {
                "query": query,
                "selected_ids": [],
                "context": "",
                "resolution": preliminary,
                "note": "No results available for context resolution.",
            },
            ensure_ascii=False,
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "resolve_instruction_context.completed",
            duration_ms,
            failure=False,
            args_key_payload={"query": telemetry.query_fingerprint(query), "max_results": max_results},
            payload={
                "selected_ids_count": 0,
                "search_confidence": preliminary.get("criteria", {}).get("search_confidence"),
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "calls_with_non_empty_result": 0,
                "empty_result_rate": 1.0,
            },
        )
        return raw
    section_focus = preliminary.get("selection", {}).get("section_focus")
    batch_raw = get_instructions_batch(
        ids=",".join(top_ids),
        max_chars_per_instruction=4000,
        section_contains=section_focus if isinstance(section_focus, str) and section_focus.strip() else None,
        include_headings=True,
    )
    batch_parsed = json.loads(batch_raw)
    resolution = build_resolved_context(
        query=query,
        max_results=max_results,
        search_payload=parsed,
        batch_payload=batch_parsed,
    )
    raw = json.dumps(
        {
            "query": query,
            "selected_ids": top_ids,
            "search": parsed,
            "batch": batch_parsed,
            "context": resolution.get("actionable_context", {}).get("implementation_brief")
            or parsed.get("composed_context", ""),
            "resolution": resolution,
            "corpus_version": parsed.get("corpus_version"),
        },
        ensure_ascii=False,
    )
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    _emit_tool_completed(
        "resolve_instruction_context.completed",
        duration_ms,
        failure=False,
        args_key_payload={"query": telemetry.query_fingerprint(query), "max_results": max_results},
        payload={
            "selected_ids_count": len(top_ids),
            "normative_ids_count": len(resolution.get("actionable_context", {}).get("normative_ids", [])),
            "supporting_ids_count": len(resolution.get("actionable_context", {}).get("supporting_ids", [])),
            "search_confidence": resolution.get("criteria", {}).get("search_confidence"),
            "low_confidence": bool(resolution.get("criteria", {}).get("low_confidence")),
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
            "calls_with_non_empty_result": 1 if top_ids else 0,
            "empty_result_rate": 0.0 if top_ids else 1.0,
            "corpus_version": parsed.get("corpus_version"),
        },
    )
    return raw


def validate_applicability(
    instruction_ids: list[Any],
    target_artifact: dict[str, Any],
    workspace_evidence: list[Any] | None = None,
) -> str:
    """Evaluate applicability of instructions using scope + workspace evidence gate."""
    call_start = time.perf_counter()
    try:
        idx, _, _ = _ensure_index()
    except Exception as exc:
        return _format_error(
            error_code="APPLICABILITY_INDEX_UNAVAILABLE",
            message="Unable to validate applicability because index is unavailable.",
            details={"reason": str(exc)},
            suggested_next_call={"tool": "list_instructions_index", "args": {}},
        )
    try:
        requested_ids = _parse_instruction_ids(instruction_ids)
        target_path = _parse_target_path(target_artifact)
        evidence_items = parse_workspace_evidence(workspace_evidence)
    except ValueError as exc:
        raw = _format_error(
            error_code="INVALID_APPLICABILITY_INPUT",
            message=str(exc),
            details={
                "instruction_ids": instruction_ids,
                "target_artifact": target_artifact,
            },
            suggested_next_call={
                "tool": "validate_applicability",
                "args": {
                    "instruction_ids": ["microservice-authorization-resource-scope-and-audit"],
                    "target_artifact": {"path": "Api/Endpoints/ClienteEndpoints.cs"},
                    "workspace_evidence": ["HttpContext.User"],
                },
            },
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "validate_applicability.completed",
            duration_ms,
            failure=True,
            args_key_payload={"instruction_ids_count": len(instruction_ids) if isinstance(instruction_ids, list) else 0},
            payload={"error_code": "INVALID_APPLICABILITY_INPUT"},
        )
        return raw

    missing_ids = [instruction_id for instruction_id in requested_ids if instruction_id not in idx]
    if missing_ids:
        raw = _format_error(
            error_code="INSTRUCTION_IDS_NOT_FOUND",
            message="One or more instruction_ids were not found in the current index.",
            details={"missing_instruction_ids": missing_ids},
            suggested_next_call={"tool": "list_instructions_index", "args": {}},
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "validate_applicability.completed",
            duration_ms,
            failure=True,
            args_key_payload={"instruction_ids_count": len(requested_ids)},
            payload={"error_code": "INSTRUCTION_IDS_NOT_FOUND", "missing_ids_count": len(missing_ids)},
        )
        return raw

    results = [decide_applicability(idx[instruction_id], target_path=target_path, evidence_items=evidence_items) for instruction_id in requested_ids]
    raw = json.dumps(
        {
            "results": results,
            "summary": {
                "requested_count": len(requested_ids),
                "resolved_count": len(results),
                "target_path": target_path,
                "by_applicability": {
                    state: sum(1 for row in results if row.get("applicability") == state)
                    for state in sorted(APPLICABILITY_STATES)
                },
            },
        },
        ensure_ascii=False,
    )
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    _emit_tool_completed(
        "validate_applicability.completed",
        duration_ms,
        failure=False,
        args_key_payload={"instruction_ids_count": len(requested_ids)},
        payload={
            "resolved_count": len(results),
            "target_path": target_path,
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
        },
    )
    return raw


def build_compliance_matrix(
    target_artifact: dict[str, Any],
    instruction_results: list[dict[str, Any]],
    artifact_observations: list[dict[str, Any]] | None = None,
) -> str:
    """Build operational compliance matrix from applicability and artifact observations."""
    call_start = time.perf_counter()
    try:
        target_path = _parse_target_path(target_artifact)
    except ValueError as exc:
        return _format_error(
            error_code="INVALID_COMPLIANCE_MATRIX_INPUT",
            message=str(exc),
            details={"target_artifact": target_artifact},
            suggested_next_call={
                "tool": "build_compliance_matrix",
                "args": {
                    "target_artifact": {"path": "Api/Endpoints/ClienteEndpoints.cs"},
                    "instruction_results": [
                        {
                            "instruction_id": "microservice-api-openfinance-patterns",
                            "kind": "policy",
                            "applicability": "applicable",
                        }
                    ],
                },
            },
        )
    if not isinstance(instruction_results, list) or not instruction_results:
        return _format_error(
            error_code="INVALID_COMPLIANCE_MATRIX_INPUT",
            message="instruction_results must be a non-empty array.",
            details={"instruction_results": instruction_results},
        )
    observations = artifact_observations if isinstance(artifact_observations, list) else []
    by_instruction_id: dict[str, list[dict[str, Any]]] = {}
    for row in observations:
        instruction_id = str(row.get("instruction_id", "")).strip() if isinstance(row, dict) else ""
        if not instruction_id:
            continue
        by_instruction_id.setdefault(instruction_id, []).append(row)

    matrix: list[dict[str, Any]] = []
    for item in instruction_results:
        if not isinstance(item, dict):
            return _format_error(
                error_code="INVALID_COMPLIANCE_MATRIX_INPUT",
                message="Each instruction_results entry must be an object.",
            )
        instruction_id = str(item.get("instruction_id", "")).strip()
        kind = str(item.get("kind", "")).strip()
        applicability = str(item.get("applicability", "")).strip().lower()
        if not instruction_id or not kind or applicability not in APPLICABILITY_STATES:
            return _format_error(
                error_code="INVALID_COMPLIANCE_MATRIX_INPUT",
                message=(
                    "Each instruction_results entry must contain instruction_id, kind, "
                    "and applicability in the official applicability states."
                ),
                details={"instruction_result": item},
            )
        matrix.append(build_compliance_row(item, by_instruction_id.get(instruction_id, [])))

    summary = {
        "conformant": 0,
        "partial_conformance": 0,
        "non_conformance": 0,
        "not_enforceable": 0,
        "not_applicable": 0,
        "insufficient_evidence": 0,
    }
    for row in matrix:
        status = str(row.get("status", "")).strip()
        if status in summary:
            summary[status] += 1

    raw = json.dumps(
        {
            "target_artifact": {"path": target_path},
            "matrix": matrix,
            "summary": summary,
        },
        ensure_ascii=False,
    )
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    _emit_tool_completed(
        "build_compliance_matrix.completed",
        duration_ms,
        failure=False,
        args_key_payload={"instruction_results_count": len(instruction_results)},
        payload={
            "matrix_rows_count": len(matrix),
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
        },
    )
    return raw


def get_context_triggers(input_payload: str) -> str:
    """Return deterministic context-routing triggers from a structured contract payload.

    This tool classifies the scenario and returns the recommended orchestration sequence. It does not
    execute repo edits, run builds, or automatically call other tools.
    """
    call_start = time.perf_counter()
    args_payload: dict[str, Any] = {"input_payload_len": len(str(input_payload))}
    if isinstance(input_payload, dict):
        parsed_input: Any = input_payload
    else:
        try:
            parsed_input = json.loads(str(input_payload))
        except json.JSONDecodeError:
            example_payload = (
                '{"schema_version":"1.0.0","request":{},"workspace":{},'
                '"context_state":{},"constraints":{}}'
            )
            raw = _format_error(
                error_code="INVALID_REQUEST_PAYLOAD",
                message="input_payload must be a valid JSON object.",
                details={"input_payload_len": len(str(input_payload))},
                suggested_next_call={
                    "tool": "get_context_triggers",
                    "args": {"input_payload": example_payload},
                },
            )
            duration_ms = int((time.perf_counter() - call_start) * 1000)
            _emit_tool_completed(
                "get_context_triggers.completed",
                duration_ms,
                failure=True,
                args_key_payload=args_payload,
                payload={
                    "response_chars": len(raw),
                    "response_bytes": len(raw.encode("utf-8", errors="replace")),
                    "error_code": "INVALID_REQUEST_PAYLOAD",
                },
            )
            return raw

    if not isinstance(parsed_input, dict):
        example_payload = (
            '{"schema_version":"1.0.0","request":{},"workspace":{},'
            '"context_state":{},"constraints":{}}'
        )
        raw = _format_error(
            error_code="INVALID_REQUEST_PAYLOAD",
            message="input_payload must decode to a JSON object.",
            details={"input_payload_len": len(str(input_payload))},
            suggested_next_call={
                "tool": "get_context_triggers",
                "args": {"input_payload": example_payload},
            },
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "get_context_triggers.completed",
            duration_ms,
            failure=True,
            args_key_payload=args_payload,
            payload={
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "error_code": "INVALID_REQUEST_PAYLOAD",
            },
        )
        return raw

    parsed_input.setdefault("schema_version", SUPPORTED_SCHEMA_VERSION)
    req = parsed_input.get("request", {})
    if isinstance(req, dict):
        args_payload.update(
            {
                "schema_version": parsed_input.get("schema_version"),
                "operation_mode": req.get("operation_mode"),
                "wants_only_plan": req.get("wants_only_plan"),
                "mentions_cross_cutting_concerns": req.get("mentions_cross_cutting_concerns"),
            }
        )

    try:
        output = build_context_triggers(cast(dict[str, Any], parsed_input))
    except ContractError as exc:
        raw = _format_error(
            error_code=exc.code,
            message=exc.message,
            details=exc.details or {},
            suggested_next_call={"tool": "get_context_triggers", "args": {"input_payload": input_payload}},
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "get_context_triggers.completed",
            duration_ms,
            failure=True,
            args_key_payload=args_payload,
            payload={
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "error_code": exc.code,
            },
        )
        return raw
    except Exception as exc:
        raw = _format_error(
            error_code="CONTEXT_TRIGGER_INTERNAL_ERROR",
            message="Unexpected error while computing context triggers.",
            details={"reason": str(exc)},
            suggested_next_call={"tool": "get_context_triggers", "args": {"input_payload": input_payload}},
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "get_context_triggers.completed",
            duration_ms,
            failure=True,
            args_key_payload=args_payload,
            payload={
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "error_code": "CONTEXT_TRIGGER_INTERNAL_ERROR",
            },
        )
        return raw

    raw = json.dumps(output, ensure_ascii=False)
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    strategy = output.get("strategy", {}) if isinstance(output.get("strategy"), dict) else {}
    scenario = output.get("scenario", {}) if isinstance(output.get("scenario"), dict) else {}
    _emit_tool_completed(
        "get_context_triggers.completed",
        duration_ms,
        failure=False,
        args_key_payload=args_payload,
        payload={
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
            "tool_sequence_count": len(output.get("tool_sequence", [])),
            "scenario_id": scenario.get("scenario_id"),
            "scenario_family": scenario.get("scenario_family"),
            "recommended_execution_mode": strategy.get("recommended_execution_mode"),
            "should_use_mcp": strategy.get("should_use_mcp"),
            "should_stop_for_human_input": strategy.get("should_stop_for_human_input"),
            "calls_with_non_empty_result": 1,
            "empty_result_rate": 0.0,
        },
    )
    return raw


def get_normative_checklist(scenario: str) -> str:
    """Return checklist for a scenario with evidence from current index."""
    call_start = time.perf_counter()
    try:
        idx, index_meta, _ = _ensure_index()
    except Exception as exc:
        raw = _format_error(
            error_code="CHECKLIST_INDEX_UNAVAILABLE",
            message="Unable to build checklist because index is unavailable.",
            details={"reason": str(exc)},
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "get_normative_checklist.completed",
            duration_ms,
            failure=True,
            args_key_payload={"scenario": normalize_text(scenario)},
            payload={
                "scenario": scenario,
                "items_count": 0,
                "missing_instruction_ids_count": 0,
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "error_code": "CHECKLIST_INDEX_UNAVAILABLE",
            },
        )
        return raw
    payload = build_normative_checklist(idx, scenario)
    payload["corpus_version"] = index_meta.get("corpus_version")
    raw = json.dumps(payload, ensure_ascii=False)
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    _emit_tool_completed(
        "get_normative_checklist.completed",
        duration_ms,
        failure=False,
        args_key_payload={"scenario": normalize_text(scenario)},
        payload={
            "scenario": scenario,
            "items_count": len(payload.get("items", [])),
            "missing_instruction_ids_count": len(payload.get("missing_instruction_ids", [])),
            "required_items": summary.get("required_items", 0),
            "required_items_covered": summary.get("required_items_covered", 0),
            "implementation_readiness": summary.get("implementation_readiness"),
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
            "corpus_version": payload.get("corpus_version"),
        },
    )
    return raw


def detect_instruction_conflicts(ids: str) -> str:
    """Detect potential conflicts and precedence among instruction ids."""
    call_start = time.perf_counter()
    try:
        idx, index_meta, _ = _ensure_index()
    except Exception as exc:
        raw = _format_error(
            error_code="CONFLICT_INDEX_UNAVAILABLE",
            message="Unable to detect conflicts because index is unavailable.",
            details={"reason": str(exc)},
        )
        duration_ms = int((time.perf_counter() - call_start) * 1000)
        _emit_tool_completed(
            "detect_instruction_conflicts.completed",
            duration_ms,
            failure=True,
            args_key_payload={"ids": sorted([part.strip() for part in ids.split(",") if part.strip()])},
            payload={
                "checked_ids_count": 0,
                "missing_ids_count": 0,
                "relationships_count": 0,
                "potential_conflicts_count": 0,
                "response_chars": len(raw),
                "response_bytes": len(raw.encode("utf-8", errors="replace")),
                "error_code": "CONFLICT_INDEX_UNAVAILABLE",
            },
        )
        return raw
    selected_ids = [part.strip() for part in ids.split(",") if part.strip()]
    payload = resolve_conflicts(idx, selected_ids)
    payload["corpus_version"] = index_meta.get("corpus_version")
    raw = json.dumps(payload, ensure_ascii=False)
    duration_ms = int((time.perf_counter() - call_start) * 1000)
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    _emit_tool_completed(
        "detect_instruction_conflicts.completed",
        duration_ms,
        failure=False,
        args_key_payload={"ids": sorted(selected_ids)},
        payload={
            "checked_ids_count": summary.get("checked_count", 0),
            "missing_ids_count": summary.get("missing_count", 0),
            "relationships_count": summary.get("relationships_count", 0),
            "potential_conflicts_count": summary.get("potential_conflicts_count", 0),
            "response_chars": len(raw),
            "response_bytes": len(raw.encode("utf-8", errors="replace")),
            "corpus_version": payload.get("corpus_version"),
        },
    )
    return raw


def main() -> None:
    _configure_logging()
    telemetry.emit_server_start(os.environ.get("INSTRUCTIONS_ROOT", ""))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
