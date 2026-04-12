"""Unit tests for indexing helpers (pure logic, no MCP runtime)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from corporate_instructions_mcp import indexing
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
        (root / "a.md").write_text("---\nid: dup\ntitle: A\n---\nbody", encoding="utf-8")
        (root / "b.md").write_text("---\nid: dup\ntitle: B\n---\nbody", encoding="utf-8")
        with pytest.raises(ValueError, match="Duplicate instruction id"):
            build_index(root)


def test_build_index_missing_dir_returns_empty():
    missing = Path(tempfile.gettempdir()) / "nonexistent_instructions_root_xyz"
    assert build_index(missing) == {}


def test_build_index_skips_huge_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(indexing, "MAX_INSTRUCTION_FILE_BYTES", 80)
    (tmp_path / "ok.md").write_text("---\nid: ok\ntitle: OK\n---\nbody", encoding="utf-8")
    (tmp_path / "big.md").write_text("---\nid: big\ntitle: B\n---\n" + "x" * 200, encoding="utf-8")
    idx = build_index(tmp_path)
    assert set(idx) == {"ok"}


def test_build_index_skips_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("---\nid: leak\ntitle: X\n---\n", encoding="utf-8")
    root = tmp_path / "inst"
    root.mkdir()
    (root / "good.md").write_text("---\nid: g\ntitle: G\n---\n", encoding="utf-8")
    link = root / "bad.md"
    try:
        link.symlink_to(outside / "secret.md")
    except OSError:
        if os.name == "nt":
            pytest.skip("symlink creation not permitted")
        raise
    idx = build_index(root)
    assert "g" in idx
    assert "leak" not in idx


def test_build_index_skips_huge_frontmatter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(indexing, "MAX_FRONTMATTER_SECTION_CHARS", 20)
    (tmp_path / "huge_fm.md").write_text(
        "---\n" + "x" * 100 + "\n---\nbody",
        encoding="utf-8",
    )
    idx = build_index(tmp_path)
    assert len(idx) == 1
    rec = next(iter(idx.values()))
    assert rec.raw_frontmatter == {}
    assert "body" in rec.body


def test_yaml_non_dict_frontmatter_treated_as_empty(tmp_path: Path) -> None:
    (tmp_path / "list_fm.md").write_text("---\n- a\n- b\n---\nbody", encoding="utf-8")
    idx = build_index(tmp_path)
    rec = idx[next(iter(idx))]
    assert rec.raw_frontmatter == {}
    assert rec.id == "list_fm"
    assert rec.body == "body"
