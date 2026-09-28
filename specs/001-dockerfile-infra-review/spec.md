# Feature Specification: Dockerfile and Infrastructure Review

**Feature Branch**: `001-dockerfile-infra-review`

**Created**: 2026-09-26

**Status**: Draft

**Input**: User description: Dockerfile and Infra Reviewer product requirements from `prd.md`, with repository constitution and available skills as governing context.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a Dockerfile (Priority: P1)

A developer or DevOps engineer submits a Dockerfile and receives an evidence-backed review of security, image-size optimization, reliability, and maintainability concerns.

**Why this priority**: Dockerfile review is the primary workflow and provides immediate value before a container image is built or committed.

**Independent Test**: Submit a representative Dockerfile containing a root runtime user, a floating base-image tag, and package-cache retention. Verify that the review returns findings with severity, line references, explanations, recommendations, and a corrected version with a diff.

**Acceptance Scenarios**:

1. **Given** a valid Dockerfile, **When** the user submits it for review, **Then** the system returns a summary, categorized findings, severity, line references where available, recommendations, corrected code, and a unified diff.
2. **Given** a Dockerfile with deterministic issues, **When** the review is generated, **Then** deterministic findings remain present even if an optional explanation or remediation service is unavailable.
3. **Given** a Dockerfile review result, **When** the user views a recommendation, **Then** the original source remains available and unchanged beside the corrected version.

---

### User Story 2 - Review Terraform Infrastructure (Priority: P1)

A cloud or platform engineer submits Terraform configuration and receives a review of security exposure, reliability risks, and maintainability concerns before applying it.

**Why this priority**: Terraform can create costly or publicly exposed infrastructure, so identifying risks before deployment is a core product promise.

**Independent Test**: Submit Terraform containing an unrestricted SSH rule and unencrypted storage. Verify that the review identifies the risks, shows affected lines when available, proposes safer alternatives, and clearly labels changes requiring human review.

**Acceptance Scenarios**:

1. **Given** valid Terraform configuration, **When** the user submits it for review, **Then** the system returns security, reliability, and maintainability findings with severity, explanations, recommendations, corrected configuration, and a diff.
2. **Given** Terraform that exposes a sensitive port to `0.0.0.0/0`, **When** the review is generated, **Then** the system reports the public exposure as a high-impact security finding and recommends restricting access or using a private administrative path.
3. **Given** a generated Terraform correction, **When** the user views the result, **Then** the system states that the configuration requires human review and does not claim it is safe to apply.

---

### User Story 3 - Understand and Act on Findings (Priority: P2)

A developer who is not an infrastructure specialist can understand why findings matter, inspect the exact changes proposed, and decide whether to export the corrected configuration.

**Why this priority**: Clear explanations and transparent diffs turn scanner output into an actionable developer workflow rather than an opaque list of warnings.

**Independent Test**: Use a review containing findings at multiple severities. Verify that the user can filter or inspect findings, navigate to their source lines, compare original and corrected code, copy the diff, and download the corrected file without changing the original.

**Acceptance Scenarios**:

1. **Given** a completed review, **When** the user opens a finding, **Then** the interface shows its category, severity, source location when available, impact, recommendation, and supporting evidence.
2. **Given** original and corrected configurations, **When** the user opens the diff, **Then** every meaningful change is visible and accompanied by an explanation of its purpose and trade-offs when relevant.
3. **Given** the user selects an export action, **When** the corrected file is downloaded, **Then** the downloaded content matches the displayed corrected version and the original submitted content remains unchanged.

### Edge Cases

