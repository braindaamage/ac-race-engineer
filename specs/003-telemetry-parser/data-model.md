# Data Model: Telemetry Parser

**Branch**: `003-telemetry-parser` | **Date**: 2026-03-03

---

## Entity Overview

```
ParsedSession
├── metadata: SessionMetadata
├── setups: list[SetupEntry]
│   └── parameters: list[SetupParameter]
└── laps: list[LapSegment]
    ├── data: dict[str, list]   ← 82-channel time series
    ├── corners: list[CornerSegment]
    ├── active_setup: SetupEntry | None   ← reference into setups list
    └── quality_warnings: list[QualityWarning]
```

---

## Entities

### `QualityWarning`

A data quality issue detected on a specific lap.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `warning_type` | `str` (enum) | one of 5 types (see below) | Machine-readable warning type |
| `normalized_position` | `float` | 0.0–1.0 | Track position where issue was detected |
| `description` | `str` | non-empty | Human-readable explanation |

**Warning types**:
- `time_series_gap` — consecutive samples more than 0.5 s apart
- `position_jump` — normalized position changed > 0.05 in a single sample
- `zero_speed_mid_lap` — speed ≤ 1 km/h for > 3 s between 10%–90% track position
- `incomplete` — lap segment has no closing lap count transition
- `duplicate_timestamp` — consecutive samples share the same timestamp

**State transitions**: None (immutable value object created by `quality_validator.py`).

---

### `SetupParameter`

One key-value parameter extracted from a setup `.ini` file.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `section` | `str` | non-empty | INI section name (e.g., `"FRONT"`) |
| `name` | `str` | non-empty | Parameter name (e.g., `"CAMBER"`) |
| `value` | `float \| str` | — | Numeric if parseable, string otherwise |

**Validation rules**:
- Section and name are stripped of whitespace and preserved as-is (no normalization
  to uppercase — preserve original casing from the `.ini` file).
- Non-numeric values (e.g., `"SOFT"`, `"enabled"`) are stored as `str`.
- Comments (`;` prefix) and blank lines are ignored.

---

### `SetupEntry`

One setup stint read from `setup_history`. Represents the active setup
configuration from `lap_start` until the next `SetupEntry` (or session end).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `lap_start` | `int` | ≥ 0 | Lap number when this setup became active |
| `trigger` | `str` | `"session_start"` or `"pit_exit"` | What caused the setup read |
| `confidence` | `str \| None` | `"high"/"medium"/"low"` or `None` | How confidently the file was identified |
| `filename` | `str \| None` | — | Original `.ini` filename, `None` if not found |
| `timestamp` | `str` | ISO 8601 | When the setup was captured |
| `parameters` | `list[SetupParameter]` | — | All parsed `.ini` parameters |

**Validation rules**:
- If `contents` (raw `.ini` text) was `None` in metadata, `parameters` is an
  empty list (no parameters to parse — not an error).
- `lap_start = 0` for the initial `session_start` entry.

**Relationships**:
- One `SetupEntry` is referenced by many `LapSegment` objects (the laps that ran
  under this setup).

---

### `CornerSegment`

One detected corner within a lap. Corner numbers are session-consistent (same
physical location across all laps in the session).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `corner_number` | `int` | ≥ 1 | Session-consistent corner number (1-indexed) |
| `entry_norm_pos` | `float` | 0.0–1.0 | Track position at corner entry |
| `apex_norm_pos` | `float` | 0.0–1.0 | Track position at apex (min speed) |
| `exit_norm_pos` | `float` | 0.0–1.0 | Track position at corner exit |
| `apex_speed_kmh` | `float` | ≥ 0 | Speed at apex in km/h |
| `max_lat_g` | `float` | ≥ 0 | Peak absolute lateral G in the corner |
| `entry_speed_kmh` | `float` | ≥ 0 | Speed at corner entry |
| `exit_speed_kmh` | `float` | ≥ 0 | Speed at corner exit |

