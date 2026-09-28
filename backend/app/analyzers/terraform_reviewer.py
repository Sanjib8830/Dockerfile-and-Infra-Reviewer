"""TerraformReviewer: combines all Terraform rule modules into one analysis (PRD Section 18)."""

from __future__ import annotations

from app.models.review import AnalysisResult
from app.rules import terraform_quality, terraform_security
from app.schemas.review import ReviewType


class TerraformReviewer:
    """Deterministic Terraform analyzer implementing the `Reviewer` protocol."""

    def analyze(self, source: str) -> AnalysisResult:
        findings = [
            *terraform_security.run_all(source),
            *terraform_quality.run_all(source),
        ]
        return AnalysisResult(type=ReviewType.TERRAFORM, findings=findings)
