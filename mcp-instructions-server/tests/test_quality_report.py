from __future__ import annotations

import importlib.util
from pathlib import Path


def _module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "build_quality_report.py"
    spec = importlib.util.spec_from_file_location("build_quality_report", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_quality_report_has_nested_summary_and_breakdown() -> None:
    mod = _module()
    report = mod.build_report(
        [
            {
                "event": "search_instructions.completed",
                "tool": "search_instructions",
                "failure": False,
                "retry_increment": 0,
                "search_zero_results": False,
                "search_with_low_confidence_rate": 0.0,
                "search_confidence": 0.9,
                "tool_latency_ms": 12,
                "latency_p95_ms": 15,
                "session_id": "s1",
            },
            {
                "event": "search_instructions.completed",
                "tool": "search_instructions",
                "failure": False,
                "retry_increment": 1,
                "search_zero_results": True,
                "search_with_low_confidence_rate": 1.0,
                "search_confidence": 0.42,
                "tool_latency_ms": 20,
                "latency_p95_ms": 25,
                "session_id": "s1",
            },
            {
                "event": "resolve_instruction_context.completed",
                "tool": "resolve_instruction_context",
                "failure": False,
                "retry_increment": 0,
                "tool_latency_ms": 35,
                "latency_p95_ms": 35,
                "session_id": "s1",
            },
            {
                "event": "get_normative_checklist.completed",
                "tool": "get_normative_checklist",
                "failure": True,
                "retry_increment": 0,
                "tool_latency_ms": 5,
                "latency_p95_ms": 5,
                "session_id": "s2",
            },
        ]
    )

    assert report["summary"]["total_completed_calls"] == 4
    assert report["summary"]["search_completed_calls"] == 2
    assert report["counts"]["tool_failures"] == 1
    assert report["rates"]["zero_result_rate"] == 0.5
    assert report["rates"]["low_confidence_rate"] == 0.5
    assert "resolve_instruction_context" in report["tool_breakdown"]
    assert report["tool_breakdown"]["search_instructions"]["retry_rate"] == 0.5
    assert report["warnings"]


def test_build_quality_report_can_compare_with_baseline() -> None:
    mod = _module()
    report = mod.build_report(
        [
            {
                "event": "search_instructions.completed",
                "tool": "search_instructions",
                "failure": False,
                "retry_increment": 0,
                "search_zero_results": False,
                "search_with_low_confidence_rate": 0.0,
                "search_confidence": 0.8,
                "tool_latency_ms": 10,
                "latency_p95_ms": 10,
                "session_id": "s1",
            }
        ],
        baseline={
            "rates": {
                "tool_failure_rate": 0.1,
                "retry_rate": 0.2,
                "zero_result_rate": 0.3,
                "low_confidence_rate": 0.4,
            }
        },
    )

    assert report["comparison_to_baseline"]["tool_failure_rate"]["delta"] == -0.1
    assert report["comparison_to_baseline"]["retry_rate"]["delta"] == -0.2
