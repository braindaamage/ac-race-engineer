# Implementation Plan: Config, Knowledge & Packaging Endpoints

**Branch**: `014-config-knowledge-endpoints` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-config-knowledge-endpoints/spec.md`

## Summary

Expose user configuration (GET/PATCH/validate) and knowledge base (search, session fragments) as API endpoints, centralize path resolution for standalone packaging via PyInstaller.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: FastAPI, Pydantic v2, uvicorn (all already installed)
**Storage**: JSON config file (`data/config.json`), knowledge base markdown docs (read-only)
**Testing**: pytest + httpx AsyncClient (existing pattern)
**Target Platform**: Windows (Tauri sidecar), localhost HTTP
**Project Type**: Web service (backend API)
**Performance Goals**: All endpoints respond in < 1s, knowledge search < 500ms
**Constraints**: No new dependencies; thin route files only; no modifications to `ac_engineer.*` packages
**Scale/Scope**: 5 new endpoints, 1 utility module, ~30 tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Config endpoints validate before persisting; knowledge is read-only |
| II. Car-Agnostic Design | PASS | No car-specific logic introduced |
| III. Setup File Autonomy | N/A | No setup file modifications in this phase |
| IV. LLM as Interpreter | N/A | No LLM calls in these endpoints |
| V. Educational Explanations | PASS | Knowledge search enables users to learn vehicle dynamics concepts |
| VI. Incremental Changes | N/A | No setup changes |
| VII. CLI-First MVP | PASS | API endpoints are the CLI-equivalent for Phase 6; backend remains fully usable |
| VIII. API-First Design | PASS | Routes are thin wrappers delegating to `ac_engineer.config` and `ac_engineer.knowledge` |
| IX. Separation of Concerns | PASS | No business logic in routes; `ac_engineer/` untouched; response models in route files |
| X. Desktop App Stack | PASS | Packaging prep supports Tauri sidecar pattern from this principle |
| XI. LLM Provider Abstraction | N/A | No LLM interaction in these endpoints |

All gates pass. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/014-config-knowledge-endpoints/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  api/
    paths.py                        # NEW — centralized path resolution (dev vs frozen)
    main.py                         # MODIFIED — use paths.py, register new routers
    routes/
      config.py                     # NEW — GET /config, PATCH /config, GET /config/validate
      knowledge.py                  # NEW — GET /knowledge/search, GET /sessions/{id}/knowledge
  tests/
    api/
      test_config_routes.py         # NEW — config endpoint tests
      test_knowledge_routes.py      # NEW — knowledge endpoint tests
      test_paths.py                 # NEW — path resolution tests (dev + frozen mock)
build/
  ac_engineer.spec                  # NEW — PyInstaller spec file
  README_build.md                   # NEW — Build documentation
```

**Structure Decision**: Follows existing pattern — new route files in `backend/api/routes/`, response models defined inline in route files (matching `analysis.py` and `engineer.py` patterns from Phases 6.3-6.4). One new utility module (`paths.py`) at the `api/` package level for cross-cutting path resolution.
