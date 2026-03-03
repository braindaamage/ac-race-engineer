# Contract: Session Metadata JSON (v2.0)

**Feature**: 002-setup-stint-tracking
**Version**: 2.0
**Supersedes**: `specs/001-telemetry-capture/contracts/meta-json.md` (v1.0)
**Breaking changes**: `setup_filename`, `setup_contents`, `setup_confidence` removed; `setup_history` added.

## Format

- **Encoding**: UTF-8
- **Format**: JSON object, single file
- **Pretty-printed**: yes (indent=2)
- **Extension**: `.meta.json`
- **Naming**: same base filename as corresponding `.csv`

## Schema

```json
{
  "app_version": "0.2.0",
  "session_start": "2026-03-03T14:30:00",
  "session_end": "2026-03-03T15:05:32",
  "car_name": "ks_ferrari_488_gt3",
  "track_name": "monza",
  "track_config": "",
  "track_length_m": 5793.0,
  "session_type": "race",
  "tyre_compound": "Soft",
  "laps_completed": 20,
  "total_samples": 90000,
  "sample_rate_hz": 25.0,
  "air_temp_c": 24.0,
  "road_temp_c": 32.0,
  "driver_name": "PlayerName",
  "setup_history": [
    {
      "timestamp": "2026-03-03T14:30:00",
      "trigger": "session_start",
      "lap": 0,
      "filename": "aggressive_v2.ini",
      "contents": "[TYRES]\nPRESSURE_LF=26.0\n...",
      "confidence": "high"
    },
    {
      "timestamp": "2026-03-03T14:52:11",
      "trigger": "pit_exit",
      "lap": 8,
      "filename": "aggressive_v3.ini",
      "contents": "[TYRES]\nPRESSURE_LF=27.0\n...",
      "confidence": "high"
    }
  ],
  "channels_available": ["throttle", "brake", "speed_kmh"],
  "channels_unavailable": ["handbrake", "turbo_boost"],
  "sim_info_available": true,
  "reduced_mode": false,
  "tyre_temp_zones_validated": true,
  "csv_filename": "2026-03-03_1430_ks_ferrari_488_gt3_monza.csv"
}
```

## Field Definitions

| Field | Type | Required | Notes |
|---|---|---|---|
| app_version | string | yes | Semantic version of the capture app |
| session_start | string | yes | ISO 8601 local time |
| session_end | string | yes | ISO 8601 local time; null if game crashed |
| car_name | string | yes | AC internal car identifier |
| track_name | string | yes | AC internal track identifier |
| track_config | string | yes | Track layout variant; empty string if none |
| track_length_m | float | yes | Track length in meters |
| session_type | string | yes | One of: "practice", "qualify", "race", "hotlap", "time_attack", "drift", "drag", "unknown" |
| tyre_compound | string | yes | Tyre compound name from AC |
| laps_completed | int | yes | Total laps completed; null if crashed |
| total_samples | int | yes | Total data rows written to CSV; null if crashed |
| sample_rate_hz | float | yes | Actual average samples/second; null if crashed |
| air_temp_c | float | no | Ambient temperature in Celsius; null if unavailable |
| road_temp_c | float | no | Track surface temperature in Celsius; null if unavailable |
| driver_name | string | yes | Player name from AC |
| setup_history | array | yes | Ordered list of SetupHistoryEntry objects; always ≥1 entry; never null |
| channels_available | list | yes | Channel names that produced valid data |
| channels_unavailable | list | yes | Channel names that returned NaN/unavailable |
| sim_info_available | bool | yes | Whether shared memory was accessible |
| reduced_mode | bool | yes | true if sim_info failed to load |
| tyre_temp_zones_validated | bool | yes | true if inner/middle/outer tyre temps read non-zero |
| csv_filename | string | yes | Name of the corresponding CSV file |

## SetupHistoryEntry Schema

Each element of `setup_history` conforms to:

| Field | Type | Required | Notes |
|---|---|---|---|
| timestamp | string | yes | ISO 8601 local time of capture event |
| trigger | string | yes | "session_start" or "pit_exit" |
| lap | int | yes | Lap count (`acsys.CS.LapCount`) at time of capture |
| filename | string | no | Base filename of setup `.ini`; null if not found or read failed |
| contents | string | no | Complete raw `.ini` text; null if not found or read failed |
| confidence | string | no | "high", "medium", "low", or null if not found or read failed |

### Confidence Level Rules

| Condition | Value |
|---|---|
| Exactly 1 `.ini` in `setups/{car}/{track}/` | "high" |
| 2+ `.ini` files in `setups/{car}/{track}/` | "medium" |
| Files found only in `setups/{car}/` | "low" |
| No `.ini` files found | null |

Modification timestamp is only used to select the most recently modified file when multiple candidates exist in the same directory. It does **not** affect confidence level.

## Invariants

- `setup_history` is always a JSON array — never null, never absent.
- `setup_history[0].trigger` is always `"session_start"`.
- All subsequent entries have `trigger = "pit_exit"`.
- Entries are ordered chronologically (ascending `lap` values).
- No two consecutive entries have identical `contents` values (deduplication applied at capture time).

## Per-Stint Lookup

To find the setup active at lap `N`:

```python
active = None
for entry in meta["setup_history"]:
    if entry["lap"] <= N:
        active = entry
# active holds the setup that was in effect at lap N
```

## Write Strategy

The `.meta.json` is written **two or more times** per session:

1. **At session start** (`session_start` trigger): Initial `setup_history` with one entry, deferred fields null.
2. **At each pit exit where setup changed** (`pit_exit` trigger): Full metadata rewritten with new `setup_history` entry appended; deferred fields remain null.
3. **At session end**: Final write with all deferred fields populated.

**Deferred fields** (null until session end):
- `session_end`, `laps_completed`, `total_samples`, `sample_rate_hz`

## Crash Behavior

If the game crashes:
- The `.meta.json` on disk reflects the last successful write (session start or most recent pit exit write).
- `session_end` is null — downstream tools detect crashed sessions by this field.
- `setup_history` contains all entries up to the last successful write.
- `laps_completed`, `total_samples`, `sample_rate_hz` are null.

## Migration from v1.0

Files produced by app version 0.1.0 use the v1.0 schema (flat `setup_filename`, `setup_contents`, `setup_confidence` fields). Files produced by app version 0.2.0+ use this schema.

Downstream tools should check for the presence of `setup_history` to determine which schema version the file uses:
- If `setup_history` exists → v2.0 schema
- If `setup_filename` exists → v1.0 schema (legacy)
