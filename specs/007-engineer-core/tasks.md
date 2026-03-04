# Tasks: Engineer Core (Deterministic Layer)

**Input**: Design documents from `/specs/007-engineer-core/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/public-api.md

**Tests**: Included — spec targets ~54 tests across 4 test modules. TDD approach: write tests first, then implement.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package structure and shared test fixtures

- [x] T001 Create engineer package directory structure: `backend/ac_engineer/engineer/__init__.py`, `backend/ac_engineer/engineer/models.py`, `backend/ac_engineer/engineer/summarizer.py`, `backend/ac_engineer/engineer/setup_reader.py`, `backend/ac_engineer/engineer/setup_writer.py`
- [x] T002 Create test package directory structure: `backend/tests/engineer/__init__.py`, `backend/tests/engineer/conftest.py`, `backend/tests/engineer/test_models.py`, `backend/tests/engineer/test_summarizer.py`, `backend/tests/engineer/test_setup_reader.py`, `backend/tests/engineer/test_setup_writer.py`
- [x] T003 Implement shared test fixtures in `backend/tests/engineer/conftest.py`: fixture `sample_metadata` returning a SessionMetadata, fixture `make_analyzed_lap` factory that builds an AnalyzedLap with configurable classification/metrics/corners, fixture `make_analyzed_session` factory that builds an AnalyzedSession with configurable laps/stints/consistency, fixture `sample_config` returning an ACConfig with a tmp_path ac_install_path, fixture `sample_setup_ini` that writes a multi-section setup .ini file to tmp_path, fixture `sample_car_data_dir` that creates a car's `data/setup.ini` with parameter ranges in tmp_path

**Checkpoint**: Package structure ready, shared fixtures available for all test modules

---

## Phase 2: Foundational (Pydantic v2 Models)

**Purpose**: Define all data models used across all user stories — MUST be complete before any story implementation

**⚠️ CRITICAL**: All user stories depend on these models

- [x] T004 Implement summary models in `backend/ac_engineer/engineer/models.py`: LapSummary (lap_number, lap_time_s, gap_to_best_s, is_best, tyre_temp_avg_c, understeer_ratio_avg, peak_lat_g, peak_speed_kmh — with gap_to_best_s >= 0.0 validator), CornerIssue (corner_number, issue_type, severity as Literal["high","medium","low"], understeer_ratio, apex_speed_loss_pct, avg_lat_g, description), StintSummary (stint_index, flying_lap_count, lap_time_mean_s, lap_time_stddev_s, lap_time_trend as Literal["improving","degrading","stable"], lap_time_slope_s_per_lap, tyre_temp_slope_c_per_lap, setup_filename, setup_changes_from_prev as list[str] default []), SessionSummary (session_id, car_name, track_name, track_config, recorded_at, total_lap_count, flying_lap_count, best_lap_time_s, worst_lap_time_s, lap_time_stddev_s, avg_understeer_ratio, active_setup_filename, active_setup_parameters, laps as list[LapSummary], signals as list[str], corner_issues as list[CornerIssue], stints as list[StintSummary], tyre_temp_averages, tyre_pressure_averages, slip_angle_averages)
- [x] T005 Implement setup and validation models in `backend/ac_engineer/engineer/models.py`: ParameterRange (section, parameter, min_value, max_value, step, default_value — with min_value <= max_value validator and step > 0 validator), ValidationResult (section, parameter, proposed_value, clamped_value as float|None, is_valid as bool, warning as str|None), ChangeOutcome (section, parameter, old_value as str, new_value as str)
- [x] T006 Implement engineer response models in `backend/ac_engineer/engineer/models.py`: SetupChange (section, parameter, value_before as float|None, value_after as float, reasoning, expected_effect, confidence as Literal["high","medium","low"]), DriverFeedback (area, observation, suggestion, corners_affected as list[int], severity as Literal["high","medium","low"]), EngineerResponse (session_id, setup_changes as list[SetupChange], driver_feedback as list[DriverFeedback], signals_addressed as list[str], summary, explanation, confidence as Literal["high","medium","low"])
- [x] T007 Write model validation tests in `backend/tests/engineer/test_models.py`: test LapSummary rejects negative gap_to_best_s, test CornerIssue rejects invalid severity, test StintSummary rejects invalid lap_time_trend, test ParameterRange rejects min > max, test ParameterRange rejects step <= 0, test SetupChange rejects invalid confidence, test DriverFeedback rejects invalid severity, test EngineerResponse rejects invalid confidence, test SessionSummary serialization with model_dump(exclude_none=True) omits None fields, test all models round-trip through model_dump/model_validate, test ParameterRange accepts valid range with default_value=None, test ValidationResult accepts clamped_value=None for valid results (~12 tests)

**Checkpoint**: All 12 Pydantic models defined and validated. Foundation ready for story implementation.

---

## Phase 3: User Story 1 — Session Summary for AI Consumption (Priority: P1) 🎯 MVP

**Goal**: Transform AnalyzedSession into a compact SessionSummary optimized for LLM consumption

**Independent Test**: Pass an AnalyzedSession and verify the returned SessionSummary contains correct car, track, lap count, best lap, signals, stints, and averages — no LLM or file system required

### Tests for User Story 1

> **Write tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Write flying lap filtering tests in `backend/tests/engineer/test_summarizer.py`: test only flying laps included (outlaps/inlaps/invalid excluded), test session with 15 laps (3 outlap + 10 flying + 2 inlap) produces 10 LapSummary entries, test each LapSummary has correct lap_number and lap_time_s (~3 tests)
- [x] T009 [P] [US1] Write best lap and gap tests in `backend/tests/engineer/test_summarizer.py`: test best lap has is_best=True and gap_to_best_s=0.0, test other laps have correct positive gap_to_best_s, test single flying lap has is_best=True and gap=0.0 (~3 tests)
- [x] T010 [P] [US1] Write signal detection and corner issue tests in `backend/tests/engineer/test_summarizer.py`: test signals list populated from detect_signals output, test corner_issues sorted by severity (high > medium > low), test corner_issues capped at max_corner_issues=5 default, test custom max_corner_issues=3 produces at most 3 issues (~4 tests)
- [x] T011 [P] [US1] Write stint summary tests in `backend/tests/engineer/test_summarizer.py`: test stint breakdowns include correct flying_lap_count, test lap_time_trend derived from slope (negative=improving, >0.05=degrading, else stable), test setup_filename populated from StintMetrics, test setup_changes_from_prev populated from StintComparison (~4 tests)
- [x] T012 [P] [US1] Write edge case and determinism tests in `backend/tests/engineer/test_summarizer.py`: test zero flying laps produces valid empty summary, test missing tyre data produces None tyre_temp_averages, test identical input produces identical output (determinism), test input AnalyzedSession not mutated (deep compare before/after) (~4 tests)

### Implementation for User Story 1

- [x] T013 [US1] Implement helper functions in `backend/ac_engineer/engineer/summarizer.py`: `_extract_flying_laps(session) -> list[AnalyzedLap]` filtering by classification=="flying", `_build_lap_summary(lap, best_time) -> LapSummary` computing gap_to_best_s and aggregating per-lap metrics (tyre_temp_avg_c as mean of 4 wheel core temps, understeer_ratio_avg as mean of corner understeer_ratios), `_compute_session_averages(flying_laps) -> tuple[dict|None, dict|None, dict|None]` for tyre temps/pressures/slip angles
- [x] T014 [US1] Implement corner issue extraction in `backend/ac_engineer/engineer/summarizer.py`: `_extract_corner_issues(flying_laps, max_issues) -> list[CornerIssue]` scanning all corners across flying laps, computing severity as "high"/"medium"/"low" based on understeer_ratio deviation from 1.0 (>0.3=high, >0.15=medium, else low), populating understeer_ratio/apex_speed_loss_pct/avg_lat_g, generating description string, sorting by severity then deviation magnitude, truncating to max_issues
- [x] T015 [US1] Implement stint summary building in `backend/ac_engineer/engineer/summarizer.py`: `_build_stint_summaries(session) -> list[StintSummary]` iterating session.stints, deriving lap_time_trend from slope, populating tyre_temp_slope_c_per_lap from StintTrends, building setup_changes_from_prev from session.stint_comparisons
- [x] T016 [US1] Implement `summarize_session(session, config, *, max_corner_issues=5) -> SessionSummary` in `backend/ac_engineer/engineer/summarizer.py`: orchestrate all helpers, call detect_signals(session) for signals list, populate session_id from metadata.session_name, populate active_setup_filename/active_setup_parameters from the LAST stint's setup, populate best/worst/stddev from ConsistencyMetrics, populate avg_understeer_ratio from flying lap corner data
- [x] T017 [US1] Run US1 tests and verify all pass: `conda run -n ac-race-engineer pytest backend/tests/engineer/test_summarizer.py -v`

**Checkpoint**: summarize_session() fully functional. Given any AnalyzedSession, produces a complete SessionSummary. ~18 tests passing.

---

## Phase 4: User Story 2 — Setup Parameter Range Discovery (Priority: P2)

**Goal**: Read parameter ranges (min/max/step) from AC car data files for any car

**Independent Test**: Point reader at fixture directory with car data files and verify correct ParameterRange dict; point at nonexistent directory and verify empty dict

### Tests for User Story 2

> **Write tests FIRST, ensure they FAIL before implementation**

- [x] T018 [P] [US2] Write valid data parsing tests in `backend/tests/engineer/test_setup_reader.py`: test reads complete data/setup.ini with multiple sections and returns correct ParameterRange per section, test MIN/MAX/STEP parsed as floats, test default_value populated when present in data, test section name matches dict key (~4 tests)
- [x] T019 [P] [US2] Write error handling tests in `backend/tests/engineer/test_setup_reader.py`: test None ac_install_path returns empty dict, test nonexistent path returns empty dict, test missing car directory returns empty dict, test missing data/setup.ini returns empty dict, test malformed section (missing MIN or MAX) skipped gracefully with partial result, test get_parameter_range returns None for unknown section (~6 tests)

### Implementation for User Story 2

- [x] T020 [US2] Implement `read_parameter_ranges(ac_install_path, car_name) -> dict[str, ParameterRange]` in `backend/ac_engineer/engineer/setup_reader.py`: resolve path as `ac_install_path/content/cars/{car_name}/data/setup.ini`, return empty dict if path is None or does not exist, parse with configparser (case-sensitive via optionxform=str), iterate sections, extract MIN/MAX/STEP (skip section if any missing or non-numeric), build ParameterRange with section name as key, log warnings for skipped sections
- [x] T021 [US2] Implement `get_parameter_range(ranges, section) -> ParameterRange | None` in `backend/ac_engineer/engineer/setup_reader.py`: simple dict lookup returning None on KeyError
- [x] T022 [US2] Run US2 tests and verify all pass: `conda run -n ac-race-engineer pytest backend/tests/engineer/test_setup_reader.py -v`

**Checkpoint**: read_parameter_ranges() works for any car with unpacked data. Graceful degradation on missing/malformed data. ~10 tests passing.

---

## Phase 5: User Story 3 — Setup Change Validation (Priority: P3)

**Goal**: Validate proposed setup changes against parameter ranges without touching files

**Independent Test**: Provide ranges and proposed changes, verify each gets correct is_valid/clamped_value/warning

### Tests for User Story 3

> **Write tests FIRST, ensure they FAIL before implementation**

- [x] T023 [P] [US3] Write validation logic tests in `backend/tests/engineer/test_setup_writer.py`: test value within range → is_valid=True clamped_value=None, test value below min → is_valid=False clamped_value=min_value, test value above max → is_valid=False clamped_value=max_value, test no range data → is_valid=True clamped_value=None warning contains "no range", test batch of 5 changes returns 5 ValidationResults in same order, test exact boundary values (value==min, value==max) both valid (~6 tests)

### Implementation for User Story 3

- [x] T024 [US3] Implement `validate_changes(ranges, proposed) -> list[ValidationResult]` in `backend/ac_engineer/engineer/setup_writer.py`: iterate proposed SetupChange list, look up ParameterRange by section, if found check value_after against min_value/max_value (clamp to boundary if out of range), if not found return is_valid=True with warning, return list in same order as input
- [x] T025 [US3] Run US3 tests and verify all pass: `conda run -n ac-race-engineer pytest backend/tests/engineer/test_setup_writer.py -k "test_validate" -v`

**Checkpoint**: validate_changes() correctly classifies every proposed change. Pure function, no I/O. ~6 tests passing.

---

## Phase 6: User Story 4 — Safe Setup File Writing (Priority: P4)

**Goal**: Apply validated changes to setup .ini files with atomic writes and timestamped backups

**Independent Test**: Create tmp_path setup file, apply changes, verify file modified correctly, backup exists, unchanged params preserved

### Tests for User Story 4

> **Write tests FIRST, ensure they FAIL before implementation**

- [x] T026 [P] [US4] Write backup tests in `backend/tests/engineer/test_setup_writer.py`: test create_backup produces timestamped file with original content, test create_backup raises FileNotFoundError for nonexistent file, test multiple backups have different timestamps (~3 tests)
- [x] T027 [P] [US4] Write apply_changes tests in `backend/tests/engineer/test_setup_writer.py`: test applying 2 changes to 20-param file preserves other 18 params, test backup created before modification, test empty change list raises ValueError, test file not found raises FileNotFoundError, test atomic write (original intact on simulated failure), test last change wins when duplicate section targeted, test sections not in changes are preserved exactly, test ChangeOutcome has correct old_value and new_value (~8 tests)

### Implementation for User Story 4

- [x] T028 [US4] Implement `create_backup(setup_path) -> Path` in `backend/ac_engineer/engineer/setup_writer.py`: verify file exists (raise FileNotFoundError if not), generate backup path as `{name}.ini.bak.{YYYYMMDD_HHMMSS}`, copy with shutil.copy2, return backup path
- [x] T029 [US4] Implement `apply_changes(setup_path, changes) -> list[ChangeOutcome]` in `backend/ac_engineer/engineer/setup_writer.py`: raise ValueError if changes empty, raise FileNotFoundError if file missing, call create_backup first, read file with configparser (case-sensitive), apply each ValidationResult (use proposed_value if is_valid else clamped_value, deduplicate by last-wins for same section), write to .tmp file, os.replace atomically, clean up .tmp on error, return list of ChangeOutcome with old/new values
- [x] T030 [US4] Run US4 tests and verify all pass: `conda run -n ac-race-engineer pytest backend/tests/engineer/test_setup_writer.py -v`

**Checkpoint**: Full write pipeline working — backup, validate, apply atomically. ~17 tests passing (6 validation + 11 writer).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Wire up public exports, run full suite, verify integration

- [x] T031 Implement public exports in `backend/ac_engineer/engineer/__init__.py`: export all models (SessionSummary, LapSummary, CornerIssue, StintSummary, ParameterRange, ValidationResult, ChangeOutcome, SetupChange, DriverFeedback, EngineerResponse) and all functions (summarize_session, read_parameter_ranges, get_parameter_range, validate_changes, apply_changes, create_backup) with `__all__` list
- [x] T032 Run full engineer test suite and verify all ~54 tests pass: `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v`
- [x] T033 Run full project test suite to verify no regressions: `conda run -n ac-race-engineer pytest backend/tests/ -v` (expect ~450 tests: 396 existing + ~54 new)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on other stories
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on other stories
- **US3 (Phase 5)**: Depends on Phase 2 — no dependency on other stories
- **US4 (Phase 6)**: Depends on Phase 2 and Phase 5 (uses ValidationResult from validate_changes)
- **Polish (Phase 7)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (Session Summary)**: Independent — only needs analyzer models + knowledge signals
- **US2 (Parameter Reader)**: Independent — only needs AC file system access
- **US3 (Change Validator)**: Independent — only needs ParameterRange + SetupChange models
- **US4 (Setup Writer)**: Depends on US3 (validate_changes produces ValidationResult consumed by apply_changes)

### Within Each User Story

1. Tests written FIRST and verified to FAIL
2. Implementation tasks in dependency order
3. Test verification run to confirm all pass

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T004, T005, T006 can run in parallel (different model groups, same file but additive)
- T007 must wait for T004-T006

**Phase 3-5 (US1, US2, US3) — all can start in parallel after Phase 2**:
- US1 test tasks (T008-T012) can all run in parallel
- US2 test tasks (T018-T019) can run in parallel
- US3 test task (T023) independent
- US1, US2, US3 implementation is fully independent

**Phase 6 (US4)**:
- T026 and T027 can run in parallel (backup tests vs. apply tests)
- T028 and T029 sequential (backup before apply)

---

## Parallel Example: After Phase 2 Completes

```
# All three user stories can start simultaneously:

