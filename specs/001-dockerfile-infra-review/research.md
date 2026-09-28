# Phase 0 Research: Dockerfile and Infrastructure Review

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

All Technical Context fields were resolved directly from `prd.md`, the repository constitution, and
`.github/instructions/`; no `NEEDS CLARIFICATION` markers remain. This document records the rationale for
each significant technology and architecture decision.

## Decision: Backend framework and language

- **Decision**: Python 3.11+ with FastAPI, Pydantic v2 schemas, and Uvicorn.
- **Rationale**: Mandated by the constitution's Security and Product Constraints section and the PRD's backend
  architecture (Section 27). FastAPI's dependency injection and Pydantic validation fit the requirement for
  validated request/response schemas (FR-008, FR-009, Constitution Principle IV) and async I/O suits calling an
  external AI provider without blocking deterministic analysis.
- **Alternatives considered**: Flask (rejected: no first-class async support or built-in schema validation);
  Django REST Framework (rejected: heavier than needed for a stateless review API).

## Decision: Frontend framework and language

- **Decision**: React 18 + TypeScript + Vite, with Monaco Editor for code input/diff display.
- **Rationale**: Mandated by the constitution and PRD Section 28. Monaco provides syntax highlighting, line
  numbers, and a diff view out of the box, satisfying FR-002 and the diff-viewer requirements without building a
  custom editor.
- **Alternatives considered**: CodeMirror (rejected: weaker built-in diff-view support); Next.js (rejected: no
  server-rendering requirement for this MVP; adds complexity not justified by Constitution Principle V).

## Decision: AI orchestration and provider

- **Decision**: LangChain as the orchestration layer calling Google AI Studio / Gemini API with the
  `gemma-4-26b-a4b-it` model, using separate prompts for explanation, remediation, and diff explanation
  (PRD Section 16).
- **Rationale**: Required by the constitution's Security and Product Constraints and PRD Sections 13–16.
  Separate prompts keep each AI call auditable and reduce hallucinated findings versus a single large prompt.
  AI output is treated as advisory only per Constitution Principle I.
- **Alternatives considered**: A single combined prompt (rejected: harder to validate and more prone to
  hallucination); direct model hosting (rejected: PRD specifies Google AI Studio as the provider).

## Decision: Deterministic analysis approach

- **Decision**: A custom Python rule engine implementing `DockerfileReviewer` and `TerraformReviewer` against a
  shared `Reviewer.analyze(source) -> ReviewResult` abstraction (PRD Section 18), with optional integration of
  Hadolint/Trivy (Dockerfile) and TFLint/Checkov/`terraform validate` (Terraform) whose output is normalized into
  the internal finding schema (FR-005, FR-006, FR-007).
- **Rationale**: Satisfies Constitution Principle I (evidence before AI) and IV (contracted, tested results).
  Treating external scanner output as untrusted input and normalizing it keeps the finding schema stable
  regardless of which underlying tool detected the issue.
- **Alternatives considered**: Relying solely on external scanners (rejected: inconsistent output formats and
  availability); relying solely on AI detection (rejected: violates Constitution Principle I and FR-010).

## Decision: Execution boundary

- **Decision**: No submitted Dockerfile or Terraform content is ever executed, built, or applied by the review
  service (FR-004, Constitution Principle II). Only text parsing and static analysis are performed.
- **Rationale**: PRD Section 32 and Constitution Principle II explicitly prohibit `docker build`, `terraform
  apply`, or arbitrary provider execution on the application host for the MVP.
- **Alternatives considered**: Sandboxed ephemeral build/plan execution (explicitly deferred to a future
  version per PRD Section 32; out of scope for this feature).

## Decision: Secret handling

- **Decision**: Pattern-based secret detection and redaction runs before any content is sent to the AI service;
  redacted values are replaced with a `[REDACTED]` marker and never logged (FR-017, PRD Section 33).
- **Rationale**: Required by the constitution's Security and Product Constraints and by FR-017/SC-005.
- **Alternatives considered**: Redacting only at the logging layer (rejected: would still send secrets to the
  external AI provider, violating the constitution).

## Decision: Terraform change-risk labeling

- **Decision**: Every AI-generated or rule-generated Terraform correction is tagged with one of
  `SAFE_CHANGE`, `POTENTIALLY_BREAKING_CHANGE`, `DESTRUCTIVE_CHANGE`, or `REQUIRES_HUMAN_REVIEW`, and the API
  and UI never state that generated Terraform is safe to apply (FR-014, PRD Section 20).
- **Rationale**: Required by Constitution Principle III and SC-006.
- **Alternatives considered**: A single boolean "safe/unsafe" flag (rejected: PRD explicitly calls for a
  four-state risk classification with human review required).

## Decision: Testing strategy

- **Decision**: Backend unit tests per deterministic rule and per service, FastAPI `TestClient`-based contract
  tests for `GET /health` and `POST /review`, and integration tests covering full review scenarios (PRD Section
  38). Frontend component/hook tests with Vitest + React Testing Library covering submission, rendering, and
  error states.
- **Rationale**: Required by Constitution Principle IV and the repository's backend/frontend instructions.
- **Alternatives considered**: End-to-end browser tests only (rejected as the sole strategy: too slow for
  per-rule regression coverage; may be added later as a complement, not a replacement).
