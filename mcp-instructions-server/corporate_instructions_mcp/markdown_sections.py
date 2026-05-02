"""Markdown section slicing helpers for semantic batch extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class MarkdownSection:
    heading: str | None
    content: str
    level: int = 0
    heading_path: tuple[str, ...] = ()

    @property
    def block(self) -> str:
        if self.heading:
            return f"{self.heading}\n{self.content}".strip()
        return self.content.strip()

    @property
    def heading_label(self) -> str:
        if not self.heading_path:
            return self.heading or ""
        return " > ".join(self.heading_path)


def split_markdown_sections(body: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    current_heading: str | None = None
    current_level = 0
    current_lines: list[str] = []
    heading_stack: list[tuple[int, str]] = []

    def flush_current() -> None:
        nonlocal current_lines
        if current_heading is None and not current_lines:
            return
        heading_path = tuple(label for _, label in heading_stack)
        sections.append(
            MarkdownSection(
                heading=current_heading,
                content="\n".join(current_lines).strip(),
                level=current_level,
                heading_path=heading_path,
            )
        )
        current_lines = []

    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush_current()
            current_level = len(match.group(1))
            heading_text = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= current_level:
                heading_stack.pop()
            heading_stack.append((current_level, heading_text))
            current_heading = line.strip()
            continue
        current_lines.append(line)

    flush_current()
    return sections or [MarkdownSection(heading=None, content=body.strip())]


def filter_sections(sections: list[MarkdownSection], section_contains: str | None) -> tuple[list[MarkdownSection], int]:
    if not section_contains:
        return sections, len(sections)
    terms = [term.strip().lower() for term in section_contains.split(",") if term.strip()]
    if not terms:
        return sections, len(sections)
    out: list[MarkdownSection] = []
    for section in sections:
        searchable = "\n".join(
            [
                section.heading or "",
                section.heading_label,
                section.content,
            ]
        ).lower()
        if all(term in searchable for term in terms):
            out.append(section)
    if not out:
        return [], 0
    return out, len(out)


def _truncate_block(raw: str, max_chars: int) -> str:
    if len(raw) <= max_chars:
        return raw
    if max_chars <= 20:
        return raw[:max_chars]
    return raw[: max_chars - 20].rstrip() + "\n\n… [truncated]"


def compose_section_payload(
    sections: list[MarkdownSection],
    *,
    include_headings: bool = True,
    headings_only: bool = False,
    max_chars: int,
) -> tuple[str, bool, list[str]]:
    chunks: list[str] = []
    included_headings: list[str] = []
    truncated = False
    remaining = max_chars

    for section in sections:
        if headings_only:
            chunk = section.heading_label or section.heading or ""
        elif include_headings:
            chunk = section.block
        else:
            chunk = section.content.strip()

        chunk = chunk.strip()
        if not chunk:
            continue

        separator = "\n\n" if chunks else ""
        projected = len(separator) + len(chunk)
        if projected > remaining:
            if not chunks:
                chunks.append(_truncate_block(chunk, remaining))
                truncated = len(chunk) > remaining
                if section.heading_label:
                    included_headings.append(section.heading_label)
            else:
                truncated = True
            break

        if separator:
            chunks.append("")
        chunks.append(chunk)
        remaining -= projected
        if section.heading_label:
            included_headings.append(section.heading_label)

    raw = "\n\n".join(part for part in chunks if part is not None).strip()
    return raw, truncated, included_headings

