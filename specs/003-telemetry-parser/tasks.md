# Tasks: Telemetry Parser

**Input**: Design documents from `specs/003-telemetry-parser/`
**Branch**: `003-telemetry-parser`
**Stack**: Python 3.11+, pandas, numpy, pyarrow, pydantic v2, pytest — conda env `ac-race-engineer`

**Note on D5 → is_invalid**: Tasks T006–T007 amend the design docs before implementation.
`LapSegment` carries both `classification` (pit-lane logic: outlap/inlap/incomplete/invalid/flying)
and `is_invalid: bool` (data-quality flag: True whenever any sample has `lap_invalid==1` or a
disqualifying anomaly is detected, regardless of classification). An outlap with `lap_invalid`
set → `classification="outlap"`, `is_invalid=True`.

---

## Format: `[ID] [P?] [Story?] Description — file path`

- **[P]**: Can run in parallel (different files, no shared state dependencies)
- **[Story]**: User story from spec.md (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the `backend/` directory tree, package config, and development environment
so all user story work can begin.

- [x] T001 Create directory tree: `backend/ac_engineer/parser/`, `backend/tests/parser/fixtures/` — repo root
- [x] T002 [P] Create `backend/pyproject.toml` with hatchling config declaring `ac_engineer` as the package (packages = `["ac_engineer"]`, no src layout) and pytest testpaths pointing to `tests/` — `backend/pyproject.toml`
- [x] T003 [P] Install runtime dependencies in conda env `ac-race-engineer`: `conda activate ac-race-engineer && pip install pandas numpy pyarrow "pydantic>=2.0"` — terminal
- [x] T004 [P] Create empty `backend/ac_engineer/__init__.py` and stub `backend/ac_engineer/parser/__init__.py` (imports placeholder comment) — `backend/ac_engineer/__init__.py`, `backend/ac_engineer/parser/__init__.py`
- [x] T005 [P] Create `backend/tests/__init__.py` and `backend/tests/parser/__init__.py` — `backend/tests/__init__.py`, `backend/tests/parser/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Amend design docs for the `is_invalid` decision, implement all Pydantic models,
and create the test fixture infrastructure. All user story phases depend on this phase.

**⚠️ CRITICAL**: No user story work can begin until T008 (models) and T010 (conftest) are complete.

- [x] T006 [P] Update `specs/003-telemetry-parser/data-model.md`: in the `LapSegment` entity table add row `is_invalid | bool | — | True if any sample has lap_invalid==1 or a disqualifying anomaly; independent of classification`; update the classification rules note (replace D5 paragraph with the is_invalid resolution) — `specs/003-telemetry-parser/data-model.md`
- [x] T007 [P] Update `specs/003-telemetry-parser/contracts/public-api.md`: add `is_invalid: bool` field to the `LapSegment` class definition block; update the D5 design decision note in `plan.md` to reflect the resolved approach — `specs/003-telemetry-parser/contracts/public-api.md`, `specs/003-telemetry-parser/plan.md`
- [x] T008 Implement all Pydantic v2 models in `backend/ac_engineer/parser/models.py`: `WarnType` Literal, `LapClassification` Literal, `QualityWarning`, `SetupParameter`, `SetupEntry`, `CornerSegment`, `LapSegment` (with `is_invalid: bool = False` field, `to_dataframe()` method), `SessionMetadata`, `ParsedSession` (with `flying_laps` property and `lap_by_number()` method), `ParserError` exception — `backend/ac_engineer/parser/models.py`
- [x] T009 Expose public API in `backend/ac_engineer/parser/__init__.py`: import and re-export `parse_session`, `save_session`, `load_session` (stubs that raise `NotImplementedError`), and all model classes — `backend/ac_engineer/parser/__init__.py`
- [x] T010 Create `backend/tests/parser/conftest.py` with programmatic fixture builder functions that generate synthetic DataFrames and metadata dicts (no game files needed): `make_session_df(lap_configs)`, `make_metadata_v2(overrides)`, `make_metadata_v1_legacy()`, and named pytest fixtures for all 8 integration scenarios: `minimal_session_files`, `zero_laps_files`, `crash_session_files`, `legacy_v1_files`, `all_invalid_files`, `reduced_mode_files`, `multi_setup_files`, `data_gaps_files` — each fixture returns `(csv_path, meta_path)` tmp paths — `backend/tests/parser/conftest.py`
- [x] T011 [P] Write `backend/tests/parser/test_models.py`: test Pydantic validation for each model (valid construction, field constraints, type coercion), test `LapSegment.to_dataframe()` roundtrip, test `ParsedSession.flying_laps` returns only flying-classified laps, test `lap_by_number()` lookup, test `is_invalid=True` is independent of `classification` — `backend/tests/parser/test_models.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_models.py` passes — foundation ready.

---

## Phase 3: User Story 1 — Lap Segmentation and Classification (Priority: P1) 🎯 MVP

**Goal**: `parse_session()` reads a CSV + meta.json and returns a `ParsedSession` with correctly
segmented and classified `LapSegment` list. No corners, no setups, no quality warnings yet.

**Independent Test**: Run `test_lap_segmenter.py` and the US1 scenarios in `test_session_parser.py`.
Verify: exact lap count matches, all 5 classification types produced correctly, `is_invalid` set
correctly on outlaps/inlaps with `lap_invalid` flag, no samples lost between laps,
zero-lap session returns empty laps list without error.

- [x] T01X [US1] Implement `segment_laps(df: pd.DataFrame) -> list[pd.DataFrame]` in `backend/ac_engineer/parser/lap_segmenter.py`: group rows by `lap_count` value in temporal order, return one DataFrame per unique `lap_count` value (including partial first/last groups), handle 0-row and single-row DataFrames, raise `ParserError` if `lap_count` column missing — `backend/ac_engineer/parser/lap_segmenter.py`
- [x] T01X [US1] Implement `classify_lap(lap_df, is_first, is_last) -> tuple[LapClassification, bool]` in `backend/ac_engineer/parser/lap_segmenter.py`: apply 5-rule state machine in priority order (outlap → inlap → incomplete → invalid → flying); return `(classification, is_invalid)` where `is_invalid=True` whenever any sample has `lap_invalid==1`; `is_last=True` forces `incomplete` for the final partial lap — `backend/ac_engineer/parser/lap_segmenter.py`
- [x] T01X [P] [US1] Write `backend/tests/parser/test_lap_segmenter.py`: test `segment_laps` with 0 laps, 1 lap, 10 laps, missing `lap_count` column; test `classify_lap` for all 5 types including outlap+is_invalid=True, inlap+is_invalid=True, incomplete+is_invalid=True, pure invalid, flying; test no samples lost between segments — `backend/tests/parser/test_lap_segmenter.py`
- [x] T01X [US1] Implement metadata reading in `backend/ac_engineer/parser/session_parser.py`: `_read_metadata(meta_path)` function that reads `.meta.json`, detects v1.0 (missing `setup_history` key) vs v2.0, converts v1.0 flat fields to single-entry `setup_history` array with `lap=0, trigger="session_start"`, derives null `session_end`/`total_samples`/`sample_rate_hz` from CSV data when those fields are null (crash recovery) — `backend/ac_engineer/parser/session_parser.py`
- [x] T01X [US1] Implement CSV reading and lap segmentation pipeline in `backend/ac_engineer/parser/session_parser.py`: `_read_csv(csv_path)` that reads with pandas, validates `lap_count` and `normalized_position` columns present, detects all-NaN columns as unavailable; wire pipeline steps 1–4 in `parse_session()`: call `_read_metadata`, `_read_csv`, `segment_laps`, `classify_lap` for each segment — `backend/ac_engineer/parser/session_parser.py`
- [x] T01X [US1] Implement US1 model assembly in `backend/ac_engineer/parser/session_parser.py`: build `SessionMetadata` from metadata dict, build `LapSegment` objects from each classified DataFrame (convert DataFrame to `dict[str, list]` replacing NaN with None, populate `is_invalid`, `sample_count`, `start_timestamp`, `end_timestamp`, `start_norm_pos`, `end_norm_pos`; set `corners=[]`, `active_setup=None`, `quality_warnings=[]` as placeholders), assemble `ParsedSession` — `backend/ac_engineer/parser/session_parser.py`
- [x] T01X [P] [US1] Write US1 integration tests in `backend/tests/parser/test_session_parser.py`: use `minimal_session_files`, `zero_laps_files`, `all_invalid_files`, `crash_session_files` fixtures; assert correct lap count, correct classifications, `is_invalid` flags, no samples lost, `ParsedSession.metadata` fields populated, crash session derives `total_samples` from CSV row count — `backend/tests/parser/test_session_parser.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_lap_segmenter.py backend/tests/parser/test_session_parser.py` passes. US1 independently deliverable.

---

## Phase 4: User Story 2 — Setup-Stint Association and Setup Parsing (Priority: P2)

**Goal**: Each `LapSegment.active_setup` references the correct `SetupEntry` with all `.ini`
parameters fully parsed. Legacy v1.0 metadata is transparently upgraded.

**Independent Test**: Run `test_setup_parser.py` and the US2 scenarios in `test_session_parser.py`.
Verify: correct setup association at lap boundaries, all parameters present for a 40-parameter
mod ini, v1.0 metadata produces identical output to v2.0 single-entry equivalent.

- [x] TXXX [P] [US2] Implement `parse_ini(ini_text: str | None) -> list[SetupParameter]` in `backend/ac_engineer/parser/setup_parser.py`: use Python `configparser` (or manual line parsing) to extract all `[section]` + `key=value` pairs; try to cast value to `float` first, keep as `str` if not parseable; strip whitespace from section/name/value; return empty list for None/empty input; skip comments and blank lines — `backend/ac_engineer/parser/setup_parser.py`
- [x] TXXX [P] [US2] Implement `associate_setup(lap_number: int, setup_entries: list[SetupEntry]) -> SetupEntry | None` in `backend/ac_engineer/parser/setup_parser.py`: return the `SetupEntry` with the highest `lap_start` that is ≤ `lap_number`; return `None` if `setup_entries` is empty — `backend/ac_engineer/parser/setup_parser.py`
- [x] TXXX [P] [US2] Write `backend/tests/parser/test_setup_parser.py`: test `parse_ini` with standard INI, multi-section, numeric values, non-numeric values (string stored as str), empty/None input, 40-parameter mod INI, comments and blank lines ignored; test `associate_setup` with 1/2/3 entries, lap at exact boundary, lap before first entry, empty entries list — `backend/tests/parser/test_setup_parser.py`
- [x] TXXX [US2] Integrate setup parsing into `backend/ac_engineer/parser/session_parser.py` (pipeline steps 6–7): build `SetupEntry` models by calling `parse_ini` for each `setup_history` entry's `contents`; call `associate_setup` for each lap and populate `LapSegment.active_setup`; store full `setups` list on `ParsedSession` — `backend/ac_engineer/parser/session_parser.py`
- [x] TXXX [P] [US2] Write US2 integration tests in `backend/tests/parser/test_session_parser.py`: use `multi_setup_files` (3 changes at laps 1, 6, 12) and `legacy_v1_files` fixtures; assert lap 5 references entry at lap 1, lap 7 references entry at lap 6, lap 15 references entry at lap 12; assert `legacy_v1` produces same `setup_history` shape as v2.0 single-entry equivalent — `backend/tests/parser/test_session_parser.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_setup_parser.py backend/tests/parser/test_session_parser.py` passes. US1 + US2 independently deliverable.

---

## Phase 5: User Story 3 — Corner Detection Across Laps (Priority: P2)

**Goal**: Each `LapSegment.corners` contains session-consistent `CornerSegment` objects with
correct entry/apex/exit positions. Corner N in lap 1 matches corner N in lap 5 within ±5%.

**Independent Test**: Run `test_corner_detector.py` and the US3 scenarios in `test_session_parser.py`.
Verify: 10-corner track produces exactly 10 corners per lap, chicane detects 2 separate corners,
oval detects 2 corners with no phantoms, apex positions consistent across laps within ±0.05.

- [x] TXXX [P] [US3] Implement `compute_session_thresholds(session_df: pd.DataFrame, sample_rate: float) -> dict` in `backend/ac_engineer/parser/corner_detector.py`: compute `g_threshold = np.nanpercentile(abs(g_lat), 80)` and `steer_threshold = np.nanpercentile(abs(steering), 70)` across all session rows; if `g_lat` is all-NaN set `g_threshold = 0.0` (reduced mode flag); return `{"g_threshold": float, "steer_threshold": float, "reduced_mode": bool}` — `backend/ac_engineer/parser/corner_detector.py`
- [x] TXXX [P] [US3] Implement `build_reference_map(lap_df: pd.DataFrame, thresholds: dict, sample_rate: float) -> list[float]` in `backend/ac_engineer/parser/corner_detector.py`: run the cornering-sample detection and merging algorithm (mark samples where `abs(g_lat) > g_threshold*0.6` AND `abs(steering) > steer_threshold*0.4`, or steering-only if reduced mode; merge runs with gap < `sample_rate*0.3` samples; discard runs shorter than `sample_rate*0.5` samples; find apex = min speed index per run); return ordered list of apex `normalized_position` values — `backend/ac_engineer/parser/corner_detector.py`
- [x] TXXX [US3] Implement `detect_corners(lap_df, reference_apexes, thresholds, sample_rate) -> list[CornerSegment]` in `backend/ac_engineer/parser/corner_detector.py`: run the same detection algorithm on the lap; match each detected corner's apex to the nearest reference apex (within 0.05 tolerance); assign the reference corner number; build `CornerSegment` with entry/apex/exit norm positions and speeds; preserve chicane separation by NOT merging runs of opposite `g_lat` sign; return list ordered by `corner_number` — `backend/ac_engineer/parser/corner_detector.py`
- [x] TXXX [P] [US3] Write `backend/tests/parser/test_corner_detector.py`: test `compute_session_thresholds` with normal data and all-NaN g_lat (reduced mode); test `build_reference_map` with synthetic 10-corner lap, oval (2 corners), chicane (2 tight direction changes), flat straight (0 corners); test `detect_corners` with consistent apex alignment (within ±0.05), chicane produces 2 corners, phantom-free straight, reduced mode fallback — `backend/tests/parser/test_corner_detector.py`
- [x] TXXX [US3] Integrate corner detection into `backend/ac_engineer/parser/session_parser.py` (pipeline step 8): after lap segmentation, call `compute_session_thresholds` on the full session DataFrame; select reference lap (first flying lap, else first outlap, else skip); call `build_reference_map` on reference lap; call `detect_corners` for each lap and populate `LapSegment.corners`; if no reference lap found, set `corners=[]` for all laps — `backend/ac_engineer/parser/session_parser.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_corner_detector.py` passes. US1 + US2 + US3 independently deliverable.

---

## Phase 6: User Story 4 — Data Quality Flagging (Priority: P3)

**Goal**: Each `LapSegment.quality_warnings` contains all detected quality issues as named
`QualityWarning` objects. No laps are silently dropped. Bad laps are flagged, not removed.

**Independent Test**: Run `test_quality_validator.py` and the US4 scenarios in `test_session_parser.py`.
Verify: all 5 warning types generated for intentional anomalies, clean laps have empty warnings list,
incomplete last lap carries `incomplete` warning, crash session's last lap is `incomplete`.

- [x] TXXX [P] [US4] Implement `validate_lap(lap_df: pd.DataFrame, sample_rate: float, is_last: bool) -> list[QualityWarning]` in `backend/ac_engineer/parser/quality_validator.py`: check all 5 conditions using module-level configurable constants (`TIME_GAP_THRESHOLD=0.5`, `POSITION_JUMP_THRESHOLD=0.05`, `ZERO_SPEED_THRESHOLD=1.0`, `ZERO_SPEED_DURATION=3.0`, `ZERO_SPEED_MIN=0.10`, `ZERO_SPEED_MAX=0.90`); for each triggered condition build a `QualityWarning` with `warning_type`, `normalized_position` of first occurrence, and `description`; `is_last=True` adds `incomplete` warning automatically — `backend/ac_engineer/parser/quality_validator.py`
- [x] TXXX [P] [US4] Write `backend/tests/parser/test_quality_validator.py`: inject each anomaly type into a synthetic DataFrame (gap > 0.5s, position jump > 0.05, zero-speed 4s between 10%–90% norm_pos, is_last=True, duplicate timestamp); verify each produces exactly the right `WarnType`; verify clean lap produces empty list; verify threshold boundary values (gap = 0.49s → no warning, gap = 0.51s → warning) — `backend/tests/parser/test_quality_validator.py`
- [x] TXXX [US4] Integrate quality validation into `backend/ac_engineer/parser/session_parser.py` (pipeline step 5): call `validate_lap(lap_df, sample_rate, is_last)` for each lap segment and assign result to `LapSegment.quality_warnings`; `is_last=True` only for the final segment; propagate `position_jump` anomaly to set `is_invalid=True` on the affected lap — `backend/ac_engineer/parser/session_parser.py`
- [x] TXXX [P] [US4] Write US4 integration tests in `backend/tests/parser/test_session_parser.py`: use `data_gaps_files` and `crash_session_files` fixtures; assert lap with injected 2s gap has `time_series_gap` warning; assert lap with position jump has `position_jump` warning and `is_invalid=True`; assert crash session's last lap has `incomplete` warning; assert no laps dropped — `backend/tests/parser/test_session_parser.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_quality_validator.py` passes. US1–US4 independently deliverable.

---

## Phase 7: User Story 5 — Cached Session Access (Priority: P3)

**Goal**: `save_session()` + `load_session()` produce a round-trip identical `ParsedSession`.
Downstream tools never need to re-parse the raw CSV.

**Independent Test**: Run `test_cache.py`. Parse a `minimal_session`, save to tmp dir, reload,
and assert the reloaded `ParsedSession` is field-for-field identical to the original.

- [x] TXXX [P] [US5] Implement `save_session(session, output_dir, base_name=None) -> Path` in `backend/ac_engineer/parser/cache.py`: create `output_dir/<base_name>/` subdirectory; build a single DataFrame from all `LapSegment.data` dicts with `lap_number` int column prepended and write to `telemetry.parquet` via pyarrow; build `session.json` dict with `format_version="1.0"`, `session` (SessionMetadata.model_dump()), `setups` (list of SetupEntry dicts with parameters), `laps` (list of lap dicts excluding `data` field, using `active_setup_index` integer instead of full object); write JSON; return session dir path — `backend/ac_engineer/parser/cache.py`
- [x] TXXX [P] [US5] Implement `load_session(session_dir: Path) -> ParsedSession` in `backend/ac_engineer/parser/cache.py`: read `session.json`, validate `format_version == "1.0"` (raise `ValueError` otherwise); read `telemetry.parquet` with pandas; for each lap entry in JSON, filter parquet by `lap_number`, convert to `dict[str, list]` (replacing NaN with None), resolve `active_setup_index` back to `SetupEntry` reference; reconstruct all Pydantic models and return `ParsedSession` — `backend/ac_engineer/parser/cache.py`
- [x] TXXX [P] [US5] Write `backend/tests/parser/test_cache.py`: test `save_session` creates both files with correct structure; test `load_session` round-trip identity for all `ParsedSession` fields (metadata, lap count, classifications, is_invalid, corners, setup associations, quality warnings, data values); test NaN values preserved as None in `data` dict; test `format_version` mismatch raises `ValueError`; test missing files raise `FileNotFoundError` — `backend/tests/parser/test_cache.py`
- [x] TXXX [US5] Write US5 integration tests in `backend/tests/parser/test_session_parser.py`: parse `minimal_session_files`, call `save_session`, call `load_session`, assert all fields identical; parse `multi_setup_files`, do same round-trip, assert setup associations and corner segments preserved — `backend/tests/parser/test_session_parser.py`

**Checkpoint**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_cache.py` passes. All 5 user stories independently deliverable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Full test suite, docstrings, remaining integration scenarios, and final validation.

- [x] TXXX [P] Write remaining `test_session_parser.py` integration scenarios not yet covered: `legacy_v1_files` (verify v1.0→v2.0 upgrade), `reduced_mode_files` (28 NaN channels marked unavailable, corner detection uses steering fallback), `all_invalid_files` (all laps have is_invalid=True, none dropped) — `backend/tests/parser/test_session_parser.py`
- [x] TXXX [P] Add docstrings to all public functions across parser modules per constitution §Documentation Standards: each function in `session_parser.py`, `lap_segmenter.py`, `corner_detector.py`, `setup_parser.py`, `quality_validator.py`, `cache.py` must have a docstring with purpose, args, and returns — all `backend/ac_engineer/parser/*.py` files
- [x] TXXX Run full test suite and fix any failures: `conda run -n ac-race-engineer pytest backend/tests/parser/ -v` — all tests must pass before this task is marked complete — terminal
- [x] TXXX [P] Update `specs/003-telemetry-parser/plan.md`: replace D5 section text with final resolved approach (`is_invalid` boolean field added, `invalid` classification retained for non-pit pure-invalid laps) — `specs/003-telemetry-parser/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **Phase 3 (US1)**: Depends on Phase 2 — no dependency on other user stories
- **Phase 4 (US2)**: Depends on Phase 2 — no dependency on US1 (setup_parser is independent); integrates into session_parser.py after US1's pipeline is stable
- **Phase 5 (US3)**: Depends on Phase 2 — no dependency on US2; integrates into session_parser.py
- **Phase 6 (US4)**: Depends on Phase 2 — no dependency on US1/2/3; integrates into session_parser.py
- **Phase 7 (US5)**: Depends on Phase 2 — `save_session`/`load_session` are independent of US1–4; full round-trip test requires a complete `ParsedSession`, so integration test (T036) depends on US1–4 being merged
- **Phase 8 (Polish)**: Depends on all user story phases

### User Story Dependencies (within session_parser.py integration)

Each user story adds one or more pipeline steps to `session_parser.py`. The steps are independent
modules but integrate sequentially into the orchestrator:

```
US1 (T015–T017) → adds steps 1-4, 9  (segmentation + assembly)
US2 (T022)      → adds steps 6-7     (setup parsing + association)
US3 (T028)      → adds step 8        (corner detection)
US4 (T031)      → adds step 5        (quality validation)
```

Because each story modifies `session_parser.py`, the tasks T022, T028, T031 should be done
in story completion order to avoid merge conflicts. However each story's module files
(`setup_parser.py`, `corner_detector.py`, `quality_validator.py`) are fully independent
and can be written in parallel.

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 all run in parallel after T001
- **Phase 2**: T006, T007, T011 run in parallel; T008 unblocks T009, T010
- **Phase 3 (US1)**: T014 (tests) runs in parallel with T012–T013 (implementation)
- **Phase 4 (US2)**: T019, T020, T021 all run in parallel; T023 (integration test) in parallel with T022
- **Phase 5 (US3)**: T024, T025, T027 run in parallel; T026 depends on T025
- **Phase 6 (US4)**: T029, T030, T032 run in parallel
- **Phase 7 (US5)**: T033, T034, T035 all run in parallel
- **Phase 8**: T037, T038, T040 run in parallel; T039 is sequential (needs all tests written)

---

## Parallel Example: Phase 4 (US2)

```
Parallel group A — start together:
  Task T019: parse_ini() in backend/ac_engineer/parser/setup_parser.py
  Task T020: associate_setup() in backend/ac_engineer/parser/setup_parser.py
  Task T021: test_setup_parser.py tests

Sequential after A:
  Task T022: integrate into session_parser.py
  Task T023: US2 integration tests in test_session_parser.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational — T006, T007, T008, T009, T010, T011 (models + fixtures)
3. Complete Phase 3: US1 (T012–T018)
4. **STOP and VALIDATE**: `conda run -n ac-race-engineer pytest backend/tests/parser/test_lap_segmenter.py backend/tests/parser/test_session_parser.py`
5. `parse_session()` returns a `ParsedSession` with correct laps, classifications, and `is_invalid` flags — MVP deliverable

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. US1 → parse + segment + classify → **MVP**
3. US2 → add setup associations → AI Engineer can start consuming data
4. US3 → add corners → Analyzer can compute per-corner metrics
5. US4 → add quality warnings → full data integrity flagging
6. US5 → add cache → Parquet+JSON round-trip complete
7. Polish → full test suite, docstrings, spec doc updates

### Suggested Parallel Team Strategy

With two developers after Phase 2 completes:

- **Dev A**: US1 (T012–T018) → US4 (T029–T032)
- **Dev B**: US2 (T019–T023) → US3 (T024–T028)
- **Both**: US5 (T033–T036), then Phase 8

---

## Notes

- All Python commands must use `conda run -n ac-race-engineer` or activate the env first
- The existing `src/` directory stubs are not modified by this feature
- `backend/` is the authoritative source location per CLAUDE.md and constitution §Project Structure
- Fixture CSV/meta.json files are generated programmatically in `conftest.py` — no game installation required for tests
- Real session files in `data/sessions/` can be used for optional smoke tests via a `@pytest.mark.integration` mark (skip in CI)
- [P] tasks write to different files — confirmed no shared state conflicts within each phase

---

## Task Summary

| Phase | Tasks | [P] tasks | Story |
|-------|-------|-----------|-------|
| Phase 1: Setup | T001–T005 | 4 | — |
| Phase 2: Foundational | T006–T011 | 4 | — |
| Phase 3: US1 (P1) | T012–T018 | 2 | US1 |
| Phase 4: US2 (P2) | T019–T023 | 3 | US2 |
| Phase 5: US3 (P2) | T024–T028 | 3 | US3 |
| Phase 6: US4 (P3) | T029–T032 | 3 | US4 |
| Phase 7: US5 (P3) | T033–T036 | 3 | US5 |
| Phase 8: Polish | T037–T040 | 3 | — |
| **Total** | **40 tasks** | **25 [P]** | |
