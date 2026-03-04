# Tasks: Knowledge Base Module

**Input**: Design documents from `/specs/005-knowledge-base/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — spec explicitly requires full test suite passing (SC-004) and lists test files in plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Package Structure)

**Purpose**: Create the knowledge module package and test directory structure

- [x] T001 Create knowledge package directory structure: `backend/ac_engineer/knowledge/` with empty `__init__.py`, and `backend/ac_engineer/knowledge/docs/` directory
- [x] T002 Create test package directory structure: `backend/tests/knowledge/` with empty `__init__.py`

---

## Phase 2: Foundational (Model + Loader + Domain Documents)

**Purpose**: Core infrastructure that ALL user stories depend on — the KnowledgeFragment model, document parser/validator/cache, all 10 domain documents, and shared test fixtures

**CRITICAL**: No user story work can begin until this phase is complete

### Core Infrastructure

- [x] T003 Implement KnowledgeFragment Pydantic model in `backend/ac_engineer/knowledge/models.py` — 4 fields: source_file (str), section_title (str), content (str), tags (list[str]). Pydantic v2 BaseModel. source_file and section_title must be non-empty (use min_length=1 or field validators). content can be empty. tags defaults to empty list.
- [x] T004 Implement document loader in `backend/ac_engineer/knowledge/loader.py` — REQUIRED_SECTIONS constant listing the 4 required H2 headings ("Physical Principles", "Adjustable Parameters and Effects", "Telemetry Diagnosis", "Cross-References"). Functions: parse_document(path: Path) -> dict[str, str] splits Markdown by `## ` headings into section_title→content dict; validate_document(sections: dict[str, str]) -> list[str] returns missing required sections; load_all_documents(docs_dir: Path | None = None) -> dict[str, dict[str, str]] scans docs/ and docs/user/ for .md files, parses and validates each, logs warnings for invalid docs and excludes them from results; get_docs_cache() -> dict[str, dict[str, str]] implements lazy singleton cache via module-level _cache variable, calls load_all_documents on first use. Default docs_dir is the docs/ directory relative to this file.

### Domain Documents (all parallelizable — each is a standalone Markdown file)

Each document MUST follow the 4-section structure with H1 title and 4 H2 sections. Content must be car-agnostic, informational only (no decision logic like "if X then do Y"), and written in English. See FR-001 in spec.md for required topics per document.

- [x] T005 [P] Write `backend/ac_engineer/knowledge/docs/vehicle_balance_fundamentals.md` — weight transfer basics (lateral and longitudinal), understeer/oversteer gradient (slip angle ratio explanation), balance by corner phase (entry/mid-corner/exit), neutral steer concept, load sensitivity. Cross-ref: suspension_and_springs, alignment, aero_balance, tyre_dynamics.
- [x] T006 [P] Write `backend/ac_engineer/knowledge/docs/tyre_dynamics.md` — slip angle theory and optimal slip window, traction circle/friction ellipse, thermal model (core vs surface, inner/mid/outer zones), pressure effects on contact patch shape and grip, wear mechanisms (thermal and mechanical degradation). Cross-ref: vehicle_balance_fundamentals, alignment, suspension_and_springs.
- [x] T007 [P] Write `backend/ac_engineer/knowledge/docs/suspension_and_springs.md` — spring rate effects on load transfer speed, ride height and its mechanical effects on geometry/grip, anti-roll bars (front/rear distribution, roll stiffness ratio), natural frequency and ride quality, motion ratio. Cross-ref: vehicle_balance_fundamentals, dampers, alignment.
- [x] T008 [P] Write `backend/ac_engineer/knowledge/docs/dampers.md` — bump vs rebound distinction, slow-speed vs fast-speed damping, damper velocity histograms and what they reveal, transient vs steady-state load transfer control, damper effect on tyre contact patch loading. Cross-ref: suspension_and_springs, vehicle_balance_fundamentals, tyre_dynamics.
- [x] T009 [P] Write `backend/ac_engineer/knowledge/docs/alignment.md` — camber angle geometry and contact patch optimization, toe effects on straight-line stability vs turn-in response vs tyre wear, caster angle and mechanical trail, tyre temperature distribution across inner/mid/outer as diagnostic for camber/pressure. Cross-ref: tyre_dynamics, suspension_and_springs, vehicle_balance_fundamentals.
- [x] T010 [P] Write `backend/ac_engineer/knowledge/docs/aero_balance.md` — downforce generation (wings, diffuser, body), drag and drag-downforce trade-off, front/rear aero balance and speed-dependent handling, ride height sensitivity (ground effect), aero map concept (downforce vs ride height vs speed). Cross-ref: vehicle_balance_fundamentals, suspension_and_springs, setup_methodology.
- [x] T011 [P] Write `backend/ac_engineer/knowledge/docs/braking.md` — brake bias front/rear distribution, engine braking contribution and its rear-axle effect, brake temperature management and fade, trail braking technique and weight transfer during corner entry, ABS interaction. Cross-ref: vehicle_balance_fundamentals, tyre_dynamics, drivetrain.
- [x] T012 [P] Write `backend/ac_engineer/knowledge/docs/drivetrain.md` — LSD types (1-way, 1.5-way, 2-way), preload effect on initial turn-in, power/coast ramp angles and their corner-phase effects, gear ratio selection (acceleration vs top speed vs keeping engine in power band), final drive ratio trade-offs. Cross-ref: vehicle_balance_fundamentals, braking, tyre_dynamics.
- [x] T013 [P] Write `backend/ac_engineer/knowledge/docs/telemetry_and_diagnosis.md` — how to read each telemetry channel category (inputs, dynamics, tyres, suspension), driver input analysis patterns (throttle application, brake trace, steering smoothness), symptom-to-cause diagnosis table mapping observable symptoms to possible causes and which telemetry channels to inspect. Cross-ref: all other documents.
- [x] T014 [P] Write `backend/ac_engineer/knowledge/docs/setup_methodology.md` — baseline setup process (start from known good), one-variable-at-a-time principle, session planning (what to test and how many laps), change validation (comparing before/after with telemetry), iterative refinement workflow. Cross-ref: telemetry_and_diagnosis, vehicle_balance_fundamentals.

