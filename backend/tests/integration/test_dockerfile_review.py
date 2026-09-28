"""Dockerfile review integration tests including AI-unavailable fallback (T026)."""

from __future__ import annotations

from tests.conftest import SAMPLE_DOCKERFILE


def test_dockerfile_review_detects_root_user_and_floating_tag(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    ids = {f["id"] for f in body["findings"]}
    assert "DF-SEC-001" in ids  # root user
    assert "DF-SEC-002" not in ids  # python:3.12 is pinned, not floating

    with_latest = SAMPLE_DOCKERFILE.replace("python:3.12", "python:latest")
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": with_latest})
    ids = {f["id"] for f in response.json()["findings"]}
    assert "DF-SEC-002" in ids


def test_dockerfile_review_returns_deterministic_findings_when_ai_unavailable(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module

    monkeypatch.setattr(
        assistant_module.ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError("simulated provider outage")),
    )

    from app.api.routes import review as review_routes

    review_routes._service = review_routes.ReviewService()

    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    assert response.status_code == 200
    body = response.json()
    assert body["ai_status"] == "unavailable"
    assert body["findings"], "deterministic findings must remain available"

    review_routes._service = review_routes.ReviewService()
