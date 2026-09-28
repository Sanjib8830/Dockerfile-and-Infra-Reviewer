"""Deterministic Terraform security rules (PRD Section 9, FR-007)."""

from __future__ import annotations

import re

from app.rules._terraform_common import resource_blocks as _resource_blocks
from app.schemas.review import Category, Finding, FindingSource, Severity

_SENSITIVE_PORTS = {22, 3389, 5432, 3306}
_PUBLIC_CIDR = "0.0.0.0/0"


def _lines(source: str) -> list[str]:
    return source.splitlines()


def check_public_sensitive_port_exposure(source: str) -> list[Finding]:
    """TF-SEC-001: a security group rule exposes a sensitive port to 0.0.0.0/0."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in ("aws_security_group", "aws_security_group_rule"):
            continue
        if _PUBLIC_CIDR not in block:
            continue
        for port_match in re.finditer(r"(from_port|to_port)\s*=\s*(\d+)", block):
            port = int(port_match.group(2))
            if port in _SENSITIVE_PORTS:
                offset = block[: port_match.start()].count("\n")
                findings.append(
                    Finding(
                        id="TF-SEC-001",
                        category=Category.SECURITY,
                        severity=Severity.HIGH,
                        title=f"Sensitive port {port} exposed to the public internet",
                        line_start=start_line + offset,
                        line_end=start_line + offset,
                        description=(
                            f"`{resource_type}.{name}` allows ingress from {_PUBLIC_CIDR} on port {port}."
                        ),
                        impact="Any host on the internet can attempt to reach this port.",
                        recommendation=(
                            "Restrict cidr_blocks to a trusted range or use a private administrative path."
                        ),
                        source=FindingSource.STATIC_ANALYSIS,
                    )
                )
                break  # one finding per resource block is sufficient evidence
    return findings


def check_public_resource_exposure(source: str) -> list[Finding]:
    """TF-SEC-002: an S3-style bucket or resource is explicitly made public."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in ("aws_s3_bucket", "aws_s3_bucket_acl", "aws_s3_bucket_public_access_block"):
            continue
        if re.search(r'acl\s*=\s*"public-read(-write)?"', block) or re.search(
            r"block_public_acls\s*=\s*false", block
        ):
            findings.append(
                Finding(
                    id="TF-SEC-002",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title="Public bucket access",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` grants public read/write access.",
                    impact="Anyone on the internet may be able to read or modify bucket contents.",
                    recommendation="Remove public ACLs and enable the S3 public access block.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_unencrypted_storage(source: str) -> list[Finding]:
    """TF-SEC-003: storage resources omit server-side encryption."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in ("aws_s3_bucket", "aws_db_instance", "aws_ebs_volume"):
            continue
        has_encryption_flag = re.search(r"encrypted\s*=\s*true", block) or re.search(
            r"server_side_encryption_configuration", block
        )
        if not has_encryption_flag:
            findings.append(
                Finding(
                    id="TF-SEC-003",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title="Missing server-side encryption",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` does not enable server-side encryption.",
                    impact="Data at rest is not encrypted, increasing exposure if storage media is compromised.",
                    recommendation="Enable server-side encryption for this resource.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_hardcoded_credentials(source: str) -> list[Finding]:
    """TF-SEC-004: a hardcoded credential-like literal is assigned in the configuration."""
    findings: list[Finding] = []
    pattern = re.compile(
        r'(?i)(password|secret|access_key|token)\s*=\s*"(?!\$\{)[^"$]{4,}"',
    )
    for index, line in enumerate(_lines(source), start=1):
        if pattern.search(line):
            findings.append(
                Finding(
                    id="TF-SEC-004",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title="Hardcoded credential in Terraform configuration",
                    line_start=index,
                    line_end=index,
                    description="A password, secret, token, or access key is hardcoded as a literal value.",
                    impact="Credentials committed to configuration files can be extracted from version control.",
                    recommendation="Use a variable sourced from a secret manager instead of a literal value.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_broad_iam_permissions(source: str) -> list[Finding]:
    """TF-SEC-005: an IAM policy grants wildcard actions or resources."""
    findings: list[Finding] = []
    for resource_type, name, start_line, block in _resource_blocks(source):
        if resource_type not in ("aws_iam_policy", "aws_iam_role_policy"):
            continue
        has_wildcard_action = re.search(r'Action\s*[:=]\s*"\*"', block, re.IGNORECASE)
        has_wildcard_resource = re.search(r'Resource\s*[:=]\s*"\*"', block, re.IGNORECASE)
        if has_wildcard_action or has_wildcard_resource:
            findings.append(
                Finding(
                    id="TF-SEC-005",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    title="Overly permissive IAM policy",
                    line_start=start_line,
                    line_end=start_line,
                    description=f"`{resource_type}.{name}` grants wildcard IAM actions or resources.",
                    impact="The attached principal may be able to perform far more actions than required.",
                    recommendation="Scope the policy to only the specific actions and resources required.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def run_all(source: str) -> list[Finding]:
    """Run every Terraform security rule and return the combined findings."""
    findings: list[Finding] = []
    findings.extend(check_public_sensitive_port_exposure(source))
    findings.extend(check_public_resource_exposure(source))
    findings.extend(check_unencrypted_storage(source))
    findings.extend(check_hardcoded_credentials(source))
    findings.extend(check_broad_iam_permissions(source))
    return findings
