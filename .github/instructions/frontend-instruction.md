# Frontend Instructions

## Scope

These instructions apply to the React + TypeScript frontend for the Dockerfile & Infra Reviewer.

## Product Context

The frontend is a developer-focused DevSecOps review interface. Users paste or upload Dockerfiles or Terraform files, submit them for analysis, and inspect evidence-backed findings, recommendations, corrected code, and diffs.

## Ground Rules

1. Preserve the primary workflow:
   - Select `Dockerfile` or `Terraform`.
   - Paste or upload source code.
   - Review the submission.
   - Inspect findings, corrected code, and the unified or side-by-side diff.

2. Never silently modify the user's original source. Suggested fixes may update a displayed working copy only after an explicit user action. Exporting or downloading corrected code must also be explicit.

3. Treat backend findings as authoritative evidence. Do not invent findings, severities, line references, scanner results, or claims about execution, image size, Terraform validation, or cloud resources.

4. Clearly distinguish these states in the UI:
   - Original source
   - Deterministic findings
   - AI explanation
   - Recommended remediation
   - Corrected source
   - Diff
   - Changes requiring human review

5. Display exactly one severity per finding: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`. Preserve deterministic scanner severity when AI explanations are displayed.

6. Show finding metadata when supplied by the API, including category, severity, title, line references, description, impact, recommendation, and source.

7. Do not state or imply that Terraform is safe to apply. Present generated Terraform as a recommendation that requires human review.

8. Surface AI degradation gracefully. If AI analysis fails, continue showing deterministic findings and clearly label AI explanations or remediation as unavailable.

9. Never expose secrets in the interface, logs, telemetry, error messages, URLs, or copied content. Respect backend redaction markers and do not attempt to reconstruct redacted values.

10. Never execute submitted Dockerfiles, Terraform configurations, shell commands, cloud operations, or builds from the browser. The frontend may display analysis results only.

## API Conventions

- Use the `/api/v1` API base path.
- The MVP must support `GET /health` and `POST /review`.
- Send review requests in the documented shape:
  ```json
  {
    "type": "dockerfile",
    "content": "..."
  }
  ```
- Handle loading, success, invalid input, unsupported file type, request failure, and AI-unavailable states explicitly.
- Treat API responses as untrusted input: validate or safely narrow data before rendering it.
- Render code and diff content as text, never as executable HTML.

## UX Requirements

- Use Monaco Editor or the established code-editor abstraction when available.
- Provide syntax highlighting, line numbers, clear-editor behavior, copy actions, file upload, and an example-loading action.
- Keep the original source available while viewing recommendations.
- Provide overview, security, optimization, reliability, corrected-version, and diff views where the result supports them.
- Support copy diff, copy corrected version, and download corrected file actions.
- Ensure controls are keyboard accessible and have visible focus states.
- Provide accessible labels, roles, and status announcements for loading and errors.
- Keep severity and finding information scannable without hiding the explanation or line reference.
- Avoid claiming measured image-size savings when the backend did not provide measurements. Use the backend's qualified language.

## TypeScript Rules

- Define shared request and response types for review data, findings, summaries, diffs, and errors.
- Prefer strict null handling and exhaustive handling of file types, severities, categories, and request states.
- Keep API calls in a service layer rather than embedding fetch logic throughout components.
- Keep presentation components focused; move parsing, formatting, and state transitions into tested utilities or hooks.
- Do not use `any` to bypass an API or rendering type mismatch.

## Testing Requirements

Add or update tests for:

- File type selection and source editing.
- Review submission and loading state.
- Summary counts and finding rendering.
- Severity display and filtering.
- Line-reference navigation where supported.
- Corrected code and diff rendering.
- Copy and download actions.
- Invalid input, unsupported file types, backend errors, and AI failure fallback.
- Accessibility of the main review workflow.

A frontend change is complete only when its relevant tests pass and the original-source safety behavior remains intact.
