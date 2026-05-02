# Quality Dashboard

The release quality report is generated from telemetry NDJSON lines:

```bash
python scripts/build_quality_report.py --input telemetry.ndjson --output quality-report.json
```

Optional comparison against the previous release baseline:

```bash
python scripts/build_quality_report.py --input telemetry.ndjson --baseline previous-quality-report.json --output quality-report.json
```

## Metrics

- `zero_result_rate`
- `low_confidence_rate`
- `retry_rate`
- `tool_failure_rate`

## Operational Gate

Every release should compare current metrics against the previous baseline. Investigate and document regressions before rollout.

## Output Shape

The generated JSON now includes:

- `summary` with event/session/tool totals
- `counts` with raw numerators
- `rates` with release KPIs
- `search_quality` with confidence aggregates
- `tool_breakdown` with per-tool calls, retries, failures and latency
- `comparison_to_baseline` when `--baseline` is provided
- `warnings` when key rates exceed the default guardrails

