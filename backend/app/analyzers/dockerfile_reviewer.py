"""DockerfileReviewer: combines all Dockerfile rule modules into one analysis (PRD Section 18)."""

from __future__ import annotations

from app.models.review import AnalysisResult
from app.rules import dockerfile_optimization, dockerfile_reliability, dockerfile_security
from app.schemas.review import ReviewType


class DockerfileReviewer:
    """Deterministic Dockerfile analyzer implementing the `Reviewer` protocol."""

    def analyze(self, source: str) -> AnalysisResult:
        findings = [
            *dockerfile_security.run_all(source),
            *dockerfile_optimization.run_all(source),
            *dockerfile_reliability.run_all(source),
        ]
        return AnalysisResult(type=ReviewType.DOCKERFILE, findings=findings)
