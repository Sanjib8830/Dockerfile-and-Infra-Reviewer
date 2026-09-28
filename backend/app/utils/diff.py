"""Unified diff generation for distinct original and corrected content (PRD Section 24)."""

from __future__ import annotations

import difflib


def generate_unified_diff(original: str, corrected: str, *, filename: str = "review") -> str:
    """Return a unified diff between `original` and `corrected`.

    Both inputs are treated as immutable; this function never mutates either
    argument nor the caller's stored `original_content` (Constitution Principle III).
    """
    original_lines = original.splitlines(keepends=True)
    corrected_lines = corrected.splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        original_lines,
        corrected_lines,
        fromfile=f"original/{filename}",
        tofile=f"corrected/{filename}",
    )
    return "".join(diff_lines)
