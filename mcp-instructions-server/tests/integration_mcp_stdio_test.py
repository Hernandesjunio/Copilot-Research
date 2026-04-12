"""Integration test: spawn the real MCP server over stdio and call tools."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Repo root = Copilot-Research (parent of mcp-instructions-server)
_SERVER_DIR = Path(__file__).resolve().parents[1]
_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


def _corpus_root() -> Path:
    """Default: repo fixtures. Override with INSTRUCTIONS_ROOT to test your own corpus."""
    override = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _FIXTURES.resolve()


def _tool_text(result) -> str:
    assert not result.isError, getattr(result, "content", result)
    assert result.content, "tool returned no content"
    block = result.content[0]
    assert hasattr(block, "text"), block
    return block.text


def test_mcp_stdio_list_search_get_instruction():
    """End-to-end: subprocess runs FastMCP; client exercises the three tools."""

    corpus = _corpus_root()
    use_fixture_expectations = corpus == _FIXTURES.resolve()

    async def _run() -> None:
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
            names = {t.name for t in listed.tools}
            assert names == {"get_instruction", "list_instructions_index", "search_instructions"}

            raw = _tool_text(await session.call_tool("list_instructions_index", {}))
            index = json.loads(raw)
            assert index["count"] >= 1, f"no .md indexed under {corpus}"
            ids = {x["id"] for x in index["instructions"]}

            if use_fixture_expectations:
                assert index["count"] >= 3
                expected_ids = {"dns-retry-pattern", "security-baseline-secrets", "csharp-async-style"}
                assert expected_ids.issubset(ids)

            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "retry DNS polly", "max_results": 3},
                )
            )
            search = json.loads(raw)
            assert "composed_context" in search
            if use_fixture_expectations:
                assert search["results"]
                assert search["results"][0]["id"] == "dns-retry-pattern"

            fetch_id = (
                "dns-retry-pattern"
                if use_fixture_expectations and "dns-retry-pattern" in ids
                else index["instructions"][0]["id"]
            )
            raw = _tool_text(await session.call_tool("get_instruction", {"id": fetch_id}))
            doc = json.loads(raw)
            assert doc.get("id") == fetch_id
            assert isinstance(doc.get("content"), str) and len(doc["content"]) > 0
            if use_fixture_expectations and fetch_id == "dns-retry-pattern":
                assert "Polly" in doc["content"]

    asyncio.run(_run())
