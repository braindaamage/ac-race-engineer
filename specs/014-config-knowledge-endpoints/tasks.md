# Tasks: Config, Knowledge & Packaging Endpoints

**Input**: Design documents from `/specs/014-config-knowledge-endpoints/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — this project mandates test coverage per constitution (Quality Gates).

**Organization**: Tasks grouped by user story. US1+US2 share the config route file and are both P1, so they are combined in Phase 3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Create the path resolution module that all other code depends on

- [ ] T001 Create centralized path resolution module with `get_data_dir()`, `get_db_path()`, `get_config_path()`, `get_sessions_dir()` — detecting dev vs frozen (PyInstaller) mode via `getattr(sys, 'frozen', False)` in `backend/api/paths.py`
- [ ] T002 Create path resolution tests — dev mode paths resolve relative to repo root, frozen mode (mocked `sys.frozen=True` + `sys.executable`) resolves relative to exe dir, all helpers return absolute `Path` objects in `backend/tests/api/test_paths.py`

**Checkpoint**: `paths.py` tested independently, provides correct paths in both dev and packaged modes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire centralized paths into the app lifespan and register new routers

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Modify `backend/api/main.py` — replace `DEFAULT_DB_PATH` and `DEFAULT_SESSIONS_DIR` with imports from `api.paths`, add `app.state.config_path` from `get_config_path()`, import and register config router (prefix `/config`) and knowledge router (no prefix — it has mixed prefixes), update lifespan to use centralized path functions
- [ ] T004 Update `backend/api/routes/engineer.py` — remove `DEFAULT_CONFIG_PATH` constant (line 40), replace `getattr(request.app.state, "config_path", DEFAULT_CONFIG_PATH)` with `request.app.state.config_path` in `run_engineer` (line 79), `apply_recommendation_endpoint` (line 257), and `send_message` (line 328)

**Checkpoint**: Server starts using centralized paths, existing tests still pass, `app.state.config_path` available to all routes

---

## Phase 3: User Story 1+2 — View, Update & Validate Configuration (Priority: P1)

**Goal**: User can view current config, partially update it, and validate it before running the engineer

**Independent Test**: GET returns config with "" for unset fields, PATCH updates only provided fields, validate reports per-field status

### Tests for User Story 1+2

- [ ] T005 [US1] Write config endpoint tests in `backend/tests/api/test_config_routes.py` — tests MUST cover: GET returns defaults with empty strings (never null), GET returns existing config values, PATCH single field leaves others unchanged, PATCH multiple fields at once, PATCH empty body returns current config unchanged, PATCH invalid llm_provider returns 422, PATCH unknown field returns 422, GET validate all valid (mock paths exist), GET validate missing AC path, GET validate missing setups path, GET validate empty config

### Implementation for User Story 1+2

- [ ] T006 [US1] Define response/request models in `backend/api/routes/config.py` — `ConfigResponse` (all `str`, never None), `ConfigUpdateRequest` (all `Optional[str]`, `extra="forbid"`), `ConfigValidationResponse` (`ac_path_valid`, `setups_path_valid`, `llm_provider_valid`, `is_valid` — all `bool`)
- [ ] T007 [US1] Implement `GET /config` in `backend/api/routes/config.py` — call `read_config(config_path)`, coerce `None` paths to `""` in response, coerce `None` llm_model to `""`
- [ ] T008 [US1] Implement `PATCH /config` in `backend/api/routes/config.py` — extract provided fields via `body.model_dump(exclude_unset=True)`, call `update_config(config_path, **fields)`, return updated config as `ConfigResponse` with same None-to-"" coercion
- [ ] T009 [US2] Implement `GET /config/validate` in `backend/api/routes/config.py` — call `read_config(config_path)`, check `config.is_ac_configured`, `config.is_setups_configured`, provider in valid list, compute `is_valid` as all-true

**Checkpoint**: Config endpoints fully functional — GET/PATCH/validate all work, 11+ tests passing

---

## Phase 4: User Story 3 — Search the Knowledge Base (Priority: P2)

**Goal**: User can search vehicle dynamics topics by keyword and get ranked results capped at 10

**Independent Test**: Search for "camber" returns relevant results, empty query returns [], results never exceed 10

### Tests for User Story 3

- [ ] T010 [US3] Write knowledge search tests in `backend/tests/api/test_knowledge_routes.py` — tests MUST cover: search with matching query returns results with source_file/section_title/content/tags, search with no-match query returns empty list, search with empty query returns empty list, search with whitespace-only query returns empty list, results capped at 10 with total reflecting unfiltered count, response includes query echo

### Implementation for User Story 3

- [ ] T011 [US3] Define knowledge response models in `backend/api/routes/knowledge.py` — `KnowledgeFragmentResponse` (`source_file`, `section_title`, `content`, `tags`), `KnowledgeSearchResponse` (`query`, `results: list[KnowledgeFragmentResponse]`, `total: int`)
- [ ] T012 [US3] Implement `GET /knowledge/search` in `backend/api/routes/knowledge.py` — read `q` query param, call `search_knowledge(q)`, slice first 10, return `KnowledgeSearchResponse` with total = len(all_results)

**Checkpoint**: Knowledge search works — queries return ranked, capped results, 6+ tests passing

---

## Phase 5: User Story 4 — Session Knowledge Fragments (Priority: P2)

**Goal**: User can see which knowledge fragments the engineer consulted for a specific session's signals

**Independent Test**: Request fragments for an analyzed session, verify signals list and fragments correspond to detected signals

### Tests for User Story 4

- [ ] T013 [US4] Write session knowledge tests in `backend/tests/api/test_knowledge_routes.py` — tests MUST cover: returns fragments for analyzed session (mock AnalyzedSession + cache), returns fragments for engineered session, returns 404 for nonexistent session, returns 409 for discovered (unanalyzed) session, returns 409 with re-process message when cache missing, returns signals list alongside fragments, returns empty signals/fragments when no signals detected

### Implementation for User Story 4

- [ ] T014 [US4] Add `SessionKnowledgeResponse` model in `backend/api/routes/knowledge.py` — fields: `session_id: str`, `signals: list[str]`, `fragments: list[KnowledgeFragmentResponse]`
- [ ] T015 [US4] Implement `GET /sessions/{session_id}/knowledge` in `backend/api/routes/knowledge.py` — guard: 404 if session not in DB, 409 if state not in ("analyzed", "engineered"), load AnalyzedSession via `load_analyzed_session()`, 409 if cache missing, run `detect_signals()`, call `get_knowledge_for_signals()`, return response with signals and fragments

**Checkpoint**: Session knowledge endpoint works — returns signals + fragments for analyzed sessions, guards reject invalid states, 7+ tests passing

---

## Phase 6: User Story 5 — Packaging Verification (Priority: P3)

**Goal**: Document and verify the PyInstaller build process so Phase 7 can package the server as a standalone .exe

**Independent Test**: Build docs are complete, spec file references correct entry point and data files

- [ ] T016 [P] [US5] Create PyInstaller spec file in `build/ac_engineer.spec` — entry point `backend/api/server.py`, include data files (`backend/ac_engineer/knowledge/docs/`, `backend/ac_engineer/engineer/skills/`), hidden imports (`pydantic_ai`, `anthropic`, `openai`, `watchdog`, `google.generativeai`), recommend `--onedir` mode
- [ ] T017 [P] [US5] Create build documentation in `build/README_build.md` — prerequisites (conda env, PyInstaller install), step-by-step build commands for both `--onedir` and `--onefile`, expected output structure, how Tauri launches the sidecar, troubleshooting common issues (missing hidden imports, data files not found)

**Checkpoint**: Build artifacts documented, developer can follow README to produce a working .exe

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [ ] T018 Run full test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) and verify all existing + new tests pass
- [ ] T019 Verify server starts from a non-project working directory (e.g., `cd /tmp && python -m api.server`) and all endpoints respond correctly
- [ ] T020 Run quickstart.md manual validation — test each curl command listed in `specs/014-config-knowledge-endpoints/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1+US2 Config)**: Depends on Phase 2
- **Phase 4 (US3 Knowledge Search)**: Depends on Phase 2 — can run in parallel with Phase 3
- **Phase 5 (US4 Session Knowledge)**: Depends on Phase 2 — can run in parallel with Phase 3
- **Phase 6 (US5 Packaging)**: Depends on Phase 1 (paths.py) — can run in parallel with Phases 3-5
- **Phase 7 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (Config)**: Independent — only needs `ac_engineer.config` (exists)
- **US3 (Knowledge Search)**: Independent — only needs `ac_engineer.knowledge.search_knowledge` (exists)
- **US4 (Session Knowledge)**: Independent — needs `api.analysis.cache` (exists) + `ac_engineer.knowledge` (exists)
- **US5 (Packaging)**: Independent — documentation task, references `api/paths.py` from Phase 1

