"""`GET /api/v1/health` and `POST /api/v1/review` routes (PRD Sections 25-26)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.core.errors import InvalidInputError, ReviewFailedError, UnsupportedFileTypeError
from app.schemas.review import ReviewRequest, ReviewResult
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1")
_service = ReviewService()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness/readiness check. MUST NOT depend on the AI provider being available."""
    return {"status": "ok"}


@router.post("/review", response_model=ReviewResult)
def create_review(request: Request, payload: dict) -> ReviewResult:
    request_id = request.headers.get("x-request-id", "unknown")

    review_type = payload.get("type")
    if review_type not in ("dockerfile", "terraform"):
        raise UnsupportedFileTypeError()

    try:
        review_request = ReviewRequest.model_validate(payload)
    except ValidationError as exc:
        raise InvalidInputError(_first_error_message(exc)) from exc

    try:
        return _service.review(review_request, request_id=request_id)
    except Exception as exc:  # noqa: BLE001 - never leak internals to the caller
        raise ReviewFailedError() from exc


def _first_error_message(exc: ValidationError) -> str:
    errors = exc.errors()
    if errors:
        return str(errors[0].get("msg", "The submitted content is invalid."))
    return "The submitted content is invalid."
