"""Spawn real MCP (stdio) and run list_instructions_index with varied args (smoke / manual)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

_SERVER_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_FIXTURES = _SERVER_DIR.parent / "fixtures" / "instructions"

# At least 10 distinct query shapes across fields (ADR-003 / EPIC-11).
BATTERY: list[dict[str, Any]] = [
    {},  # defaults
    {"limit": 5, "offset": 0},
    {"limit": 3, "offset": 5},
    {"tags": "security,microservice", "tags_mode": "any"},
    {"tags": "security,microservice", "tags_mode": "all"},
    {"kind": "policy"},
    {"kind": "reference"},
    {"priority": "high"},
    {"scope": "**/*.cs"},
    {"status": "active"},
    {"owner": "platform-architecture"},
    {"workspace_evidence_required": True},
    {"include_facets": True, "limit": 0},
    {"current_file_path": "src/Api/Foo.cs"},
    {"current_file_path": "docs/README.md", "include_non_matching_global": True},
    {"kind": "policy", "priority": "high", "tags": "microservice", "current_file_path": "Api/Endpoints/X.cs"},
]


def _corpus_root() -> Path:
    raw = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_FIXTURES.resolve()


async def _run() -> list[dict[str, Any]]:
    corpus = _corpus_root()
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "corporate_instructions_mcp"],
        cwd=str(_SERVER_DIR),
        env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
    )
    rows: list[dict[str, Any]] = []
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        for args in BATTERY:
            result = await session.call_tool("list_instructions_index", args)
            if result.isError:
                rows.append(
                    {
                        "args": args,
                        "ok": False,
                        "error": getattr(result, "content", str(result)),
                    }
                )
                continue
            block = result.content[0]
            text = cast(str, block.text)
            payload = json.loads(text)
            ok = payload.get("ok") is not False and payload.get("error_code") is None
            rows.append(
                {
                    "args": args,
                    "ok": ok,
                    "index_status": payload.get("index_status"),
                    "total_indexed": payload.get("total_indexed"),
                    "total_matched": payload.get("total_matched"),
                    "items_len": len(payload.get("items") or []),
                    "has_facets": "facets" in payload,
                    "error_code": payload.get("error_code"),
                }
            )
    return rows


def main() -> None:
    summary = asyncio.run(_run())
    errors = [r for r in summary if not r.get("ok")]
    print(json.dumps({"corpus": str(_corpus_root()), "calls": len(summary), "errors_count": len(errors), "results": summary}, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
