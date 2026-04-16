"""Integration test: spawn the real MCP server over stdio and call tools."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

import pytest
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


def _tool_text(result: Any) -> str:
    assert not result.isError, getattr(result, "content", result)
    assert result.content, "tool returned no content"
    block = result.content[0]
    assert hasattr(block, "text"), block
    return cast(str, block.text)


def test_mcp_stdio_list_search_get_instruction() -> None:
    """End-to-end: subprocess runs FastMCP; client exercises MCP tools."""

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
            assert names == {
                "get_instructions_batch",
                "list_instructions_index",
                "search_instructions",
            }

            raw = _tool_text(await session.call_tool("list_instructions_index", {}))
            index = json.loads(raw)
            assert index["count"] >= 1, f"no .md indexed under {corpus}"
            assert "by_tag" in index
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
            batch_ids = ",".join(
                [
                    fetch_id,
                    "microservice-rest-http-semantics-and-status-codes" if use_fixture_expectations else fetch_id,
                ]
            )
            raw = _tool_text(await session.call_tool("get_instructions_batch", {"ids": batch_ids}))
            batch = json.loads(raw)
            assert batch["found_count"] >= 1
            assert isinstance(batch["instructions"], list)
            first = batch["instructions"][0]
            assert first.get("id") == fetch_id
            assert isinstance(first.get("content"), str) and len(first["content"]) > 0
            if use_fixture_expectations and fetch_id == "dns-retry-pattern":
                assert "Polly" in first["content"]

    asyncio.run(_run())


def test_mcp_stdio_search_default_max_persistencia_sql_and_related_ids() -> None:
    """M4, I1, I2: STDIO path matches smoke — default max_results=10, persistência SQL hit, related_ids present."""

    corpus = _corpus_root()
    use_fixture_expectations = corpus == _FIXTURES.resolve()
    if not use_fixture_expectations:
        pytest.skip("fixture-only expectations (INSTRUCTIONS_ROOT override)")

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

            raw = _tool_text(await session.call_tool("list_instructions_index", {}))
            index = json.loads(raw)
            assert index["count"] >= 3
            assert "by_tag" in index

            # M4: omit max_results → default 10
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "microservice"},
                )
            )
            micro = json.loads(raw)
            assert len(micro["results"]) == 10

            # I1: synonym / domain query finds data-access (same as smoke)
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "persistência SQL"},
                )
            )
            persist = json.loads(raw)
            ids = {r["id"] for r in persist["results"]}
            assert "microservice-data-access-and-sql-security" in ids
            assert persist.get("composed_context", "").strip() != ""

            # I2: multi-hit search; top result carries related_ids (discoverability contract)
            raw = _tool_text(
                await session.call_tool(
                    "search_instructions",
                    {"query": "retry DNS polly", "max_results": 3},
                )
            )
            dns = json.loads(raw)
            assert dns["results"]
            first = dns["results"][0]
            assert first["id"] == "dns-retry-pattern"
            assert "related_ids" in first
            assert isinstance(first["related_ids"], list)
            assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in first["related_ids"]

    asyncio.run(_run())
