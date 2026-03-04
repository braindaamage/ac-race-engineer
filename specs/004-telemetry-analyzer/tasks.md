# Tasks: Telemetry Analyzer

**Input**: Design documents from `/specs/004-telemetry-analyzer/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/public-api.md, quickstart.md

**Tests**: Included — the feature specification explicitly requires programmatic test fixtures and real session validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/ac_engineer/analyzer/` for source, `backend/tests/analyzer/` for tests
- **Parser dependency**: `backend/ac_engineer/parser/models.py` (import only)

---

## Phase 1: Setup

**Purpose**: Create the analyzer package structure and configure dependencies

- [ ] T001 Create analyzer package directory structure: `backend/ac_engineer/analyzer/__init__.py`, `backend/ac_engineer/analyzer/models.py`, `backend/ac_engineer/analyzer/lap_analyzer.py`, `backend/ac_engineer/analyzer/corner_analyzer.py`, `backend/ac_engineer/analyzer/stint_analyzer.py`, `backend/ac_engineer/analyzer/consistency.py`, `backend/ac_engineer/analyzer/_utils.py`
- [ ] T002 [P] Create test directory structure: `backend/tests/analyzer/__init__.py`, `backend/tests/analyzer/conftest.py`, `backend/tests/analyzer/test_models.py`, `backend/tests/analyzer/test_lap_analyzer.py`, `backend/tests/analyzer/test_corner_analyzer.py`, `backend/tests/analyzer/test_stint_analyzer.py`, `backend/tests/analyzer/test_consistency.py`, `backend/tests/analyzer/test_session_analyzer.py`, `backend/tests/analyzer/test_real_session.py`
- [ ] T003 [P] Add `scipy` to dependencies in `backend/pyproject.toml` and install via `conda run -n ac-race-engineer pip install scipy`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement all Pydantic v2 models in `backend/ac_engineer/analyzer/models.py` per data-model.md: WheelTempZones, TimingMetrics, TyreMetrics, GripMetrics, DriverInputMetrics, SpeedMetrics, FuelMetrics, SuspensionMetrics, CornerPerformance, CornerGrip, CornerTechnique, CornerLoading, CornerMetrics, LapMetrics, AnalyzedLap, AggregatedStintMetrics, StintTrends, StintMetrics, SetupParameterDelta, MetricDeltas, StintComparison, CornerConsistency, ConsistencyMetrics, AnalyzedSession. Use `from __future__ import annotations`, Pydantic v2 BaseModel, `float | None` union syntax, `dict[str, float]` for per-wheel data keyed by "fl"/"fr"/"rl"/"rr". Import LapClassification from `ac_engineer.parser.models`.
- [ ] T005 Implement shared utility functions in `backend/ac_engineer/analyzer/_utils.py`: `safe_mean(series) -> float | None` (returns None if all NaN, uses numpy.nanmean), `safe_max(series) -> float | None`, `safe_min(series) -> float | None`, `channel_available(df, column) -> bool` (True if column exists and has any non-NaN data), `extract_corner_data(df, entry_pos, exit_pos) -> DataFrame` (filters by normalized_position range, handles wrap-around where entry > exit), `compute_trend_slope(values: list[float]) -> float | None` (scipy.stats.linregress slope, None if < 2 values). Also define module-level threshold constants: `THROTTLE_FULL = 0.95`, `THROTTLE_ON = 0.05`, `BRAKE_ON = 0.05`, `SPEED_PIT_FILTER = 10.0`.
- [ ] T006 Build programmatic test fixtures in `backend/tests/analyzer/conftest.py`: Create helper functions to build ParsedSession, LapSegment, CornerSegment, and SetupEntry objects with controlled data for testing. Key fixtures: `make_lap_data(channels_config) -> dict[str, list]` (generates a data dict with specified channel values), `make_lap_segment(lap_number, classification, data, corners, active_setup) -> LapSegment`, `make_parsed_session(laps, setups, metadata_overrides) -> ParsedSession`, `flying_lap_session` (1 flying lap with full data), `multi_lap_session` (outlap + 2 flying + inlap), `reduced_mode_session` (NaN for tyre_wear, fuel, wheel_load channels), `two_stint_session` (2 stints with different setups, 2 flying laps each), `single_flying_lap_session` (1 flying lap only), `all_invalid_session` (all laps with is_invalid=True). Follow the same programmatic fixture pattern as `backend/tests/parser/conftest.py`.
- [ ] T007 [P] Write model tests in `backend/tests/analyzer/test_models.py`: Test construction of all models with valid data, test None/optional fields, test dict key conventions ("fl"/"fr"/"rl"/"rr"), test that models reject invalid types via Pydantic validation. Follow `backend/tests/parser/test_models.py` pattern with test classes per entity.
- [ ] T008 [P] Write utility tests in `backend/tests/analyzer/test_utils.py`: Test `safe_mean`/`safe_max`/`safe_min` with normal data, all-NaN data (returns None), mixed NaN data. Test `channel_available` with existing column, missing column, all-NaN column. Test `extract_corner_data` with normal range, wrap-around range (entry_pos > exit_pos), empty result. Test `compute_trend_slope` with 0 values (None), 1 value (None), 2+ values (correct slope).

