"""ReviewService: evidence-first orchestration of deterministic analysis plus optional AI (PRD Section 18).

Sequencing is Parse -> Static Analysis -> Rules -> AI (Constitution Principle I,
II). `original_content` is always preserved unmodified (Constitution Principle
III), and any AI failure still returns the deterministic findings (FR-016).
"""

from __future__ import annotations

from app.ai.review_assistant import ReviewAssistant
from app.analyzers.dockerfile_reviewer import DockerfileReviewer
from app.analyzers.terraform_reviewer import TerraformReviewer
from app.core.config import Settings, load_settings
from app.core.observability import ReviewTiming, log_review_outcome, new_review_id, timed
from app.models.review import Reviewer
from app.schemas.review import (
    AiStatus,
    ChangeRisk,
    ReviewRequest,
    ReviewResult,
    ReviewType,
)
from app.utils.diff import generate_unified_diff


class ReviewService:
    """Coordinates reviewer selection, deterministic analysis, and optional AI augmentation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or load_settings()
        self._reviewers: dict[ReviewType, Reviewer] = {
            ReviewType.DOCKERFILE: DockerfileReviewer(),
            ReviewType.TERRAFORM: TerraformReviewer(),
        }
        self._assistant = ReviewAssistant(self._settings)

    def review(self, request: ReviewRequest, *, request_id: str) -> ReviewResult:
        review_id = new_review_id()
        timing = ReviewTiming()

        reviewer = self._reviewers[request.type]
        with timed(timing, "analysis_duration"):
            analysis = reviewer.analyze(request.content)

        findings = list(analysis.findings)
        ai_status = AiStatus.NOT_REQUESTED
        ai_summary: str | None = None
        corrected_content: str | None = None
        diff: str | None = None
        change_summary = None

        with timed(timing, "ai_duration"):
            ai_result = self._assistant.assist(
                review_type=request.type,
                original_content=request.content,
                findings=findings,
            )

        ai_status = ai_result.status
        if ai_result.status is AiStatus.AVAILABLE:
            ai_summary = ai_result.ai_summary
            if ai_result.explanations:
                for finding in findings:
                    if finding.id in ai_result.explanations:
                        finding.explanation = ai_result.explanations[finding.id]

            if ai_result.corrected_content and ai_result.corrected_content != request.content:
                corrected_content = ai_result.corrected_content
                diff = generate_unified_diff(request.content, corrected_content, filename=request.type.value)
                change_summary = ai_result.change_summary

                # Terraform corrections MUST always carry a risk classification (FR-014, Constitution III).
                if request.type is ReviewType.TERRAFORM and change_summary:
                    for change in change_summary:
                        if change.risk_classification is None:
                            change.risk_classification = ChangeRisk.REQUIRES_HUMAN_REVIEW

        result = ReviewResult(
            review_id=review_id,
            type=request.type,
            summary=analysis.summary,
            findings=findings,
            metrics=analysis.metrics,
            corrected_content=corrected_content,
            original_content=request.content,
            diff=diff,
            change_summary=change_summary,
            ai_summary=ai_summary,
            ai_status=ai_status,
        )

        log_review_outcome(
            request_id=request_id,
            review_id=review_id,
            file_type=request.type.value,
            timing=timing,
            success=True,
            ai_status=ai_status.value,
        )
        return result
