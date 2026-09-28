# Dockerfile & Infra Reviewer

An AI-assisted DevSecOps tool that reviews Dockerfiles and Terraform configuration for
security, size/optimization, reliability, and maintainability issues. See [prd.md](prd.md)
for the full product requirements and [specs/001-dockerfile-infra-review](specs/001-dockerfile-infra-review)
for the feature specification, plan, data model, API contract, and task breakdown.

## Repository Structure

```text
backend/    FastAPI application, deterministic rule engine, optional AI assistant, tests
frontend/   React + TypeScript + Vite application, Monaco-based editor, tests
specs/      Spec Kit feature specification, plan, research, data model, contracts, tasks
.specify/   Spec Kit governance (constitution) and templates
.github/    Copilot instructions and skills
```

## Backend Setup

Requirements: Python 3.11+.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the backend test suite:

```bash
cd backend
python -m pytest -q
```

The backend exposes:

- `GET /api/v1/health` — liveness check, independent of the AI provider.
- `POST /api/v1/review` — submit a `dockerfile` or `terraform` review request.

### Optional AI configuration

AI-assisted explanation and remediation (LangChain + Google AI Studio, model
`gemma-4-26b-a4b-it`) is optional. Without a key, the API returns deterministic
findings only, with `ai_status: "not_requested"`.

```bash
export GOOGLE_API_KEY="<your-google-ai-studio-key>"
```

Never commit this key. If the AI provider fails, times out, or returns invalid output,
the API returns `ai_status: "unavailable"` and still includes deterministic findings.

## Frontend Setup

Requirements: Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

Run the frontend test suite:

```bash
cd frontend
npm test
```

Type-check the project:

```bash
cd frontend
npx tsc -b
```

By default the frontend calls `/api/v1`. Set `VITE_API_BASE_URL` to point at a
different backend origin during local development if needed.

## Validating the Feature

Follow [specs/001-dockerfile-infra-review/quickstart.md](specs/001-dockerfile-infra-review/quickstart.md)
for end-to-end validation scenarios. These scenarios are also covered by automated tests:

- `backend/tests/integration/test_quickstart_scenarios.py` — Dockerfile review, Terraform
  review, AI-unavailable fallback, and input validation.
- `frontend/tests/ReviewExperience.test.tsx` — finding navigation, diff viewing, and export.

## Security Boundary

This application **never executes** submitted Dockerfile or Terraform content. It does not
run `docker build`, `terraform apply`, `terraform init` with arbitrary providers, or any
other command against user-submitted configuration. Analysis is limited to static parsing
and pattern-based rules (see `backend/app/rules/` and `backend/app/analyzers/`).

Secrets detected in submitted content are redacted (`backend/app/utils/redaction.py`)
before any optional AI processing and are never logged or included in API responses.
Terraform corrections always carry a risk classification and the product never states
that generated infrastructure is safe to apply — see
[specs/001-dockerfile-infra-review/data-model.md](specs/001-dockerfile-infra-review/data-model.md).

## Known Limitations

- The MVP does not integrate external scanners (Hadolint, Trivy, TFLint, Checkov) by
  default; `backend/app/analyzers/external_scanners.py` provides normalization adapters
  for their output but does not invoke the external binaries.
- Review results are not persisted; there is no review history or authentication in this
  feature (see the specification's Assumptions section).
- Size/optimization findings use qualified language ("likely reduces...") rather than
  exact measured savings, since no image build or scan is performed.
- The frontend's Monaco-based editor is mocked in tests to avoid loading web workers in
  the test environment; manual verification in a browser is recommended before release.
- `npm install` reported dependency vulnerabilities from `npm audit` in third-party
  packages; run `npm audit` and review/upgrade before production deployment.
