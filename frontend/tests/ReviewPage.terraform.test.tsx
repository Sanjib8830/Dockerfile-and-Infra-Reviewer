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

const TERRAFORM_RESULT: ReviewResult = {
  review_id: "rev_2",
  type: "terraform",
  summary: { critical: 0, high: 1, medium: 0, low: 0, info: 0 },
  findings: [
    {
      id: "TF-SEC-001",
      category: "security",
      severity: "HIGH",
      title: "Sensitive port 22 exposed to the public internet",
      description: "The security group allows ingress from 0.0.0.0/0 on port 22.",
      impact: "Any host on the internet can attempt to reach SSH.",
      recommendation: "Restrict cidr_blocks to a trusted range.",
      source: "static-analysis",
    },
  ],
  original_content: 'resource "aws_security_group" "app" {}\n',
  corrected_content: 'resource "aws_security_group" "app" { cidr_blocks = var.admin_cidr }\n',
  diff: "--- original\n+++ corrected\n",
  change_summary: [
    {
      change: "Restrict SSH CIDR",
      reason: "Reduce public exposure",
      risk_classification: "REQUIRES_HUMAN_REVIEW",
    },
  ],
  ai_status: "available",
  ai_summary: "One high-severity public SSH exposure was found.",
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("ReviewPage - Terraform workflow", () => {
  it("renders the public SSH finding with HIGH severity", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => TERRAFORM_RESULT }),
    );

    render(<ReviewPage />);
    await user.selectOptions(screen.getByLabelText(/input type/i), "terraform");
    await user.type(screen.getByLabelText("mock-editor"), "resource");
    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByText(/Sensitive port 22 exposed/i)).toBeInTheDocument());
    expect(screen.getByText("HIGH", { selector: ".severity-badge" })).toBeInTheDocument();
  });

  it("shows a risk-classification badge and human-review warning, never a safe-to-apply claim", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => TERRAFORM_RESULT }),
    );

    render(<ReviewPage />);
    await user.selectOptions(screen.getByLabelText(/input type/i), "terraform");
    await user.type(screen.getByLabelText("mock-editor"), "resource");
    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByText(/not guaranteed to be safe to apply/i)).toBeInTheDocument());
    expect(screen.queryByText(/^this terraform is safe to apply\.?$/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /diff/i }));
    await waitFor(() => expect(screen.getByText(/REQUIRES HUMAN REVIEW/i)).toBeInTheDocument());
  });
});
