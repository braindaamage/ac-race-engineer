# Implementation Plan: Setup Stint Tracking

**Branch**: `002-setup-stint-tracking` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-setup-stint-tracking/spec.md`

## Summary

Fix two bugs in the telemetry capture app's setup tracking: (1) confidence scoring incorrectly penalizes old timestamps on track-specific setup files, and (2) setup changes made during pit stops are never captured. The fix rewrites the confidence scoring function to use directory location as the primary signal, and adds frame-diff pit exit detection to trigger setup re-reads mid-session. Setup data moves from three flat metadata fields to an ordered `setup_history` list, enabling per-stint setup attribution in downstream analysis phases.

## Technical Context

**Language/Version**: Python 3.3.5 (AC embedded runtime) for all in-game app code; Python 3.11 (conda env `ac-race-engineer`) for tests only
**Primary Dependencies**: `os`, `time`, `glob`, `json` (Python 3.3 stdlib — no external packages)
**Storage**: JSON (.meta.json sidecar files), overwritten in-place at session start, pit exit, and session end
**Testing**: pytest 3.11 (conda env), existing mock layer for `ac`/`acsys` modules
**Target Platform**: Assetto Corsa in-game Python app (Windows, AC's embedded Python 3.3.5)
**Project Type**: In-game telemetry capture app (AC Python app)
**Performance Goals**: Pit exit detection overhead: O(1) per frame (single boolean comparison). Setup re-read at pit exit: <5ms (small file read, rare event). No impact on 25Hz sampling loop.
**Constraints**: Python 3.3 syntax only — no f-strings, no pathlib, no typing module. No new dependencies. Single-threaded execution.
**Scale/Scope**: 4 source files changed; 2 test files modified/created; 1 contract document updated.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Data Integrity First | ✅ PASS | Feature improves data quality. Null entries on read failure preserve session rather than crashing. |
| II. Car-Agnostic Design | ✅ PASS | No car-specific logic. Setup discovery is generic by directory path. |
| III. Setup File Autonomy | ✅ PASS | Read-only at capture time. No writes to setup files. No parameter validation needed. |
| IV. LLM as Interpreter | ✅ PASS | No LLM involvement. All logic is deterministic Python. |
| V. Educational Explanations | N/A | No explanations generated in this feature. |
| VI. Incremental Changes | N/A | No setup changes suggested in this feature. |
| VII. CLI-First MVP | N/A | In-game telemetry capture app, not CLI. |
| Quality Gates | ✅ PASS | Type annotations not applicable (Python 3.3 in-game code). Tests required for setup_reader and new setup history logic. |
| Development Environment | ✅ PASS | In-game code: AC Python 3.3 runtime (exempt from conda). Tests: must run in `conda activate ac-race-engineer`. |

**Post-design re-check**: No violations introduced in Phase 1 design. The mid-session metadata rewrite (FR-010) reuses existing `write_early_metadata` without new I/O patterns. The pit exit detector is a pure state comparison with no side effects beyond the setup re-read.

## Project Structure

### Documentation (this feature)

```text
specs/002-setup-stint-tracking/
├── plan.md              # This file
├── research.md          # Phase 0 complete
├── data-model.md        # Phase 1 complete
├── quickstart.md        # Phase 1 complete
├── contracts/
│   └── meta-json.md     # Phase 1 complete (v2.0, supersedes 001 contract)
└── tasks.md             # Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code (modified files only)

```text
ac_app/
└── ac_race_engineer/
    ├── ac_race_engineer.py          # Modified: pit exit detection, setup_history
    └── modules/
        └── setup_reader.py          # Modified: confidence scoring

tests/
└── telemetry_capture/
    └── unit/
        ├── test_setup_reader.py     # Modified: update confidence assertions
        └── test_setup_history.py    # New: pit exit + history logic

specs/
└── 001-telemetry-capture/
    └── contracts/
        └── meta-json.md             # Updated: deprecation note + pointer to v2.0
```

**Structure Decision**: Single project. All changes are within the existing `ac_app/` and `tests/` directory structure. No new directories required.

---

## Phase 0: Research

*Complete. See [research.md](research.md) for full decisions and rationale.*

**Summary of key decisions**:

- **R-001**: Confidence scoring uses location-first logic. Single file in track-specific dir → `"high"`. Multiple files → `"medium"`. Generic dir → `"low"`. Timestamp not used for confidence.
- **R-002**: Pit exit detected via `_was_in_pitlane` boolean transition (`True` → `False`) each frame. No debounce needed.
- **R-003**: Mid-session metadata rewrite reuses existing `write_early_metadata` — no new writer function needed.
- **R-004**: `setup_history` ordered list replaces three flat fields. Breaking change; no migration needed (Phase 2 not yet built).
- **R-005**: Content comparison via raw string equality after text-mode read. Consistent, simple, handles line-ending normalization.
- **R-006**: Two test files changed. One existing test assertion flipped. New tests for pit exit scenarios.

---

## Phase 1: Design & Contracts

*Complete. Artifacts in this specs directory.*

### Change 1: `setup_reader.py` — Confidence Scoring

**Current logic** (lines 86–94 of `_search_directory`):

```python
if is_track_specific:
    if len(ini_files) == 1 and age_seconds <= 60:
        confidence = "high"
    elif age_seconds <= 600:
        confidence = "medium"
    else:
        confidence = "low"
else:
    confidence = "low"
```

**Replacement logic**:

