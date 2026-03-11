# Tasks: Fix Setup Value Domain Conversion

**Input**: Design documents from `specs/034-fix-setup-value-domains/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — the spec requires round-trip integrity tests (SC-005), all existing tests must pass (SC-004), and the plan explicitly defines test_conversion.py with 20 test cases.

**Organization**: Tasks are grouped by user story. US1 (INDEX) and US2 (SCALED) share all implementation code and are combined into a single phase since both are P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Foundational — Conversion Module & Model Changes

**Purpose**: Build the pure conversion functions and extend ParameterRange before touching any pipeline code. Zero existing behavior changes in this phase.

**⚠ CRITICAL**: No pipeline integration can begin until this phase is complete.

### Tests

- [x] T001 Create conversion unit tests with all 20 test cases enumerated in plan.md Phase A in `backend/tests/engineer/test_conversion.py`. Tests cover: classify_parameter (5 cases: index, direct, scaled, None, unknown), to_physical (4 cases: index, scaled, direct, None convention), to_storage (7 cases: index exact, index snap, index clamp low, index clamp high, scaled, scaled rounding, direct), round-trip (3 cases: index parametric, scaled, direct), edge case (step zero fallback). The `test_to_storage_scaled_rounding` case verifies that physical=-1.15 with scale_factor=0.1 produces storage=-12 (rounded from -11.5, not truncated to -11 or left as -11.5). All tests must initially FAIL since conversion.py does not exist yet.

### Implementation

- [x] T002 Create `backend/ac_engineer/engineer/conversion.py` with: SCALE_FACTORS constant (`{"CAMBER": 0.1}`), `_get_scale_factor(section)` helper, `classify_parameter(section, show_clicks)` implementing FR-001 decision tree (SHOW_CLICKS=2→"index", =0+CAMBER→"scaled", =0→"direct", else→"direct"), `to_physical(storage_value, param_range)` per data-model.md formulas, `to_storage(physical_value, param_range)` with index snapping via round() and clamping to [0, max_index]. For SCALED parameters, `to_storage` must round the result to the nearest integer since AC stores camber as integer tenths of degree: `round(physical_value / scale_factor)`. Import only ParameterRange from models.py. All functions must be pure — no I/O, no database, no LLM calls.

- [x] T003 Run T001 tests — all 20 must now pass. Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) to confirm zero regressions from the new module.

- [x] T004 [P] Add `show_clicks: int | None = None` and `storage_convention: str | None = None` fields to ParameterRange in `backend/ac_engineer/engineer/models.py`. Both fields must default to None for backward compatibility with existing serialized data and test fixtures. Add Field description to SetupChange.value_before and value_after noting they are in physical units.

- [x] T005 Modify `_parse_setup_ini()` in `backend/ac_engineer/resolver/resolver.py` to read SHOW_CLICKS as int from each section (optional, default None). Call `classify_parameter(section_name, show_clicks)` from conversion.py to compute storage_convention. Pass both `show_clicks` and `storage_convention` to the ParameterRange constructor. Only Tier 1 and Tier 2 call this function — Tier 3 correctly gets show_clicks=None. **Depends on T004** — ParameterRange fields must exist before the resolver can set them.

- [x] T006 Run full backend test suite to confirm T004 and T005 cause zero regressions. The new ParameterRange fields default to None, so all existing ParameterRange constructions remain valid.

**Checkpoint**: conversion.py exists with full test coverage. ParameterRange has new fields. Resolver reads SHOW_CLICKS. No pipeline behavior has changed yet.

---

## Phase 2: US1 + US2 — Index & Scaled Parameter Conversion (Priority: P1) 🎯 MVP

**Goal**: INDEX parameters (SHOW_CLICKS=2) display physical-unit values to the LLM and write correct storage indices to the .ini file. SCALED parameters (camber) display degree values and write correctly scaled storage values. These two stories share all implementation code.

**Independent Test**: Run the engineer pipeline with a FunctionModel on a car that has INDEX parameters (ARB_FRONT) and SCALED parameters (CAMBER_LF). Verify: (1) LLM prompt shows physical values, (2) proposed physical values are converted back to correct storage format before writing.

### Tests

- [x] T007 [P] [US1] Add test in `backend/tests/engineer/test_summarizer.py`: given a setup .ini with an INDEX parameter (ARB_FRONT VALUE=2) and a parameter_ranges dict with show_clicks=2/min=25500/step=4500/storage_convention="index", verify that `summarize_session()` with `parameter_ranges` kwarg produces `active_setup_parameters["ARB_FRONT"]["VALUE"] == 34500.0`.

- [x] T008 [P] [US2] Add test in `backend/tests/engineer/test_summarizer.py`: given a setup .ini with CAMBER_LR VALUE=-18 and a parameter_ranges dict with show_clicks=0/storage_convention="scaled", verify that `summarize_session()` produces `active_setup_parameters["CAMBER_LR"]["VALUE"] == -1.8`.

- [x] T009 [P] [US1] Add test in `backend/tests/engineer/test_setup_writer.py`: given a ValidationResult with proposed_value=30000.0 for an INDEX parameter (ARB_FRONT, min=25500, step=4500, storage_convention="index"), verify that `apply_changes()` with `parameter_ranges` kwarg writes `VALUE=1` (not VALUE=30000.0) to the .ini file.

- [x] T010 [P] [US2] Add test in `backend/tests/engineer/test_setup_writer.py`: given a ValidationResult with proposed_value=-1.0 for CAMBER_LR (storage_convention="scaled"), verify that `apply_changes()` writes `VALUE=-10.0` to the .ini file.

### Implementation

- [x] T011 [US1] [US2] Add `parameter_ranges: dict[str, ParameterRange] | None = None` keyword parameter to `summarize_session()` in `backend/ac_engineer/engineer/summarizer.py`. After `_parse_setup_ini()` returns `active_setup_parameters` (line ~80), iterate the dict: for each section with a matching ParameterRange, call `to_physical(value, param_range)` to convert the VALUE. If parameter_ranges is None, skip conversion entirely (backward compatible). Do NOT modify `_parse_setup_ini()` — it remains a pure .ini parser.

- [x] T012 [US1] [US2] Add `parameter_ranges: dict[str, ParameterRange] | None = None` parameter to `apply_changes()` in `backend/ac_engineer/engineer/setup_writer.py`. Before writing each VALUE to the .ini (line ~171), if parameter_ranges is provided and the section has a matching range, call `to_storage(effective_value, param_range)` to convert back to storage format. If parameter_ranges is None or section not found, write value unchanged (backward compatible).

- [x] T013 [US1] [US2] Update `analyze_with_engineer()` in `backend/ac_engineer/engineer/agents.py` to pass `parameter_ranges` to `summarize_session()` so the inbound conversion is active during analysis.

- [x] T014 [US1] [US2] Update `apply_recommendation()` in `backend/ac_engineer/engineer/agents.py` to pass `parameter_ranges` to `apply_changes()` so the outbound conversion is active when writing recommendations.

- [x] T015 [US1] [US2] Run T007–T010 tests — all must pass. Run full backend test suite to confirm zero regressions.

**Checkpoint**: INDEX and SCALED parameters are now converted at both boundaries. The LLM sees physical values and the .ini file receives correct storage values. US1 and US2 acceptance scenarios are satisfied.

---

## Phase 3: US3 + US4 — Direct Passthrough & Physical Display (Priority: P2)

**Goal**: Verify DIRECT parameters (SHOW_CLICKS=0, non-CAMBER) continue working unchanged, and that value_before/value_after in recommendations are in physical units.

**Independent Test**: Run the engineer pipeline with DIRECT parameters (PRESSURE_LF) and verify values pass through unchanged. Inspect EngineerResponse to confirm value_before and value_after are physical.

### Tests

- [x] T016 [P] [US3] Add test in `backend/tests/engineer/test_summarizer.py`: given PRESSURE_LF VALUE=18 with parameter_ranges containing show_clicks=0/storage_convention="direct", verify `summarize_session()` produces `active_setup_parameters["PRESSURE_LF"]["VALUE"] == 18.0` (unchanged).

- [x] T017 [P] [US3] Add test in `backend/tests/engineer/test_setup_writer.py`: given proposed_value=16.0 for PRESSURE_LF (storage_convention="direct"), verify `apply_changes()` writes `VALUE=16.0` (unchanged).

- [x] T018 [P] [US4] Add test in `backend/tests/engineer/test_agents.py`: given an INDEX parameter with storage value_before=2 (physical: 34500) and a FunctionModel that proposes value_after=30000, verify the resulting SetupChange in EngineerResponse has value_before=34500 and value_after=30000 (both physical).

### Implementation

- [x] T019 [US3] [US4] No new implementation code needed for US3 or US4 — DIRECT passthrough and physical display are automatic consequences of Phases 1-2. If T016–T018 pass, these stories are verified. If any fail, diagnose and fix the conversion path for the failing case.

**Checkpoint**: DIRECT parameters verified as passthrough. value_before/value_after confirmed as physical units. US3 and US4 acceptance scenarios are satisfied.

---

## Phase 4: US5 — Stale Parameter Cache Invalidation (Priority: P3)

**Goal**: Existing cached parameter data lacking show_clicks metadata is automatically detected as stale and re-resolved with the new field.

**Independent Test**: Pre-populate a parameter cache entry without show_clicks, then call resolve_parameters(). Verify the stale entry is discarded and fresh resolution occurs with show_clicks populated.

### Tests

- [x] T020 [P] [US5] Add test in `backend/tests/resolver/test_cache.py`: save a ResolvedParameters to cache with ParameterRange objects that have show_clicks=None. Call `get_cached_parameters()`. Verify it returns None (stale detection triggered).

- [x] T021 [P] [US5] Add test in `backend/tests/resolver/test_cache.py`: save a ResolvedParameters to cache with ParameterRange objects that have show_clicks=2. Call `get_cached_parameters()`. Verify it returns the cached entry (not stale).

### Implementation

- [x] T022 [US5] Modify `get_cached_parameters()` in `backend/ac_engineer/resolver/cache.py`: after deserializing the ResolvedParameters, check if any ParameterRange has `show_clicks is None`. If so, return None to trigger lazy re-resolution. The DB schema has `CHECK(tier IN (1, 2))` so Tier 3 is never cached — no tier check needed.

- [x] T023 [US5] Run T020–T021 tests — both must pass. Run full resolver test suite (`conda run -n ac-race-engineer pytest backend/tests/resolver/ -v`) to confirm zero regressions.

**Checkpoint**: Stale cache entries are lazily detected and re-resolved. US5 acceptance scenarios are satisfied.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Exports, full regression, integration verification.

- [x] T024 [P] Export conversion functions from `backend/ac_engineer/engineer/__init__.py`: add `classify_parameter`, `to_physical`, `to_storage`, `SCALE_FACTORS` to public imports.

- [x] T025 Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`). All 1410+ existing tests plus all new tests must pass. This verifies SC-004 (no regressions) and SC-005 (round-trip integrity via test_conversion.py).