**Checkpoint**: Models defined, utilities working, fixtures ready — user story implementation can begin

---

## Phase 3: User Story 1 — Analyze a Single Lap's Performance (Priority: P1) 🎯 MVP

**Goal**: Compute per-lap metrics (timing, tyres, grip, driver inputs, speed, fuel, suspension) for every lap in a ParsedSession

**Independent Test**: Pass a ParsedSession with one flying lap and verify all metric categories are populated with correct values

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Write lap analyzer tests in `backend/tests/analyzer/test_lap_analyzer.py`: Test `analyze_lap()` with a flying lap (all metrics computed), test with reduced-mode lap (fuel=None, wear=None), test with invalid lap (metrics computed, is_invalid flagged), test timing metrics (lap_time_s = end_timestamp - start_timestamp), test tyre metrics (average/peak temps per wheel per zone, pressure avg, temp spread, front-rear balance), test grip metrics (slip angle/ratio avg/peak per wheel, peak G-forces), test driver input metrics (throttle percentages with thresholds 0.95/0.05, braking pct, steering avg, gear distribution sums to ~100%), test speed metrics (max, min excluding < 10 km/h, avg), test fuel metrics (start - end), test suspension metrics (avg/peak/range per wheel), test sector times (3 equal sectors by normalized position). Use `multi_lap_session` and `reduced_mode_session` fixtures.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `analyze_lap(lap: LapSegment, metadata: SessionMetadata) -> LapMetrics` in `backend/ac_engineer/analyzer/lap_analyzer.py`: Extract lap DataFrame via `lap.to_dataframe()`. Compute TimingMetrics (lap_time_s from timestamps; sector_times_s by interpolating timestamps at normalized_position 0.333 and 0.667 boundaries, return list of 3 sector durations or None if insufficient position data). Compute TyreMetrics (for each wheel fl/fr/rl/rr: safe_mean/safe_max of tyre_temp_{zone}_{wheel} for core/inner/mid/outer → WheelTempZones; pressure_avg from tyre_pressure_{wheel}; temp_spread = inner_avg - outer_avg per wheel; front_rear_balance = mean(fl_core+fr_core)/mean(rl_core+rr_core); wear_rate from tyre_wear delta or None). Compute GripMetrics (safe_mean/safe_max of abs(slip_angle_{wheel}) and abs(slip_ratio_{wheel}); peak_lat_g = safe_max(abs(g_lat)); peak_lon_g = safe_max(abs(g_lon))). Compute DriverInputMetrics (full_throttle_pct = % samples throttle >= 0.95; partial = 0.05 < throttle < 0.95; off = throttle <= 0.05; braking_pct = % brake > 0.05; avg_steering_angle = safe_mean(abs(steering)); gear_distribution = value_counts of gear column as percentages). Compute SpeedMetrics (max/min filtered > 10 km/h/avg of speed_kmh). Compute FuelMetrics (fuel first/last sample delta, or None if channel unavailable). Compute SuspensionMetrics (safe_mean/safe_max/range of susp_travel_{wheel} per wheel). Use _utils helpers throughout.
- [ ] T011 [US1] Verify all T009 tests pass for User Story 1 by running `conda run -n ac-race-engineer pytest backend/tests/analyzer/test_lap_analyzer.py -v`

