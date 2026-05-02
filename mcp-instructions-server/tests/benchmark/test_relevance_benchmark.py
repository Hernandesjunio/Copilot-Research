from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "instructions"
_QUERIES = Path(__file__).with_name("queries.yaml")


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None


def _load_queries() -> list[dict[str, str]]:
    loaded = yaml.safe_load(_QUERIES.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        return []
    out: list[dict[str, str]] = []
    for row in loaded:
        if not isinstance(row, dict):
            continue
        query = str(row.get("query", "")).strip()
        expected = str(row.get("expected_id", "")).strip()
        if query and expected:
            out.append({"query": query, "expected_id": expected})
    return out


def _rank_of(expected_id: str, results: list[dict[str, object]]) -> int | None:
    for idx, row in enumerate(results, start=1):
        if row.get("id") == expected_id:
            return idx
    return None


def test_relevance_benchmark_metrics_baseline() -> None:
    from corporate_instructions_mcp.server import search_instructions

    rows = _load_queries()
    assert rows, "benchmark queries cannot be empty"

    reciprocal_sum = 0.0
    p1_hits = 0
    p3_hits = 0
    p5_hits = 0

    for row in rows:
        raw = search_instructions(
            query=row["query"],
            max_results=5,
            telemetry_expected_instruction_id=row["expected_id"],
        )
        parsed = json.loads(raw)
        rank = _rank_of(row["expected_id"], parsed.get("results", []))
        if rank:
            reciprocal_sum += 1.0 / rank
            if rank <= 1:
                p1_hits += 1
            if rank <= 3:
                p3_hits += 1
            if rank <= 5:
                p5_hits += 1

    total = len(rows)
    mrr = reciprocal_sum / total
    p1 = p1_hits / total
    p3 = p3_hits / total
    p5 = p5_hits / total

    # Baseline safety thresholds for fixture corpus
    assert mrr >= 0.5
    assert p1 >= 0.33
    assert p3 >= 0.66
    assert p5 >= 0.66

