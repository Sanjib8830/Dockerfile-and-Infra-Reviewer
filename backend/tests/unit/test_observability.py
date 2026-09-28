"""Observability unit tests: secret-safe review logging (T061)."""

from __future__ import annotations

import logging

from app.core.observability import ReviewTiming, log_review_outcome, new_review_id, timed


def test_new_review_id_is_unique_and_stable_format() -> None:
    first = new_review_id()
    second = new_review_id()
    assert first != second
    assert first.startswith("rev_")


def test_timed_records_elapsed_duration() -> None:
    timing = ReviewTiming()
    with timed(timing, "analysis_duration"):
        pass
    assert timing.analysis_duration is not None
    assert timing.analysis_duration >= 0


def test_log_review_outcome_does_not_include_raw_source(caplog) -> None:
    caplog.set_level(logging.INFO, logger="review")
    timing = ReviewTiming(analysis_duration=0.01, ai_duration=None)
    log_review_outcome(
        request_id="req-1",
        review_id="rev_abc123",
        file_type="dockerfile",
        timing=timing,
        success=True,
        ai_status="not_requested",
    )
    assert caplog.records
    record = caplog.records[-1]
    assert record.review_id == "rev_abc123"
    assert record.file_type == "dockerfile"
    assert not hasattr(record, "content")
    assert not hasattr(record, "secret")
