"""AI timeout, malformed response, and redaction-before-prompt regression tests (T058)."""

from __future__ import annotations

from app.ai.review_assistant import ReviewAssistant
from app.core.config import Settings
from app.schemas.review import Category, Finding, FindingSource, ReviewType, Severity

_FINDING = Finding(
    id="DF-SEC-001",
    category=Category.SECURITY,
    severity=Severity.HIGH,
    title="Container runs as root",
    description="d",
    impact="i",
    recommendation="r",
    source=FindingSource.STATIC_ANALYSIS,
)


def _assistant(**overrides) -> ReviewAssistant:
    settings = Settings(google_api_key="test-key", **overrides)
    return ReviewAssistant(settings)


def test_ai_disabled_returns_not_requested() -> None:
    assistant = ReviewAssistant(Settings(google_api_key=None))
    result = assistant.assist(review_type=ReviewType.DOCKERFILE, original_content="FROM x", findings=[_FINDING])
    assert result.status.value == "not_requested"


def test_ai_timeout_returns_unavailable(monkeypatch) -> None:
    assistant = _assistant()
    monkeypatch.setattr(
        ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: (_ for _ in ()).throw(TimeoutError()),
    )
    result = assistant.assist(review_type=ReviewType.DOCKERFILE, original_content="FROM x", findings=[_FINDING])
    assert result.status.value == "unavailable"


def test_ai_malformed_json_returns_unavailable(monkeypatch) -> None:
    assistant = _assistant()
    monkeypatch.setattr(ReviewAssistant, "_invoke_model", lambda self, **kwargs: "not json")
    result = assistant.assist(review_type=ReviewType.DOCKERFILE, original_content="FROM x", findings=[_FINDING])
    assert result.status.value == "unavailable"


def test_ai_structured_response_returns_available(monkeypatch) -> None:
    assistant = _assistant()
    monkeypatch.setattr(
        ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: (
            '{"summary":"A finding was detected.","corrected_code":"",'
            '"change_summary":[],"explanations":['
            '{"finding_id":"DF-SEC-001","explanation":"Run the container as a non-root user."}]}'
        ),
    )
    result = assistant.assist(review_type=ReviewType.DOCKERFILE, original_content="FROM x", findings=[_FINDING])
    assert result.status.value == "available"
    assert result.explanations == {"DF-SEC-001": "Run the container as a non-root user."}


def test_terraform_response_schema_requires_valid_risk_classification() -> None:
    schema = ReviewAssistant._response_schema(ReviewType.TERRAFORM)
    change_item = schema["properties"]["change_summary"]["items"]
    assert "risk_classification" in change_item["required"]
    assert change_item["properties"]["risk_classification"]["enum"] == [
        "SAFE_CHANGE",
        "POTENTIALLY_BREAKING_CHANGE",
        "DESTRUCTIVE_CHANGE",
        "REQUIRES_HUMAN_REVIEW",
    ]


def test_ai_response_claiming_safe_to_apply_is_rejected(monkeypatch) -> None:
    assistant = _assistant()
    monkeypatch.setattr(
        ReviewAssistant,
        "_invoke_model",
        lambda self, **kwargs: '{"summary": "This is safe to apply.", "corrected_code": "FROM x"}',
    )
    result = assistant.assist(review_type=ReviewType.TERRAFORM, original_content="FROM x", findings=[_FINDING])
    assert result.status.value == "unavailable"


def test_secret_redacted_before_prompt_is_built(monkeypatch) -> None:
    assistant = _assistant()
    captured: dict[str, str] = {}

    def fake_invoke(self, *, review_type, redacted_content, findings):
        captured["content"] = redacted_content
        return '{"summary": "ok"}'

    monkeypatch.setattr(ReviewAssistant, "_invoke_model", fake_invoke)
    secret_source = 'ENV DB_PASSWORD="hunter2"\n'
    assistant.assist(review_type=ReviewType.DOCKERFILE, original_content=secret_source, findings=[_FINDING])
    assert "hunter2" not in captured["content"]
    assert "[REDACTED]" in captured["content"]


def test_no_findings_skips_ai_call_entirely(monkeypatch) -> None:
    assistant = _assistant()

    def fail_if_called(self, **kwargs):
        raise AssertionError("AI must not be invoked when there are no findings")

    monkeypatch.setattr(ReviewAssistant, "_invoke_model", fail_if_called)
    result = assistant.assist(review_type=ReviewType.DOCKERFILE, original_content="FROM x", findings=[])
    assert result.status.value == "not_requested"
