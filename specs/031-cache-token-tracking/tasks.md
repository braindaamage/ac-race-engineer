# Tasks: Cache Token Tracking

**Input**: Design documents from `/specs/031-cache-token-tracking/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-usage.md, quickstart.md

**Tests**: Included per layer — storage, capture, API, and frontend.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Foundational (Storage + Capture + API)

**Purpose**: Backend pipeline changes shared by both user stories. All layers from storage through API response must be complete before any UI work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T001 [P] Add `cache_read_tokens` and `cache_write_tokens` fields to `LlmEvent` model with `Field(default=0, ge=0)` in `backend/ac_engineer/storage/models.py`
- [x] T002 [P] Add migration 7 to `_MIGRATIONS` list with two `ALTER TABLE llm_events ADD COLUMN` statements (`cache_read_tokens` and `cache_write_tokens`, both `INTEGER NOT NULL DEFAULT 0 CHECK(col >= 0)`) in `backend/ac_engineer/storage/db.py`
- [x] T003 Include `cache_read_tokens` and `cache_write_tokens` in the INSERT statement of `save_llm_event()` and in the row-to-model reconstruction of `get_llm_events()` in `backend/ac_engineer/storage/usage.py`
- [x] T004 Add storage tests: save/get round-trip with non-zero cache fields, and verify pre-existing records (inserted without cache columns) default to 0 on read, in `backend/tests/storage/test_usage.py`
- [x] T005 [P] Read `usage.cache_read_tokens` and `usage.cache_write_tokens` from `result.usage()` into the `LlmEvent` constructor in the specialist agent usage capture block (~line 625) of `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py`
- [x] T006 [P] Read `usage.cache_read_tokens` and `usage.cache_write_tokens` from `result.usage()` into the `LlmEvent` constructor in the chat usage capture block (~line 218) of `make_chat_job()` in `backend/api/engineer/pipeline.py`
- [x] T007 Add capture tests: verify `LlmEvent` construction reads `cache_read_tokens` and `cache_write_tokens` from a mock `RunUsage` object (non-zero values pass through, missing/zero values default to 0), in `backend/tests/engineer/test_usage_capture.py`
- [x] T008 [P] Add `cache_read_tokens: int = 0` and `cache_write_tokens: int = 0` to both `AgentUsageDetail` and `UsageTotals` Pydantic models in `backend/api/engineer/serializers.py`
- [x] T009 Sum `cache_read_tokens` and `cache_write_tokens` in the totals computation and pass them through in the per-agent detail construction within `_compute_usage_response()` in `backend/api/routes/engineer.py`
- [x] T010 Add API tests: verify both usage endpoints (`/recommendations/{rid}/usage` and `/messages/{mid}/usage`) return `cache_read_tokens` and `cache_write_tokens` in both `totals` and per-agent `agents[]` objects, in `backend/tests/api/test_usage_routes.py`
- [x] T011 [P] Add `cache_read_tokens: number` and `cache_write_tokens: number` to `UsageTotals` and `AgentUsageDetail` TypeScript interfaces in `frontend/src/lib/types.ts`

**Checkpoint**: Backend pipeline complete with tests. Both usage endpoints now return cache token fields (defaulting to 0 for older records). Frontend types updated. Run `conda run -n ac-race-engineer pytest backend/tests/ -v` to verify all tests pass.

---

## Phase 2: User Story 1 - View Cache Savings in Usage Details (Priority: P1) 🎯 MVP

**Goal**: Users see cache read and cache write token counts per agent in the usage detail modal when values are non-zero. Zero values (older records, non-caching providers) show no cache information.

**Independent Test**: Open the usage detail modal for a recommendation or chat message that has non-zero cache tokens → cache read and cache write appear per agent row. Open it for a record with zero cache tokens → no cache info shown, identical to current behavior.

### Implementation for User Story 1

- [x] T012 [US1] Add conditional cache read and cache write display per agent row (shown only when `cache_read_tokens > 0 || cache_write_tokens > 0` for that agent) using `formatTokenCount()` in `frontend/src/views/engineer/UsageDetailModal.tsx`
- [x] T013 [US1] Add frontend tests: verify cache read/write renders per agent when non-zero, verify cache info hidden when both are zero, verify modal works with legacy data (no cache fields), in `frontend/tests/views/engineer/UsageDetailModal.test.tsx`

**Checkpoint**: User Story 1 complete. The detail modal shows cache breakdown per agent when data exists, and hides it otherwise.

---

## Phase 3: User Story 2 - Cache Totals in Summary Bar (Priority: P2)

**Goal**: Users see aggregated cache read token count in the usage summary bar at a glance, without opening the detail modal.

**Independent Test**: Render the summary bar with usage data containing non-zero `cache_read_tokens` total → cache count appears. Render with zero cache totals → bar looks identical to current behavior.

### Implementation for User Story 2

- [x] T014 [US2] Add conditional cache read total display (shown only when `totals.cache_read_tokens > 0`) using `formatTokenCount()` in `frontend/src/views/engineer/UsageSummaryBar.tsx`
- [x] T015 [US2] Add frontend tests: verify cache read total renders when non-zero, verify cache info hidden when zero, in `frontend/tests/views/engineer/UsageSummaryBar.test.tsx`

**Checkpoint**: User Story 2 complete. Summary bar shows cache totals when present.

---

## Phase 4: Polish & Verification

**Purpose**: Verify backward compatibility, run full test suites, confirm no regressions.

- [x] T016 Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) and verify all tests pass including new cache token tests
- [x] T017 Run frontend type check and test suite (`cd frontend && npx tsc --noEmit && npm run test`) and verify all tests pass with zero type errors including new cache token tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately. BLOCKS all user stories.
- **User Story 1 (Phase 2)**: Depends on Foundational completion (T001-T011).
- **User Story 2 (Phase 3)**: Depends on Foundational completion (T001-T011). Independent of User Story 1.
- **Polish (Phase 4)**: Depends on all user stories being complete.

### Within Foundational Phase

```
T001 (models.py) ─┐
T002 (db.py)    ───┤──► T003 (usage.py) ──► T004 (storage tests)
                   │                              │
