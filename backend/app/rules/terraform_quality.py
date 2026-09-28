"""Deterministic Terraform reliability and maintainability rules (PRD Section 9, FR-007)."""

from __future__ import annotations

import re

from app.rules._terraform_common import resource_blocks as _resource_blocks
from app.schemas.review import Category, Finding, FindingSource, Severity

_LOGGABLE_RESOURCES = ("aws_s3_bucket", "aws_lb")
_BACKUP_CAPABLE_RESOURCES = ("aws_db_instance", "aws_ebs_volume")


def check_missing_logging(source: str) -> list[Finding]:
    """TF-REL-001: a resource that supports logging does not configure it."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in _LOGGABLE_RESOURCES:
            continue
        if "logging" not in block and "access_logs" not in block:
            findings.append(
                Finding(
                    id="TF-REL-001",
                    category=Category.RELIABILITY,
                    severity=Severity.MEDIUM,
                    title="Missing access logging",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` does not configure access logging.",
                    impact="Security incidents and operational issues will be harder to investigate.",
                    recommendation="Enable access logging for this resource.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_missing_backups(source: str) -> list[Finding]:
    """TF-REL-002: a stateful resource does not configure backups/snapshots."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in _BACKUP_CAPABLE_RESOURCES:
            continue
        has_backup = re.search(r"backup_retention_period\s*=\s*[1-9]", block) or re.search(
            r"snapshot_id\s*=", block
        )
        if not has_backup:
            findings.append(
                Finding(
                    id="TF-REL-002",
                    category=Category.RELIABILITY,
                    severity=Severity.MEDIUM,
                    title="Missing backup configuration",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` does not configure automated backups.",
                    impact="Data loss risk increases without a recent recoverable backup.",
                    recommendation="Configure a non-zero backup retention period or snapshot policy.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_missing_tags(source: str) -> list[Finding]:
    """TF-MAINT-001: a resource omits a `tags` block."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if not resource_type.startswith("aws_"):
            continue
        if "tags" not in block:
            findings.append(
                Finding(
                    id="TF-MAINT-001",
                    category=Category.MAINTAINABILITY,
                    severity=Severity.LOW,
                    title="Missing resource tags",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` does not define any tags.",
                    impact="Untagged resources are harder to attribute for cost, ownership, and governance.",
                    recommendation="Add a tags block, e.g. `tags = { Environment = var.environment }`.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_hardcoded_values(source: str) -> list[Finding]:
    """TF-MAINT-002: an `instance_type` (or similar) is hardcoded rather than variable-driven."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type != "aws_instance":
            continue
        match = re.search(r'instance_type\s*=\s*"([^"$]+)"', block)
        if match:
            offset = block[: match.start()].count("\n")
            findings.append(
                Finding(
                    id="TF-MAINT-002",
                    category=Category.MAINTAINABILITY,
                    severity=Severity.LOW,
                    title="Hardcoded instance type",
                    line_start=start_line + offset,
                    line_end=start_line + offset,
                    description=f"`{resource_type}.{name}` hardcodes `instance_type = \"{match.group(1)}\"`.",
                    impact="Hardcoded values are harder to change consistently across environments.",
                    recommendation="Use a variable for the instance type instead of a literal value.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def run_all(source: str) -> list[Finding]:
    """Run every Terraform reliability/maintainability rule and return the combined findings."""
    findings: list[Finding] = []
    findings.extend(check_missing_logging(source))
    findings.extend(check_missing_backups(source))
    findings.extend(check_missing_tags(source))
    findings.extend(check_hardcoded_values(source))
    return findings
