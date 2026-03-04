# Data Model: Engineer Core (Phase 5.2)

**Branch**: `007-engineer-core` | **Date**: 2026-03-04

All models are Pydantic v2 BaseModel subclasses defined in `backend/ac_engineer/engineer/models.py`.

## Entity Relationship Overview

```
AnalyzedSession (input, from analyzer)
       │
       ▼
  summarize_session()
       │
       ▼
  SessionSummary ─────────┬── laps: list[LapSummary]
                          ├── corner_issues: list[CornerIssue]
                          ├── stints: list[StintSummary]
                          └── tyre_averages / slip_averages (dicts)

  ParameterRange ◄── read from data/setup.ini
       │
       ▼
  validate_changes(ranges, proposals)
       │
       ▼
  ValidationResult ◄── per-change outcome
       │
       ▼
  apply_changes(setup_path, validated_changes)
       │
       ▼
  ChangeOutcome ◄── per-change result with old/new values

  SetupChange ─────── used by AI engineer (Phase 5.3) for recommendations
  DriverFeedback ───── used by AI engineer (Phase 5.3) for driving tips
  EngineerResponse ── composite output from AI engineer (Phase 5.3)
```

## Models

### ParameterRange

Represents the valid range for a single adjustable setup parameter, as read from the car's `data/setup.ini`.

| Field | Type | Description |
|-------|------|-------------|
| section | str | INI section name (e.g., "CAMBER_LF") |
| parameter | str | Parameter key within the section (e.g., "VALUE") |
| min_value | float | Minimum allowed value |
| max_value | float | Maximum allowed value |
| step | float | Increment per adjustment click |
| default_value | float \| None | Default value from car data (None if not specified) |

**Validation rules**:
- `min_value <= max_value` (enforced by validator)
- `step > 0` (enforced by validator)

**Relationships**: Belongs to a ParameterRangeSet (dict keyed by section name).

### LapSummary

Compact per-lap entry for flying laps in the session summary.

| Field | Type | Description |
|-------|------|-------------|
| lap_number | int | Lap identifier |
| lap_time_s | float | Lap time in seconds |
| gap_to_best_s | float | Time difference from best lap (0.0 for best lap) |
| is_best | bool | True if this is the best flying lap |
| tyre_temp_avg_c | float \| None | Single average tyre temp across all 4 wheels (°C) |
| understeer_ratio_avg | float \| None | Average understeer ratio across corners |
| peak_lat_g | float \| None | Peak lateral G-force |
| peak_speed_kmh | float \| None | Maximum speed during lap |

**Validation rules**: `gap_to_best_s >= 0.0`

### CornerIssue

A prioritized corner-specific problem detected in the session.

| Field | Type | Description |
|-------|------|-------------|
| corner_number | int | Which corner |
| issue_type | str | Signal-like identifier (e.g., "understeer", "oversteer", "high_slip") |
| severity | str | "high" / "medium" / "low" |
| understeer_ratio | float \| None | Understeer ratio at this corner (if relevant) |
| apex_speed_loss_pct | float \| None | Percentage of apex speed lost vs. potential |
| avg_lat_g | float \| None | Average lateral G-force at this corner |
| description | str | Human-readable description of the issue |

**Validation rules**: `severity` must be one of the three allowed values.

**Ordering**: Sorted by severity (high > medium > low); truncated to `max_corner_issues`.

### StintSummary

Per-stint breakdown within the session summary.

| Field | Type | Description |
|-------|------|-------------|
| stint_index | int | Stint identifier |
| flying_lap_count | int | Number of flying laps in this stint |
| lap_time_mean_s | float \| None | Mean lap time of flying laps |
| lap_time_stddev_s | float \| None | Lap time standard deviation within stint |
| lap_time_trend | str | "improving" / "degrading" / "stable" |
| lap_time_slope_s_per_lap | float \| None | Raw slope: seconds gained/lost per lap |
| tyre_temp_slope_c_per_lap | float \| None | Tyre temperature trend: °C change per lap |
| setup_filename | str \| None | Active setup .ini filename |
| setup_changes_from_prev | list[str] | Human-readable list of setup changes vs. previous stint |

**Validation rules**: `lap_time_trend` must be one of the three allowed values.

**Derivation**: `lap_time_trend` derived from StintTrends.lap_time_slope — negative = "improving", positive > 0.05 = "degrading", else "stable".

### SessionSummary

