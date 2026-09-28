# Review API Contract

**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Data Model**: [data-model.md](../data-model.md)

Base path: `/api/v1` (Constitution: Security and Product Constraints; PRD Section 25–26).

MVP scope implements exactly two endpoints. Additional endpoints listed in the PRD (explain, remediate,
get-by-id, rules, examples) are explicitly out of scope for this feature and are not part of this contract.

## GET /health

**Purpose**: Liveness/readiness check for observability (Constitution Principle V; PRD Section 37).

**Request**: No parameters, no body.

**Response 200**:

```json
{
  "status": "ok"
}
```

No error responses are defined for this endpoint; it MUST NOT depend on the AI provider being available.

## POST /review

**Purpose**: Submit a Dockerfile or Terraform source for review and receive findings, an optional corrected
version, and a diff (FR-001 through FR-020).

### Request

```json
{
  "type": "dockerfile",
  "content": "FROM python:3.12\n...",
  "filename": "Dockerfile"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"dockerfile"` \| `"terraform"` | Yes | Must be one of the two supported values |
| `content` | string | Yes | Non-empty; UTF-8; max 1 MB |
| `filename` | string | No | Display-only metadata |

### Response 200 (success)

```json
{
  "review_id": "rev_123456",
  "type": "dockerfile",
  "summary": {
    "critical": 0,
    "high": 2,
    "medium": 3,
    "low": 1,
    "info": 2
  },
  "findings": [
    {
      "id": "DF-SEC-001",
      "category": "security",
      "severity": "HIGH",
      "title": "Container runs as root",
      "line_start": 12,
      "line_end": 12,
      "description": "The Docker image does not define a non-root runtime user.",
      "impact": "If the application is compromised, the attacker may obtain root-level privileges inside the container.",
      "recommendation": "Create a dedicated non-root user and switch to it using USER.",
      "source": "static-analysis",
      "explanation": "Running as root increases the impact of a container compromise."
    }
  ],
  "metrics": {
    "base_image": "python:3.12",
    "optimization_note": "Likely reduces image size because python:3.12-slim omits unused OS packages."
  },
  "original_content": "FROM python:3.12\n...",
  "corrected_content": "FROM python:3.12-slim\n...",
  "diff": "--- original\n+++ corrected\n-FROM python:3.12\n+FROM python:3.12-slim\n",
  "change_summary": [
    {
      "change": "Replaced base image with slim variant",
      "reason": "Reduces unnecessary OS packages and image size",
      "related_finding_id": "DF-SEC-001",
      "risk_classification": "SAFE_CHANGE"
    }
  ],
  "ai_summary": "The Dockerfile has 2 high and 3 medium issues, most notably running as root.",
  "ai_status": "available"
}
```

Every object in `findings` and `change_summary` follows the `Finding` and `RemediationChange` schemas defined in
[data-model.md](../data-model.md). `severity` MUST be exactly one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`
(FR-008). `original_content` MUST always equal the submitted `content` (FR-013). When `type` is `terraform`,
every entry in `change_summary` MUST include `risk_classification`, and the response MUST NOT state or imply
that the configuration is safe to apply (FR-014).

### Response 200 (AI unavailable, deterministic findings still returned)

```json
{
  "review_id": "rev_123457",
  "type": "terraform",
  "summary": { "critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0 },
  "findings": [
    {
      "id": "TF-SEC-010",
      "category": "security",
      "severity": "HIGH",
      "title": "SSH access exposed to the public internet",
      "description": "The security group allows ingress from 0.0.0.0/0 on port 22.",
      "impact": "Any host on the internet can attempt to reach SSH.",
      "recommendation": "Restrict cidr_blocks to a trusted range or use a private administrative path.",
      "source": "static-analysis"
    }
  ],
  "original_content": "resource \"aws_security_group\" \"app\" { ... }",
  "ai_summary": null,
  "ai_status": "unavailable"
}
```

Deterministic findings MUST be returned even when `ai_status` is `unavailable` (FR-016, SC-004). No
`corrected_content` or `diff` is required when AI-based remediation could not be generated.

### Response 400 (invalid input)

```json
{
  "error": "INVALID_INPUT",
  "message": "The uploaded file is empty."
}
```

Also used for oversized input (> 1 MB), with a message indicating the size limit.

### Response 400 (unsupported file type)

```json
{
  "error": "UNSUPPORTED_FILE_TYPE",
  "message": "Only Dockerfile and Terraform input are currently supported."
}
```

### Response 5xx (unexpected failure)

```json
{
  "error": "REVIEW_FAILED",
  "message": "The review could not be completed. Please try again."
}
```

MUST NOT include stack traces, provider credentials, internal paths, or raw secret-bearing content (Constitution:
Security and Product Constraints).

## Contract Test Expectations

- `GET /health` returns `200` with `{"status": "ok"}` and does not call the AI provider.
- `POST /review` with a valid Dockerfile payload returns `200` with a `ReviewResult` containing `original_content`
  equal to the request `content`.
- `POST /review` with empty `content` returns `400` with `error: "INVALID_INPUT"`.
- `POST /review` with `content` larger than 1 MB returns `400` with `error: "INVALID_INPUT"`.
- `POST /review` with an unsupported `type` returns `400` with `error: "UNSUPPORTED_FILE_TYPE"`.
- `POST /review` with a Terraform payload containing a public security-group rule returns a `HIGH` or higher
  severity finding and, if a correction is generated, a `risk_classification` on every `change_summary` entry.
- `POST /review` when the AI provider is simulated as unavailable still returns `200` with deterministic
  `findings` and `ai_status: "unavailable"`.