### Shared Test Fixtures

- [x] T015 Create shared test fixtures in `backend/tests/knowledge/conftest.py` — Builder functions (not fixtures): make_analyzed_session(**overrides) creates minimal AnalyzedSession with controllable fields (must import models from ac_engineer.analyzer.models); make_corner_metrics(**overrides) creates minimal CornerMetrics with configurable understeer_ratio; make_stint_metrics(**overrides) creates minimal StintMetrics with configurable trends (lap_time_slope, tyre_temp_slope). Named pytest fixtures: understeer_session (corners with understeer_ratio > 1.2), tyre_temp_session (temp_spread above threshold on some wheels), degradation_session (positive lap_time_slope in stint trends), clean_session (all metrics within normal ranges — no signals should fire). Follow the make_* builder pattern from existing conftest.py files in parser/ and analyzer/ tests.

### Validation Tests (US3 — depends only on model + loader above)

- [x] T016 [P] [US3] Write loader and validation tests in `backend/tests/knowledge/test_loader.py` — test_parse_document_extracts_sections (parse a well-formed test .md → returns dict with 4 sections), test_parse_document_content_correct (parsed section content matches expected text), test_validate_document_all_present (4-section dict → empty missing list), test_validate_document_missing_section (dict missing "Telemetry Diagnosis" → returns ["Telemetry Diagnosis"]), test_validate_document_missing_multiple (dict missing 2 sections → returns both names), test_load_all_bundled_documents_valid (load real docs/ directory → all 10 domain docs + 2 templates pass validation, total 12 files), test_load_excludes_invalid_document (create temp dir with one valid and one invalid .md → only valid one in result), test_load_empty_directory (empty temp dir → empty dict result, no crash), test_load_nonexistent_directory (nonexistent path → empty dict result, no crash), test_cache_returns_same_object (two calls to get_docs_cache → same dict object returned), test_parse_empty_sections (doc with valid headings but empty content → sections with empty string values), test_documents_load_under_one_second (time the load of all bundled docs → assert < 1.0 seconds).
- [x] T017 [P] [US3] Write model tests in `backend/tests/knowledge/test_models.py` — test_fragment_creation (create KnowledgeFragment with all fields → fields accessible), test_fragment_empty_content (content="" is valid), test_fragment_empty_tags (tags=[] is valid), test_fragment_immutability (frozen=True if configured, or test that fields are set correctly), test_fragment_source_file_required (empty source_file → ValidationError), test_fragment_section_title_required (empty section_title → ValidationError).

**Checkpoint**: Foundation ready — KnowledgeFragment model works, loader can parse/validate/cache all 12 documents, all domain documents exist with correct structure, validation is thoroughly tested (SC-003, SC-007), test fixtures are available for all stories.

---

## Phase 3: User Story 1 — Signal-Based Knowledge Retrieval (Priority: P1) MVP

**Goal**: Given an AnalyzedSession, detect problematic conditions and return relevant knowledge fragments from the domain documents.

