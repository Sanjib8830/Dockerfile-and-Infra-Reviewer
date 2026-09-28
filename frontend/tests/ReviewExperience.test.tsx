import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ReviewPage from "../src/pages/ReviewPage";
import type { ReviewResult } from "../src/types/review";
import * as exportReview from "../src/utils/exportReview";

vi.mock("@monaco-editor/react", () => ({
  default: ({ value, onChange }: { value: string; onChange: (value: string) => void }) => (
    <textarea aria-label="mock-editor" value={value} onChange={(event) => onChange(event.target.value)} />
  ),
}));

vi.mock("../src/utils/exportReview", () => ({
  copyToClipboard: vi.fn().mockResolvedValue(undefined),
  downloadTextFile: vi.fn(),
}));

const RESULT: ReviewResult = {
  review_id: "rev_3",
  type: "dockerfile",
  summary: { critical: 0, high: 1, medium: 1, low: 0, info: 0 },
  findings: [
    {
      id: "DF-SEC-001",
      category: "security",
      severity: "HIGH",
      title: "Container runs as root",
      line_start: 1,
      description: "d",
      impact: "i",
      recommendation: "r",
      source: "static-analysis",
    },
    {
      id: "DF-SIZE-001",
      category: "size",
      severity: "MEDIUM",
      title: "Base image may contain unnecessary packages",
      description: "d2",
      impact: "i2",
      recommendation: "r2",
      source: "static-analysis",
    },
  ],
  original_content: "FROM python:3.12\n",
  corrected_content: "FROM python:3.12-slim\n",
  diff: "--- original\n+++ corrected\n-FROM python:3.12\n+FROM python:3.12-slim\n",
  change_summary: [{ change: "Use slim image", reason: "Reduce size" }],
  ai_status: "available",
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.mocked(exportReview.copyToClipboard).mockResolvedValue(undefined);
  vi.mocked(exportReview.downloadTextFile).mockReset();
});

async function renderCompletedReview() {
  const user = userEvent.setup();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => RESULT }));
  render(<ReviewPage />);
  await user.type(screen.getByLabelText("mock-editor"), "FROM python:3.12");
  await user.click(screen.getByRole("button", { name: /review/i }));
  await waitFor(() => expect(screen.getByText(/Container runs as root/i)).toBeInTheDocument());
  return user;
}

describe("Review experience: finding navigation, diff, and export", () => {
  it("filters findings by severity", async () => {
    const user = await renderCompletedReview();
    await user.selectOptions(screen.getByLabelText(/^severity$/i), "MEDIUM");
    expect(screen.queryByText(/Container runs as root/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Base image may contain unnecessary packages/i)).toBeInTheDocument();
  });

  it("navigates between Overview, Corrected Version, and Diff tabs", async () => {
    const user = await renderCompletedReview();
    await user.click(screen.getByRole("tab", { name: /corrected version/i }));
    expect(screen.getByLabelText(/corrected content/i)).toHaveTextContent("FROM python:3.12-slim");

    await user.click(screen.getByRole("tab", { name: /^diff$/i }));
    expect(screen.getByLabelText(/unified diff/i)).toHaveTextContent("+FROM python:3.12-slim");
  });

  it("copies the diff and corrected version, and triggers a download, without mutating the original", async () => {
    const user = await renderCompletedReview();
    await user.click(screen.getByRole("tab", { name: /^diff$/i }));

    await user.click(screen.getByRole("button", { name: /copy diff/i }));
    expect(exportReview.copyToClipboard).toHaveBeenCalledWith(RESULT.diff);

    await user.click(screen.getByRole("button", { name: /copy corrected version/i }));
    expect(exportReview.copyToClipboard).toHaveBeenCalledWith(RESULT.corrected_content);

    await user.click(screen.getByRole("button", { name: /download corrected file/i }));
    expect(exportReview.downloadTextFile).toHaveBeenCalledWith(
      expect.stringContaining("corrected"),
      RESULT.corrected_content,
    );

    const editor = screen.getByLabelText("mock-editor") as HTMLTextAreaElement;
    expect(editor.value).toBe("FROM python:3.12");
  });
});
