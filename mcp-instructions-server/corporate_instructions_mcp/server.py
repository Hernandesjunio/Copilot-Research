"""MCP stdio server exposing read-only tools over the instruction corpus."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

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
from corporate_instructions_mcp.paths import instruction_path_needle_is_safe, require_existing_dir

mcp = FastMCP(
    "corporate-instructions",
    instructions=(
        "Read-only catalog of organizational Copilot instructions. "
        "Native repo instructions override this catalog when they conflict."
    ),
)

_index: dict[str, InstructionRecord] = {}
_index_root: Path | None = None

log = logging.getLogger(__name__)


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


@mcp.tool()
def list_instructions_index() -> str:
    """Use when you need an overview of all available organizational instruction documents (ids, titles, tags).

    Returns lightweight metadata for every indexed .md file under INSTRUCTIONS_ROOT. Restart the server or
    set INSTRUCTIONS_ROOT to a new path to refresh. JSON array of objects.
    """
    idx = _ensure_index()
    out = []
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
    return json.dumps({"instructions": out, "count": len(out)}, ensure_ascii=False)


@mcp.tool()
def search_instructions(
    query: str,
    tags: str | None = None,
    max_results: int = 5,
) -> str:
    """Use when the user asks about architecture, patterns, DNS, security, style, or any org-specific guideline.

    Full-text style search (keyword overlap) over the instruction corpus. Prefer calling this before
    proposing cross-cutting design. Parameters: query (natural language), optional comma-separated tags
    filter, max_results (default 5, cap 10).
    """
    idx = _ensure_index()
    tokens = tokenize_query(query)
    tag_filter = _parse_tags(tags)
    cap = _clamp_int(max_results, default=5, lo=1, hi=10)

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
            }
        )
        composed_parts.append(f"### {rec.title} ({rec.id})\n{summarize_body(rec.body, 280)}")

    payload = {
        "results": results,
        "composed_context": "\n\n".join(composed_parts),
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def get_instruction(
    id: str | None = None,
    path: str | None = None,
    max_chars: int = 12000,
) -> str:
    """Use when search_instructions returned an id/path and you need the full instruction text.

    Fetch the complete markdown body (after frontmatter). Provide either id or path relative to INSTRUCTIONS_ROOT.
    max_chars truncates very large files (default 12000).
    """
    idx = _ensure_index()
    rec: InstructionRecord | None = None
    if id and str(id).strip():
        rec = idx.get(str(id).strip())
    elif path and str(path).strip():
        needle = str(path).strip().replace("\\", "/")
        if not instruction_path_needle_is_safe(needle):
            return json.dumps(
                {
                    "error": "Invalid path argument.",
                    "hint": (
                        "Use a relative path without '..' segments; prefer document id from list_instructions_index."
                    ),
                },
                ensure_ascii=False,
            )
        for candidate in idx.values():
            if candidate.rel_path == needle or candidate.rel_path.endswith("/" + needle):
                rec = candidate
                break
    else:
        return json.dumps(
            {"error": "Provide either id or path."},
            ensure_ascii=False,
        )

    if rec is None:
        return json.dumps(
            {"error": "Instruction not found.", "hint": "Call list_instructions_index or search_instructions."},
            ensure_ascii=False,
        )

    limit = _clamp_int(max_chars, default=12000, lo=500, hi=200_000)
    body = rec.body
    truncated = len(body) > limit
    if truncated:
        body = body[: limit - 20] + "\n\n… [truncated]"

    return json.dumps(
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
        },
        ensure_ascii=False,
    )


def main() -> None:
    _configure_logging()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