**Validation rules**:
- `entry_norm_pos ≤ apex_norm_pos ≤ exit_norm_pos` (corners progress forward on
  track). Note: for corners that cross the start/finish (wrap-around), this
  invariant may be relaxed.
- `apex_speed_kmh ≤ entry_speed_kmh` and `apex_speed_kmh ≤ exit_speed_kmh`
  (apex is the slowest point).

---

### `LapSegment`

One lap's worth of telemetry data plus all derived structures.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `lap_number` | `int` | ≥ 0 | Lap count value from the `lap_count` channel |
| `classification` | `str` (enum) | one of 5 types | Lap type (see below) |
| `start_timestamp` | `float` | Unix epoch | First sample's `timestamp` value |
| `end_timestamp` | `float` | Unix epoch, > start | Last sample's `timestamp` value |
| `start_norm_pos` | `float` | 0.0–1.0 | `normalized_position` at first sample |
| `end_norm_pos` | `float` | 0.0–1.0 | `normalized_position` at last sample |
| `sample_count` | `int` | ≥ 1 | Number of samples in this lap |
| `data` | `dict[str, list]` | keys = channel names | Time-series data (82 columns) |
| `corners` | `list[CornerSegment]` | ordered by `corner_number` | Detected corners |
| `active_setup` | `SetupEntry \| None` | — | Setup active during this lap |
| `quality_warnings` | `list[QualityWarning]` | — | Detected data quality issues |

**Classification values**:
- `flying` — complete clean lap, no pit entry or exit
- `outlap` — first sample in pit lane, exits to track
- `inlap` — enters pit lane before next lap count increment
- `invalid` — AC `lap_invalid` flag set for any sample, or disqualifying anomaly
- `incomplete` — no closing lap count transition (first or last partial lap)

**Classification rules** (evaluated in priority order):
1. If first sample `in_pit_lane == 1` and last sample `in_pit_lane == 0` → `outlap`
2. If any sample `in_pit_lane == 1` AND the lap_count does not increment after
   → `inlap` (car is still in pits at session end); or if `in_pit_lane` goes
   from 0→1 within the lap → `inlap`
3. If no closing lap_count transition → `incomplete`
4. If any sample `lap_invalid == 1` → `invalid`
5. Otherwise → `flying`

Note: An outlap can also be `invalid` (e.g., driver cuts a lap during pit exit).
The classification priority ensures `outlap`/`inlap` are detected first; `invalid`
can be applied as an additional flag. Implementation: `is_invalid` boolean field
in addition to `classification`, or keep `classification` as the primary label.

**`data` field encoding**:
- Keys are the 82 channel names from `HEADER` in `channels.py`
- Values are `list[float | int | None]`, one entry per sample
- NaN values from reduced mode are stored as `None` in the serialized form
  (JSON-compatible); in-memory helpers use `float('nan')`
- Helper method: `LapSegment.to_dataframe() -> pd.DataFrame` reconstructs the
  DataFrame from the `data` dict (used by the Analyzer)

---

### `SessionMetadata`

Session-level context from the `.meta.json` file.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `car_name` | `str` | No | AC car identifier |
| `track_name` | `str` | No | AC track identifier |
| `track_config` | `str` | No | Track layout (empty string if no config) |
| `track_length_m` | `float` | Yes | Track length in metres |
| `session_type` | `str` | No | `"practice"/"qualify"/"race"/...` |
| `tyre_compound` | `str` | No | Tyre compound string from AC |
| `driver_name` | `str` | No | Driver name (empty string if unavailable) |
| `air_temp_c` | `float` | Yes | Air temperature |
| `road_temp_c` | `float` | Yes | Road temperature |
| `session_start` | `str` | No | ISO 8601 datetime |
| `session_end` | `str` | Yes | ISO 8601 datetime; `None` if crashed |
| `laps_completed` | `int` | Yes | From metadata; `None` if crashed |
| `total_samples` | `int` | Yes | From metadata or derived from CSV row count |
| `sample_rate_hz` | `float` | Yes | From metadata or derived |
| `channels_available` | `list[str]` | No | Channels with non-NaN data |
| `channels_unavailable` | `list[str]` | No | Channels always NaN (reduced mode) |
| `sim_info_available` | `bool` | No | Whether sim_info was available |
| `reduced_mode` | `bool` | No | Whether reduced mode was active |
| `csv_filename` | `str` | No | Original CSV filename |
| `app_version` | `str` | No | Capture app version that wrote the files |

