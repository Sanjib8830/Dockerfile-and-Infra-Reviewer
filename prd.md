# Product Requirements Document

## Dockerfile & Infra Reviewer

**Version:** 1.0
**Status:** Proposed
**Product Type:** Developer / DevSecOps Tool
**Frontend:** React + TypeScript
**Backend:** Python + FastAPI
**AI Model:** `gemma-4-26b-a4b-it`
**AI Provider:** Google AI Studio 
**LLM Framework:** LangChain
**Primary Deployment:** Docker / Kubernetes compatible
**Target Users:** DevOps Engineers, Platform Engineers, Cloud Engineers, Developers, DevSecOps Engineers

---

# 1. Product Overview

**Dockerfile & Infra Reviewer** is a developer-focused web application that allows users to paste or upload:

1. Dockerfiles
2. Terraform files

The application analyzes the submitted configuration for:

* Security issues
* Image/build-size optimization opportunities
* Infrastructure misconfigurations
* Reliability issues
* Best-practice violations

It then generates:

* A structured review
* Severity-based findings
* Explanation of each issue
* Corrected/recommended configuration
* Unified diff between original and corrected configuration
* Explanation of why each change was made

The product should behave like a lightweight **AI-assisted DevSecOps code reviewer** rather than simply being a chatbot.

---

# 2. Problem Statement

DevOps engineers frequently review Dockerfiles and Terraform configurations manually.

Typical problems include:

* Running containers as root
* Using oversized base images
* Installing unnecessary packages
* Missing multi-stage builds
* Exposing unnecessary ports
* Using unpinned image versions
* Hardcoded credentials
* Public cloud resources exposed unintentionally
* Unencrypted storage
* Overly permissive security groups
* Missing tags
* Incorrect IAM/security configuration
* Missing resource constraints
* Terraform configuration that is valid syntactically but insecure operationally

Existing scanners can detect many problems, but their output can be difficult to understand.

The product combines:

**Static analysis + policy checks + AI reasoning + remediation generation**

to create an easier developer experience.

---

# 3. Product Vision

Create a simple web-based reviewer where a developer can paste infrastructure code and receive a review similar to:

> "Your Dockerfile builds successfully, but it has 5 security issues, 3 optimization opportunities, and 2 maintainability issues. Here is the corrected version and the exact diff."

The same workflow should work for Terraform.

---

# 4. Goals

## Primary Goals

### G1 — Dockerfile Security Review

Detect common security issues such as:

* Running as root
* Secrets embedded in Dockerfile
* Untrusted base images
* `latest` tags
* Unsafe package installation
* Excessive privileges
* Use of insecure instructions
* Exposed unnecessary ports
* Missing health checks where relevant
* Unsafe curl/wget installation patterns
* Inappropriate file permissions

### G2 — Dockerfile Size Review

Identify:

* Large base images
* Unnecessary packages
* Cache not being cleaned
* Excessive build layers
* Lack of multi-stage builds
* Large application artifacts
* Copying unnecessary files
* Missing `.dockerignore`

### G3 — Terraform Security Review

Detect common cloud/IaC issues such as:

* Publicly accessible resources
* Open security-group rules
* Unencrypted storage
* Hardcoded secrets
* Missing IAM restrictions
* Public S3-style access
* Missing logging
* Missing versioning where relevant
* Missing backups where relevant
* Missing tags
* Overly permissive CIDR ranges
* Insecure defaults

### G4 — Corrected Configuration

Generate a safer/optimized version of the submitted configuration.

The system must clearly distinguish:

**Original**

from

**Recommended**

and never silently modify the user's code.

### G5 — Explain the Diff

For every meaningful change, provide a human-readable explanation.

Example:

```diff
-FROM python:3.12
+FROM python:3.12-slim

 USER root

-RUN pip install flask
+RUN pip install --no-cache-dir flask

+USER app
```

Explanation:

> Replaced the full Python image with the slim variant to reduce unnecessary OS packages and image size. Added `--no-cache-dir` to avoid retaining pip cache and switched runtime execution to a non-root user.

---

# 5. Non-Goals for MVP

The first version should NOT:

