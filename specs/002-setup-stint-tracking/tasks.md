# Tasks: Setup Stint Tracking

**Input**: Design documents from `specs/002-setup-stint-tracking/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — constitution requires unit tests for logic changes; existing project has a full test suite to maintain.

**Organization**: Tasks are grouped by user story. US1 (confidence fix) and US2 (pit exit detection) touch different files and can proceed in parallel after the foundational phase.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no competing edits)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Confirm baseline is green before any changes land.

- [X] T001 Run `conda activate ac-race-engineer && pytest tests/telemetry_capture/ -v` and confirm all tests pass before any changes are made

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Version bump that must ship with this feature so downstream tools can detect the new schema by `app_version`.

**⚠️ CRITICAL**: Must complete before either user story ships to production.

- [X] T002 Bump `APP_VERSION` from `"0.1.0"` to `"0.2.0"` in `ac_app/ac_race_engineer/ac_race_engineer.py` (line 38)

**Checkpoint**: Version updated — user story implementation can now begin.

---

## Phase 3: User Story 1 — Track-Specific Setup Is Recognized as Reliable (Priority: P1) 🎯 MVP

**Goal**: A setup file in `setups/{car}/{track}/` always receives `"high"` or `"medium"` confidence, never `"low"`, regardless of file age. A file in the generic `setups/{car}/` folder always receives `"low"`.

**Independent Test**: Place one `.ini` file in the track-specific folder, set its mtime to 48 hours ago, run a session, and confirm `setup_history[0]["confidence"] == "high"` in the resulting `.meta.json`.

### Implementation for User Story 1

- [X] T003 [US1] Rewrite `_search_directory` in `ac_app/ac_race_engineer/modules/setup_reader.py`: remove the `now` parameter and `age_seconds` computation; replace the timestamp-threshold confidence block (lines 86–94) with the location+count rule: `is_track_specific + 1 file → "high"`, `is_track_specific + multiple files → "medium"`, `not is_track_specific → "low"`; also remove `now = time.time()` and the `now` argument in the `find_active_setup` caller

- [X] T004 [US1] Update `tests/telemetry_capture/unit/test_setup_reader.py`: (1) rename `test_confidence_low_old_file` → `test_confidence_high_single_old_file` and change its assertion from `"low"` to `"high"`, (2) add `test_confidence_high_old_single` with `age_seconds=48*3600` asserting `"high"`, (3) add `test_confidence_medium_old_multiple` with two old files asserting `"medium"`

**Checkpoint**: US1 fully functional. Run `pytest tests/telemetry_capture/unit/test_setup_reader.py -v` — all tests green, including the three changed/new cases.

---

## Phase 4: User Story 2 — Setup Change After a Pit Stop Is Captured (Priority: P1)

**Goal**: Each pit exit during a recording session triggers a setup re-read. If the contents changed, a new entry is appended to `setup_history` in the metadata and the `.meta.json` is rewritten to disk immediately. If unchanged (including both null), no entry is added.

**Independent Test**: Start a session, pit, save a modified setup, exit pits, end session. The `.meta.json` has two entries in `setup_history` (trigger: `"session_start"` and `"pit_exit"`). Pit without changing → still only one entry.

### Implementation for User Story 2

- [X] T005 [US2] In `ac_app/ac_race_engineer/ac_race_engineer.py`, in `_start_recording`: remove the three flat fields `"setup_filename"`, `"setup_contents"`, `"setup_confidence"` from the `_session_metadata` dict and replace them with a `"setup_history"` key initialized to a one-element list: `[{"timestamp": ..., "trigger": "session_start", "lap": 0, "filename": setup_filename, "contents": setup_contents, "confidence": setup_confidence}]`

- [X] T006 [US2] In `ac_app/ac_race_engineer/ac_race_engineer.py`: add `_was_in_pitlane = False` to the module-level globals block; in `_start_recording`, initialize it by reading `bool(ac.isCarInPitlane(0))` inside a try/except (fall back to `False` on exception)

- [X] T007 [US2] In `ac_app/ac_race_engineer/ac_race_engineer.py`, implement `_on_pit_exit(car_name, track_name)`: read lap count via `ac.getCarState(0, acsys.CS.LapCount)`; call `find_active_setup(car_name, track_name)`; compare new `contents` against `_session_metadata["setup_history"][-1]["contents"]`; if equal (including `None == None` — FR-011 takes precedence over FR-012 in the null-null case: no entry appended), return without action; otherwise append a new `{"timestamp": ..., "trigger": "pit_exit", "lap": ..., "filename": ..., "contents": ..., "confidence": ...}` entry and call `write_early_metadata(_meta_filepath, _session_metadata)` in a try/except that logs a warning on IOError but does not set `_error_flag`

- [X] T008 [US2] In `ac_app/ac_race_engineer/ac_race_engineer.py`, in the `STATE_RECORDING` branch of `acUpdate`, after the `check_session_end` block and before the `_sample_interval` throttle check: read `current_in_pitlane = bool(ac.isCarInPitlane(0))` in a try/except; detect pit exit as `_was_in_pitlane and not current_in_pitlane`; call `_on_pit_exit(car_name, track_name)` on exit; update `_was_in_pitlane = current_in_pitlane`

- [X] T009 [P] [US2] Create `tests/telemetry_capture/unit/test_setup_history.py` with the following six test cases using monkeypatching and `tmp_path`: `test_history_initial_entry` (one entry after session start with valid setup), `test_history_initial_null_setup` (one entry after session start when no setup found — null fields), `test_pit_exit_with_change` (different contents → new entry appended, metadata file rewritten), `test_pit_exit_no_change` (identical contents → no new entry, metadata unchanged), `test_pit_exit_null_dedup` (previous entry has null contents, new read also returns null → no new entry; this is the FR-011-over-FR-012 clarification), `test_pit_exit_unreadable_file` (find_active_setup returns `(None, None, None)` but previous entry had real contents → null entry IS appended and metadata is rewritten)

**Checkpoint**: US2 fully functional. Run `pytest tests/telemetry_capture/unit/test_setup_history.py -v` — all six tests green.

---

## Phase 5: User Story 3 — Setup History Is Queryable by Stint (Priority: P2)

**Goal**: Any downstream tool can determine the active setup for any lap number by iterating `setup_history` without touching the CSV.

**Independent Test**: A `.meta.json` with three history entries (laps 0, 8, 15) returns the correct entry when queried for laps 0, 7, 8, 10, and 20 using the standard lookup pattern.

### Implementation for User Story 3

- [X] T010 [US3] Add `test_history_queryable_by_lap` to `tests/telemetry_capture/unit/test_setup_history.py`: build a three-entry history list (session_start at lap 0, pit_exit at lap 8, pit_exit at lap 15); implement the lookup pattern `active = [e for e in history if e["lap"] <= N][-1]` inline; assert: lap 0 → entry 0, lap 7 → entry 0, lap 8 → entry 1, lap 10 → entry 1, lap 15 → entry 2, lap 20 → entry 2

**Checkpoint**: US3 verified. The history data structure produced by US2 correctly supports per-stint setup attribution.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation pass.

- [X] T011 [P] Add the following deprecation header to the top of `specs/001-telemetry-capture/contracts/meta-json.md`, below the title: `> **DEPRECATED (v1.0)**: Superseded by specs/002-setup-stint-tracking/contracts/meta-json.md (v2.0). Fields setup_filename, setup_contents, setup_confidence no longer exist in files produced by app version 0.2.0+.`

- [X] T012 [P] Add a deprecation note to the `setup_filename`, `setup_contents`, and `setup_confidence` rows in the SessionMetadata table in `specs/001-telemetry-capture/data-model.md`, marking each as `**Removed in v2.0** — see specs/002-setup-stint-tracking/data-model.md`

- [X] T013 Run `conda activate ac-race-engineer && pytest tests/telemetry_capture/ -v` — confirm all tests pass (baseline tests from T001 still green, plus new tests from T004, T009, T010)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run immediately
- **Foundational (Phase 2)**: No dependencies — can run immediately after Phase 1
- **US1 (Phase 3)**: No dependency on Phase 2; can start immediately
- **US2 (Phase 4)**: T005–T008 are sequential within the phase; T009 is parallel (different file); T005 must precede T007 (T007 reads from `setup_history`)
- **US3 (Phase 5)**: Depends on T009 (file must exist before T010 appends to it)
- **Polish (Phase 6)**: T011 and T012 depend on nothing; T013 depends on all prior phases complete

### User Story Dependencies

- **US1 (P1)**: Independent — touches only `setup_reader.py` and its test file
- **US2 (P1)**: Independent — touches only `ac_race_engineer.py` and a new test file; calls `find_active_setup` which benefits from US1 but does not require it
- **US3 (P2)**: Depends on T009 (test file creation) — T010 appends to that file

### Within Phase 4 (Sequential Chain)

```
T005 → T006 → T007 → T008   (all in ac_race_engineer.py)
T009                          (parallel — separate test file)
```

T007 reads `_session_metadata["setup_history"]` initialized by T005.
T008 calls `_on_pit_exit` implemented by T007.
T006 adds `_was_in_pitlane` used by T008.

### Parallel Opportunities

- **T003 and T009** can run in parallel (different files: `setup_reader.py` vs `test_setup_history.py`)
- **T011 and T012** can run in parallel (different spec files)
- **US1 (Phase 3) and US2 (Phase 4)** can run in parallel if two contributors are available

---

## Parallel Example: US1 and US2 Simultaneously

```bash
# Contributor A works on US1:
T003: Rewrite _search_directory in setup_reader.py
T004: Update test_setup_reader.py

