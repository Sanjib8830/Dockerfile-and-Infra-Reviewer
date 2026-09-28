"""Environment settings for optional Google AI configuration and bounded requests."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration resolved from environment variables.

    The AI provider is optional: when `google_api_key` is unset, the review
    pipeline MUST still return deterministic findings with `ai_status`
    `"not_requested"` (FR-016).
    """

    google_api_key: str | None = None
    google_ai_model: str = "gemini-3.1-flash-lite"
    ai_timeout_seconds: float = 15.0
    max_content_bytes: int = 1024 * 1024

    @property
    def ai_enabled(self) -> bool:
        return bool(self.google_api_key)


def load_settings() -> Settings:
    """Load settings from environment variables, applying documented defaults."""
    return Settings(
        google_api_key=os.environ.get("GOOGLE_API_KEY") or None,
        google_ai_model=os.environ.get("GOOGLE_AI_MODEL", "gemini-3.1-flash-lite"),
        ai_timeout_seconds=float(os.environ.get("AI_TIMEOUT_SECONDS", "15")),
        max_content_bytes=int(os.environ.get("MAX_CONTENT_BYTES", str(1024 * 1024))),
    )
