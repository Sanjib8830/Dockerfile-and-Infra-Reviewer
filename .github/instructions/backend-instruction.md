# Backend Instructions

## Scope

These instructions apply to the Python + FastAPI backend for the Dockerfile & Infra Reviewer.

## Product Context

The backend accepts Dockerfile and Terraform source, performs deterministic analysis and policy checks, optionally uses LangChain with Google AI Studio and `gemma-4-26b-a4b-it` for explanation and remediation, validates the result, and returns findings, corrected code, and a diff.

## Ground Rules

1. Keep the review pipeline evidence-first:
   ```text
   Parse -> deterministic analysis -> policy rules -> structured findings -> AI reasoning -> validation -> diff
   ```

2. Deterministic scanners and rules are authoritative for whether a known rule is violated and for its severity. AI may explain context and recommendations, but must not override scanner severity or invent findings.

3. Never execute user-provided Dockerfiles or Terraform configurations on the application host. Do not run `docker build`, `terraform apply`, arbitrary providers, shell commands, or cloud operations as part of the MVP review path.

4. Never automatically deploy infrastructure, apply Terraform, push images, access cloud accounts, create pull requests, or modify repositories.

5. Treat all submitted source and external scanner output as untrusted input. Parse, normalize, constrain, and validate it before using it in prompts or API responses.

6. Redact secrets before AI processing and before logging. Cover credentials, tokens, API keys, passwords, private keys, connection strings, and cloud-provider secrets. Never log raw sensitive Terraform or Dockerfile content.

7. Do not claim that code was executed, an image was built, Terraform was validated, a vulnerability was confirmed, cloud resources were inspected, or an image-size reduction was measured unless the system actually performed and recorded that operation.

8. Return deterministic findings even when the AI provider is unavailable, times out, returns malformed JSON, or produces incomplete output.

9. Generated Terraform must be labeled as a recommendation and may include `SAFE_CHANGE`, `POTENTIALLY_BREAKING_CHANGE`, `DESTRUCTIVE_CHANGE`, or `REQUIRES_HUMAN_REVIEW` classifications. Never describe it as safe to apply.

10. Keep review limits explicit and enforce them server-side. The MVP target is a maximum input size of 1 MB per file and a bounded review duration.

## Architecture Rules

- Use FastAPI for the HTTP layer and Pydantic schemas for validation.
- Keep API, review services, analyzers, rules, AI integration, diff generation, and validation in separate modules.
- Implement a common reviewer abstraction for supported inputs, such as:
  ```python
  class Reviewer:
      def analyze(self, source: str) -> ReviewResult:
          ...
  ```
- Provide separate Dockerfile and Terraform reviewers while keeping the result contract consistent.
- Normalize Hadolint, Trivy, Checkov, TFLint, and custom-rule output into the internal finding schema.
- Keep provider-specific Terraform checks modular so the architecture remains extensible beyond AWS-oriented rules.

## API Contract

- Use the `/api/v1` base path.
- The MVP must implement:
  - `GET /health`
  - `POST /review`
- Validate input type and content before analysis. Supported types are `dockerfile` and `terraform`.
- Return structured findings with exactly one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO` as severity.
- Findings should include, when available: `id`, `category`, `severity`, `title`, `line_start`, `line_end`, `description`, `impact`, `recommendation`, and `source`.
- Return structured errors for empty input, unsupported file types, size violations, scanner failures, and AI failures.
- Do not expose stack traces, provider credentials, internal paths, prompts containing secrets, or raw secret-bearing input in responses.

## AI Rules

- Use LangChain as orchestration and Google AI Studio / Gemini API for the configured Gemma model.
- Use separate prompts for finding explanation, remediation, and diff explanation.
- Supply structured findings and only the minimum necessary source context to the model.
- Prompt the model to use only supplied code and scanner evidence, distinguish facts from recommendations, and avoid invented evidence.
- Validate AI output against a strict schema before returning it.
- Reject or safely degrade malformed, incomplete, unsafe, or unparseable corrected code.
- Keep static findings available independently of AI output.
- Never send unredacted secrets to the model.

## Review Coverage

At minimum, deterministic rules should cover:

- Dockerfile root execution, embedded secrets, untrusted or floating base images, unsafe package installation, dangerous permissions, privileged indicators, cache retention, oversized base-image indicators, missing multi-stage opportunities, broad copy patterns, missing `.dockerignore`, and reliability concerns.
- Terraform public exposure such as `0.0.0.0/0` on sensitive ports, public databases or buckets, unencrypted storage, broad IAM actions, wildcard resources, hardcoded credentials, missing logging, backups, monitoring, lifecycle rules, redundancy indicators, and tags.

Use qualified language for static estimates, such as "likely reduces image size because...". Do not fabricate exact byte or megabyte savings.

## Observability and Reliability

- Expose `GET /health`.
- Track request ID, review ID, file type, analysis duration, scanner duration, LLM duration, and success or failure status without recording secrets or raw sensitive source.
- Apply timeouts and bounded resource use to scanners and AI calls.
- Return useful deterministic results when optional tools fail.
- Make failures actionable but avoid leaking implementation details.

## Testing Requirements

Add or update tests for:

- Empty and oversized input.
- Unsupported file types.
- Dockerfile root-user, floating-tag, secret, and multi-stage detection.
- Terraform public security-group access, unencrypted storage, wildcard IAM, and secret detection.
- Severity precedence and finding normalization.
- Secret redaction before prompt construction.
- AI timeout, provider failure, malformed output, and schema validation.
- Corrected-code generation and unified diff generation.
- `GET /health` and `POST /review` integration behavior.
- Assurance that review code never executes submitted infrastructure.

Pin dependency versions during implementation, keep credentials in environment configuration, and never commit API keys or cloud credentials.