* Automatically deploy Terraform
* Automatically execute `terraform apply`
* Automatically push Docker images
* Automatically modify GitHub repositories
* Automatically create pull requests
* Automatically build arbitrary user Dockerfiles
* Automatically connect to AWS/Azure/GCP accounts
* Automatically access cloud credentials
* Replace enterprise security scanners
* Guarantee that generated infrastructure is production-safe

The application provides **recommendations**, not automatic deployment.

---

# 6. Target Users

## Persona 1 — DevOps Engineer

Wants to quickly review a Dockerfile before committing it.

Primary need:

> "Tell me what is wrong and how to fix it."

## Persona 2 — Cloud / Platform Engineer

Wants to review Terraform before deployment.

Primary need:

> "Identify security and infrastructure risks before I run terraform apply."

## Persona 3 — Developer

May understand application code better than infrastructure.

Primary need:

> "Explain infrastructure problems in simple language."

---

# 7. Core User Journey

## Dockerfile Workflow

```text
Open Application
      ↓
Select Dockerfile
      ↓
Paste / Upload Dockerfile
      ↓
Click "Review"
      ↓
Frontend → Backend API
      ↓
Dockerfile Parser
      ↓
Security Scanner
      ↓
Size/Optimization Analyzer
      ↓
AI Analysis
      ↓
Remediation Generator
      ↓
Diff Generator
      ↓
Return Review
      ↓
Display Results
```

## Terraform Workflow

```text
Open Application
      ↓
Select Terraform
      ↓
Paste / Upload .tf
      ↓
Click "Review"
      ↓
Terraform Parser
      ↓
IaC Security Scanner
      ↓
Policy Analyzer
      ↓
AI Reasoning
      ↓
Corrected Terraform
      ↓
Diff Generator
      ↓
Display Results
```

---

# 8. Functional Requirements

## FR-01 — Input Selection

The application must support:

```text
Dockerfile
Terraform
```

The user should be able to select the type before submitting.

---

## FR-02 — Code Input

The application must support:

* Paste code
* File upload
* Clear editor
* Copy code
* Load example

The editor should provide:

* Syntax highlighting
* Line numbers
* Basic formatting

Recommended frontend editor:

**Monaco Editor**

---

## FR-03 — Dockerfile Review

The backend must identify at minimum:

### Security

* Root user
* Hardcoded credentials
* Secrets in ENV/ARG
* Unsafe base image
* Unpinned image
* Insecure package installation
* Dangerous permissions
* Privileged execution indicators
* Unnecessary package installation

### Size

* Full distribution images
* Unnecessary packages
* Build artifacts
* Cache retention
* Multi-stage opportunities
* Excessive layers
* Large COPY patterns
* Missing `.dockerignore`

### Reliability

* Missing healthcheck
* Floating image tags
* Poor signal handling
* Application launched as root
* Misconfigured entrypoint/CMD

---

# 9. Terraform Review

Terraform analysis should initially focus on common AWS-oriented patterns while keeping the architecture provider-neutral.

Supported resource families should include:

```text
aws_instance
aws_security_group
aws_security_group_rule
aws_s3_bucket
aws_db_instance
aws_iam_role
aws_iam_policy
aws_iam_role_policy
aws_ebs_volume
aws_vpc
aws_subnet
aws_route
aws_lb
```

The system should identify issues such as:

### Security

```text
0.0.0.0/0
```

on sensitive ports.

Examples:

```text
22
3389
5432
3306
```

Also detect:

* Public database
* Unencrypted storage
* Missing server-side encryption
* Broad IAM actions
* Wildcard resources
* Hardcoded credentials
* Public buckets
* Missing logging

### Reliability

* Missing deletion protection where relevant
* Missing backups
* Missing monitoring
* Missing lifecycle rules
* Missing redundancy indicators

### Maintainability

* Missing tags
* Hardcoded values
* Duplicate configuration
* Missing variables
* Excessive repetition

---

# 10. Severity Model

Each finding must have exactly one severity:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Example:

| Severity | Meaning                                   |
| -------- | ----------------------------------------- |
| CRITICAL | Immediate security or infrastructure risk |
| HIGH     | Significant security/reliability issue    |
| MEDIUM   | Important improvement recommended         |
| LOW      | Minor issue or optimization               |
| INFO     | Informational / best-practice suggestion  |

