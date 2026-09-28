# Tasks: Dockerfile and Infrastructure Review

**Input**: Design documents from `/specs/001-dockerfile-infra-review/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/review-api.md](./contracts/review-api.md), and
[quickstart.md](./quickstart.md)

**Tests**: Required. The specification and constitution require focused backend unit tests, API contract and
integration tests, frontend component/hook tests, and validation of security guarantees.

**Organization**: Tasks are grouped by user story so each can be implemented, tested, and demonstrated
independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in its phase after prerequisites are complete.
- **[Story]**: Maps a task to a user story in [spec.md](./spec.md).
- Every task includes an exact target file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the two deployable applications and their test/tooling baselines.

- [X] T001 Create backend package directories and Python package markers in `backend/app/__init__.py`, `backend/app/api/__init__.py`, `backend/app/core/__init__.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`, `backend/app/services/__init__.py`, `backend/app/analyzers/__init__.py`, `backend/app/rules/__init__.py`, `backend/app/ai/__init__.py`, and `backend/app/utils/__init__.py`
- [X] T002 Create pinned backend dependencies and development test tooling in `backend/requirements.txt`
- [X] T003 [P] Configure pytest discovery and test settings in `backend/pyproject.toml`
- [X] T004 Create the React + TypeScript Vite project manifest and scripts in `frontend/package.json`
- [X] T005 [P] Configure Vite and TypeScript compilation in `frontend/vite.config.ts`, `frontend/tsconfig.json`, and `frontend/tsconfig.app.json`
- [X] T006 [P] Configure Vitest with the browser-like test environment in `frontend/vitest.config.ts` and `frontend/src/test/setup.ts`
- [X] T007 [P] Create backend runtime container configuration in `backend/Dockerfile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the common validated data contract, safety boundary, review orchestration seam, and API
shell used by every user story.

**CRITICAL**: Complete this phase before beginning user-story phases.

- [X] T008 Define Pydantic schemas for `ReviewRequest`, `ReviewResult`, `Finding`, `Summary`, `RemediationChange`, `ReviewType`, `Severity`, `Category`, `AiStatus`, and `ChangeRisk` in `backend/app/schemas/review.py`; enforce verbatim constraints: `content` is "Required; non-empty; UTF-8 text; max 1 MB", `type` is `dockerfile` or `terraform`, every `severity` is exactly `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`, and Terraform `risk_classification` is required
- [X] T009 [P] Implement typed domain result and reviewer protocol abstractions in `backend/app/models/review.py`, including `Reviewer.analyze(source) -> ReviewResult`
- [X] T010 [P] Implement standardized `INVALID_INPUT`, `UNSUPPORTED_FILE_TYPE`, and `REVIEW_FAILED` API error responses that never include stack traces, provider credentials, internal paths, or raw secret-bearing input in `backend/app/core/errors.py`
- [X] T011 [P] Implement secret-detection and `[REDACTED]` replacement utilities for tokens, passwords, private keys, connection strings, and cloud credentials in `backend/app/utils/redaction.py`
- [X] T012 [P] Implement unified-diff generation that accepts distinct original and corrected content in `backend/app/utils/diff.py`
- [X] T013 [P] Implement review IDs, duration metadata, and secret-safe structured logging in `backend/app/core/observability.py`
- [X] T014 Create environment settings for optional Google AI configuration and bounded request settings in `backend/app/core/config.py`
- [X] T015 Implement `ReviewService` orchestration in `backend/app/services/review_service.py` that preserves `original_content`, chooses a reviewer by `type`, runs deterministic analysis before any optional AI step, and returns deterministic findings if AI is unavailable
- [X] T016 Implement `GET /api/v1/health` and the `POST /api/v1/review` router shell in `backend/app/api/routes/review.py` using the schemas and error responses
- [X] T017 Create the FastAPI application, router registration, and exception-handler wiring in `backend/app/main.py`
- [X] T018 [P] Define shared frontend review, finding, remediation, severity, error, and request types in `frontend/src/types/review.ts` that mirror `contracts/review-api.md`
- [X] T019 [P] Implement a typed `/api/v1` client and normalized API-error parsing in `frontend/src/services/reviewApi.ts`
- [X] T020 [P] Create frontend application entry points and global styles in `frontend/index.html`, `frontend/src/main.tsx`, and `frontend/src/styles.css`
- [X] T021 Create the main application shell and review-state boundary in `frontend/src/App.tsx`
- [X] T022 [P] Write backend contract tests for `GET /api/v1/health`, empty content, input larger than 1 MB, unsupported type, and secret-safe error messages in `backend/tests/contract/test_review_contract.py`
- [X] T023 [P] Write unit tests for secret redaction, diff generation, severity-summary counting, and the invariant that `original_content` always equals submitted content in `backend/tests/unit/test_foundation.py`

