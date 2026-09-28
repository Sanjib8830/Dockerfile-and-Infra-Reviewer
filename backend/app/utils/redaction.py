"""Secret detection and redaction utilities (FR-017, PRD Section 33).

Secrets MUST be redacted before any AI processing and MUST NOT appear in logs,
telemetry, URLs, or errors. This module never logs or returns the original
secret value; only a boolean "was anything redacted" signal is safe to surface.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REDACTION_MARKER = "[REDACTED]"

# Patterns cover: AWS keys, generic cloud/API tokens, passwords, private keys,
# and connection strings (PRD Section 33). Each pattern captures the sensitive
# value in a named group `secret` so only that portion is replaced.
_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(
        r"(?i)(aws_secret_access_key\s*=\s*[\"']?)(?P<secret>[A-Za-z0-9/+=]{20,})",
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*[\"']?(?P<secret>[^\s\"'\n]{4,})",
    ),
    re.compile(r"(?i)([a-z][a-z0-9+.\-]*://[^:\s]+:)(?P<secret>[^@\s]{3,})(@)"),  # connection strings
]


@dataclass(frozen=True)
class RedactionResult:
    """Outcome of a redaction pass over a source string."""

    content: str
    redacted: bool


def redact_secrets(source: str) -> RedactionResult:
    """Replace detected secret-like values with `[REDACTED]` and report whether any were found."""
    redacted = False
    result = source

    for pattern in _SECRET_PATTERNS:
        if pattern.groups and "secret" in pattern.groupindex:

            def _replace(match: re.Match[str]) -> str:
                nonlocal redacted
                redacted = True
                return match.group(0).replace(match.group("secret"), REDACTION_MARKER)

            result = pattern.sub(_replace, result)
        else:
            if pattern.search(result):
                redacted = True
            result = pattern.sub(REDACTION_MARKER, result)

    return RedactionResult(content=result, redacted=redacted)
