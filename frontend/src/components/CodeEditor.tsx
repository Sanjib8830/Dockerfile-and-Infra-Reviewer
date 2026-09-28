import Editor from "@monaco-editor/react";
import type { ReviewType } from "../types/review";

interface CodeEditorProps {
  type: ReviewType;
  value: string;
  onChange: (value: string) => void;
  ariaLabel?: string;
}

const LANGUAGE_BY_TYPE: Record<ReviewType, string> = {
  dockerfile: "dockerfile",
  terraform: "hcl",
};

/**
 * Monaco-based source editor with line numbers. Renders submitted text as plain
 * text content only; Monaco never interprets or executes the value.
 */
function CodeEditor({ type, value, onChange, ariaLabel = "Source code editor" }: CodeEditorProps) {
  return (
    <div role="group" aria-label={ariaLabel} data-testid="code-editor">
      <Editor
        height="360px"
        language={LANGUAGE_BY_TYPE[type]}
        value={value}
        onChange={(next) => onChange(next ?? "")}
        options={{
          lineNumbers: "on",
          minimap: { enabled: false },
          readOnly: false,
        }}
      />
    </div>
  );
}

export default CodeEditor;
