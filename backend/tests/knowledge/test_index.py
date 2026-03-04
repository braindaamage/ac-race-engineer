"""Tests for KNOWLEDGE_INDEX and SIGNAL_MAP validity."""

from __future__ import annotations

from pathlib import Path

from ac_engineer.knowledge.index import KNOWLEDGE_INDEX, SIGNAL_MAP
from ac_engineer.knowledge.loader import REQUIRED_SECTIONS

DOCS_DIR = Path(__file__).resolve().parents[2] / "ac_engineer" / "knowledge" / "docs"

# Template files are excluded from the index
TEMPLATE_FILES = {"car_template.md", "track_template.md"}


class TestKnowledgeIndex:
    def test_knowledge_index_references_valid_documents(self):
        """Every key in KNOWLEDGE_INDEX is a .md file that exists in docs/."""
        for filename in KNOWLEDGE_INDEX:
            assert (DOCS_DIR / filename).exists(), f"{filename} not found in docs/"

    def test_knowledge_index_references_valid_sections(self):
        """Every section name in KNOWLEDGE_INDEX matches a required section."""
        for filename, sections in KNOWLEDGE_INDEX.items():
            for section in sections:
                assert section in REQUIRED_SECTIONS, (
                    f"{filename}: '{section}' not in REQUIRED_SECTIONS"
                )

    def test_all_documents_in_index(self):
        """Every domain .md file in docs/ (except templates) has an entry in KNOWLEDGE_INDEX."""
        for md_file in sorted(DOCS_DIR.glob("*.md")):
            if md_file.name in TEMPLATE_FILES:
                continue
            assert md_file.name in KNOWLEDGE_INDEX, (
                f"{md_file.name} not in KNOWLEDGE_INDEX"
            )


class TestSignalMap:
    def test_signal_map_references_valid_documents(self):
        """Every (doc, section) in SIGNAL_MAP references a doc in KNOWLEDGE_INDEX."""
        for signal, pairs in SIGNAL_MAP.items():
            for doc, section in pairs:
                assert doc in KNOWLEDGE_INDEX, (
                    f"Signal '{signal}': doc '{doc}' not in KNOWLEDGE_INDEX"
                )

    def test_signal_map_references_valid_sections(self):
        """Every section in SIGNAL_MAP tuples is a valid required section."""
        for signal, pairs in SIGNAL_MAP.items():
            for doc, section in pairs:
                assert section in REQUIRED_SECTIONS, (
                    f"Signal '{signal}': section '{section}' not valid"
                )

    def test_signal_map_covers_core_signals(self):
        """SIGNAL_MAP contains at minimum the three core signals."""
        assert "high_understeer" in SIGNAL_MAP
        assert "tyre_temp_spread_high" in SIGNAL_MAP
        assert "lap_time_degradation" in SIGNAL_MAP
