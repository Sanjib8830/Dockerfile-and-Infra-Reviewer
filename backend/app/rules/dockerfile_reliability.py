"""Deterministic Dockerfile reliability rules (PRD Section 8 FR-03)."""

from __future__ import annotations

import re

from app.schemas.review import Category, Finding, FindingSource, Severity


def check_missing_healthcheck(source: str) -> list[Finding]:
    """DF-REL-001: no HEALTHCHECK instruction is defined."""
    if re.search(r"^\s*HEALTHCHECK\b", source, re.MULTILINE | re.IGNORECASE):
        return []
    return [
        Finding(
            id="DF-REL-001",
            category=Category.RELIABILITY,
            severity=Severity.LOW,
            title="Missing HEALTHCHECK instruction",
            description="The Dockerfile does not define a HEALTHCHECK.",
            impact="Container orchestrators cannot automatically detect an unhealthy running container.",
            recommendation="Add a HEALTHCHECK instruction appropriate for the application.",
            source=FindingSource.STATIC_ANALYSIS,
        )
    ]


def check_missing_entrypoint_or_cmd(source: str) -> list[Finding]:
    """DF-REL-002: neither ENTRYPOINT nor CMD is defined."""
    has_entrypoint = bool(re.search(r"^\s*ENTRYPOINT\b", source, re.MULTILINE | re.IGNORECASE))
    has_cmd = bool(re.search(r"^\s*CMD\b", source, re.MULTILINE | re.IGNORECASE))
    if has_entrypoint or has_cmd:
        return []
    return [
        Finding(
            id="DF-REL-002",
            category=Category.RELIABILITY,
            severity=Severity.MEDIUM,
            title="Missing ENTRYPOINT or CMD",
            description="The Dockerfile does not define an ENTRYPOINT or CMD instruction.",
            impact="The container has no default runtime command and will not start as expected.",
            recommendation="Add a CMD or ENTRYPOINT instruction that launches the application.",
            source=FindingSource.STATIC_ANALYSIS,
        )
    ]


def run_all(source: str) -> list[Finding]:
    """Run every Dockerfile reliability rule and return the combined findings."""
    findings: list[Finding] = []
    findings.extend(check_missing_healthcheck(source))
    findings.extend(check_missing_entrypoint_or_cmd(source))
    return findings
