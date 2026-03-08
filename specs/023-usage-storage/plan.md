# Implementation Plan: Usage Storage

**Branch**: `023-usage-storage` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-usage-storage/spec.md`

## Summary

Add two new SQLite tables (`agent_usage` and `tool_call_details`) to the existing database to persist LLM agent token consumption per specialist execution. New Pydantic v2 models and pure-function CRUD operations follow the established `storage/` patterns. Backend-only, no API endpoints or frontend changes.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: Pydantic v2 (models), stdlib sqlite3 (persistence), pytest (testing)
**Storage**: SQLite via stdlib sqlite3, existing database at `data/ac_engineer.db`
**Testing**: pytest with `tmp_path` fixtures, existing `conftest.py` with `db_path` fixture
**Target Platform**: Windows (desktop app backend)
**Project Type**: Desktop app backend library (`backend/ac_engineer/`)
**Performance Goals**: N/A — write-once storage for small volumes (4 records per recommendation at most)
**Constraints**: Migration must be idempotent; records are immutable; no external dependencies beyond existing stack
**Scale/Scope**: ~4 usage records per engineer session, each with 0-20 tool call details

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Immutable records, FK constraints, CHECK constraints, transactional writes |
| II. Car-Agnostic Design | PASS | No car-specific logic; domain tracks agent type, not car |
| III. Setup File Autonomy | N/A | No setup file interaction |
| IV. LLM as Interpreter | PASS | Storage only — no LLM calls |
| V. Educational Explanations | N/A | No user-facing explanations |
| VI. Incremental Changes | PASS | Small, additive change to existing module |
| VII. Desktop App as Primary Interface | N/A | No UI changes |
| VIII. API-First Design | PASS | Pure functions in `ac_engineer/storage/`, no HTTP code |
| IX. Separation of Concerns | PASS | Changes only in `ac_engineer/storage/` layer |
| X. Desktop App Stack | N/A | No Tauri/React changes |
| XI. LLM Provider Abstraction | N/A | No LLM interactions |
| XII. Frontend Architecture | N/A | No frontend changes |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/023-usage-storage/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    storage/
      models.py          # MODIFY — add AgentUsage, ToolCallDetail models
      db.py              # MODIFY — add 2 CREATE TABLE IF NOT EXISTS to _MIGRATIONS
      usage.py           # CREATE — save_agent_usage, get_agent_usage functions
      __init__.py        # MODIFY — export new models and functions
  tests/
    storage/
      test_usage.py      # CREATE — tests for usage CRUD + migration
```

**Structure Decision**: All changes within the existing `backend/ac_engineer/storage/` package and its corresponding test directory. One new source file (`usage.py`) and one new test file (`test_usage.py`). Three existing files modified (`models.py`, `db.py`, `__init__.py`).
