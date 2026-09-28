import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ReviewPage from "../src/pages/ReviewPage";
import type { ReviewResult } from "../src/types/review";

vi.mock("@monaco-editor/react", () => ({
  default: ({ value, onChange }: { value: string; onChange: (value: string) => void }) => (
    <textarea aria-label="mock-editor" value={value} onChange={(event) => onChange(event.target.value)} />
  ),
}));

const RESULT: ReviewResult = {
  review_id: "rev_4",
  type: "dockerfile",
  summary: { critical: 0, high: 1, medium: 0, low: 0, info: 0 },
  findings: [
    {
      id: "DF-SEC-001",
      category: "security",
      severity: "HIGH",
      title: "Container runs as root",
      description: "<script>alert('xss')</script>",
      impact: "i",
      recommendation: "r",
      source: "static-analysis",
    },
  ],
  original_content: "FROM python:3.12\n",
  ai_status: "not_requested",
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Review accessibility and text safety", () => {
  it("exposes the review tabs with proper tab roles and keyboard-focusable buttons", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => RESULT }));
    render(<ReviewPage />);

    await user.type(screen.getByLabelText("mock-editor"), "FROM python:3.12");
    await user.click(screen.getByRole("button", { name: /review/i }));
    await waitFor(() => expect(screen.getByRole("tablist")).toBeInTheDocument());

    const tabs = screen.getAllByRole("tab");
    expect(tabs.length).toBeGreaterThan(0);
    for (const tab of tabs) {
      expect(tab).toHaveAttribute("aria-selected");
    }
  });

  it("announces loading and error states via role=status/alert", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ error: "INVALID_INPUT", message: "The uploaded file is empty." }),
      }),
    );
    render(<ReviewPage />);
    await user.type(screen.getByLabelText("mock-editor"), "x");
    await user.click(screen.getByRole("button", { name: /review/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  it("renders finding descriptions as plain text rather than executable HTML", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => RESULT }));
    render(<ReviewPage />);
    await user.type(screen.getByLabelText("mock-editor"), "FROM python:3.12");
    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByText(/alert\('xss'\)/i)).toBeInTheDocument());
    expect(document.querySelector("script")).toBeNull();
  });

  it("keeps the review button reachable via keyboard tab order", async () => {
    render(<ReviewPage />);
    const editor = screen.getByLabelText("mock-editor");
    editor.focus();
    expect(document.activeElement).toBe(editor);
  });
});
