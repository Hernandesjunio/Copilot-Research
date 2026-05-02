# Synonyms Governance

`corporate_instructions_mcp/synonyms.yaml` is the source of truth for search expansion clusters.

## Rules

- Keep clusters domain-focused; avoid broad generic words.
- Limit each cluster to at most 5 related terms.
- Prefer normalized tokens (lowercase, no diacritics).
- Every update must include benchmark verification (`tests/benchmark`).

## Change Workflow

1. Edit `synonyms.yaml`.
2. Update `docs/SYNONYMS-CHANGELOG.md`.
3. Run `pytest -q`.
4. Run benchmark test: `pytest -q tests/benchmark/test_relevance_benchmark.py`.
5. Record impact on MRR/P@k in PR description.

