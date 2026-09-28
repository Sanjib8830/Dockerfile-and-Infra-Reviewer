/**
 * Shared frontend review, finding, remediation, severity, and error types.
 * Mirrors specs/001-dockerfile-infra-review/contracts/review-api.md and data-model.md.
 */

export type ReviewType = "dockerfile" | "terraform";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export type Category =
  | "security"
  | "size"
  | "performance"
  | "reliability"
  | "maintainability"
  | "best-practice";

export type FindingSourceKind = "static-analysis" | "external-scanner";

export type AiStatus = "available" | "unavailable" | "not_requested";

export type ChangeRisk =
  | "SAFE_CHANGE"
  | "POTENTIALLY_BREAKING_CHANGE"
  | "DESTRUCTIVE_CHANGE"
  | "REQUIRES_HUMAN_REVIEW";

export interface ReviewRequestPayload {
  type: ReviewType;
  content: string;
  filename?: string;
}

export interface Finding {
  id: string;
  category: Category;
  severity: Severity;
  title: string;
  line_start?: number | null;
  line_end?: number | null;
  description: string;
  impact: string;
  recommendation: string;
  source: FindingSourceKind;
  explanation?: string | null;
}

export interface RemediationChange {
  change: string;
  reason: string;
  related_finding_id?: string | null;
  risk_classification?: ChangeRisk | null;
  tradeoffs?: string | null;
}

export interface Summary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface ReviewResult {
  review_id: string;
  type: ReviewType;
  summary: Summary;
  findings: Finding[];
  metrics?: Record<string, string> | null;
  corrected_content?: string | null;
  original_content: string;
  diff?: string | null;
  change_summary?: RemediationChange[] | null;
  ai_summary?: string | null;
  ai_status: AiStatus;
}

export interface ApiErrorBody {
  error: "INVALID_INPUT" | "UNSUPPORTED_FILE_TYPE" | "REVIEW_FAILED" | string;
  message: string;
}

export class ReviewApiError extends Error {
  readonly code: string;

  constructor(body: ApiErrorBody) {
    super(body.message);
    this.code = body.error;
  }
}
