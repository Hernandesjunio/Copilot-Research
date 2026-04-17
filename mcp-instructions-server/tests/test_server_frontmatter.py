"""Unit tests for frontmatter JSON normalization (no MCP corpus required)."""

from datetime import date, datetime
from decimal import Decimal

from corporate_instructions_mcp.server import _json_safe_frontmatter


def test_json_safe_frontmatter_converts_date_and_nested() -> None:
    out = _json_safe_frontmatter(
        {
            "id": "x",
            "d": date(2026, 4, 12),
            "nested": {"n": date(2025, 1, 1)},
        }
    )
    assert out["d"] == "2026-04-12"
    assert out["nested"]["n"] == "2025-01-01"


def test_json_safe_frontmatter_datetime_and_decimal() -> None:
    out = _json_safe_frontmatter(
        {
            "dt": datetime(2026, 4, 12, 15, 30, 0),
            "dec": Decimal("1.5"),
        }
    )
    assert out["dt"] == "2026-04-12T15:30:00"
    assert out["dec"] == 1.5


def test_json_safe_frontmatter_lists() -> None:
    out = _json_safe_frontmatter(
        {
            "tags": ["a", "b"],
            "dates": [date(2026, 1, 1)],
        }
    )
    assert out["tags"] == ["a", "b"]
    assert out["dates"] == ["2026-01-01"]


def test_json_safe_frontmatter_empty() -> None:
    assert _json_safe_frontmatter({}) == {}
