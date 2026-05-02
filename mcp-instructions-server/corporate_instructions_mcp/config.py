"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int, *, lo: int, hi: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw, 10)
    except ValueError:
        return default
    return max(lo, min(value, hi))


def _env_float(name: str, default: float, *, lo: float, hi: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return max(lo, min(value, hi))


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RuntimeConfig:
    search_default_max_results: int
    search_max_results_cap: int
    batch_default_max_chars_per_instruction: int
    batch_min_chars_per_instruction: int
    batch_max_chars_per_instruction: int
    batch_max_total_chars: int
    low_confidence_relevance_threshold: float
    ambiguous_score_gap_threshold: float
    expansion_only_penalty_ratio: float
    expansion_only_results_threshold: int
    index_staleness_check_seconds: int
    include_legacy_error_field: bool


def load_runtime_config() -> RuntimeConfig:
    cap = _env_int("MCP_SEARCH_MAX_RESULTS_CAP", 20, lo=1, hi=200)
    default_search = _env_int("MCP_SEARCH_DEFAULT_MAX_RESULTS", 10, lo=1, hi=cap)
    batch_max = _env_int("MCP_BATCH_MAX_CHARS_PER_INSTRUCTION", 200_000, lo=1000, hi=2_000_000)
    batch_min = _env_int("MCP_BATCH_MIN_CHARS_PER_INSTRUCTION", 500, lo=100, hi=batch_max)
    batch_default = _env_int(
        "MCP_BATCH_DEFAULT_MAX_CHARS_PER_INSTRUCTION",
        8000,
        lo=batch_min,
        hi=batch_max,
    )
    return RuntimeConfig(
        search_default_max_results=default_search,
        search_max_results_cap=cap,
        batch_default_max_chars_per_instruction=batch_default,
        batch_min_chars_per_instruction=batch_min,
        batch_max_chars_per_instruction=batch_max,
        batch_max_total_chars=_env_int("MCP_BATCH_MAX_TOTAL_CHARS", 120_000, lo=1000, hi=4_000_000),
        low_confidence_relevance_threshold=_env_float(
            "MCP_LOW_CONFIDENCE_THRESHOLD",
            0.2,
            lo=0.0,
            hi=1.0,
        ),
        ambiguous_score_gap_threshold=_env_float(
            "MCP_AMBIGUOUS_SCORE_GAP_THRESHOLD",
            1.5,
            lo=0.0,
            hi=100.0,
        ),
        expansion_only_penalty_ratio=_env_float(
            "MCP_EXPANSION_ONLY_PENALTY_RATIO",
            0.85,
            lo=0.0,
            hi=1.0,
        ),
        expansion_only_results_threshold=_env_int(
            "MCP_EXPANSION_ONLY_RESULTS_THRESHOLD",
            1,
            lo=0,
            hi=100,
        ),
        index_staleness_check_seconds=_env_int("MCP_INDEX_STALENESS_CHECK_SECONDS", 10, lo=0, hi=3600),
        include_legacy_error_field=_env_bool("MCP_INCLUDE_LEGACY_ERROR_FIELD", True),
    )

