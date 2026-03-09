# Tasks: Usage Capture

**Input**: Design documents from `/specs/024-usage-capture/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/usage-endpoint.md

**Organization**: Tasks are grouped by user story. US1 (pipeline instrumentation) must complete before US2 (API endpoint) since the endpoint reads data that US1 writes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in all descriptions

---

## Phase 1: User Story 1 — Automatic Usage Tracking (Priority: P1) 🎯 MVP

**Goal**: After each specialist agent completes in `analyze_with_engineer()`, capture token usage, tool call details, and execution timing. Persist all records to the database after the recommendation is saved. Log a summary per agent.

**Independent Test**: Run an engineer analysis with FunctionModel, then query the database via `get_agent_usage()` to verify usage records exist with correct token counts, tool call details, and timing.

### Implementation for User Story 1

- [x] T001 [US1] Add `_extract_tool_calls()` helper function that iterates `result.all_messages()`, finds `ToolReturnPart` instances in `ModelRequest.parts`, and returns a list of `ToolCallDetail` objects with `tool_name` and estimated `token_count` (`len(str(content)) // 4`) — in `backend/ac_engineer/engineer/agents.py`
- [x] T002 [US1] Modify the specialist agent loop in `analyze_with_engineer()` to: (a) record `start_time = time.perf_counter()` before `agent.run()`, (b) compute `duration_ms` after, (c) extract `result.usage()` for token counts and turn count, (d) call `_extract_tool_calls(result)` for tool details, (e) build an `AgentUsage` object (with empty `recommendation_id`), and (f) append it to a `collected_usage: list[AgentUsage]` — in `backend/ac_engineer/engineer/agents.py`
- [x] T003 [US1] Add usage persistence block after `save_recommendation()` succeeds: set `recommendation_id` from the returned `Recommendation` on each collected `AgentUsage`, call `save_agent_usage(db_path, usage)` for each record, all wrapped in try/except that logs a warning and never raises — in `backend/ac_engineer/engineer/agents.py`
- [x] T004 [US1] Add a structured `logger.info()` call per agent immediately after usage extraction (inside the agent loop), logging domain, input_tokens, output_tokens, tool_call_count, and duration_ms — in `backend/ac_engineer/engineer/agents.py`
- [x] T005 [US1] Write tests for usage capture logic in `backend/tests/engineer/test_usage_capture.py`: (a) `_extract_tool_calls()` with mocked message history containing `ToolReturnPart` objects, (b) `_extract_tool_calls()` with no tool calls returns empty list, (c) `_extract_tool_calls()` token estimation matches `len(str(content)) // 4`, (d) full `analyze_with_engineer()` pipeline with `FunctionModel` verifying usage records are persisted via `get_agent_usage()`, (e) usage persistence failure does not prevent recommendation delivery, (f) logging output includes expected fields

**Checkpoint**: Usage data is captured and persisted for every engineer analysis. Logs show per-agent token consumption.

---

## Phase 2: User Story 2 — Retrieve Usage Endpoint (Priority: P2)

**Goal**: Expose `GET /sessions/{session_id}/recommendations/{recommendation_id}/usage` that returns aggregated totals and per-agent breakdown with tool call details.

**Independent Test**: Seed the database with usage records, call the endpoint, verify the response matches the contract in `contracts/usage-endpoint.md`.

**Depends on**: US1 (data must be capturable), but endpoint can also return empty results for recommendations without usage data.

### Implementation for User Story 2

- [x] T006 [P] [US2] Add four Pydantic v2 response models to `backend/api/engineer/serializers.py`: `ToolCallInfo` (tool_name, token_count), `AgentUsageDetail` (domain, model, input_tokens, output_tokens, tool_call_count, turn_count, duration_ms, tool_calls: list[ToolCallInfo]), `UsageTotals` (input_tokens, output_tokens, total_tokens, tool_call_count, agent_count), `RecommendationUsageResponse` (recommendation_id, totals: UsageTotals, agents: list[AgentUsageDetail])
- [x] T007 [US2] Add `GET /{session_id}/recommendations/{recommendation_id}/usage` route to `backend/api/routes/engineer.py`: guard with 404 for missing session (via `get_session`) and missing recommendation (via `get_recommendation(db_path, recommendation_id)` directly, the same pattern used in the existing `get_recommendation_detail` route), call `get_agent_usage(db_path, recommendation_id)`, compute `UsageTotals` by summing fields, map each `AgentUsage` to `AgentUsageDetail`, return `RecommendationUsageResponse` — follow existing guard pattern from `get_recommendation_detail`
- [x] T008 [US2] Write tests for usage endpoint in `backend/tests/api/test_usage_routes.py`: (a) 200 with usage data — seed session, recommendation, and agent_usage records, verify aggregated totals and per-agent breakdown, (b) 200 with empty usage — recommendation exists but no usage records, verify zero totals and empty agents list, (c) 404 for nonexistent session, (d) 404 for nonexistent recommendation, (e) verify domain names in response match agent domains (balance/tyre/aero/technique)

**Checkpoint**: Usage endpoint returns correct data for any recommendation. All acceptance scenarios from spec verified.

---

## Phase 3: Polish & Verification

**Purpose**: Ensure pipeline changes don't break existing tests.

- [x] T009 Run full backend test suite (`pytest backend/tests/ -v`) to verify no regressions from pipeline modifications

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US2)**: T006 (response models) can start in parallel with Phase 1. T007 and T008 can start after Phase 1 completes (they rely on usage data being capturable for meaningful integration testing)
- **Phase 3 (Polish)**: Depends on Phase 1 and Phase 2 completion

### Within User Story 1

```
T001 (_extract_tool_calls helper)
  ↓
T002 (modify agent loop to collect usage) — depends on T001
  ↓
T003 (persistence block after save_recommendation) — depends on T002
  ↓
T004 (logging) — depends on T002
  ↓
T005 (tests) — depends on T001–T004
```

### Within User Story 2

```
T006 (response models) — no dependencies, can run in parallel with US1
  ↓
T007 (route) — depends on T006
  ↓
T008 (tests) — depends on T007
```

### Parallel Opportunities

```
# These can run in parallel:
T006 (response models in serializers.py) || T001–T004 (pipeline changes in agents.py)

# T004 (logging) can run in parallel with T003 (persistence):
T003 (persistence block) || T004 (logging)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001–T005 (pipeline instrumentation + tests)
2. **STOP and VALIDATE**: Run `pytest backend/tests/engineer/test_usage_capture.py -v`
3. Usage data is now being captured — core value delivered

### Full Delivery

1. Complete US1 (T001–T005) → validate
2. Complete US2 (T006–T008) → validate
3. Run full suite (T009) → confirm no regressions
4. All 9 tasks complete

---

## Notes

- All usage capture code in `agents.py` must be wrapped in try/except per FR-007 (failures never block recommendations)
- `AgentUsage` and `ToolCallDetail` models from Phase 9.1 are used as-is — no modifications
- `save_agent_usage()` and `get_agent_usage()` from Phase 9.1 are used as-is — no modifications
- Token estimation for tool calls: `len(str(content)) // 4` (research decision R2)
- Turn count maps to `RunUsage.requests` (research decision R4)
- Model string via `get_effective_model(config)` (research decision R6)
