"""Keyword search across the knowledge base."""

from __future__ import annotations

import re

from .index import KNOWLEDGE_INDEX
from .loader import get_docs_cache
from .models import KnowledgeFragment


def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumeric, filter tokens shorter than 2 chars."""
    tokens = re.split(r"[^a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if len(t) >= 2]


def search_knowledge(query: str) -> list[KnowledgeFragment]:
    """Search the knowledge base by keyword matching.

    Matches query tokens against KNOWLEDGE_INDEX tags and document content.
    Returns fragments ranked by match count (descending).
    Returns empty list for empty/whitespace queries or no matches.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    cache = get_docs_cache()
    scored: list[tuple[int, KnowledgeFragment]] = []

    for doc_name, sections in cache.items():
        index_entry = KNOWLEDGE_INDEX.get(doc_name, {})

        for section_title, content in sections.items():
            score = 0
            tags = index_entry.get(section_title, [])

            # Match against tags
            tags_lower = [t.lower() for t in tags]
            for token in query_tokens:
                for tag in tags_lower:
                    if token in tag:
                        score += 1
                        break

            # Match against content
            content_lower = content.lower()
            for token in query_tokens:
                if token in content_lower:
                    score += 1

            if score > 0:
                frag = KnowledgeFragment(
                    source_file=doc_name,
                    section_title=section_title,
                    content=content,
                    tags=tags,
                )
                scored.append((score, frag))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [frag for _, frag in scored]
