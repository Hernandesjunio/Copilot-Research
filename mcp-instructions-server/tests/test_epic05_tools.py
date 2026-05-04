"""P0 acceptance tests for validate_applicability and build_compliance_matrix."""

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
    yield


def test_validate_applicability_scope_no_match_returns_non_applicable() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-api-openfinance-patterns"],
            target_artifact={"path": "Domain/Cliente.cs"},
            workspace_evidence=None,
        )
    )
    assert data["results"][0]["applicability"] == "non_applicable"


def test_validate_applicability_policy_in_scope_without_workspace_requirement_returns_applicable() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-api-openfinance-patterns"],
            target_artifact={"path": "Servico/Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=None,
        )
    )
    assert data["results"][0]["applicability"] == "applicable"


def test_validate_applicability_policy_with_sufficient_evidence_returns_applicable() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-authorization-resource-scope-and-audit"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=["HttpContext.User"],
        )
    )
    assert data["results"][0]["applicability"] == "applicable"


def test_validate_applicability_policy_on_absence_hypothesis_only() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-authorization-resource-scope-and-audit"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=[],
        )
    )
    assert data["results"][0]["applicability"] == "hypothesis_only"


def test_validate_applicability_policy_without_on_absence_defaults_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from corporate_instructions_mcp.server import validate_applicability
    import corporate_instructions_mcp.server as srv

    policy = """---
id: policy-no-on-absence
title: Policy without on_absence
scope: "**/*.cs"
kind: policy
workspace_evidence_required: true
workspace_signals: [FooSignal]
---
Body.
"""
    (tmp_path / "policy-no-on-absence.md").write_text(policy, encoding="utf-8")
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path))
    srv._index = {}
    srv._index_root = None

    data = json.loads(
        validate_applicability(
            instruction_ids=["policy-no-on-absence"],
            target_artifact={"path": "Api/Program.cs"},
            workspace_evidence=[],
        )
    )
    assert data["results"][0]["applicability"] == "blocked_by_missing_evidence"


def test_validate_applicability_reference_in_scope_returns_hypothesis_only() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["dns-retry-pattern"],
            target_artifact={"path": "Api/Infrastructure/DnsClient.cs"},
            workspace_evidence=None,
        )
    )
    assert data["results"][0]["applicability"] == "hypothesis_only"


def test_validate_applicability_accepts_simple_string_evidence() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-authorization-resource-scope-and-audit"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=["IAuthorizationRequirement"],
        )
    )
    assert data["results"][0]["applicability"] == "applicable"


def test_validate_applicability_accepts_structured_evidence() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-authorization-resource-scope-and-audit"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=[
                {
                    "value": "IAuthorizationRequirement",
                    "path": "Api/Security/OwnerRequirement.cs",
                    "symbol": "OwnerRequirement",
                    "source": "code_search",
                    "evidence_type": "positive",
                }
            ],
        )
    )
    assert data["results"][0]["applicability"] == "applicable"


def test_validate_applicability_accepts_negative_evidence() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-authorization-resource-scope-and-audit"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=[{"value": "HttpContext.User", "evidence_type": "negative"}],
        )
    )
    assert data["results"][0]["applicability"] == "hypothesis_only"
    assert data["results"][0]["diagnostics"]["evidence_negative_count"] == 1


def test_validate_applicability_normalizes_windows_path() -> None:
    from corporate_instructions_mcp.server import validate_applicability

    data = json.loads(
        validate_applicability(
            instruction_ids=["microservice-api-openfinance-patterns"],
            target_artifact={"path": r"Servico\Api\Endpoints\ClienteEndpoints.cs"},
            workspace_evidence=None,
        )
    )
    assert data["results"][0]["scope_match"] is True
    assert data["results"][0]["applicability"] == "applicable"


def _matrix_status(
    *,
    applicability: str,
    observations: list[dict[str, str]] | None = None,
) -> str:
    from corporate_instructions_mcp.server import build_compliance_matrix

    payload = json.loads(
        build_compliance_matrix(
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            instruction_results=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "kind": "policy",
                    "applicability": applicability,
                    "reason": "synthetic-test-row",
                }
            ],
            artifact_observations=observations or [],
        )
    )
    return payload["matrix"][0]["status"]


