# Quickstart: Knowledge Base Module

**Branch**: `005-knowledge-base` | **Date**: 2026-03-04

## Setup

```bash
conda activate ac-race-engineer
# No additional dependencies needed — uses pydantic (already installed) + stdlib
```

## Usage

### Signal-Based Retrieval (Primary)

```python
from ac_engineer.analyzer import analyze_session
from ac_engineer.knowledge import get_knowledge_for_signals

# After analyzing a session...
analyzed = analyze_session(parsed_session)

# Get knowledge fragments for detected conditions
fragments = get_knowledge_for_signals(analyzed)

for frag in fragments:
    print(f"[{frag.source_file}] {frag.section_title}")
    print(f"  Tags: {frag.tags}")
    print(f"  Content: {frag.content[:100]}...")
```

### Keyword Search

```python
from ac_engineer.knowledge import search_knowledge

# Free-text search
fragments = search_knowledge("rear anti-roll bar oversteer")

for frag in fragments:
    print(f"[{frag.source_file}] {frag.section_title}")
```

## Running Tests

```bash
conda activate ac-race-engineer

# All knowledge tests
pytest backend/tests/knowledge/ -v

# All backend tests (parser + analyzer + knowledge)
pytest backend/tests/ -v
```

## File Structure

```
backend/ac_engineer/knowledge/
├── __init__.py       # Public API
├── models.py         # KnowledgeFragment
├── index.py          # KNOWLEDGE_INDEX + SIGNAL_MAP
├── loader.py         # Document loading/validation/caching
├── signals.py        # Signal detectors + thresholds
├── search.py         # Keyword search
└── docs/             # 10 domain docs + 2 templates
    └── user/         # User-created documents
```
