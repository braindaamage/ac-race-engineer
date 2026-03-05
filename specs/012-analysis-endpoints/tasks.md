# Tasks: Analysis Endpoints

**Input**: Design documents from `/specs/012-analysis-endpoints/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/analysis-api.md

**Tests**: Included — the project has strong test discipline (530+ existing tests) and the implementation plan specifies 4 test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package structure and shared API response models

- [x] T001 Create `backend/api/analysis/__init__.py` with package docstring and public exports placeholder (will be populated as modules are built)
- [x] T002 Define all API response Pydantic v2 models in `backend/api/analysis/models.py`: ProcessResponse (job_id, session_id), LapSummary (lap_number, classification, is_invalid, lap_time_s, tyre_temps_avg, peak_lat_g, peak_lon_g, full_throttle_pct, braking_pct), LapListResponse (session_id, lap_count, laps), LapDetailResponse (session_id, lap_number, classification, is_invalid, metrics: LapMetrics), AggregatedCorner (corner_number, sample_count, avg_apex_speed_kmh, avg_entry_speed_kmh, avg_exit_speed_kmh, avg_duration_s, avg_understeer_ratio, avg_trail_braking_intensity, avg_peak_lat_g), CornerListResponse (session_id, corner_count, corners), CornerLapEntry (lap_number, metrics: CornerMetrics), CornerDetailResponse (session_id, corner_number, laps), StintListResponse (session_id, stint_count, stints: list[StintMetrics]), StintComparisonResponse (session_id, comparison: StintComparison), ConsistencyResponse (session_id, consistency: ConsistencyMetrics). Import existing analyzer models (LapMetrics, CornerMetrics, StintMetrics, StintComparison, ConsistencyMetrics) — do not redefine them.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cache module, router skeleton, shared guard rails — MUST complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement cache functions in `backend/api/analysis/cache.py`: `get_cache_dir(sessions_dir, session_id) -> Path` returns `sessions_dir / session_id`, `save_analyzed_session(cache_dir, analyzed: AnalyzedSession) -> Path` writes `analyzed.json` using `model_dump(mode="json")` with indent=2, `load_analyzed_session(cache_dir) -> AnalyzedSession` reads `analyzed.json` and calls `AnalyzedSession.model_validate()`, raising `FileNotFoundError` if missing and `ValueError` if corrupted JSON or validation fails
- [x] T004 Write cache round-trip tests in `backend/tests/api/test_analysis_cache.py`: test save then load produces identical AnalyzedSession (use `make_parsed_session` + `analyze_session` from existing test helpers to generate realistic data), test load from nonexistent directory raises FileNotFoundError, test load from corrupted JSON raises ValueError, test save overwrites existing file (idempotent), test get_cache_dir returns correct path
- [x] T005 Create analysis router skeleton in `backend/api/routes/analysis.py`: create `router = APIRouter()` (no prefix — endpoints are nested under `/sessions`), implement a shared `_get_analyzed_session(request, session_id)` helper that: (1) calls `get_session(db_path, session_id)` and raises HTTPException 404 if not found, (2) checks `session.state` is in ("analyzed", "engineered") and raises HTTPException 409 with message "Session has not been analyzed yet. Current state: {state}. Process the session first." if not, (3) calls `load_analyzed_session(get_cache_dir(...))` and raises HTTPException 409 with "Cached results are corrupted or missing — re-process the session" on FileNotFoundError/ValueError. This helper is used by all metric GET endpoints.
- [x] T006 Register the analysis router and initialize active_processing_jobs in `backend/api/main.py`: import and include the analysis router, add `app.state.active_processing_jobs = {}` in the lifespan function (before yield)

**Checkpoint**: Foundation ready — cache works, router is registered, guard rails are in place

---

## Phase 3: User Story 1 — Process a Session (Priority: P1) MVP

**Goal**: User triggers processing on a discovered session; pipeline runs as a tracked job with progress updates; session advances to "analyzed" with cached results on disk.

**Independent Test**: Trigger processing on a discovered session, verify state becomes "analyzed", verify analyzed.json + parser cache files exist on disk.

### Implementation for User Story 1

- [x] T007 [US1] Implement `run_processing_pipeline()` in `backend/api/analysis/pipeline.py`: async callable matching the `run_job` signature `async def(update_callback) -> result`. Steps: (1) validate csv_path and meta_path exist — raise FileNotFoundError with descriptive message if missing, (2) `await update(5, "Parsing session...")`, (3) run `parse_session(csv_path, meta_path)` via `asyncio.to_thread()`, (4) `await update(35, "Saving parsed data...")`, (5) run `save_session(parsed, cache_dir)` via `asyncio.to_thread()`, (6) `await update(45, "Analyzing metrics...")`, (7) run `analyze_session(parsed)` via `asyncio.to_thread()`, (8) `await update(85, "Caching analysis results...")`, (9) call `save_analyzed_session(cache_dir, analyzed)`, (10) `await update(95, "Updating session state...")`, (11) call `update_session_state(db_path, session_id, "analyzed")`, (12) return `{"session_id": session_id, "state": "analyzed"}`. The function signature: `make_processing_job(session_id, csv_path, meta_path, sessions_dir, db_path)` returns the async callable. Also include cleanup logic: after job completes (success or failure), remove session_id from `active_processing_jobs` dict (pass dict ref into the callable).
- [x] T008 [US1] Implement `POST /sessions/{session_id}/process` endpoint in `backend/api/routes/analysis.py`: (1) get session via `get_session()` — 404 if not found, (2) check `app.state.active_processing_jobs` for session_id — 409 if already running, (3) validate csv_path and meta_path are set on the session record — 409 if missing, (4) create job via `manager.create_job("process_session")`, (5) register session_id → job_id in `active_processing_jobs`, (6) build the pipeline callable via `make_processing_job(...)`, (7) create asyncio task via `run_job(manager, job_id, callable)` and register with manager, (8) return 202 with ProcessResponse(job_id, session_id)
- [x] T009 [US1] Write pipeline unit tests in `backend/tests/api/test_analysis_pipeline.py`: test successful pipeline with synthetic session data (build CSV+meta.json via parser conftest helpers `make_session_df` + `make_metadata_v2` + `_write_session_files`), verify parsed cache + analyzed.json created, verify session state updated in SQLite, verify progress callback called with expected steps and percentages. Test pipeline failure when CSV missing — verify FileNotFoundError with descriptive message. Test pipeline failure when meta.json missing. Test idempotent re-processing — verify analyzed.json overwritten. Test cleanup of active_processing_jobs dict on success and on failure.
- [x] T010 [US1] Write process endpoint tests in `backend/tests/api/test_analysis_routes.py`: test POST /sessions/{id}/process returns 202 with job_id for discovered session, test 404 for nonexistent session, test 409 when job already running for same session, test 409 when csv_path/meta_path missing on session record. Use httpx AsyncClient with test app, pre-populate SQLite with session records via `save_session()`. For the 202 test, verify the job appears in the job manager. Note: do not test full pipeline execution in route tests — that's covered by T009.

**Checkpoint**: Processing pipeline is functional. User can trigger processing, watch progress, and get analyzed results cached to disk.

---

## Phase 4: User Story 2 — Explore Lap Metrics (Priority: P2)

**Goal**: User queries lap list with summaries and drills into individual lap detail with full 7-group metrics.

**Independent Test**: On an analyzed session, query GET /laps and verify all laps returned with summary fields; query GET /laps/{n} and verify full LapMetrics returned.

### Implementation for User Story 2

- [x] T011 [P] [US2] Implement lap serializers in `backend/api/analysis/serializers.py`: `summarize_lap(lap: AnalyzedLap) -> LapSummary` extracts lap_number, classification, is_invalid, lap_time_s from timing, tyre_temps_avg (dict of FL/FR/RL/RR core temp averages from tyres.temps_avg), peak_lat_g and peak_lon_g from grip, full_throttle_pct and braking_pct from driver_inputs. `summarize_all_laps(analyzed: AnalyzedSession) -> list[LapSummary]` maps over all laps.
- [x] T012 [US2] Implement `GET /sessions/{session_id}/laps` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, serialize all laps via `summarize_all_laps()`, return LapListResponse with session_id, lap_count, and laps list
- [x] T013 [US2] Implement `GET /sessions/{session_id}/laps/{lap_number}` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, find lap by lap_number in `analyzed.laps` — 404 if not found, return LapDetailResponse with session_id, lap_number, classification, is_invalid, and full metrics (LapMetrics from the existing analyzer model)
- [x] T014 [P] [US2] Write lap serializer tests in `backend/tests/api/test_analysis_serializers.py`: test `summarize_lap` produces correct LapSummary with all fields from a known AnalyzedLap fixture (build via `analyze_session(make_parsed_session(...))`), test tyre_temps_avg extracts core temps correctly, test summarize_all_laps returns correct count
- [x] T015 [US2] Write lap endpoint tests in `backend/tests/api/test_analysis_routes.py`: test GET /laps returns 200 with all laps for analyzed session, test GET /laps/{n} returns 200 with full metrics for valid lap, test GET /laps/{n} returns 404 for nonexistent lap number, test GET /laps returns 404 for nonexistent session, test GET /laps returns 409 for session in "discovered" state. Pre-populate test DB with session record in "analyzed" state and pre-cache analyzed.json via `save_analyzed_session()`.

**Checkpoint**: Lap list and detail endpoints are functional with all guard rails.

---

## Phase 5: User Story 3 — Explore Corner Metrics (Priority: P3)

**Goal**: User views aggregated corner metrics across flying laps and drills into per-lap corner detail.

**Independent Test**: On an analyzed session with corners, query GET /corners and verify aggregated metrics; query GET /corners/{n} and verify per-lap breakdown.

### Implementation for User Story 3

- [x] T016 [P] [US3] Implement corner aggregation serializer in `backend/api/analysis/serializers.py`: `aggregate_corners(analyzed: AnalyzedSession) -> list[AggregatedCorner]` collects all corners from flying laps (classification == "flying"), groups by corner_number, computes mean of apex_speed_kmh, entry_speed_kmh, exit_speed_kmh, duration_s, understeer_ratio (skip None values), trail_braking_intensity, peak_lat_g across laps. Return sorted by corner_number. Also implement `get_corner_by_lap(analyzed: AnalyzedSession, corner_number: int) -> list[CornerLapEntry]` that returns per-lap metrics for a specific corner across all laps that have it.
- [x] T017 [US3] Implement `GET /sessions/{session_id}/corners` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, call `aggregate_corners()`, return CornerListResponse
- [x] T018 [US3] Implement `GET /sessions/{session_id}/corners/{corner_number}` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, call `get_corner_by_lap()` — if empty list (corner not found in any lap), return 404 — otherwise return CornerDetailResponse
- [x] T019 [P] [US3] Write corner serializer tests in `backend/tests/api/test_analysis_serializers.py`: test `aggregate_corners` with multi-lap session having 2 corners — verify mean values are correct, verify sample_count, verify sorted by corner_number. Test with session having no corners — verify empty list. Test with mixed flying/outlap laps — verify only flying laps included. Test `get_corner_by_lap` returns correct per-lap entries. Test `get_corner_by_lap` with nonexistent corner returns empty list.
- [x] T020 [US3] Write corner endpoint tests in `backend/tests/api/test_analysis_routes.py`: test GET /corners returns 200 with aggregated corners, test GET /corners/{n} returns 200 with per-lap data, test GET /corners/{n} returns 404 for nonexistent corner, test empty corners list for session with no corners, test 404/409 guard rails

**Checkpoint**: Corner list (aggregated) and corner detail (per-lap) endpoints are functional.

---

## Phase 6: User Story 4 — Stint Trends and Comparisons (Priority: P4)

**Goal**: User views stint list with trends and compares two stints by index.

**Independent Test**: On an analyzed session with multiple stints, query GET /stints and verify trends; query GET /compare?stint_a=0&stint_b=1 and verify deltas.

### Implementation for User Story 4

- [x] T021 [P] [US4] Implement `GET /sessions/{session_id}/stints` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, return StintListResponse wrapping `analyzed.stints` directly (StintMetrics is already a Pydantic model — no serialization needed)
- [x] T022 [US4] Implement `GET /sessions/{session_id}/compare` endpoint in `backend/api/routes/analysis.py`: accept query params `stint_a: int` and `stint_b: int`, call `_get_analyzed_session()`, find the StintComparison in `analyzed.stint_comparisons` where `stint_a_index == stint_a` and `stint_b_index == stint_b` (or the reverse) — 404 if not found. Return StintComparisonResponse. If stint indices are out of range of `analyzed.stints`, return 404 with descriptive message.
- [x] T023 [US4] Write stint/comparison endpoint tests in `backend/tests/api/test_analysis_routes.py`: test GET /stints returns 200 with stint list for analyzed session, test GET /compare?stint_a=0&stint_b=1 returns 200 with comparison for multi-stint session, test GET /compare with nonexistent stint index returns 404, test GET /compare without required params returns 422, test single-stint session returns empty stint_comparisons and compare returns 404, test 404/409 guard rails. Use `two_stint_session` fixture pattern from analyzer conftest to build multi-stint test data.

**Checkpoint**: Stint list and comparison endpoints are functional.

---

## Phase 7: User Story 5 — Session Consistency (Priority: P5)

**Goal**: User views session-wide consistency metrics.

**Independent Test**: On an analyzed session, query GET /consistency and verify all fields populated.

### Implementation for User Story 5

- [x] T024 [P] [US5] Implement `GET /sessions/{session_id}/consistency` endpoint in `backend/api/routes/analysis.py`: call `_get_analyzed_session()`, return ConsistencyResponse wrapping `analyzed.consistency`. If consistency is None (edge case: no flying laps), return ConsistencyResponse with a default ConsistencyMetrics (flying_lap_count=0, lap_time_stddev_s=0, best_lap_time_s=0, worst_lap_time_s=0, lap_time_trend_slope=None, corner_consistency=[]).
- [x] T025 [US5] Write consistency endpoint tests in `backend/tests/api/test_analysis_routes.py`: test GET /consistency returns 200 with all consistency fields for analyzed session, test with session having no flying laps returns zero-valued consistency, test 404/409 guard rails

**Checkpoint**: All 8 endpoints (1 POST + 7 GET) are functional and tested.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, exports, and cleanup

- [x] T026 Update `backend/api/analysis/__init__.py` with final public exports: import and re-export `save_analyzed_session`, `load_analyzed_session`, `get_cache_dir` from cache, `make_processing_job` from pipeline, all response models from models, all serializer functions from serializers
- [x] T027 Run full test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) and verify all existing tests (530+) still pass alongside new analysis tests — fix any import conflicts or test isolation issues
- [x] T028 Validate quickstart.md commands: start the server, run POST /sessions/sync, run POST /sessions/{id}/process on a real session (if available), query all 7 metric endpoints, verify responses match contract shapes from `contracts/analysis-api.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001, T002) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — BLOCKS US2-US5 (metric endpoints need cached data to test against)
- **US2 (Phase 4)**: Depends on Phase 2 (guard rails) — can start after Phase 2; independent of US3-US5
- **US3 (Phase 5)**: Depends on Phase 2 (guard rails) — can start after Phase 2; independent of US2, US4, US5
- **US4 (Phase 6)**: Depends on Phase 2 (guard rails) — can start after Phase 2; independent of US2, US3, US5
- **US5 (Phase 7)**: Depends on Phase 2 (guard rails) — can start after Phase 2; independent of US2, US3, US4
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories. **Must be done first for MVP.**
- **US2 (P2)**: Can start after Phase 2 — independent of other stories. Tests reuse analyzed session cache.
- **US3 (P3)**: Can start after Phase 2 — independent of other stories. Tests reuse analyzed session cache.
- **US4 (P4)**: Can start after Phase 2 — independent of other stories. Tests reuse analyzed session cache.
- **US5 (P5)**: Can start after Phase 2 — independent of other stories. Tests reuse analyzed session cache.

