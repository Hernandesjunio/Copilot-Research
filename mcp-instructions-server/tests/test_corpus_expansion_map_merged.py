"""Regression tests after merging legacy `.yml` maps into ADR-002 `*.yaml` domains."""

from __future__ import annotations

from pathlib import Path

import yaml

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"
MAP_DIR = FIXTURES_ROOT / "metadata" / "corpus-query-expansion-map"


def test_yaml_directory_has_no_legacy_yml_sources() -> None:
    """Merged corpus must not ship duplicate legacy maps (.yml)."""
    legacy = sorted(MAP_DIR.glob("*.yml"))
    assert legacy == [], f"Remove legacy .yml after merge: {[p.name for p in legacy]}"


def test_yaml_domain_files_use_adr_schema_not_namespace_terms() -> None:
    """Each *.yaml must declare `domain` + `entries`, not legacy `namespace` + `terms`."""
    for path in sorted(MAP_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict), path.name
        assert "domain" in raw and raw["domain"], path.name
        assert "entries" in raw and isinstance(raw["entries"], list), path.name
        assert "namespace" not in raw, path.name
        assert "terms" not in raw, path.name


def test_load_merge_contains_expected_canonicals() -> None:
    """Spot-check merged canonical keys from former .yml sources."""
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map

    emap = load_corpus_expansion_map(FIXTURES_ROOT)
    assert emap.disabled is False
    all_canonical = {e.canonical for d in emap.domains for e in d.entries}
    for must in (
        "api-error-catalog",
        "sql-parameterization-timeouts-transactions",
        "encoding-texto",
        "bmad-spec-driven-controlled-inference",
        "csharp-async-naming-style",
        "dns-retry-backoff-jitter",
        "rabbitmq-idempotency-dlq-outbox",
    ):
        assert must in all_canonical, f"missing merged canonical {must!r}"


def test_expand_simulation_mensageria_and_sql_tokens() -> None:
    """Simulation: lookup + expansion include merged related terms (expand caps at 5/token)."""
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, load_corpus_expansion_map
    from corporate_instructions_mcp.indexing import expand_query_with_metadata, tokenize_query

    emap = load_corpus_expansion_map(FIXTURES_ROOT)
    lu = build_unidirectional_lookup(emap)
    assert "rabbitmq" in {c.term for c in lu["mensageria"]}

    info_m = expand_query_with_metadata(tokenize_query("mensageria"), expansion_map=emap)
    assert info_m.weights.get("publish", 0) > 0

    info_sql = expand_query_with_metadata(tokenize_query("persistência"), expansion_map=emap)
    assert info_sql.weights.get("dapper", 0) > 0

    # Canonical carries a hyphen; pass token directly (tokenize_query splits on '-').
    info_enc = expand_query_with_metadata(["encoding-texto"], expansion_map=emap)
    assert info_enc.weights.get("bom", 0) > 0 or info_enc.weights.get("charset", 0) > 0


def test_disk_yaml_entry_count_matches_loaded_domains() -> None:
    """Sanity: sum of parsed entries from disk equals loader domain entry counts."""
    from corporate_instructions_mcp.expansion import load_corpus_expansion_map, parse_domain_file

    emap = load_corpus_expansion_map(FIXTURES_ROOT)
    loaded_total = sum(len(d.entries) for d in emap.domains)
    disk_total = 0
    for path in sorted(MAP_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        dom = parse_domain_file(raw, source=path.name)
        assert dom is not None, path.name
        disk_total += len(dom.entries)
    assert disk_total == loaded_total