```python
if is_track_specific:
    if len(ini_files) == 1:
        confidence = "high"
    else:
        confidence = "medium"
else:
    confidence = "low"
```

The `age_seconds` variable (computed from `mtime`) is still needed for **sorting** — `ini_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)` remains unchanged (selects most recent when multiple files exist). Only the confidence assignment block changes.

The `now` parameter passed to `_search_directory` becomes unused after this change. It should be removed from the function signature for cleanliness, and the `now = time.time()` call in `find_active_setup` removed accordingly.

### Change 2: `ac_race_engineer.py` — Setup History + Pit Exit Detection

#### 2a. New module-level state

```python
_was_in_pitlane = False  # tracks previous frame's pit lane status
```

Reset to `False` in `_start_recording` (so a session starting inside pits doesn't immediately fire a false pit exit).

#### 2b. Metadata dict in `_start_recording`

Remove:
```python
"setup_filename": setup_filename,
"setup_contents": setup_contents,
"setup_confidence": setup_confidence,
```

Replace with:
```python
"setup_history": [
    {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(_session_start_time)),
        "trigger": "session_start",
        "lap": 0,
        "filename": setup_filename,
        "contents": setup_contents,
        "confidence": setup_confidence,
    }
],
```

#### 2c. New helper: `_on_pit_exit(car_name, track_name)`

Extract as a named function for testability:

```python
def _on_pit_exit(car_name, track_name):
    """Handle a pit exit event: re-read setup, append history entry if changed."""
    global _session_metadata, _meta_filepath

    now_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    try:
        lap = int(ac.getCarState(0, acsys.CS.LapCount))
    except Exception:
        lap = 0

    filename, contents, confidence = find_active_setup(car_name, track_name)

    last_contents = _session_metadata["setup_history"][-1]["contents"]
    if contents == last_contents:
        return  # No change — do not append

    _session_metadata["setup_history"].append({
        "timestamp": now_str,
        "trigger": "pit_exit",
        "lap": lap,
        "filename": filename,
        "contents": contents,
        "confidence": confidence,
    })

    try:
        write_early_metadata(_meta_filepath, _session_metadata)
    except IOError as e:
        _log("warn", "Cannot update metadata after pit exit: %s" % str(e))
```

**Error handling**: If `find_active_setup` raises unexpectedly, the exception propagates to `acUpdate`'s outer try/except, which sets the error flag. This is consistent with how other mid-session errors are handled.

If the file cannot be read (`find_active_setup` returns `(None, None, None)`), the entry is appended with null values as required by FR-012.

#### 2d. Pit exit detection in `acUpdate`

In the `STATE_RECORDING` branch, before the sampling throttle check:

```python
# Pit exit detection
try:
    current_in_pitlane = bool(ac.isCarInPitlane(0))
except Exception:
    current_in_pitlane = _was_in_pitlane  # assume no change on error

if _was_in_pitlane and not current_in_pitlane:
    _on_pit_exit(car_name, track_name)
    _log("info", "Pit exit detected at lap %d" % ...)

_was_in_pitlane = current_in_pitlane
```

**Placement**: After `check_session_end` (which returns early if session ended), before the `_sample_interval` throttle check. This ensures pit exits are detected every frame, not just on sampling frames.

#### 2e. `_start_recording` — initialize pit state

```python
global _was_in_pitlane
try:
    _was_in_pitlane = bool(ac.isCarInPitlane(0))
except Exception:
    _was_in_pitlane = False
```

Initializing from the current state rather than hardcoding `False` prevents a false pit exit if the session starts with the car physically in the pit lane (e.g., practice session starting from the garage).

### Change 3: Test Updates

#### `test_setup_reader.py` — assertions to change

| Test name | Old assertion | New assertion |
|---|---|---|
| `test_confidence_low_old_file` | `confidence == "low"` | `confidence == "high"` |

Also add:
- `test_confidence_high_old_single`: age_seconds=48*3600, one file → `"high"`
- `test_confidence_medium_old_multiple`: two files, both old → `"medium"`

Remove: the `now` parameter usage from any tests that directly call `_search_directory` (if applicable; the function signature change removes `now`).

#### `test_setup_history.py` — new file

Tests for the `_on_pit_exit` logic. Since this function calls `ac.getCarState`, `find_active_setup`, `write_early_metadata`, and modifies `_session_metadata`, it needs to be tested by directly calling the helper with a mocked `_session_metadata` dict, monkeypatched `find_active_setup`, and a temporary file path.

Test cases (maps to R-006):
- `test_pit_exit_no_change`: same contents → history unchanged
- `test_pit_exit_with_change`: different contents → new entry appended
- `test_pit_exit_file_unreadable`: `find_active_setup` returns `(None, None, None)` → null entry appended, no exception
- `test_pit_exit_metadata_written`: after change, `write_early_metadata` called with updated history
- `test_history_initial_entry`: `_start_recording` metadata dict has exactly one history entry
- `test_history_initial_null_setup`: `find_active_setup` returns `(None, None, None)` at start → null entry present

### Change 4: Update 001 contract document

Add deprecation header to `specs/001-telemetry-capture/contracts/meta-json.md`:

```markdown
> **DEPRECATED (v1.0)**: This contract is superseded by
> `specs/002-setup-stint-tracking/contracts/meta-json.md` (v2.0).
> Files produced by app version 0.2.0+ use the new schema.
> The fields `setup_filename`, `setup_contents`, `setup_confidence` no longer exist.
```

---

## Complexity Tracking

No constitution violations. No entries required.
