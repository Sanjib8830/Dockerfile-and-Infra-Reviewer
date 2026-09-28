"""Terraform review integration tests: severity, human-review warnings, AI fallback (T042)."""

from __future__ import annotations

from tests.conftest import SAMPLE_TERRAFORM_PUBLIC_SSH


def test_terraform_review_never_claims_safe_to_apply(client) -> None:
    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    assert "safe to apply" not in (body.get("ai_summary") or "").lower()
    for change in body.get("change_summary") or []:
        assert "safe to apply" not in change.get("reason", "").lower()


def test_terraform_review_returns_deterministic_findings_when_ai_unavailable(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module
    from app.api.routes import review as review_routes

    monkeypatch.setattr(
        assistant_module.ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: (_ for _ in ()).throw(TimeoutError("simulated timeout")),
    )
    review_routes._service = review_routes.ReviewService()

    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    assert body["ai_status"] == "unavailable"
    assert any(f["id"] == "TF-SEC-001" for f in body["findings"])

    review_routes._service = review_routes.ReviewService()


def test_terraform_review_rejects_ai_output_missing_risk_classification(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module
    from app.api.routes import review as review_routes

    def fake_invoke(self, **kwargs):
        return (
            '{"summary": "s", "corrected_code": "resource \\"aws_security_group\\" \\"app\\" {}", '
            '"change_summary": [{"change": "c", "reason": "r"}]}'
        )

    monkeypatch.setattr(assistant_module.ReviewAssistant, "_invoke_model", fake_invoke)
    review_routes._service = review_routes.ReviewService()

    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    body = response.json()
    assert body["ai_status"] == "unavailable"

    review_routes._service = review_routes.ReviewService()
