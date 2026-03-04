"""Tests for KnowledgeFragment model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ac_engineer.knowledge.models import KnowledgeFragment


class TestKnowledgeFragment:
    """KnowledgeFragment creation and validation."""

    def test_fragment_creation(self):
        frag = KnowledgeFragment(
            source_file="test.md",
            section_title="Physical Principles",
            content="Some content here.",
            tags=["balance", "weight transfer"],
        )
        assert frag.source_file == "test.md"
        assert frag.section_title == "Physical Principles"
        assert frag.content == "Some content here."
        assert frag.tags == ["balance", "weight transfer"]

    def test_fragment_empty_content(self):
        frag = KnowledgeFragment(
            source_file="test.md",
            section_title="Section",
            content="",
            tags=[],
        )
        assert frag.content == ""

    def test_fragment_empty_tags(self):
        frag = KnowledgeFragment(
            source_file="test.md",
            section_title="Section",
        )
        assert frag.tags == []

    def test_fragment_source_file_required(self):
        with pytest.raises(ValidationError):
            KnowledgeFragment(
                source_file="",
                section_title="Section",
            )

    def test_fragment_section_title_required(self):
        with pytest.raises(ValidationError):
            KnowledgeFragment(
                source_file="test.md",
                section_title="",
            )

    def test_fragment_defaults(self):
        frag = KnowledgeFragment(
            source_file="test.md",
            section_title="Section",
        )
        assert frag.content == ""
        assert frag.tags == []