- Empty input MUST be rejected with a clear validation message.
- Input larger than 1 MB per file MUST be rejected before review processing.
- Unsupported file types MUST be rejected with a message identifying the supported Dockerfile and Terraform inputs.
- Invalid or partially formed configuration MUST return useful validation or parsing feedback without executing the input.
- Secret-like values MUST be detected and redacted before optional AI processing; the user MUST be informed that redaction occurred without exposing the secret.
- Scanner failure MUST not prevent other available deterministic checks from returning results.
- AI timeout, provider failure, malformed output, or incomplete output MUST leave deterministic findings available and clearly mark unavailable AI content.
- A review with no findings MUST state that no supported issues were detected rather than implying that the configuration is guaranteed safe.
- A generated correction that cannot be validated or differs unexpectedly MUST not replace the original or be presented as approved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept exactly two review input types for the MVP: Dockerfile and Terraform.
- **FR-002**: The system MUST allow users to paste source content and upload a corresponding file.
- **FR-003**: The system MUST reject empty, unsupported, or oversized input with a structured, user-readable error.
- **FR-004**: The system MUST analyze submitted content without executing Dockerfiles, Terraform configurations, providers, cloud operations, or arbitrary commands.
- **FR-005**: The system MUST produce deterministic findings for supported security, optimization, reliability, maintainability, and best-practice rules.
- **FR-006**: Dockerfile analysis MUST cover, at minimum, root execution, embedded secrets, floating or unsafe base images, unsafe package installation, dangerous permissions, cache retention, broad copy patterns, missing `.dockerignore` opportunities, and relevant reliability concerns.
- **FR-007**: Terraform analysis MUST cover, at minimum, public sensitive-port exposure, public resources, unencrypted storage, hardcoded secrets, broad IAM permissions, missing logging or backups, missing tags, and relevant maintainability concerns.
- **FR-008**: Every finding MUST have exactly one severity: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`.
- **FR-009**: Every finding MUST include a stable identifier, category, title, description, impact, recommendation, and source; line references MUST be included when available.
- **FR-010**: Deterministic severity and findings MUST take precedence over any AI-generated interpretation.
- **FR-011**: The system MUST generate a corrected or recommended configuration only when the result can be returned as a distinct version from the original.
- **FR-012**: The system MUST provide a unified diff between the original and recommended configuration and explain meaningful changes.
- **FR-013**: The system MUST preserve the original submitted source and MUST require an explicit user action before copying or downloading a corrected version.
- **FR-014**: The system MUST clearly identify Terraform changes that are safe-looking, potentially breaking, destructive, or require human review, and MUST never claim Terraform is safe to apply.
- **FR-015**: Optional AI assistance MUST explain findings, assess context, generate remediation, explain diffs, and summarize reviews using only supplied source and evidence.
- **FR-016**: AI output MUST be validated before display; malformed or unavailable AI output MUST degrade gracefully without removing deterministic findings.
- **FR-017**: The system MUST redact secrets, tokens, passwords, private keys, connection strings, and cloud credentials before AI processing and MUST NOT expose them in logs, telemetry, URLs, or errors.
- **FR-018**: The system MUST provide a health check and a review operation through the product's documented review interface.
- **FR-019**: The system MUST report review status, validation errors, scanner failures, and AI availability clearly to the user.
- **FR-020**: The system MUST avoid unmeasured claims about exact image-size reductions and MUST label static estimates as estimates or likely opportunities.

### Key Entities *(include if feature involves data)*

- **Review Request**: The user's selected input type and submitted source content, subject to size and secret-handling rules.
- **Review Result**: A completed analysis containing summary counts, findings, optional metrics, corrected content, diff, and AI availability status.
- **Finding**: A normalized, evidence-backed issue with identifier, category, severity, location, explanation, impact, recommendation, and source.
- **Remediation Change**: A proposed modification describing the changed content, reason, affected risk, and any trade-off or human-review classification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of valid representative Dockerfile and Terraform review requests return deterministic findings or a clear no-findings result within 2 seconds, excluding optional AI time.
- **SC-002**: At least 90% of first-time users can submit a valid Dockerfile or Terraform file and locate the highest-severity finding without assistance.
- **SC-003**: 100% of returned findings use one allowed severity and include the required evidence and recommendation fields.
- **SC-004**: 100% of tested AI outage, timeout, malformed-output, and scanner-failure cases preserve the deterministic findings available from the review.
- **SC-005**: 100% of tested secret-bearing inputs prevent the detected secret from appearing in AI prompts, logs, telemetry, URLs, or error responses.
- **SC-006**: 100% of tested Terraform recommendations display an explicit human-review warning and never state that the configuration is safe to apply.
- **SC-007**: At least 90% of evaluation users report that the finding explanation and diff make the recommended change understandable.
- **SC-008**: No tested review path executes submitted Dockerfile or Terraform content or performs deployment actions.

## Assumptions

- Users have permission to review the Dockerfile or Terraform content they submit.
- The MVP supports common Dockerfile syntax and AWS-oriented Terraform resource patterns while keeping the review concepts provider-neutral.
- The product does not need cloud credentials, repository access, or deployment permissions to perform a review.
- Static analysis can identify likely optimization opportunities but cannot claim exact image-size savings without an actual measurement.
- AI assistance is optional and may be unavailable; deterministic review remains the minimum viable result.
- Review results are treated as ephemeral for the MVP unless a later requirement explicitly adds authenticated history or retention.
- Authentication, multi-user permissions, automatic pull requests, repository integration, and deployment workflows are outside the MVP scope.