- [x] T026 Run full frontend test suite (`cd frontend && npm run test`) and TypeScript check (`npx tsc --noEmit`). No frontend changes were made, but verify no transitive breakage from API response changes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — starts immediately
- **US1+US2 (Phase 2)**: Depends on Phase 1 completion — BLOCKS on conversion module + model changes
- **US3+US4 (Phase 3)**: Depends on Phase 2 completion — verification of behavior established in Phase 2
- **US5 (Phase 4)**: Depends on Phase 1 only (model changes) — can run in parallel with Phases 2-3
- **Polish (Phase 5)**: Depends on all phases complete

### User Story Dependencies

- **US1 + US2 (P1)**: Can start after Phase 1. Core conversion — all other stories depend on this.
- **US3 (P2)**: Can start after Phase 2. Verifies DIRECT passthrough — no new code expected.
- **US4 (P2)**: Can start after Phase 2. Verifies physical display — no new code expected.
- **US5 (P3)**: Can start after Phase 1. Independent of US1-US4 (only touches cache.py).

### Within Each Phase

- Tests (T001, T007-T010, T016-T018, T020-T021) are written FIRST and must FAIL before implementation
- T005 depends on T004 (ParameterRange fields must exist before resolver can set them)
- Summarizer changes (T011) and writer changes (T012) can run in parallel (different files)
- Agent wiring (T013, T014) depends on T011 and T012 respectively

