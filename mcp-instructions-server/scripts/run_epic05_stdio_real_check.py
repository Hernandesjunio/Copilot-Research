"""Run a real MCP stdio consumption check for EPIC-05 requirements."""

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


def _corpus_root() -> Path:
    override = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_FIXTURES.resolve()


def _tool_text(result: Any) -> str:
    if result.isError:
        raise RuntimeError(f"Tool returned isError=True: {result.content!r}")
    if not result.content:
        raise RuntimeError("Tool returned empty content.")
    block = result.content[0]
    if not hasattr(block, "text"):
        raise RuntimeError(f"Unexpected MCP content block: {block!r}")
    return cast(str, block.text)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def _run() -> dict[str, Any]:
    corpus = _corpus_root()
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "corporate_instructions_mcp"],
        cwd=str(_SERVER_DIR),
        env={**os.environ, "INSTRUCTIONS_ROOT": str(corpus)},
    )
    summary: dict[str, Any] = {"corpus_root": str(corpus), "checks": []}
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        listed = await session.list_tools()
        names = {tool.name for tool in listed.tools}
        expected = {
            "list_instructions_index",
            "search_instructions",
            "get_instructions_batch",
        }
        _assert(names == expected, f"MCP tools must be exactly {sorted(expected)!r}, got {sorted(names)!r}.")
        summary["checks"].append({"name": "tools_list", "ok": True, "details": {"tools_count": len(names)}})

        index_raw = _tool_text(await session.call_tool("list_instructions_index", {}))
        index_data = json.loads(index_raw)
        _assert(
            index_data.get("index_status") in {"ok", "partial"},
            "list_instructions_index index_status should be ok/partial.",
        )
        _assert("index_health" in index_data, "list_instructions_index must include index_health.")
        _assert("warnings" in index_data and "errors" in index_data, "list_instructions_index must include warnings/errors.")
        summary["checks"].append(
            {
                "name": "list_instructions_index_health",
                "ok": True,
                "details": {
                    "index_status": index_data.get("index_status"),
                    "total_indexed": index_data.get("total_indexed"),
                    "warnings": len(index_data.get("warnings", [])),
                },
            }
        )

        multi_raw = _tool_text(
            await session.call_tool(
                "search_instructions",
                {
                    "query": "",
                    "queries": [
                        "minimal api rest status codes",
                        "response envelope global error handling",
                    ],
                    "max_results_per_query": 3,
                    "include_diagnostics": True,
                },
            )
        )
        multi_data = json.loads(multi_raw)
        _assert(isinstance(multi_data.get("queries"), list), "search_instructions multi-query must return queries list.")
        consolidated = multi_data.get("consolidated", {})
        _assert(isinstance(consolidated.get("top_policies"), list), "Missing consolidated.top_policies.")
        _assert(isinstance(consolidated.get("top_references"), list), "Missing consolidated.top_references.")
        _assert(isinstance(consolidated.get("coverage_gaps"), list), "Missing consolidated.coverage_gaps.")
        summary["checks"].append(
            {
                "name": "search_instructions_multi_query",
                "ok": True,
                "details": {
                    "queries_count": len(multi_data.get("queries", [])),
                    "top_policies": len(consolidated.get("top_policies", [])),
                    "top_references": len(consolidated.get("top_references", [])),
                },
            }
        )

    os.environ["INSTRUCTIONS_ROOT"] = str(corpus)
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None
    from corporate_instructions_mcp.server import (
        build_compliance_matrix,
        resolve_instruction_context,
        validate_applicability,
    )

    applicability_raw = validate_applicability(
        instruction_ids=["microservice-authorization-resource-scope-and-audit"],
        target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
        workspace_evidence=["HttpContext.User"],
    )
    applicability_data = json.loads(applicability_raw)
    decision = applicability_data["results"][0]["applicability"]
    _assert(decision == "applicable", "validate_applicability should return applicable for positive evidence.")
    summary["checks"].append({"name": "validate_applicability_positive", "ok": True, "details": {"decision": decision}})

    matrix_raw = build_compliance_matrix(
        target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
        instruction_results=[
            {
                "instruction_id": "microservice-authorization-resource-scope-and-audit",
                "kind": "policy",
                "applicability": "applicable",
                "reason": "Artifact in scope with evidence.",
            }
        ],
        artifact_observations=[
            {
                "instruction_id": "microservice-authorization-resource-scope-and-audit",
                "observation_type": "positive",
                "value": "Authorization requirement found.",
            },
            {
                "instruction_id": "microservice-authorization-resource-scope-and-audit",
                "observation_type": "gap",
                "value": "Audit metadata still missing.",
            },
        ],
    )
    matrix_data = json.loads(matrix_raw)
    matrix_status = matrix_data["matrix"][0]["status"]
    _assert(matrix_status == "partial_conformance", "build_compliance_matrix should return partial_conformance here.")
    summary["checks"].append({"name": "build_compliance_matrix_partial", "ok": True, "details": {"status": matrix_status}})

    resolved_raw = resolve_instruction_context(
        query="authorization owner audit endpoint",
        max_results=3,
        include_diagnostics=True,
    )
    resolved_data = json.loads(resolved_raw)
    resolution = resolved_data.get("resolution", {})
    for key in (
        "selection_rationale",
        "pending_evidence",
        "required_workspace_signals",
        "next_repo_evidence_actions",
    ):
        _assert(key in resolution, f"resolve_instruction_context missing P1 field: {key}")
    summary["checks"].append({"name": "resolve_instruction_context_p1_fields", "ok": True})

    summary["ok"] = True
    return summary


def main() -> None:
    summary = asyncio.run(_run())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