def test_build_compliance_matrix_non_applicable_maps_not_applicable() -> None:
    assert _matrix_status(applicability="non_applicable") == "not_applicable"


def test_build_compliance_matrix_hypothesis_only_maps_not_enforceable() -> None:
    assert _matrix_status(applicability="hypothesis_only") == "not_enforceable"


def test_build_compliance_matrix_blocked_maps_not_enforceable() -> None:
    assert _matrix_status(applicability="blocked_by_missing_evidence") == "not_enforceable"


def test_build_compliance_matrix_applicable_positive_maps_conformant() -> None:
    assert (
        _matrix_status(
            applicability="applicable",
            observations=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "positive",
                    "value": "Found expected response envelope",
                }
            ],
        )
        == "conformant"
    )


def test_build_compliance_matrix_applicable_positive_and_gap_maps_partial() -> None:
    assert (
        _matrix_status(
            applicability="applicable",
            observations=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "positive",
                    "value": "Found expected response envelope",
                },
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "gap",
                    "value": "Missing global error mapping",
                },
            ],
        )
        == "partial_conformance"
    )


def test_build_compliance_matrix_applicable_deviation_maps_non_conformance() -> None:
    assert (
        _matrix_status(
            applicability="applicable",
            observations=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "deviation",
                    "value": "Returns raw exception message to caller",
                }
            ],
        )
        == "non_conformance"
    )


def test_build_compliance_matrix_applicable_without_observation_maps_insufficient_evidence() -> None:
    assert _matrix_status(applicability="applicable") == "insufficient_evidence"


def test_validate_applicability_generic_substring_evidence_does_not_match_specific_signal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corporate_instructions_mcp.server import validate_applicability
    import corporate_instructions_mcp.server as srv

    policy = """---
id: policy-httpclient-factory
title: Use HttpClientFactory
scope: "**/*.cs"
kind: policy
workspace_evidence_required: true
workspace_signals: [httpclientfactory]
---
Body.
"""
    (tmp_path / "policy-httpclient-factory.md").write_text(policy, encoding="utf-8")
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path))
    srv._index = {}
    srv._index_root = None

    data = json.loads(
        validate_applicability(
            instruction_ids=["policy-httpclient-factory"],
            target_artifact={"path": "Api/Services/ClienteService.cs"},
            workspace_evidence=["http"],
        )
    )
    assert data["results"][0]["applicability"] == "blocked_by_missing_evidence"


def test_validate_applicability_specific_tokenized_evidence_matches_signal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from corporate_instructions_mcp.server import validate_applicability
    import corporate_instructions_mcp.server as srv

    policy = """---
id: policy-httpcontext-user
title: Use HttpContext User checks
scope: "**/*.cs"
kind: policy
workspace_evidence_required: true
workspace_signals: [HttpContext.User]
---
Body.
"""
    (tmp_path / "policy-httpcontext-user.md").write_text(policy, encoding="utf-8")
    monkeypatch.setenv("INSTRUCTIONS_ROOT", str(tmp_path))
    srv._index = {}
    srv._index_root = None

    data = json.loads(
        validate_applicability(
            instruction_ids=["policy-httpcontext-user"],
            target_artifact={"path": "Api/Endpoints/ClienteEndpoints.cs"},
            workspace_evidence=["HttpContext.User.Identity.IsAuthenticated"],
        )
    )
    assert data["results"][0]["applicability"] == "applicable"


def test_build_compliance_matrix_applicable_trivial_positive_maps_insufficient_evidence() -> None:
    assert (
        _matrix_status(
            applicability="applicable",
            observations=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "positive",
                    "value": "ok",
                }
            ],
        )
        == "insufficient_evidence"
    )


def test_build_compliance_matrix_applicable_substantive_positive_maps_conformant() -> None:
    assert (
        _matrix_status(
            applicability="applicable",
            observations=[
                {
                    "instruction_id": "microservice-api-openfinance-patterns",
                    "observation_type": "positive",
                    "value": "Api/Endpoints/ClienteEndpoints.cs returns standardized response envelope for 2xx and 4xx cases.",
                }
            ],
        )
        == "conformant"
    )