**Checkpoint**: Per-lap metrics working for all lap types. Core MVP functional.

---

## Phase 4: User Story 2 — Analyze Corner-by-Corner Performance (Priority: P1)

**Goal**: Compute per-corner metrics (performance, grip, technique, loading) for each detected corner on each lap

**Independent Test**: Pass a ParsedSession with one lap containing corners and verify each corner has accurate metrics from time series data

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [US2] Write corner analyzer tests in `backend/tests/analyzer/test_corner_analyzer.py`: Test `analyze_corner()` with a normal braked corner (all metrics computed), test with a flat-out kink (brake_point_norm=None, trail_braking_intensity=0), test performance metrics (entry/apex/exit speeds match time series at those normalized positions, duration > 0), test grip metrics (peak/avg lat G, understeer_ratio computed as front_slip_avg/rear_slip_avg), test technique metrics (brake_point_norm is first position where brake > threshold, throttle_on_norm is first position after apex where throttle > threshold, trail_braking_intensity = mean brake where brake > threshold AND abs(steering) > threshold), test loading metrics (peak wheel loads per wheel, or None if wheel_load channels NaN), test with wrap-around corner (entry_norm_pos > exit_norm_pos). Build specific corner fixtures with known data values for precise assertion.

### Implementation for User Story 2

- [ ] T013 [US2] Implement `analyze_corner(corner: CornerSegment, lap_df: DataFrame) -> CornerMetrics` in `backend/ac_engineer/analyzer/corner_analyzer.py`: Use `extract_corner_data(lap_df, corner.entry_norm_pos, corner.exit_norm_pos)` to get corner samples. Compute CornerPerformance (entry_speed = speed_kmh at sample nearest entry_norm_pos; apex_speed at apex_norm_pos; exit_speed at exit_norm_pos; duration_s from timestamp range of corner samples). Compute CornerGrip (peak_lat_g = max abs(g_lat); avg_lat_g = mean abs(g_lat); understeer_ratio = mean(abs(slip_angle_fl), abs(slip_angle_fr)) / mean(abs(slip_angle_rl), abs(slip_angle_rr)), or None if rear slip avg < epsilon (0.01 rad) per FR-021 — insufficient data to compute ratio). Compute CornerTechnique (brake_point_norm = normalized_position of first sample where brake > BRAKE_ON threshold, None if no braking; throttle_on_norm = normalized_position of first sample after apex_norm_pos where throttle > THROTTLE_ON; trail_braking_intensity = mean(brake) for samples where brake > BRAKE_ON AND abs(steering) > 0.05, 0.0 if no overlap). Compute CornerLoading (peak_wheel_load per wheel from wheel_load_{wheel} channels, None if unavailable). Use _utils helpers.
- [ ] T014 [US2] Verify all T012 tests pass for User Story 2 by running `conda run -n ac-race-engineer pytest backend/tests/analyzer/test_corner_analyzer.py -v`

**Checkpoint**: Per-corner metrics working. Combined with US1, can analyze individual laps with full detail.

---

## Phase 5: User Story 3 — Compare Performance Across Stints (Priority: P2)

**Goal**: Group laps by setup, compute aggregated stint metrics with trends, and compare across stints

**Independent Test**: Pass a ParsedSession with 2 stints (different setups, 2+ flying laps each) and verify aggregated metrics, trends, and cross-stint deltas

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [US3] Write stint analyzer tests in `backend/tests/analyzer/test_stint_analyzer.py`: Test `group_stints()` with 2 stints (laps grouped by active_setup identity), test with 1 stint (single group), test with all laps having no setup (single group with None setup). Test `compute_stint_trends()` with 3 flying laps (lap_time_slope, tyre_temp_slope per wheel, fuel_consumption_slope), test with 1 flying lap (returns None), test with 2 flying laps (slope computed). Test `compare_stints()` with 2 stints having different setups (metric deltas = B - A, setup_changes list populated), test with identical setups (empty setup_changes, deltas near zero), test with stints where one has no flying laps (deltas are None where applicable). Use `two_stint_session` fixture.

### Implementation for User Story 3

