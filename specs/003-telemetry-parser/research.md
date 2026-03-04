# Research: Telemetry Parser

**Branch**: `003-telemetry-parser` | **Date**: 2026-03-03

---

## 1. Exact CSV Schema (from `ac_app/ac_race_engineer/modules/channels.py`)

The in-game app produces 82 columns in this exact order. Channels marked
`(sim_info)` return NaN in reduced mode:

| # | Column | Source | Notes |
|---|--------|--------|-------|
| 0 | `timestamp` | computed | Unix epoch float |
| 1 | `session_time_ms` | computed | ms since session start |
| 2 | `normalized_position` | ac_state | 0.0–1.0, lap boundary signal |
| 3 | `lap_count` | ac_state | increments at S/F crossing |
| 4 | `lap_time_ms` | ac_state | current lap timer in ms |
| 5 | `throttle` | ac_state | 0–1 |
| 6 | `brake` | ac_state | 0–1 |
| 7 | `steering` | ac_state | signed float |
| 8 | `gear` | ac_state | int |
| 9 | `clutch` | ac_state | 0–1 |
| 10 | `handbrake` | none | always NaN |
| 11 | `speed_kmh` | ac_state | |
| 12 | `rpm` | ac_state | |
| 13 | `g_lat` | ac_state | lateral G, primary corner signal |
| 14 | `g_lon` | ac_state | longitudinal G |
| 15 | `g_vert` | ac_state | vertical G |
| 16 | `yaw_rate` | ac_state | rad/s |
| 17-19 | `local_vel_x/y/z` | ac_state | m/s |
| 20-23 | `tyre_temp_core_fl/fr/rl/rr` | ac_state | °C |
| 24-27 | `tyre_temp_inner_fl/fr/rl/rr` | sim_info | °C, NaN in reduced mode |
| 28-31 | `tyre_temp_mid_fl/fr/rl/rr` | sim_info | °C, NaN in reduced mode |
| 32-35 | `tyre_temp_outer_fl/fr/rl/rr` | sim_info | °C, NaN in reduced mode |
| 36-39 | `tyre_pressure_fl/fr/rl/rr` | ac_state | PSI |
| 40-43 | `slip_angle_fl/fr/rl/rr` | ac_state | rad |
| 44-47 | `slip_ratio_fl/fr/rl/rr` | ac_state | |
| 48-51 | `tyre_wear_fl/fr/rl/rr` | sim_info | NaN in reduced mode |
| 52-55 | `tyre_dirty_fl/fr/rl/rr` | ac_state | 0–1 |
| 56-59 | `wheel_speed_fl/fr/rl/rr` | ac_state | rad/s |
| 60-63 | `susp_travel_fl/fr/rl/rr` | ac_state | m |
| 64-67 | `wheel_load_fl/fr/rl/rr` | sim_info | N, NaN in reduced mode |
| 68-70 | `world_pos_x/y/z` | ac_state | m, world coordinates |
| 71 | `turbo_boost` | ac_state | |
| 72 | `drs` | sim_info | NaN in reduced mode |
| 73 | `ers_charge` | sim_info | NaN in reduced mode |
| 74 | `fuel` | sim_info | L, NaN in reduced mode |
| 75-79 | `damage_front/rear/left/right/center` | sim_info | NaN in reduced mode |
| 80 | `in_pit_lane` | ac_func | 0 or 1, key for outlap/inlap classification |
| 81 | `lap_invalid` | ac_state | 0 or 1, key for invalid classification |

**Key channels for parser logic**:
- `lap_count` + `normalized_position` → lap segmentation
- `in_pit_lane` → outlap/inlap classification
- `lap_invalid` → invalid classification
- `g_lat` + `steering` + `speed_kmh` → corner detection

---

## 2. Metadata v2.0 Schema (from `ac_race_engineer.py`)

```json
{
  "app_version": "0.2.0",
  "session_start": "2026-03-02T14:30:00",
  "session_end": "2026-03-02T15:00:00",  // null on crash
  "car_name": "ks_ferrari_488_gt3",
  "track_name": "monza",
  "track_config": "",
  "track_length_m": 5793.0,
  "session_type": "practice",
  "tyre_compound": "DHF",
  "laps_completed": 12,         // null on crash
  "total_samples": 44000,       // null on crash
  "sample_rate_hz": 24.4,       // null on crash
  "air_temp_c": 22.0,
  "road_temp_c": 30.5,
  "driver_name": "Driver Name",
  "setup_history": [
    {
      "timestamp": "2026-03-02T14:30:00",
      "trigger": "session_start",   // or "pit_exit"
      "lap": 0,
      "filename": "my_setup.ini",   // null if not found
      "contents": "[FRONT]\nCAMBER=-2.5\n...",  // null if not found
      "confidence": "high"          // "high"|"medium"|"low"|null
    }
  ],
  "channels_available": ["timestamp", "speed_kmh", ...],
  "channels_unavailable": ["fuel", "drs", ...],
  "sim_info_available": true,
  "reduced_mode": false,
  "tyre_temp_zones_validated": true,
  "csv_filename": "2026-03-02_1430_ks_ferrari_488_gt3_monza.csv"
}
```

