# Contract: CSV Telemetry Output

**Feature**: 001-telemetry-capture
**Version**: 1.0

## Format

- **Encoding**: UTF-8
- **Delimiter**: comma (`,`)
- **Line ending**: `\r\n` (Windows)
- **Quoting**: minimal (only when values contain commas or quotes)
- **Header**: single row, first line of file
- **Data rows**: one per telemetry sample

## Column Order

Columns appear in this exact order. All columns are always present in every file, regardless of car. Missing data is represented as empty string (which pandas reads as NaN).

```csv
timestamp,session_time_ms,normalized_position,lap_count,lap_time_ms,throttle,brake,steering,gear,clutch,handbrake,speed_kmh,rpm,g_lat,g_lon,g_vert,yaw_rate,local_vel_x,local_vel_y,local_vel_z,tyre_temp_core_fl,tyre_temp_core_fr,tyre_temp_core_rl,tyre_temp_core_rr,tyre_temp_inner_fl,tyre_temp_inner_fr,tyre_temp_inner_rl,tyre_temp_inner_rr,tyre_temp_mid_fl,tyre_temp_mid_fr,tyre_temp_mid_rl,tyre_temp_mid_rr,tyre_temp_outer_fl,tyre_temp_outer_fr,tyre_temp_outer_rl,tyre_temp_outer_rr,tyre_pressure_fl,tyre_pressure_fr,tyre_pressure_rl,tyre_pressure_rr,slip_angle_fl,slip_angle_fr,slip_angle_rl,slip_angle_rr,slip_ratio_fl,slip_ratio_fr,slip_ratio_rl,slip_ratio_rr,tyre_wear_fl,tyre_wear_fr,tyre_wear_rl,tyre_wear_rr,tyre_dirty_fl,tyre_dirty_fr,tyre_dirty_rl,tyre_dirty_rr,wheel_speed_fl,wheel_speed_fr,wheel_speed_rl,wheel_speed_rr,susp_travel_fl,susp_travel_fr,susp_travel_rl,susp_travel_rr,wheel_load_fl,wheel_load_fr,wheel_load_rl,wheel_load_rr,world_pos_x,world_pos_y,world_pos_z,turbo_boost,drs,ers_charge,fuel,damage_front,damage_rear,damage_left,damage_right,damage_center,in_pit_lane,lap_invalid
```

**Total columns**: 82

## Data Types

| Type | Format | Example | Missing |
|---|---|---|---|
| float | decimal, up to 6 significant digits | `123.456789` | (empty) |
| int | integer, no decimal | `3` | (empty) |
| timestamp | Unix epoch seconds, 3 decimal places | `1709391042.123` | never missing |

## Example Row

```csv
1709391042.123,5042.123,0.3421,2,45123.456,0.85,0.0,-12.3,4,0.0,,185.432,7250.0,-0.15,0.42,1.01,0.023,0.1,-0.05,51.2,92.1,91.8,95.3,94.9,89.5,89.2,93.1,92.7,91.3,91.0,94.2,93.8,93.7,93.4,97.1,96.8,26.1,26.0,25.8,25.7,-1.2,-1.1,0.8,0.9,0.02,0.02,0.03,0.03,0.98,0.98,0.97,0.97,0.0,0.0,0.0,0.0,85.2,85.3,84.1,84.0,0.045,0.044,0.038,0.039,4521.0,4498.0,5102.0,5089.0,-234.5,12.3,567.8,0.0,,,,0.0,0.0,0.0,0.0,0.0,0,0
```

## Compatibility

- **pandas**: `pd.read_csv(path)` reads the file directly. Empty cells become `NaN`.
- **Excel**: opens as comma-separated file. Empty cells display as blank.
- **R**: `read.csv(path)` reads the file directly. Empty cells become `NA`.
- **No custom preprocessing required** (SC-009).

## File Naming

Pattern: `{date}_{time}_{car}_{track}.csv`

- **date**: `YYYY-MM-DD` format
- **time**: `HHMM` format (24-hour, no separators)
- **car**: sanitized car name (lowercase, special chars → underscore, no leading/trailing underscores)
- **track**: sanitized track name (same rules as car)
- Example: `2026-03-02_1430_ks_ferrari_488_gt3_monza.csv`

## Filename Sanitization Rules

1. Convert to lowercase
2. Replace spaces with underscores
3. Replace any character not in `[a-z0-9_]` with underscore
4. Collapse multiple consecutive underscores to single underscore
5. Strip leading and trailing underscores
