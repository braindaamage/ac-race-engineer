# Tasks: Telemetry Capture App

**Input**: Design documents from `/specs/001-telemetry-capture/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — the plan defines a full test structure with mock ac/acsys modules and unit tests for all pure logic modules.

**Organization**: Tasks grouped by user story (6 stories from spec.md). Each story is independently testable after completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **AC app code**: `ac_app/ac_race_engineer/` (distributable app folder)
- **AC app modules**: `ac_app/ac_race_engineer/modules/` (pure logic, testable)
- **Tests**: `tests/telemetry_capture/` (run in conda `ac-race-engineer` env)
- **All AC app code**: Python 3.3 compatible (no f-strings, no pathlib, no enum, no typing)
- **All test code**: Python 3.11+ (conda env)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and static configuration files

- [ ] T001 Create AC app directory structure: `ac_app/ac_race_engineer/` with `modules/__init__.py`, `DLLs/.gitkeep`, and test structure `tests/telemetry_capture/` with `mocks/__init__.py`, `unit/` directories per plan.md
- [ ] T002 [P] Create default `ac_app/ac_race_engineer/config.ini` per contracts/config-ini.md — `[SETTINGS]` section with `output_dir`, `sample_rate_hz=25`, `buffer_size=1000`, `flush_interval_s=30`, `log_level=info`
- [ ] T003 [P] Create test conftest.py in `tests/telemetry_capture/conftest.py` — add `ac_app/ac_race_engineer` and `ac_app/ac_race_engineer/modules` to `sys.path`, inject mock `ac` and `acsys` modules into `sys.modules` before test imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utility modules and test mocks that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement config reader in `ac_app/ac_race_engineer/modules/config_reader.py` — parse `config.ini` using `configparser`, return dict with defaults for missing keys, clamp `sample_rate_hz` to 20-30, clamp `buffer_size` to 100-5000, clamp `flush_interval_s` to 5-120, expand `~` in `output_dir` via `os.path.expanduser()`, handle missing file gracefully (all defaults). Python 3.3 compatible.
- [ ] T005 [P] Implement filename sanitizer in `ac_app/ac_race_engineer/modules/sanitize.py` — function `sanitize_name(name)` that lowercases, replaces spaces with underscores, replaces non-`[a-z0-9_]` chars with underscore, collapses consecutive underscores, strips leading/trailing underscores. Per contracts/csv-output.md sanitization rules. Python 3.3 compatible.
- [ ] T006a [P] Implement base shared memory wrapper in `ac_app/ac_race_engineer/sim_info.py` — define `SPageFilePhysics` ctypes Structure with standard fields only: `packetId`, `gas`, `brake`, `fuel`, `gear`, `rpms`, `steerAngle`, `speedKmh`, `velocity` (c_float*3), `accG` (c_float*3), `wheelSlip` (c_float*4), `wheelLoad` (c_float*4), `wheelsPressure` (c_float*4), `wheelAngularSpeed` (c_float*4), `tyreWear` (c_float*4), `tyreDirtyLevel` (c_float*4), `tyreCoreTemperature` (c_float*4), `camberRAD` (c_float*4), `suspensionTravel` (c_float*4), `drs`, `tc`, `heading`, `pitch`, `roll`, `cgHeight`, `carDamage` (c_float*5), `numberOfTyresOut`, `pitLimiterOn`, `abs`, `kersCharge`, `kersInput`, `autoShifterOn`, `rideHeight` (c_float*2). Define `SPageFileGraphic` with: `packetId`, `status`, `session`, `currentTime`, `lastTime`, `bestTime`, `split`, `completedLaps`, `position`, `iCurrentTime`, `iLastTime`, `iBestTime`, `sessionTimeLeft`, `distanceTraveled`, `isInPit`, `currentSectorIndex`, `lastSectorTime`, `numberOfLaps`, `tyreCompound`, `replayTimeMultiplier`, `normalizedCarPosition`, `carCoordinates` (c_float*3), `penaltyTime`, `flag`, `idealLineOn`. Define `SPageFileStatic` with: `_smVersion`, `_acVersion`, `numberOfSessions`, `numCars`, `carModel`, `track`, `playerName`, `playerSurname`, `playerNick`, `sectorCount`, `maxTorque`, `maxPower`, `maxRpm`, `maxFuel`, `suspensionMaxTravel` (c_float*4), `tyreRadius` (c_float*4). Use `_pack_ = 4` on all structs. Create `SimInfo` class that opens `mmap` handles for `acpmf_physics`, `acpmf_graphics`, `acpmf_static` and exposes `info.physics`, `info.graphics`, `info.static` via `from_buffer()`. Wrap entire module init in try/except ImportError for missing `_ctypes.pyd` — if import fails, export `info = None`. Python 3.3 compatible.
- [ ] T006b Extend SPageFilePhysics with AC 1.14+ fields in `ac_app/ac_race_engineer/sim_info.py` — append to the end of `SPageFilePhysics._fields_`: `turboBoost` (c_float), `ballast` (c_float), `airDensity` (c_float), `airTemp` (c_float), `roadTemp` (c_float), `tyreTempI` (c_float*4), `tyreTempM` (c_float*4), `tyreTempO` (c_float*4). These fields are appended after the base fields so they do not affect earlier field offsets. Also add `airTemp` (c_float) and `roadTemp` (c_float) to `SPageFileStatic` if not already present. Document the expected `ctypes.sizeof(SPageFilePhysics)` value in a comment. At `SimInfo.__init__`, compare `mmap` buffer size against `ctypes.sizeof(SPageFilePhysics)` — if mmap is smaller than expected (older AC version), log a warning that extended tyre temp fields may be unavailable. Python 3.3 compatible. Depends on T006a.
- [ ] T007 [P] Create mock ac module in `tests/telemetry_capture/mocks/ac.py` — stub functions: `getCarState(carIndex, channel)` returning configurable values (scalars, tuples of 3-4), `getCarName(i)`, `getTrackName(i)`, `getTrackConfiguration(i)`, `getTrackLength(i)`, `getDriverName(i)`, `getCarTyreCompound(i)`, `isCarInPitlane(i)`, `isCarInPit(i)`, `newApp(name)`, `addLabel(appId, text)`, `setSize`, `setPosition`, `setBackgroundColor`, `drawBackground`, `setBackgroundOpacity`, `setFontColor`, `setFontSize`, `setText`, `setTitle`, `log(msg)`. All return sensible defaults. Include mechanism to configure per-channel return values for testing.
- [ ] T008 [P] Create mock acsys module in `tests/telemetry_capture/mocks/acsys.py` — define `CS` class with all 60 channel constants (`SpeedMS=0` through `CamberDeg=59`) per research.md R-002. Define `WHEELS` class with `FL=0, FR=1, RL=2, RR=3`. Define `AERO` class if needed.
- [ ] T009 [P] Write unit tests for config_reader in `tests/telemetry_capture/unit/test_config_reader.py` — test: default values when no file, valid config parsing, out-of-range clamping, missing keys use defaults, malformed values use defaults, `~` expansion in output_dir
- [ ] T010 [P] Write unit tests for sanitize in `tests/telemetry_capture/unit/test_sanitize.py` — test: lowercase conversion, space→underscore, special char→underscore, consecutive underscore collapse, leading/trailing underscore strip, empty string, already-clean name, unicode characters

**Checkpoint**: Foundation ready — all utility modules and test infrastructure in place

---

## Phase 3: User Story 1 — Automatic Telemetry Recording (Priority: P1) MVP

**Goal**: The app automatically records a complete telemetry session (76 channels) to a properly named CSV file with a JSON metadata sidecar when the driver enters and exits any track session.

**Independent Test**: Enter any practice session in AC, drive for 10 seconds, exit to menu. Verify: (1) CSV file exists in output directory with correct filename pattern, (2) file has header row + 200-300 data rows, (3) `.meta.json` sidecar exists with matching filename and valid JSON schema.

**Satisfies**: FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-013, FR-014, FR-016

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement channel definitions in `ac_app/ac_race_engineer/modules/channels.py` — define `CHANNEL_DEFINITIONS` list of 76 channel dicts (name, source, reader_key, index, fallback) per data-model.md TelemetrySample table. Define `HEADER` list of column names in CSV column order per contracts/csv-output.md. Implement `read_all_channels(ac_module, sim_info_obj)` function that reads all channels and returns a list of values in header order. For multi-value channels (AccG→3, per-wheel→4), unpack into individual columns. Python 3.3 compatible.
- [ ] T012 [P] [US1] Implement sample buffer in `ac_app/ac_race_engineer/modules/buffer.py` — `SampleBuffer` class with `__init__(max_size)`, `append(sample_row)` adds row to internal list, `get_all()` returns copy and clears, `count` property, `clear()` method. Simple list-based storage. Python 3.3 compatible.
- [ ] T013 [P] [US1] Implement setup file reader in `ac_app/ac_race_engineer/modules/setup_reader.py` — function `find_active_setup(car_name, track_name)` that searches `Documents/Assetto Corsa/setups/{car_name}/{track_name}/*.ini` then `Documents/Assetto Corsa/setups/{car_name}/*.ini`, returns `(filename, contents, confidence)` tuple per research.md R-004. Confidence: "high" if single file in track dir modified within 60s of now, "medium" if most recent but multiple or older than 60s, "low" if only in generic dir or older than 10min, None if no files. Read file contents with `open(path, 'r').read()`. Handle IOError gracefully. Python 3.3 compatible.
- [ ] T014 [US1] Implement CSV and JSON writer in `ac_app/ac_race_engineer/modules/writer.py` — function `write_csv_header(filepath, header_list)` writes header row to new file; function `append_csv_rows(filepath, rows)` opens in append mode, writes rows via `csv.writer`, closes file; function `write_metadata(filepath, metadata_dict)` writes JSON with `indent=2`; function `generate_filename(car, track, timestamp)` returns `{date}_{time}_{sanitized_car}_{sanitized_track}` using sanitize module; function `ensure_output_dir(path)` calls `os.makedirs(path, exist_ok=True)`. Python 3.3 compatible.
- [ ] T015 [US1] Implement session lifecycle state machine in `ac_app/ac_race_engineer/modules/session.py` — `SessionManager` class with exactly 3 states: IDLE, RECORDING, FINALIZING per data-model.md state diagram. FLUSHING is NOT a state — flush operations occur inline within RECORDING without a state transition (the UI status module handles the yellow indicator independently). Methods: `check_session_start(car_name, track_name, session_status)` transitions IDLE→RECORDING if status is LIVE (2); `check_session_end(car_name, track_name, session_status)` transitions RECORDING→FINALIZING if status leaves LIVE or car/track changes; `finalize()` transitions FINALIZING→IDLE. Tracks current car/track names for change detection. Python 3.3 compatible.
- [ ] T016 [US1] Implement AC app entry point in `ac_app/ac_race_engineer/ac_race_engineer.py` — `acMain(ac_version)`: load config, attempt sim_info import, create app window, return app name. `acUpdate(deltaT)`: check session state, if RECORDING read channels and append to buffer, if FINALIZING do final flush and write metadata. `acShutdown()`: finalize if recording. Wire together config_reader, channels, buffer, writer, setup_reader, session modules. Import `ac` and `acsys` (only file to do so). Build session metadata dict per contracts/meta-json.md schema. Python 3.3 compatible.
- [ ] T017 [P] [US1] Write unit tests for channels in `tests/telemetry_capture/unit/test_channels.py` — test: HEADER list has exactly 76 entries matching contracts/csv-output.md column order, CHANNEL_DEFINITIONS covers all 76 channels, `read_all_channels` returns correct length, each channel type (scalar, 3-tuple, 4-tuple) is correctly unpacked
- [ ] T018 [P] [US1] Write unit tests for buffer in `tests/telemetry_capture/unit/test_buffer.py` — test: append increments count, get_all returns all rows and clears buffer, clear resets count to 0, empty buffer get_all returns empty list
- [ ] T019 [P] [US1] Write unit tests for writer in `tests/telemetry_capture/unit/test_writer.py` — test: CSV header matches contract, append rows produce valid CSV readable by csv.reader, JSON metadata matches contract schema (all required fields present), filename generation produces `{date}_{time}_{car}_{track}` pattern, ensure_output_dir creates nested directories
- [ ] T020 [P] [US1] Write unit tests for setup_reader in `tests/telemetry_capture/unit/test_setup_reader.py` — test: finds .ini in track-specific dir, falls back to generic dir, returns None when no setups exist, confidence "high"/"medium"/"low" based on timestamp and uniqueness, handles IOError gracefully
- [ ] T021 [P] [US1] Write unit tests for session state machine in `tests/telemetry_capture/unit/test_session.py` — test: IDLE→RECORDING on live status, RECORDING→FINALIZING on status change, RECORDING→FINALIZING on car/track change, FINALIZING→IDLE after finalize(), stays IDLE when not live

**Checkpoint**: MVP complete — app records a full session with all 76 channels to CSV + meta.json. Test by entering/exiting a practice session in AC.

---

## Phase 4: User Story 2 — Universal Car Compatibility (Priority: P1)

**Goal**: The app captures telemetry from ANY car (vanilla or mod) without crashing, writing NaN for unavailable channels and logging which channels are missing.

**Independent Test**: Run sessions with 3 different cars (vanilla Kunos car, popular mod, obscure mod). Verify each produces a valid CSV with correct header, NaN for missing channels, and `channels_unavailable` list in metadata.

**Satisfies**: FR-012, FR-021, FR-026, FR-027, FR-028

### Implementation for User Story 2

- [ ] T022 [US2] Add try/except wrapping with NaN fallback to all channel reader functions in `ac_app/ac_race_engineer/modules/channels.py` — wrap every `ac.getCarState()` call in try/except that returns `float('nan')` on failure. Wrap every `sim_info.physics.*` access similarly. Log first failure per channel at session start (not per-sample to avoid log spam). Python 3.3 compatible.
- [ ] T023 [US2] Implement reduced mode detection in `ac_app/ac_race_engineer/modules/channels.py` — at init, try importing sim_info; if ImportError set `reduced_mode=True` and define fallback readers for the 29 sim_info-only channels (all return NaN). Log warning with full list of unavailable channels per R-011 table.
- [ ] T024 [US2] Implement tyre temp zone validation in `ac_app/ac_race_engineer/modules/channels.py` — at first sample, read all 12 tyre temp zone values (`tyreTempI/M/O`). If ALL 12 are exactly 0.0, set `tyre_temp_zones_validated=False`, switch zone readers to return NaN, and log info message. Otherwise `tyre_temp_zones_validated=True`.
- [ ] T025 [US2] Add channel availability tracking in `ac_app/ac_race_engineer/modules/channels.py` — after first sample, build two lists: `channels_available` (names that returned valid data) and `channels_unavailable` (names that returned NaN). Store as module state. Include these in metadata dict built by entry point.
- [ ] T026 [US2] Update unit tests for compatibility features in `tests/telemetry_capture/unit/test_channels.py` — add tests: channel read returning exception produces NaN, reduced mode sets correct 29 channels to NaN and 47 to valid, tyre zone validation detects all-zero and sets flag, availability tracking correctly categorizes channels

**Checkpoint**: App handles any car gracefully. Missing channels produce NaN, metadata reports what's available.

---

## Phase 5: User Story 3 — Crash-Safe Data Persistence (Priority: P2)

**Goal**: At least 90% of captured data survives a game crash or force-close, and partial files from crashed sessions are never overwritten.

**Independent Test**: Start a session, drive for 5+ minutes, force-close AC. Verify: CSV file exists with data from periodic flushes, `.meta.json` exists (from write-early) with `session_end=null`. Start a new session — verify old files are preserved.

**Satisfies**: FR-017, FR-018

### Implementation for User Story 3

- [ ] T027 [US3] Add periodic flush logic to buffer in `ac_app/ac_race_engineer/modules/buffer.py` — add `last_flush_time` tracking, `is_flush_due(flush_interval_s)` checks elapsed time since last flush, `mark_flushed()` updates timestamp. Buffer signals flush needed when `count >= max_size` OR `is_flush_due()` returns True.
- [ ] T028 [US3] Implement write-early metadata in `ac_app/ac_race_engineer/modules/writer.py` — add function `write_early_metadata(filepath, metadata_dict)` that writes metadata with `session_end=null`, `laps_completed=null`, `total_samples=null`, `sample_rate_hz=null` per contracts/meta-json.md write-early strategy. Add function `write_final_metadata(filepath, metadata_dict)` that overwrites with all fields populated including computed `sample_rate_hz`.
- [ ] T029 [US3] Add file preservation logic in `ac_app/ac_race_engineer/modules/session.py` — before creating new session files, check if files with same base name already exist. If so, append a numeric suffix (e.g., `_2`, `_3`) to avoid overwriting. Never delete or overwrite existing CSV or meta.json files.
- [ ] T030 [US3] Wire flush and write-early into entry point in `ac_app/ac_race_engineer/ac_race_engineer.py` — in acUpdate: after appending sample to buffer, check `is_flush_due()` or `count >= max_size`; if true, call `append_csv_rows()` with buffer contents, call `buffer.mark_flushed()`. On session start (IDLE→RECORDING): write CSV header, call `write_early_metadata()`. On session end (FINALIZING): do final flush, call `write_final_metadata()`.
- [ ] T031 [US3] Update unit tests for crash safety in `tests/telemetry_capture/unit/test_buffer.py` and `tests/telemetry_capture/unit/test_writer.py` — add tests: `is_flush_due` returns True after interval, `is_flush_due` returns False before interval, `mark_flushed` resets timer, write-early metadata has null deferred fields, write-final metadata has all fields populated, file preservation appends suffix when file exists

**Checkpoint**: Data survives crashes. Periodic flushes + write-early metadata ensure >=90% data recovery.

---

## Phase 6: User Story 4 — Zero-Impact Performance (Priority: P2)

**Goal**: The app has zero perceptible impact on frame rate. Non-sampling frames return in <1ms. Disk I/O never blocks the game thread. Memory stays bounded.

**Independent Test**: Compare frame times with app enabled vs disabled over identical sessions. Verify no measurable difference. Run a 60+ minute session and verify memory does not grow.

**Satisfies**: FR-003, FR-022, FR-025

### Implementation for User Story 4

- [ ] T032 [US4] Implement time-based sampling throttle in `ac_app/ac_race_engineer/ac_race_engineer.py` — in acUpdate, compute `sample_interval = 1.0 / config['sample_rate_hz']`. Track `last_sample_time`. On each acUpdate call, if `current_time - last_sample_time < sample_interval`, return immediately (no channel reads, no allocations). Only read channels and append to buffer when interval has elapsed. This ensures 20-30Hz sampling regardless of 60-144+ fps render rate.
- [ ] T033 [US4] Enforce bounded buffer size in `ac_app/ac_race_engineer/modules/buffer.py` — ensure `append()` triggers immediate flush callback if buffer is at `max_size`. The buffer must NEVER exceed `max_size` rows in memory. Add safety check: if append called when full, log error and drop sample rather than grow unbounded.
- [ ] T034 [US4] Optimize non-sampling acUpdate path in `ac_app/ac_race_engineer/ac_race_engineer.py` — ensure the early return path (when not sampling) does minimal work: one `time.time()` call, one float comparison, one return. No object creation, no function calls beyond the timestamp check. Document performance contract in code comment.
- [ ] T035 [US4] Write unit tests for throttle and bounds in `tests/telemetry_capture/unit/test_buffer.py` — add tests: buffer refuses to exceed max_size, append at max_size triggers flush signal. (Throttle timing is verified via integration testing in AC.)

**Checkpoint**: App is performance-safe. Sampling throttle limits work to 20-30Hz, buffer is bounded, non-sampling frames are near-zero cost.

---

## Phase 7: User Story 5 — Organized Session Files (Priority: P3)

**Goal**: Each session is saved with a clearly named file following `{date}_{time}_{car}_{track}.csv` pattern. Multiple sessions on the same day/car/track produce unique filenames. Special characters are sanitized.

**Independent Test**: Run 3 sessions with different cars/tracks, and 2 sessions with the same car/track. Verify: all filenames follow the pattern, all are unique, special characters are sanitized, files are in the configured output directory.

**Satisfies**: FR-015, FR-019

### Implementation for User Story 5

- [ ] T036 [US5] Verify and harden filename generation in `ac_app/ac_race_engineer/modules/writer.py` — confirm `generate_filename()` uses `time.strftime('%Y-%m-%d_%H%M')` for date/time, calls `sanitize_name()` on car and track, joins with underscore. Ensure time precision to the minute guarantees uniqueness for non-concurrent sessions. Add docstring with example output.
- [ ] T037 [US5] Add edge case handling for filenames in `ac_app/ac_race_engineer/modules/sanitize.py` and `ac_app/ac_race_engineer/modules/writer.py` — handle: empty car/track name (use "unknown"), very long names (truncate to 50 chars before sanitization), names that sanitize to empty string (use "unknown"). Python 3.3 compatible.
- [ ] T038 [US5] Write unit tests for filename edge cases in `tests/telemetry_capture/unit/test_writer.py` and `tests/telemetry_capture/unit/test_sanitize.py` — add tests: empty name→"unknown", long name truncation, name with only special chars→"unknown", two filenames generated 1 minute apart are unique, unicode names produce valid ASCII filenames

**Checkpoint**: Session files are well-organized and discoverable by filename alone.

---

## Phase 8: User Story 6 — Visual Recording Status (Priority: P3)

**Goal**: A small in-game widget shows recording status: green (recording), yellow (flushing), red (error).

**Independent Test**: Observe the app widget during a session: green on track, briefly yellow during flushes, red if error occurs (simulate by making output dir read-only).

**Satisfies**: FR-020, FR-023

### Implementation for User Story 6

- [ ] T039 [P] [US6] Implement status indicator module in `ac_app/ac_race_engineer/modules/status.py` — define state constants: `STATUS_IDLE=0`, `STATUS_RECORDING=1`, `STATUS_FLUSHING=2`, `STATUS_ERROR=3`. Define color map: IDLE→(0.5, 0.5, 0.5), RECORDING→(0.0, 0.8, 0.0), FLUSHING→(0.9, 0.8, 0.0), ERROR→(0.8, 0.0, 0.0). Define text map: IDLE→"IDLE", RECORDING→"REC", FLUSHING→"FLUSH", ERROR→"ERR". Function `get_status_display(state)` returns `(text, r, g, b)`. Python 3.3 compatible.
- [ ] T040 [US6] Create AC app window and status label in `ac_app/ac_race_engineer/ac_race_engineer.py` acMain — call `ac.newApp("AC Race Engineer")`, `ac.setSize(window, 200, 60)`, `ac.setTitle(window, "")`, create label via `ac.addLabel()`, configure font size/color, enable background drawing. Store window and label IDs as globals.
- [ ] T041 [US6] Wire status updates into recording lifecycle in `ac_app/ac_race_engineer/ac_race_engineer.py` — in acUpdate: set status to RECORDING during normal sampling, FLUSHING during flush operations, ERROR on IOError/disk-full (catch exceptions from writer, set error flag, stop recording gracefully per FR-023). Call `ac.setBackgroundColor()` and `ac.setText()` with values from `status.get_status_display()`.
- [ ] T042 [US6] Write unit tests for status module in `tests/telemetry_capture/unit/test_status.py` — test: each state returns correct text and RGB tuple, all 4 states are covered, color values are floats in 0-1 range

**Checkpoint**: Visual feedback works. Driver can confirm recording at a glance.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, error handling, and documentation that span multiple stories

- [ ] T043 Implement disk-full error handling in `ac_app/ac_race_engineer/ac_race_engineer.py` — wrap all writer calls in try/except for IOError/OSError. On disk-full: set status to ERROR, stop recording (transition to IDLE), log error message via `ac.log()`. Do NOT crash the game. Per FR-023 and edge case spec.
- [ ] T044 Handle session edge cases in `ac_app/ac_race_engineer/ac_race_engineer.py` — short sessions (<5s): still save valid file with whatever samples exist. Session restart detection: if lap count drops to 0 and normalized position resets while car/track unchanged, finalize current session and start new one. Per spec edge cases.
- [ ] T045 Add AC logging throughout in `ac_app/ac_race_engineer/ac_race_engineer.py` and modules — use `ac.log()` for: session start/end with car/track, channel failures at session start, flush operations (debug level), errors. Respect `log_level` from config. Write to AC's `py_log.txt`.
- [ ] T046 Create installation README in `ac_app/ac_race_engineer/README.txt` — plain text (no markdown, AC users may view in Notepad). Cover: installation steps (copy folder), optional _ctypes.pyd setup, output file locations, config.ini options. Keep brief. Per quickstart.md content.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — this is the MVP
- **US2 (Phase 4)**: Depends on Phase 3 (T011 channels.py must exist to add error handling)
- **US3 (Phase 5)**: Depends on Phase 3 (T012 buffer.py and T014 writer.py must exist to add flush logic)
- **US4 (Phase 6)**: Depends on Phase 3 (T016 ac_race_engineer.py must exist to add throttle)
- **US5 (Phase 7)**: Depends on Phase 3 (T014 writer.py must exist to harden)
- **US6 (Phase 8)**: Depends on Phase 3 (T016 ac_race_engineer.py must exist to add UI)
- **Polish (Phase 9)**: Depends on all previous phases

### User Story Dependencies

```
Phase 1 (Setup) ──→ Phase 2 (Foundational) ──→ Phase 3 (US1 MVP)
                                                      │
                                                      ├──→ Phase 4 (US2) ──┐
                                                      ├──→ Phase 5 (US3) ──┤
                                                      ├──→ Phase 6 (US4) ──├──→ Phase 9 (Polish)
                                                      ├──→ Phase 7 (US5) ──┤
                                                      └──→ Phase 8 (US6) ──┘
```

- **US2, US3, US4, US5, US6** can all proceed in parallel after US1 is complete
- Recommended sequential order for a single implementer: US1 → US2 → US3 → US4 → US5 → US6 → Polish

### Within Each User Story

- Implementation tasks before test tasks
- Pure module tasks (marked [P]) can run in parallel within the same phase
- Entry point tasks (ac_race_engineer.py) depend on the module tasks in the same phase
- Test tasks depend on their corresponding implementation tasks

### Parallel Opportunities

**Phase 2** — 7 of 8 tasks can run in parallel; T006b depends on T006a:
```
Parallel:  T004 (config_reader) | T005 (sanitize) | T006a (sim_info base) | T007 (mock ac) | T008 (mock acsys) | T009 (test config) | T010 (test sanitize)
Then:      T006b (sim_info extended, depends on T006a)
```

**Phase 3** — Module implementations can run in parallel, then entry point, then tests:
```
Parallel:  T011 (channels) | T012 (buffer) | T013 (setup_reader)
Then:      T014 (writer, uses sanitize) | T015 (session)
Then:      T016 (entry point, wires all modules)
Parallel:  T017 | T018 | T019 | T020 | T021 (all tests)
```

**Phases 4-8** — After US1, all five can start simultaneously with different developers:
```
Developer A: Phase 4 (US2 — channels.py)
Developer B: Phase 5 (US3 — buffer.py, writer.py)
Developer C: Phase 6 (US4 — ac_race_engineer.py)
Developer D: Phase 7 (US5 — sanitize.py, writer.py)
Developer E: Phase 8 (US6 — status.py, ac_race_engineer.py)
```

Note: US4 and US6 both modify `ac_race_engineer.py` — if done in parallel, merge carefully.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (8 tasks)
3. Complete Phase 3: User Story 1 (11 tasks)
4. **STOP and VALIDATE**: Install app in AC, enter a practice session, drive 10 seconds, exit. Verify CSV and meta.json files.
5. MVP is functional — app records complete telemetry sessions

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. Add US1 → basic recording works → **MVP** (test in AC)
3. Add US2 → any car works → test with vanilla + mod cars
4. Add US3 → crash-safe → test by force-closing AC mid-session
5. Add US4 → performance-safe → verify no frame drops
6. Add US5 → clean filenames → verify naming across sessions
7. Add US6 → visual feedback → verify widget colors
8. Polish → edge cases and docs → final validation

### Suggested MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1)** = 22 tasks

This delivers a fully functional telemetry capture app that:
- Records all 76 channels at 25Hz
- Saves to properly named CSV + meta.json
- Captures active setup file
- Works for one complete session cycle

Everything after is hardening, resilience, and polish.

---

## Notes

- All AC app code MUST be Python 3.3 compatible — no f-strings, no pathlib, no enum, no typing
- Test code runs in Python 3.11+ conda env — modern syntax is fine
- `ac_race_engineer.py` is the ONLY file that imports `ac` and `acsys` modules
- All `modules/*.py` files are pure Python with no AC dependencies — this enables pytest testing
- Commit after each task or logical group of tasks
- Test in AC after completing each user story phase
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
