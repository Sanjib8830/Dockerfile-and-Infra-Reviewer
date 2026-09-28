"""Pydantic schemas for the review API request/response contract.

Mirrors specs/001-dockerfile-infra-review/contracts/review-api.md and
specs/001-dockerfile-infra-review/data-model.md.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

MAX_CONTENT_BYTES = 1024 * 1024  # 1 MB, per FR-003 / data-model.md


class ReviewType(str, Enum):
    """Selected input type. Required; must be one of the two supported values (FR-001)."""

    DOCKERFILE = "dockerfile"
    TERRAFORM = "terraform"


class Severity(str, Enum):
    """Exactly one severity. Required; set by the deterministic rule, never overridden by AI (FR-010)."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    """Finding category."""

    SECURITY = "security"
    SIZE = "size"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICE = "best-practice"


class FindingSource(str, Enum):
    """Where the finding originated."""

    STATIC_ANALYSIS = "static-analysis"
    EXTERNAL_SCANNER = "external-scanner"


class AiStatus(str, Enum):
    """Indicates whether AI-assisted content succeeded."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_REQUESTED = "not_requested"


class ChangeRisk(str, Enum):
    """Risk level of applying a remediation change."""

    SAFE_CHANGE = "SAFE_CHANGE"
    POTENTIALLY_BREAKING_CHANGE = "POTENTIALLY_BREAKING_CHANGE"
    DESTRUCTIVE_CHANGE = "DESTRUCTIVE_CHANGE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


class ReviewRequest(BaseModel):
    """Represents the user's submitted review input (FR-001, FR-002, FR-003)."""

    type: ReviewType
    content: str = Field(..., min_length=1)
    filename: str | None = None

    @field_validator("content")
    @classmethod
    def content_must_fit_size_limit(cls, value: str) -> str:
        # "Required; non-empty; UTF-8 text; max 1 MB" (data-model.md ReviewRequest.content)
        if not value.strip():
            raise ValueError("content must not be empty")
        if len(value.encode("utf-8")) > MAX_CONTENT_BYTES:
            raise ValueError("content exceeds the 1 MB size limit")
        return value


class Finding(BaseModel):
    """A single normalized, evidence-backed issue (FR-008, FR-009, FR-010)."""

    id: str
    category: Category
    severity: Severity
    title: str
    line_start: int | None = None
    line_end: int | None = None
    description: str
    impact: str
    recommendation: str
    source: FindingSource
    explanation: str | None = None


class RemediationChange(BaseModel):
    """One explained change between the original and corrected configuration (FR-012, FR-014)."""

    change: str
    reason: str
    related_finding_id: str | None = None
    risk_classification: ChangeRisk | None = None
    tradeoffs: str | None = None


class Summary(BaseModel):
    """Aggregated severity counts."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ReviewResult(BaseModel):
    """Represents the completed analysis returned to the caller (FR-018, FR-019)."""

    review_id: str
    type: ReviewType
    summary: Summary
    findings: list[Finding] = Field(default_factory=list)
    metrics: dict[str, str] | None = None
    corrected_content: str | None = None
    original_content: str
    diff: str | None = None
    change_summary: list[RemediationChange] | None = None
    ai_summary: str | None = None
    ai_status: AiStatus = AiStatus.NOT_REQUESTED


class ErrorResponse(BaseModel):
    """Standard error envelope (PRD Section 35)."""

    error: str
    message: str
