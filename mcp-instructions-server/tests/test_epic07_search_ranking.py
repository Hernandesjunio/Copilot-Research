"""Acceptance tests for EPIC-07 (search ranking quality and corpus integrity)."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"

_META_GOVERNANCE_IDS = {
    "assistant-workflow-bmad-planning-and-controlled-inference",
    "instruction-authoring-standard",
}


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None
    yield


def test_stopwords_pt_contains_common_connectives() -> None:
    from corporate_instructions_mcp.indexing import STOPWORDS

    required = {"como", "deve", "ser", "que", "me", "quando", "qual", "quais"}
    assert required.issubset(STOPWORDS)


def test_stopwords_pt_do_not_conflict_with_expansion_keys() -> None:
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, load_corpus_expansion_map
    from corporate_instructions_mcp.indexing import STOPWORDS

    emap = load_corpus_expansion_map(_FIXTURES)
    lookup = build_unidirectional_lookup(emap)
    keys = set(lookup.keys())
    assert not (keys & STOPWORDS)


def test_common_pt_connectives_do_not_score_unrelated_messaging_doc() -> None:
    from corporate_instructions_mcp.indexing import expand_query_with_metadata, score_record_breakdown, tokenize_query
    from corporate_instructions_mcp.server import _ensure_index

    idx, _, _ = _ensure_index()
    tokens = tokenize_query("como deve ser")
    info = expand_query_with_metadata(tokens)
    breakdown = score_record_breakdown(idx["microservice-messaging-rabbitmq-publish-consume"], tokens, None, info)
    assert breakdown.score_body_blob == 0.0


def test_generic_pt_validation_verb_is_filtered_as_stopword() -> None:
    from corporate_instructions_mcp.indexing import STOPWORDS, expand_query_with_metadata, score_record_breakdown, tokenize_query
    from corporate_instructions_mcp.server import _ensure_index

    assert "validar" in STOPWORDS

    idx, _, _ = _ensure_index()
    tokens = tokenize_query("como validar")
    info = expand_query_with_metadata(tokens)
    breakdown = score_record_breakdown(idx["microservice-messaging-rabbitmq-publish-consume"], tokens, None, info)
    assert breakdown.score_body_blob == 0.0


def test_architecture_query_top3_excludes_meta_governance() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="como o projeto deve ser estruturado", max_results=7))
    top3 = [row["id"] for row in data["results"][:3]]
    assert not (_META_GOVERNANCE_IDS & set(top3))

    architecture_expected = {
        "microservice-architecture-layering",
        "microservice-clean-architecture-guardrails",
        "microservice-domain-interfaces-models-repository",
    }
    assert len(architecture_expected & set(top3)) >= 2


def test_resolve_architecture_query_excludes_meta_governance() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context("como separar Api, Dominio, Interfaces e Repositorio", max_results=7))
    assert not (_META_GOVERNANCE_IDS & set(data["selected_ids"]))


def test_example_security_baseline_id_matches_filename_slug() -> None:
    from corporate_instructions_mcp.server import _ensure_index

    idx, _, _ = _ensure_index()
    assert "example-security-baseline" in idx


def test_example_security_baseline_is_retrievable_by_batch() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(get_instructions_batch(ids="example-security-baseline"))
    assert data["found_count"] == 1
    assert data["instructions"][0]["id"] == "example-security-baseline"


def test_security_baseline_secrets_legacy_id_is_not_in_index() -> None:
    from corporate_instructions_mcp.server import get_instructions_batch

    data = json.loads(get_instructions_batch(ids="security-baseline-secrets"))
    assert data["found_count"] == 0
    assert "security-baseline-secrets" in data["missing_ids"]


def test_corpus_invariant_filename_slug_matches_frontmatter_id() -> None:
    from corporate_instructions_mcp.indexing import _slug_from_path
    from corporate_instructions_mcp.server import _ensure_index

    idx, _, _ = _ensure_index()
    mismatches = [
        f"arquivo={record.rel_path} id_frontmatter={record_id} slug_esperado={_slug_from_path(Path(record.rel_path))}"
        for record_id, record in idx.items()
        if record_id != _slug_from_path(Path(record.rel_path))
    ]
    assert not mismatches, "\n".join(mismatches)


def test_observability_query_includes_configuration_readiness() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context("me informe como a observabilidade deve ser implementada", max_results=7))
    selected = set(data["selected_ids"])
    assert "microservice-opentelemetry-correlation-and-health" in selected
    assert "microservice-configuration-production-readiness" in selected


def test_health_check_query_includes_configuration_readiness() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context("como separar /health/live de /health/ready em servico .NET", max_results=7))
    assert "microservice-configuration-production-readiness" in data["selected_ids"]


def test_health_or_observability_expansion_reaches_configuration_terms() -> None:
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, load_corpus_expansion_map

    emap = load_corpus_expansion_map(_FIXTURES)
    lu = build_unidirectional_lookup(emap)

    def terms_for(canonical: str) -> set[str]:
        return {c.term for c in lu.get(canonical, [])}

    observability_expansion = terms_for("observabilidade")
    healthcheck_expansion = terms_for("healthcheck")
    configuracao_expansion = terms_for("configuracao")
    combined = observability_expansion | healthcheck_expansion | configuracao_expansion
    expected = {"configuration", "production", "readiness", "deployment"}
    assert combined & expected


def test_retry_backoff_circuit_breaker_query_excludes_dns_retry_pattern() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(
        search_instructions("como configurar retry com backoff e circuit breaker para API de pagamentos", max_results=7)
    )
    ids = [row["id"] for row in data["results"]]
    assert "dns-retry-pattern" not in ids


def test_dns_query_still_returns_dns_retry_pattern_first() -> None:
    from corporate_instructions_mcp.server import search_instructions

    data = json.loads(search_instructions(query="retry DNS polly", max_results=3))
    assert data["results"][0]["id"] == "dns-retry-pattern"


def test_composite_query_has_three_primary_themes_in_top5() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(
        resolve_instruction_context(
            "quero estruturar o projeto, instrumentar observabilidade e integrar API externa com resiliencia",
            max_results=7,
        )
    )
    top5 = data["selected_ids"][:5]
    required = {
        "microservice-architecture-layering",
        "microservice-opentelemetry-correlation-and-health",
        "microservice-integration-httpclientfactory-contracts",
    }
    assert not (required - set(top5))


def test_integration_query_surfaces_integration_and_resilience_docs() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context("como fazer integracao externa", max_results=7))
    selected = set(data["selected_ids"])
    assert "microservice-integration-httpclientfactory-contracts" in selected
    assert "microservice-resilience-polly-timeouts-and-circuit-breaker" in selected


def test_collection_query_surfaces_openfinance_and_collection_contracts() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(
        resolve_instruction_context(
            "como implementar paginacao, filtro e ordenacao em colecoes sem quebrar contrato",
            max_results=7,
        )
    )
    selected = set(data["selected_ids"])
    assert "microservice-api-collection-resources-pagination-filters" in selected
    assert "microservice-api-openfinance-patterns" in selected


def test_expansion_map_lookup_for_paginacao() -> None:
    from corporate_instructions_mcp.expansion import build_unidirectional_lookup, load_corpus_expansion_map

    emap = load_corpus_expansion_map(_FIXTURES)
    lu = build_unidirectional_lookup(emap)
    expansion = {c.term for c in lu.get("paginacao", [])}
    assert expansion & {"pagination", "filtering", "collection", "envelope"}


def test_cache_query_still_surfaces_cache_policy() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context("quando usar imemorycache, ttl e invalidacao em API de consulta"))
    assert "microservice-caching-imemorycache-policy" in data["selected_ids"]
