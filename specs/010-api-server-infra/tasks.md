# Tasks: API Server Infrastructure

**Input**: Design documents from `/specs/010-api-server-infra/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — spec SC-006 requires automated tests for all infrastructure components.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project directory structure and install dependencies

- [ ] T001 Create the `backend/api/` package directory structure with all `__init__.py` files per plan.md: `api/`, `api/jobs/`, `api/routes/`, `api/ws/`, `api/errors/`, and `backend/tests/api/`
- [ ] T002 Install FastAPI and httpx into the conda env `ac-race-engineer` (`pip install fastapi httpx`); uvicorn 0.41.0 is already present
- [ ] T003 Create `backend/api/__init__.py` with `__version__ = "0.1.0"` constant (used by health endpoint)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic models and app factory that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement job models in `backend/api/jobs/models.py`: `JobStatus` enum (pending, running, completed, failed), `Job` model (job_id, job_type, status, progress, current_step, result, error, created_at), `JobEvent` model (event, job_id, status, progress, current_step, result, error) per data-model.md
- [ ] T005 [P] Implement error response model in `backend/api/errors/models.py`: `ErrorDetail` model (type, message, detail) and `ErrorResponse` model (error: ErrorDetail) per contracts/http-endpoints.md error envelope format
- [ ] T006 [P] Implement `HealthResponse` model (status, version) in `backend/api/routes/health.py` (colocated with the route, per data-model.md)
- [ ] T007 Implement FastAPI app factory in `backend/api/main.py`: `create_app()` function using `@asynccontextmanager` lifespan pattern (research R1), initializes `JobManager` on `app.state` during startup (research R2), cancels all jobs on shutdown (research R6); include `get_job_manager(request)` dependency function
- [ ] T008 Create shared test fixtures in `backend/tests/api/conftest.py`: `app` fixture calling `create_app()`, `client` fixture using httpx `AsyncClient` with `ASGITransport`, `manager` fixture returning `app.state.job_manager`

**Checkpoint**: Foundation ready — app factory creates a working FastAPI app with lifespan and injectable job manager

---

## Phase 3: User Story 1 - Desktop App Launches the Server (Priority: P1) MVP

**Goal**: Server starts, health check responds with status and version, configurable port via --port flag and PORT env var

**Independent Test**: Start the server process and verify GET /health returns `{"status": "ok", "version": "0.1.0"}`

### Tests for User Story 1

- [ ] T009 [P] [US1] Write health endpoint tests in `backend/tests/api/test_health.py`: test GET /health returns 200 with status "ok" and version matching `api.__version__`, test response content type is JSON

### Implementation for User Story 1

- [ ] T010 [US1] Implement GET /health route in `backend/api/routes/health.py`: returns `HealthResponse(status="ok", version=api.__version__)` per contracts/http-endpoints.md; register router in `create_app()` in `backend/api/main.py`
- [ ] T011 [US1] Implement server entry point in `backend/api/server.py`: argparse with `--port` flag (default from `PORT` env var or 57832), call `uvicorn.run()` with host `127.0.0.1` per research R5; make it runnable via `python -m api.server` by adding `backend/api/__main__.py` that imports and calls `server.main()`

**Checkpoint**: `python -m api.server` starts the server; `curl http://localhost:57832/health` returns version — US1 is independently testable

---

## Phase 4: User Story 2 - Desktop App Tracks a Long-Running Job (Priority: P1)

**Goal**: Job manager creates and tracks background jobs; WebSocket streams real-time progress events; GET /jobs/{job_id} returns current state; reconnection works for completed jobs

**Independent Test**: Create a mock job via the manager, connect to WS /ws/jobs/{job_id}, receive progress/completed events in order; verify GET /jobs/{job_id} returns job state

### Tests for User Story 2

