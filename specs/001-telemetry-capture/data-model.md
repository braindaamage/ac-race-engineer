# Data Model: Telemetry Capture App

**Feature**: 001-telemetry-capture
**Date**: 2026-03-02

## Entities

### TelemetrySample

A single point-in-time capture of all telemetry channels. One row in the CSV output.

| Field Group | Field Name | Type | Source | Notes |
|---|---|---|---|---|
| **Timing** | timestamp | float | `time.time()` | Unix epoch seconds |
| | session_time_ms | float | computed | ms since session start |
| | normalized_position | float | `acsys.CS.NormalizedSplinePosition` | 0.0-1.0 track position |
| | lap_count | int | `acsys.CS.LapCount` | completed laps |
| | lap_time_ms | float | `acsys.CS.LapTime` | current lap time in ms |
| **Inputs** | throttle | float | `acsys.CS.Gas` | 0.0-1.0 |
| | brake | float | `acsys.CS.Brake` | 0.0-1.0 |
| | steering | float | `acsys.CS.Steer` | degrees |
| | gear | int | `acsys.CS.Gear` | 0=R, 1=N, 2=1st... |
| | clutch | float | `acsys.CS.Clutch` | 0.0-1.0 |
| | handbrake | float | N/A | NaN (not exposed by AC) |
| **Dynamics** | speed_kmh | float | `acsys.CS.SpeedKMH` | km/h |
| | rpm | float | `acsys.CS.RPM` | engine RPM |
| | g_lat | float | `acsys.CS.AccG[0]` | lateral g-force |
| | g_lon | float | `acsys.CS.AccG[2]` | longitudinal g-force |
| | g_vert | float | `acsys.CS.AccG[1]` | vertical g-force |
| | yaw_rate | float | `acsys.CS.LocalAngularVelocity[1]` | rad/s |
| | local_vel_x | float | `acsys.CS.LocalVelocity[0]` | m/s |
| | local_vel_y | float | `acsys.CS.LocalVelocity[1]` | m/s |
| | local_vel_z | float | `acsys.CS.LocalVelocity[2]` | m/s |
| **Tyre Temp Core** | tyre_temp_core_fl | float | `acsys.CS.CurrentTyresCoreTemp[0]` | Celsius |
| | tyre_temp_core_fr | float | `acsys.CS.CurrentTyresCoreTemp[1]` | Celsius |
| | tyre_temp_core_rl | float | `acsys.CS.CurrentTyresCoreTemp[2]` | Celsius |
| | tyre_temp_core_rr | float | `acsys.CS.CurrentTyresCoreTemp[3]` | Celsius |
| **Tyre Temp Inner** | tyre_temp_inner_fl | float | `sim_info.physics.tyreTempI[0]` | Celsius, NaN if unavailable |
| | tyre_temp_inner_fr | float | `sim_info.physics.tyreTempI[1]` | Celsius, NaN if unavailable |
| | tyre_temp_inner_rl | float | `sim_info.physics.tyreTempI[2]` | Celsius, NaN if unavailable |
| | tyre_temp_inner_rr | float | `sim_info.physics.tyreTempI[3]` | Celsius, NaN if unavailable |
| **Tyre Temp Middle** | tyre_temp_mid_fl | float | `sim_info.physics.tyreTempM[0]` | Celsius, NaN if unavailable |
| | tyre_temp_mid_fr | float | `sim_info.physics.tyreTempM[1]` | Celsius, NaN if unavailable |
| | tyre_temp_mid_rl | float | `sim_info.physics.tyreTempM[2]` | Celsius, NaN if unavailable |
| | tyre_temp_mid_rr | float | `sim_info.physics.tyreTempM[3]` | Celsius, NaN if unavailable |
| **Tyre Temp Outer** | tyre_temp_outer_fl | float | `sim_info.physics.tyreTempO[0]` | Celsius, NaN if unavailable |
| | tyre_temp_outer_fr | float | `sim_info.physics.tyreTempO[1]` | Celsius, NaN if unavailable |
| | tyre_temp_outer_rl | float | `sim_info.physics.tyreTempO[2]` | Celsius, NaN if unavailable |
| | tyre_temp_outer_rr | float | `sim_info.physics.tyreTempO[3]` | Celsius, NaN if unavailable |
| **Tyre Data** | tyre_pressure_fl | float | `acsys.CS.DynamicPressure[0]` | PSI |
| | tyre_pressure_fr | float | `acsys.CS.DynamicPressure[1]` | PSI |
| | tyre_pressure_rl | float | `acsys.CS.DynamicPressure[2]` | PSI |
| | tyre_pressure_rr | float | `acsys.CS.DynamicPressure[3]` | PSI |
| | slip_angle_fl | float | `acsys.CS.SlipAngle[0]` | degrees |
| | slip_angle_fr | float | `acsys.CS.SlipAngle[1]` | degrees |
| | slip_angle_rl | float | `acsys.CS.SlipAngle[2]` | degrees |
| | slip_angle_rr | float | `acsys.CS.SlipAngle[3]` | degrees |
| | slip_ratio_fl | float | `acsys.CS.SlipRatio[0]` | dimensionless |
| | slip_ratio_fr | float | `acsys.CS.SlipRatio[1]` | dimensionless |
| | slip_ratio_rl | float | `acsys.CS.SlipRatio[2]` | dimensionless |
| | slip_ratio_rr | float | `acsys.CS.SlipRatio[3]` | dimensionless |
| | tyre_wear_fl | float | `sim_info.physics.tyreWear[0]` | 0.0-1.0 (1.0=new) |
| | tyre_wear_fr | float | `sim_info.physics.tyreWear[1]` | 0.0-1.0 |
| | tyre_wear_rl | float | `sim_info.physics.tyreWear[2]` | 0.0-1.0 |
| | tyre_wear_rr | float | `sim_info.physics.tyreWear[3]` | 0.0-1.0 |
| | tyre_dirty_fl | float | `acsys.CS.TyreDirtyLevel[0]` | 0-10 |
| | tyre_dirty_fr | float | `acsys.CS.TyreDirtyLevel[1]` | 0-10 |
| | tyre_dirty_rl | float | `acsys.CS.TyreDirtyLevel[2]` | 0-10 |
| | tyre_dirty_rr | float | `acsys.CS.TyreDirtyLevel[3]` | 0-10 |
| **Wheel Speed** | wheel_speed_fl | float | `acsys.CS.WheelAngularSpeed[0]` | rad/s |
| | wheel_speed_fr | float | `acsys.CS.WheelAngularSpeed[1]` | rad/s |
| | wheel_speed_rl | float | `acsys.CS.WheelAngularSpeed[2]` | rad/s |
| | wheel_speed_rr | float | `acsys.CS.WheelAngularSpeed[3]` | rad/s |
| **Suspension** | susp_travel_fl | float | `acsys.CS.SuspensionTravel[0]` | meters |
| | susp_travel_fr | float | `acsys.CS.SuspensionTravel[1]` | meters |
| | susp_travel_rl | float | `acsys.CS.SuspensionTravel[2]` | meters |
| | susp_travel_rr | float | `acsys.CS.SuspensionTravel[3]` | meters |
| | wheel_load_fl | float | `sim_info.physics.wheelLoad[0]` | Newtons |
| | wheel_load_fr | float | `sim_info.physics.wheelLoad[1]` | Newtons |
| | wheel_load_rl | float | `sim_info.physics.wheelLoad[2]` | Newtons |
| | wheel_load_rr | float | `sim_info.physics.wheelLoad[3]` | Newtons |
| **World Position** | world_pos_x | float | `acsys.CS.WorldPosition[0]` | meters |
| | world_pos_y | float | `acsys.CS.WorldPosition[1]` | meters |
| | world_pos_z | float | `acsys.CS.WorldPosition[2]` | meters |
| **Car State** | turbo_boost | float | `acsys.CS.TurboBoost` | bar, NaN if N/A |
| | drs | float | `sim_info.physics.drs` | 0 or 1, NaN if N/A |
| | ers_charge | float | `sim_info.physics.kersCharge` | 0.0-1.0, NaN if N/A |
| | fuel | float | `sim_info.physics.fuel` | liters |
| | damage_front | float | `sim_info.physics.carDamage[0]` | damage value |
| | damage_rear | float | `sim_info.physics.carDamage[1]` | damage value |
| | damage_left | float | `sim_info.physics.carDamage[2]` | damage value |
| | damage_right | float | `sim_info.physics.carDamage[3]` | damage value |
| | damage_center | float | `sim_info.physics.carDamage[4]` | damage value |
| **Flags** | in_pit_lane | int | `ac.isCarInPitlane(0)` | 0 or 1 |
| | lap_invalid | int | `acsys.CS.LapInvalidated` | 0 or 1 |