- [ ] T016 [US3] Implement stint analysis functions in `backend/ac_engineer/analyzer/stint_analyzer.py`: `group_stints(laps: list[AnalyzedLap], session_laps: list[LapSegment]) -> list[StintMetrics]` — iterate laps in order, start new stint when active_setup changes (compare by lap_start + filename as identity key, treat None as its own group). For each stint: collect lap_numbers, count flying laps, compute AggregatedStintMetrics (mean/stddev of flying lap times from LapMetrics.timing.lap_time_s; mean tyre core temps per wheel from TyreMetrics; mean slip angles/ratios per wheel from GripMetrics; mean peak_lat_g). `compute_stint_trends(stint: StintMetrics, analyzed_laps: list[AnalyzedLap]) -> StintTrends | None` — filter to flying laps in stint, extract sequential values, compute_trend_slope for lap_time, tyre_temp per wheel, fuel_consumption; None if < 2 flying laps. `compare_stints(stint_a: StintMetrics, stint_b: StintMetrics, setup_a: SetupEntry | None, setup_b: SetupEntry | None) -> StintComparison` — compute MetricDeltas (B.aggregated - A.aggregated for each metric); diff setup parameters to build list[SetupParameterDelta] (match by section+name, report changes).
- [ ] T017 [US3] Verify all T015 tests pass for User Story 3 by running `conda run -n ac-race-engineer pytest backend/tests/analyzer/test_stint_analyzer.py -v`

**Checkpoint**: Stint analysis working. Setup changes correlated with metric deltas.

---

## Phase 6: User Story 4 — Assess Driver Consistency (Priority: P3)

**Goal**: Compute session-wide consistency metrics across all flying laps

**Independent Test**: Pass a ParsedSession with 3+ flying laps and verify stddev, variance per corner, and trend are correct

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [US4] Write consistency tests in `backend/tests/analyzer/test_consistency.py`: Test `compute_consistency()` with 4 flying laps (lap_time_stddev, best/worst lap time, lap_time_trend_slope, per-corner apex_speed_variance and brake_point_variance). Test with 1 flying lap (stddev=0, no variance, trend=None). Test with 0 flying laps (returns None). Test with corner missing from some laps (variance computed from available data, sample_count reflects actual count). Test that best_lap_time <= worst_lap_time always.

### Implementation for User Story 4

- [ ] T019 [US4] Implement `compute_consistency(analyzed_laps: list[AnalyzedLap]) -> ConsistencyMetrics | None` in `backend/ac_engineer/analyzer/consistency.py`: Filter to flying laps. Return None if 0 flying laps. Extract lap times → compute stddev (numpy.std), min (best), max (worst). compute_trend_slope for lap time trend (None if < 2). For corner consistency: collect all unique corner_numbers across all flying laps' CornerMetrics, for each corner_number: gather apex_speed_kmh values from laps that have it → compute variance (numpy.var) and stddev; gather brake_point_norm values (excluding None) → compute variance; record sample_count. Return ConsistencyMetrics with flying_lap_count, lap time stats, and list of CornerConsistency.
- [ ] T020 [US4] Verify all T018 tests pass for User Story 4 by running `conda run -n ac-race-engineer pytest backend/tests/analyzer/test_consistency.py -v`

**Checkpoint**: All four analysis modules complete and independently tested.

---

## Phase 7: Integration & Real Data Validation

**Purpose**: Wire up the full pipeline and validate against real session data

