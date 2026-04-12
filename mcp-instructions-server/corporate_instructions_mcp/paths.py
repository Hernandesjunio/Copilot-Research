"""Path validation for instruction corpus roots and tool arguments."""

from __future__ import annotations

from pathlib import Path


def require_existing_dir(raw: str) -> Path:
    """Resolve ``raw`` to an absolute path and require that it is an existing directory.

    Raises:
        ValueError: If ``raw`` is empty or the path is not a directory.
    """
    text = str(raw).strip()
    if not text:
        msg = "INSTRUCTIONS_ROOT is empty."
        raise ValueError(msg)
    root = Path(text).expanduser().resolve()
    if not root.is_dir():
        msg = f"INSTRUCTIONS_ROOT is not a directory or does not exist: {root}"
        raise ValueError(msg)
    return root


def is_path_under_root(path: Path, root: Path) -> bool:
    """Return True if ``path`` resolves to a location inside ``root`` (inclusive).

    Used to skip symlink escapes when indexing the corpus.
    """
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    else:
        return True


def instruction_path_needle_is_safe(needle: str) -> bool:
    """Return False for absolute paths, empty needles, or ``..`` segments.

    ``needle`` is a POSIX-style relative path as provided to ``get_instruction``.
    """
    n = str(needle).strip().replace("\\", "/")
    if not n or n.startswith("/"):
        return False
    p = Path(n)
    if p.is_absolute():
        return False
    return ".." not in p.parts
