"""Foundation unit tests: redaction, diff, summary counting, original-content invariant (T023)."""

from __future__ import annotations

from app.schemas.review import Category, Finding, FindingSource, Severity, Summary
from app.utils.diff import generate_unified_diff
from app.utils.redaction import redact_secrets


def test_redact_secrets_replaces_password_value() -> None:
    result = redact_secrets('password = "supersecret"')
    assert result.redacted is True
    assert "supersecret" not in result.content
    assert "[REDACTED]" in result.content


def test_redact_secrets_replaces_aws_access_key() -> None:
    result = redact_secrets("AKIAABCDEFGHIJKLMNOP")
    assert result.redacted is True
    assert "AKIAABCDEFGHIJKLMNOP" not in result.content


def test_redact_secrets_leaves_normal_content_untouched() -> None:
    source = "FROM python:3.12\nCOPY . /app\n"
    result = redact_secrets(source)
    assert result.redacted is False
    assert result.content == source


def test_generate_unified_diff_shows_changed_line() -> None:
    diff = generate_unified_diff("FROM python:3.12\n", "FROM python:3.12-slim\n", filename="Dockerfile")
    assert "-FROM python:3.12" in diff
    assert "+FROM python:3.12-slim" in diff


def test_summary_counts_match_finding_severities() -> None:
    findings = [
        Finding(
            id="X-1",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="t",
            description="d",
            impact="i",
            recommendation="r",
            source=FindingSource.STATIC_ANALYSIS,
        ),
        Finding(
            id="X-2",
            category=Category.SECURITY,
            severity=Severity.HIGH,
            title="t",
            description="d",
            impact="i",
            recommendation="r",
            source=FindingSource.STATIC_ANALYSIS,
        ),
    ]
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in findings:
        counts[finding.severity.value.lower()] += 1
    summary = Summary(**counts)
    assert summary.high == 2
    assert summary.critical == 0


def test_review_result_original_content_matches_request(client) -> None:
    source = "FROM alpine:3.20\nCMD [\"true\"]\n"
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": source})
    assert response.status_code == 200
    assert response.json()["original_content"] == source
