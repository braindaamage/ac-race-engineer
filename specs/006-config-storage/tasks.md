# Tasks: Config + Storage (Phase 5.1)

**Input**: Design documents from `/specs/006-config-storage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — spec targets ~40 tests across 4 test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package directories, `__init__.py` files, and empty module files per plan.md structure.

- [ ] T001 Create config package structure: `backend/ac_engineer/config/__init__.py`, `backend/ac_engineer/config/models.py`, `backend/ac_engineer/config/io.py`
- [ ] T002 Create storage package structure: `backend/ac_engineer/storage/__init__.py`, `backend/ac_engineer/storage/models.py`, `backend/ac_engineer/storage/db.py`, `backend/ac_engineer/storage/sessions.py`, `backend/ac_engineer/storage/recommendations.py`, `backend/ac_engineer/storage/messages.py`
- [ ] T003 [P] Create test directories: `backend/tests/config/__init__.py`, `backend/tests/config/conftest.py`, `backend/tests/storage/__init__.py`, `backend/tests/storage/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Models and database init that ALL user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Implement ACConfig Pydantic v2 model in `backend/ac_engineer/config/models.py` — 4 stored fields (ac_install_path: Path|None, setups_path: Path|None, llm_provider: str="anthropic", llm_model: str|None), llm_provider validator (must be "anthropic"|"openai"|"gemini"), empty-string-to-None coercion, 4 computed properties (ac_cars_path, ac_tracks_path, is_ac_configured, is_setups_configured), Path serialization as strings in JSON
- [ ] T005 [P] Implement storage models in `backend/ac_engineer/storage/models.py` — SessionRecord, Recommendation, SetupChange, Message per data-model.md, with Field constraints
- [ ] T006 [P] Implement LLM_MODEL_DEFAULTS constant and get_effective_model() function in `backend/ac_engineer/config/io.py` — returns config.llm_model if set, else provider default from dict
- [ ] T007 Implement init_db() and _connect() helper in `backend/ac_engineer/storage/db.py` — CREATE TABLE IF NOT EXISTS for all 4 tables per data-model.md SQLite schema, PRAGMA foreign_keys=ON, PRAGMA journal_mode=WAL, idempotent

**Checkpoint**: All models defined, database can be initialized — user story implementation can begin.

---

## Phase 3: User Story 1 — Configure AC Installation Path (Priority: P1) MVP

**Goal**: Users can set/read/update the AC installation path and have it survive restarts. Corrupt/missing config never crashes.

**Independent Test**: Write config with AC path, read it back, verify persistence. Corrupt the file, read again, verify defaults returned.

### Tests for User Story 1

- [ ] T008 [P] [US1] Write config model tests in `backend/tests/config/test_models.py` — test ACConfig defaults, llm_provider validator (valid values + ValueError on invalid), empty-string-to-None coercion, Path serialization round-trip, computed properties (ac_cars_path, ac_tracks_path, is_ac_configured, is_setups_configured with real and non-existent paths). Target: ~10 tests.
- [ ] T009 [P] [US1] Write config I/O tests in `backend/tests/config/test_io.py` — test write_config + read_config round-trip, read_config on missing file returns defaults, read_config on corrupt JSON returns defaults, read_config on invalid types returns defaults, atomic write (verify .tmp not left behind), update_config partial update preserves other fields, update_config with unknown field raises ValueError, get_effective_model with explicit model, get_effective_model with default per provider. Use tmp_path fixture. Target: ~12 tests.

### Implementation for User Story 1

- [ ] T010 [US1] Implement read_config() in `backend/ac_engineer/config/io.py` — read JSON file, validate via ACConfig.model_validate(), never raise (catch all exceptions, log warning, return ACConfig())
- [ ] T011 [US1] Implement write_config() in `backend/ac_engineer/config/io.py` — serialize ACConfig to JSON (paths as strings), write to .tmp file, os.replace() to final path, create parent dirs if needed
- [ ] T012 [US1] Implement update_config() in `backend/ac_engineer/config/io.py` — read current config (via read_config), apply **kwargs via model_copy(update=...), write back atomically, raise ValueError for unknown fields, return updated ACConfig
- [ ] T013 [US1] Wire config public API in `backend/ac_engineer/config/__init__.py` — import and re-export ACConfig, read_config, write_config, update_config, get_effective_model, LLM_MODEL_DEFAULTS in __all__
- [ ] T014 [US1] Write conftest fixtures in `backend/tests/config/conftest.py` — config_path(tmp_path) fixture returning tmp_path/"config.json", sample_config() fixture returning a populated ACConfig

