"""Unit tests for indexing helpers (pure logic, no MCP runtime)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from corporate_instructions_mcp.indexing import (
    InstructionRecord,
    build_index,
    excerpt_around_match,
    score_record,
    summarize_body,
    tokenize_query,
)


def test_tokenize_query_drops_short_and_splits():
    assert tokenize_query("a BC de-f") == ["bc", "de"]


def test_summarize_body_truncates():
    long = "word " * 100
    out = summarize_body(long, limit=30)
    assert len(out) <= 30
    assert out.endswith("...")


def test_excerpt_around_match_prefers_token_hit():
    body = "intro " * 50 + "needle" + " tail " * 50
    ex = excerpt_around_match(body, ["needle"], max_len=80)
    assert "needle" in ex


def test_score_record_respects_tag_filter():
    rec = InstructionRecord(
        id="x",
        rel_path="x.md",
        title="Alpha",
        tags=["api"],
        scope=None,
        priority="high",
        kind="reference",
        body="hello world",
        content_hash="0" * 64,
    )
    tokens = ["hello"]
    assert score_record(rec, tokens, {"api"}) > 0
    assert score_record(rec, tokens, {"other"}) == 0.0


def test_build_index_duplicate_id_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.md").write_text(
            "---\nid: dup\ntitle: A\n---\nbody", encoding="utf-8"
        )
        (root / "b.md").write_text(
            "---\nid: dup\ntitle: B\n---\nbody", encoding="utf-8"
        )
        with pytest.raises(ValueError, match="Duplicate instruction id"):
            build_index(root)


def test_build_index_missing_dir_returns_empty():
    missing = Path(tempfile.gettempdir()) / "nonexistent_instructions_root_xyz"
    assert build_index(missing) == {}
