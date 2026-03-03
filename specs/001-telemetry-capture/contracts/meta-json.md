# Contract: Session Metadata JSON

> **DEPRECATED (v1.0)**: Superseded by specs/002-setup-stint-tracking/contracts/meta-json.md (v2.0). Fields setup_filename, setup_contents, setup_confidence no longer exist in files produced by app version 0.2.0+.

**Feature**: 001-telemetry-capture
**Version**: 1.0

## Format

- **Encoding**: UTF-8
- **Format**: JSON object, single file
- **Pretty-printed**: yes (indent=2)
- **Extension**: `.meta.json`
- **Naming**: same base filename as corresponding `.csv`

## Schema

```json
{
  "app_version": "0.1.0",
  "session_start": "2026-03-02T14:30:00",
  "session_end": "2026-03-02T15:05:32",
  "car_name": "ks_ferrari_488_gt3",
  "track_name": "monza",
  "track_config": "",
  "track_length_m": 5793.0,
  "session_type": "practice",
  "tyre_compound": "Soft",
  "laps_completed": 12,
  "total_samples": 52500,
  "sample_rate_hz": 25.0,
  "air_temp_c": 24.0,
  "road_temp_c": 32.0,
  "driver_name": "PlayerName",
  "setup_filename": "aggressive_v2.ini",
  "setup_contents": "[TYRES]\nPRESSURE_LF=26.0\nPRESSURE_RF=26.0\n...",
  "setup_confidence": "high",
  "channels_available": ["throttle", "brake", "speed_kmh", "..."],
  "channels_unavailable": ["handbrake", "turbo_boost"],
  "sim_info_available": true,
  "reduced_mode": false,
  "tyre_temp_zones_validated": true,
  "csv_filename": "2026-03-02_1430_ks_ferrari_488_gt3_monza.csv"
}
```

## Field Definitions

| Field | Type | Required | Notes |
|---|---|---|---|
| app_version | string | yes | Semantic version of the capture app |
| session_start | string | yes | ISO 8601 local time |
| session_end | string | yes | ISO 8601 local time, null if crashed |
| car_name | string | yes | AC internal car identifier |
| track_name | string | yes | AC internal track identifier |
| track_config | string | yes | Track layout variant, empty string if none |
| track_length_m | float | yes | Track length in meters |
| session_type | string | yes | One of: "practice", "qualify", "race", "hotlap", "time_attack", "drift", "drag", "unknown" |
| tyre_compound | string | yes | Tyre compound name from AC |
| laps_completed | int | yes | Total laps completed in session |
| total_samples | int | yes | Total data rows written to CSV |
| sample_rate_hz | float | yes | Actual average samples/second (total_samples / session_duration) |
| air_temp_c | float | no | Ambient temperature, null if unavailable |
| road_temp_c | float | no | Track surface temperature, null if unavailable |
| driver_name | string | yes | Player name from AC |
| setup_filename | string | no | Name of setup file found, null if none |
| setup_contents | string | no | Complete raw .ini text, null if unavailable |
| setup_confidence | string | no | "high", "medium", "low", or null. See R-004 in research.md for criteria |
| channels_available | list | yes | Channel names that produced valid data |
| channels_unavailable | list | yes | Channel names that returned NaN/unavailable |
| sim_info_available | bool | yes | Whether shared memory was accessible |
| reduced_mode | bool | yes | true if sim_info failed to load (28 CSV channels unavailable). See R-011 |
| tyre_temp_zones_validated | bool | yes | true if inner/middle/outer tyre temps read non-zero values. false if zones unavailable (core temp still valid). See R-011 |
| csv_filename | string | yes | Name of the corresponding CSV file |

## Session Type Mapping

| `info.graphics.session` value | JSON string |
|---|---|
| -1 | "unknown" |
| 0 | "practice" |
| 1 | "qualify" |
| 2 | "race" |
| 3 | "hotlap" |
| 4 | "time_attack" |
| 5 | "drift" |
| 6 | "drag" |

## Write-Early Strategy

The `.meta.json` is written **twice** per session:

1. **At session start**: All known metadata is written with `session_end = null` and deferred fields set to null. This guarantees metadata exists on disk even if the game crashes.
2. **At session end**: The file is overwritten with finalized values (`session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`).

**Fields available at session start** (early write):
- `app_version`, `session_start`, `car_name`, `track_name`, `track_config`, `track_length_m`
- `session_type`, `tyre_compound`, `air_temp_c`, `road_temp_c`, `driver_name`
- `setup_filename`, `setup_contents`, `setup_confidence`
- `channels_available`, `channels_unavailable`, `sim_info_available`, `reduced_mode`, `tyre_temp_zones_validated`
- `csv_filename`

**Fields deferred until session end** (null in early write):
- `session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`

## Crash Behavior

If the session ends due to a game crash:
- The `.meta.json` **exists on disk** (written at session start) with `session_end = null`
- Downstream tools detect a crashed session by checking `session_end == null`
- A partial `.csv` will also exist on disk (from periodic flushes)
- `laps_completed`, `total_samples`, and `sample_rate_hz` will be null — downstream tools must derive these from the CSV if needed
- On next session start, the app does NOT overwrite existing files — new session creates new filenames
