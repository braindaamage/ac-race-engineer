# Implementation Plan: Knowledge Base Module

**Branch**: `005-knowledge-base` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-knowledge-base/spec.md`

## Summary

Build a self-contained vehicle dynamics knowledge base module at `backend/ac_engineer/knowledge/`. The module contains 10 domain documents and 2 user templates in Markdown, a retrieval index (plain Python dicts), and two retrieval functions: `get_knowledge_for_signals(session)` for threshold-based signal detection mapping to document sections, and `search_knowledge(query)` for keyword matching. Output is `list[KnowledgeFragment]` (Pydantic model). Zero external dependencies beyond pydantic + stdlib.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: pydantic v2 (already installed), pathlib + re (stdlib)
**Storage**: Markdown files in `backend/ac_engineer/knowledge/docs/`
**Testing**: pytest (already installed)
**Target Platform**: Windows 11 (local development)
**Project Type**: Backend library module within existing package
**Performance Goals**: Document loading + validation < 1 second
**Constraints**: Zero external dependencies, no imports from `api/`, mock-testable
**Scale/Scope**: 12 Markdown documents (~10-15 KB each), 10 signal detectors, 2 retrieval functions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Knowledge module is informational only — no setup changes. Signal detectors handle None/missing data gracefully. |
| II. Car-Agnostic Design | PASS | All documents describe general vehicle dynamics principles, not car-specific logic. Templates allow user-specific notes. |
| III. Setup File Autonomy | N/A | Knowledge module does not read or write setup files. |
| IV. LLM as Interpreter, Not Calculator | PASS | No LLM calls. Module provides pre-computed reference material for future LLM consumption. |
| V. Educational Explanations | PASS | Documents are written to educate — physical principles, cause-effect, telemetry diagnosis. |
| VI. Incremental Changes | N/A | No setup changes made by this module. |
| VII. CLI-First MVP | PASS | Module is a library — usable from CLI, API, or tests without modification. |
| VIII. API-First Design | PASS | Pure Python functions in `ac_engineer/knowledge/`, no HTTP code. |
| IX. Separation of Concerns | PASS | Module lives in `ac_engineer/`, no `api/` imports, no frontend concerns. |
| X. Desktop App Stack | N/A | No desktop UI in this phase. |
| XI. LLM Provider Abstraction | N/A | No LLM calls in this module. |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/005-knowledge-base/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── public-api.md    # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   ├── parser/              # Existing — Phase 2
│   ├── analyzer/            # Existing — Phase 3
│   └── knowledge/           # NEW — Phase 4
│       ├── __init__.py      # Public API: get_knowledge_for_signals, search_knowledge, KnowledgeFragment
│       ├── models.py        # KnowledgeFragment Pydantic model
│       ├── index.py         # KNOWLEDGE_INDEX + SIGNAL_MAP dicts
│       ├── loader.py        # Document loading, parsing, validation, caching
│       ├── signals.py       # Signal detector functions + threshold constants
│       ├── search.py        # Keyword search implementation
│       └── docs/
│           ├── vehicle_balance_fundamentals.md
│           ├── suspension_and_springs.md
│           ├── dampers.md
│           ├── alignment.md
│           ├── aero_balance.md
│           ├── braking.md
│           ├── drivetrain.md
│           ├── tyre_dynamics.md
│           ├── telemetry_and_diagnosis.md
│           ├── setup_methodology.md
│           ├── car_template.md
│           ├── track_template.md
│           └── user/        # User-created documents (gitignored)
└── tests/
    └── knowledge/           # NEW — Phase 4 tests
        ├── __init__.py
        ├── conftest.py      # Mock fixtures for AnalyzedSession, test documents
        ├── test_models.py
        ├── test_loader.py
        ├── test_index.py
        ├── test_signals.py
        ├── test_search.py
        └── test_integration.py
```

**Structure Decision**: Follows the established `ac_engineer/<module>/` pattern from parser and analyzer. Internal modules (loader, signals, search) are private implementation; only `__init__.py` exposes the public API. Documents are co-located in `docs/` subdirectory within the package.

## Implementation Phases

### Phase A: Foundation (models + loader + validation)

**Goal**: KnowledgeFragment model, document parser, structure validator, document cache.

1. **models.py** — `KnowledgeFragment(BaseModel)` with 4 fields: source_file, section_title, content, tags.

2. **loader.py** — Core document infrastructure:
   - `REQUIRED_SECTIONS = ["Physical Principles", "Adjustable Parameters and Effects", "Telemetry Diagnosis", "Cross-References"]`
   - `parse_document(path: Path) -> dict[str, str]`: Split Markdown by `## ` headings into section_title → content dict.
   - `validate_document(sections: dict[str, str]) -> list[str]`: Return list of missing required sections.
   - `load_all_documents(docs_dir: Path | None = None) -> dict[str, dict[str, str]]`: Scan `docs/` + `docs/user/`, parse each `.md`, validate, cache results. Return filename → sections dict. Log warnings for invalid documents.
   - Module-level `_cache: dict | None` for lazy singleton pattern.
   - `get_docs_cache() -> dict[str, dict[str, str]]`: Return cached docs, loading on first call.

3. **Test files**: `test_models.py` (fragment creation, validation), `test_loader.py` (parsing, validation, caching, edge cases: empty sections, missing sections, no docs directory).

### Phase B: Domain Documents

**Goal**: Write all 10 domain documents + 2 templates following the 4-section structure.