Severity generated by deterministic scanners must take precedence over AI-generated severity.

The AI may explain the severity but should not arbitrarily override the scanner's severity.

---

# 11. Finding Structure

Every finding returned by the backend should follow a consistent structure.

Example:

```json
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
  "source": "static-analysis"
}
```

Possible categories:

```text
security
size
performance
reliability
maintainability
best-practice
```

---

# 12. AI Responsibilities

AI should NOT be responsible for discovering everything.

The application should follow:

```text
Static Analysis
      +
Policy Rules
      +
AI Reasoning
```

## AI should be used for:

### A. Explain findings

Convert technical scanner output into understandable explanations.

### B. Assess contextual impact

For example:

A broad security-group rule might be more concerning on a production database than a temporary development environment.

The AI may explain context, but deterministic findings remain authoritative.

### C. Generate remediation

Generate a corrected configuration based on:

* Original code
* Findings
* Tool output
* Security rules
* User-selected preferences

### D. Explain the diff

The model should explain:

* What changed
* Why it changed
* What risk it addresses
* Possible trade-offs

### E. Summarize the review

Example:

```text
Security: 3 issues
Optimization: 4 issues
Maintainability: 2 issues

Most important issue:
The container runs as root.

Estimated image optimization opportunities:
Multi-stage build + slim base image + package cleanup.
```

---

# 13. AI Model Configuration

Use:

```text
Model:
gemma-4-26b-a4b-it

Provider:
Google AI Studio / Gemini API

Framework:
LangChain
```

Google currently documents `gemma-4-26b-a4b-it` as a supported Gemma 4 model through the Gemini API, with API access obtained from Google AI Studio.

Gemma 4 26B A4B is a Mixture-of-Experts model with approximately 25.2B total parameters and approximately 3.8B active parameters; Google documents support for coding, reasoning, function calling, and a 256K-token context window.

The initial implementation should still limit prompts to the minimum required context rather than sending unnecessarily large inputs.

---

# 14. AI Architecture

Use LangChain as the orchestration layer.

Recommended flow:

```text
User Input
   ↓
Analyzer
   ↓
Structured Findings
   ↓
Prompt Builder
   ↓
LangChain
   ↓
Gemma 4
   ↓
Structured AI Response
   ↓
Validation
   ↓
Diff Engine
   ↓
API Response
```

The AI should receive structured findings rather than relying solely on raw code interpretation.

Example:

```json
{
  "file_type": "dockerfile",
  "code": "...",
  "findings": [
    {
      "rule": "DF-SEC-001",
      "severity": "HIGH",
      "line": 12,
      "message": "Container runs as root"
    }
  ]
}
```

---

# 15. AI Output Contract

AI responses must be structured.

Preferred format:

```json
{
  "summary": "The Dockerfile has 4 security and optimization issues.",
  "explanations": [
    {
      "finding_id": "DF-SEC-001",
      "explanation": "...",
      "recommended_fix": "..."
    }
  ],
  "corrected_code": "...",
  "change_summary": [
    {
      "change": "Added non-root user",
      "reason": "Reduces container privilege"
    }
  ]
}
```

The backend must validate AI output before returning it to the frontend.

Malformed JSON or incomplete AI output must not break the review.

---

# 16. Prompt Design

Use separate prompts instead of one giant prompt.

## Prompt 1 — Explanation

Input:

```text
code
finding
severity
scanner_reason
```

Output:

```text
explanation
impact
recommendation
```

## Prompt 2 — Remediation

Input:

```text
original_code
findings
constraints
```

Output:

```text
corrected_code
```

## Prompt 3 — Diff Explanation

Input:

```text
original_code
corrected_code
unified_diff
```

Output:

```text
changes
reason
impact
tradeoffs
```

This separation makes the system easier to test and reduces hallucinated findings.

---

# 17. Deterministic Tools

The project should integrate established tools wherever practical.

## Dockerfile

Potential analyzers:

```text
Hadolint
Trivy
Docker Scout-compatible checks where appropriate
Custom Python rules
```

## Terraform

Potential analyzers:

```text
terraform fmt
terraform validate
TFLint
Checkov
Custom policy rules
```

Important:

The application should treat external scanner output as untrusted input and normalize it into the internal finding schema.

