# Implementation Plan: Dockerfile and Infrastructure Review

**Branch**: `001-dockerfile-infra-review` | **Date**: 2026-09-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-dockerfile-infra-review/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Users paste or upload a Dockerfile or Terraform file and receive an evidence-first review: deterministic
security/size/reliability/maintainability findings with severity and line references, an optional AI-generated
explanation and corrected configuration (never silently replacing the original), and a unified diff explaining
every meaningful change. The approach follows the PRD architecture: FastAPI backend running deterministic
analyzers and policy rules first, an optional LangChain + Google AI Studio (`gemma-4-26b-a4b-it`) explanation and
remediation layer with strict output validation, and a React + TypeScript frontend (Monaco editor) presenting
findings, corrected code, and a diff viewer without ever executing submitted infrastructure code.

## Technical Context

**Language/Version**: Backend: Python 3.11+. Frontend: TypeScript 5.x on Node.js 20 LTS.

**Primary Dependencies**: Backend: FastAPI, Pydantic v2, Uvicorn, python-multipart, LangChain,
langchain-google-genai, google-genai. Frontend: React 18, Vite, Monaco Editor. Deterministic analysis:
custom Python rule engine, with optional Hadolint/Trivy (Dockerfile) and TFLint/Checkov/`terraform validate`
(Terraform) integrations normalized into the internal finding schema.

**Storage**: N/A for the MVP. Reviews are processed in-memory/per-request and returned directly; no
persistent datastore is required because review history and authentication are out of scope (see spec
Assumptions).

**Testing**: Backend: pytest with FastAPI `TestClient` for contract/integration tests and unit tests per
analyzer rule. Frontend: Vitest + React Testing Library for component/hook tests.

**Target Platform**: Linux server (Docker/Kubernetes-compatible) for the backend API; evergreen desktop
browsers for the frontend, per the PRD's primary deployment target.

**Project Type**: Web application (frontend + backend), matching Option 2 below.

**Performance Goals**: Deterministic analysis completes in under 2 seconds per review (SC-001); AI-assisted
explanation/remediation targets under 15 seconds when enabled, per PRD Section 36.

**Constraints**: Maximum 1 MB input per file (FR-003); no execution of submitted Dockerfile/Terraform content
under any circumstance (FR-004, Constitution Principle II); secrets MUST be redacted before any AI processing
and MUST NOT appear in logs, telemetry, URLs, or errors (FR-017); AI failures MUST degrade gracefully without
losing deterministic findings (FR-016, SC-004).

**Scale/Scope**: Single-user, stateless review requests for the MVP; two supported input types (Dockerfile,
Terraform); no authentication, multi-tenant, or review-history scope in this feature (see spec Assumptions).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Evidence Before AI** — PASS. Plan sequences deterministic analyzers and rules before any AI call
  (Phase 1 data model separates `Finding` sourced from `static-analysis` from AI `Explanation`/`Remediation`
  outputs); AI prompts will only receive structured findings and source, never asked to invent evidence.
- **II. Secure Non-Execution** — PASS. No task in this plan builds Docker images, runs `terraform apply`,
  or executes submitted content; analyzers operate on parsed text only.
- **III. Transparent Remediation** — PASS. Data model keeps `original_content` immutable and separate from
  `corrected_content`/`diff`; Terraform corrections carry a `change_risk` classification
  (`SAFE_CHANGE`/`POTENTIALLY_BREAKING_CHANGE`/`DESTRUCTIVE_CHANGE`/`REQUIRES_HUMAN_REVIEW`) and the API
  contract never returns an "safe to apply" claim.
- **IV. Contracted and Tested Results** — PASS. `contracts/review-api.md` defines validated request/response
  schemas with a single severity enum per finding; quickstart and task planning require unit tests per rule
  and integration tests for `POST /review`.
- **V. Small, Observable, Maintainable Changes** — PASS. Scope stays within the MVP endpoints
  (`GET /health`, `POST /review`) with clear module boundaries (analyzers, rules, AI service, diff service,
  validation) and no speculative persistence or infrastructure execution added.

No violations identified; the Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-dockerfile-infra-review/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/            # POST /review, GET /health routers
│   ├── core/           # settings, logging, redaction utilities
│   ├── models/          # ReviewRequest/ReviewResult/Finding domain models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # ReviewService orchestration
│   ├── analyzers/       # DockerfileReviewer, TerraformReviewer
│   ├── rules/           # deterministic security/size/reliability rules
│   ├── ai/              # LangChain prompts, Gemma client, output validation
│   └── utils/           # diff engine, secret redaction
├── tests/
│   ├── contract/        # POST /review, GET /health contract tests
│   ├── integration/     # end-to-end review scenarios
│   └── unit/            # per-rule and per-service unit tests
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── components/       # FileTypeSelector, CodeEditor, FindingCard, DiffViewer, etc.
│   ├── pages/            # main review page
│   ├── services/         # review API client
│   ├── hooks/            # review submission/state hooks
│   ├── types/            # shared review/finding TypeScript types
│   └── utils/
├── tests/                # Vitest + React Testing Library specs
├── package.json
└── vite.config.ts
```

**Structure Decision**: Web application (Option 2), matching the PRD's recommended repository layout
(PRD Section 29). Backend lives under `backend/app` with API, analyzers, rules, AI, and diff/validation
modules kept as separate packages per Constitution Principle V. Frontend lives under `frontend/src` with a
service layer isolating API calls from presentation components per the frontend instructions.