**Independent Test**: Construct mock sessions with known signal patterns (high understeer, tyre temp spread, lap degradation) and verify the correct documents/sections are returned.

### Implementation for User Story 1

- [x] T018 [US1] Define KNOWLEDGE_INDEX in `backend/ac_engineer/knowledge/index.py` — dict mapping each of the 10 document filenames to their 4 section titles, each section with a curated list of keyword tags (see data-model.md for example structure). Tags should cover the key technical terms in each section. Include tags that match the vocabulary used in the documents (e.g., "weight transfer", "understeer", "slip angle", "anti-roll bar", "camber", "brake bias", "differential", "preload"). Do NOT include template files in the index.
- [x] T019 [US1] Define SIGNAL_MAP in `backend/ac_engineer/knowledge/index.py` — dict mapping signal names to lists of (document_filename, section_title) tuples. Signal names: high_understeer, high_oversteer, tyre_temp_spread_high, tyre_temp_imbalance, lap_time_degradation, high_slip_angle, suspension_bottoming, low_consistency, brake_balance_issue, tyre_wear_rapid. Each signal should map to 3-6 relevant (doc, section) pairs. See data-model.md SIGNAL_MAP example for high_understeer and tyre_temp_spread_high mappings. Ensure acceptance scenarios from spec are satisfiable: understeer→vehicle_balance_fundamentals+suspension_and_springs+alignment; temp_spread→tyre_dynamics+alignment+suspension_and_springs; degradation→tyre_dynamics+vehicle_balance_fundamentals+setup_methodology.
- [x] T020 [US1] Implement signal detector functions in `backend/ac_engineer/knowledge/signals.py` — Module-level threshold constants: UNDERSTEER_THRESHOLD (1.2), OVERSTEER_THRESHOLD, TEMP_SPREAD_THRESHOLD, TEMP_BALANCE_THRESHOLD, LAP_TIME_SLOPE_THRESHOLD, SLIP_ANGLE_THRESHOLD, CONSISTENCY_THRESHOLD, and any others needed. Main function: detect_signals(session: AnalyzedSession) -> list[str] runs all detectors and returns list of signal names that fired. Private detector functions: _check_understeer, _check_oversteer, _check_tyre_temp_spread, _check_tyre_temp_imbalance, _check_lap_time_degradation, _check_high_slip_angle, _check_suspension_bottoming, _check_low_consistency, _check_brake_balance, _check_tyre_wear. Each receives the session, inspects relevant fields from AnalyzedSession model (see data-model.md R2 table for field mappings), handles None/missing/empty gracefully (return False), returns bool.
- [x] T021 [US1] Implement get_knowledge_for_signals in `backend/ac_engineer/knowledge/__init__.py` — Import detect_signals from signals, SIGNAL_MAP from index, get_docs_cache from loader, KnowledgeFragment from models. Function signature: get_knowledge_for_signals(session: AnalyzedSession) -> list[KnowledgeFragment]. Logic: (1) call detect_signals(session) to get signal names, (2) for each signal, look up (doc, section) pairs in SIGNAL_MAP, (3) collect unique (doc, section) pairs (set-based dedup), (4) for each pair, load content from get_docs_cache(), look up tags from KNOWLEDGE_INDEX, build KnowledgeFragment, (5) return list. Never raises — return empty list if no signals or missing data. Also re-export KnowledgeFragment in __all__.
- [x] T022 [P] [US1] Write signal detector tests in `backend/tests/knowledge/test_signals.py` — Test each detector function via detect_signals(): test_understeer_detected (understeer_session fixture → "high_understeer" in result), test_no_signals_clean_session (clean_session fixture → empty list), test_tyre_temp_spread_detected (tyre_temp_session → "tyre_temp_spread_high" in result), test_lap_time_degradation_detected (degradation_session → "lap_time_degradation" in result), test_none_fields_no_crash (session with None corners/stints/consistency → empty list, no exception), test_empty_laps_no_crash (session with empty laps list → empty list).
- [x] T023 [P] [US1] Write integration tests for signal-based retrieval in `backend/tests/knowledge/test_integration.py` — test_understeer_returns_balance_fragments (understeer_session → fragments include vehicle_balance_fundamentals, suspension_and_springs, alignment sources), test_tyre_temp_returns_tyre_fragments (tyre_temp_session → fragments include tyre_dynamics, alignment), test_degradation_returns_methodology_fragments (degradation_session → fragments include tyre_dynamics, vehicle_balance_fundamentals, setup_methodology), test_clean_session_returns_empty (clean_session → empty list), test_deduplication (session triggering multiple signals pointing to same doc/section → no duplicate fragments, verified by checking uniqueness of (source_file, section_title) pairs), test_fragments_have_content (all returned fragments have non-empty content field), test_fragments_have_tags (fragments from indexed docs have non-empty tags list).

