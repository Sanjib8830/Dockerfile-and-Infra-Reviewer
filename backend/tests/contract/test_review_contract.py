"""Contract tests for GET /api/v1/health, invalid input, and unsupported types (T022)."""

from __future__ import annotations

from tests.conftest import SAMPLE_DOCKERFILE


def test_health_returns_ok(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_does_not_require_ai(client, monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_review_rejects_empty_content(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": ""})
    assert response.status_code == 400
    body = response.json()["detail"] if "detail" in response.json() else response.json()
    assert body["error"] == "INVALID_INPUT"


def test_review_rejects_oversized_content(client) -> None:
    oversized = "A" * (1024 * 1024 + 1)
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": oversized})
    assert response.status_code == 400
    body = response.json()["detail"] if "detail" in response.json() else response.json()
    assert body["error"] == "INVALID_INPUT"


def test_review_rejects_unsupported_type(client) -> None:
    response = client.post("/api/v1/review", json={"type": "yaml", "content": "key: value"})
    assert response.status_code == 400
    body = response.json()["detail"] if "detail" in response.json() else response.json()
    assert body["error"] == "UNSUPPORTED_FILE_TYPE"


def test_review_error_response_is_secret_safe(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": ""})
    text = response.text.lower()
    assert "traceback" not in text
    assert "api_key" not in text
    assert "/home/" not in text


def test_review_success_preserves_original_content(client) -> None:
    response = client.post("/api/v1/review", json={"type": "dockerfile", "content": SAMPLE_DOCKERFILE})
    assert response.status_code == 200
    body = response.json()
    assert body["original_content"] == SAMPLE_DOCKERFILE
