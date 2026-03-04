"""Vehicle dynamics knowledge base with signal-based and keyword retrieval."""

from __future__ import annotations

from ac_engineer.analyzer.models import AnalyzedSession

from .index import KNOWLEDGE_INDEX, SIGNAL_MAP
from .loader import get_docs_cache
from .models import KnowledgeFragment
from .search import search_knowledge as search_knowledge
from .signals import detect_signals

__all__ = [
    "get_knowledge_for_signals",
    "search_knowledge",
    "KnowledgeFragment",
]


def get_knowledge_for_signals(
    session: AnalyzedSession,
) -> list[KnowledgeFragment]:
    """Detect signals in an analyzed session and return relevant knowledge.

    Never raises — returns empty list if no signals detected or data is missing.
    """
    try:
        signal_names = detect_signals(session)
    except Exception:
        return []

    if not signal_names:
        return []

    # Collect unique (doc, section) pairs
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str]] = []
    for signal in signal_names:
        for doc, section in SIGNAL_MAP.get(signal, []):
            key = (doc, section)
            if key not in seen:
                seen.add(key)
                pairs.append(key)

    # Build fragments
    cache = get_docs_cache()
    fragments: list[KnowledgeFragment] = []
    for doc, section in pairs:
        doc_sections = cache.get(doc, {})
        content = doc_sections.get(section, "")
        tags = KNOWLEDGE_INDEX.get(doc, {}).get(section, [])
        fragments.append(
            KnowledgeFragment(
                source_file=doc,
                section_title=section,
                content=content,
                tags=tags,
            )
        )

    return fragments
