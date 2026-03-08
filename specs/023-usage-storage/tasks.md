# Tasks: Usage Storage

**Input**: Design documents from `/specs/023-usage-storage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — the spec requires ≥ 95% line coverage (SC-001) and defines explicit acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pydantic models and database migration — shared by all user stories

- [ ] T001 [P] Add `VALID_DOMAINS` tuple, `ToolCallDetail` model, and `AgentUsage` model (with `Literal` domain type) to `backend/ac_engineer/storage/models.py`, following existing model conventions per data-model.md
- [ ] T002 [P] Append two `CREATE TABLE IF NOT EXISTS` statements (agent_usage, tool_call_details) to `_MIGRATIONS` list in `backend/ac_engineer/storage/db.py`, using the DDL from data-model.md

**Checkpoint**: Models defined and tables created on `init_db()`. Verify by running `init_db` on a fresh temp database and confirming 7 tables exist.

---

## Phase 2: User Story 1 + 2 — Save Agent Usage with Tool Call Details (Priority: P1)

**Goal**: Persist a usage record and its tool call details in a single atomic transaction.

**Independent Test**: Call `save_agent_usage` with valid data including tool calls, then query the database directly to verify all rows exist with correct values and foreign key linkage.

**Note**: US1 (save agent usage) and US2 (save tool call details) are combined into one phase because `save_agent_usage` handles both atomically in a single transaction per research decision R2. They cannot be implemented or tested independently.

### Tests for US1+US2

- [ ] T003 [P] [US1] Write test `TestSaveAgentUsage::test_creates_record_with_all_fields` — save a usage record with tool calls, verify all fields populated and UUIDs generated (32-char hex), in `backend/tests/storage/test_usage.py`. Include `_setup_session` and `_setup_recommendation` helpers plus a `_sample_tool_calls` factory.
- [ ] T004 [P] [US1] Write test `TestSaveAgentUsage::test_auto_generates_ids` — verify usage_id and all detail_ids are unique 32-char hex strings, in `backend/tests/storage/test_usage.py`
- [ ] T005 [P] [US1] Write test `TestSaveAgentUsage::test_invalid_recommendation_raises` — save with nonexistent recommendation_id, expect `sqlite3.IntegrityError`, in `backend/tests/storage/test_usage.py`
- [ ] T006 [P] [US1] Write test `TestSaveAgentUsage::test_invalid_domain_raises` — attempt to save with domain `'invalid'`, expect Pydantic `ValidationError`, in `backend/tests/storage/test_usage.py`
- [ ] T007 [P] [US2] Write test `TestSaveAgentUsage::test_tool_calls_persisted_atomically` — save with multiple tool calls, verify all rows exist in tool_call_details table with correct usage_id FK, in `backend/tests/storage/test_usage.py`
- [ ] T008 [P] [US2] Write test `TestSaveAgentUsage::test_saves_without_tool_calls` — save a usage record with empty tool_calls list, verify agent_usage row exists and tool_call_details table is empty, in `backend/tests/storage/test_usage.py`

### Implementation for US1+US2

- [ ] T009 [US1] Create `backend/ac_engineer/storage/usage.py` with `save_agent_usage(db_path, usage: AgentUsage) -> AgentUsage` function. Follow `save_recommendation` pattern: open `_connect`, insert agent_usage row with `uuid4().hex` ID and `datetime.now(UTC).isoformat()` timestamp, loop to insert each tool_call_detail with generated IDs, `conn.commit()`, return populated model. Single transaction per R2.

**Checkpoint**: All T003–T008 tests pass. `save_agent_usage` persists parent and child rows atomically.

---

## Phase 3: User Story 3 — Retrieve Usage Records (Priority: P2)

**Goal**: Retrieve all usage records for a recommendation with nested tool call details.

**Independent Test**: Save known data, call `get_agent_usage`, verify returned list is correctly structured with nested tool calls and ordered by `created_at` ASC.

### Tests for US3

- [ ] T010 [P] [US3] Write test `TestGetAgentUsage::test_returns_with_tool_calls` — save 2 usage records (each with tool calls) for same recommendation, verify retrieval returns both ordered by created_at with tool calls populated, in `backend/tests/storage/test_usage.py`
- [ ] T011 [P] [US3] Write test `TestGetAgentUsage::test_empty_returns_empty` — call get_agent_usage for recommendation with no usage records, verify empty list returned, in `backend/tests/storage/test_usage.py`
- [ ] T012 [P] [US3] Write test `TestGetAgentUsage::test_does_not_return_other_recommendations` — save usage for rec A and rec B, verify get_agent_usage(rec_A) only returns rec A's records, in `backend/tests/storage/test_usage.py`

### Implementation for US3

- [ ] T013 [US3] Add `get_agent_usage(db_path, recommendation_id: str) -> list[AgentUsage]` to `backend/ac_engineer/storage/usage.py`. Follow `get_recommendations` pattern: query agent_usage rows ordered by created_at ASC, for each row query tool_call_details, return nested `AgentUsage` models with `tool_calls` populated.

**Checkpoint**: All T010–T012 tests pass. Full read path works with nested results.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Exports, migration idempotency, cascade behavior

- [ ] T014 Update `backend/ac_engineer/storage/__init__.py` to import and export `AgentUsage`, `ToolCallDetail`, `VALID_DOMAINS`, `save_agent_usage`, `get_agent_usage` in both the import block and `__all__` list
- [ ] T015 [P] Write test `TestMigration::test_fresh_db_creates_all_tables` — call `init_db` on fresh temp path, query `sqlite_master` for all 7 table names (sessions, recommendations, setup_changes, messages, parameter_cache, agent_usage, tool_call_details), in `backend/tests/storage/test_usage.py`
- [ ] T016 [P] Write test `TestMigration::test_idempotent_on_existing_db` — call `init_db` twice on same path, verify no errors and tables intact, in `backend/tests/storage/test_usage.py`
- [ ] T017 [P] Write test `TestCascade::test_delete_recommendation_cascades_to_usage_and_details` — create session → recommendation → usage → tool_calls, delete recommendation, verify agent_usage and tool_call_details rows are gone, in `backend/tests/storage/test_usage.py`
- [ ] T018 Run full storage test suite (`conda run -n ac-race-engineer pytest backend/tests/storage/ -v`) to verify no regressions in existing tests
- [ ] T019 Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) to verify no regressions across the project

**Checkpoint**: All exports wired, all edge cases covered, full suite green.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (US1+US2)**: Depends on Phase 1 (models and migration must exist before CRUD)
- **Phase 3 (US3)**: Depends on Phase 2 (`get_agent_usage` needs `save_agent_usage` for test data setup)
- **Phase 4 (Polish)**: Depends on Phases 2 and 3 (exports and cross-cutting tests need all functions)

### User Story Dependencies

- **US1 + US2 (P1)**: Combined — `save_agent_usage` handles both atomically. Can start after Phase 1.
- **US3 (P2)**: Requires US1+US2 to be complete (needs save function to create test data for retrieval tests).

### Within Each Phase

- Tests marked [P] can all run in parallel (different test classes, no shared state)
- T001 and T002 can run in parallel (different files)
- Implementation tasks (T009, T013) depend on their corresponding tests being written first

### Parallel Opportunities

Phase 1: T001 ‖ T002 (different files)
Phase 2 tests: T003 ‖ T004 ‖ T005 ‖ T006 ‖ T007 ‖ T008 (all independent test methods)
Phase 3 tests: T010 ‖ T011 ‖ T012 (all independent test methods)
Phase 4: T015 ‖ T016 ‖ T017 (independent test classes)

---

## Parallel Example: Phase 1

```
# Launch both setup tasks together (different files):
Task: "Add models to backend/ac_engineer/storage/models.py"
Task: "Add migrations to backend/ac_engineer/storage/db.py"
```

## Parallel Example: Phase 2 Tests

```
# Launch all US1+US2 tests together (same file, independent test methods):
Task: "test_creates_record_with_all_fields"
Task: "test_auto_generates_ids"
Task: "test_invalid_recommendation_raises"
Task: "test_invalid_domain_raises"
Task: "test_tool_calls_persisted_atomically"
Task: "test_saves_without_tool_calls"
```

---

## Implementation Strategy

### MVP First (US1+US2 Only)

1. Complete Phase 1: Models + Migration
2. Complete Phase 2: save_agent_usage with tests
3. **STOP and VALIDATE**: Run `pytest backend/tests/storage/test_usage.py -v` — all save tests pass
4. Data can be written; retrieval can follow

### Incremental Delivery

1. Phase 1 → Models + tables ready
2. Phase 2 → Write path complete (US1+US2) → Test independently
3. Phase 3 → Read path complete (US3) → Test independently
4. Phase 4 → Exports, edge cases, full regression → Ship

---

## Notes

- [P] tasks = different files or independent test methods, no dependencies
- US1 and US2 are combined because `save_agent_usage` handles both atomically (research decision R2)
- No update/delete functions per FR-011 — immutability by design
- Total: 19 tasks (2 setup, 6 US1+US2 tests, 1 US1+US2 impl, 3 US3 tests, 1 US3 impl, 6 polish)
- Test file: single `backend/tests/storage/test_usage.py` with 4 test classes (TestSaveAgentUsage, TestGetAgentUsage, TestMigration, TestCascade)