- [ ] T012 [P] [US2] Write JobManager unit tests in `backend/tests/api/test_jobs_manager.py`: test create_job returns Job with pending status and UUID4 id; test update_progress changes progress/step/status; test complete_job sets result and status=completed; test fail_job sets error and status=failed; test get_job returns None for unknown id; test cancel_all cancels running tasks; test asyncio.Event is set on state changes
- [ ] T013 [P] [US2] Write worker tests in `backend/tests/api/test_jobs_worker.py`: test run_job with a successful mock callable that reports 3 progress steps → job ends completed with result; test run_job with a failing mock callable → job ends failed with error message; test cancellation mid-job → job ends failed
- [ ] T014 [P] [US2] Write GET /jobs/{job_id} tests in `backend/tests/api/test_jobs_api.py`: test 200 response matches Job model for existing job; test 404 with error envelope for unknown job_id
- [ ] T015 [P] [US2] Write WebSocket tests in `backend/tests/api/test_ws_jobs.py`: test connect to running job receives progress events then completed event then connection closes with 1000; test connect to failed job receives error event then closes; test connect to already-completed job receives completed event immediately; test connect with unknown job_id closes with 4004; test multiple clients on same job both receive events

### Implementation for User Story 2

- [ ] T016 [US2] Implement `JobManager` in `backend/api/jobs/manager.py`: dict-based job store keyed by job_id; `create_job(job_type) → Job`; `get_job(job_id) → Job | None`; `update_progress(job_id, progress, current_step)`; `complete_job(job_id, result)`; `fail_job(job_id, error)`; `cancel_all()`; maintain `asyncio.Event` per job_id, set on every state change (research R3)
- [ ] T017 [US2] Implement `run_job()` in `backend/api/jobs/worker.py`: accepts async callable with progress callback signature `async def fn(update: Callable[[int, str], Awaitable[None]]) → Any`; creates asyncio task, transitions job pending→running, calls callable, transitions to completed with result or failed with error on exception; handles CancelledError
- [ ] T018 [US2] Implement GET /jobs/{job_id} route in `backend/api/routes/jobs.py`: inject `JobManager` via `Depends(get_job_manager)`; return Job model on success; raise HTTPException(404) if job not found; register router in `create_app()`
- [ ] T019 [US2] Implement WebSocket handler in `backend/api/ws/jobs.py`: accept connection at `/ws/jobs/{job_id}`; if job not found close with code 4004 and reason "Job not found"; loop: await `asyncio.Event` with timeout, send `JobEvent` JSON on state change; on terminal state (completed/failed) send final event and close with 1000; handle client disconnect gracefully; register WebSocket route in `create_app()`
- [ ] T020 [US2] Export public API from `backend/api/jobs/__init__.py`: export `JobManager`, `Job`, `JobStatus`, `JobEvent`, `run_job`

**Checkpoint**: Full job lifecycle works — create job, track via WS, get via HTTP, reconnect to finished job — US2 is independently testable

---

## Phase 5: User Story 3 - Desktop App Handles Server Errors Gracefully (Priority: P2)

**Goal**: All API errors return uniform `{"error": {"type", "message", "detail"}}` envelope; covers 404, 422, and 500

**Independent Test**: Send requests to non-existent endpoints, malformed requests, and trigger internal errors — all return the same error envelope format

### Tests for User Story 3

- [ ] T021 [P] [US3] Write error handling tests in `backend/tests/api/test_errors.py`: test 404 for unknown route returns error envelope with type "not_found"; test 422 for validation error returns envelope with type "validation_error" and field details; test 500 for unhandled exception returns envelope with type "internal_error" and no stack trace

### Implementation for User Story 3

- [ ] T022 [US3] Implement global exception handlers in `backend/api/errors/handlers.py`: handler for `HTTPException` → maps status to error type (404→"not_found", etc.); handler for `RequestValidationError` → type "validation_error" with field errors in detail; catch-all `Exception` handler → type "internal_error" with generic message (no stack trace); register all handlers in `create_app()` in `backend/api/main.py`
- [ ] T023 [US3] Export public API from `backend/api/errors/__init__.py`: export `ErrorResponse`, `ErrorDetail`, `register_error_handlers` (or equivalent)

**Checkpoint**: Every error path returns uniform JSON envelope — US3 is independently testable

---