**Checkpoint**: Config module fully functional — read/write/update with atomic writes and corruption recovery.

---

## Phase 4: User Story 2 — Choose AI Provider (Priority: P1)

**Goal**: Users can set LLM provider/model, provider is validated, get_effective_model resolves defaults.

**Independent Test**: Already covered by T008 (provider validator) and T009 (get_effective_model). No additional tasks needed — this story is satisfied by the config module implemented in US1.

*Note: US2 is fully covered by the ACConfig model (llm_provider field with validator, llm_model field) and get_effective_model() function already implemented in Phase 3. No separate tasks required.*

**Checkpoint**: Provider selection and model resolution work correctly.

---

## Phase 5: User Story 3 — Browse Past Sessions (Priority: P2)

**Goal**: Users can save, list (ordered by date DESC), filter by car, and retrieve sessions by ID.

**Independent Test**: Save 3 sessions with different cars/tracks/dates, list all (verify order), filter by car, get by ID.

### Tests for User Story 3

- [ ] T015 [US3] Write session storage tests in `backend/tests/storage/test_sessions.py` — test save_session insert, save_session upsert (update existing), list_sessions empty db returns [], list_sessions ordering (most recent first), list_sessions filter by car, list_sessions filter no matches returns [], get_session found, get_session not found returns None, cascade delete (save session with recommendation and message, delete session, verify both recommendation and message are also deleted). Use tmp_path + init_db fixture. Target: ~9 tests.
- [ ] T015b [P] [US3] Write database initialization tests in `backend/tests/storage/test_db.py` — test init_db() is idempotent (safe to call twice), connection has foreign_keys=ON (verify with PRAGMA query), connection has WAL journal mode. Use tmp_path fixture. Target: ~3 tests.

### Implementation for User Story 3

- [ ] T016 [US3] Implement save_session() in `backend/ac_engineer/storage/sessions.py` — INSERT OR REPLACE (upsert) using _connect() helper
- [ ] T017 [US3] Implement list_sessions() in `backend/ac_engineer/storage/sessions.py` — SELECT with ORDER BY session_date DESC, optional WHERE car=? filter, return list[SessionRecord]
- [ ] T018 [US3] Implement get_session() in `backend/ac_engineer/storage/sessions.py` — SELECT WHERE session_id=?, return SessionRecord or None
- [ ] T019 [US3] Write conftest fixtures in `backend/tests/storage/conftest.py` — db_path(tmp_path) fixture that creates tmp db and runs init_db(), sample_session() builder returning SessionRecord with overrides

**Checkpoint**: Sessions CRUD fully functional and tested.

---

## Phase 6: User Story 4 — Track Engineer Recommendations (Priority: P2)

**Goal**: Users can save recommendations with setup changes, retrieve them per session, and update status (proposed→applied/rejected).

**Independent Test**: Save a recommendation with 2 changes, retrieve it, verify changes populated, update status to applied.

### Tests for User Story 4

- [ ] T020 [US4] Write recommendation storage tests in `backend/tests/storage/test_recommendations.py` — test save_recommendation creates with status "proposed" and auto-generated IDs, save_recommendation with invalid session_id raises ValueError, get_recommendations returns all with changes populated, get_recommendations empty returns [], update_recommendation_status to "applied", update_recommendation_status to "rejected", update_recommendation_status invalid recommendation_id raises ValueError, update_recommendation_status invalid status value raises ValueError. Target: ~8 tests.

### Implementation for User Story 4

- [ ] T021 [US4] Implement save_recommendation() in `backend/ac_engineer/storage/recommendations.py` — generate recommendation_id (uuid4 hex), set status="proposed" and created_at, INSERT recommendation row, generate change_id for each SetupChange and INSERT into setup_changes, return populated Recommendation. Wrap in transaction. Raise ValueError if session_id not in sessions.
- [ ] T022 [US4] Implement get_recommendations() in `backend/ac_engineer/storage/recommendations.py` — SELECT recommendations WHERE session_id, for each SELECT its setup_changes, assemble Recommendation objects with changes list, ORDER BY created_at ASC
- [ ] T023 [US4] Implement update_recommendation_status() in `backend/ac_engineer/storage/recommendations.py` — validate status is "applied" or "rejected", UPDATE WHERE recommendation_id, raise ValueError if not found or invalid status

