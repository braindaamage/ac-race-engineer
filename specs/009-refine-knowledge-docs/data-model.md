# Data Model: Refine Knowledge Base Documents

**Branch**: `009-refine-knowledge-docs` | **Date**: 2026-03-05

## Overview

This feature modifies content within existing data structures. No new entities, schemas, or data models are introduced. The changes are purely textual within 10 markdown files and tag additions within a Python dictionary.

## Existing Entities (Unchanged Structure)

### Knowledge Document (Markdown file)

Each document in `backend/ac_engineer/knowledge/docs/` has a fixed structure:

```
# [Document Title]

## Physical Principles
[free-form prose content]

## Adjustable Parameters and Effects
[free-form prose content]

## Telemetry Diagnosis
[free-form prose content]

## Cross-References
[free-form prose content]
```

**Validation rules** (enforced by `loader.py`):
- Must contain all 4 `## ` headings exactly as named
- Parsed by regex `^## (.+)$` into `dict[str, str]`
- Missing sections cause document exclusion (logged warning)

**What changes**: Content within sections. Structure unchanged.

### KNOWLEDGE_INDEX (Python dict in `index.py`)

```python
KNOWLEDGE_INDEX: dict[str, dict[str, list[str]]] = {
    "document_name.md": {
        "Section Title": ["tag1", "tag2", ...],
    },
}
```

**What changes**: Tag lists expanded for sections that gain significant new content. No keys (document names or section titles) added or removed.

### SIGNAL_MAP (Python dict in `index.py`)

```python
SIGNAL_MAP: dict[str, list[tuple[str, str]]] = {
    "signal_name": [("document.md", "Section Title"), ...],
}
```

**What changes**: Nothing. No new signals or signal-to-document mappings.

## Files Modified

| File | Change Type | Scope |
|------|------------|-------|
| `backend/ac_engineer/knowledge/docs/tyre_dynamics.md` | Content edit | Add brush model, load sensitivity, SAT, relaxation length |
| `backend/ac_engineer/knowledge/docs/vehicle_balance_fundamentals.md` | Content edit | Fix transfer attribution, add decomposition, TLLTD |
| `backend/ac_engineer/knowledge/docs/telemetry_and_diagnosis.md` | Content edit | Fix sample rate, add G-G diagram, reframe symptom table |
| `backend/ac_engineer/knowledge/docs/suspension_and_springs.md` | Content edit | Fix spring→wheel rate, fix transfer speed, add roll center |
| `backend/ac_engineer/knowledge/docs/drivetrain.md` | Content edit | Fix ramp angles→lock percentages in Physical Principles |
| `backend/ac_engineer/knowledge/docs/braking.md` | Content edit | Add car-specific availability notes |
| `backend/ac_engineer/knowledge/docs/dampers.md` | Content edit | Add velocity domains, AC parameter names, ratios |
| `backend/ac_engineer/knowledge/docs/alignment.md` | Content edit | Clarify adjustable vs fixed, add dynamic camber |
| `backend/ac_engineer/knowledge/docs/aero_balance.md` | Content edit | Add AC aero model, CoP, L/D ratio |
| `backend/ac_engineer/knowledge/docs/setup_methodology.md` | Content edit | Add OVAT limits, increase lap count, sensitivity hierarchy |
| `backend/ac_engineer/knowledge/index.py` | Tag expansion | Add new tags to existing section entries |
