#!/usr/bin/env python3
"""Bump the first `version = \"X.Y.Z\"` line in a pyproject.toml (semver)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def bump(current: str, kind: str) -> str:
    parts = current.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"expected semver X.Y.Z, got {current!r}")
    major, minor, patch = (int(parts[0]), int(parts[1]), int(parts[2]))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "build":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump kind: {kind!r} (use build, minor, major)")


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: bump_pyproject_version.py <pyproject.toml> <build|minor|major>", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    kind = sys.argv[2]
    text = path.read_text(encoding="utf-8")

    m = re.search(r"^version\s*=\s*\"([^\"]+)\"\s*$", text, flags=re.MULTILINE)
    if not m:
        print("error: no `version = \"...\"` line found", file=sys.stderr)
        sys.exit(1)

    new_ver = bump(m.group(1), kind)
    new_text = re.sub(
        r"^version\s*=\s*\"[^\"]+\"\s*$",
        f'version = "{new_ver}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(new_ver)


if __name__ == "__main__":
    main()
