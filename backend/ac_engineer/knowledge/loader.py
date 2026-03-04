"""Document loading, parsing, validation, and caching."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_SECTIONS = [
    "Physical Principles",
    "Adjustable Parameters and Effects",
    "Telemetry Diagnosis",
    "Cross-References",
]

_HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)

_cache: dict[str, dict[str, str]] | None = None


def _default_docs_dir() -> Path:
    """Return the docs/ directory relative to this file."""
    return Path(__file__).parent / "docs"


def parse_document(path: Path) -> dict[str, str]:
    """Split a Markdown file by ``## `` headings into section_title → content."""
    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    matches = list(_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def validate_document(sections: dict[str, str]) -> list[str]:
    """Return list of missing required sections."""
    return [s for s in REQUIRED_SECTIONS if s not in sections]


def load_all_documents(
    docs_dir: Path | None = None,
) -> dict[str, dict[str, str]]:
    """Scan docs/ and docs/user/ for .md files, parse and validate each.

    Invalid documents are logged and excluded from the result.
    """
    base = docs_dir or _default_docs_dir()
    result: dict[str, dict[str, str]] = {}

    dirs_to_scan = [base]
    user_dir = base / "user"
    if user_dir.is_dir():
        dirs_to_scan.append(user_dir)

    for d in dirs_to_scan:
        if not d.is_dir():
            continue
        for md_file in sorted(d.glob("*.md")):
            sections = parse_document(md_file)
            missing = validate_document(sections)
            if missing:
                logger.warning(
                    "Skipping %s: missing sections %s", md_file.name, missing
                )
                continue
            result[md_file.name] = sections

    return result


def get_docs_cache() -> dict[str, dict[str, str]]:
    """Lazy singleton cache — loads all documents on first call."""
    global _cache  # noqa: PLW0603
    if _cache is None:
        _cache = load_all_documents()
    return _cache
