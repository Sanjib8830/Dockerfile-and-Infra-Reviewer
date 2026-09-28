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

const DOCKERFILE_RESULT: ReviewResult = {
  review_id: "rev_1",
  type: "dockerfile",
  summary: { critical: 0, high: 1, medium: 0, low: 0, info: 0 },
  findings: [
    {
      id: "DF-SEC-001",
      category: "security",
      severity: "HIGH",
      title: "Container runs as root",
      description: "The Docker image does not define a non-root runtime user.",
      impact: "Elevated privileges if compromised.",
      recommendation: "Create a dedicated non-root user and switch to it using USER.",
      source: "static-analysis",
    },
  ],
  original_content: "FROM python:3.12\nCMD [\"python\", \"app.py\"]\n",
  ai_status: "not_requested",
};

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("ReviewPage - Dockerfile workflow", () => {
  it("lets the user select Dockerfile, paste content, submit, and see findings", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => DOCKERFILE_RESULT,
      }),
    );

    render(<ReviewPage />);

    const editor = screen.getByLabelText("mock-editor");
    await user.type(editor, "FROM python:3.12");

    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByText(/Container runs as root/i)).toBeInTheDocument());
    expect(screen.getByText("HIGH", { selector: ".severity-badge" })).toBeInTheDocument();
  });

  it("shows a loading state while the review request is pending", async () => {
    const user = userEvent.setup();
    let resolveFetch: (value: unknown) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
      ),
    );

    render(<ReviewPage />);
    const editor = screen.getByLabelText("mock-editor");
    await user.type(editor, "FROM python:3.12");
    await user.click(screen.getByRole("button", { name: /review/i }));

    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    resolveFetch({ ok: true, json: async () => DOCKERFILE_RESULT });
  });

  it("displays an error message when the request fails", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ error: "INVALID_INPUT", message: "The uploaded file is empty." }),
      }),
    );

    render(<ReviewPage />);
    const editor = screen.getByLabelText("mock-editor");
    await user.type(editor, "x");
    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/empty/i));
  });

  it("shows the AI-unavailable fallback message while keeping deterministic findings", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ ...DOCKERFILE_RESULT, ai_status: "unavailable" }),
      }),
    );

    render(<ReviewPage />);
    const editor = screen.getByLabelText("mock-editor");
    await user.type(editor, "FROM python:3.12");
    await user.click(screen.getByRole("button", { name: /review/i }));

    await waitFor(() => expect(screen.getByText(/AI explanation temporarily unavailable/i)).toBeInTheDocument());
    expect(screen.getByText(/Container runs as root/i)).toBeInTheDocument();
  });

  it("clears the editor content when Clear is clicked", async () => {
    const user = userEvent.setup();
    render(<ReviewPage />);
    const editor = screen.getByLabelText("mock-editor") as HTMLTextAreaElement;
    await user.type(editor, "FROM python:3.12");
    expect(editor.value).toContain("FROM python:3.12");

    await user.click(screen.getByRole("button", { name: /^clear$/i }));
    expect(editor.value).toBe("");
  });

  it("loads example content when Load example is clicked", async () => {
    const user = userEvent.setup();
    render(<ReviewPage />);
    await user.click(screen.getByRole("button", { name: /load example/i }));
    const editor = screen.getByLabelText("mock-editor") as HTMLTextAreaElement;
    expect(editor.value).toContain("FROM python:3.12");
  });
});
