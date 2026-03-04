# Public API Contract: Knowledge Base Module

**Module**: `ac_engineer.knowledge`
**Branch**: `005-knowledge-base` | **Date**: 2026-03-04

## Exports

```python
from ac_engineer.knowledge import (
    get_knowledge_for_signals,  # Signal-based retrieval
    search_knowledge,            # Keyword search
    KnowledgeFragment,           # Output model
)
```

## Functions

### `get_knowledge_for_signals(session: AnalyzedSession) -> list[KnowledgeFragment]`

Inspects an analyzed session for detectable conditions and returns relevant knowledge fragments.

**Parameters**:
- `session`: An `AnalyzedSession` object from the analyzer module.

**Returns**: List of `KnowledgeFragment` objects, deduplicated by `(source_file, section_title)`. Empty list if no signals detected or session has no analyzable data.

**Behavior**:
1. Runs all signal detectors against the session
2. For each detected signal, looks up relevant (document, section) pairs in SIGNAL_MAP
3. Loads section content from documents
4. Deduplicates by (source_file, section_title)
5. Returns fragments

**Error handling**: Never raises. Returns empty list on missing/None fields.

---

### `search_knowledge(query: str) -> list[KnowledgeFragment]`

Searches the knowledge base for fragments matching the given query.

**Parameters**:
- `query`: Free-text search string (e.g., `"rear anti-roll bar oversteer"`).

**Returns**: List of `KnowledgeFragment` objects ranked by relevance (number of keyword matches, descending). Empty list if no matches or query is empty/whitespace.

**Behavior**:
1. Tokenizes query (lowercase, split on whitespace/punctuation)
2. Filters out tokens shorter than 2 characters
3. Matches tokens against KNOWLEDGE_INDEX tags and document section content
4. Ranks results by match count
5. Returns fragments

**Error handling**: Never raises. Returns empty list for empty/nonsensical queries.

---

## Model

### `KnowledgeFragment(BaseModel)`

```python
class KnowledgeFragment(BaseModel):
    source_file: str      # e.g., "vehicle_balance_fundamentals.md"
    section_title: str    # e.g., "Physical Principles"
    content: str          # Full section text
    tags: list[str]       # Associated keywords from KNOWLEDGE_INDEX
```

## Dependencies

**Imports FROM** (allowed):
- `ac_engineer.analyzer.models.AnalyzedSession` (type annotation for `get_knowledge_for_signals`)

**Imports TO** (expected consumers):
- `ac_engineer.engineer.*` (Phase 5 — AI agents will call both functions)
- `api/` routes (Phase 6 — thin HTTP wrappers)
- `backend/tests/knowledge/` (tests)
