# Tasks: Session Discovery (Phase 6.2)

**Input**: Design documents from `/specs/011-session-discovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sessions-api.md

**Tests**: Included — the project requires comprehensive test coverage (530 existing tests across all modules).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install new dependency and create package structure

- [x] T001 Install `watchdog>=4.0` in conda env `ac-race-engineer` and add to `backend/requirements.txt`
- [x] T002 Create `backend/api/watcher/__init__.py` package (empty init)
- [x] T003 Create `backend/tests/api/__init__.py` if not present (empty init for test discovery)

---

## Phase 2: Foundational (Storage Layer Extensions)

**Purpose**: Extend the existing storage layer with new fields and functions. MUST complete before any user story.

- [x] T004 Extend `SessionRecord` model in `backend/ac_engineer/storage/models.py` — add fields: `state` (str, default "discovered"), `session_type` (str | None), `csv_path` (str | None), `meta_path` (str | None). Add `VALID_SESSION_STATES` constant.
- [x] T005 Add `SyncResult` model in `backend/ac_engineer/storage/models.py` — fields: `discovered` (int), `already_known` (int), `incomplete` (int)
- [x] T006 Extend `init_db()` in `backend/ac_engineer/storage/db.py` — add idempotent `ALTER TABLE sessions ADD COLUMN` for state, session_type, csv_path, meta_path (catch OperationalError on duplicate column)
- [x] T007 Extend `save_session()` in `backend/ac_engineer/storage/sessions.py` — include new fields (state, session_type, csv_path, meta_path) in INSERT OR REPLACE statement
- [x] T008 [P] Add `session_exists(db_path, session_id) -> bool` in `backend/ac_engineer/storage/sessions.py`
- [x] T009 [P] Add `delete_session(db_path, session_id) -> bool` in `backend/ac_engineer/storage/sessions.py` — returns True if deleted, False if not found. FK cascade handles related records.
- [x] T010 [P] Add `update_session_state(db_path, session_id, state) -> bool` in `backend/ac_engineer/storage/sessions.py` — validate state is in VALID_SESSION_STATES before updating
- [x] T011 Update `backend/ac_engineer/storage/__init__.py` — export new functions: `session_exists`, `delete_session`, `update_session_state`, `SyncResult`
- [x] T012 Write tests for storage extensions in `backend/tests/storage/test_sessions_extended.py` — test: save with new fields, session_exists (true/false), delete_session (found/not found, cascade), update_session_state (valid/invalid state, not found), migration idempotency, list_sessions returns new fields

**Checkpoint**: Storage layer extended. Run `pytest backend/tests/storage/ -v` — all existing + new tests pass.

---

## Phase 3: User Story 2 — Session List and Detail (Priority: P1)

**Goal**: Expose endpoints to list all sessions and get single session detail. This is implemented before US1 (auto-discovery) because the endpoints are needed to verify that discovery works.

**Independent Test**: Call GET /sessions and GET /sessions/{id} with pre-populated database records and verify correct responses.

### Implementation

- [x] T013 [US2] Create sessions router in `backend/api/routes/sessions.py` — define `router = APIRouter(prefix="/sessions")` with Pydantic response models: `SessionListResponse` (wrapping list of `SessionRecord`), and direct `SessionRecord` for detail
- [x] T014 [US2] Implement `GET /sessions` in `backend/api/routes/sessions.py` — optional `?car=` query param, calls `list_sessions()`, returns `SessionListResponse`
- [x] T015 [US2] Implement `GET /sessions/{session_id}` in `backend/api/routes/sessions.py` — calls `get_session()`, raises HTTPException(404) if not found
- [x] T016 [US2] Register sessions router in `backend/api/main.py` — import and `app.include_router(sessions_router)`
- [x] T017 [US2] Write tests in `backend/tests/api/test_sessions_routes.py` — test: list empty, list with sessions, list filtered by car, get existing session, get nonexistent session (404). Use httpx TestClient with a test database.

**Checkpoint**: `GET /sessions` and `GET /sessions/{id}` work. Run `pytest backend/tests/api/test_sessions_routes.py -v`.

---

## Phase 4: User Story 1 — Automatic Session Appearance (Priority: P1)

**Goal**: File watcher detects new CSV + meta.json pairs and automatically registers them in the database.

**Independent Test**: Create a CSV + meta.json pair in a temp directory while the watcher is running; verify the session appears in the database within 5 seconds.

### Implementation

- [x] T018 [P] [US1] Implement `scan_sessions_dir()` in `backend/api/watcher/scanner.py` — pure function: takes `sessions_dir` (Path) and `db_path` (Path), scans for `.csv` files, checks for matching `.meta.json`, reads metadata (car_name, track_name, session_start, laps_completed, session_type), registers new sessions via `save_session()`, returns `SyncResult`. Handles: missing dir, malformed JSON, orphan files.
- [x] T019 [P] [US1] Write tests for scanner in `backend/tests/api/test_scanner.py` — test: empty dir, valid pair registered, orphan csv skipped, orphan meta skipped, already registered not duplicated, malformed json skipped, missing dir returns empty result, multiple pairs mixed valid/invalid
- [x] T020 [US1] Implement `SessionEventHandler` in `backend/api/watcher/handler.py` — extends `watchdog.FileSystemEventHandler`, tracks file modification timestamps in a dict, implements 2-second debounce. On stabilized pair: calls scanner's registration logic for that single pair.
- [x] T021 [US1] Implement `SessionWatcher` in `backend/api/watcher/observer.py` — wraps `watchdog.Observer`: `start(sessions_dir, db_path)` schedules handler on directory, `stop()` calls `observer.stop()` + `observer.join()`. Handles missing directory gracefully (log warning, schedule on parent or retry).
- [x] T022 [US1] Export public API from `backend/api/watcher/__init__.py` — export `SessionWatcher`, `scan_sessions_dir`
- [x] T023 [US1] Integrate watcher into lifespan in `backend/api/main.py` — in `lifespan()`: resolve sessions dir path, create and start `SessionWatcher`, store on `app.state.session_watcher`. On exit: stop watcher. Run initial `scan_sessions_dir()` on startup to catch sessions missed while server was down.
- [x] T024 [US1] Write tests for watcher handler in `backend/tests/api/test_watcher.py` — test: handler tracks events, debounce prevents premature processing, stabilized pair triggers registration, handler ignores non-csv/meta files

**Checkpoint**: File watcher starts with server, detects new file pairs, registers them. Run `pytest backend/tests/api/ -v`.

---

## Phase 5: User Story 3 — Manual Sync (Priority: P2)

**Goal**: User triggers a manual rescan that discovers unregistered sessions.

**Independent Test**: Place files in sessions dir, call `POST /sessions/sync`, verify new sessions registered and SyncResult returned.

### Implementation

- [x] T025 [US3] Implement `POST /sessions/sync` in `backend/api/routes/sessions.py` — calls `scan_sessions_dir()` with sessions dir from `app.state`, returns `SyncResult` as JSON response
- [x] T026 [US3] Write tests for sync endpoint in `backend/tests/api/test_sessions_routes.py` — test: sync empty dir, sync with new pairs, sync with already-known sessions, sync with orphan files, sync with nonexistent dir

**Checkpoint**: Manual sync works end-to-end. Run `pytest backend/tests/api/test_sessions_routes.py -v`.

---

## Phase 6: User Story 4 — Session Deletion (Priority: P3)

**Goal**: User removes a session from the registry without deleting files from disk.

**Independent Test**: Create a session record, call `DELETE /sessions/{id}`, verify DB record gone, verify files still on disk.

### Implementation

- [x] T027 [US4] Implement `DELETE /sessions/{session_id}` in `backend/api/routes/sessions.py` — calls `delete_session()`, returns 204 on success, raises HTTPException(404) if not found
- [x] T028 [US4] Write tests for delete endpoint in `backend/tests/api/test_sessions_routes.py` — test: delete existing session (204, record gone, files remain), delete nonexistent session (404), delete cascades to related records

**Checkpoint**: Deletion works. Files preserved on disk. Run `pytest backend/tests/api/test_sessions_routes.py -v`.

---

## Phase 7: User Story 5 — File Watcher Lifecycle (Priority: P2)

**Goal**: Watcher starts/stops cleanly with the server lifespan.

**Independent Test**: Start server, verify watcher is active. Stop server, verify no orphaned threads.

### Implementation

- [x] T029 [US5] Write lifecycle tests in `backend/tests/api/test_watcher.py` — test: watcher starts on lifespan enter, watcher stops on lifespan exit, watcher handles missing sessions dir at startup, initial scan runs on startup

**Checkpoint**: Watcher lifecycle is solid. Run full test suite: `pytest backend/tests/ -v`.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T030 Run full test suite (`pytest backend/tests/ -v`) — all 530+ existing tests still pass, all new tests pass
- [x] T031 Validate quickstart.md scenarios manually — server starts, watcher runs, endpoints respond, manual sync works
- [x] T032 Verify existing storage tests in `backend/tests/storage/` pass unchanged (no regressions from schema migration)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US2 - List/Detail)**: Depends on Phase 2 — endpoints needed to verify other stories
- **Phase 4 (US1 - Auto Discovery)**: Depends on Phase 2 — can run in parallel with Phase 3
- **Phase 5 (US3 - Manual Sync)**: Depends on Phase 4 (reuses scanner) and Phase 3 (endpoint patterns)
- **Phase 6 (US4 - Deletion)**: Depends on Phase 2 — can run in parallel with Phases 3-5
- **Phase 7 (US5 - Lifecycle)**: Depends on Phase 4 (watcher exists)
- **Phase 8 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US2 (List/Detail)**: Independent after Phase 2
- **US1 (Auto Discovery)**: Independent after Phase 2. Scanner function is shared with US3.
- **US3 (Manual Sync)**: Depends on US1's `scan_sessions_dir()` function
- **US4 (Deletion)**: Independent after Phase 2
- **US5 (Lifecycle)**: Depends on US1's watcher implementation

### Parallel Opportunities

Within Phase 2:
- T008, T009, T010 can run in parallel (independent functions)

Within Phase 4:
- T018 and T019 can run in parallel (scanner impl + tests are in different files)

Across phases:
- Phase 3 (US2) and Phase 4 (US1) can start simultaneously after Phase 2
- Phase 6 (US4) can start any time after Phase 2

---

## Parallel Example: Phase 2 (Foundational)

```text
# Sequential first (model changes before function changes):
T004 → T005 → T006 → T007

