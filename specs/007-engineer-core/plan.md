# Implementation Plan: Engineer Core (Deterministic Layer)

**Branch**: `007-engineer-core` | **Date**: 2026-03-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-engineer-core/spec.md`

## Summary

Build the deterministic core layer for Phase 5.2: a session summarizer that compresses AnalyzedSession into a token-efficient SessionSummary, a setup parameter reader that discovers min/max/step ranges from AC car data files, a setup change validator that checks proposed values against those ranges, and a safe setup file writer with atomic writes and timestamped backups. All pure Python 3.11+ with Pydantic v2, no new external dependencies, no LLM involvement.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: Pydantic v2 (already installed), stdlib only (configparser, pathlib, os, shutil, datetime, copy, logging)
**Storage**: N/A (this phase is pure computation + file I/O; no database)
**Testing**: pytest with tmp_path fixtures
**Target Platform**: Windows 11 (primary), cross-platform compatible
**Project Type**: Library (Python package under `backend/ac_engineer/engineer/`)
**Performance Goals**: Summarizer < 100ms for a 20-lap session
**Constraints**: No new pip/conda dependencies; all code deterministic; no LLM calls
**Scale/Scope**: ~4 modules, ~12 Pydantic models, ~54 tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Summarizer receives already-validated AnalyzedSession; validator checks ranges before writes |
| II. Car-Agnostic Design | PASS | Parameter reader is fully generic; no hardcoded car names or parameter names |
| III. Setup File Autonomy | PASS | Writer validates against car data ranges, preserves unknown params, creates backups, writes atomically |
| IV. LLM as Interpreter, Not Calculator | PASS | This entire phase is deterministic Python — no LLM involvement |
| V. Educational Explanations | PASS | SetupChange model has reasoning + expected_effect fields; EngineerResponse has full explanation |
| VI. Incremental Changes | N/A | Change recommendation logic is Phase 5.3 (AI agents) |
| VII. CLI-First MVP | PASS | All functions are pure Python callable from CLI/tests/API |
| VIII. API-First Design | PASS | All code lives in `ac_engineer/engineer/`, no HTTP imports |
| IX. Separation of Concerns | PASS | Pure computation layer, no HTTP or frontend concerns |
| X. Desktop App Stack | N/A | Phase 7 |
| XI. LLM Provider Abstraction | N/A | No LLM calls in this phase |
| Dev Environment | PASS | Uses conda env `ac-race-engineer` |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-engineer-core/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── public-api.md   # Public function signatures
├── checklists/
│   └── requirements.md # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    engineer/
      __init__.py          # Public exports
      models.py            # All Pydantic v2 models (12 models)
      summarizer.py        # summarize_session()
      setup_reader.py      # read_parameter_ranges(), get_parameter_range()
      setup_writer.py      # validate_changes(), apply_changes(), create_backup()
  tests/
    engineer/
      __init__.py
      conftest.py          # Shared fixtures (sample sessions, setup files, car data)
      test_models.py       # ~12 tests
      test_summarizer.py   # ~18 tests
      test_setup_reader.py # ~10 tests
      test_setup_writer.py # ~14 tests
```

**Structure Decision**: Follows the established `backend/ac_engineer/<module>/` pattern used by parser, analyzer, knowledge, config, and storage modules. Tests mirror at `backend/tests/<module>/`.

## Post-Design Constitution Re-Check

*Re-evaluated after Phase 1 design artifacts (data-model.md, contracts/, research.md).*

| Principle | Status | Post-Design Notes |
|-----------|--------|-------------------|
| I. Data Integrity First | PASS | Summarizer only reads validated AnalyzedSession. Validator enforces min/max before writes. Writer creates backup. |
| II. Car-Agnostic Design | PASS | `read_parameter_ranges()` parses whatever sections exist in `data/setup.ini` — no hardcoded names. ParameterRange model is generic. |
| III. Setup File Autonomy | PASS | `apply_changes()` preserves all untouched sections/params. Atomic write via `.tmp` + `os.replace()`. Timestamped backups per R5. `show_clicks` flag handled per R3. |
| IV. LLM as Interpreter, Not Calculator | PASS | Zero LLM calls. All computation is deterministic Python. SetupChange/EngineerResponse models are data containers for Phase 5.3. |
| V. Educational Explanations | PASS | SetupChange includes `reasoning` and `expected_effect` fields. DriverFeedback includes `observation` and `suggestion`. |
| VIII. API-First Design | PASS | All functions in `ac_engineer/engineer/` — no HTTP imports, no web framework dependencies. |
| IX. Separation of Concerns | PASS | Pure computation + file I/O only. No cross-layer imports. |

**Post-design gate result**: PASS — no violations. Design is constitution-compliant.

## Complexity Tracking

> No constitution violations — this section is empty.
