"""Optional AI-assisted explanation, remediation, and diff-explanation service.

Uses LangChain + Google AI Studio (`gemma-4-26b-a4b-it`) per PRD Sections 13-16.
AI output is strictly advisory (Constitution Principle I): it only ever receives
already-redacted source plus structured deterministic findings, and its output is
validated before use. Any failure degrades to `ai_status="unavailable"` without
ever discarding deterministic findings (FR-016).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.review import (
    AiStatus,
    ChangeRisk,
    Finding,
    RemediationChange,
    ReviewType,
)
from app.utils.redaction import redact_secrets

logger = logging.getLogger("review.ai")

_FORBIDDEN_SAFETY_CLAIMS = (
    "safe to apply",
    "guaranteed safe",
    "production-safe",
)


@dataclass
class AiAssistResult:
    """Validated, optional AI output for one review."""

    status: AiStatus
    ai_summary: str | None = None
    corrected_content: str | None = None
    change_summary: list[RemediationChange] | None = None
    explanations: dict[str, str] | None = None


class ReviewAssistant:
    """Coordinates the three separate prompts (explanation, remediation, diff) per PRD Section 16."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def assist(
        self,
        *,
        review_type: ReviewType,
        original_content: str,
        findings: list[Finding],
    ) -> AiAssistResult:
        if not self._settings.ai_enabled:
            return AiAssistResult(status=AiStatus.NOT_REQUESTED)

        if not findings:
            # Nothing to explain or remediate; do not fabricate issues (Constitution Principle I).
            return AiAssistResult(status=AiStatus.NOT_REQUESTED)

        redaction = redact_secrets(original_content)

        try:
            raw_response = self._invoke_model(
                review_type=review_type,
                redacted_content=redaction.content,
                findings=findings,
            )
            return self._validate_response(raw_response, review_type=review_type)
        except Exception:  # noqa: BLE001 - any AI failure must degrade gracefully (FR-016)
            logger.warning("ai_assist_failed", extra={"review_type": review_type.value})
            return AiAssistResult(status=AiStatus.UNAVAILABLE)

    # --- internals -------------------------------------------------------

    def _invoke_model(
        self,
        *,
        review_type: ReviewType,
        redacted_content: str,
        findings: list[Finding],
    ) -> str:
        """Call the configured LLM and return its raw structured-JSON response.

        Isolated so tests can monkeypatch this single method instead of the
        network-calling LangChain/Google GenAI client.
        """
        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415

        client = genai.Client(
            api_key=self._settings.google_api_key,
            http_options=types.HttpOptions(
                timeout=int(self._settings.ai_timeout_seconds * 1000),
            ),
        )
        prompt = self._build_prompt(review_type, redacted_content, findings)
        response = client.models.generate_content(
            model=self._settings.google_ai_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=self._response_schema(review_type),
            ),
        )
        return response.text or ""

    @staticmethod
    def _response_schema(review_type: ReviewType) -> dict[str, object]:
        change_properties: dict[str, object] = {
            "change": {"type": "string"},
            "reason": {"type": "string"},
            "related_finding_id": {"type": "string"},
            "risk_classification": {"type": "string"},
            "tradeoffs": {"type": "string"},
        }
        required_change_fields = ["change", "reason"]
        if review_type is ReviewType.TERRAFORM:
            change_properties["risk_classification"] = {
                "type": "string",
                "enum": [risk.value for risk in ChangeRisk],
            }
            required_change_fields.append("risk_classification")

        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "corrected_code": {"type": "string"},
                "change_summary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": change_properties,
                        "required": required_change_fields,
                    },
                },
                "explanations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "finding_id": {"type": "string"},
                            "explanation": {"type": "string"},
                        },
                        "required": ["finding_id", "explanation"],
                    },
                },
            },
            "required": ["summary", "corrected_code", "change_summary", "explanations"],
        }

    @staticmethod
    def _build_prompt(review_type: ReviewType, redacted_content: str, findings: list[Finding]) -> str:
        finding_payload = [
            {"rule": f.id, "severity": f.severity.value, "line": f.line_start, "message": f.title}
            for f in findings
        ]
        # Separate-prompt guardrails per PRD Section 16 / Section 34.
        return (
            "Use only the supplied code and scanner findings. Do not invent evidence. "
            "Clearly distinguish detected facts from recommendations. Never claim the "
            "configuration is safe to apply. Return compact JSON only, using exactly "
            "these keys: summary, corrected_code, change_summary, explanations. Each "
            "change_summary item must contain change, reason, and related_finding_id. "
            "Each explanations item must contain finding_id and explanation. "
            "For Terraform, every change_summary item must also include a "
            "risk_classification of SAFE_CHANGE, POTENTIALLY_BREAKING_CHANGE, "
            "DESTRUCTIVE_CHANGE, or REQUIRES_HUMAN_REVIEW. Keep each explanation and "
            "reason under 30 words. Use an empty string or array when a value is not "
            "needed.\n\n"
            f"file_type: {review_type.value}\n"
            f"code: {redacted_content}\n"
            f"findings: {json.dumps(finding_payload)}\n"
        )

    def _validate_response(self, raw_response: str, *, review_type: ReviewType) -> AiAssistResult:
        try:
            payload = json.loads(raw_response)
        except (TypeError, ValueError):
            return AiAssistResult(status=AiStatus.UNAVAILABLE)

        if not isinstance(payload, dict):
            return AiAssistResult(status=AiStatus.UNAVAILABLE)

        ai_summary = payload.get("summary")
        corrected_content = payload.get("corrected_code")
        raw_changes = payload.get("change_summary") or []
        explanations_raw = payload.get("explanations") or []

        if any(_contains_forbidden_claim(text) for text in (ai_summary, corrected_content)):
            return AiAssistResult(status=AiStatus.UNAVAILABLE)

        change_summary: list[RemediationChange] = []
        for entry in raw_changes:
            if not isinstance(entry, dict):
                return AiAssistResult(status=AiStatus.UNAVAILABLE)
            if _contains_forbidden_claim(entry.get("reason")) or _contains_forbidden_claim(entry.get("change")):
                return AiAssistResult(status=AiStatus.UNAVAILABLE)

            risk_raw = entry.get("risk_classification")
            risk_classification: ChangeRisk | None = None
            if risk_raw is not None:
                try:
                    risk_classification = ChangeRisk(risk_raw)
                except ValueError:
                    return AiAssistResult(status=AiStatus.UNAVAILABLE)

            # Terraform corrections MUST always carry a risk classification (FR-014).
            if review_type is ReviewType.TERRAFORM and risk_classification is None:
                return AiAssistResult(status=AiStatus.UNAVAILABLE)

            change_summary.append(
                RemediationChange(
                    change=str(entry.get("change", "")),
                    reason=str(entry.get("reason", "")),
                    related_finding_id=entry.get("related_finding_id"),
                    risk_classification=risk_classification,
                    tradeoffs=entry.get("tradeoffs"),
                )
            )

        explanations: dict[str, str] = {}
        for entry in explanations_raw:
            if not isinstance(entry, dict):
                continue
            finding_id = entry.get("finding_id")
            explanation = entry.get("explanation")
            if finding_id and explanation:
                explanations[str(finding_id)] = str(explanation)

        return AiAssistResult(
            status=AiStatus.AVAILABLE,
            ai_summary=str(ai_summary) if ai_summary else None,
            corrected_content=str(corrected_content) if corrected_content else None,
            change_summary=change_summary or None,
            explanations=explanations or None,
        )


def _contains_forbidden_claim(text: object) -> bool:
    if not isinstance(text, str):
        return False
    lowered = text.lower()
    return any(claim in lowered for claim in _FORBIDDEN_SAFETY_CLAIMS)