**Total**: 82 channels per sample

### SessionMetadata

Session-level information stored in the `.meta.json` sidecar file.

| Field | Type | Source | Notes |
|---|---|---|---|
| app_version | string | hardcoded constant | e.g. "0.1.0" |
| session_start | string | `time.strftime()` | ISO 8601 format |
| session_end | string | `time.strftime()` | ISO 8601, written at finalization |
| car_name | string | `ac.getCarName(0)` | e.g. "ks_ferrari_488_gt3" |
| track_name | string | `ac.getTrackName(0)` | e.g. "monza" |
| track_config | string | `ac.getTrackConfiguration(0)` | layout variant, may be empty |
| track_length_m | float | `ac.getTrackLength(0)` | meters |
| session_type | string | `info.graphics.session` | "practice", "qualify", "race", etc. |
| tyre_compound | string | `ac.getCarTyreCompound(0)` | e.g. "Soft" |
| laps_completed | int | `acsys.CS.LapCount` | at session end |
| total_samples | int | computed | total rows written to CSV |
| sample_rate_hz | float | computed | actual avg samples/second |
| air_temp_c | float | `info.physics.airTemp` | Celsius, real-time value (AC 1.14+). Falls back to `info.static.airTemp` |
| road_temp_c | float | `info.physics.roadTemp` | Celsius, real-time value (AC 1.14+). Falls back to `info.static.roadTemp` |
| driver_name | string | `ac.getDriverName(0)` | player name |
| setup_filename | string | discovered | name of setup file found, or null — **Removed in v2.0** — see specs/002-setup-stint-tracking/data-model.md |
| setup_contents | string | file read | raw .ini text, or null — **Removed in v2.0** — see specs/002-setup-stint-tracking/data-model.md |
| setup_confidence | string | computed | "high", "medium", "low", or null (see R-004) — **Removed in v2.0** — see specs/002-setup-stint-tracking/data-model.md |
| channels_available | list[string] | computed | channels that returned valid data |
| channels_unavailable | list[string] | computed | channels that returned NaN |
| sim_info_available | bool | computed | whether shared memory was accessible |
| reduced_mode | bool | computed | true if sim_info failed to load (see R-011) |
| tyre_temp_zones_validated | bool | computed | true if inner/mid/outer tyre temps read non-zero (see R-011) |
| csv_filename | string | computed | corresponding .csv filename |

