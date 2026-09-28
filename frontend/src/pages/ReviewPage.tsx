import { useState } from "react";
import ReviewInput from "../components/ReviewInput";
import CodeEditor from "../components/CodeEditor";
import ReviewResults from "../components/ReviewResults";
import useReview from "../hooks/useReview";
import type { Finding, ReviewType } from "../types/review";

/**
 * Composes the full review workflow: type selection, source input, submission,
 * loading/error states, and results (US1, US2, US3).
 */
function ReviewPage() {
  const [type, setType] = useState<ReviewType>("dockerfile");
  const [content, setContent] = useState("");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const { status, result, errorMessage, submit, reset } = useReview();

  const handleClear = () => {
    setContent("");
    setSelectedFinding(null);
    reset();
  };

  const handleTypeChange = (nextType: ReviewType) => {
    setType(nextType);
    setSelectedFinding(null);
    reset();
  };

  const handleSubmit = async () => {
    await submit({ type, content });
  };

  return (
    <div className="review-layout">
      <section aria-label="Review input">
        <ReviewInput
          type={type}
          onTypeChange={handleTypeChange}
          onContentChange={setContent}
          onClear={handleClear}
        />
        <CodeEditor type={type} value={content} onChange={setContent} />
        <button type="button" onClick={handleSubmit} disabled={status === "loading" || content.trim() === ""}>
          {status === "loading" ? "Reviewing..." : "Review"}
        </button>
        {status === "loading" && (
          <p role="status" className="status-message">
            Analyzing your submission…
          </p>
        )}
        {status === "error" && errorMessage && (
          <p role="alert" className="status-message">
            {errorMessage}
          </p>
        )}
      </section>

      <section aria-label="Review results">
        {result && (
          <ReviewResults result={result} selectedFindingId={selectedFinding?.id} onSelectFinding={setSelectedFinding} />
        )}
      </section>
    </div>
  );
}

export default ReviewPage;
