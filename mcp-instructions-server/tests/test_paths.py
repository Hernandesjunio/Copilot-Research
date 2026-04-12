"""Tests for path validation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from corporate_instructions_mcp.paths import (
    instruction_path_needle_is_safe,
    is_path_under_root,
    require_existing_dir,
)


def test_require_existing_dir_ok(tmp_path: Path) -> None:
    d = tmp_path / "corpus"
    d.mkdir()
    assert require_existing_dir(str(d)) == d.resolve()


def test_require_existing_dir_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        require_existing_dir("  ")


def test_require_existing_dir_missing_raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with pytest.raises(ValueError, match="not a directory"):
        require_existing_dir(str(missing))


def test_instruction_path_needle_is_safe() -> None:
    assert instruction_path_needle_is_safe("docs/guide.md") is True
    assert instruction_path_needle_is_safe("") is False
    assert instruction_path_needle_is_safe("/etc/passwd") is False
    assert instruction_path_needle_is_safe("../secret.md") is False
    assert instruction_path_needle_is_safe("foo/../bar.md") is False


def test_is_path_under_root(tmp_path: Path) -> None:
    root = tmp_path / "r"
    root.mkdir()
    inner = root / "a" / "b"
    inner.mkdir(parents=True)
    f = inner / "x.md"
    f.write_text("x", encoding="utf-8")
    assert is_path_under_root(f, root) is True
