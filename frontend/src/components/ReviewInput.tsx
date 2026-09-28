import { useRef } from "react";
import type { ReviewType } from "../types/review";

const EXAMPLES: Record<ReviewType, string> = {
  dockerfile: `FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install flask requests

EXPOSE 5000

CMD ["python", "app.py"]
`,
  terraform: `resource "aws_security_group" "app" {
  name = "app"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
`,
};

interface ReviewInputProps {
  type: ReviewType;
  onTypeChange: (type: ReviewType) => void;
  onContentChange: (content: string) => void;
  onClear: () => void;
}

/**
 * Input-selection controls: Dockerfile/Terraform type, file upload, clear, and
 * example loading (FR-001, FR-002).
 */
function ReviewInput({ type, onTypeChange, onContentChange, onClear }: ReviewInputProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      onContentChange(String(reader.result ?? ""));
    };
    reader.readAsText(file);
    event.target.value = "";
  };

  return (
    <div className="review-input-controls">
      <label htmlFor="review-type-select">Input type</label>
      <select
        id="review-type-select"
        value={type}
        onChange={(event) => onTypeChange(event.target.value as ReviewType)}
      >
        <option value="dockerfile">Dockerfile</option>
        <option value="terraform">Terraform</option>
      </select>

      <button type="button" onClick={() => fileInputRef.current?.click()}>
        Upload file
      </button>
      <input
        ref={fileInputRef}
        type="file"
        aria-label="Upload source file"
        style={{ display: "none" }}
        onChange={handleFileUpload}
      />

      <button type="button" onClick={() => onContentChange(EXAMPLES[type])}>
        Load example
      </button>

      <button type="button" onClick={onClear}>
        Clear
      </button>
    </div>
  );
}

export default ReviewInput;
