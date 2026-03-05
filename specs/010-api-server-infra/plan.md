# Implementation Plan: API Server Infrastructure

**Branch**: `010-api-server-infra` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-api-server-infra/spec.md`

## Summary

Build the foundational HTTP server with WebSocket support for AC Race Engineer Phase 6. The server provides a health check endpoint, an in-memory job manager for tracking long-running background operations, WebSocket-based real-time progress streaming, and uniform error handling. Built with FastAPI + Uvicorn, it establishes the infrastructure patterns that sub-phases 6.2-6.5 will build on to expose parser, analyzer, and engineer functionality as API endpoints.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: FastAPI, Uvicorn (already installed), httpx (test only)
**Storage**: N/A — in-memory job store only, no database
**Testing**: pytest with httpx AsyncClient and starlette TestClient for WebSocket
**Target Platform**: Windows 11 (localhost desktop app backend)
**Project Type**: Web service (backend API for desktop app)
**Performance Goals**: Health check responds within 3 seconds of process start; clean shutdown within 5 seconds
**Constraints**: Single-process, localhost-only; no external dependencies beyond LLM providers (not used in this phase)
**Scale/Scope**: Single user, ~10 concurrent jobs max; in-memory state only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | No telemetry processing in this phase |
| II. Car-Agnostic Design | N/A | No car-specific logic in this phase |
| III. Setup File Autonomy | N/A | No setup file operations in this phase |
| IV. LLM as Interpreter | N/A | No LLM calls in this phase |
| V. Educational Explanations | N/A | No user-facing explanations in this phase |
| VI. Incremental Changes | N/A | No setup changes in this phase |
| VII. CLI-First MVP | PASS | Server is a CLI-invocable process (`python -m api.server`) |
| VIII. API-First Design | PASS | `api/` routes will be thin wrappers; job manager is pure Python with no HTTP awareness |
| IX. Separation of Concerns | PASS | New `api/` layer does not import from `ac_engineer/` yet; when it does (6.2+), imports will flow `api/` → `ac_engineer/` only |
| X. Desktop App Stack | PASS | Server designed to be started as subprocess by Tauri; CORS configured for localhost React dev server |
| XI. LLM Provider Abstraction | N/A | No LLM calls in this phase |

**Pre-design gate**: PASS — no violations.
**Post-design gate**: PASS — design maintains separation of concerns. `api/` package is independent of `ac_engineer/`. Job manager is a pure Python class with no framework coupling.

## Project Structure

### Documentation (this feature)

```text
specs/010-api-server-infra/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: setup and run instructions
├── contracts/
│   ├── http-endpoints.md    # HTTP API contracts
│   └── websocket-protocol.md # WebSocket message protocol
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
  api/
    __init__.py              # Package marker with version constant
    main.py                  # FastAPI app factory + lifespan (startup/shutdown)
    server.py                # CLI entry point: argparse --port, starts uvicorn
    jobs/
      __init__.py
      manager.py             # JobManager: create, update_progress, complete, fail, get, cancel_all
      models.py              # JobStatus enum, Job model, JobEvent model
      worker.py              # run_job(): wraps async callable as tracked job
    routes/
      __init__.py
      health.py              # GET /health → HealthResponse
      jobs.py                # GET /jobs/{job_id} → Job
    ws/
      __init__.py
      jobs.py                # WebSocket /ws/jobs/{job_id} → streams JobEvent
    errors/
      __init__.py
      handlers.py            # Exception handlers for HTTPException, ValidationError, Exception
      models.py              # ErrorResponse Pydantic model
  tests/
    api/
      __init__.py
      conftest.py            # Shared fixtures: app, client, manager
      test_health.py         # Health endpoint tests
      test_jobs_manager.py   # JobManager unit tests
      test_jobs_worker.py    # Worker lifecycle tests
      test_jobs_api.py       # GET /jobs/{job_id} tests
      test_ws_jobs.py        # WebSocket integration tests
      test_errors.py         # Error handler tests
```

**Structure Decision**: Follows the existing project convention where `backend/` contains all Python code. The new `api/` package sits alongside `ac_engineer/` under `backend/`. Tests follow the existing pattern in `backend/tests/` with a new `api/` subdirectory. This matches the constitution's three-layer architecture (Principle IX).

## Complexity Tracking

No violations to justify — all constitution gates pass without exceptions.
