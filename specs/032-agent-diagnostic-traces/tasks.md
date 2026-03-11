# Tasks: Agent Diagnostic Traces

**Input**: Design documents from `/specs/032-agent-diagnostic-traces/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — test files are specified in plan.md and quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/ac_engineer/` (core package), `backend/api/` (FastAPI server), `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the config field and path helper that all subsequent work depends on

- [ ] T001 Add `diagnostic_mode: bool = False` field to ACConfig and include it in `_serialize()` in backend/ac_engineer/config/models.py
- [ ] T002 Add `get_traces_dir() -> Path` helper returning `get_data_dir() / "traces"` in backend/api/paths.py
- [ ] T003 [P] Add `TraceResponse` interface and `diagnostic_mode: boolean` to config type in frontend/src/lib/types.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core trace serialization module — MUST be complete before any trace capture or API work

**⚠️ CRITICAL**: All user story phases depend on this module

- [ ] T004 Create backend/ac_engineer/engineer/trace.py with four functions: `serialize_agent_trace(domain, system_prompt, user_prompt, result) -> dict` that iterates `result.all_messages()` and handles SystemPromptPart, UserPromptPart, TextPart, ToolCallPart, ToolReturnPart; `format_trace_markdown(session_id, trace_type, context_id, agent_traces, timestamp) -> str` that formats agent trace dicts into Markdown per data-model.md structure; `write_trace(traces_dir, trace_type, context_id, content) -> Path` that writes to `{traces_dir}/{type}_{id}.md` creating directory if needed; `read_trace(traces_dir, trace_type, context_id) -> str | None` that reads trace file or returns None
- [ ] T005 Create backend/tests/engineer/test_trace.py with tests for: serialize_agent_trace with mock Pydantic AI result (ModelRequest/ModelResponse with various part types), format_trace_markdown output contains expected headings and code blocks, write_trace/read_trace round-trip in tmp_path, read_trace returns None for missing file, write_trace creates directory if not exists

**Checkpoint**: Core trace module ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Enable Diagnostic Mode (Priority: P1) 🎯 MVP

**Goal**: User can toggle diagnostic mode on/off in Settings; the config persists and is readable by the backend

**Independent Test**: Toggle setting on/off in Settings, verify config.json contains diagnostic_mode, verify PATCH /config accepts the field

### Tests for User Story 1

- [ ] T006 [P] [US1] Add test in backend/tests/config/test_config_models.py verifying ACConfig defaults diagnostic_mode to False, serializes it, and round-trips through read_config/write_config
- [ ] T007 [P] [US1] Add test in frontend/tests/views/settings/SettingsView.test.tsx verifying diagnostic mode toggle renders in Advanced section, isDirty tracks changes, and handleSave includes diagnostic_mode

### Implementation for User Story 1

- [ ] T008 [US1] Add `diagnosticMode` local state to SettingsView initialized from `config.diagnostic_mode`, add toggle control in Advanced Card section, include in `isDirty` computation and `handleSave()` fields dict in frontend/src/views/settings/index.tsx

**Checkpoint**: Diagnostic mode can be toggled on/off from Settings and persists via PATCH /config. All existing settings behavior unchanged.

---

## Phase 4: User Story 2 — Inspect Engineer Analysis Trace (Priority: P1)

**Goal**: When diagnostic mode is on, engineer analysis captures a complete multi-agent trace file; the trace is accessible via API and viewable in the frontend

**Independent Test**: Enable diagnostic mode, run an engineer analysis, verify trace file exists in data/traces/, GET the trace endpoint, view trace in frontend via indicator on RecommendationCard

### Tests for User Story 2

- [ ] T009 [P] [US2] Create backend/tests/api/test_engineer_traces.py with tests for: GET recommendation trace returns `{available: true, content: "..."}` when trace file exists; returns `{available: false, content: null}` when no trace file; returns 404 when recommendation does not exist in DB
- [ ] T010 [P] [US2] Create frontend/tests/hooks/useTrace.test.ts with tests for: useTrace fetches from correct endpoint path, returns available/unavailable state, does not fetch when id is null
- [ ] T011 [P] [US2] Create frontend/tests/views/engineer/TraceModal.test.tsx with tests for: renders trace content as preformatted text, handles null content gracefully, close button triggers onClose callback

### Implementation for User Story 2

- [ ] T012 [US2] Add `diagnostic_mode: bool = False` parameter to `analyze_with_engineer()` signature in backend/ac_engineer/engineer/agents.py. After each `agent.run()` in the specialist loop (~line 610-616), if diagnostic_mode is true, call `serialize_agent_trace()` with domain, system_prompt (from `_load_skill_prompt(domain)`), user_prompt, and result; collect into a `collected_traces` list
- [ ] T013 [US2] After recommendation persistence (~line 702) in `analyze_with_engineer()`, if diagnostic_mode is true and collected_traces is non-empty and recommendation_id is known, call `format_trace_markdown()` then `write_trace()` to `data/traces/rec_{recommendation_id}.md`. Wrap in try-except (non-critical). Import `get_traces_dir` from api.paths or accept traces_dir as parameter.
- [ ] T014 [US2] In `make_engineer_job()` in backend/api/engineer/pipeline.py, pass `diagnostic_mode=config.diagnostic_mode` and `traces_dir=get_traces_dir()` to `analyze_with_engineer()`
- [ ] T015 [US2] Add `TraceResponse` Pydantic model to backend/api/routes/engineer.py (or backend/api/engineer/serializers.py) with fields: `available: bool`, `content: str | None`, `trace_type: str`, `id: str`
- [ ] T016 [US2] Add `GET /sessions/{session_id}/recommendations/{recommendation_id}/trace` endpoint in backend/api/routes/engineer.py that calls `read_trace(get_traces_dir(), "rec", recommendation_id)` and returns TraceResponse. Return 404 if recommendation does not exist in DB; return 200 with available=false if trace file not found
- [ ] T017 [US2] Create frontend/src/hooks/useTrace.ts with `useTrace(sessionId, traceType, id)` hook using TanStack Query: queryKey `["trace", traceType, id]`, queryFn fetches `GET /sessions/{sessionId}/recommendations/{id}/trace` or `/messages/{id}/trace` based on traceType, enabled only when sessionId and id are truthy, staleTime Infinity
- [ ] T018 [US2] Create frontend/src/views/engineer/TraceModal.tsx — Modal component that accepts `open`, `onClose`, `traceContent: string | null` props. Display trace content in a `<pre>` block with monospace font and horizontal scroll. Use existing Modal component from components/ui. Apply `ace-trace-modal` CSS class for styling (max-height with vertical scroll)
- [ ] T019 [US2] Add trace indicator to RecommendationCard in frontend/src/views/engineer/RecommendationCard.tsx: use `useTrace(sessionId, "recommendation", recommendation.recommendation_id)` hook; when trace is available, show a small "Trace" button; on click, open TraceModal with trace content
- [ ] T020 [US2] Add test in backend/tests/engineer/test_agents.py verifying that `analyze_with_engineer()` calls write_trace when diagnostic_mode=True and skips when False (mock trace functions)

**Checkpoint**: Engineer analysis traces are captured when diagnostic mode is on. Trace files are human-readable Markdown. API returns trace content. Frontend shows trace indicator and modal on RecommendationCard. No trace captured when diagnostic mode is off.

---

## Phase 5: User Story 3 — Inspect Chat Message Trace (Priority: P2)

**Goal**: When diagnostic mode is on, chat interactions capture a trace file for the assistant's response; the trace is accessible via API and viewable in the frontend

**Independent Test**: Enable diagnostic mode, send a chat message, verify trace file exists in data/traces/, GET the message trace endpoint, view trace via indicator on assistant message

### Tests for User Story 3

- [ ] T021 [P] [US3] Add test in backend/tests/api/test_engineer_traces.py for: GET message trace returns available/unavailable correctly, returns 404 when message does not exist

### Implementation for User Story 3

- [ ] T022 [US3] In `make_chat_job()` in backend/api/engineer/pipeline.py, after `save_message()` (~line 208), if `config.diagnostic_mode` is true, call `serialize_agent_trace("principal", system_prompt, user_content, result)`, then `format_trace_markdown()` + `write_trace()` to `data/traces/msg_{assistant_msg.message_id}.md`. Wrap in try-except (non-critical, same pattern as usage capture)
- [ ] T023 [US3] Add `GET /sessions/{session_id}/messages/{message_id}/trace` endpoint in backend/api/routes/engineer.py that calls `read_trace(get_traces_dir(), "msg", message_id)` and returns TraceResponse. Return 404 if message does not exist; 200 with available=false if trace file not found
- [ ] T024 [US3] Add trace indicator to assistant messages in frontend/src/views/engineer/MessageList.tsx: for each assistant message, use `useTrace(sessionId, "message", msg.message_id)` hook; when trace is available, show a "Trace" button next to or below the message; on click, open TraceModal with trace content

**Checkpoint**: Chat message traces are captured when diagnostic mode is on. Full engineer+chat trace coverage complete.

---

## Phase 6: User Story 4 — Traces Are Independent of Normal Operation (Priority: P1)

**Goal**: Verify that all existing functionality works identically regardless of trace presence/absence. This story is validated by the negative test cases in US2 and US3, plus explicit verification.

**Independent Test**: Run full backend test suite and frontend test suite. Verify no regressions. Query trace endpoints for items without traces and confirm clean responses.

- [ ] T025 [US4] Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) and verify all existing tests pass with the new diagnostic_mode field defaulting to False
- [ ] T026 [US4] Run full frontend test suite (`cd frontend && npx tsc --noEmit && npm run test`) and verify all existing tests pass with the new types and components

**Checkpoint**: All existing tests pass. Trace feature has zero impact on existing functionality.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T027 Add CSS styles for trace modal and trace indicator button in frontend/src/views/engineer/Engineer.css (or appropriate CSS file): `ace-trace-modal` with max-height, overflow-y auto, monospace font for pre block; `ace-trace-btn` for the indicator button styling
- [ ] T028 Run quickstart.md validation — execute all backend and frontend test commands listed in specs/032-agent-diagnostic-traces/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (config field) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on T001, T003 — config field and frontend type
- **US2 (Phase 4)**: Depends on Phase 2 (trace module), T002 (paths), T003 (types)
- **US3 (Phase 5)**: Depends on Phase 2 (trace module), T002 (paths), US2 (shared API patterns/types, TraceModal, useTrace)
- **US4 (Phase 6)**: Depends on all previous phases
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Independent — only needs config field from Phase 1
- **US2 (P1)**: Needs foundational trace module (Phase 2). Independent of US1 at code level (diagnostic_mode flag is just a bool parameter)
- **US3 (P2)**: Reuses trace module, TraceModal, and useTrace from US2. Depends on US2 for shared components.
- **US4 (P1)**: Verification only — depends on all implementation being complete

### Within Each User Story

- Tests first (when included) → verify they fail
- Backend changes before frontend changes
- Core logic before API endpoints
- API endpoints before frontend hooks
- Frontend hooks before UI components

### Parallel Opportunities

- T001 and T003 can run in parallel (backend config vs frontend types)
- T006, T007 can run in parallel (different test files)
- T009, T010, T011 can run in parallel (different test files)
- T012 and T015 can run in parallel (agents.py vs serializers.py, but T012 should land first for integration)

---

## Parallel Example: User Story 2

```bash
# Launch all tests for US2 together:
Task T009: "backend/tests/api/test_engineer_traces.py"
Task T010: "frontend/tests/hooks/useTrace.test.ts"
Task T011: "frontend/tests/views/engineer/TraceModal.test.tsx"

