import type { RemediationChange } from "../types/review";
import { copyToClipboard, downloadTextFile } from "../utils/exportReview";

interface DiffViewerProps {
  originalContent: string;
  correctedContent?: string | null;
  diff?: string | null;
  changeSummary?: RemediationChange[] | null;
  downloadFilename?: string;
}

/**
 * Corrected-code display, unified diff, and per-change explanation view (US3).
 * Never mutates `originalContent`; export actions require an explicit click.
 */
function DiffViewer({
  originalContent,
  correctedContent,
  diff,
  changeSummary,
  downloadFilename = "corrected-review.txt",
}: DiffViewerProps) {
  if (!correctedContent || !diff) {
    return <p>No corrected version was generated for this review.</p>;
  }

  return (
    <div>
      <div className="diff-side-by-side">
        <section aria-label="Original content">
          <h3>Original</h3>
          <pre>{originalContent}</pre>
        </section>
        <section aria-label="Recommended content">
          <h3>Recommended</h3>
          <pre>{correctedContent}</pre>
        </section>
      </div>

      <pre aria-label="Unified diff">{diff}</pre>

      {changeSummary && changeSummary.length > 0 && (
        <ul aria-label="Change explanations">
          {changeSummary.map((change, index) => (
            <li key={`${change.change}-${index}`}>
              <p>
                <strong>{change.change}</strong>: {change.reason}
              </p>
              {change.risk_classification && (
                <p className="risk-warning" role="alert">
                  {change.risk_classification.replace(/_/g, " ")}. Review the generated diff before applying.
                </p>
              )}
              {change.tradeoffs && <p>Trade-offs: {change.tradeoffs}</p>}
            </li>
          ))}
        </ul>
      )}

      <div className="diff-actions">
        <button type="button" onClick={() => copyToClipboard(diff)}>
          Copy Diff
        </button>
        <button type="button" onClick={() => copyToClipboard(correctedContent)}>
          Copy Corrected Version
        </button>
        <button type="button" onClick={() => downloadTextFile(downloadFilename, correctedContent)}>
          Download Corrected File
        </button>
      </div>
    </div>
  );
}

export default DiffViewer;