**Checkpoint**: Recommendations CRUD with setup changes fully functional and tested.

---

## Phase 7: User Story 5 — Continue Engineer Conversations (Priority: P3)

**Goal**: Users can save messages per session, retrieve in chronological order, and clear conversation.

**Independent Test**: Save 3 messages (alternating user/assistant), retrieve them, verify order, clear and verify empty.

### Tests for User Story 5

- [ ] T024 [US5] Write message storage tests in `backend/tests/storage/test_messages.py` — test save_message creates with auto-generated ID and timestamp, save_message with invalid session_id raises ValueError, save_message with invalid role raises ValueError, get_messages returns chronological order, get_messages empty returns [], clear_messages deletes only target session's messages (not other sessions'), clear_messages returns count of deleted messages. Target: ~7 tests.

### Implementation for User Story 5

- [ ] T025 [US5] Implement save_message() in `backend/ac_engineer/storage/messages.py` — generate message_id (uuid4 hex), set created_at, validate role in ("user","assistant"), INSERT into messages, raise ValueError if session_id not in sessions or invalid role, return populated Message
- [ ] T026 [US5] Implement get_messages() in `backend/ac_engineer/storage/messages.py` — SELECT WHERE session_id ORDER BY created_at ASC, return list[Message]
- [ ] T027 [US5] Implement clear_messages() in `backend/ac_engineer/storage/messages.py` — DELETE WHERE session_id, return rowcount

**Checkpoint**: Conversation persistence fully functional and tested.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Wire up storage public API, verify all tests pass, validate quickstart scenarios.

- [ ] T028 Wire storage public API in `backend/ac_engineer/storage/__init__.py` — import and re-export all CRUD functions + models in __all__ per contracts/storage-api.md
- [ ] T029 Run full test suite (`pytest backend/tests/ -v`) and verify all ~40 new tests pass alongside existing 334 tests
- [ ] T030 Validate quickstart.md scenarios work end-to-end against tmp_path databases

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: No additional work — covered by US1 implementation
- **US3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1
- **US4 (Phase 6)**: Depends on Phase 5 (needs sessions table for FK)
- **US5 (Phase 7)**: Depends on Phase 5 (needs sessions table for FK)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 + US2 (Config)**: Independent of storage stories. Can start immediately after Phase 2.
- **US3 (Sessions)**: Independent of config. Can start immediately after Phase 2.
- **US4 (Recommendations)**: Depends on US3 (session records must exist for FK).
- **US5 (Messages)**: Depends on US3 (session records must exist for FK). Can run in parallel with US4.

### Within Each User Story

- Tests written first (TDD)
- Models before query functions
- Query functions before public API wiring
- Conftest fixtures can be written in parallel with tests

### Parallel Opportunities

Within Phase 2 (Foundational):
```
T004 (ACConfig model)  ||  T005 (storage models)  ||  T006 (get_effective_model)
         └──────────────────────┬────────────────────────────┘
                                T007 (init_db)
```

Config (US1) and Sessions (US3) can run in parallel after Phase 2:
```
         Phase 2 complete
              ├── US1: T008-T014 (config)
              └── US3: T015-T019 (sessions)
                          ├── US4: T020-T023 (recommendations)
                          └── US5: T024-T027 (messages)  [parallel with US4]
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (models + init_db)
3. Complete Phase 3: US1 (config read/write/update)
4. **STOP and VALIDATE**: Run `pytest backend/tests/config/ -v` — all ~22 tests pass
5. Config module is independently useful

### Incremental Delivery

1. Setup + Foundational → Models and DB ready
2. US1 + US2 (Config) → Test independently → Config works
3. US3 (Sessions) → Test independently → Session index works
4. US4 (Recommendations) → Test independently → Recommendation tracking works
5. US5 (Messages) → Test independently → Conversation persistence works
6. Polish → Full suite passes alongside existing 334 tests

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests use `tmp_path` fixture — never touch `data/`
- Target: ~49 tests (10 model + 12 I/O + 3 db init + 9 sessions + 8 recommendations + 7 messages)
- Commit after each phase checkpoint
- Stop at any checkpoint to validate story independently
