"""Tests for NDJSON telemetry on stderr (CORPORATE_INSTRUCTIONS_TELEMETRY)."""

from __future__ import annotations

import io
import json
from collections.abc import Generator
from contextlib import redirect_stderr
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


@pytest.fixture(autouse=True)
def _env_and_reset_index(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    yield


def _json_lines(stderr: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        out.append(json.loads(line))
    return out


def test_telemetry_off_emits_no_ndjson(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "off")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp.telemetry import emit_event

        emit_event("test_event", {"hello": "world"})
    assert buf.getvalue() == ""


def test_telemetry_minimal_list_instructions_emits_structured_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "minimal")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp.server import list_instructions_index

        list_instructions_index()

    lines = _json_lines(buf.getvalue())
    types = [str(x.get("event")) for x in lines]
    assert "index_rebuilt" in types
    assert "list_instructions_index.completed" in types
    tool_lines = [x for x in lines if x.get("event") == "list_instructions_index.completed"]
    assert len(tool_lines) == 1
    inv = tool_lines[0]
    assert inv.get("schema_version") == 2
    assert inv.get("session_id")
    assert inv.get("unique_instruction_ids_count", 0) >= 3
    assert "by_tag_count" in inv or "instructions_by_tag" in inv


def test_telemetry_minimal_search_has_query_sha256_not_raw_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "minimal")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp.server import search_instructions

        search_instructions(query="retry DNS polly", max_results=3)

    lines = _json_lines(buf.getvalue())
    inv = next(x for x in lines if x.get("event") == "search_instructions.completed")
    args = inv.get("args_summary")
    assert isinstance(args, dict)
    assert "query_sha256" in args
    assert len(str(args.get("query_sha256"))) == 64
    assert "query_preview" not in args


def test_telemetry_full_includes_query_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "full")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp.server import search_instructions

        search_instructions(query="microservice test query", max_results=2)

    lines = _json_lines(buf.getvalue())
    inv = next(x for x in lines if x.get("event") == "search_instructions.completed")
    args = inv.get("args_summary")
    assert isinstance(args, dict)
    assert args.get("query_preview")


def test_telemetry_minimal_get_batch_result_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "minimal")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp.server import get_instructions_batch

        get_instructions_batch(ids="dns-retry-pattern", max_chars_per_instruction=500)

    lines = _json_lines(buf.getvalue())
    inv = next(x for x in lines if x.get("event") == "get_instructions_batch.completed")
    assert inv.get("tool") == "get_instructions_batch"
    assert inv.get("returned_ids_count") == 1
    assert inv.get("requested_ids_count") == 1
    assert inv.get("missing_ids_count") == 0
    assert inv.get("batch_chars_total", 0) > 0


def test_server_start_single_emit(monkeypatch: pytest.MonkeyPatch) -> None:
    """emit_server_start produces one NDJSON line with corpus label (basename in minimal)."""
    monkeypatch.setenv("CORPORATE_INSTRUCTIONS_TELEMETRY", "minimal")
    buf = io.StringIO()
    with redirect_stderr(buf):
        from corporate_instructions_mcp import telemetry

        telemetry.emit_server_start(str(_FIXTURES))
    lines = _json_lines(buf.getvalue())
    assert len(lines) == 1
    assert lines[0].get("event") == "server_start"
    assert lines[0].get("instructions_root_label") == _FIXTURES.name