**Derived fields** (when metadata values are `None` due to crash):
- `total_samples` → derived from CSV row count
- `sample_rate_hz` → derived from median inter-sample interval in CSV
- `session_end` → derived from last `timestamp` value in CSV

---

### `ParsedSession`

Top-level container returned by `parse_session()`.

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | `SessionMetadata` | Session-level context |
| `setups` | `list[SetupEntry]` | All setup stints (ordered by `lap_start`) |
| `laps` | `list[LapSegment]` | All lap segments (ordered by `lap_number`) |

**Derived accessors** (model properties):
- `flying_laps` → laps where classification == "flying"
- `lap_by_number(n)` → single lap lookup

---

## State Transitions

### Lap Classification State Machine

```
CSV row stream
      │
      ▼
┌─────────────────┐
│  Group by        │
│  lap_count value │
└────────┬─────────┘
         │
         ▼
    ┌────────────────────────────────────────┐
    │ First sample in_pit_lane == 1          │──► outlap
    │ AND last sample in_pit_lane == 0?      │
    └────────────────┬───────────────────────┘
                     │ No
                     ▼
    ┌────────────────────────────────────────┐
    │ in_pit_lane transitions 0→1            │──► inlap
    │ within the lap?                        │
    └────────────────┬───────────────────────┘
                     │ No
                     ▼
    ┌────────────────────────────────────────┐
    │ No closing lap_count transition?       │──► incomplete
    └────────────────┬───────────────────────┘
                     │ No
                     ▼
    ┌────────────────────────────────────────┐
    │ Any sample lap_invalid == 1?           │──► invalid
    └────────────────┬───────────────────────┘
                     │ No
                     ▼
                  flying
```

---

## Serialization Round-Trip Invariants

For `save_session(session)` → `load_session(path)`:

1. All `LapSegment` fields are preserved exactly.
2. `LapSegment.data` values round-trip via Parquet without precision loss for
   float64 values.
3. `None` (NaN) values in `data` are preserved as `None` through JSON and as
   `NaN` through Parquet.
4. `CornerSegment` and `QualityWarning` fields round-trip through JSON without
   loss.
5. `SetupEntry.parameters` — `value` type (`float` vs `str`) is preserved.

---

## Intermediate Cache Format

**Save layout** (`data/sessions/<base_name>/`):

```
data/sessions/2026-03-02_1430_ks_ferrari_488_gt3_monza/
├── telemetry.parquet     # full time series, all laps, with lap_number column
└── session.json          # SessionMetadata + laps metadata + setups + corners + warnings
```

**`session.json` top-level structure**:

```json
{
  "format_version": "1.0",
  "session": { ...SessionMetadata... },
  "setups": [ ...SetupEntry with parameters... ],
  "laps": [
    {
      "lap_number": 0,
      "classification": "outlap",
      "start_timestamp": 1740000000.0,
      "end_timestamp": 1740000082.5,
      "start_norm_pos": 0.0,
      "end_norm_pos": 0.99,
      "sample_count": 1875,
      "active_setup_index": 0,
      "corners": [ ...CornerSegment dicts... ],
      "quality_warnings": [ ...QualityWarning dicts... ]
    }
  ]
}
```

`active_setup_index` is an integer index into the `setups` array, to avoid
duplicating the full setup in every lap entry.

The `telemetry.parquet` file has columns: `[lap_number, timestamp,
session_time_ms, normalized_position, ...]` (82 channel columns + `lap_number`).
To load a specific lap: filter by `lap_number == N`.
