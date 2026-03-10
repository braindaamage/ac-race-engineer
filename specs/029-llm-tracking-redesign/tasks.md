# Tasks: LLM Tracking Redesign + Chat Fixes

**Input**: Design documents from `/specs/029-llm-tracking-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — the spec (SC-005) requires test coverage for all changes, and the existing usage test files must be updated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/ac_engineer/` (core), `backend/api/` (routes), `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Foundational — Storage Redesign (Blocking)

**Purpose**: Replace the old agent_usage/tool_call_details tables and models with the new decoupled llm_events/llm_tool_calls schema. This MUST complete before any user story work since all three stories depend on the new storage layer.

- [ ] T001 [P] Replace `AgentUsage` and `ToolCallDetail` models with `LlmEvent` and `LlmToolCall` Pydantic v2 models in `backend/ac_engineer/storage/models.py`. Remove `VALID_DOMAINS`. Follow field definitions from data-model.md: LlmEvent has `id`, `session_id`, `event_type`, `agent_name`, `model`, `input_tokens`, `output_tokens`, `request_count`, `tool_call_count`, `duration_ms`, `created_at`, `context_type` (nullable), `context_id` (nullable), `tool_calls` list. LlmToolCall has `id`, `event_id`, `tool_name`, `response_tokens`, `call_index`.
- [ ] T002 [P] Replace migrations 5-6 (agent_usage, tool_call_details) with `llm_events` and `llm_tool_calls` DDL in `backend/ac_engineer/storage/db.py`. No CHECK constraints on `event_type` or `context_type` (open strings). `llm_tool_calls.event_id` has FK to `llm_events.id` with CASCADE delete. Integer fields have `CHECK(field >= 0)`.
- [ ] T003 Replace `save_agent_usage()` and `get_agent_usage()` with `save_llm_event(db_path, event)` and `get_llm_events(db_path, context_type, context_id)` in `backend/ac_engineer/storage/usage.py`. Follow the contract in `contracts/llm-events-storage.md`: save generates id/created_at, inserts atomically; get queries by context_type+context_id, returns list ordered by created_at ASC with tool_calls populated.
- [ ] T004 Update public exports in `backend/ac_engineer/storage/__init__.py`: replace `save_agent_usage`, `get_agent_usage`, `AgentUsage`, `ToolCallDetail`, `VALID_DOMAINS` with `save_llm_event`, `get_llm_events`, `LlmEvent`, `LlmToolCall`.
- [ ] T005 Rewrite `backend/tests/storage/test_usage.py` for the new schema. Cover: LlmEvent creation with all fields, auto-generated id/created_at, LlmToolCall persistence with event_id linkage, atomic save (event + tool calls in one transaction), get_llm_events by context_type+context_id, empty result for non-matching context, tool_calls ordered by call_index, cascade delete when event is deleted. Test count must not decrease from current (14 tests).

**Checkpoint**: Storage layer complete — `save_llm_event` and `get_llm_events` work with new tables. Run `pytest backend/tests/storage/test_usage.py -v`.

---

## Phase 2: User Story 1 — Decoupled LLM Usage Storage (Priority: P1) 🎯 MVP

**Goal**: Analysis pipeline persists usage to the new tables and the existing UI (UsageSummaryBar, UsageDetailModal) continues working unchanged.

**Independent Test**: Run an analysis job → verify usage stored in llm_events/llm_tool_calls → verify frontend displays identical token counts, tool calls, and agent breakdowns.

### Tests for User Story 1

- [ ] T006 [P] [US1] Update `backend/tests/engineer/test_usage_capture.py`: replace `AgentUsage`/`ToolCallDetail` references with `LlmEvent`/`LlmToolCall`, verify `analyze_with_engineer()` builds LlmEvent with `event_type="analysis"`, `context_type="recommendation"`, `context_id=recommendation_id`. Verify `_extract_tool_calls()` produces `LlmToolCall` objects with `response_tokens` and `call_index`. Test count must not decrease from current (8 tests).
- [ ] T007 [P] [US1] Update `backend/tests/api/test_usage_routes.py`: update `_seed_usage()` helper to insert into `llm_events`/`llm_tool_calls` tables with new column names. Update all assertions for field name changes (domain→agent_name in DB, but still `domain` in API response). Verify `GET /sessions/{sid}/recommendations/{rid}/usage` returns correct totals and per-agent breakdown. Test count must not decrease from current (5 tests).

### Implementation for User Story 1

- [ ] T008 [US1] Update `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`: replace `AgentUsage` construction with `LlmEvent` — set `event_type="analysis"`, `agent_name=domain`, `request_count` from `usage.requests`, `context_type="recommendation"`, `context_id=recommendation_id`. Replace `save_agent_usage()` calls with `save_llm_event()`. Update `_extract_tool_calls()` to return `LlmToolCall` objects with `response_tokens` (was `token_count`) and `call_index` (was `called_at`). Also rename `_extract_tool_calls` to `extract_tool_calls` (remove leading underscore) and add it to `backend/ac_engineer/engineer/__init__.py` exports, since T015 needs to import it from the pipeline.
- [ ] T009 [US1] Update `get_recommendation_usage()` in `backend/api/routes/engineer.py`: replace `get_agent_usage(db_path, recommendation_id)` with `get_llm_events(db_path, "recommendation", recommendation_id)`. Map `LlmEvent` fields to existing `AgentUsageDetail` response model: `agent_name→domain`, `request_count→turn_count`, `LlmToolCall.response_tokens→ToolCallInfo.token_count`. Update import from `ac_engineer.storage.usage`.
- [ ] T010 [US1] Update `backend/api/engineer/serializers.py` if needed: verify `AgentUsageDetail`, `ToolCallInfo`, `UsageTotals`, and `RecommendationUsageResponse` models still match the API contract (no field changes expected — mapping happens in the route).

**Checkpoint**: Analysis usage flow works end-to-end with new tables. Run `pytest backend/tests/engineer/test_usage_capture.py backend/tests/api/test_usage_routes.py -v`. Frontend displays identical data (no frontend changes needed for US1).

---

## Phase 3: User Story 2 — Chat Message Token Tracking (Priority: P2)

**Goal**: Chat responses capture principal agent token usage, a new endpoint exposes it, and the frontend displays UsageSummaryBar below assistant messages.

**Independent Test**: Send a chat message → verify llm_events row with event_type="chat" → call GET /sessions/{sid}/messages/{mid}/usage → verify UsageSummaryBar appears below the assistant message.

### Tests for User Story 2

- [ ] T011 [P] [US2] Add message usage endpoint tests in `backend/tests/api/test_usage_routes.py`: test `GET /sessions/{sid}/messages/{mid}/usage` with usage data (200 with totals + agents), without usage data (200 with zero totals), session not found (404), message not found (404). At least 4 new tests.
- [ ] T012 [P] [US2] Add chat pipeline usage capture tests in `backend/tests/engineer/test_usage_capture.py` or a new `backend/tests/api/test_chat_usage.py`: test that `make_chat_job()` persists an LlmEvent with `event_type="chat"`, `agent_name="principal"`, `context_type="message"` after agent.run(). Test graceful degradation: usage capture failure still delivers the message. Test fallback: if AgentDeps construction fails, chat proceeds without tools. At least 3 new tests.
- [ ] T013 [P] [US2] Update `frontend/tests/views/engineer/EngineerView.test.tsx`: add test that assistant messages fetch usage from `/sessions/{sid}/messages/{mid}/usage`. Add test that UsageSummaryBar renders below assistant messages with usage data. Add test that UsageSummaryBar does NOT render below messages without usage data. At least 3 new tests.

### Implementation for User Story 2

- [ ] T014 [US2] Update `make_chat_job()` in `backend/api/engineer/pipeline.py` to construct AgentDeps and register tools: (1) load `AnalyzedSession` from `load_analyzed_session(cache_dir)`, (2) get `car_name` from `get_session(db_path, session_id).car_name`, (3) get `ac_install_path` from `read_config(config_path).ac_install_path`, (4) call `resolve_parameters(ac_install_path, car_name, db_path)` to get parameter_ranges, (5) build `AgentDeps(analyzed_session=analyzed, parameter_ranges=parameter_ranges, knowledge_fragments=[])`, (6) create `Agent[AgentDeps, str]` with tools from `DOMAIN_TOOLS["principal"]`. Wrap steps 1-5 in try/except: if AgentDeps construction fails for any reason, fall back to plain `Agent[None, str]` without tools and log a warning. Add imports for `resolve_parameters`, `AgentDeps`, `DOMAIN_TOOLS`, `read_config`, `get_session`, and the tool functions.
- [ ] T015 [US2] Add usage capture after `agent.run()` in `make_chat_job()` in `backend/api/engineer/pipeline.py`: extract usage via `result.usage()`, extract tool calls via `_extract_tool_calls(result)` (import from `ac_engineer.engineer.agents`), measure duration_ms, build `LlmEvent(event_type="chat", agent_name="principal", session_id=session_id, model=effective_model, context_type="message", context_id=message_id, ...)`, call `save_llm_event(db_path, event)` wrapped in try/except so failure doesn't block message saving.
- [ ] T016 [US2] Add `MessageUsageResponse` model to `backend/api/engineer/serializers.py`: identical to `RecommendationUsageResponse` but with `message_id: str` instead of `recommendation_id: str`. Shares `UsageTotals` and `AgentUsageDetail`.
- [ ] T017 [US2] Add `GET /sessions/{sid}/messages/{mid}/usage` endpoint in `backend/api/routes/engineer.py`: validate session exists (404), validate message exists in that session (404), call `get_llm_events(db_path, "message", message_id)`, compute totals, map to `AgentUsageDetail` list, return `MessageUsageResponse`. If no events found, return 200 with zero totals and empty agents (not 404). Follow the contract in `contracts/message-usage-endpoint.md`.
- [ ] T018 [US2] Add `MessageUsageResponse` type to `frontend/src/lib/types.ts`: `{ message_id: string; totals: UsageTotals; agents: AgentUsageDetail[] }`.
- [ ] T018a [US2] Verify that the `Message` type in `frontend/src/lib/types.ts` includes a `message_id: string` field. If not present, add it. This field is required for T019-T020 to build the messageUsageMap. Check that the existing `useMessages()` hook and `MessageList` component pass `message_id` through — update if needed.
- [ ] T019 [US2] Add message usage queries in `frontend/src/views/engineer/index.tsx`: collect assistant message IDs from `useMessages()`, create `useQueries` to fetch `/sessions/{sid}/messages/{mid}/usage` for each, build a `messageUsageMap: Map<string, MessageUsageResponse>`, pass it to `MessageList` as a new `messageUsageMap` prop.
- [ ] T020 [US2] Render `UsageSummaryBar` below assistant messages in `frontend/src/views/engineer/MessageList.tsx`: accept `messageUsageMap` prop, for each assistant message check if `messageUsageMap.get(msg.message_id)` has non-zero totals, if so render `UsageSummaryBar` with the totals and a details callback. Do NOT render for messages with zero/missing usage.

**Checkpoint**: Chat usage captured and displayed end-to-end. Run `pytest backend/tests/ -v`, `cd frontend && npm run test`, `npx tsc --noEmit`.

---

## Phase 4: User Story 3 — Driver Feedback Display Fix (Priority: P3)

**Goal**: Each driver feedback item appears exactly once in the Engineer view — only inside RecommendationCard, not duplicated in the parent MessageList.

**Independent Test**: View a recommendation with driver feedback → count that each feedback item appears exactly once.

### Tests for User Story 3

- [ ] T021 [P] [US3] Add or update test in `frontend/tests/views/engineer/MessageList.test.tsx` (or `EngineerView.test.tsx`): render a recommendation with driver_feedback items, assert that DriverFeedbackCard components appear exactly once per feedback item (not duplicated). At least 1 new test.

### Implementation for User Story 3

- [ ] T022 [US3] Remove the duplicate `rec.driver_feedback.map(...)` block from `frontend/src/views/engineer/MessageList.tsx` (approximately lines 116-118) that renders `DriverFeedbackCard` outside of `RecommendationCard`. The `RecommendationCard` component already renders feedback at its lines 96-102.

**Checkpoint**: No duplicate feedback cards. Run `cd frontend && npm run test`.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [ ] T023 Run full backend test suite: `conda run -n ac-race-engineer pytest backend/tests/ -v`. Verify total test count has not decreased (was 900+).
- [ ] T024 Run full frontend test suite: `cd frontend && npm run test`. Verify total test count has not decreased (was 341).
- [ ] T025 Run TypeScript strict check: `cd frontend && npx tsc --noEmit`. Zero errors.
- [ ] T026 Delete `data/ac_engineer.db` to force DB recreation with new schema. Verify app starts cleanly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on Phase 1 completion — uses new storage functions
- **Phase 3 (US2)**: Depends on Phase 1 completion — uses new storage functions. Independent of US1 at the storage/API level, but US1 should complete first to validate the storage layer with the simpler analysis path.
- **Phase 4 (US3)**: No backend dependencies — can start after Phase 1 or in parallel with US1/US2. Frontend-only change.
- **Phase 5 (Polish)**: Depends on all stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 1 (foundational storage). No dependencies on other stories.
- **US2 (P2)**: Depends on Phase 1 (foundational storage). Logically depends on US1 being validated first (same storage functions used by both paths).
- **US3 (P3)**: Independent of all other stories. Can run in parallel with US1/US2 at any time after Phase 1.

### Within Each User Story

- Tests written first, verify they reference correct models/functions
- Models/storage before services/pipeline
- Pipeline/backend before API endpoints
- API endpoints before frontend
- Frontend types before components

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files: models.py and db.py)
- **Phase 2 (US1)**: T006 and T007 can run in parallel (different test files). T009 and T010 can run in parallel (routes vs serializers).
- **Phase 3 (US2)**: T011, T012, and T013 can run in parallel (three different test files). T016 and T018 can run in parallel (backend serializer vs frontend types).
- **Phase 4 (US3)**: T021 and T022 can potentially run in parallel, but T022 is trivial enough to do first.
- **Cross-story**: US3 (Phase 4) can run in parallel with US1 (Phase 2) or US2 (Phase 3) since it's a frontend-only fix in a different code path.

---

## Parallel Example: Phase 1 (Foundational)

```
# These two touch different files — run in parallel:
T001: Replace models in backend/ac_engineer/storage/models.py
T002: Replace migrations in backend/ac_engineer/storage/db.py

