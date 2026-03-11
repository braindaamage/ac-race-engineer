# Implementation Plan: Domain-Scoped Setup Context

**Branch**: `030-domain-scoped-setup-context` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/030-domain-scoped-setup-context/spec.md`

## Summary

Filter setup parameters injected into each specialist agent's prompt by domain relevance. Add a `DOMAIN_PARAMS` constant mapping each domain to its setup section prefixes, and modify `_build_user_prompt()` to accept a `domain` parameter that filters `active_setup_parameters` before serialization. No changes outside `backend/ac_engineer/engineer/agents.py` and its tests.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: Pydantic AI (agent framework), no new dependencies
**Storage**: N/A — no storage changes
**Testing**: pytest (backend/tests/engineer/)
**Target Platform**: Windows desktop (backend component)
**Project Type**: Desktop app backend (ac_engineer library)
**Performance Goals**: 60–70% reduction in setup parameter tokens per analysis
**Constraints**: No changes to SessionSummary, summarize_session(), API endpoints, or frontend
**Scale/Scope**: 2 changes in 1 file + new tests in 1 test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | No telemetry or data processing changes |
| II. Car-Agnostic Design | PASS | Section prefix matching is generic; unrecognized sections fall back to balance domain — no car-specific logic |
| III. Setup File Autonomy | PASS | No setup file read/write changes |
| IV. LLM as Interpreter | PASS | Filtering is deterministic Python; LLM still receives pre-computed data |
| V. Educational Explanations | PASS | No change to explanation generation |
| VI. Incremental Changes | PASS | Minimal scope: 1 constant + 1 function signature change |
| VII. Desktop App as Primary Interface | PASS | No frontend or API changes |
| VIII. API-First Design | PASS | Change is in `ac_engineer/` pure Python, not in API layer |
| IX. Separation of Concerns | PASS | Change stays within `ac_engineer/engineer/` |
| X. Desktop App Stack | PASS | No Tauri/React changes |
| XI. LLM Provider Abstraction | PASS | No provider-specific changes |
| XII. Frontend Architecture | PASS | No frontend changes |

No violations. Complexity Tracking section not needed.

## Project Structure

### Documentation (this feature)

```text
specs/030-domain-scoped-setup-context/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    engineer/
      agents.py          # MODIFIED: add DOMAIN_PARAMS, modify _build_user_prompt()
  tests/
    engineer/
      test_agents.py     # MODIFIED: add domain-scoped filtering tests
```

**Structure Decision**: Backend-only change touching a single source file and its corresponding test file. No new files, no new modules.
