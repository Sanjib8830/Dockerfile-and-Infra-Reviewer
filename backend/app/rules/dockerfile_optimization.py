"""Deterministic Dockerfile size and maintainability rules (PRD Section 8 FR-03, Section 19).

Static estimates always use qualified language ("likely reduces...") rather than
claiming an exact, unmeasured size reduction (FR-020).
"""

from __future__ import annotations

import re

from app.schemas.review import Category, Finding, FindingSource, Severity

_FULL_DISTRO_IMAGES = ("ubuntu", "debian", "centos", "python", "node", "golang")
_SLIM_MARKERS = ("slim", "alpine", "distroless")
_BROAD_COPY_PATTERN = re.compile(r"^\s*COPY\s+\.\s+(\.|/\S*)\s*$")
_PIP_INSTALL_NO_CACHE = re.compile(r"pip\s+install(?!.*--no-cache-dir)", re.IGNORECASE)
_APT_GET_INSTALL_NO_CLEAN = re.compile(r"apt-get\s+install", re.IGNORECASE)
_APT_GET_CLEAN_HINT = re.compile(r"rm\s+-rf\s+/var/lib/apt/lists", re.IGNORECASE)


def _lines(source: str) -> list[str]:
    return source.splitlines()


def check_full_distro_base_image(source: str) -> list[Finding]:
    """DF-SIZE-001: a full (non-slim) base image is used where a smaller variant likely exists."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        match = re.match(r"^\s*FROM\s+([^\s]+)", line, re.IGNORECASE)
        if not match:
            continue
        image = match.group(1).lower()
        base = image.split(":", 1)[0].split("/")[-1]
        if base in _FULL_DISTRO_IMAGES and not any(marker in image for marker in _SLIM_MARKERS):
            findings.append(
                Finding(
                    id="DF-SIZE-001",
                    category=Category.SIZE,
                    severity=Severity.MEDIUM,
                    title="Base image may contain unnecessary packages",
                    line_start=index,
                    line_end=index,
                    description=f"The base image `{image}` is a full distribution image.",
                    impact="Larger images increase pull time, attack surface, and storage cost.",
                    recommendation="Likely reduces image size because a slim or alpine variant omits unused OS packages.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_pip_cache_retention(source: str) -> list[Finding]:
    """DF-SIZE-002: pip installs without `--no-cache-dir` retain unnecessary cache in the image layer."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        if _PIP_INSTALL_NO_CACHE.search(line):
            findings.append(
                Finding(
                    id="DF-SIZE-002",
                    category=Category.SIZE,
                    severity=Severity.MEDIUM,
                    title="Dependency installation retains package cache",
                    line_start=index,
                    line_end=index,
                    description="`pip install` is used without `--no-cache-dir`.",
                    impact="The pip download cache is retained in the image layer, increasing image size.",
                    recommendation="Likely reduces image size because --no-cache-dir avoids storing the pip cache.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_broad_copy(source: str) -> list[Finding]:
    """DF-SIZE-003: `COPY . .` style instructions may copy unnecessary build/context files."""
    findings: list[Finding] = []
    for index, line in enumerate(_lines(source), start=1):
        if _BROAD_COPY_PATTERN.match(line):
            findings.append(
                Finding(
                    id="DF-SIZE-003",
                    category=Category.SIZE,
                    severity=Severity.LOW,
                    title="Broad COPY may include unnecessary files",
                    line_start=index,
                    line_end=index,
                    description="`COPY . .` copies the entire build context into the image.",
                    impact="Unrelated files (tests, docs, local caches) may be copied into the final image.",
                    recommendation="Copy only the files required at runtime, or add a `.dockerignore` file.",
                    source=FindingSource.STATIC_ANALYSIS,
                )
            )
    return findings


def check_missing_dockerignore_opportunity(source: str, *, dockerignore_present: bool = False) -> list[Finding]:
    """DF-SIZE-004: a broad COPY is used but no `.dockerignore` was supplied alongside the review."""
    if dockerignore_present:
        return []
    if not _BROAD_COPY_PATTERN.search(source) and "COPY . " not in source:
        return []
    return [
        Finding(
            id="DF-SIZE-004",
            category=Category.SIZE,
            severity=Severity.INFO,
            title="Missing .dockerignore opportunity",
            description="No `.dockerignore` was supplied alongside a broad COPY instruction.",
            impact="Without a `.dockerignore`, local build artifacts and caches may be copied into the image.",
            recommendation="Likely reduces image size because a .dockerignore excludes unnecessary local files.",
            source=FindingSource.STATIC_ANALYSIS,
        )
    ]


def check_missing_multistage_build(source: str) -> list[Finding]:
    """DF-SIZE-005: a single-stage build is used even though build tooling is installed."""
    from_count = len(re.findall(r"^\s*FROM\s+", source, re.MULTILINE | re.IGNORECASE))
    has_build_tools = bool(re.search(r"\b(gcc|build-essential|make|cmake)\b", source, re.IGNORECASE))
    if from_count <= 1 and has_build_tools:
        return [
            Finding(
                id="DF-SIZE-005",
                category=Category.SIZE,
                severity=Severity.INFO,
                title="Multi-stage build may reduce final image size",
                description="Build tooling is installed in a single-stage build.",
                impact="Compilers and build dependencies remain in the final runtime image.",
                recommendation="Likely reduces image size because a multi-stage build discards build-only tooling.",
                source=FindingSource.STATIC_ANALYSIS,
            )
        ]
    return []


def check_apt_cache_retention(source: str) -> list[Finding]:
    """DF-SIZE-006: apt-get install without cleaning the package list cache."""
    if _APT_GET_INSTALL_NO_CLEAN.search(source) and not _APT_GET_CLEAN_HINT.search(source):
        return [
            Finding(
                id="DF-SIZE-006",
                category=Category.SIZE,
                severity=Severity.LOW,
                title="APT package list cache retained",
                description="`apt-get install` is used without removing `/var/lib/apt/lists`.",
                impact="The apt package index is retained in the image layer, increasing image size.",
                recommendation="Likely reduces image size because removing the apt cache trims unused index data.",
                source=FindingSource.STATIC_ANALYSIS,
            )
        ]
    return []


def run_all(source: str, *, dockerignore_present: bool = False) -> list[Finding]:
    """Run every Dockerfile size/optimization rule and return the combined findings."""
    findings: list[Finding] = []
    findings.extend(check_full_distro_base_image(source))
    findings.extend(check_pip_cache_retention(source))
    findings.extend(check_broad_copy(source))
    findings.extend(check_missing_dockerignore_opportunity(source, dockerignore_present=dockerignore_present))
    findings.extend(check_missing_multistage_build(source))
    findings.extend(check_apt_cache_retention(source))
    return findings
