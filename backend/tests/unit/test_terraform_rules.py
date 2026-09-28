"""Terraform deterministic rule unit tests (T040)."""

from __future__ import annotations

from app.rules import terraform_quality, terraform_security

PUBLIC_SSH = """resource "aws_security_group" "app" {
  name = "app"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""

PUBLIC_BUCKET = """resource "aws_s3_bucket" "data" {
  bucket = "example"
  acl    = "public-read"
}
"""

UNENCRYPTED_DB = """resource "aws_db_instance" "main" {
  allocated_storage = 20
  engine            = "postgres"
}
"""

HARDCODED_CREDENTIAL = """resource "aws_db_instance" "main" {
  password = "hunter2hunter2"
}
"""

WILDCARD_IAM = """resource "aws_iam_policy" "broad" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}
"""


def test_public_sensitive_port_detected() -> None:
    findings = terraform_security.check_public_sensitive_port_exposure(PUBLIC_SSH)
    assert any(f.id == "TF-SEC-001" and f.severity.value == "HIGH" for f in findings)


def test_public_sensitive_port_not_flagged_for_restricted_cidr() -> None:
    restricted = PUBLIC_SSH.replace('["0.0.0.0/0"]', '["10.0.0.0/16"]')
    findings = terraform_security.check_public_sensitive_port_exposure(restricted)
    assert findings == []


def test_public_bucket_detected() -> None:
    findings = terraform_security.check_public_resource_exposure(PUBLIC_BUCKET)
    assert any(f.id == "TF-SEC-002" for f in findings)


def test_unencrypted_storage_detected() -> None:
    findings = terraform_security.check_unencrypted_storage(UNENCRYPTED_DB)
    assert any(f.id == "TF-SEC-003" for f in findings)


def test_encrypted_storage_not_flagged() -> None:
    encrypted = UNENCRYPTED_DB.replace(
        'engine            = "postgres"',
        'engine            = "postgres"\n  storage_encrypted = true',
    )
    findings = terraform_security.check_unencrypted_storage(encrypted)
    assert findings == []


def test_hardcoded_credentials_detected() -> None:
    findings = terraform_security.check_hardcoded_credentials(HARDCODED_CREDENTIAL)
    assert any(f.id == "TF-SEC-004" for f in findings)


def test_wildcard_iam_detected() -> None:
    findings = terraform_security.check_broad_iam_permissions(WILDCARD_IAM)
    assert any(f.id == "TF-SEC-005" for f in findings)


def test_missing_logging_detected() -> None:
    findings = terraform_quality.check_missing_logging(PUBLIC_BUCKET)
    assert any(f.id == "TF-REL-001" for f in findings)


def test_missing_backups_detected() -> None:
    findings = terraform_quality.check_missing_backups(UNENCRYPTED_DB)
    assert any(f.id == "TF-REL-002" for f in findings)


def test_missing_tags_detected() -> None:
    findings = terraform_quality.check_missing_tags(PUBLIC_BUCKET)
    assert any(f.id == "TF-MAINT-001" for f in findings)


def test_tags_present_not_flagged() -> None:
    tagged = PUBLIC_BUCKET.replace(
        'acl    = "public-read"',
        'acl    = "public-read"\n  tags = { Environment = "prod" }',
    )
    findings = terraform_quality.check_missing_tags(tagged)
    assert findings == []
