from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_lines(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def _tool_breakdown(completed: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in completed:
        tool = str(event.get("tool") or str(event.get("event", "")).split(".", 1)[0] or "unknown")
        grouped.setdefault(tool, []).append(event)

    breakdown: dict[str, dict[str, Any]] = {}
    for tool, rows in sorted(grouped.items()):
        failures = sum(1 for row in rows if bool(row.get("failure")))
        retries = sum(int(row.get("retry_increment", 0) or 0) for row in rows)
        latencies = [float(row.get("tool_latency_ms", 0) or 0) for row in rows]
        breakdown[tool] = {
            "calls": len(rows),
            "failure_rate": _rate(failures, len(rows)),
            "retry_rate": _rate(retries, len(rows)),
            "avg_latency_ms": _avg(latencies),
            "max_latency_ms": max(latencies) if latencies else 0.0,
            "latest_latency_p95_ms": rows[-1].get("latency_p95_ms"),
        }
    return breakdown


def _build_warnings(rates: dict[str, float]) -> list[str]:
    warnings: list[str] = []
    if rates.get("tool_failure_rate", 0.0) > 0.05:
        warnings.append("tool_failure_rate above 5%")
    if rates.get("retry_rate", 0.0) > 0.15:
        warnings.append("retry_rate above 15%")
    if rates.get("zero_result_rate", 0.0) > 0.20:
        warnings.append("zero_result_rate above 20%")
    if rates.get("low_confidence_rate", 0.0) > 0.35:
        warnings.append("low_confidence_rate above 35%")
    return warnings


def _compare_metrics(current: dict[str, float], baseline: dict[str, Any] | None) -> dict[str, dict[str, float]]:
    if not baseline:
        return {}
    baseline_rates = baseline.get("rates")
    if not isinstance(baseline_rates, dict):
        return {}
    comparison: dict[str, dict[str, float]] = {}
    for key, current_value in current.items():
        previous = baseline_rates.get(key)
        if isinstance(previous, (int, float)):
            comparison[key] = {
                "current": round(float(current_value), 6),
                "baseline": round(float(previous), 6),
                "delta": round(float(current_value) - float(previous), 6),
            }
    return comparison


def build_report(events: list[dict[str, Any]], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    completed = [e for e in events if str(e.get("event", "")).endswith(".completed")]
    total_calls = len(completed)
    tool_failures = sum(1 for e in completed if bool(e.get("failure")))
    retries_total = sum(int(e.get("retry_increment", 0) or 0) for e in completed)
    search_completed = [e for e in completed if e.get("event") == "search_instructions.completed"]
    zero_results = sum(1 for e in search_completed if bool(e.get("search_zero_results")))
    low_confidence = sum(1 for e in search_completed if float(e.get("search_with_low_confidence_rate", 0.0) or 0.0) > 0)
    search_confidence_values = [
        float(e.get("search_confidence", 0.0) or 0.0)
        for e in search_completed
        if isinstance(e.get("search_confidence"), (int, float))
    ]
    session_ids = {str(e.get("session_id")) for e in events if e.get("session_id")}
    rates = {
        "tool_failure_rate": _rate(tool_failures, total_calls),
        "retry_rate": _rate(retries_total, total_calls),
        "zero_result_rate": _rate(zero_results, len(search_completed)),
        "low_confidence_rate": _rate(low_confidence, len(search_completed)),
    }
    report = {
        "summary": {
            "events_total": len(events),
            "sessions_total": len(session_ids),
            "total_completed_calls": total_calls,
            "search_completed_calls": len(search_completed),
            "tools_seen": sorted({str(e.get("tool") or "").strip() for e in completed if str(e.get("tool") or "").strip()}),
        },
        "counts": {
            "tool_failures": tool_failures,
            "retries_total": retries_total,
            "zero_results": zero_results,
            "low_confidence_searches": low_confidence,
        },
        "rates": rates,
        "search_quality": {
            "avg_search_confidence": _avg(search_confidence_values),
            "max_search_confidence": round(max(search_confidence_values), 6) if search_confidence_values else 0.0,
            "min_search_confidence": round(min(search_confidence_values), 6) if search_confidence_values else 0.0,
        },
        "tool_breakdown": _tool_breakdown(completed),
        "warnings": _build_warnings(rates),
    }
    comparison = _compare_metrics(rates, baseline)
    if comparison:
        report["comparison_to_baseline"] = comparison
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build quality report from NDJSON telemetry.")
    parser.add_argument("--input", required=True, help="Path to telemetry NDJSON file")
    parser.add_argument("--output", required=False, help="Optional output JSON file")
    parser.add_argument("--baseline", required=False, help="Optional baseline quality report JSON")
    args = parser.parse_args()

    events = _load_lines(Path(args.input))
    baseline = None
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    report = build_report(events, baseline=baseline)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()