# Stream 1: US1 — Session Summary
T008, T009, T010, T011, T012 (all test tasks in parallel)
→ T013, T014, T015 (helpers in parallel)
→ T016 (orchestrator)
→ T017 (verify)

# Stream 2: US2 — Parameter Reader
T018, T019 (test tasks in parallel)
→ T020 (reader implementation)
→ T021 (lookup helper)
→ T022 (verify)

# Stream 3: US3 — Change Validator
T023 (test task)
→ T024 (validator implementation)
→ T025 (verify)

# Then US4 can start (needs US3's validate_changes):
T026, T027 (test tasks in parallel)
→ T028 (backup), T029 (apply)
→ T030 (verify)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational models (T004-T007)
3. Complete Phase 3: US1 — Session Summary (T008-T017)
4. **STOP and VALIDATE**: `pytest backend/tests/engineer/ -v` — ~30 tests pass
5. SessionSummary is usable by Phase 5.3 AI agents immediately

### Incremental Delivery

1. Setup + Foundational → models ready (~12 tests)
2. Add US1 (Summary) → core LLM input ready (~30 tests) **← MVP**
3. Add US2 (Reader) → parameter discovery works (~40 tests)
4. Add US3 (Validator) → change safety verified (~46 tests)
5. Add US4 (Writer) → full write pipeline working (~54 tests)
6. Polish → exports, full suite, regression check

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests use tmp_path fixtures — no real AC install or running game required
- Models file (T004-T006) is additive — tasks write different model groups to same file
- Existing test suite (396 tests) must remain green throughout
- Target: ~54 new tests across 4 test modules
