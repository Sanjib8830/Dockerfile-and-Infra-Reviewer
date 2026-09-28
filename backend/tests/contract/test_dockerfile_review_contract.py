"""POST /api/v1/review contract tests for Dockerfile reviews (T025)."""

from __future__ import annotations

from tests.conftest import SAMPLE_DOCKERFILE

_ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
_REQUIRED_FINDING_FIELDS = {
    "id",
    "category",
    "severity",
    "title",
    "description",
    "impact",
    "recommendation",
    "source",
}


def test_valid_dockerfile_review_returns_200(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    assert response.status_code == 200


def test_dockerfile_review_findings_have_required_fields(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    assert body["findings"], "expected at least one deterministic finding"
    for finding in body["findings"]:
        assert _REQUIRED_FINDING_FIELDS.issubset(finding.keys())


def test_dockerfile_review_findings_use_allowed_severity(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    for finding in body["findings"]:
        assert finding["severity"] in _ALLOWED_SEVERITIES


def test_dockerfile_review_preserves_original_content(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    assert body["original_content"] == SAMPLE_DOCKERFILE


def test_dockerfile_review_summary_matches_findings_count(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    total = sum(body["summary"].values())
    assert total == len(body["findings"])