### Parallel Opportunities

- T005 depends on T004 (ParameterRange fields must exist before resolver can set them)
- T007, T008, T009, T010 can all run in parallel (test files, no implementation deps)
- T011 and T012 can run in parallel (summarizer.py vs setup_writer.py)
- T016, T017, T018 can all run in parallel (test files)
- T020 and T021 can run in parallel (same test file but independent test cases)
- Phase 4 (US5) can run in parallel with Phases 2-3

---

## Parallel Example: Phase 2 (US1 + US2)

```bash
# Launch all tests for US1+US2 together:
Task: T007 "test summarizer INDEX conversion in backend/tests/engineer/test_summarizer.py"
Task: T008 "test summarizer SCALED conversion in backend/tests/engineer/test_summarizer.py"
Task: T009 "test writer INDEX conversion in backend/tests/engineer/test_setup_writer.py"
Task: T010 "test writer SCALED conversion in backend/tests/engineer/test_setup_writer.py"

# Launch both pipeline boundary changes together:
Task: T011 "inbound conversion in backend/ac_engineer/engineer/summarizer.py"
Task: T012 "outbound conversion in backend/ac_engineer/engineer/setup_writer.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Foundational (conversion.py + models + resolver)
2. Complete Phase 2: US1 + US2 (inbound + outbound conversion)
3. **STOP and VALIDATE**: Run full test suite. INDEX and SCALED parameters now produce correct values.
4. This alone fixes the critical bugs documented in the problem statement.

### Incremental Delivery

1. Phase 1 → Conversion module built and tested (no behavior changes)
2. Phase 2 → INDEX + SCALED conversion active (MVP — fixes critical bugs)
3. Phase 3 → DIRECT passthrough verified (confidence that no regressions)
4. Phase 4 → Cache invalidation active (stale data auto-corrected)
5. Phase 5 → Full regression verified, exports clean

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 share all implementation tasks (same conversion module, same pipeline changes)
- US3 and US4 require no new implementation — they are verification-only phases
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
