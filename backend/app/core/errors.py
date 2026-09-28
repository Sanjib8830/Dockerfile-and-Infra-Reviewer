"""Standardized, secret-safe API error responses (PRD Section 35).

None of these helpers ever include stack traces, provider credentials, internal
paths, or raw secret-bearing input in their output.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.schemas.review import ErrorResponse


class ReviewApiError(HTTPException):
    """Base class for review API errors with a stable machine-readable `error` code."""

    def __init__(self, status_code: int, error: str, message: str) -> None:
        super().__init__(status_code=status_code, detail=ErrorResponse(error=error, message=message).model_dump())


class InvalidInputError(ReviewApiError):
    """Empty content or content exceeding the 1 MB limit (FR-003)."""

    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, "INVALID_INPUT", message)


class UnsupportedFileTypeError(ReviewApiError):
    """An unsupported `type` value was submitted (FR-001, Edge Cases)."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            "UNSUPPORTED_FILE_TYPE",
            "Only Dockerfile and Terraform input are currently supported.",
        )


class ReviewFailedError(ReviewApiError):
    """Unexpected failure while producing a review; never leaks internal detail."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "REVIEW_FAILED",
            "The review could not be completed. Please try again.",
        )
