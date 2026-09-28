"""Remediation output unit tests: diff/change_summary presence and qualified estimates (T051)."""

from __future__ import annotations

from app.rules import dockerfile_optimization


def test_qualified_language_used_for_all_size_findings() -> None:
    source = (
        "FROM ubuntu:20.04\n"
        "RUN apt-get install -y build-essential gcc\n"
        "RUN pip install flask\n"
        "COPY . .\n"
    )
    findings = dockerfile_optimization.run_all(source)
    assert findings
    for finding in findings:
        text = f"{finding.description} {finding.recommendation}".lower()
        assert "exactly" not in text
        assert " mb" not in text


def test_corrected_content_implies_diff_and_change_summary(client, monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from app.ai import review_assistant as assistant_module
    from app.api.routes import review as review_routes

    def fake_invoke(self, **kwargs):
        return (
            '{"summary": "Found issues.", "corrected_code": "FROM python:3.12-slim\\nUSER appuser\\n", '
            '"change_summary": [{"change": "Use slim image", "reason": "Reduce size"}]}'
        )

    monkeypatch.setattr(assistant_module.ReviewAssistant, "_invoke_model", fake_invoke)
    review_routes._service = review_routes.ReviewService()

    response = client.post(
        "/api/v1/review",
        json={"type": "dockerfile", "content": "FROM python:3.12\nCMD [\"python\", \"app.py\"]\n"},
    )
    body = response.json()
    if body.get("corrected_content"):
        assert body.get("diff")
        assert body.get("change_summary")

    review_routes._service = review_routes.ReviewService()