The complete compact summary of an analyzed session, optimized for LLM consumption.

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | Unique session identifier |
| car_name | str | Car identifier |
| track_name | str | Track identifier |
| track_config | str \| None | Track configuration/layout |
| recorded_at | str \| None | When the session was recorded |
| total_lap_count | int | Total laps in session (all types) |
| flying_lap_count | int | Number of flying laps |
| best_lap_time_s | float \| None | Best flying lap time |
| worst_lap_time_s | float \| None | Worst flying lap time |
| lap_time_stddev_s | float \| None | Lap time standard deviation across flying laps |
| avg_understeer_ratio | float \| None | Session-wide average understeer ratio |
| active_setup_filename | str \| None | Primary setup .ini filename for this session |
| active_setup_parameters | dict[str, dict[str, float \| str]] \| None | Setup parameters keyed by section then name |
| laps | list[LapSummary] | Flying laps only, sorted by lap number |
| signals | list[str] | Detected problem signals (e.g., "high_understeer") |
| corner_issues | list[CornerIssue] | Top corner problems, sorted by severity |
| stints | list[StintSummary] | Per-stint breakdowns |
| tyre_temp_averages | dict[str, float] \| None | Session-wide per-wheel avg temps |
| tyre_pressure_averages | dict[str, float] \| None | Session-wide per-wheel avg pressures |
| slip_angle_averages | dict[str, float] \| None | Session-wide per-wheel avg slip angles |

**Validation rules**: `flying_lap_count == len(laps)`

**Immutability**: Input AnalyzedSession is never mutated. Summary is constructed from deep copies/extractions.

### ValidationResult

Outcome of validating a single proposed setup change.

| Field | Type | Description |
|-------|------|-------------|
| section | str | INI section name |
| parameter | str | Parameter key within the section |
| proposed_value | float | Value the engineer proposed |
| clamped_value | float \| None | Clamped value if out of range, None if valid or no range data |
| is_valid | bool | True if proposed value is within range or no range data exists |
| warning | str \| None | Warning message (e.g., out-of-range detail, no range data notice) |

### ChangeOutcome

Result of applying a single validated change to a setup file.

| Field | Type | Description |
|-------|------|-------------|
| section | str | INI section name |
| parameter | str | What was changed (VALUE key in setup file) |
| old_value | str | Previous value in the file |
| new_value | str | New value written |

### SetupChange

A fully described setup modification proposed by the AI engineer (used in Phase 5.3).

| Field | Type | Description |
|-------|------|-------------|
| section | str | INI section name (e.g., "CAMBER_LF") |
| parameter | str | Display name |
| value_before | float \| None | Current value (None if unknown) |
| value_after | float | Proposed new value |
| reasoning | str | Why this change helps (educational) |
| expected_effect | str | What the driver will feel on track |
| confidence | str | "high" / "medium" / "low" |

**Validation rules**: `confidence` must be one of the three allowed values.

### DriverFeedback

A driving technique observation from the engineer (used in Phase 5.3).

| Field | Type | Description |
|-------|------|-------------|
| area | str | Driving area (e.g., "braking", "throttle_application", "cornering") |
| observation | str | What was observed in the data |
| suggestion | str | What to try next |
| corners_affected | list[int] | Which corner numbers are relevant |
| severity | str | "high" / "medium" / "low" |

**Validation rules**: `severity` must be one of the three allowed values.

### EngineerResponse

Complete output of the AI engineer for a session (used in Phase 5.3).

| Field | Type | Description |
|-------|------|-------------|
| session_id | str | Session this response is for |
| setup_changes | list[SetupChange] | Proposed modifications |
| driver_feedback | list[DriverFeedback] | Driving tips |
| signals_addressed | list[str] | Which detected signals this response addresses |
| summary | str | Short display summary (1-2 sentences) |
| explanation | str | Full explanation in plain language |
| confidence | str | Overall confidence: "high" / "medium" / "low" |

**Validation rules**: `confidence` must be one of the three allowed values.

## State Transitions

### ValidationResult Flow

```
SetupChange
      │
      ▼
validate_changes()
      │
      ├── value in [min, max] → is_valid=True,  clamped_value=None
      ├── value < min         → is_valid=False, clamped_value=min_value
      ├── value > max         → is_valid=False, clamped_value=max_value
      └── no range found      → is_valid=True,  clamped_value=None, warning="no range data"
```

### Setup Write Flow

```
list[ValidationResult] (all validated)
      │
      ▼
create_backup(setup_path) → backup file created
      │
      ▼
apply_changes(setup_path, results) → list[ChangeOutcome]
      │
      ├── Empty list → ValueError raised, no files touched
      ├── Read original → Apply changes in memory → Write .tmp → os.replace()
      └── On error → .tmp cleaned up, original intact
```
