#!/usr/bin/env python3
"""Run the manual MCP query-expansion battery (3 tools) and print a results table.

Requires ``INSTRUCTIONS_ROOT`` (or ``--instructions-root``) pointing at the corpus
root (folder with ``*.md`` and ``metadata/corpus-query-expansion-map/*.yaml``).

Usage (from ``mcp-instructions-server/``)::

    pip install -e ".[dev]"
    python scripts/run_query_expansion_manual_battery.py

    python scripts/run_query_expansion_manual_battery.py --json
    python scripts/run_query_expansion_manual_battery.py --strict

See ``docs/MCP-QUERY-EXPANSION-MANUAL-TEST-PLAN.md`` for the full protocol.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SERVER_DIR = SCRIPT_DIR.parent
REPO_FIXTURE = SERVER_DIR.parent / "fixtures" / "instructions"

SEARCH_CASES: list[tuple[str, str]] = [
    ("E1", "persistência"),
    ("E2", "mensageria"),
    ("E3", "retry DNS polly"),
    ("E4", "polly retry circuit breaker"),
    ("E5", "como padronizar ProblemDetails sem try catch duplicado nos endpoints"),
    ("E6", "qual baseline para autenticacao JWT bearer e claims authorization?"),
    ("E7", "persistência SQL dapper"),
]

# Pass rules when corpus is the monorepo ``fixtures/instructions`` reference.
REF_E1_TOP1 = "microservice-data-access-and-sql-security"
REF_E2_TOP1_OK = {
    "microservice-saga-process-manager-and-compensation",
    "microservice-messaging-rabbitmq-publish-consume",
}
REF_E3_TOP1 = "dns-retry-pattern"
REF_E4_FORBIDDEN_TOP1 = "dns-retry-pattern"
REF_E5_TOP1 = "microservice-api-validation-and-error-contracts"
REF_E6_JWT = "microservice-auth-jwt-bearer-and-authorization"
REF_E6_BASELINE = "microservice-api-error-catalog-baseline"
REF_E7_TOP1 = "microservice-data-access-and-sql-security"


def _default_instructions_root() -> Path:
    env = os.environ.get("INSTRUCTIONS_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    return REPO_FIXTURE.resolve()


def _is_reference_fixtures_corpus(root: Path) -> bool:
    try:
        r = root.resolve()
    except OSError:
        return False
    return r.name == "instructions" and r.parent.name == "fixtures"


def _reset_server_index() -> None:
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None


def _load_server(root: Path) -> Any:
    os.environ["INSTRUCTIONS_ROOT"] = str(root)
    # Import after env is set (fresh module in normal script invocation).
    import corporate_instructions_mcp.server as srv

    _reset_server_index()
    return srv


def _expansion_evidence_in_top_k(results: list[dict[str, Any]], k: int = 3) -> bool:
    for row in results[:k]:
        me = row.get("match_explanation") or {}
        if me.get("matched_expansion_only_terms"):
            return True
    return False


def _evaluate_search_case(
    case_id: str,
    data: dict[str, Any],
    *,
    reference_fixture: bool,
) -> tuple[bool, str]:
    results = data.get("results") or []
    if not results:
        return False, "no results"
    top = results[0]
    tid = str(top.get("id", ""))
    me = top.get("match_explanation") or {}
    mu = me.get("matched_user_terms") or []
    mo = me.get("matched_expansion_only_terms") or []
    exp_top3 = _expansion_evidence_in_top_k(results, 3)
    diag = data.get("diagnostics") or {}
    diag_mo = diag.get("matched_expansion_only_terms") or []

    if not reference_fixture:
        ok = exp_top3 or bool(mo) or bool(diag_mo)
        note = "non-reference corpus: expansion signal or results only"
        return ok, note

    if case_id == "E1":
        ok = tid == REF_E1_TOP1 and (bool(mo) or exp_top3)
        return ok, "top1 + expansion" if ok else f"want top1={REF_E1_TOP1} and expansion; got {tid}"
    if case_id == "E2":
        ok = tid in REF_E2_TOP1_OK and (bool(mo) or exp_top3)
        return ok, "top1 saga/messaging + expansion" if ok else f"want top1 in {REF_E2_TOP1_OK}; got {tid}"
    if case_id == "E3":
        ok = tid == REF_E3_TOP1 and (bool(mo) or exp_top3)
        return ok, "dns-retry-pattern + expansion" if ok else f"want top1={REF_E3_TOP1}; got {tid}"
    if case_id == "E4":
        ok = tid != REF_E4_FORBIDDEN_TOP1
        return ok, "top1 is not dns-retry-pattern" if ok else "regression: DNS doc dominated ranking"
    if case_id == "E5":
        ok = tid == REF_E5_TOP1 and (bool(mo) or exp_top3)
        return ok, "validation contract + expansion" if ok else f"want top1={REF_E5_TOP1}; got {tid}"
    if case_id == "E6":
        ids = [str(r.get("id", "")) for r in results[:8]]
        jwt_ok = REF_E6_JWT in ids
        baseline_ok = REF_E6_BASELINE in ids
        exp_ok = exp_top3 or bool(diag_mo)
        ok = jwt_ok and baseline_ok and exp_ok
        if ok:
            return True, "jwt + baseline in top-8 + expansion in top-3/diag"
        return False, f"jwt={jwt_ok} baseline={baseline_ok} expansion={exp_ok} ids[:8]={ids}"
    if case_id == "E7":
        ok = tid == REF_E7_TOP1 and (bool(mo) or exp_top3)
        return ok, "data-access + expansion" if ok else f"want top1={REF_E7_TOP1} and expansion; got {tid}"

    return False, "unknown case"


def run_battery(root: Path, *, max_results: int = 5) -> dict[str, Any]:
    root = root.resolve()
    reference_fixture = _is_reference_fixtures_corpus(root)
    srv = _load_server(root)

    phase1_raw = srv.list_instructions_index()
    phase1 = json.loads(phase1_raw)
    p1_ok = (
        phase1.get("status") == "ok"
        and (phase1.get("index_health") or {}).get("loaded") is True
        and int(phase1.get("count") or 0) >= 1
        and isinstance(phase1.get("by_tag"), dict)
    )

    search_rows: list[dict[str, Any]] = []
    top_ids: list[str] = []

    for case_id, query in SEARCH_CASES:
        raw = srv.search_instructions(query=query, max_results=max_results, include_diagnostics=True)
        data = json.loads(raw)
        err = data.get("error") or data.get("error_code")
        if err and "results" not in data:
            search_rows.append(
                {
                    "case": case_id,
                    "query": query,
                    "error": data,
                    "pass": False,
                    "reason": str(err),
                }
            )
            continue
        results = data.get("results") or []
        top = results[0] if results else {}
        me = top.get("match_explanation") or {}
        ok, reason = _evaluate_search_case(case_id, data, reference_fixture=reference_fixture)
        tid = top.get("id")
        if tid:
            top_ids.append(str(tid))
        search_rows.append(
            {
                "case": case_id,
                "query": query,
                "pass": ok,
                "reason": reason,
                "top1_id": tid,
                "matched_user_terms": me.get("matched_user_terms") or [],
                "matched_expansion_only_terms": me.get("matched_expansion_only_terms") or [],
                "expansion_in_top3": _expansion_evidence_in_top_k(results, 3),
                "diagnostics": data.get("diagnostics") if data.get("diagnostics") else None,
            }
        )

    uniq: list[str] = []
    for i in top_ids:
        if i not in uniq:
            uniq.append(i)
    ids_csv = ",".join(uniq[:12])
    batch_raw = srv.get_instructions_batch(
        ids=ids_csv,
        max_chars_per_instruction=4000,
        include_headings=True,
    )
    batch = json.loads(batch_raw)
    batch_err = batch.get("error") or batch.get("error_code")
    p3_ok = not batch_err and batch.get("missing_ids") == [] and int(batch.get("found_count") or 0) >= 1

    expansion_cases_pass = sum(1 for r in search_rows if r.get("pass"))
    pragmatic_ok = expansion_cases_pass >= 5 and p1_ok and p3_ok

    return {
        "instructions_root": str(root),
        "reference_fixture_corpus": reference_fixture,
        "phase1_ok": p1_ok,
        "phase1": {k: phase1.get(k) for k in ("status", "count") if k in phase1},
        "search_rows": search_rows,
        "phase3_ok": p3_ok,
        "phase3": {
            "found_count": batch.get("found_count"),
            "missing_ids": batch.get("missing_ids"),
            "requested_count": batch.get("requested_count"),
        },
        "expansion_cases_pass": expansion_cases_pass,
        "expansion_cases_total": len(SEARCH_CASES),
        "pragmatic_threshold_met": pragmatic_ok,
    }


def _print_markdown_table(report: dict[str, Any]) -> None:
    print(f"**INSTRUCTIONS_ROOT:** `{report['instructions_root']}`")
    print(f"**Reference fixture rules:** {report['reference_fixture_corpus']}")
    print(f"**Phase 1 (list_instructions_index):** {'PASS' if report['phase1_ok'] else 'FAIL'} - {report.get('phase1')}")
    print(f"**Phase 3 (get_instructions_batch):** {'PASS' if report['phase3_ok'] else 'FAIL'} - {report.get('phase3')}")
    print()
    print("| ID caso | Query (abrev.) | top-1 id | matched_user (top-1) | matched_expansion_only (top-1) | Pass |")
    print("|---------|----------------|----------|------------------------|----------------------------------|------|")
    for row in report["search_rows"]:
        q = row["query"]
        if len(q) > 48:
            q = q[:45] + "..."
        mu = row.get("matched_user_terms") or []
        mo = row.get("matched_expansion_only_terms") or []
        pf = "PASS" if row.get("pass") else "FAIL"
        err = row.get("error")
        top1 = row.get("top1_id", "")
        if err:
            print(f"| {row['case']} | {q} | | | | FAIL |")
            continue
        print(f"| {row['case']} | {q} | `{top1}` | {mu} | {mo} | {pf} |")
    print()
    n = report["expansion_cases_pass"]
    t = report["expansion_cases_total"]
    print(f"**Cases E1-E7 pass:** {n}/{t}")
    print(f"**Pragmatic gate (>= 5/7 + phase1 + phase3):** {'PASS' if report['pragmatic_threshold_met'] else 'FAIL'}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--instructions-root",
        type=Path,
        default=None,
        help="Corpus root (default: INSTRUCTIONS_ROOT env or monorepo fixtures/instructions).",
    )
    parser.add_argument("--max-results", type=int, default=5, help="search_instructions max_results (default 5).")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report on stdout.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 unless every E1–E7 row passes, phase1 passes, and phase3 passes.",
    )
    args = parser.parse_args(argv)

    root = args.instructions_root or _default_instructions_root()
    if not root.is_dir():
        print(f"error: INSTRUCTIONS_ROOT is not a directory: {root}", file=sys.stderr)
        return 2

    report = run_battery(root, max_results=args.max_results)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_markdown_table(report)

    if args.strict:
        all_search = all(r.get("pass") for r in report["search_rows"])
        ok = all_search and report["phase1_ok"] and report["phase3_ok"]
        return 0 if ok else 1

    return 0 if report["pragmatic_threshold_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
