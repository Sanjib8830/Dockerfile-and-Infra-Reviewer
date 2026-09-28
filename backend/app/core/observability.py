"""Review IDs and secret-safe structured logging/observability (PRD Section 37).

Logged fields are limited to request_id, review_id, file_type, durations, and
success/failure. Raw source, secrets, and credentials are never logged.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

logger = logging.getLogger("review")


def new_review_id() -> str:
    """Generate a stable, unique identifier for one review."""
    return f"rev_{uuid.uuid4().hex[:12]}"


@dataclass
class ReviewTiming:
    """Duration metadata for one review, in seconds."""

    analysis_duration: float | None = None
    ai_duration: float | None = None


@contextmanager
def timed(timing: ReviewTiming, attribute: str) -> Iterator[None]:
    """Record the elapsed wall-clock time for a block onto `timing.attribute`."""
    start = time.perf_counter()
    try:
        yield
    finally:
        setattr(timing, attribute, time.perf_counter() - start)


def log_review_outcome(
    *,
    request_id: str,
    review_id: str,
    file_type: str,
    timing: ReviewTiming,
    success: bool,
    ai_status: str,
) -> None:
    """Emit one secret-safe structured log line describing a completed review."""
    logger.info(
        "review_completed",
        extra={
            "request_id": request_id,
            "review_id": review_id,
            "file_type": file_type,
            "analysis_duration": timing.analysis_duration,
            "ai_duration": timing.ai_duration,
            "success": success,
            "ai_status": ai_status,
        },
    )
