"""Failing tests for EPIC-09 (`I-02`): meta/governance docs outranking technical intent."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"
_META_IDS = {
    "assistant-workflow-bmad-planning-and-controlled-inference",
    "instruction-authoring-standard",
}


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    yield


def test_FAIL_meta_governance_doc_should_not_beat_specific_technical_doc_for_httpclient_query() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context, search_instructions

    query = "qual padrao para typed client com IHttpClientFactory e mapping de DTO externo?"
    search = json.loads(search_instructions(query=query, max_results=7, include_diagnostics=True))
    by_id = {row["id"]: row for row in search["results"]}

    assert "microservice-integration-httpclientfactory-contracts" in by_id
    assert "instruction-authoring-standard" in by_id

    technical_terms = {"typed", "ihttpclientfactory", "dto", "mapping", "externo"}
    technical_hit_terms = set(by_id["microservice-integration-httpclientfactory-contracts"]["match_explanation"]["matched_user_terms"])
    meta_hit_terms = set(by_id["instruction-authoring-standard"]["match_explanation"]["matched_user_terms"])
    assert len(technical_hit_terms & technical_terms) >= 3
    assert len(meta_hit_terms & technical_terms) <= 1

    resolved = json.loads(resolve_instruction_context(query, max_results=7))
    top3 = resolved["selected_ids"][:3]
    assert "instruction-authoring-standard" not in top3, (
        "Documento meta/governance apareceu no top-3 em query técnica de HttpClientFactory. "
        f"top3={top3} technical_hit_terms={sorted(technical_hit_terms)} meta_hit_terms={sorted(meta_hit_terms)}"
    )


def test_FAIL_meta_policy_promotion_should_not_outrank_saga_reference_for_rabbitmq_query() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context, search_instructions

    query = "como padronizar publish/consume com rabbitmq, dlq e idempotencia?"
    search = json.loads(search_instructions(query=query, max_results=7, include_diagnostics=True))
    search_ids = [row["id"] for row in search["results"]]

    meta_id = "assistant-workflow-bmad-planning-and-controlled-inference"
    saga_id = "microservice-saga-process-manager-and-compensation"
    assert meta_id in search_ids and saga_id in search_ids
    assert search_ids.index(saga_id) < search_ids.index(meta_id), (
        "No ranking bruto de busca, o documento técnico de saga já aparece acima do meta doc. "
        f"search_ids={search_ids}"
    )

    resolved = json.loads(resolve_instruction_context(query, max_results=7))
    selected = resolved["selected_ids"]
    assert selected.index(saga_id) < selected.index(meta_id), (
        "Na resolução final, o documento meta/governance foi promovido acima de saga para query de RabbitMQ. "
        f"selected_ids={selected}"
    )


def test_FAIL_meta_governance_docs_should_not_be_marked_as_normative_for_technical_query() -> None:
    from corporate_instructions_mcp.server import resolve_instruction_context

    query = "qual padrao para typed client com IHttpClientFactory e mapping de DTO externo?"
    resolved = json.loads(resolve_instruction_context(query, max_results=7))
    normative_ids = set(resolved["resolution"]["actionable_context"]["normative_ids"])

    offending = sorted(_META_IDS & normative_ids)
    assert not offending, (
        "Documento meta/governance marcado como normativo em query técnica. "
        f"offending={offending} normative_ids={sorted(normative_ids)}"
    )