### AppConfig

Configuration loaded from `config.ini` at app startup.

| Field | Type | Default | Notes |
|---|---|---|---|
| output_dir | string | `~/Documents/ac-race-engineer/sessions/` | output path |
| sample_rate_hz | int | 25 | target samples per second (20-30) |
| buffer_size | int | 1000 | max samples before forced flush |
| flush_interval_s | float | 30.0 | seconds between periodic flushes |
| log_level | string | "info" | "debug", "info", "warn", "error" |

### SampleBuffer

In-memory buffer for accumulating telemetry samples before disk flush.

| Field | Type | Notes |
|---|---|---|
| samples | list[list] | list of sample rows (each row = list of channel values) |
| count | int | current number of buffered samples |
| max_size | int | from AppConfig.buffer_size |
| last_flush_time | float | `time.time()` of last flush |

**Operations**:
- `append(sample)` — add sample, trigger flush if buffer full
- `flush(writer)` — write all buffered samples to CSV, clear buffer
- `is_flush_due()` — check if flush interval has elapsed
- `clear()` — reset buffer (after flush)

### ChannelDefinition

Defines how to read a single telemetry channel.

| Field | Type | Notes |
|---|---|---|
| name | string | CSV column name |
| source | string | "ac_state", "ac_func", "sim_info", "computed" |
| reader | callable | function that reads the channel value |
| fallback | float/None | value if read fails (typically NaN) |
| index | int/None | array index for multi-value channels (0-3 for wheels) |

## State Transitions

### Recording State Machine

```
    ┌──────┐  session_live  ┌───────────┐
    │ IDLE │ ──────────────>│ RECORDING │
    │      │                │           │
    └──────┘                └───────────┘
       ^                         │
       │                         │ session_end / car_change / track_change
       │                         v
       │                    ┌────────────┐
       └────────────────────│ FINALIZING │
            file_closed     └────────────┘
```

**State descriptions**:
- **IDLE**: No active session. Waiting for AC to be live with car on track.
- **RECORDING**: Actively sampling telemetry at configured rate. Periodic flush operations (time-based or buffer-full) execute inline within this state — no state transition occurs. The status indicator briefly shows yellow during a flush, but the state machine remains in RECORDING.
- **FINALIZING**: Session ended. Performing final flush, writing metadata JSON, closing files.

**Note on flushing**: Flush is a transient operation within RECORDING, not a separate state. When a flush trigger fires (every 30 seconds or when buffer reaches max_size), the entry point writes the buffer to disk and clears it, all within a single `acUpdate()` call. The state machine does not transition. The UI status module tracks flush visually (yellow indicator) independently of the state machine — this is a display concern, not a state concern.

## Validation Rules

- `sample_rate_hz` must be between 20 and 30 (inclusive)
- `buffer_size` must be between 100 and 5000
- `flush_interval_s` must be between 5.0 and 120.0
- `output_dir` must be a writable path (created if not exists)
- Channel values are NOT validated at capture time (raw values recorded as-is per spec)
- Filenames must contain only `[a-z0-9_]` characters plus the extension
