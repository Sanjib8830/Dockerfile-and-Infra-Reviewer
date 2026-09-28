<!--
Sync Impact Report
- Version change: uninstantiated template -> 1.0.0
- Modified principles: none; all five principles were established from the PRD
- Added sections: Security and Product Constraints; Development Workflow and Quality Gates
- Removed sections: none
- Follow-up TODOs: Confirm the original ratification date when the project history is known
-->

# Dockerfile & Infra Reviewer Constitution

## Core Principles

### I. Evidence Before AI

Deterministic parsers, scanners, and policy rules MUST establish known findings before
AI reasoning is invoked. Static-analysis severity MUST remain authoritative. AI output
MUST be advisory, grounded only in supplied source and findings, and MUST distinguish
detected facts from recommendations. This prevents hallucinated security claims and
keeps review results reproducible.

### II. Secure Non-Execution

The review path MUST NOT execute submitted Dockerfiles or Terraform configurations.
The application MUST NOT run `docker build`, `terraform apply`, arbitrary providers,
cloud operations, or untrusted shell commands as part of an MVP review. It MUST NOT
automatically deploy infrastructure, push images, modify repositories, or access cloud
credentials. This limits the impact of malicious or unsafe configuration input.

### III. Transparent Remediation

Every recommendation MUST preserve the original source and present the sequence
Original -> Finding -> Recommendation -> Corrected -> Diff. Suggested fixes MUST NOT
silently modify uploaded content. Terraform changes MUST be labeled according to their
risk, including `SAFE_CHANGE`, `POTENTIALLY_BREAKING_CHANGE`, `DESTRUCTIVE_CHANGE`, or
`REQUIRES_HUMAN_REVIEW`, and MUST require human review before application.

### IV. Contracted and Tested Results

Review results MUST use validated schemas for requests, findings, summaries, corrected
code, diffs, and errors. Each finding MUST have exactly one severity from `CRITICAL`,
`HIGH`, `MEDIUM`, `LOW`, or `INFO`. Changes to analyzers, API contracts, shared schemas,
AI output validation, or diff generation MUST include focused unit and integration tests.
AI failures MUST leave deterministic findings available to the caller.

### V. Small, Observable, Maintainable Changes

The system MUST favor the narrow MVP workflow over speculative infrastructure features.
Backend operations MUST expose health status and structured timing and outcome metadata
without logging secrets or raw sensitive source. New dependencies, architecture layers,
and provider-specific behavior MUST be justified by a product requirement or measured
benefit. Changes MUST preserve clear boundaries between API, analyzers, rules, AI,
validation, and diff services.

## Security and Product Constraints

The product MUST use React and TypeScript for the frontend and Python with FastAPI for
the backend. LangChain MUST orchestrate AI features using Google AI Studio / Gemini API
with `gemma-4-26b-a4b-it`, subject to validated structured output.

Secrets, tokens, passwords, private keys, connection strings, and cloud credentials MUST
be redacted before AI processing and MUST NOT appear in logs, telemetry, URLs, or error
responses. Submitted source and external scanner output MUST be treated as untrusted
input. The MVP MUST enforce a maximum input size of 1 MB per file and MUST use qualified
language for static estimates rather than inventing measured image-size savings.

The supported review types are Dockerfile and Terraform. The MVP review API is rooted at
`/api/v1` and MUST provide `GET /health` and `POST /review` with validated request and
response schemas.

## Development Workflow and Quality Gates

Implementation work MUST follow the repository's frontend and backend instructions in
`.github/instructions/` and the applicable skills in `.github/skills/`. Features are not
complete until code, focused unit tests, integration coverage, error handling, and
security review are present. CI MUST pass before merge.

The Dockerfile reviewer MUST cover root execution, embedded secrets, floating or unsafe
base images, package and cache issues, size optimization opportunities, and reliability
concerns. The Terraform reviewer MUST cover public exposure, unencrypted storage,
hardcoded credentials, broad IAM, missing logging or backups, and maintainability risks.
External scanner output MUST be normalized into the internal finding schema.

Pull requests MUST explain affected requirements, security implications, test evidence,
and any known limitations. Generated remediation MUST never bypass deterministic findings
or claim that infrastructure is safe to apply.

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

This constitution supersedes conflicting project practices. Every pull request and
release review MUST verify compliance with these principles, the PRD, and applicable
repository instructions. Exceptions MUST be documented with their scope, rationale,
risk, owner, and expiry or review date.

Amendments MUST update this file, include a Sync Impact Report, state the affected
principles and migration implications, and pass the same validation and review gates as
the change they govern. Versioning follows semantic versioning: MAJOR for incompatible
principle removals or redefinitions, MINOR for new or materially expanded governance,
and PATCH for clarifications or non-semantic corrections.

Compliance MUST be reviewed at feature completion, before release, and whenever the PRD,
technology stack, AI provider, or execution boundary changes. The repository guidance
files are supporting instructions; they MUST remain consistent with this constitution.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date is unknown | **Last Amended**: 2026-09-26