# Then sequentially (depends on T001+T002):
T003: Replace functions in backend/ac_engineer/storage/usage.py
T004: Update exports in backend/ac_engineer/storage/__init__.py
T005: Rewrite tests in backend/tests/storage/test_usage.py
```

## Parallel Example: User Story 2

```
# Tests can run in parallel (different files):
T011: API usage route tests in backend/tests/api/test_usage_routes.py
T012: Chat pipeline tests in backend/tests/engineer/ or backend/tests/api/
T013: Frontend EngineerView tests in frontend/tests/views/engineer/

# Backend serializer + frontend type in parallel (different languages):
T016: MessageUsageResponse in backend/api/engineer/serializers.py
T018: MessageUsageResponse type in frontend/src/lib/types.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational storage redesign
2. Complete Phase 2: US1 — analysis pipeline + existing UI
3. **STOP and VALIDATE**: All existing usage features work identically with new tables
4. This alone delivers the storage redesign (CHANGE 1 from the spec)

### Incremental Delivery

1. Phase 1 (Foundational) → New storage layer works
2. Phase 2 (US1) → Analysis usage works end-to-end → Validate (MVP!)
3. Phase 3 (US2) → Chat tracking + message usage endpoint + frontend display
4. Phase 4 (US3) → Driver feedback bug fix (can also be done earlier)
5. Phase 5 (Polish) → Full suite validation
6. Each phase adds value without breaking previous phases

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Test count must never decrease — existing tests are updated, not removed
- DB is recreated from scratch (delete `data/ac_engineer.db`) — no migration needed
- Chat agent tool registration (T014) is a prerequisite for meaningful tool call tracking (T015)
- The `AgentUsageDetail.domain` field in API responses is populated from `agent_name` in the DB — "principal" for chat, specialist domain names for analysis
