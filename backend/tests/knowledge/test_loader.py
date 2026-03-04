"""Tests for document loader, parser, validator, and cache."""

from __future__ import annotations

import time
from pathlib import Path

from ac_engineer.knowledge import loader
from ac_engineer.knowledge.loader import (
    REQUIRED_SECTIONS,
    get_docs_cache,
    load_all_documents,
    parse_document,
    validate_document,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_DOC = """\
# Test Document

## Physical Principles

Physics content here.

## Adjustable Parameters and Effects

Parameters content here.

## Telemetry Diagnosis

Diagnosis content here.

## Cross-References

Cross-ref content here.
"""

INVALID_DOC = """\
# Incomplete Document

## Physical Principles

Only one section.
"""


def _write_doc(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# parse_document
# ---------------------------------------------------------------------------


class TestParseDocument:
    def test_parse_document_extracts_sections(self, tmp_path):
        path = _write_doc(tmp_path, "test.md", VALID_DOC)
        sections = parse_document(path)
        assert set(sections.keys()) == set(REQUIRED_SECTIONS)

    def test_parse_document_content_correct(self, tmp_path):
        path = _write_doc(tmp_path, "test.md", VALID_DOC)
        sections = parse_document(path)
        assert sections["Physical Principles"] == "Physics content here."
        assert sections["Cross-References"] == "Cross-ref content here."

    def test_parse_empty_sections(self, tmp_path):
        doc = "# Title\n\n## Physical Principles\n\n## Adjustable Parameters and Effects\n\n## Telemetry Diagnosis\n\n## Cross-References\n"
        path = _write_doc(tmp_path, "empty.md", doc)
        sections = parse_document(path)
        for section in REQUIRED_SECTIONS:
            assert section in sections
            # Empty sections get empty string after strip
            assert isinstance(sections[section], str)


# ---------------------------------------------------------------------------
# validate_document
# ---------------------------------------------------------------------------


class TestValidateDocument:
    def test_validate_document_all_present(self):
        sections = {s: "content" for s in REQUIRED_SECTIONS}
        assert validate_document(sections) == []

    def test_validate_document_missing_section(self):
        sections = {s: "content" for s in REQUIRED_SECTIONS if s != "Telemetry Diagnosis"}
        missing = validate_document(sections)
        assert missing == ["Telemetry Diagnosis"]

    def test_validate_document_missing_multiple(self):
        sections = {"Physical Principles": "content"}
        missing = validate_document(sections)
        assert "Adjustable Parameters and Effects" in missing
        assert "Telemetry Diagnosis" in missing
        assert len(missing) == 3


# ---------------------------------------------------------------------------
# load_all_documents
# ---------------------------------------------------------------------------


class TestLoadAllDocuments:
    def test_load_all_bundled_documents_valid(self):
        """All bundled docs + templates pass validation — expect 12 files."""
        result = load_all_documents()
        assert len(result) >= 12
        for filename, sections in result.items():
            assert validate_document(sections) == [], f"{filename} has missing sections"

    def test_load_excludes_invalid_document(self, tmp_path):
        _write_doc(tmp_path, "good.md", VALID_DOC)
        _write_doc(tmp_path, "bad.md", INVALID_DOC)
        result = load_all_documents(tmp_path)
        assert "good.md" in result
        assert "bad.md" not in result

    def test_load_empty_directory(self, tmp_path):
        result = load_all_documents(tmp_path)
        assert result == {}

    def test_load_nonexistent_directory(self, tmp_path):
        result = load_all_documents(tmp_path / "nonexistent")
        assert result == {}


# ---------------------------------------------------------------------------
# get_docs_cache
# ---------------------------------------------------------------------------


class TestDocsCache:
    def test_cache_returns_same_object(self):
        # Reset cache to ensure clean state
        loader._cache = None
        try:
            a = get_docs_cache()
            b = get_docs_cache()
            assert a is b
        finally:
            loader._cache = None


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_documents_load_under_one_second(self):
        start = time.perf_counter()
        load_all_documents()
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"Loading took {elapsed:.3f}s"
