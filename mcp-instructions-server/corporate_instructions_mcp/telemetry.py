"""Structured NDJSON telemetry on stderr for experiments and analysis (never stdout — MCP JSON-RPC)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

TELEMETRY_SCHEMA_VERSION = 2

TelemetryLevel = Literal["off", "minimal", "full"]

_lock = threading.Lock()
_call_seq = 0

# Process-scoped experiment session (stdio MCP process lifetime).
_session_id: str | None = None
_server_start_mono: float | None = None
_first_tool_mono: float | None = None
_last_tool_mono: float | None = None
_tool_calls_total = 0
_tool_calls_by_name: dict[str, int] = defaultdict(int)
_retries_total = 0
_retries_by_tool: dict[str, int] = defaultdict(int)
_tool_failures_total = 0
_session_seen_failure = False
_invocation_counts: dict[tuple[str, str], int] = {}
_index_rebuild_count = 0
_first_index_build_done = False
_corpus_policy_counts: dict[str, int] = {"workspace_evidence_required_true": 0, "total_indexed": 0}

# Ring buffer per tool for percentile telemetry (process lifetime).
_LATENCY_SAMPLES_CAP = 2000
_latency_by_tool: dict[str, list[int]] = defaultdict(list)
_first_relevant_search_recorded = False


def telemetry_level() -> TelemetryLevel:
    """CORPORATE_INSTRUCTIONS_TELEMETRY: off | minimal | full (unknown → off)."""
    raw = os.environ.get("CORPORATE_INSTRUCTIONS_TELEMETRY", "off").strip().lower()
    if raw in ("0", "false", "no", "off", ""):
        return "off"
    if raw == "full":
        return "full"
    if raw in ("1", "true", "yes", "minimal", "min"):
        return "minimal"
    return "off"


def _server_version() -> str:
    try:
        from importlib.metadata import version

        return version("corporate-instructions-mcp")
    except Exception:
        return "unknown"


def _next_seq() -> int:
    global _call_seq
    with _lock:
        _call_seq += 1
        return _call_seq


def session_id() -> str:
    """Stable id for this server process (override via CORPORATE_INSTRUCTIONS_SESSION_ID)."""
    global _session_id
    if _session_id is None:
        raw = os.environ.get("CORPORATE_INSTRUCTIONS_SESSION_ID", "").strip()
        _session_id = raw if raw else str(uuid.uuid4())
    return _session_id


def reset_session_counters_for_tests() -> None:
    """Test hook: clear session counters (not normally used in production)."""
    global _session_id, _server_start_mono, _first_tool_mono, _last_tool_mono
    global _tool_calls_total, _retries_total, _tool_failures_total, _session_seen_failure
    global _invocation_counts, _index_rebuild_count, _first_index_build_done, _retries_by_tool
    global _latency_by_tool, _first_relevant_search_recorded
    _session_id = None
    _server_start_mono = None
    _first_tool_mono = None
    _last_tool_mono = None
    _tool_calls_total = 0
    _tool_calls_by_name = defaultdict(int)
    _retries_total = 0
    _retries_by_tool = defaultdict(int)
    _tool_failures_total = 0
    _session_seen_failure = False
    _invocation_counts = {}
    _index_rebuild_count = 0
    _first_index_build_done = False
    _latency_by_tool = defaultdict(list)
    _first_relevant_search_recorded = False


def _append_latency_sample(tool: str, duration_ms: int) -> None:
    lst = _latency_by_tool[tool]
    lst.append(duration_ms)
    overflow = len(lst) - _LATENCY_SAMPLES_CAP
    if overflow > 0:
        del lst[:overflow]


def index_rebuild_count() -> int:
    with _lock:
        return _index_rebuild_count


def commit_first_relevant_search_if_needed() -> dict[str, Any]:
    global _first_relevant_search_recorded
    if telemetry_level() == "off" or _first_relevant_search_recorded:
        return {}
    _first_relevant_search_recorded = True
    start = _server_start_mono
    now = time.perf_counter()
    if start is None:
        return {}
    return {
        "time_to_first_relevant_instruction_ms": int((now - start) * 1000),
        "first_relevant_instruction_observed": True,
    }


def latency_percentiles_snapshot(tool: str) -> dict[str, Any]:
    """p50 / p95 / p99 and max for one tool (cumulative in this process)."""
    lst = sorted(_latency_by_tool.get(tool, []))
    if not lst:
        return {}
    n = len(lst)

    def pct(p: float) -> float:
        if n == 1:
            return float(lst[0])
        idx = min(n - 1, max(0, int(round((n - 1) * p))))
        return float(lst[idx])

    return {
        "latency_p50_ms": pct(0.50),
        "latency_p95_ms": pct(0.95),
        "latency_p99_ms": pct(0.99),
        "max_latency_ms": float(lst[-1]),
        "latency_samples": n,
    }


def _ensure_server_clock() -> None:
    global _server_start_mono
    if _server_start_mono is None:
        _server_start_mono = time.perf_counter()


def set_corpus_governance_snapshot(policies_workspace_evidence_required: int, total_indexed: int) -> None:
    """After index build: corpus-wide counts from frontmatter (best-effort)."""
    global _corpus_policy_counts
    _corpus_policy_counts["workspace_evidence_required_true"] = policies_workspace_evidence_required
    _corpus_policy_counts["total_indexed"] = total_indexed


def args_fingerprint(payload: dict[str, Any]) -> str:
    """Stable hash for retry detection (order keys for determinism)."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def register_tool_completion(
    tool: str,
    duration_ms: int,
    *,
    failure: bool,
    args_key: str,
) -> dict[str, Any]:
    """Update session aggregates; returns fields merged into tool telemetry events."""
    global _first_tool_mono, _last_tool_mono, _tool_calls_total, _tool_failures_total
    global _session_seen_failure, _retries_total, _retries_by_tool

    _ensure_server_clock()
    _append_latency_sample(tool, duration_ms)
    now = time.perf_counter()
    with _lock:
        _tool_calls_total += 1
        _tool_calls_by_name[tool] += 1
        if failure:
            _tool_failures_total += 1
            _session_seen_failure = True
        prev = _invocation_counts.get((tool, args_key), 0)
        _invocation_counts[(tool, args_key)] = prev + 1
        repeat_index = prev + 1
        is_retry = prev > 0
        retry_increment = 1 if is_retry else 0
        _retries_total += retry_increment
        if is_retry:
            _retries_by_tool[tool] += 1

        if _first_tool_mono is None:
            _first_tool_mono = now
        _last_tool_mono = now

        first_mono = _first_tool_mono
        start_mono = _server_start_mono
        tc_total = _tool_calls_total
        tf_total = _tool_failures_total
        tr_total = _retries_total
        tc_by_name = dict(_tool_calls_by_name)
        tr_by_name = dict(_retries_by_tool)

    first_to_last_ms = int((now - first_mono) * 1000)
    server_uptime_ms = int((now - start_mono) * 1000) if start_mono is not None else 0

    tool_failure_rate = tf_total / max(1, tc_total)
    retry_rate = tr_total / max(1, tc_total)
    lat_snap = latency_percentiles_snapshot(tool)

    return {
        "tool": tool,
        "tool_latency_ms": duration_ms,
        **lat_snap,
        "tool_call_repeat_index": repeat_index,
        "is_retry_or_repeat_call": is_retry,
        "retry_increment": retry_increment,
        "session_duration_ms": first_to_last_ms,
        "first_tool_to_last_tool_ms": first_to_last_ms,
        "server_uptime_ms": server_uptime_ms,
        "tool_calls_total": tc_total,
        "tool_calls_by_name": tc_by_name,
        "avg_tool_calls_per_task": float(tc_total),
        "retries_total": tr_total,
        "retries_by_tool": tr_by_name,
        "retry_rate": round(retry_rate, 6),
        "tool_failures_total": tf_total,
        "tool_failure_rate": round(tool_failure_rate, 6),
        "sessions_with_any_failure": _session_seen_failure,
    }