Each document follows this skeleton:
```markdown
# [Document Title]

## Physical Principles

[Theory content — car-agnostic, informational]

## Adjustable Parameters and Effects

[Setup parameters, what they control, directional effects]

## Telemetry Diagnosis

[How to identify issues from telemetry data]

## Cross-References

[Links to related documents]
```

Documents (in authoring order — foundational topics first):

1. **vehicle_balance_fundamentals.md** — Weight transfer basics, understeer/oversteer gradient, balance by corner phase (entry/mid/exit), neutral steer concept.
2. **tyre_dynamics.md** — Slip angle theory, traction circle/friction ellipse, thermal model (core/surface/inner/mid/outer), pressure effects on contact patch, wear mechanisms.
3. **suspension_and_springs.md** — Spring rate effects, ride height (mechanical grip, not aero), anti-roll bars and roll stiffness distribution, natural frequency.
4. **dampers.md** — Bump/rebound distinction, slow/fast speed ranges, damper velocity histograms, transient vs steady-state load transfer control.
5. **alignment.md** — Camber geometry and contact patch, toe effects on stability/turn-in/tyre wear, caster and mechanical trail, temperature distribution as diagnostic.
6. **aero_balance.md** — Downforce generation, drag, front/rear aero balance, ride height sensitivity (ground effect), speed-dependent grip.
7. **braking.md** — Brake bias front/rear, engine braking effect, brake temperature management, trail braking technique and weight transfer.
8. **drivetrain.md** — LSD types (1-way, 1.5-way, 2-way), preload, power/coast ramp angles, gear ratio selection, final drive trade-offs.
9. **telemetry_and_diagnosis.md** — How to read each telemetry channel category, driver input analysis patterns, symptom-to-cause diagnosis table (symptom → possible causes → which channels to check).
10. **setup_methodology.md** — Baseline setup process, one-variable-at-a-time principle, session planning, how to validate that a change worked.

Templates:
11. **car_template.md** — Placeholder sections for car-specific characteristics (e.g., engine placement, aero presence, mechanical vs aero grip ratio).
12. **track_template.md** — Placeholder sections for track-specific notes (e.g., key corners, surface grip level, elevation changes).

### Phase C: Index and Signal Detection

**Goal**: KNOWLEDGE_INDEX, SIGNAL_MAP, and signal detector functions.

1. **index.py** — Define KNOWLEDGE_INDEX and SIGNAL_MAP as module-level dicts:
   - KNOWLEDGE_INDEX: Map each of the 10 document filenames to their 4 sections, each with a curated list of keyword tags.
   - SIGNAL_MAP: Map each signal name to a list of (document, section) tuples that are relevant to that condition.

2. **signals.py** — Signal detection functions:
   - Threshold constants (module-level).
   - `detect_signals(session: AnalyzedSession) -> list[str]`: Run all detectors, return list of signal names that fired.
   - Individual detector functions (private): `_check_understeer()`, `_check_oversteer()`, `_check_tyre_temp_spread()`, `_check_tyre_temp_imbalance()`, `_check_lap_time_degradation()`, `_check_high_slip_angle()`, `_check_suspension_bottoming()`, `_check_low_consistency()`, `_check_brake_balance()`, `_check_tyre_wear()`.
   - Each detector receives the session, inspects relevant fields, handles None/missing gracefully, returns bool.

3. **Test files**: `test_index.py` (validate all index entries reference existing documents and sections), `test_signals.py` (test each detector with mock sessions above/below thresholds, test None handling).

### Phase D: Search and Public API

**Goal**: Keyword search, public API wiring, integration tests.

1. **search.py** — Keyword search implementation:
   - `_tokenize(text: str) -> list[str]`: Lowercase, split on non-alphanumeric, filter tokens < 2 chars.
   - `search_knowledge(query: str) -> list[KnowledgeFragment]`: Tokenize query, match against KNOWLEDGE_INDEX tags and document content, score by match count, return sorted fragments.

2. **__init__.py** — Public API:
   - `get_knowledge_for_signals(session: AnalyzedSession) -> list[KnowledgeFragment]`: Call `detect_signals()`, look up SIGNAL_MAP, load content via `get_docs_cache()`, build and deduplicate fragments.
   - Re-export `search_knowledge` from search.py.
   - Re-export `KnowledgeFragment` from models.py.
   - `__all__` list.

3. **conftest.py** — Shared test fixtures:
   - `make_analyzed_session(**overrides)` builder function — creates minimal AnalyzedSession with controllable fields (understeer_ratio, temp_spread, lap_time_slope, etc.).
   - `make_corner_metrics(**overrides)` builder — minimal CornerMetrics.
   - `make_stint_metrics(**overrides)` builder — minimal StintMetrics with trends.
   - Named fixtures: `understeer_session`, `tyre_temp_session`, `degradation_session`, `clean_session` (no issues).

4. **test_integration.py** — End-to-end tests:
   - Signal-based retrieval returns fragments for understeer session.
   - Signal-based retrieval returns fragments for tyre temp spread session.
   - Signal-based retrieval returns fragments for lap degradation session.
   - Signal-based retrieval returns empty for clean session.
   - Keyword search for "rear anti-roll bar oversteer" returns results.
   - Keyword search for nonsense returns empty.
   - Deduplication works when multiple signals point to same section.
   - All 10 documents + 2 templates pass validation.

### Phase E: Polish and Finalization

**Goal**: User docs directory, gitignore, final validation.

1. Create `docs/user/` directory with `.gitkeep`.
2. Add `docs/user/*.md` to `.gitignore` (except templates).
3. Run full test suite, fix any issues.
4. Verify all success criteria from spec pass.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
