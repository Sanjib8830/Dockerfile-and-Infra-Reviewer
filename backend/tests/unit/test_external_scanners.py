"""External scanner adapter normalization tests (T057)."""

from __future__ import annotations

from app.analyzers.external_scanners import normalize_findings
from app.schemas.review import FindingSource


def test_hadolint_style_findings_are_normalized() -> None:
    raw = [{"code": "DL3006", "level": "error", "message": "Pin base image tag", "line": 1}]
    findings = normalize_findings(raw, tool="hadolint")
    assert len(findings) == 1
    assert findings[0].source is FindingSource.EXTERNAL_SCANNER
    assert findings[0].severity.value == "HIGH"


def test_checkov_style_findings_are_normalized() -> None:
    raw = [{"check_id": "CKV_AWS_23", "check_name": "SG missing description", "severity": "medium", "line": 4}]
    findings = normalize_findings(raw, tool="checkov")
    assert len(findings) == 1
    assert findings[0].source is FindingSource.EXTERNAL_SCANNER
    assert findings[0].severity.value == "MEDIUM"


def test_untrusted_scanner_output_missing_fields_is_skipped_not_raised() -> None:
    raw = [{"unexpected": "field"}, "not-a-dict", None, {"code": None}]
    findings = normalize_findings(raw, tool="hadolint")
    assert findings == []


def test_untrusted_scanner_output_with_unknown_severity_defaults_safely() -> None:
    raw = [{"code": "X1", "level": "unknown-level", "message": "m", "line": 1}]
    findings = normalize_findings(raw, tool="hadolint")
    assert findings[0].severity.value == "INFO"