## Phase 6: User Story 4 - Desktop App Connects from a Different Port (Priority: P2)

**Goal**: CORS configured for any localhost origin so React dev server on a different port can make API calls

**Independent Test**: Make a cross-origin request with Origin header set to `http://localhost:3000` and verify CORS headers in response

### Tests for User Story 4

- [ ] T024 [P] [US4] Write CORS tests in `backend/tests/api/test_cors.py`: test preflight OPTIONS request from `http://localhost:3000` returns Access-Control-Allow-Origin; test actual request from localhost origin includes CORS headers; test request from non-localhost origin does NOT get CORS headers

### Implementation for User Story 4

- [ ] T025 [US4] Add CORS middleware in `create_app()` in `backend/api/main.py`: use `CORSMiddleware` with `allow_origin_regex=r"^https?://localhost(:\d+)?$"`, allow all methods, allow common headers (Content-Type, Authorization) per research R4

**Checkpoint**: Cross-origin requests from any localhost port succeed — US4 is independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, graceful shutdown, and full suite confirmation

- [ ] T026 Verify graceful shutdown: add test in `backend/tests/api/test_shutdown.py` that creates a running job, triggers app shutdown via lifespan exit, and confirms jobs are cancelled and no tasks leak (SC-005)
- [ ] T027 Run the full test suite (`pytest backend/tests/api/ -v`) and confirm all tests pass; verify no import errors, no warnings about deprecated APIs
- [ ] T028 Validate quickstart.md: manually verify the server starts with `python -m api.server`, health check responds, and tests run as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2; no dependency on other stories
- **US2 (Phase 4)**: Depends on Phase 2; no dependency on US1 (job system is independent of health endpoint)
- **US3 (Phase 5)**: Depends on Phase 2; benefits from US1 routes existing for testing but not strictly required
- **US4 (Phase 6)**: Depends on Phase 2; benefits from US1 routes existing for CORS header verification
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent — only needs foundational app factory
- **US2 (P1)**: Independent — only needs foundational app factory and job models
- **US3 (P2)**: Independent — registers global handlers on app; having routes from US1/US2 makes testing richer but handlers work regardless
- **US4 (P2)**: Independent — CORS middleware is registered on app; having any route makes testing easier

### Within Each User Story

- Tests written first (TDD) — verify they fail before implementation
- Models/infrastructure before routes
- Routes before integration
- Story complete and checkpoint verified before moving on

### Parallel Opportunities

- T004, T005, T006 can run in parallel (different files, independent models)
- T009 can run in parallel with T012-T015 (different test files)
- US1 and US2 can run in parallel after Phase 2 (independent stories)
- US3 and US4 can run in parallel after Phase 2 (independent middleware)
- All test tasks within a phase marked [P] can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all model tasks together (different files):
Task T004: "Implement job models in backend/api/jobs/models.py"
Task T005: "Implement error response model in backend/api/errors/models.py"
Task T006: "Implement HealthResponse model in backend/api/routes/health.py"
```

## Parallel Example: User Story 2 Tests

```bash
# Launch all US2 test tasks together (different test files):
Task T012: "Write JobManager unit tests in backend/tests/api/test_jobs_manager.py"
Task T013: "Write worker tests in backend/tests/api/test_jobs_worker.py"
Task T014: "Write GET /jobs/{job_id} tests in backend/tests/api/test_jobs_api.py"
Task T015: "Write WebSocket tests in backend/tests/api/test_ws_jobs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: User Story 1 (T009-T011)
4. **STOP and VALIDATE**: `python -m api.server` starts, GET /health returns version
5. Server is usable — Tauri can launch it and confirm connectivity

### Incremental Delivery

1. Setup + Foundational → App factory exists, can create test clients
2. Add US1 → Health check works → Server is launchable (MVP!)
3. Add US2 → Job system works → Background operations trackable
4. Add US3 → Error handling uniform → All errors have consistent format
5. Add US4 → CORS works → Frontend dev server can make API calls
6. Polish → Shutdown clean, full suite green, quickstart validated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD approach for US test tasks)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total: 28 tasks across 7 phases
