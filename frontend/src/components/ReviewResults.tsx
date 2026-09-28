import { useState } from "react";
import type { ReviewResult, Finding } from "../types/review";
import FindingsList from "./FindingsList";
import DiffViewer from "./DiffViewer";

interface ReviewResultsProps {
  result: ReviewResult;
  selectedFindingId?: string | null;
  onSelectFinding: (finding: Finding) => void;
}

type TabId = "overview" | "security" | "optimization" | "reliability" | "corrected" | "diff";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "security", label: "Security" },
  { id: "optimization", label: "Optimization" },
  { id: "reliability", label: "Reliability" },
  { id: "corrected", label: "Corrected Version" },
  { id: "diff", label: "Diff" },
];

/**
 * Review-results surface: summary, severity-tabbed findings, corrected version,
 * and diff (US1/US2/US3). Never claims Terraform configuration is safe to apply.
 */
function ReviewResults({ result, selectedFindingId, onSelectFinding }: ReviewResultsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const findingsByCategory = (category: string) =>
    result.findings.filter((finding) => finding.category === category);

  return (
    <div>
      <section aria-label="Review summary">
        <h2>Review Summary</h2>
        <ul>
          <li>Critical: {result.summary.critical}</li>
          <li>High: {result.summary.high}</li>
          <li>Medium: {result.summary.medium}</li>
          <li>Low: {result.summary.low}</li>
          <li>Info: {result.summary.info}</li>
        </ul>
        {result.findings.length === 0 && <p>No supported issues were detected for this submission.</p>}
        {result.ai_status === "unavailable" && (
          <p role="status" className="status-message">
            AI explanation temporarily unavailable. Static analysis results are still available.
          </p>
        )}
        {result.ai_summary && <p>{result.ai_summary}</p>}
        {result.type === "terraform" && result.corrected_content && (
          <p className="risk-warning" role="alert">
            This configuration has been modified according to the detected findings. Review the generated diff
            before applying. This Terraform is not guaranteed to be safe to apply.
          </p>
        )}
      </section>

      <div role="tablist" aria-label="Review result sections" className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === "overview" && (
          <FindingsList
            findings={result.findings}
            selectedFindingId={selectedFindingId}
            onSelectFinding={onSelectFinding}
          />
        )}
        {activeTab === "security" && (
          <FindingsList
            findings={findingsByCategory("security")}
            selectedFindingId={selectedFindingId}
            onSelectFinding={onSelectFinding}
          />
        )}
        {activeTab === "optimization" && (
          <FindingsList
            findings={[...findingsByCategory("size"), ...findingsByCategory("performance")]}
            selectedFindingId={selectedFindingId}
            onSelectFinding={onSelectFinding}
          />
        )}
        {activeTab === "reliability" && (
          <FindingsList
            findings={findingsByCategory("reliability")}
            selectedFindingId={selectedFindingId}
            onSelectFinding={onSelectFinding}
          />
        )}
        {activeTab === "corrected" && (
          <pre aria-label="Corrected content">
            {result.corrected_content ?? "No corrected version was generated for this review."}
          </pre>
        )}
        {activeTab === "diff" && (
          <DiffViewer
            originalContent={result.original_content}
            correctedContent={result.corrected_content}
            diff={result.diff}
            changeSummary={result.change_summary}
            downloadFilename={result.type === "dockerfile" ? "Dockerfile.corrected" : "main.tf.corrected"}
          />
        )}
      </div>
    </div>
  );
}

export default ReviewResults;