- [ ] T021 Implement `analyze_session(session: ParsedSession) -> AnalyzedSession` orchestrator in `backend/ac_engineer/analyzer/__init__.py`: Import all submodules. For each lap in session.laps: call analyze_lap → build AnalyzedLap with lap metadata + LapMetrics; for each corner in lap.corners: call analyze_corner → append CornerMetrics. Call group_stints to build StintMetrics list, then compute_stint_trends for each stint, then compare_stints for each adjacent pair. Call compute_consistency on all analyzed laps. Assemble and return AnalyzedSession. Re-export all public models via `__all__`.
- [ ] T022 Write integration tests in `backend/tests/analyzer/test_session_analyzer.py`: Test `analyze_session()` with `multi_lap_session` fixture (verify AnalyzedSession has correct lap count, each lap has metrics, corners analyzed, stints grouped). Test with `reduced_mode_session` (fuel/wear metrics None, other metrics present). Test with `all_invalid_session` (all laps analyzed with is_invalid=True). Test with `single_flying_lap_session` (consistency has stddev=0, 1 stint with no trends). Test determinism (run twice, compare output). Test that input ParsedSession is not modified.
- [ ] T023 Write real session validation tests in `backend/tests/analyzer/test_real_session.py`: Load the real BMW M235i Mugello session from `examples/sessions/` using `parse_session()` from ac_engineer.parser. Run `analyze_session()`. Validate: correct number of analyzed laps (matches parser output), all flying laps have non-None timing/tyre/grip/speed metrics, corner metrics present for laps with corners, 2 stints detected (matching setup history), stint comparison exists with setup parameter deltas, plausible metric ranges (lap times > 30s and < 300s, speeds > 0, temperatures > 0°C, percentages 0-100). Test determinism on real data.
- [ ] T024 Run full test suite: `conda run -n ac-race-engineer pytest backend/tests/analyzer/ -v` and verify all tests pass

**Checkpoint**: Full pipeline working end-to-end with real data validation.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final quality pass

- [ ] T025 [P] Add docstrings to all public functions and classes following Google-style format (Args, Returns) matching parser conventions in `backend/ac_engineer/analyzer/`
- [ ] T026 Run quickstart.md validation: execute the usage example from `specs/004-telemetry-analyzer/quickstart.md` against real session data and verify output matches expected structure

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Lap Metrics (Phase 3)**: Depends on Foundational (Phase 2)
- **US2 Corner Metrics (Phase 4)**: Depends on Foundational (Phase 2). Can run in parallel with US1.
- **US3 Stint Comparison (Phase 5)**: Depends on US1 (needs AnalyzedLap with LapMetrics for aggregation)
- **US4 Consistency (Phase 6)**: Depends on US1 + US2 (needs AnalyzedLap with LapMetrics + CornerMetrics)
- **Integration (Phase 7)**: Depends on ALL user stories complete
- **Polish (Phase 8)**: Depends on Integration

### User Story Dependencies

- **US1 (Lap Metrics)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (Corner Metrics)**: Can start after Phase 2 — No dependencies on other stories. Can run in parallel with US1.
- **US3 (Stint Comparison)**: Depends on US1 — needs LapMetrics for aggregation
- **US4 (Consistency)**: Depends on US1 + US2 — needs LapMetrics + CornerMetrics for variance analysis

### Within Each User Story

- Tests written FIRST and must FAIL before implementation
- Implementation makes tests pass
- Verification step confirms all tests green

### Parallel Opportunities

- T001, T002, T003 can all run in parallel (Phase 1)
- T007, T008 can run in parallel with each other (model + util tests, different files)
- T004 and T005 can run sequentially (models first, then utils that use them)
- US1 (Phase 3) and US2 (Phase 4) can run in parallel after Phase 2
- T025 can run in parallel with T026 (Polish phase)

---

## Parallel Example: Phase 1

```
# Launch all setup tasks together:
Task T001: "Create analyzer package directory structure"
Task T002: "Create test directory structure"
Task T003: "Add scipy dependency"
```

## Parallel Example: US1 + US2

```
# After Phase 2 completes, US1 and US2 can proceed in parallel:
Stream A (US1): T009 → T010 → T011
Stream B (US2): T012 → T013 → T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Lap Metrics)
4. **STOP and VALIDATE**: Test lap metrics independently
5. A single `analyze_lap()` function already delivers actionable per-lap data

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Lap Metrics) → Per-lap analysis functional (MVP!)
3. US2 (Corner Metrics) → Corner-level detail added
4. US3 (Stint Comparison) → Setup change impact analysis
5. US4 (Consistency) → Driver consistency assessment
6. Integration → Full `analyze_session()` pipeline
7. Each increment adds value without breaking previous functionality

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All wheel-keyed dicts use lowercase: "fl", "fr", "rl", "rr"
- All metrics using thresholds reference constants in _utils.py (THROTTLE_FULL=0.95, THROTTLE_ON=0.05, BRAKE_ON=0.05, SPEED_PIT_FILTER=10.0)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
