/**
 * Typed /api/v1 client with normalized API-error parsing.
 */

import type { ApiErrorBody, ReviewRequestPayload, ReviewResult } from "../types/review";
import { ReviewApiError } from "../types/review";

const API_BASE_URL = (import.meta as { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL ?? "/api/v1";

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

export async function submitReview(payload: ReviewRequestPayload): Promise<ReviewResult> {
  const response = await fetch(`${API_BASE_URL}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const errorBody = normalizeErrorBody(body);
    throw new ReviewApiError(errorBody);
  }

  return body as ReviewResult;
}

function normalizeErrorBody(body: unknown): ApiErrorBody {
  if (body && typeof body === "object") {
    const candidate = (body as { detail?: unknown }).detail ?? body;
    if (
      candidate &&
      typeof candidate === "object" &&
      "error" in candidate &&
      "message" in candidate
    ) {
      const typed = candidate as { error: unknown; message: unknown };
      return {
        error: String(typed.error),
        message: String(typed.message),
      };
    }
  }
  return { error: "REVIEW_FAILED", message: "The review could not be completed. Please try again." };
}