**Checkpoint**: The shared foundation validates request shapes and limits, never executes user content, exposes a
health endpoint, retains original content unchanged, and has an API shell ready for both review types.

---

## Phase 3: User Story 1 - Review a Dockerfile (Priority: P1) MVP

**Goal**: Let a user submit a Dockerfile and receive evidence-backed deterministic security, optimization,
reliability, and maintainability findings, plus an optional correction and diff.

**Independent Test**: Submit a Dockerfile containing a root runtime user, floating base-image tag, pip cache,
and broad `COPY`. Confirm severity-tagged findings include evidence and source locations; confirm the original
remains unchanged and deterministic results remain available if the optional AI step fails.

### Tests for User Story 1

- [X] T024 [P] [US1] Write unit tests for Dockerfile root user, floating/`latest` base image, secret-like `ENV`/`ARG`, unsafe package install, dangerous permission, cache retention, broad `COPY`, missing `.dockerignore` opportunity, and missing healthcheck detection in `backend/tests/unit/test_dockerfile_rules.py`
- [X] T025 [P] [US1] Write `POST /api/v1/review` contract tests for valid Dockerfile responses, required `Finding` fields, allowed severity values, and preserved `original_content` in `backend/tests/contract/test_dockerfile_review_contract.py`
- [X] T026 [P] [US1] Write integration tests for Dockerfile review including an AI-unavailable fallback that retains deterministic findings in `backend/tests/integration/test_dockerfile_review.py`

### Implementation for User Story 1

- [X] T027 [P] [US1] Implement deterministic Dockerfile security rules with stable `DF-SEC-*` IDs and line-number capture in `backend/app/rules/dockerfile_security.py`
- [X] T028 [P] [US1] Implement deterministic Dockerfile size and maintainability rules with stable IDs and qualified optimization language in `backend/app/rules/dockerfile_optimization.py`
- [X] T029 [P] [US1] Implement deterministic Dockerfile reliability rules with stable IDs and line-number capture in `backend/app/rules/dockerfile_reliability.py`
- [X] T030 [US1] Implement `DockerfileReviewer` to combine rule outputs, normalize every result to the `Finding` schema, and calculate `Summary` counts in `backend/app/analyzers/dockerfile_reviewer.py`
- [X] T031 [US1] Connect `DockerfileReviewer` to `ReviewService` for `type="dockerfile"` in `backend/app/services/review_service.py`
- [X] T032 [US1] Implement the optional AI client, separate explanation/remediation/diff prompts, pre-prompt redaction, and strict structured-output validation in `backend/app/ai/review_assistant.py`; it MUST use supplied source and structured findings only and MUST return `ai_status="unavailable"` without removing deterministic findings on any failure
- [X] T033 [US1] Integrate validated Dockerfile explanation/remediation output, unified diff, and `change_summary` into `ReviewService` in `backend/app/services/review_service.py`
- [X] T034 [P] [US1] Implement Dockerfile/Terraform type selection, paste input, clear action, upload validation, and example loading in `frontend/src/components/ReviewInput.tsx`
- [X] T035 [P] [US1] Implement Monaco-based source editor with line numbers and safe text rendering in `frontend/src/components/CodeEditor.tsx`
- [X] T036 [US1] Implement review submission, loading state, request errors, and AI-unavailable display state in `frontend/src/hooks/useReview.ts`
- [X] T037 [US1] Render Dockerfile summary counts and evidence-backed finding cards with category, severity, location, impact, recommendation, and source in `frontend/src/components/ReviewResults.tsx`
- [X] T038 [US1] Compose the Dockerfile review workflow in `frontend/src/pages/ReviewPage.tsx` and connect it in `frontend/src/App.tsx`
- [X] T039 [P] [US1] Write frontend tests for Dockerfile selection, paste/upload/clear behavior, review loading, findings, error display, and AI-unavailable fallback in `frontend/tests/ReviewPage.dockerfile.test.tsx`

**Checkpoint**: A user can independently submit a Dockerfile and receive deterministic findings within the target
static-review path, with an optional validated explanation/remediation path and no execution of submitted content.

---

## Phase 4: User Story 2 - Review Terraform Infrastructure (Priority: P1)

**Goal**: Let a user submit Terraform and receive evidence-backed security, reliability, and maintainability
findings, including public-exposure detection and risk-labeled remediations requiring human review.