**v1.0 legacy detection**: `setup_history` key absent (older app versions
stored flat `setup_filename`, `setup_contents`, `setup_confidence` at top
level). Detection: `"setup_history" not in metadata`. Conversion: wrap the
flat fields into a single-entry array with `lap=0, trigger="session_start"`.

---

## 3. Lap Segmentation Algorithm

**Decision**: Group CSV rows by `lap_count` value. When `lap_count` increments,
the boundary row (first row with the new value) starts a new segment.

**Rationale**: `lap_count` is the authoritative lap boundary signal from AC.
It increments at the start/finish crossing. `normalized_position` resets to 0.0
at the same moment. This is simpler and more reliable than detecting position
rollover (which could have timing jitter).

**Boundary handling**:
- First group (`lap_count == 0` or the lowest value): may start mid-track if
  the driver was already moving when recording began. Classified as `incomplete`
  unless it cleanly starts from pit lane (`in_pit_lane == 1` at first sample).
- Last group: if no further `lap_count` increment follows, it is the partial
  final lap. Classified as `incomplete` (session ended mid-lap).
- Intermediate groups: complete laps for which a full cycle was recorded.

**Alternatives considered**:
- Detect `normalized_position` rollover (>0.8 → <0.2): rejected because
  timing jitter near the start/finish can cause false positives/negatives.
- Use `lap_time_ms` resets: rejected because it resets only when AC officially
  registers the crossing, same as `lap_count` but less reliable.

---

## 4. Corner Detection Algorithm

**Decision**: Percentile-based self-calibrating threshold on `g_lat` and
`steering`, merged-run approach for contiguous cornering windows.

**Algorithm (per lap)**:

1. Compute `abs_g_lat = abs(g_lat)` for all samples in the session (not
   per-lap, to ensure consistent thresholds).
2. `g_threshold = np.nanpercentile(abs_g_lat, 80)` — 80th percentile.
3. `steer_threshold = np.nanpercentile(abs(steering), 70)` — 70th percentile.
4. Mark a sample as a "cornering sample" if:
   `abs_g_lat > g_threshold * 0.6` AND `abs(steering) > steer_threshold * 0.4`
5. Find contiguous runs of cornering samples within each lap.
6. Merge runs separated by fewer than `min_gap = int(sample_rate * 0.3)` samples
   (~7 samples at 22 Hz) — this prevents splitting one corner into multiple
   detections due to brief G-force dips.
7. Discard runs shorter than `min_duration = int(sample_rate * 0.5)` samples
   (~11 samples) — eliminates phantom corners from brief steering corrections on
   straights.
8. Within each surviving run: apex = index of minimum `speed_kmh`.
9. Extract `normalized_position` at entry (first sample), apex, and exit
   (last sample).

**Session-wide corner reference and consistent numbering**:

1. After processing all laps, select a reference lap: the first lap classified
   as `flying`; if no flying lap, the first `outlap`; if neither, skip corner
   numbering entirely (park/pit-only session).
2. Reference lap establishes the "track corner map": an ordered list of apex
   `normalized_position` values → corner numbers 1..N.
3. For each other lap, match each detected corner to the nearest reference
   corner by `|apex_pos_detected - apex_pos_ref|`. A match is valid if
   distance ≤ 0.05 (spec requirement ±5%).
4. Matched corners inherit the reference corner number. Unmatched detections
   are discarded (likely phantom). Reference corners with no match on a lap are
   silently skipped (car may have missed a corner, already flagged invalid).

**Edge cases**:
- **Chicanes**: Two cornering runs with opposite `g_lat` sign close together
  (< 1.5 seconds apart) are NOT merged — the minimum gap merge only applies
  within the same sign. They get separate corner numbers.
- **Ovals**: The 80th percentile threshold adapts: an oval with two long
  sweeping turns will have much lower average G-forces; the 80th percentile
  will still correctly identify the highest-G regions as corners.
- **Reduced mode (NaN g_lat)**: Fall back to `steering` alone for corner
  detection. Set `g_threshold = 0` (skip G check) and rely only on steering
  amplitude. Mark all such corners with a quality note.