def emit_event(event: str, payload: dict[str, Any]) -> None:
    """Emit one NDJSON line to stderr. No-op when telemetry is off."""
    if telemetry_level() == "off":
        return
    now = datetime.now(timezone.utc)
    ts = now.isoformat().replace("+00:00", "Z")
    record: dict[str, Any] = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "event": event,
        "ts": ts,
        "server_version": _server_version(),
        "process_id": os.getpid(),
        "call_seq": _next_seq(),
        "telemetry": telemetry_level(),
        "session_id": session_id(),
        **payload,
    }
    line = json.dumps(record, ensure_ascii=False) + "\n"
    sys.stderr.write(line)
    sys.stderr.flush()


def instructions_root_label(path: Path | str) -> str:
    """Minimal: directory name only. Full: resolved absolute path."""
    p = Path(path)
    if telemetry_level() == "full":
        try:
            return str(p.resolve())
        except OSError:
            return str(p)
    return p.name


def query_fingerprint(query: str) -> str:
    """SHA-256 of normalized query (whitespace-collapsed, lowercased)."""
    normalized = " ".join(str(query).split()).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def emit_server_start(instructions_root_raw: str) -> None:
    if telemetry_level() == "off":
        return
    _ensure_server_clock()
    session_id()  # pin id early for logs
    label = ""
    if instructions_root_raw.strip():
        label = instructions_root_label(instructions_root_raw.strip())
    emit_event(
        "server_start",
        {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "instructions_root_label": label,
        },
    )