**Checkpoint**: Signal-based retrieval fully functional — SC-001 and SC-005 verifiable. MVP complete.

---

## Phase 4: User Story 2 — Keyword Search (Priority: P2)

**Goal**: Free-text search across knowledge base documents by keyword matching against content and index tags.

**Independent Test**: Call search_knowledge with known queries and verify correct documents/sections are returned.

### Implementation for User Story 2

- [x] T024 [US2] Implement keyword search in `backend/ac_engineer/knowledge/search.py` — Private function: _tokenize(text: str) -> list[str] lowercases, splits on non-alphanumeric characters (re.split), filters tokens shorter than 2 characters. Public function: search_knowledge(query: str) -> list[KnowledgeFragment] tokenizes query, then for each (doc, sections) pair in get_docs_cache(): for each section, compute score as number of query tokens found in either (a) the KNOWLEDGE_INDEX tags for that doc/section (if indexed) or (b) the section content text (case-insensitive). If score > 0, create KnowledgeFragment with tags from KNOWLEDGE_INDEX (or empty list if not indexed). Sort results by score descending. Return empty list for empty/whitespace query or no matches. Import KNOWLEDGE_INDEX from index, get_docs_cache from loader, KnowledgeFragment from models.
- [x] T025 [US2] Wire search_knowledge into public API in `backend/ac_engineer/knowledge/__init__.py` — Import search_knowledge from search module, add to __all__ list alongside get_knowledge_for_signals and KnowledgeFragment. Ensure `from ac_engineer.knowledge import search_knowledge` works.
- [x] T026 [US2] Write keyword search tests in `backend/tests/knowledge/test_search.py` — test_search_anti_roll_bar_oversteer (query "rear anti-roll bar oversteer" → at least one fragment from suspension_and_springs.md or vehicle_balance_fundamentals.md), test_search_camber_tyre_temperature (query "camber tyre temperature" → fragments from alignment.md covering camber), test_search_brake_bias (query "brake bias" → fragments from braking.md, NOT from unrelated docs), test_search_nonsense_returns_empty (query "xyzzy foobar" → empty list), test_search_empty_query_returns_empty (query "" → empty list), test_search_whitespace_only_returns_empty (query "   " → empty list), test_search_results_ranked_by_relevance (query with multiple matching tokens → first result has highest score), test_search_case_insensitive (query "BRAKE BIAS" returns same results as "brake bias").

**Checkpoint**: Keyword search fully functional — SC-002 and SC-006 verifiable.

---

## Phase 5: User Story 4 — User-Editable Templates (Priority: P4)

**Goal**: Provide car-specific and track-specific templates that users can fill in; user documents are discovered and indexed alongside bundled documents.

**Independent Test**: Place a filled-in template in docs/user/, load knowledge base, verify it appears in search results.

### Implementation for User Story 4

- [x] T027 [P] [US4] Write car-specific template in `backend/ac_engineer/knowledge/docs/car_template.md` — H1 title "[Car Name] — Specific Notes", then 4 H2 sections with placeholder guidance: Physical Principles (e.g., "engine placement: front/mid/rear", "drivetrain: FWD/RWD/AWD", "aero presence: high/low/none", "mechanical vs aero grip ratio"), Adjustable Parameters and Effects (e.g., "unique parameters for this car", "known parameter sensitivities"), Telemetry Diagnosis (e.g., "specific telemetry patterns for this car", "known quirks or data anomalies"), Cross-References (e.g., "related documents for this car's characteristics").
- [x] T028 [P] [US4] Write track-specific template in `backend/ac_engineer/knowledge/docs/track_template.md` — H1 title "[Track Name] — Specific Notes", then 4 H2 sections with placeholder guidance: Physical Principles (e.g., "surface grip level", "elevation changes", "ambient conditions effects"), Adjustable Parameters and Effects (e.g., "setup priorities for this track", "key compromises"), Telemetry Diagnosis (e.g., "key corners to analyze", "reference lap times and sector targets"), Cross-References (e.g., "relevant setup domains for this track").
- [x] T029 [US4] Create user documents directory `backend/ac_engineer/knowledge/docs/user/` with `.gitkeep` file, and add `backend/ac_engineer/knowledge/docs/user/*.md` pattern to the project `.gitignore` (keeping .gitkeep tracked). Verify that loader.py already scans docs/user/ — if not, update load_all_documents to include that path.
- [x] T030 [US4] Write template integration test in `backend/tests/knowledge/test_integration.py` (append to existing file) — test_user_document_discovered (create a filled-in car template in a tmp docs/user/ dir, call load_all_documents with that docs dir → user doc appears in results), test_user_document_searchable (place filled-in template with specific keywords, call search_knowledge → fragments from user doc are returned), test_templates_pass_validation (load car_template.md and track_template.md → both pass validate_document).