**Alternatives considered**:
- scipy `find_peaks`: rejected per user decision (no scipy dependency at this stage).
- Fixed absolute G threshold (e.g., >0.5 G): rejected because car-specific;
  a low-grip car rarely exceeds 0.5 G even in corners.
- Curvature from `world_pos_x/z`: rejected because world position is noisy
  at low speeds and requires numerical differentiation.

---

## 5. Intermediate Format: Parquet + JSON Sidecar

**Decision**: One Parquet file per session containing all lap time-series data
(82 channel columns + `lap_number` int column), plus one JSON sidecar
containing all non-tabular structured data.

**Parquet file schema**:
- 82 channel columns (float64 or int64 matching original CSV types)
- `lap_number` int column (foreign key to the JSON sidecar's lap entries)
- Partitioned or sorted by `lap_number` for fast per-lap retrieval

**JSON sidecar schema**:
```json
{
  "format_version": "1.0",
  "session": { ...SessionMetadata fields... },
  "setups": [ ...SetupEntry objects... ],
  "laps": [
    {
      "lap_number": 1,
      "classification": "flying",
      "start_timestamp": 1740000100.0,
      "end_timestamp": 1740000190.0,
      "start_norm_pos": 0.0,
      "end_norm_pos": 0.99,
      "active_setup_index": 0,
      "corners": [ ...CornerSegment objects... ],
      "quality_warnings": [ ...QualityWarning objects... ]
    }
  ]
}
```

**Save location**: `data/sessions/<session_base_name>/` directory, containing:
- `telemetry.parquet` — full time series
- `session.json` — structured metadata

**Rationale**:
- Columnar Parquet is ideal for the Analyzer's per-channel slice access pattern
- JSON sidecar avoids nesting complex Pydantic models inside Parquet
- Single Parquet (not per-lap) minimizes file count and simplifies loading
- This matches the constitution's "Parquet for post-processed sessions" decision

**Alternatives considered**:
- Per-lap Parquet files: rejected (too many files, more complex glob logic)
- HDF5: rejected (heavier dependency, less portable)
- Pickle: rejected (Python-version-specific, not human-inspectable)
- Msgpack: rejected (less tooling support, no obvious advantage over Parquet+JSON)

---

## 6. Pydantic Model Strategy for DataFrame Data

**Decision**: `LapSegment.data` is stored as `dict[str, list[float | None]]`
in the Pydantic model (serializable). Internal parser helpers work with
DataFrames, but the final model stores column → row-list dictionaries.

**Rationale**: Pydantic v2 cannot serialize `pd.DataFrame` natively. Storing as
`dict[str, list]` keeps the model fully serializable to JSON and enables
straightforward Parquet reconstruction: `pd.DataFrame(lap.data)`.

The Analyzer receives a `LapSegment` and calls `lap.to_dataframe()` (a model
method that wraps the dict). This keeps the DataFrame reconstruction in one place.

**Alternatives considered**:
- Custom Pydantic serializer for DataFrame: rejected (complex, fragile across
  pandas versions).
- Storing DataFrame reference outside the model: rejected (breaks cache
  round-trip identity).

---

## 7. Repository Layout Clarification

**Finding**: The current repo has empty stub `__init__.py` files in `src/parser/`,
`src/analyzer/`, etc. These predate the `backend/` layout specified in CLAUDE.md
and the user's plan input.

**Decision**: Implementation targets `backend/ac_engineer/parser/` as specified
in CLAUDE.md and user input. The existing `src/` stubs remain untouched (they are
empty placeholders and do not conflict). Tests go in `backend/tests/parser/`.

**pyproject.toml** will need updating to include `backend/` on the Python path
(or a `backend/pyproject.toml`). This is noted as a dependency for the first
implementation task.

---

## 8. Quality Warning Thresholds (Resolved)

| Warning | Threshold | Rationale |
|---------|-----------|-----------|
| `time_series_gap` | > 0.5 s between consecutive samples | At 22–25 Hz, normal gap is ~45 ms; anything > 500 ms is dropped samples |
| `position_jump` | > 0.05 normalized pos in one sample | ~292 m jump at Monza (5793 m track); physically impossible |
| `zero_speed_mid_lap` | speed ≤ 1 km/h for > 3 s, norm_pos ∈ (0.10, 0.90) | Excludes deliberate slow zones near pit entry/exit |
| `incomplete` | no closing `lap_count` increment | Last partial lap |
| `duplicate_timestamp` | consecutive `timestamp` values identical | Indicates buffer flush artifact |

All thresholds are constants in `quality_validator.py` and configurable at
import time for testing.