def emit_index_rebuilt(
    root: Path,
    instruction_count: int,
    duration_ms: int,
    *,
    index_size_estimate_bytes: int = 0,
    policies_workspace_evidence_required_count: int = 0,
) -> None:
    """Emit index rebuild; also updates process-level rebuild counter."""
    global _index_rebuild_count, _first_index_build_done
    if telemetry_level() == "off":
        return
    with _lock:
        _index_rebuild_count += 1
        ibc = _index_rebuild_count
        _first_index_build_done = True
    cold_start = ibc == 1
    emit_event(
        "index_rebuilt",
        {
            "instructions_root_label": instructions_root_label(root),
            "documents_indexed_count": instruction_count,
            "instruction_count": instruction_count,
            "index_rebuild_duration_ms": duration_ms,
            "duration_ms": duration_ms,
            "index_rebuild_count": ibc,
            "cold_start": cold_start,
            "index_size_estimate_bytes": index_size_estimate_bytes,
            "corpus_policies_workspace_evidence_required_count": policies_workspace_evidence_required_count,
        },
    )


def emit_tool_invocation(
    tool: str,
    duration_ms: int,
    args_summary: dict[str, Any],
    result_summary: dict[str, Any],
) -> None:
    if telemetry_level() == "off":
        return
    emit_event(
        "tool_invocation",
        {
            "tool": tool,
            "duration_ms": duration_ms,
            "args_summary": args_summary,
            "result_summary": result_summary,
        },
    )


def search_args_summary(query: str, tags: str | None, max_results: object) -> dict[str, Any]:
    """Args metadata for search_instructions (no raw query in minimal)."""
    level = telemetry_level()
    cap = _clamp_optional_int(max_results, default=10, lo=1, hi=20)
    out: dict[str, Any] = {
        "query_sha256": query_fingerprint(query),
        "tags_filter_present": bool(tags and str(tags).strip()),
        "max_results": cap,
    }
    if level == "full":
        q = str(query)
        out["query_preview"] = q[:2048] + ("…" if len(q) > 2048 else "")
        if tags is not None:
            out["tags"] = str(tags)[:512]
    return out


def get_batch_args_summary(ids: str, max_chars_per_instruction: object) -> dict[str, Any]:
    level = telemetry_level()
    raw = str(ids).strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    out: dict[str, Any] = {
        "ids_order": parts[:50],
        "requested_id_count": len(parts),
    }
    m = _clamp_optional_int(max_chars_per_instruction, default=8000, lo=500, hi=200_000)
    out["max_chars_per_instruction"] = m
    if level == "full" and len(parts) > 50:
        out["ids_order_note"] = f"truncated_to_50_of_{len(parts)}"
    return out


def _clamp_optional_int(value: object, default: int, lo: int, hi: int) -> int:
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