**Checkpoint**: Templates and user document discovery fully functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories, verify all success criteria

- [x] T031 Write index validation tests in `backend/tests/knowledge/test_index.py` — test_knowledge_index_references_valid_documents (every key in KNOWLEDGE_INDEX is a .md filename that exists in docs/), test_knowledge_index_references_valid_sections (every section name in KNOWLEDGE_INDEX matches one of the 4 REQUIRED_SECTIONS), test_signal_map_references_valid_documents (every (doc, section) tuple in SIGNAL_MAP references a doc in KNOWLEDGE_INDEX), test_signal_map_references_valid_sections (every section in SIGNAL_MAP tuples is a valid section name), test_all_documents_in_index (every domain .md file in docs/ except templates has an entry in KNOWLEDGE_INDEX), test_signal_map_covers_core_signals (SIGNAL_MAP contains at minimum: high_understeer, tyre_temp_spread_high, lap_time_degradation).
- [x] T032 Run full test suite and verify all 7 success criteria from spec.md — Execute `conda run -n ac-race-engineer pytest backend/tests/knowledge/ -v` and verify all tests pass. Cross-check: SC-001 (signal retrieval for understeer/temp/degradation), SC-002 (search "rear anti-roll bar oversteer"), SC-003 (all 12 docs validate), SC-004 (zero external deps), SC-005 (no duplicates), SC-006 (empty search for nonsense), SC-007 (load < 1 second). Fix any failures.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories. Includes US3 validation tests (depend only on model + loader).
- **US1 (Phase 3)**: Depends on Phase 2 (needs model, loader, documents, fixtures)
- **US2 (Phase 4)**: Depends on Phase 2 (needs model, loader, documents) + T018 from US1 (needs KNOWLEDGE_INDEX for tag matching)
- **US4 (Phase 5)**: Depends on Phase 2 (needs loader) + Phase 4 (template search test uses search_knowledge)
- **Polish (Phase 6)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on other stories
- **US2 (P2)**: Can start after Phase 2 + T018 (needs KNOWLEDGE_INDEX from US1)
- **US3 (P3)**: Completed within Phase 2 — tests only foundational code (model + loader)
- **US4 (P4)**: Can start after Phase 2 — templates are independent; search test depends on US2 (T030 depends on T024-T025)

### Within Each User Story

- Index before signals (US1: T018-T019 before T020)
- Implementation before tests (or parallel where marked [P])
- Core function before public API wiring

### Parallel Opportunities

- **Phase 2**: T005-T014 (all 10 documents) can run in parallel with each other. T003 and T004 can run in parallel. T016 and T017 (US3 validation tests) can run in parallel once T003-T004 are done.
- **Phase 3**: T022 and T023 (tests) can run in parallel with each other once T020-T021 are done
- **Phase 5**: T027 and T028 (templates) can run in parallel

---

## Parallel Example: Phase 2 Documents

```
# All 10 domain documents can be written simultaneously:
T005: vehicle_balance_fundamentals.md
T006: tyre_dynamics.md
T007: suspension_and_springs.md
T008: dampers.md
T009: alignment.md
T010: aero_balance.md
T011: braking.md
T012: drivetrain.md
T013: telemetry_and_diagnosis.md
T014: setup_methodology.md
```

## Parallel Example: User Story 1

```
# After T018-T021 are done, tests can run in parallel:
T022: test_signals.py
T023: test_integration.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (model + loader + all documents + fixtures)
3. Complete Phase 3: User Story 1 (index + signals + get_knowledge_for_signals)
4. **STOP and VALIDATE**: Test signal-based retrieval independently
5. SC-001 and SC-005 should pass

### Incremental Delivery

1. Setup + Foundational (includes US3 validation tests) → Foundation ready (12 docs load and validate, SC-003/SC-007 pass)
2. Add US1 → Signal-based retrieval works → MVP!
3. Add US2 → Keyword search works → SC-002/SC-006 pass
4. Add US4 → Templates + user docs → Full feature complete
5. Polish → All SC-001 through SC-007 verified

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 32 (2 setup + 15 foundational [incl. 2 US3 validation tests] + 6 US1 + 3 US2 + 4 US4 + 2 polish)
