"""Typed domain abstractions for the review pipeline.

Defines the `Reviewer` protocol used by DockerfileReviewer and TerraformReviewer
(PRD Section 18), decoupled from the FastAPI/Pydantic transport schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.review import Finding, ReviewType, Summary


@dataclass(frozen=True)
class AnalysisResult:
    """Deterministic analysis output for one submitted source, before AI augmentation."""

    type: ReviewType
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, str] | None = None

    @property
    def summary(self) -> Summary:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity.value.lower()] += 1
        return Summary(**counts)


class Reviewer(Protocol):
    """Common abstraction implemented by DockerfileReviewer and TerraformReviewer."""

    def analyze(self, source: str) -> AnalysisResult:
        """Run deterministic analysis over `source` and return normalized findings."""
        ...