---

# 18. Review Engine

Create a common abstraction:

```python
class Reviewer:
    def analyze(self, source: str) -> ReviewResult:
        ...
```

Implement:

```text
DockerfileReviewer
TerraformReviewer
```

Potential structure:

```text
ReviewResult
 ├── file_type
 ├── summary
 ├── findings[]
 ├── metrics
 ├── corrected_code
 └── diff
```

---

# 19. Size Review

For Dockerfiles, provide measurable information wherever possible.

Example:

```text
Base Image:
python:3.12

Optimization:
Could use python:3.12-slim

Package cache:
Detected

Multi-stage:
Not used

.dockerignore:
Not supplied
```

The MVP should avoid making fake claims such as:

> "This will reduce your image by exactly 237 MB."

Unless the application actually builds/scans the image and has measured the difference.

Use language such as:

> "Likely reduces image size because..."

when only static analysis is available.

---

# 20. Terraform Review Safety

Terraform remediation must be handled carefully.

The application should distinguish:

```text
SAFE_CHANGE
POTENTIALLY_BREAKING_CHANGE
DESTRUCTIVE_CHANGE
REQUIRES_HUMAN_REVIEW
```

Examples:

### Safe-ish

Adding:

```hcl
tags = {
  Environment = var.environment
}
```

### Potentially breaking

Changing:

```hcl
instance_type = "m5.large"
```

### Potentially destructive

Changing resource identity or replacement-triggering attributes.

The product must never claim:

> "This Terraform is safe to apply."

Instead:

> "This configuration has been modified according to the detected findings. Review the generated diff before applying."

---

# 21. Frontend Requirements

## Main Screen

Header:

```text
Dockerfile & Infra Reviewer
AI-assisted DevSecOps review
```

Main controls:

```text
[ Dockerfile ▼ ]

[ Paste / Upload ]

[ Review ]
```

Editor:

```text
┌───────────────────────────────────────────────┐
│ 1 FROM python:3.12                            │
│ 2 COPY . /app                                 │
│ 3 RUN pip install flask                       │
│ 4 CMD ["python", "app.py"]                    │
└───────────────────────────────────────────────┘
```

---

# 22. Review Results UI

After analysis:

```text
┌────────────────────────────────────────────┐
│ Review Summary                             │
│                                            │
│ Critical   0                               │
│ High       2                               │
│ Medium     3                               │
│ Low        2                               │
└────────────────────────────────────────────┘
```

Tabs:

```text
Overview
Security
Optimization
Reliability
Corrected Version
Diff
```

---

# 23. Finding UI

Example:

```text
HIGH

Container runs as root

Line 12

Why this matters
Running applications as root increases the impact
of container compromise.

Recommended fix
Create a dedicated runtime user.

[Show Code]
[Apply Suggested Fix]
```

The "Apply Suggested Fix" button should modify the displayed editor only.

It must not modify the original uploaded file unless the user explicitly exports/downloads it.

---

# 24. Diff Viewer

Use side-by-side diff:

```text
ORIGINAL                     RECOMMENDED

FROM python:3.12             FROM python:3.12-slim

COPY . /app                  COPY requirements.txt .

RUN pip install flask        RUN pip install --no-cache-dir -r requirements.txt

                             RUN useradd -r appuser
                             USER appuser

COPY . /app
```

Provide:

```text
Copy Diff
Copy Corrected Version
Download Corrected File
```

---

# 25. Backend API

Base path:

```text
/api/v1
```

## POST /review

Request:

```json
{
  "type": "dockerfile",
  "content": "FROM python:3.12\n..."
}
```

Response:

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
  "findings": [],
  "corrected_code": "...",
  "diff": "...",
  "ai_summary": "..."
}
```

---

# 26. Additional API Endpoints

```text
GET /health

POST /review

POST /review/{review_id}/explain

POST /review/{review_id}/remediate

GET /review/{review_id}

GET /rules