T005 (agents.py) ──┤                              ▼
T006 (pipeline.py)─┤──► T007 (capture tests)  T009 (routes/engineer.py) ──► T010 (API tests)
T008 (serializers)─┘──► T009 (routes/engineer.py)
T011 (types.ts)  ──── (parallel, independent file)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on T001-T011 (foundational). No dependency on US2.
- **User Story 2 (P2)**: Depends on T001-T011 (foundational). No dependency on US1.

### Parallel Opportunities

Within Foundational:
- T001, T002, T005, T006, T008, T011 can all run in parallel (different files)
- T003 depends on T001 + T002 (needs model fields and migration)
- T004 depends on T003 (tests the storage layer)
- T007 depends on T005 + T006 (tests the capture layer)
- T009 depends on T008 (needs serializer fields to reference)
- T010 depends on T009 (tests the API layer)

Across User Stories:
- T012-T013 (US1) and T014-T015 (US2) can run in parallel after foundational completes

---

## Parallel Example: Foundational Phase

```bash
# Launch all independent foundational tasks together:
Task: "T001 Add cache fields to LlmEvent model in backend/ac_engineer/storage/models.py"
Task: "T002 Add migration 7 in backend/ac_engineer/storage/db.py"
Task: "T005 Read cache fields in backend/ac_engineer/engineer/agents.py"
Task: "T006 Read cache fields in backend/api/engineer/pipeline.py"
Task: "T008 Add cache fields to serializers in backend/api/engineer/serializers.py"
Task: "T011 Add cache fields to TypeScript types in frontend/src/lib/types.ts"

# Then sequential tasks with their tests:
Task: "T003 Update save/get in backend/ac_engineer/storage/usage.py"
Task: "T004 Storage tests in backend/tests/storage/test_usage.py"
Task: "T007 Capture tests in backend/tests/engineer/test_usage_capture.py"
Task: "T009 Update _compute_usage_response in backend/api/routes/engineer.py"
Task: "T010 API tests in backend/tests/api/test_usage_routes.py"
```

## Parallel Example: User Stories

```bash
# After foundational completes, launch both stories in parallel:
Task: "T012 Show cache per agent in UsageDetailModal.tsx"
Task: "T013 UsageDetailModal tests in frontend/tests/views/engineer/UsageDetailModal.test.tsx"
Task: "T014 Show cache total in UsageSummaryBar.tsx"
Task: "T015 UsageSummaryBar tests in frontend/tests/views/engineer/UsageSummaryBar.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (T001-T011)
2. Complete Phase 2: User Story 1 (T012-T013)
3. **STOP and VALIDATE**: Verify detail modal shows cache data per agent
4. Run test suites to confirm no regressions

### Incremental Delivery

1. Complete Foundational → Backend pipeline ready with tests
2. Add User Story 1 (T012-T013) → Detail modal shows cache breakdown → MVP!
3. Add User Story 2 (T014-T015) → Summary bar shows cache totals
4. Polish (T016-T017) → Full verification

---

## Notes

- All 17 tasks modify existing files — no new files created
- 6 of 11 foundational tasks are parallelizable ([P] marked)
- Both user stories are independent of each other after foundational completes
- Existing records automatically get 0 for cache fields via SQLite DEFAULT — no data migration
- Use `or 0` when reading from RunUsage to handle None gracefully (matching existing pattern for `input_tokens`)
