from __future__ import annotations

from corporate_instructions_mcp.markdown_sections import (
    compose_section_payload,
    filter_sections,
    split_markdown_sections,
)


def test_split_markdown_sections_preserves_heading_path() -> None:
    body = """Intro

# Parent
alpha

## Child
beta
"""
    sections = split_markdown_sections(body)
    child = next(section for section in sections if section.heading == "## Child")
    assert child.heading_path == ("Parent", "Child")


def test_filter_sections_counts_matches() -> None:
    body = """# Retry
retry content

# SQL
sql content
"""
    sections = split_markdown_sections(body)
    filtered, count = filter_sections(sections, "retry")
    assert count == 1
    assert len(filtered) == 1
    assert filtered[0].heading == "# Retry"


def test_compose_section_payload_truncates_by_whole_block_first() -> None:
    body = """# First
small

# Second
""" + ("x" * 200)
    sections = split_markdown_sections(body)
    payload, truncated, included_headings = compose_section_payload(sections, include_headings=True, max_chars=40)
    assert "# First" in payload
    assert included_headings[0] == "First"
    assert truncated is True