GET /examples
```

MVP can initially implement:

```text
GET /health
POST /review
```

and expand later.

---

# 27. Backend Architecture

Recommended:

```text
FastAPI
│
├── API
│
├── Review Service
│
├── Dockerfile Analyzer
│
├── Terraform Analyzer
│
├── Security Rules
│
├── Optimization Rules
│
├── AI Service
│   └── LangChain
│       └── Google AI Studio
│           └── Gemma
│
├── Diff Service
│
└── Validation
```

Suggested Python packages:

```text
fastapi
uvicorn
pydantic
langchain
langchain-google-genai
google-genai
python-multipart
```

Exact package/API versions should be pinned during implementation.

---

# 28. Frontend Architecture

Recommended:

```text
React
TypeScript
Vite
```

Suggested components:

```text
App
├── Header
├── FileTypeSelector
├── CodeEditor
├── ReviewButton
├── ReviewSummary
├── FindingsList
├── FindingCard
├── CorrectedCodeViewer
├── DiffViewer
└── Loading/ErrorState
```

State:

```text
selectedFileType
sourceCode
reviewStatus
reviewResult
selectedFinding
```

---

# 29. Project Repository Structure

Recommended repository:

```text
dockerfile-infra-reviewer/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── analyzers/
│   │   ├── rules/
│   │   ├── ai/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── rules/
│   ├── dockerfile/
│   └── terraform/
│
├── examples/
│   ├── dockerfile/
│   └── terraform/
│
├── .github/
│   ├── workflows/
│   ├── copilot-instructions.md
│   └── instructions/
│
├── docker-compose.yml
├── README.md
└── PRD.md
```

---

# 30. GitHub Copilot Development Strategy

The repository should contain:

```text
.github/copilot-instructions.md
```

GitHub supports repository-wide Copilot instructions through this file, as well as path-specific instructions and agent instructions such as `AGENTS.md`.

Use the repository instructions to tell Copilot:

```text
Project architecture
Coding standards
Testing requirements
Security requirements
API conventions
React conventions
Python conventions
AI integration rules
Do not expose secrets
Do not execute untrusted infrastructure code
Do not invent scanner findings
```

Recommended path-specific instructions:

```text
.github/instructions/frontend.instructions.md
.github/instructions/backend.instructions.md
.github/instructions/ai.instructions.md
.github/instructions/tests.instructions.md
```

---

# 31. Important Copilot Rule

Add this principle to the repository instructions:

```text
AI-generated remediation must never bypass deterministic security findings.

Static scanners are authoritative for whether a known rule is violated.

LLM output is advisory and must be validated before being returned to the user.

Never execute user-provided Dockerfiles or Terraform configurations directly on the host.

Never expose API keys, cloud credentials, environment secrets, or internal infrastructure details.

Never automatically apply Terraform changes.
```

---

# 32. Security Architecture

This application processes potentially malicious configuration.

Therefore:

### Never:

```text
docker build <user input>
terraform apply <user input>
terraform init with arbitrary providers
```

directly on the application host.

For MVP:

```text
Parse
↓
Static Analysis
↓
Rules
↓
AI
```

No execution.

If future versions need actual builds or Terraform plans, execute them inside isolated ephemeral environments with:

* Network restrictions
* CPU limits
* Memory limits
* Execution timeout
* Read-only filesystem where possible
* Non-root user
* No host Docker socket
* No cloud credentials
* Disposable containers

---

# 33. Secret Protection

Never send environment secrets to the LLM.

Before AI processing, redact:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
GCP credentials
Azure credentials
API keys
passwords
tokens
private keys
connection strings
```

Example:

```text
password = "supersecret"
```

becomes:

```text
password = "[REDACTED]"
```

The UI should show:

```text
Secret detected and redacted before AI processing.
```

---

# 34. AI Guardrails

The model must not:

* Invent scanner results
* Claim that code was executed when it was not
* Claim an image-size reduction that was not measured
* Claim Terraform was validated when it was not
* Claim cloud resources were inspected
* Claim a vulnerability was confirmed without evidence
* Automatically approve infrastructure

The prompt should explicitly state:

```text
Use only the supplied code and scanner findings.
Do not invent evidence.
Clearly distinguish detected facts from recommendations.
```

---

# 35. Error Handling

Examples:

### Invalid input

```json
{
  "error": "INVALID_INPUT",
  "message": "The uploaded file is empty."
}
```

### Unsupported file

```json
{
  "error": "UNSUPPORTED_FILE_TYPE",
  "message": "Only Dockerfile and Terraform input are currently supported."
}
```