**Independent Test**: Submit a Terraform security group exposing port 22 to `0.0.0.0/0` plus unencrypted storage.
Verify `HIGH` (or higher) security findings, source locations, and that every generated remediation carries a
risk classification and never says it is safe to apply.

### Tests for User Story 2

- [X] T040 [P] [US2] Write unit tests for public sensitive-port exposure, public resource/bucket, unencrypted storage, hardcoded credentials, wildcard IAM, missing logging/backups, and missing tags in `backend/tests/unit/test_terraform_rules.py`
- [X] T041 [P] [US2] Write `POST /api/v1/review` contract tests for valid Terraform responses and the requirement that every generated `change_summary` entry includes `risk_classification` in `backend/tests/contract/test_terraform_review_contract.py`
- [X] T042 [P] [US2] Write integration tests for Terraform review, public SSH severity, human-review warnings, and AI-unavailable fallback in `backend/tests/integration/test_terraform_review.py`

### Implementation for User Story 2

- [X] T043 [P] [US2] Implement deterministic Terraform security rules with stable `TF-SEC-*` IDs, including public sensitive ports, public resources, unencrypted storage, hardcoded credentials, and broad IAM in `backend/app/rules/terraform_security.py`
- [X] T044 [P] [US2] Implement deterministic Terraform reliability and maintainability rules for logging, backups, tags, duplication, and hardcoded values in `backend/app/rules/terraform_quality.py`
- [X] T045 [US2] Implement `TerraformReviewer` to normalize all rule output into `Finding` objects with summary counts and source lines in `backend/app/analyzers/terraform_reviewer.py`
- [X] T046 [US2] Connect `TerraformReviewer` to `ReviewService` for `type="terraform"` and require `SAFE_CHANGE`, `POTENTIALLY_BREAKING_CHANGE`, `DESTRUCTIVE_CHANGE`, or `REQUIRES_HUMAN_REVIEW` on each remediation in `backend/app/services/review_service.py`
- [X] T047 [US2] Extend AI remediation validation to reject Terraform corrections lacking a risk classification or claiming that configuration is safe to apply in `backend/app/ai/review_assistant.py`
- [X] T048 [US2] Add Terraform-specific category rendering and explicit human-review/change-risk warnings in `frontend/src/components/ReviewResults.tsx`
- [X] T049 [P] [US2] Write frontend tests for public-SSH rendering, severity display, risk-classification badges, and human-review warnings in `frontend/tests/ReviewPage.terraform.test.tsx`

**Checkpoint**: A user can independently review Terraform and receive static security/reliability/maintainability
findings and risk-classified recommendations without any Terraform execution or safe-to-apply claim.

---

## Phase 5: User Story 3 - Understand and Act on Findings (Priority: P2)

**Goal**: Let users explore findings and compare/export a recommended configuration while preserving the original
input.

**Independent Test**: Complete either review flow, inspect a finding, view original and corrected code side by
side with a diff, copy/download corrected artifacts, and verify that the original editor content does not change.

### Tests for User Story 3

- [X] T050 [P] [US3] Write frontend tests for finding filters, source-line navigation, tab switching, copy actions, download output, and original-content preservation in `frontend/tests/ReviewExperience.test.tsx`
- [X] T051 [P] [US3] Write backend tests asserting `diff` and `change_summary` are present whenever `corrected_content` is present and that static estimates use qualified language in `backend/tests/unit/test_remediation_output.py`

### Implementation for User Story 3

- [X] T052 [P] [US3] Implement severity/category filters and source-line selection behavior in `frontend/src/components/FindingsList.tsx`
- [X] T053 [P] [US3] Implement corrected-code display, unified/side-by-side diff, and per-change explanation view in `frontend/src/components/DiffViewer.tsx`
- [X] T054 [US3] Implement copy-diff, copy-corrected-content, and explicit download actions that never mutate submitted input in `frontend/src/utils/exportReview.ts`
- [X] T055 [US3] Add Overview, Security, Optimization, Reliability, Corrected Version, and Diff result views with stable accessible tab behavior in `frontend/src/components/ReviewResults.tsx`
- [X] T056 [US3] Integrate finding navigation and export actions into `frontend/src/pages/ReviewPage.tsx`

**Checkpoint**: A user can independently understand findings, inspect evidence, compare original and recommended
content, and explicitly export a correction without silently changing the original source.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify security, performance, accessibility, observability, and full quickstart behavior across all
user stories.

