"""Deterministic-analysis performance test: under 2 seconds per review (T059, SC-001)."""

from __future__ import annotations

import time

from tests.conftest import SAMPLE_DOCKERFILE, SAMPLE_TERRAFORM_PUBLIC_SSH


def test_dockerfile_deterministic_review_completes_quickly(client) -> None:
    start = time.perf_counter()
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    elapsed = time.perf_counter() - start
    assert response.status_code == 200
    assert elapsed < 2.0


def test_terraform_deterministic_review_completes_quickly(client) -> None:
    start = time.perf_counter()
    response = client.post("/api/v1/review", json={"type": "terraform", "content": SAMPLE_TERRAFORM_PUBLIC_SSH})
    elapsed = time.perf_counter() - start
    assert response.status_code == 200
    assert elapsed < 2.0