### AI failure

The application must still return deterministic scanner findings.

Example:

```text
AI explanation temporarily unavailable.

Static analysis results are still available.
```

This is important because the product should not become unusable when the LLM provider is unavailable.

---

# 36. Performance Requirements

Target MVP:

```text
Static analysis:
< 2 seconds

AI-assisted review:
< 15 seconds target

Frontend initial load:
< 3 seconds on normal broadband

Maximum input size:
1 MB per file
```

These are product targets, not guaranteed SLAs.

---

# 37. Observability

Backend should expose:

```text
/health
```

Log:

```text
request_id
review_id
file_type
analysis_duration
scanner_duration
llm_duration
success/failure
```

Do NOT log:

```text
API keys
passwords
tokens
raw Terraform containing secrets
raw credentials
```

Metrics to add later:

```text
review_count
review_failure_count
average_review_duration
ai_failure_count
findings_by_severity
```

---

# 38. Testing Strategy

## Backend

Unit tests:

```text
test_dockerfile_root_user()
test_dockerfile_latest_tag()
test_dockerfile_secret_detection()
test_multistage_detection()

test_terraform_public_sg()
test_terraform_unencrypted_storage()
test_terraform_wildcard_iam()
```

Integration tests:

```text
POST /review
```

with known sample inputs.

## Frontend

Test:

```text
file selection
editor input
review submission
loading state
finding rendering
diff rendering
error handling
```

## AI

Use fixed evaluation cases:

```text
Input
Expected finding explanations
Expected remediation properties
Expected structured response
```

Do not rely entirely on exact wording comparisons.

---

# 39. Acceptance Criteria — MVP

The MVP is complete when all of the following are true.

### Dockerfile

A user can paste a Dockerfile and receive:

```text
Security findings
Size/optimization findings
Severity
Line references
Explanation
Recommended remediation
Corrected Dockerfile
Unified diff
```

### Terraform

A user can paste Terraform and receive:

```text
Security findings
Reliability findings
Maintainability findings
Severity
Line references
Explanation
Recommended remediation
Corrected Terraform
Unified diff
```

### AI

The application:

```text
Uses Gemma
Uses LangChain
Uses Google AI Studio/Gemini API
Returns structured output
Handles AI failures gracefully
Does not expose API secrets
```

### Security

The application:

```text
Does not execute submitted Dockerfiles
Does not execute terraform apply
Does not expose credentials
Redacts secrets before AI processing
```

---

# 40. MVP Release Scope

## Phase 1 — Foundation

Build:

```text
React frontend
FastAPI backend
Dockerfile input
Terraform input
Basic API
Monaco editor
```

## Phase 2 — Deterministic Analysis

Implement:

```text
Dockerfile rules
Terraform rules
Severity engine
Finding schema
Diff engine
```

## Phase 3 — AI

Implement:

```text
LangChain
Google AI Studio
Gemma 4
Explanation generation
Remediation generation
Diff explanation
```

## Phase 4 — UX

Implement:

```text
Dashboard
Finding cards
Severity filters
Diff viewer
Copy/download
Error handling
```

## Phase 5 — DevSecOps

Implement:

```text
Hadolint
Trivy
Checkov
TFLint
CI/CD
Unit tests
Integration tests
```

---

# 41. Future Features

Possible V2 capabilities:

```text
GitHub repository integration
GitHub Pull Request review
Automatic PR comments
GitHub Actions integration
Terraform plan analysis
Docker image analysis
SBOM analysis
CVE analysis
Kubernetes YAML review
Helm review
Ansible review
Kubernetes security review
Policy-as-code
Custom organization rules
Authentication
Review history
```

A natural future workflow would be:

```text
GitHub PR
   ↓
CI
   ↓
Dockerfile / Terraform detection
   ↓
Static scanners
   ↓
AI analysis
   ↓
PR comment
   ↓
Developer fixes
```

---

# 42. Example Dockerfile Review

Input:

```dockerfile
FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install flask requests

EXPOSE 5000

CMD ["python", "app.py"]
```

Potential deterministic findings:

```text
MEDIUM
Full Python base image may contain unnecessary packages.

MEDIUM
Dependencies are installed without disabling pip cache.

MEDIUM
No non-root USER configured.

LOW
COPY . . may include unnecessary build/context files.

INFO
Multi-stage build may not be necessary for this particular application.
```

