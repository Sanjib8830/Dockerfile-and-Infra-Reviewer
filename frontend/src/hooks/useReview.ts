import { useCallback, useState } from "react";
import { submitReview } from "../services/reviewApi";
import { ReviewApiError, type ReviewRequestPayload, type ReviewResult } from "../types/review";

export type ReviewStatus = "idle" | "loading" | "success" | "error";

interface UseReviewState {
  status: ReviewStatus;
  result: ReviewResult | null;
  errorMessage: string | null;
  submit: (payload: ReviewRequestPayload) => Promise<void>;
  reset: () => void;
}

/**
 * Manages review submission, loading state, request errors, and the
 * AI-unavailable display state (which is surfaced via `result.ai_status`).
 */
function useReview(): UseReviewState {
  const [status, setStatus] = useState<ReviewStatus>("idle");
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const submit = useCallback(async (payload: ReviewRequestPayload) => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const reviewResult = await submitReview(payload);
      setResult(reviewResult);
      setStatus("success");
    } catch (error) {
      const message =
        error instanceof ReviewApiError
          ? error.message
          : "The review could not be completed. Please try again.";
      setErrorMessage(message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setErrorMessage(null);
  }, []);

  return { status, result, errorMessage, submit, reset };
}

export default useReview;
