"""External scanner adapters (Hadolint/Trivy/TFLint/Checkov-compatible output).

External scanner output MUST be treated as untrusted input and normalized into
the internal `Finding` schema before it is used anywhere else in the pipeline
(Constitution: Development Workflow and Quality Gates; PRD Section 17).
"""

from __future__ import annotations

from typing import Any

from app.schemas.review import Category, Finding, FindingSource, Severity

_SEVERITY_MAP = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "info": Severity.INFO,
    "style": Severity.LOW,
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
}

_CATEGORY_MAP = {
    "security": Category.SECURITY,
    "performance": Category.PERFORMANCE,
    "reliability": Category.RELIABILITY,
    "maintainability": Category.MAINTAINABILITY,
    "style": Category.BEST_PRACTICE,
}


def _safe_str(value: Any, default: str = "") -> str:
    """Coerce untrusted scanner output to a plain string, never raising."""
    if value is None:
        return default
    return str(value)


def normalize_hadolint_finding(raw: dict[str, Any]) -> Finding | None:
    """Normalize one Hadolint-style finding dict into the internal `Finding` schema."""
    code = raw.get("code")
    if not code:
        return None
    severity = _SEVERITY_MAP.get(_safe_str(raw.get("level")).lower(), Severity.INFO)
    line = raw.get("line")
    return Finding(
        id=f"EXT-{_safe_str(code)}",
        category=Category.BEST_PRACTICE,
        severity=severity,
        title=_safe_str(raw.get("message"), "External scanner finding"),
        line_start=int(line) if isinstance(line, int) else None,
        line_end=int(line) if isinstance(line, int) else None,
        description=_safe_str(raw.get("message")),
        impact="Reported by an external static analysis tool.",
        recommendation="Review the external scanner's guidance for this rule.",
        source=FindingSource.EXTERNAL_SCANNER,
    )


def normalize_checkov_finding(raw: dict[str, Any]) -> Finding | None:
    """Normalize one Checkov/TFLint-style finding dict into the internal `Finding` schema."""
    check_id = raw.get("check_id") or raw.get("rule_id")
    if not check_id:
        return None
    severity = _SEVERITY_MAP.get(_safe_str(raw.get("severity")).lower(), Severity.MEDIUM)
    category = _CATEGORY_MAP.get(_safe_str(raw.get("category")).lower(), Category.SECURITY)
    line = raw.get("line")
    return Finding(
        id=f"EXT-{_safe_str(check_id)}",
        category=category,
        severity=severity,
        title=_safe_str(raw.get("check_name"), "External scanner finding"),
        line_start=int(line) if isinstance(line, int) else None,
        line_end=int(line) if isinstance(line, int) else None,
        description=_safe_str(raw.get("check_name")),
        impact="Reported by an external infrastructure-as-code scanner.",
        recommendation="Review the external scanner's guidance for this rule.",
        source=FindingSource.EXTERNAL_SCANNER,
    )


def normalize_findings(raw_findings: list[dict[str, Any]], *, tool: str) -> list[Finding]:
    """Normalize a list of untrusted external-scanner findings for the given `tool`."""
    normalizer = normalize_hadolint_finding if tool == "hadolint" else normalize_checkov_finding
    normalized: list[Finding] = []
    for raw in raw_findings:
        if not isinstance(raw, dict):
            continue
        finding = normalizer(raw)
        if finding is not None:
            normalized.append(finding)
    return normalized
