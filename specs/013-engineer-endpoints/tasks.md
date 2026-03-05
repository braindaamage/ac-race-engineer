# Tasks: Engineer Endpoints

**Input**: Design documents from `/specs/013-engineer-endpoints/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/endpoints.md, quickstart.md

**Tests**: Included — project has 530+ existing tests with established patterns (httpx AsyncClient, FunctionModel mocks, tmp_path fixtures).

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the `api/engineer/` package directory and skeleton files

- [ ] T001 Create `backend/api/engineer/` package with empty `__init__.py`
- [ ] T002 Create empty `backend/api/routes/engineer.py` with APIRouter scaffold (router = APIRouter(), no endpoints yet)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models and infrastructure that ALL user stories depend on

- [ ] T003 Define all API response models in `backend/api/engineer/serializers.py`: EngineerJobResponse, RecommendationSummary, RecommendationListResponse, SetupChangeDetail, DriverFeedbackDetail, RecommendationDetailResponse, ApplyRequest, ApplyResponse, ChatRequest, ChatJobResponse, MessageResponse, MessageListResponse, ClearMessagesResponse — per data-model.md
- [ ] T004 Implement recommendation cache helpers in `backend/api/engineer/cache.py`: `save_engineer_response(cache_dir, recommendation_id, response)` saves EngineerResponse as `{cache_dir}/recommendation_{rec_id}.json`, `load_engineer_response(cache_dir, recommendation_id)` loads it back (returns None if file missing) — per research.md R6
- [ ] T005 Update `backend/api/main.py`: add `app.state.active_engineer_jobs: dict[str, str] = {}` in lifespan startup, import and include engineer router with `prefix="/sessions"` — per research.md R4
- [ ] T006 Add shared guard helper `_require_analyzed_session()` in `backend/api/routes/engineer.py` that checks session exists (404) and state is "analyzed" or "engineered" (409) — reuse pattern from `api/routes/analysis.py:_get_analyzed_session()`
- [ ] T007 [P] Write serializer unit tests in `backend/tests/api/test_engineer_serializers.py`: verify all response models instantiate correctly with sample data, validate field types and defaults
- [ ] T008 [P] Write cache helper tests in `backend/tests/api/test_engineer_cache.py`: test save/load round-trip, test load returns None when file missing, test corrupted JSON handling

**Checkpoint**: Foundation ready — all response models defined, cache helpers working, main.py wired up. User story implementation can begin.

---

## Phase 3: User Story 1 - Run the AI Engineer (Priority: P1)

**Goal**: User triggers AI engineer on an analyzed session; a background job runs the full pipeline (load analysis, summarize, run specialists, persist recommendation, advance state to "engineered") with real-time progress updates.

**Independent Test**: Trigger POST /sessions/{id}/engineer on an analyzed session, verify job creates recommendation in DB, session state advances to "engineered", and progress updates are emitted.

### Tests for User Story 1

- [ ] T009 [P] [US1] Write pipeline tests in `backend/tests/api/test_engineer_pipeline.py`: test `make_engineer_job()` — mock `analyze_with_engineer()` to return a fake EngineerResponse, verify progress callback called with >=5 steps, verify session state updated to "engineered", verify EngineerResponse cached to disk, verify active_engineer_jobs cleaned up in finally block
- [ ] T010 [P] [US1] Write route tests for POST /engineer in `backend/tests/api/test_engineer_routes.py`: test 202 on analyzed session (job created), test 404 on nonexistent session, test 409 on discovered/parsed session, test 409 when engineer job already running, test re-run on engineered session creates new recommendation

### Implementation for User Story 1

- [ ] T011 [US1] Implement `make_engineer_job()` in `backend/api/engineer/pipeline.py`: factory function returning async callable per run_job() pattern — load AnalyzedSession via `load_analyzed_session(cache_dir)`, call `summarize_session()`, call `analyze_with_engineer(summary, config, db_path)`, save EngineerResponse to cache via `save_engineer_response()`, update session state to "engineered" via `update_session_state()`, emit progress steps (loading analysis 0-15, summarizing 15-30, running engineer 30-85, saving results 85-95, updating state 95-100), clean up active_engineer_jobs in finally block
- [ ] T012 [US1] Implement POST `/{session_id}/engineer` endpoint in `backend/api/routes/engineer.py`: call `_require_analyzed_session()`, check `active_engineer_jobs` for 409 conflict, read ACConfig via `read_config()`, create job via JobManager, register in active_engineer_jobs, launch via `run_job()`, return 202 EngineerJobResponse

**Checkpoint**: User Story 1 complete — triggering the engineer creates a recommendation and advances session state.

---

## Phase 4: User Story 2 - View Recommendations (Priority: P2)

**Goal**: User lists all recommendations for a session and drills into any recommendation to see full detail (setup changes, driver feedback, explanation).

**Independent Test**: After running the engineer, GET /recommendations returns the list; GET /recommendations/{rec_id} returns full detail including driver feedback and explanation from the cached EngineerResponse JSON.

### Tests for User Story 2

- [ ] T013 [P] [US2] Write route tests for GET /recommendations and GET /recommendations/{rec_id} in `backend/tests/api/test_engineer_routes.py`: test list returns recommendations ordered by created_at, test list returns empty array when no recommendations, test 404 on nonexistent session, test detail returns full fields (setup_changes, driver_feedback, explanation) when cache file exists, test detail falls back to SQLite-only data when cache file missing, test 404 on nonexistent recommendation_id

### Implementation for User Story 2

- [ ] T014 [US2] Implement GET `/{session_id}/recommendations` endpoint in `backend/api/routes/engineer.py`: verify session exists (404), call `get_recommendations(db_path, session_id)`, map to RecommendationListResponse with RecommendationSummary items (include change_count from len(changes))
- [ ] T015 [US2] Implement GET `/{session_id}/recommendations/{recommendation_id}` endpoint in `backend/api/routes/engineer.py`: verify session exists (404), call `get_recommendations(db_path, session_id)`, find matching rec (404 if not found), attempt `load_engineer_response(cache_dir, recommendation_id)` for full detail (driver_feedback, explanation, confidence, signals_addressed), fall back to SQLite-only data with empty driver_feedback if cache missing, return RecommendationDetailResponse

**Checkpoint**: User Story 2 complete — recommendations are viewable with full detail.

---

## Phase 5: User Story 3 - Apply a Recommendation (Priority: P3)

**Goal**: User applies a recommendation to a .ini setup file with automatic backup. Recommendation status advances to "applied".

**Independent Test**: POST /recommendations/{rec_id}/apply with a valid setup_path creates a backup, modifies the .ini file, and updates recommendation status to "applied".

### Tests for User Story 3

- [ ] T016 [P] [US3] Write route tests for POST /apply in `backend/tests/api/test_engineer_routes.py`: test successful apply (backup created, status changed to "applied", changes_applied count), test 409 on already-applied recommendation, test 404 on nonexistent recommendation, test 400 on nonexistent setup_path, use tmp_path with a real .ini fixture file

### Implementation for User Story 3

- [ ] T017 [US3] Implement POST `/{session_id}/recommendations/{recommendation_id}/apply` endpoint in `backend/api/routes/engineer.py`: verify session exists (404), find recommendation in DB (404 if not found), check status != "applied" (409), validate setup_path from ApplyRequest body exists (400), call `apply_recommendation(recommendation_id, setup_path, db_path, ac_install_path, car_name)` — get car_name from session record and ac_install_path from ACConfig, return ApplyResponse with backup_path and changes_applied count

**Checkpoint**: User Story 3 complete — recommendations can be applied to .ini files with automatic backup.

---

## Phase 6: User Story 4 - Chat with the Engineer (Priority: P4)

**Goal**: User has a back-and-forth conversation with the AI race engineer about a session, with conversation history maintained in SQLite. AI responses are generated via a background job.

**Independent Test**: POST /messages saves user message and triggers AI response job; GET /messages returns chronological history; DELETE /messages clears the session's chat.

### Tests for User Story 4

- [ ] T018 [P] [US4] Write chat pipeline tests in `backend/tests/api/test_engineer_pipeline.py`: test `make_chat_job()` — mock Pydantic AI agent to return a fixed response, verify user message already saved before job starts, verify assistant message saved after job completes, verify conversation history passed to agent, verify active cleanup not needed (no per-session exclusion for chat)
- [ ] T019 [P] [US4] Write route tests for GET/POST/DELETE /messages in `backend/tests/api/test_engineer_routes.py`: test POST returns 202 with job_id and message_id, test GET returns messages in chronological order, test DELETE clears messages and returns deleted_count, test 404 on nonexistent session, test 409 on non-analyzed session for POST, test GET on session with no messages returns empty list

### Implementation for User Story 4

- [ ] T020 [US4] Implement `make_chat_job()` in `backend/api/engineer/pipeline.py`: factory function — load AnalyzedSession, summarize to SessionSummary, load conversation history via `get_messages()`, build system prompt from `skills/principal.md` + formatted SessionSummary, build Pydantic AI agent with `get_model_string(config)`, run agent with user message and message_history, save assistant response via `save_message(db_path, session_id, "assistant", response)`, emit progress steps (loading context 0-20, generating response 20-90, saving response 90-100)
- [ ] T021 [US4] Implement GET `/{session_id}/messages` endpoint in `backend/api/routes/engineer.py`: verify session exists (404), call `get_messages(db_path, session_id)`, return MessageListResponse
- [ ] T022 [US4] Implement POST `/{session_id}/messages` endpoint in `backend/api/routes/engineer.py`: call `_require_analyzed_session()`, save user message via `save_message(db_path, session_id, "user", content)`, read ACConfig, create chat job via JobManager, launch via `run_job()`, return 202 ChatJobResponse with job_id and message_id
- [ ] T023 [US4] Implement DELETE `/{session_id}/messages` endpoint in `backend/api/routes/engineer.py`: verify session exists (404), call `clear_messages(db_path, session_id)`, return ClearMessagesResponse with deleted_count

**Checkpoint**: User Story 4 complete — users can chat with the engineer about any analyzed session.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T024 Update `backend/api/engineer/__init__.py` with public imports for pipeline functions, serializer models, and cache helpers
- [ ] T025 Run full test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) — verify all existing 530+ tests still pass and new tests pass
- [ ] T026 Verify all 7 endpoints respond correctly with manual curl/httpie smoke tests per contracts/endpoints.md examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — can start immediately after Phase 2
- **US2 (Phase 4)**: Depends on Foundational — can start after Phase 2 (independent of US1 for read-only endpoints, but testing benefits from US1's pipeline having run)
- **US3 (Phase 5)**: Depends on Foundational — can start after Phase 2 (needs recommendations in DB, so practically after US1)
- **US4 (Phase 6)**: Depends on Foundational — can start after Phase 2 (independent pipeline)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Run Engineer)**: No dependency on other stories — core MVP
- **US2 (View Recommendations)**: Independent endpoints, but integration testing requires recommendations from US1
- **US3 (Apply Recommendation)**: Requires a recommendation to exist — practically depends on US1
- **US4 (Chat)**: Fully independent — separate pipeline, separate storage, no dependency on US1/US2/US3

### Recommended Execution Order

Sequential (single developer): Phase 1 → Phase 2 → US1 → US2 → US3 → US4 → Polish

### Within Each User Story

1. Tests first (write tests, verify they fail or are pending)
2. Pipeline/service implementation
3. Route endpoints
4. Run tests to verify

### Parallel Opportunities

**Phase 2** (after Setup):
- T003 (serializers) and T004 (cache helpers) can run in parallel
- T007 (serializer tests) and T008 (cache tests) can run in parallel

**After Foundational**:
- US1 tests (T009, T010) can run in parallel
- US4 is fully independent of US1/US2/US3 and can be developed in parallel

---

## Parallel Example: User Story 1

```
# Launch tests in parallel:
Task T009: "Pipeline tests for make_engineer_job() in test_engineer_pipeline.py"
Task T010: "Route tests for POST /engineer in test_engineer_routes.py"