### Within Each User Story

- Serializers (if any) before endpoints
- Endpoints before tests (for integration tests)
- Unit tests [P] can run parallel with other unit tests

### Parallel Opportunities

- T001, T002 can run in parallel (different files)
- T003, T005 can run in parallel (different files)
- T011, T014 (US2 serializers + tests) in parallel
- T016, T019 (US3 serializers + tests) in parallel
- T021, T024 (US4 stint endpoint, US5 consistency endpoint) in parallel — different endpoints, same file but non-overlapping code
- US2, US3, US4, US5 can all be implemented in parallel after Phase 2

---

## Parallel Example: After Phase 2

```
# All metric story implementations can run in parallel (independent endpoints):
Stream A (US2): T011 → T012 → T013 → T014 → T015
Stream B (US3): T016 → T017 → T018 → T019 → T020
Stream C (US4): T021 → T022 → T023
Stream D (US5): T024 → T025
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006)
3. Complete Phase 3: User Story 1 (T007-T010)
4. **STOP and VALIDATE**: Test processing end-to-end — trigger processing, verify state advances, verify cache files exist
5. This MVP delivers the core value: sessions can be processed

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Process) → Test → MVP delivers processing capability
3. Add US2 (Laps) → Test → Users can see lap metrics
4. Add US3 (Corners) → Test → Users can see corner performance
5. Add US4 (Stints) → Test → Users can compare stints
6. Add US5 (Consistency) → Test → Users get full analysis picture
7. Polish → Final validation

### Sequential Execution (Single Developer)

Recommended order: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T026 → T027 → T028

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All metric endpoints (US2-US5) share the `_get_analyzed_session()` guard rail helper from Phase 2
- Response models reuse existing analyzer Pydantic models where possible — only new models are for API response wrappers and the LapSummary/AggregatedCorner shapes
- Test fixtures: build realistic AnalyzedSession by running `analyze_session(make_parsed_session(...))` using existing conftest helpers from `backend/tests/analyzer/conftest.py`
- Existing packages (`ac_engineer.parser`, `ac_engineer.analyzer`, `api.jobs`) are NOT modified
- Only `backend/api/main.py` gets a minor extension (router registration + active_processing_jobs init)
