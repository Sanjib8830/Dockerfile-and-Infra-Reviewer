"""Deterministic Dockerfile security rules (PRD Section 8 FR-03; Constitution Principle I).

Each rule returns zero or more `Finding` objects with a stable `DF-SEC-*` id and,
where the offending instruction can be located, a captured line number.
"""

from __future__ import annotations

import re

from app.schemas.review import Category, Finding, FindingSource, Severity

_UNSAFE_INSTALL_PATTERN = re.compile(r"(curl|wget)[^\n|]*\|\s*(sh|bash)", re.IGNORECASE)
_CHMOD_777_PATTERN = re.compile(r"chmod\s+(-R\s+)?777\b")
_SECRET_ENV_ARG_PATTERN = re.compile(
    r"^\s*(ENV|ARG)\s+([A-Za-z0-9_]*(PASSWORD|SECRET|TOKEN|API_KEY|ACCESS_KEY)[A-Za-z0-9_]*)\s*=?\s*(\S+)",
    re.IGNORECASE,
)


def _lines(source: str) -> list[str]:
    return source.splitlines()


def check_root_user(source: str) -> list[Finding]:
    """DF-SEC-001: the last USER instruction (or its absence) leaves the container running as root."""
    last_user_line: int | None = None
    last_user_value = "root"
    for index, line in enumerate(_lines(source), start=1):
        match = re.match(r"^\s*USER\s+(\S+)", line)
        if match:
            last_user_line = index
            last_user_value = match.group(1)

    if last_user_value.lower() in ("root", "0"):
        return [
            Finding(
                id="DF-SEC-001",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                title="Container runs as root",
                line_start=last_user_line,
                line_end=last_user_line,
                description="The Docker image does not define a non-root runtime user.",
                impact=(
                    "If the application is compromised, the attacker may obtain "
                    "root-level privileges inside the container."
                ),
                recommendation="Create a dedicated non-root user and switch to it using USER.",
                source=FindingSource.STATIC_ANALYSIS,
            )
        ]
    return []


def check_floating_base_image(source: str) -> list[Finding]:
    """DF-SEC-002: the base image uses `latest` or has no pinned tag."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        match = re.match(r"^\s*FROM\s+([^\s]+)", line, re.IGNORECASE)
        if not match:
            continue
        image = match.group(1)
        if "@sha256:" in image:
            continue
        if ":" not in image or image.endswith(":latest"):
            findings.append(
                Finding(
                    id="DF-SEC-002",
                    category=Category.SECURITY,
                    severity=Severity.MEDIUM,
                    title="Base image is not pinned to a specific version",
                    line_start=index,
                    line_end=index,
                    description=f"The base image `{image}` uses the floating `latest` tag or no tag at all.",
                    impact="Builds are not reproducible and may silently pull an unexpected or vulnerable image.",
                    recommendation="Pin the base image to a specific version tag or digest.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_secret_env_or_arg(source: str) -> list[Finding]:
    """DF-SEC-003: an ENV or ARG instruction defines a secret-like value."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        match = _SECRET_ENV_ARG_PATTERN.match(line)
        if match:
            instruction = match.group(1).upper()
            findings.append(
                Finding(
                    id="DF-SEC-003",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title=f"Secret-like value embedded in {instruction} instruction",
                    line_start=index,
                    line_end=index,
                    description=f"A `{instruction}` instruction appears to define a credential or secret value.",
                    impact="Secrets baked into image layers persist in the image history and can be extracted.",
                    recommendation="Remove the secret and inject it at runtime via a secret manager or orchestrator.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_unsafe_package_installation(source: str) -> list[Finding]:
    """DF-SEC-004: a `curl | sh` / `wget | bash` style unsafe install pattern is used."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        if _UNSAFE_INSTALL_PATTERN.search(line):
            findings.append(
                Finding(
                    id="DF-SEC-004",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title="Unsafe remote script execution during installation",
                    line_start=index,
                    line_end=index,
                    description="A remote script is piped directly into a shell without integrity verification.",
                    impact="A compromised or tampered remote resource could execute arbitrary code during the build.",
                    recommendation="Download the script, verify its checksum or signature, then execute it explicitly.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_dangerous_permissions(source: str) -> list[Finding]:
    """DF-SEC-005: overly permissive file permissions (chmod 777) are applied."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        if _CHMOD_777_PATTERN.search(line):
            findings.append(
                Finding(
                    id="DF-SEC-005",
                    category=Category.SECURITY,
                    severity=Severity.MEDIUM,
                    title="Overly permissive file permissions",
                    line_start=index,
                    line_end=index,
                    description="Files or directories are made world-writable with `chmod 777`.",
                    impact="Any process or user inside the container can modify these files.",
                    recommendation="Grant only the minimum permissions required by the application.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def run_all(source: str) -> list[Finding]:
    """Run every Dockerfile security rule and return the combined findings."""
    findings: list[Finding] = []
    findings.extend(check_root_user(source))
    findings.extend(check_floating_base_image(source))
    findings.extend(check_secret_env_or_arg(source))
    findings.extend(check_unsafe_package_installation(source))
    findings.extend(check_dangerous_permissions(source))
    return findings
