import { useMemo, useState } from "react";
import type { Category, Finding, Severity } from "../types/review";

interface FindingsListProps {
  findings: Finding[];
  selectedFindingId?: string | null;
  onSelectFinding: (finding: Finding) => void;
}

const ALL_SEVERITIES: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];

/**
 * Severity/category filters and source-line selection behavior (US3).
 */
function FindingsList({ findings, selectedFindingId, onSelectFinding }: FindingsListProps) {
  const [severityFilter, setSeverityFilter] = useState<Severity | "ALL">("ALL");
  const [categoryFilter, setCategoryFilter] = useState<Category | "ALL">("ALL");

  const categories = useMemo(
    () => Array.from(new Set(findings.map((finding) => finding.category))),
    [findings],
  );

  const filtered = findings.filter((finding) => {
    const matchesSeverity = severityFilter === "ALL" || finding.severity === severityFilter;
    const matchesCategory = categoryFilter === "ALL" || finding.category === categoryFilter;
    return matchesSeverity && matchesCategory;
  });

  return (
    <div>
      <div className="findings-filters">
        <label htmlFor="severity-filter">Severity</label>
        <select
          id="severity-filter"
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value as Severity | "ALL")}
        >
          <option value="ALL">All severities</option>
          {ALL_SEVERITIES.map((severity) => (
            <option key={severity} value={severity}>
              {severity}
            </option>
          ))}
        </select>

        <label htmlFor="category-filter">Category</label>
        <select
          id="category-filter"
          value={categoryFilter}
          onChange={(event) => setCategoryFilter(event.target.value as Category | "ALL")}
        >
          <option value="ALL">All categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <p>No supported issues were detected for the selected filters.</p>
      ) : (
        <ul className="findings-list">
          {filtered.map((finding) => (
            <li key={finding.id}>
              <button
                type="button"
                aria-pressed={finding.id === selectedFindingId}
                onClick={() => onSelectFinding(finding)}
              >
                <span className={`severity-badge severity-${finding.severity}`}>{finding.severity}</span>
                <span>{finding.title}</span>
                {typeof finding.line_start === "number" && <span> (line {finding.line_start})</span>}
              </button>
              <p>{finding.explanation ?? finding.description}</p>
              <p>
                <strong>Recommended fix:</strong> {finding.recommendation}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FindingsList;
