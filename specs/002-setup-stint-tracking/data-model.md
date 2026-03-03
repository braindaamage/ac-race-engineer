# Data Model: Setup Stint Tracking

**Feature**: 002-setup-stint-tracking
**Date**: 2026-03-03

This document extends and partially supersedes the data model from `specs/001-telemetry-capture/data-model.md`. Only the entities that change are described here. All other entities (`TelemetrySample`, `AppConfig`, `SampleBuffer`, `ChannelDefinition`, and the Recording State Machine) are unchanged.

---

## Modified Entity: SessionMetadata

The `SessionMetadata` entity gains one field and loses three. The `setup_history` list replaces `setup_filename`, `setup_contents`, and `setup_confidence`.

### Removed Fields

| Field | Reason |
|---|---|
| `setup_filename` | Superseded by `setup_history[*].filename` |
| `setup_contents` | Superseded by `setup_history[*].contents` |
| `setup_confidence` | Superseded by `setup_history[*].confidence` |

### Added Field

| Field | Type | Source | Notes |
|---|---|---|---|
| `setup_history` | list[SetupHistoryEntry] | see below | Ordered list of setup capture events, always ≥1 entry. Never null. |

### Full Updated Field Table

| Field | Type | Source | Notes |
|---|---|---|---|
| app_version | string | hardcoded constant | e.g. "0.1.0" |
| session_start | string | `time.strftime()` | ISO 8601 format |
| session_end | string | `time.strftime()` | ISO 8601, written at finalization; null if crashed |
| car_name | string | `ac.getCarName(0)` | AC internal identifier |
| track_name | string | `ac.getTrackName(0)` | AC internal identifier |
| track_config | string | `ac.getTrackConfiguration(0)` | layout variant, may be empty string |
| track_length_m | float | `ac.getTrackLength(0)` | meters |
| session_type | string | `info.graphics.session` | "practice", "qualify", "race", etc. |
| tyre_compound | string | `ac.getCarTyreCompound(0)` | e.g. "Soft" |
| laps_completed | int | `acsys.CS.LapCount` | at session end; null if crashed |
| total_samples | int | computed | total rows written to CSV; null if crashed |
| sample_rate_hz | float | computed | actual avg samples/second; null if crashed |
| air_temp_c | float | `info.physics.airTemp` | Celsius; null if unavailable |
| road_temp_c | float | `info.physics.roadTemp` | Celsius; null if unavailable |
| driver_name | string | `ac.getDriverName(0)` | player name |
| **setup_history** | **list** | **see SetupHistoryEntry** | **replaces setup_filename/contents/confidence** |
| channels_available | list[string] | computed | channels that returned valid data |
| channels_unavailable | list[string] | computed | channels that returned NaN |
| sim_info_available | bool | computed | whether shared memory was accessible |
| reduced_mode | bool | computed | true if sim_info failed to load |
| tyre_temp_zones_validated | bool | computed | true if inner/mid/outer tyre temps read non-zero |
| csv_filename | string | computed | corresponding .csv filename |

---

## New Entity: SetupHistoryEntry

A single record in the `setup_history` list. Represents one setup capture event — either the initial read at session start or a re-read triggered by a pit exit.

| Field | Type | Required | Notes |
|---|---|---|---|
| timestamp | string | yes | ISO 8601 local time of the capture event |
| trigger | string | yes | "session_start" or "pit_exit" |
| lap | int | yes | Lap count at the moment of capture (`acsys.CS.LapCount`) |
| filename | string | no | Base filename of the captured setup file; null if no setup found or read failed |
| contents | string | no | Complete raw `.ini` text; null if no setup found or read failed |
| confidence | string | no | "high", "medium", "low", or null if no setup found or read failed |

### Invariants

- `setup_history` is always a JSON array (never null, never absent from the metadata object).
- `setup_history[0].trigger` is always `"session_start"`.
- All entries after index 0 have `trigger = "pit_exit"`.
- Entries are ordered chronologically (ascending by `timestamp` and `lap`).
- No two consecutive entries have identical `contents` (deduplication: a new entry is only appended if contents differ from the previous entry's contents, including the case where both are null).

### Lookup Pattern

To find the active setup for any given lap `N`:

```
active = None
for entry in setup_history:
    if entry["lap"] <= N:
        active = entry
# active is now the setup that was in use at lap N
```

---

## New Runtime State: PitExitTracker

Runtime-only state tracked in `ac_race_engineer.py` during a recording session. Not persisted to any file.

| Field | Type | Initial Value | Notes |
|---|---|---|---|
| `_was_in_pitlane` | bool | False | Set to current pit lane status when recording starts; updated each frame |

### Pit Exit Detection Logic

Each `acUpdate()` call during `STATE_RECORDING`:

```
current_in_pitlane = bool(ac.isCarInPitlane(0))

if _was_in_pitlane and not current_in_pitlane:
    → PIT EXIT EVENT: trigger setup re-read

_was_in_pitlane = current_in_pitlane
```

---

## Revised Confidence Scoring Rules

Replaces the rules in `specs/001-telemetry-capture/research.md` R-004.

| Condition | Confidence | Rationale |
|---|---|---|
| 1 file found in `setups/{car}/{track}/` | `"high"` | Single unambiguous match in the correct location |
| 2+ files found in `setups/{car}/{track}/` | `"medium"` | Correct location but ambiguous; most recent selected |
| Files found only in `setups/{car}/` | `"low"` | Generic fallback; may not be track-specific |
| No `.ini` files found anywhere | `null` | No setup data available |

Modification timestamp is used **only as a selection tiebreaker** when multiple files exist in the same directory. It does not influence the confidence level.

---

## State Transition Extension

The Recording State Machine from feature 001 is unchanged. Pit exit detection is an **inline event handler** within `STATE_RECORDING`, not a new state. The machine remains:

```
IDLE → RECORDING → FINALIZING → IDLE
```

Pit exit handling fires during `STATE_RECORDING` between the session-end check and the sampling throttle check. It does not cause a state transition.

```
acUpdate() during STATE_RECORDING:
  1. Check session end → FINALIZING (if true, return)
  2. Check pit exit → append setup history entry + rewrite metadata (if exit detected)
  3. Check sampling throttle → sample + buffer flush (if interval elapsed)
```
