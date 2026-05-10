"""Fail-first tests for EPIC-09 (`I-04`): cross-domain coverage gaps."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "instructions"


@pytest.fixture(autouse=True)
def _env_instructions_root(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(_FIXTURES))
    import corporate_instructions_mcp.server as srv

    srv._index = {}
    srv._index_root = None
    srv._expansion_map = None
    yield


def _selected_ids(query: str, *, max_results: int = 7) -> list[str]:
    from corporate_instructions_mcp.server import resolve_instruction_context

    data = json.loads(resolve_instruction_context(query, max_results=max_results))
    return data["selected_ids"]


def test_FAIL_tracing_query_should_include_observability_doc() -> None:
    selected = _selected_ids("como propagar traceparent e correlation id entre API e chamadas externas?")
    assert "microservice-integration-httpclientfactory-contracts" in selected
    assert "microservice-opentelemetry-correlation-and-health" in selected


def test_FAIL_http_and_db_metrics_query_should_include_data_access_doc() -> None:
    selected = _selected_ids("quais metricas e spans devo coletar para dependencias HTTP e banco?")
    assert "microservice-opentelemetry-correlation-and-health" in selected
    assert "microservice-data-access-and-sql-security" in selected


def test_FAIL_sql_timeout_transaction_query_should_include_production_readiness() -> None:
    selected = _selected_ids(
        "qual padrao para queries SQL seguras com timeout e transacao?",
        max_results=8,
    )
    assert "microservice-data-access-and-sql-security" in selected
    assert "microservice-configuration-production-readiness" in selected


def test_FAIL_secrets_and_logs_query_should_include_production_readiness() -> None:
    selected = _selected_ids("como tratar segredos e evitar vazamento em logs e repositorio?")
    assert "example-security-baseline" in selected
    assert "microservice-configuration-production-readiness" in selected


def test_FAIL_problemdetails_query_should_include_error_catalog() -> None:
    selected = _selected_ids("como padronizar ProblemDetails sem try/catch duplicado nos endpoints?")
    assert "microservice-api-validation-and-error-contracts" in selected
    assert "microservice-api-error-catalog-baseline" in selected


def test_FAIL_jwt_baseline_query_should_include_error_catalog_supporting() -> None:
    selected = _selected_ids("qual baseline para autenticacao JWT bearer e claims authorization?")
    assert "microservice-auth-jwt-bearer-and-authorization" in selected
    assert "microservice-api-error-catalog-baseline" in selected