AI then explains the findings and generates a remediation.

---

# 43. Example Terraform Review

Input:

```hcl
resource "aws_security_group" "app" {
  name = "app"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Static analysis:

```text
HIGH
SSH access is exposed to the public internet.
```

AI explanation:

```text
The security group allows SSH connections from any IPv4
address. Restrict access to a trusted CIDR range or use
a private administrative access mechanism.
```

Recommended Terraform:

```hcl
resource "aws_security_group" "app" {
  name = "app"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr
  }
}
```

---

# 44. Product Principles

The application should follow five principles:

### 1. Evidence before AI

Scanner findings are the source of truth for deterministic rules.

### 2. AI explains; AI does not fabricate

The model should reason over evidence rather than invent problems.

### 3. Recommendations are transparent

Always show:

```text
Original
↓
Finding
↓
Recommendation
↓
Corrected
↓
Diff
```

### 4. Human approval is required

Especially for Terraform changes.

### 5. Secure by default

Never execute arbitrary infrastructure code simply to produce a review.

---

# 45. Definition of Done

A feature is considered complete when:

```text
Code implemented
↓
Unit tests added
↓
Integration test added
↓
Error handling implemented
↓
Security reviewed
↓
README updated
↓
Copilot instructions updated where required
↓
CI passes
```

No feature should be considered complete merely because the application works manually.

---

# 46. Suggested Initial GitHub Issues

Create these issues in sequence:

```text
#1 Initialize monorepo

#2 Create React application

#3 Create FastAPI backend

#4 Implement review API

#5 Implement Dockerfile rule engine

#6 Implement Terraform rule engine

#7 Implement finding/severity schema

#8 Implement diff generator

#9 Add Monaco editor

#10 Add results UI

#11 Integrate LangChain

#12 Integrate Google AI Studio / Gemma

#13 Implement AI structured output validation

#14 Implement secret redaction

#15 Add Hadolint integration

#16 Add Checkov integration

#17 Add TFLint integration

#18 Add Trivy integration

#19 Add backend tests

#20 Add frontend tests

#21 Add GitHub Actions CI

#22 Add Docker deployment

#23 Security hardening

#24 Documentation
```

---

# 47. Recommended Technical Architecture

```text
                    ┌─────────────────────┐
                    │      React UI       │
                    │  TypeScript/Vite    │
                    └──────────┬──────────┘
                               │
                               │ REST
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │     API Layer       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Review Engine    │
                    └──────┬─────┬────────┘
                           │     │
               ┌───────────┘     └────────────┐
               ▼                              ▼
       ┌────────────────┐            ┌────────────────┐
       │ Static Analyzers│            │   AI Service   │
       │                │            │                │
       │ Hadolint       │            │ LangChain      │
       │ Checkov        │            │      ↓         │
       │ TFLint         │            │ Google AI      │
       │ Trivy          │            │      ↓         │
       │ Custom Rules   │            │ Gemma 4 26B    │
       └───────┬────────┘            └───────┬────────┘
               │                             │
               └─────────────┬───────────────┘
                             ▼
                    ┌─────────────────────┐
                    │ Result Normalizer   │
                    │ + Validation        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Diff Engine      │
                    └──────────┬──────────┘
                               │
                               ▼
                         React Results
```

---

# 48. MVP Success Metrics

Track:

```text
Review completion rate
Average review duration
AI failure rate
Scanner failure rate
Number of findings per review
Number of corrected configurations generated
User copy/download actions
False-positive reports
```

The most important quality metric should be:

**Useful, evidence-backed findings**, not the raw number of findings.

---

# 49. Final Product Definition

The final MVP should feel like:

```text
"SonarQube + Checkov/Hadolint + AI remediation"
```

but intentionally narrower and simpler.

The core experience is:

```text
Paste Dockerfile/Terraform
          ↓
     Analyze
          ↓
 See security + size + reliability issues
          ↓
 Understand why
          ↓
 Get corrected configuration
          ↓
 See exact diff
          ↓
 Decide whether to apply the changes
```

The AI is an **assistant around the analysis engine**, not the security engine itself.
