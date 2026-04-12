"""Index Markdown instruction files: frontmatter, body, and lightweight search."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from corporate_instructions_mcp.paths import is_path_under_root

FRONTMATTER_SPLIT = re.compile(r"^---\s*$", re.MULTILINE)

# Defensive limits (OWASP-style abuse of CPU/memory via corpus).
MAX_INSTRUCTION_FILE_BYTES = 5 * 1024 * 1024
MAX_FRONTMATTER_SECTION_CHARS = 65536

log = logging.getLogger(__name__)


@dataclass
class InstructionRecord:
    """Single instruction document with parsed frontmatter and body."""

    id: str
    rel_path: str
    title: str
    tags: list[str]
    scope: str | None
    priority: str | None
    kind: str | None
    body: str
    content_hash: str
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)

    def search_blob(self) -> str:
        return f"{self.title}\n{' '.join(self.tags)}\n{self.body}".lower()


def _slug_from_path(path: Path) -> str:
    stem = path.stem.lower().replace(" ", "-")
    return re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "instruction"


def _parse_markdown(path: Path, root: Path) -> InstructionRecord:
    text = path.read_text(encoding="utf-8", errors="replace")
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rel = str(path.relative_to(root)).replace("\\", "/")

    meta: dict[str, Any] = {}
    body = text
    parts = FRONTMATTER_SPLIT.split(text, maxsplit=2)
    if len(parts) >= 3 and parts[0].strip() == "":
        fm_raw = parts[1]
        if len(fm_raw) > MAX_FRONTMATTER_SECTION_CHARS:
            log.warning(
                "frontmatter_truncated_skipped path=%s size=%s max=%s",
                rel,
                len(fm_raw),
                MAX_FRONTMATTER_SECTION_CHARS,
            )
            meta = {}
        else:
            try:
                loaded = yaml.safe_load(fm_raw)
                meta = loaded if isinstance(loaded, dict) else {}
            except yaml.YAMLError:
                meta = {}
        body = parts[2].lstrip("\n")

    doc_id = str(meta.get("id") or _slug_from_path(path))
    title = str(meta.get("title") or path.stem)
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(t).lower() for t in tags]
    scope = meta.get("scope")
    scope = str(scope) if scope is not None else None
    priority = meta.get("priority")
    priority = str(priority).lower() if priority is not None else None
    kind = meta.get("kind")
    kind = str(kind).lower() if kind is not None else None

    return InstructionRecord(
        id=doc_id,
        rel_path=rel,
        title=title,
        tags=tags,
        scope=scope,
        priority=priority,
        kind=kind,
        body=body.strip(),
        content_hash=h,
        raw_frontmatter=meta,
    )


def build_index(root: Path) -> dict[str, InstructionRecord]:
    """Load all ``*.md`` under ``root`` (recursive). Keys are document ids (must be unique).

    Skips files outside ``root`` after resolution (symlink escapes), files larger than
    :data:`MAX_INSTRUCTION_FILE_BYTES`, and unreadable paths.
    """
    root = root.resolve()
    if not root.is_dir():
        return {}

    by_id: dict[str, InstructionRecord] = {}
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        if not is_path_under_root(path, root):
            log.warning("skipped_path_outside_root path=%s", path)
            continue
        try:
            st = path.stat()
        except OSError as exc:
            log.warning("skipped_unreadable path=%s error=%s", path, exc)
            continue
        if st.st_size > MAX_INSTRUCTION_FILE_BYTES:
            log.warning(
                "skipped_large_file path=%s bytes=%s max=%s",
                path,
                st.st_size,
                MAX_INSTRUCTION_FILE_BYTES,
            )
            continue
        try:
            rec = _parse_markdown(path, root)
        except OSError as exc:
            log.warning("skipped_read_error path=%s error=%s", path, exc)
            continue
        if rec.id in by_id:
            msg = f"Duplicate instruction id {rec.id!r}: {by_id[rec.id].rel_path} vs {rec.rel_path}"
            raise ValueError(msg)
        by_id[rec.id] = rec
    log.info(
        "index_built root=%s count=%s max_file_bytes=%s",
        root,
        len(by_id),
        MAX_INSTRUCTION_FILE_BYTES,
    )
    return by_id


def tokenize_query(q: str) -> list[str]:
    return [t for t in re.split(r"\W+", q.lower()) if len(t) > 1]


PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1, None: 0}


def score_record(rec: InstructionRecord, tokens: list[str], tag_filter: set[str] | None) -> float:
    if tag_filter and not (tag_filter & set(rec.tags)):
        return 0.0
    blob = rec.search_blob()
    score = 0.0
    title_l = rec.title.lower()
    for t in tokens:
        c = blob.count(t)
        if c:
            score += 1.0 + min(5.0, 0.25 * c)
        if t in title_l:
            score += 3.0
        for tag in rec.tags:
            if t == tag or t in tag:
                score += 2.0
    score += 0.5 * PRIORITY_RANK.get(rec.priority, 0)
    return score


def excerpt_around_match(body: str, tokens: list[str], max_len: int = 400) -> str:
    lower = body.lower()
    pos = -1
    for t in tokens:
        idx = lower.find(t)
        if idx != -1:
            pos = idx
            break
    if pos == -1:
        snippet = body[:max_len]
    else:
        start = max(0, pos - max_len // 3)
        snippet = body[start : start + max_len]
    if len(snippet) >= max_len:
        snippet = snippet[: max_len - 3] + "..."
    return snippet.strip()


def summarize_body(body: str, limit: int = 200) -> str:
    one_line = " ".join(body.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."