# Contributor B works on US2 in parallel:
T005 → T006 → T007 → T008: ac_race_engineer.py changes
T009: Create test_setup_history.py (parallel to T005-T008)
```

Both contributors merge; then Phase 5 and Phase 6 proceed.

---

## Implementation Strategy

### MVP First (US1 Only — 3 tasks)

1. T001: Confirm baseline green
2. T003: Fix confidence scoring
3. T004: Update tests
4. **STOP and VALIDATE**: `pytest tests/telemetry_capture/unit/test_setup_reader.py -v`

This alone fixes the immediate bug (track-specific setups incorrectly scored as "low") with zero risk to the rest of the app.

### Full Delivery (US1 + US2 + US3)

1. Phase 1: T001 (baseline)
2. Phase 2: T002 (version bump)
3. Phase 3: T003 → T004 (US1 complete)
4. Phase 4: T005 → T006 → T007 → T008, T009 in parallel (US2 complete)
5. Phase 5: T010 (US3 complete)
6. Phase 6: T011, T012 in parallel → T013 (final green)

### Rollback Safety

US1 (Phase 3) is fully isolated to `setup_reader.py` — it can be merged and deployed independently without US2. The metadata schema change (US2) is a breaking change; it must ship together with US2's full implementation (T005–T009). Never ship T005 alone (removes flat fields) without T007–T008 (restores the data via setup_history).

---

## Notes

- **FR-011 over FR-012 (null-null)**: When the previous history entry has `null` contents AND the pit exit re-read also returns `null`, FR-011 takes precedence — no new entry is appended. The equality check `contents == last_contents` naturally handles `None == None` → `True` in Python. Explicit documentation in T007 ensures the implementer does not add a special case that breaks this.
- All in-game code (T003, T005–T008) must remain Python 3.3 compatible — no f-strings, no `pathlib`, no type annotations.
- Tests (T004, T009, T010) run under Python 3.11 in the `ac-race-engineer` conda environment.
- [P] tasks marked for same-phase files: only T009 and T011/T012 are truly parallelizable; T003/T004 and T005–T008 sequences must be respected.