# Then backend implementation (sequential — dependencies within agents.py):
Task T012: "Add diagnostic_mode param + trace collection in specialist loop"
Task T013: "Add trace write after recommendation persistence"
Task T014: "Pass diagnostic_mode from pipeline to analyze_with_engineer"

# API + frontend (can partially parallelize):
Task T015: "TraceResponse model" → Task T016: "Trace endpoint"
Task T017: "useTrace hook" (parallel with T15-T16)
Task T18: "TraceModal component" (parallel with T15-T16)
Task T19: "RecommendationCard indicator" (after T17, T18)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational trace module (T004-T005)
3. Complete Phase 3: US1 — Settings toggle (T006-T008)
4. Complete Phase 4: US2 — Analysis trace capture + API + frontend (T009-T020)
5. **STOP and VALIDATE**: Toggle diagnostic mode on, run an analysis, view trace in frontend
6. Deploy/demo if ready — chat traces (US3) can follow later

### Incremental Delivery

1. Setup + Foundational → Trace module ready
2. Add US1 → Settings toggle works → Config deployed
3. Add US2 → Analysis traces captured and viewable → Core debugging capability delivered
4. Add US3 → Chat traces captured and viewable → Full trace coverage
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Trace capture is always wrapped in try-except — never blocks the primary pipeline
- Trace files are Markdown (.md) for human readability per research.md R2
- No database changes needed — traces are ephemeral files in data/traces/
- The `system_prompt` variable is available in the specialist loop because `_load_skill_prompt(domain)` is called during `_build_specialist_agent()` — for trace capture, call it again or refactor to expose it
- The `user_prompt` variable is already in scope in the specialist loop
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
