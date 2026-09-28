"""POST /api/v1/review contract tests for Terraform reviews (T041)."""

from __future__ import annotations

from tests.conftest import SAMPLE_TERRAFORM_PUBLIC_SSH


def test_valid_terraform_review_returns_200(client) -> None:
    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    assert response.status_code == 200


def test_terraform_review_public_ssh_is_high_or_above(client) -> None:
    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    matching = [f for f in body["findings"] if f["id"] == "TF-SEC-001"]
    assert matching
    assert matching[0]["severity"] in ("HIGH", "CRITICAL")


def test_terraform_change_summary_entries_require_risk_classification(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module
    from app.api.routes import review as review_routes

    def fake_invoke(self, **kwargs):
        return (
            '{"summary": "Public SSH access detected.", '
            '"corrected_code": "resource \\"aws_security_group\\" \\"app\\" {}", '
            '"change_summary": [{"change": "Restrict CIDR", "reason": "Reduce exposure", '
            '"risk_classification": "REQUIRES_HUMAN_REVIEW"}]}'
        )

    monkeypatch.setattr(assistant_module.ReviewAssistant, "_invoke_model", fake_invoke)
    review_routes._service = review_routes.ReviewService()

    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    if body.get("change_summary"):
        for change in body["change_summary"]:
            assert change["risk_classification"] is not None

    review_routes._service = review_routes.ReviewService()