# Then implement sequentially:
Task T011: "Implement make_engineer_job() in pipeline.py"
Task T012: "Implement POST /engineer route in routes/engineer.py"
```

## Parallel Example: Foundational Phase

```
# Launch in parallel (different files):
Task T003: "Define response models in serializers.py"
Task T004: "Implement cache helpers in cache.py"

# Then tests in parallel:
Task T007: "Serializer tests in test_engineer_serializers.py"
Task T008: "Cache tests in test_engineer_cache.py"

# Then main.py update (depends on router existing):
Task T005: "Update main.py with lifespan + router"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T008)
3. Complete Phase 3: User Story 1 (T009-T012)
4. **STOP and VALIDATE**: POST /engineer creates a recommendation and advances state
5. This is the minimum viable integration of the AI engineer with the API

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. Add US1 (Run Engineer) → Core AI pipeline exposed via API (MVP)
3. Add US2 (View Recommendations) → Users can see what the engineer suggested
4. Add US3 (Apply Recommendation) → Users can apply changes to .ini files
5. Add US4 (Chat) → Users can have a conversation about the session
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All tests use tmp_path, FunctionModel mocks, and httpx AsyncClient — no real LLM calls
- The `api/engineer/` package mirrors the `api/analysis/` package structure from Phase 6.3
- `analyze_with_engineer()` already persists recommendations to SQLite internally — the pipeline only needs to cache the full EngineerResponse JSON and update session state
- Chat uses a simple single-agent Pydantic AI call (not specialist routing) with session summary as context
