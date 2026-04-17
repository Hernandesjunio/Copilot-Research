"""Print tools/list from the real stdio server (JSON) for IDE bug reports or diffing hosts.

Run from mcp-instructions-server/:

  set INSTRUCTIONS_ROOT=C:\\path\\to\\corpus
  python scripts/print_mcp_tools_list.py

Uses the same Python as the current process (set command to this executable in the IDE MCP JSON).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

_SERVER_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_FIXTURES = _SERVER_DIR.parent / "fixtures" / "instructions"


def _corpus_root() -> Path:
    raw = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_FIXTURES.resolve()


async def _run() -> None:
    corpus = _corpus_root()
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "corporate_instructions_mcp"],
        cwd=str(_SERVER_DIR),
        env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        listed = await session.list_tools()
        payload = []
        for t in sorted(listed.tools, key=lambda x: x.name):
            entry: dict[str, object] = {"name": t.name, "description": t.description or ""}
            if t.inputSchema:
                entry["inputSchema"] = t.inputSchema
            payload.append(entry)
        print(json.dumps({"INSTRUCTIONS_ROOT": str(corpus), "tools": payload}, ensure_ascii=False, indent=2))


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
