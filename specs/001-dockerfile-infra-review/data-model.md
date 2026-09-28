# Phase 1 Data Model: Dockerfile and Infrastructure Review

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document defines the domain entities used by the review pipeline. It describes fields, relationships, and
validation rules only; it is not an implementation (no ORM models or database schemas), consistent with the
constitution's "no persistent datastore" scope for the MVP.

## ReviewRequest

Represents the user's submitted review input (FR-001, FR-002, FR-003).

| Field | Type | Description | Validation Rules |
|---|---|---|---|
| `type` | enum: `dockerfile`, `terraform` | Selected input type | Required; must be one of the two supported values (FR-001) |
| `content` | string | Raw pasted or uploaded source text | Required; non-empty; UTF-8 text; max 1 MB (FR-003) |
| `filename` | string (optional) | Original uploaded filename, if provided | Optional; used only for display, never for execution |

**Validation rules**:

- Empty `content` is rejected with `INVALID_INPUT` (Edge Cases).
- `content` exceeding 1 MB is rejected with `INVALID_INPUT` before analysis begins (FR-003).
- An unsupported `type` value is rejected with `UNSUPPORTED_FILE_TYPE` (Edge Cases, PRD Section 35).

## ReviewResult

Represents the completed analysis returned to the caller (FR-018, FR-019).

| Field | Type | Description | Validation Rules |
|---|---|---|---|
| `review_id` | string | Stable identifier for this review | Required; unique per request |
| `type` | enum: `dockerfile`, `terraform` | Echoes the request's input type | Required |
| `summary` | Summary | Counts of findings by severity | Required; counts MUST sum to `findings.length` |
| `findings` | Finding[] | Normalized findings from deterministic analysis | Required; may be empty (Edge Cases: "no findings" case) |
| `metrics` | object (optional) | Static, qualified size/optimization observations (PRD Section 19) | Optional; MUST use qualified language, never exact unmeasured savings (FR-020) |
| `corrected_content` | string (optional) | AI- or rule-generated corrected configuration | Optional; present only when a distinct correction was generated (FR-011); MUST NOT overwrite `original_content` |
| `original_content` | string | Echo of the submitted `content`, preserved unmodified | Required; MUST always equal the original `ReviewRequest.content` (FR-013, Constitution Principle III) |
| `diff` | string (optional) | Unified diff between `original_content` and `corrected_content` | Required whenever `corrected_content` is present (FR-012) |
| `change_summary` | RemediationChange[] (optional) | Explanations for each meaningful change in the diff | Optional; present whenever `diff` is present |
| `ai_summary` | string (optional) | Natural-language review summary from the optional AI service | Optional; omitted or marked unavailable when AI fails (FR-016) |
| `ai_status` | enum: `available`, `unavailable`, `not_requested` | Indicates whether AI-assisted content succeeded | Required |

## Finding

Represents a single normalized, evidence-backed issue (FR-008, FR-009, FR-010).

| Field | Type | Description | Validation Rules |
|---|---|---|---|
| `id` | string | Stable rule identifier (e.g., `DF-SEC-001`) | Required; unique within a review |
| `category` | enum: `security`, `size`, `performance`, `reliability`, `maintainability`, `best-practice` | Finding category | Required |
| `severity` | enum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` | Exactly one severity | Required; set by the deterministic rule, never overridden by AI (FR-010) |
| `title` | string | Short human-readable title | Required |
| `line_start` | integer (optional) | First affected line | Optional; included when available |
| `line_end` | integer (optional) | Last affected line | Optional; included when available |
| `description` | string | What was detected | Required |
| `impact` | string | Why it matters | Required |
| `recommendation` | string | Suggested remediation | Required |
| `source` | enum: `static-analysis`, `external-scanner` | Where the finding originated | Required; external scanner output MUST be normalized to this schema before use |
| `explanation` | string (optional) | AI-generated plain-language explanation | Optional; MUST be grounded only in this finding's evidence (Constitution Principle I) |

## RemediationChange

Represents one explained change between the original and corrected configuration (FR-012, FR-014).

| Field | Type | Description | Validation Rules |
|---|---|---|---|
| `change` | string | What changed | Required |
| `reason` | string | Why it changed | Required |
| `related_finding_id` | string (optional) | The `Finding.id` this change addresses, if any | Optional |
| `risk_classification` | enum: `SAFE_CHANGE`, `POTENTIALLY_BREAKING_CHANGE`, `DESTRUCTIVE_CHANGE`, `REQUIRES_HUMAN_REVIEW` | Risk level of applying this change | Required for Terraform reviews (FR-014); optional for Dockerfile reviews |
| `tradeoffs` | string (optional) | Trade-offs of the change | Optional |

## Summary

Aggregated severity counts shown at the top of a review result (PRD Section 10, Section 22).

| Field | Type | Description | Validation Rules |
|---|---|---|---|
| `critical` | integer | Count of `CRITICAL` findings | Required; >= 0 |
| `high` | integer | Count of `HIGH` findings | Required; >= 0 |
| `medium` | integer | Count of `MEDIUM` findings | Required; >= 0 |
| `low` | integer | Count of `LOW` findings | Required; >= 0 |
| `info` | integer | Count of `INFO` findings | Required; >= 0 |

## Relationships

```text
ReviewRequest (1) ---> (1) ReviewResult
ReviewResult (1) ---> (0..n) Finding
ReviewResult (1) ---> (0..n) RemediationChange
ReviewResult (1) ---> (1) Summary
Finding (0..1) <--- (0..n) RemediationChange   # via related_finding_id
```

## State / Status Notes

- `ReviewResult` has no persisted state machine in the MVP; each request produces one immutable result (no
  update/edit operations), consistent with the "no persistent datastore" scope.
- `ai_status` is the only status-like field and reflects a single attempt per review: `available` (AI content
  present and validated), `unavailable` (AI was attempted but failed/timed out/returned invalid output), or
  `not_requested` (AI step was skipped, e.g., provider not configured).