- [X] T057 [P] Add external-scanner adapter interfaces and untrusted-output normalization tests for Hadolint/Trivy/TFLint/Checkov-compatible results in `backend/app/analyzers/external_scanners.py` and `backend/tests/unit/test_external_scanners.py`
- [X] T058 [P] Add timeout, malformed AI response, and secret-redaction-before-prompt regression tests in `backend/tests/integration/test_ai_failure_modes.py`
- [X] T059 [P] Add a deterministic-analysis performance test enforcing the under-2-second target for representative Dockerfile and Terraform inputs in `backend/tests/integration/test_review_performance.py`
- [X] T060 [P] Add keyboard navigation, focus state, status-announcement, and visible-text safety tests in `frontend/tests/ReviewAccessibility.test.tsx`
- [X] T061 [P] Add request/review timing, scanner timing, AI timing, and success/failure logging without raw source or secrets in `backend/app/core/observability.py` and validate it in `backend/tests/unit/test_observability.py`
- [X] T062 Add end-to-end quickstart scenarios for Dockerfile, Terraform, AI fallback, and input validation in `backend/tests/integration/test_quickstart_scenarios.py`
- [X] T063 Run and reconcile all scenarios in `specs/001-dockerfile-infra-review/quickstart.md`, updating implementation tests rather than weakening the specification
- [X] T064 Add repository setup, local validation, security-boundary, and known-limitation instructions in `README.md`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1, Dockerfile)**: Depends on Phase 2; this is the MVP slice.
- **Phase 4 (US2, Terraform)**: Depends on Phase 2 and may proceed in parallel with Phase 3, although it reuses the same review service and AI client files; in a single-agent sequence, complete Phase 3 first.
- **Phase 5 (US3, Review experience)**: Depends on the result format from Phases 3 and 4; may be partially developed after Phase 3 but is complete after both result types exist.
- **Phase 6 (Polish)**: Depends on desired story phases being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2. It is the recommended MVP delivery.
- **US2 (P1)**: Independent after Phase 2 at the domain level; shares foundational service and UI result surfaces.
- **US3 (P2)**: Depends on review-result output introduced by US1; Terraform-specific review-experience coverage is complete after US2.

### Parallel Opportunities

- Setup tasks T003, T005, T006, and T007 can run in parallel after their respective project roots exist.
- Foundational tasks T009–T013 and T018–T020 can run in parallel after T001–T007.
- US1 test tasks T024–T026 and rule tasks T027–T029 can run in parallel.
- US2 test tasks T040–T042 and rule tasks T043–T044 can run in parallel.
- US3 test tasks T050–T051 and component tasks T052–T053 can run in parallel.
- Polish tasks T057–T061 can run in parallel.

## Parallel Execution Examples

### User Story 1

```text
Task: "Write Dockerfile rule unit tests in backend/tests/unit/test_dockerfile_rules.py"
Task: "Write Dockerfile API contract tests in backend/tests/contract/test_dockerfile_review_contract.py"
Task: "Implement Dockerfile security rules in backend/app/rules/dockerfile_security.py"
Task: "Implement Dockerfile optimization rules in backend/app/rules/dockerfile_optimization.py"
Task: "Implement Monaco code editor in frontend/src/components/CodeEditor.tsx"
```

### User Story 2

```text
Task: "Write Terraform rule unit tests in backend/tests/unit/test_terraform_rules.py"
Task: "Write Terraform API contract tests in backend/tests/contract/test_terraform_review_contract.py"
Task: "Implement Terraform security rules in backend/app/rules/terraform_security.py"
Task: "Implement Terraform quality rules in backend/app/rules/terraform_quality.py"
```

### User Story 3

```text
Task: "Write review-experience tests in frontend/tests/ReviewExperience.test.tsx"
Task: "Write remediation-output tests in backend/tests/unit/test_remediation_output.py"
Task: "Implement findings list in frontend/src/components/FindingsList.tsx"
Task: "Implement diff viewer in frontend/src/components/DiffViewer.tsx"
```

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phases 1 and 2.
2. Complete Phase 3 through T039.
3. Run the Dockerfile quickstart scenario and the US1 contract/integration/frontend tests.
4. Demonstrate a static review with the AI provider unavailable, proving deterministic evidence remains useful.

### Incremental Delivery

1. Deliver Dockerfile review (US1) first as the MVP.
2. Add Terraform review (US2) while keeping the same contracts and evidence-first behavior.
3. Add the richer investigation and export workflow (US3).
4. Complete the cross-cutting security, accessibility, performance, and quickstart validation phase.

## Notes

- Every task uses the required checkbox, ID, optional parallel marker, story label where applicable, and exact file path.
- Tasks T024–T026, T040–T042, and T050–T051 are written before their associated implementation tasks, per the constitution's required test coverage.
- Do not execute submitted Dockerfile or Terraform content at any task stage.
