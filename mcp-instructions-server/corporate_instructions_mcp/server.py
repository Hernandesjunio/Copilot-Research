"""MCP stdio server exposing read-only tools over the instruction corpus."""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from corporate_instructions_mcp.indexing import (
    PRIORITY_RANK,
    InstructionRecord,
    build_index,
    excerpt_around_match,
    score_record,
    summarize_body,
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

    return _convert(meta)


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


def _ensure_index() -> dict[str, InstructionRecord]:
    global _index, _index_root
    root = _root()
    if _index_root != root or not _index:
        log.info("rebuilding_index root=%s", root)
        _index = build_index(root)
        _index_root = root
    return _index


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
    idx = _ensure_index()
    out = []
    by_tag: dict[str, list[str]] = {}
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
        for tag in rec.tags:
            by_tag.setdefault(tag, []).append(rec.id)
    by_tag = {tag: sorted(ids) for tag, ids in sorted(by_tag.items())}
    return json.dumps({"instructions": out, "count": len(out), "by_tag": by_tag}, ensure_ascii=False)


@mcp.tool()
def search_instructions(
    query: str,
    tags: str | None = None,
    max_results: int = 10,
) -> str:
    """Use when the user asks about architecture, patterns, DNS, security, style, or any org-specific guideline.

    Full-text style search (keyword overlap) over the instruction corpus. Prefer calling this before
    proposing cross-cutting design. Parameters: query (natural language), optional comma-separated tags
    filter, max_results (default 10, cap 20).
    """
    idx = _ensure_index()
    tokens = tokenize_query(query)
    tag_filter = _parse_tags(tags)
    cap = _clamp_int(max_results, default=10, lo=1, hi=20)

    if not tokens:
        if not tag_filter:
            return json.dumps(
                {
                    "results": [],
                    "composed_context": "",
                    "note": "Provide a non-empty query or use tags= to filter by comma-separated tags.",
                },
                ensure_ascii=False,
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
        return json.dumps(
            {
                "results": [],
                "composed_context": "",
                "note": "No matches; refine query or use list_instructions_index.",
            },
            ensure_ascii=False,
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

    payload = {
        "results": results,
        "composed_context": "\n\n".join(composed_parts),
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def get_instructions_batch(
    ids: str,
    max_chars_per_instruction: int = 8000,
) -> str:
    """Fetch multiple instructions in one call. Parameter ids: comma-separated instruction ids.

    Call after list_instructions_index or search_instructions when full bodies are needed.
    Each returned item includes a frontmatter object (parsed YAML header, JSON-safe).
    """
    idx = _ensure_index()
    requested_ids = [candidate.strip() for candidate in str(ids).split(",") if candidate.strip()]
    if not requested_ids:
        return json.dumps(
            {"error": "Provide at least one instruction id."},
            ensure_ascii=False,
        )

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

    return json.dumps(
        {
            "instructions": items,
            "requested_count": len(requested_ids),
            "found_count": len(items),
            "missing_ids": missing_ids,
            "skipped_ids_due_to_total_cap": skipped_ids_due_to_total_cap,
            "max_chars_per_instruction": per_instruction_limit,
            "max_total_chars": MAX_BATCH_TOTAL_CHARS,
        },
        ensure_ascii=False,
    )


def main() -> None:
    _configure_logging()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
