"""End-to-end quickstart scenarios: Dockerfile, Terraform, AI fallback, input validation (T062).

Mirrors specs/001-dockerfile-infra-review/quickstart.md Scenarios 1, 2, 4, and 5.
"""

from __future__ import annotations

from tests.conftest import SAMPLE_DOCKERFILE, SAMPLE_TERRAFORM_PUBLIC_SSH


def test_scenario_1_dockerfile_review_with_known_issue(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    assert response.status_code == 200
    assert sum(body["summary"].values()) > 0
    assert any(f["severity"] in ("HIGH", "MEDIUM") for f in body["findings"])
    assert body["original_content"] == SAMPLE_DOCKERFILE


def test_scenario_2_terraform_review_with_public_exposure(client) -> None:
    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    assert response.status_code == 200
    matching = [f for f in body["findings"] if f["id"] == "TF-SEC-001"]
    assert matching and matching[0]["severity"] in ("HIGH", "CRITICAL")


def test_scenario_4_graceful_degradation_when_ai_unavailable(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module
    from app.api.routes import review as review_routes

    monkeypatch.setattr(
        assistant_module.ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError("provider down")),
    )
    review_routes._service = review_routes.ReviewService()

    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    body = response.json()
    assert body["ai_status"] == "unavailable"
    assert body["findings"]

    review_routes._service = review_routes.ReviewService()


def test_scenario_5_input_validation(client) -> None:
    empty = client.post("/api/v1/review", json={"type": "dockerfile", "content": ""})
    assert empty.status_code == 400

    oversized = client.post("/api/v1/review", json={"type": "dockerfile", "content": "A" * (1024 * 1024 + 1)})
    assert oversized.status_code == 400

    unsupported = client.post("/api/v1/review", json={"type": "yaml", "content": "a: b"})
    assert unsupported.status_code == 400
    assert unsupported.json()["error"] == "UNSUPPORTED_FILE_TYPE"