# Then parallel (independent new functions):
T008 (session_exists) || T009 (delete_session) || T010 (update_session_state)

# Then sequential (depends on above):
T011 → T012
```

## Parallel Example: Phase 3 + Phase 4 (after Phase 2)

```text
# These two phases can start simultaneously:
Phase 3: T013 → T014 → T015 → T016 → T017
Phase 4: T018 || T019 → T020 → T021 → T022 → T023 → T024
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational storage extensions
3. Complete Phase 3: Session List/Detail endpoints (US2)
4. Complete Phase 4: Auto Discovery with file watcher (US1)
5. **STOP and VALIDATE**: Server starts, watcher detects files, sessions appear in list
6. This is the MVP — the core loop works

### Incremental Delivery

1. Setup + Foundational → Storage ready
2. Add US2 (List/Detail) → Endpoints work with manual DB entries
3. Add US1 (Auto Discovery) → Full automatic flow works (MVP!)
4. Add US3 (Manual Sync) → Safety net for missed sessions
5. Add US4 (Deletion) → User can manage their list
6. Add US5 (Lifecycle) → Clean server start/stop
7. Polish → All tests pass, no regressions

---

## Notes

- All file watcher tests use `tmp_path` — never touch real sessions directory
- Endpoint tests use httpx `TestClient` with in-memory test databases
- The scanner (`scan_sessions_dir()`) is a pure function with no HTTP coupling — testable independently
- Schema migration is idempotent — safe to run `init_db()` multiple times
- Existing 530 tests must continue to pass (no regressions)
