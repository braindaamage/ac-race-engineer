"""Pydantic v2 models for the knowledge base."""

from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeFragment(BaseModel):
    """A single section from a knowledge base document."""

    source_file: str = Field(min_length=1)
    section_title: str = Field(min_length=1)
    content: str = ""
    tags: list[str] = []