### Within Each User Story

- Tests written first (fail before implementation)
- Response models before endpoint handlers
- Core endpoint before edge case handling

### Parallel Opportunities

**Phase 3+4 in parallel** (different route files):
```
Task: T005-T009 (config routes + tests) — backend/api/routes/config.py
Task: T010-T012 (knowledge search + tests) — backend/api/routes/knowledge.py
```

**Phase 6 tasks in parallel** (independent files):
```
Task: T016 (PyInstaller spec) — build/ac_engineer.spec
Task: T017 (build docs) — build/README_build.md
```

---

## Implementation Strategy

### MVP First (User Stories 1+2 Only)

1. Complete Phase 1: Setup (paths.py)
2. Complete Phase 2: Foundational (main.py wiring)
3. Complete Phase 3: Config endpoints (GET/PATCH/validate)
4. **STOP and VALIDATE**: Config endpoints work end-to-end
5. Desktop app can already manage settings

### Incremental Delivery

1. Phases 1+2 → Foundation ready
2. Phase 3 (Config) → Settings management works → **MVP**
3. Phase 4 (Knowledge Search) → Educational search works
4. Phase 5 (Session Knowledge) → Transparency into engineer reasoning
5. Phase 6 (Packaging) → Build docs ready for Phase 7
6. Phase 7 (Polish) → Full validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1+US2 combined because they share `routes/config.py` and are both P1
- Total: 20 tasks (2 setup, 2 foundational, 5 config, 3 knowledge search, 3 session knowledge, 2 packaging, 3 polish)
- Expected test count: ~24 tests (11 config + 6 search + 7 session knowledge)
- No new pip dependencies required
