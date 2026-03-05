# Implementation Plan: Engineer Endpoints

**Branch**: `013-engineer-endpoints` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-engineer-endpoints/spec.md`

## Summary

Phase 6.4 connects the AI engineer layer (Phase 5) to the FastAPI server via 7 new endpoints. Two slow operations (run engineer, chat response) run as tracked background jobs using the existing JobManager. Four synchronous endpoints serve recommendation data and conversation history. One synchronous endpoint applies setup changes to .ini files. New code lives in `backend/api/engineer/` (pipeline + serializers) and `backend/api/routes/engineer.py` (endpoints), following the same patterns established in Phase 6.3 (analysis endpoints).

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: FastAPI, Pydantic AI, httpx (test client)
**Storage**: SQLite (existing tables: sessions, recommendations, setup_changes, messages)
**Testing**: pytest with httpx AsyncClient, FunctionModel mocks (ALLOW_MODEL_REQUESTS=False)
**Target Platform**: Windows 11 (localhost server)
**Project Type**: Web service (backend API layer)
**Performance Goals**: Engineer job completes in <30s (LLM-bound), sync endpoints <200ms
**Constraints**: No modifications to existing ac_engineer.*, api.jobs, or api.analysis packages
**Scale/Scope**: Single-user localhost app, 7 new endpoints, ~3 new source files, ~3 test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Engineer only runs on analyzed sessions (state guard) |
| II. Car-Agnostic Design | PASS | No car-specific logic — delegates to existing engine |
| III. Setup File Autonomy | PASS | Apply endpoint uses existing backup + validate + write pipeline |
| IV. LLM as Interpreter | PASS | All LLM calls go through Pydantic AI agents; no direct SDK calls |
| V. Educational Explanations | PASS | EngineerResponse already contains reasoning/explanation fields |
| VI. Incremental Changes | PASS | Recommendations persist separately; multiple per session allowed |
| VII. CLI-First MVP | PASS | API endpoints enable both CLI (curl) and future GUI usage |
| VIII. API-First Design | PASS | Routes are thin wrappers delegating to ac_engineer functions |
| IX. Separation of Concerns | PASS | api/ calls ac_engineer/; no business logic in routes |
| X. Desktop App Stack | N/A | Phase 7 — not applicable yet |
| XI. LLM Provider Abstraction | PASS | Uses ACConfig for provider/model; Pydantic AI for all LLM calls |

No violations. Complexity Tracking section not needed.

## Project Structure

### Documentation (this feature)

```text
specs/013-engineer-endpoints/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── endpoints.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
  api/
    engineer/
      __init__.py          # Public imports
      pipeline.py          # run_engineer_pipeline(), run_chat_pipeline()
      serializers.py       # EngineerResponse → API response shapes
    routes/
      engineer.py          # 7 endpoints (engineer router)
    main.py                # Updated: include engineer router, add active_engineer_jobs
  tests/
    api/
      test_engineer_pipeline.py
      test_engineer_serializers.py
      test_engineer_routes.py
```

**Structure Decision**: Follows the same pattern as Phase 6.3 — `api/engineer/` for pipeline + serializers (parallel to `api/analysis/`), `api/routes/engineer.py` for endpoints (parallel to `api/routes/analysis.py`). Router registered in `main.py` with `prefix="/sessions"`.
