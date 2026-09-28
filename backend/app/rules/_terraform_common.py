"""Shared Terraform parsing helpers used by multiple rule modules."""

from __future__ import annotations

import re


def resource_blocks(source: str) -> list[tuple[str, str, int, str]]:
    """Yield (resource_type, resource_name, start_line, block_text) for each `resource` block."""
    blocks: list[tuple[str, str, int, str]] = []
    pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE)
    for match in pattern.finditer(source):
        start_line = source[: match.start()].count("\n") + 1
        depth = 0
        end = match.end()
        for i in range(match.end() - 1, len(source)):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        blocks.append((match.group(1), match.group(2), start_line, source[match.start() : end]))
    return blocks
