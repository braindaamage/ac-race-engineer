# Data Model: Telemetry Analyzer

**Feature**: 004-telemetry-analyzer
**Date**: 2026-03-04

## Entity Relationship Overview

```
ParsedSession (input, read-only)
    │
    ▼
AnalyzedSession (output)
    ├── metadata: SessionMetadata (reference from parser)
    ├── laps: list[AnalyzedLap]
    │     ├── lap_number, classification, is_invalid
    │     ├── metrics: LapMetrics
    │     │     ├── timing: TimingMetrics
    │     │     ├── tyres: TyreMetrics
    │     │     ├── grip: GripMetrics
    │     │     ├── driver_inputs: DriverInputMetrics
    │     │     ├── speed: SpeedMetrics
    │     │     ├── fuel: FuelMetrics | None
    │     │     └── suspension: SuspensionMetrics
    │     └── corners: list[CornerMetrics]
    │           ├── performance: CornerPerformance
    │           ├── grip: CornerGrip
    │           ├── technique: CornerTechnique
    │           └── loading: CornerLoading | None
    ├── stints: list[StintMetrics]
    │     ├── setup_ref, lap_numbers, flying_lap_count
    │     ├── aggregated: AggregatedStintMetrics
    │     └── trends: StintTrends | None
    ├── stint_comparisons: list[StintComparison]
    │     ├── stint_a_index, stint_b_index
    │     ├── setup_changes: list[SetupParameterDelta]
    │     └── metric_deltas: MetricDeltas
    └── consistency: ConsistencyMetrics | None
          ├── lap_time_stddev, best_lap_time, worst_lap_time
          ├── lap_time_trend_slope
          └── corner_consistency: list[CornerConsistency]
```

## Entity Definitions

### AnalyzedSession

Top-level output container. Mirrors ParsedSession structure but adds computed metrics.

| Field               | Type                        | Description                                     |
| ------------------- | --------------------------- | ----------------------------------------------- |
| metadata            | SessionMetadata             | Reference to parser's session metadata           |
| laps                | list[AnalyzedLap]           | One per lap in ParsedSession                     |
| stints              | list[StintMetrics]          | One per consecutive setup group                  |
| stint_comparisons   | list[StintComparison]       | One per adjacent stint pair (len = stints - 1)   |
| consistency         | ConsistencyMetrics \| None  | None if < 1 flying lap                           |

### AnalyzedLap

Per-lap wrapper linking lap identity to computed metrics.

| Field          | Type                  | Description                              |
| -------------- | --------------------- | ---------------------------------------- |
| lap_number     | int                   | From LapSegment                          |
| classification | LapClassification     | flying/outlap/inlap/invalid/incomplete   |
| is_invalid     | bool                  | From LapSegment                          |
| metrics        | LapMetrics            | All lap-level metric groups              |
| corners        | list[CornerMetrics]   | One per detected corner on this lap      |

### LapMetrics

Composite of all lap-level metric groups.

| Field         | Type                      | Description                    |
| ------------- | ------------------------- | ------------------------------ |
| timing        | TimingMetrics             | Lap time, sector times         |
| tyres         | TyreMetrics               | Temperatures, pressures, wear  |
| grip          | GripMetrics               | Slip angles/ratios, G-forces   |
| driver_inputs | DriverInputMetrics        | Throttle/brake/steering stats  |
| speed         | SpeedMetrics              | Max/min/avg speed              |
| fuel          | FuelMetrics \| None       | None if fuel channel invalid   |
| suspension    | SuspensionMetrics         | Travel per wheel               |

### TimingMetrics

| Field              | Type                  | Description                                          |
| ------------------ | --------------------- | ---------------------------------------------------- |
| lap_time_s         | float                 | end_timestamp - start_timestamp                      |
| sector_times_s     | list[float] \| None   | 3-element list (equal-thirds sectors) or None        |

### TyreMetrics

Per-wheel tyre data. Uses a dict keyed by wheel position (fl, fr, rl, rr).

| Field                  | Type                                    | Description                                           |
| ---------------------- | --------------------------------------- | ----------------------------------------------------- |
| temps_avg              | dict[str, WheelTempZones]               | Average temps per zone per wheel                      |
| temps_peak             | dict[str, WheelTempZones]               | Peak temps per zone per wheel                         |
| pressure_avg           | dict[str, float]                        | Average pressure per wheel                            |
| temp_spread            | dict[str, float]                        | inner-outer temp delta per wheel (camber indicator)   |
| front_rear_balance     | float                                   | Mean front temp / mean rear temp ratio                |
| wear_rate              | dict[str, float] \| None               | Wear delta per wheel per lap, None if unavailable     |

### WheelTempZones

| Field  | Type  | Description                |
| ------ | ----- | -------------------------- |
| core   | float | Core temperature           |
| inner  | float | Inner temperature          |
| mid    | float | Middle temperature         |
| outer  | float | Outer temperature          |

### GripMetrics

| Field                | Type              | Description                                    |
| -------------------- | ----------------- | ---------------------------------------------- |
| slip_angle_avg       | dict[str, float]  | Average abs slip angle per wheel               |
| slip_angle_peak      | dict[str, float]  | Peak abs slip angle per wheel                  |
| slip_ratio_avg       | dict[str, float]  | Average abs slip ratio per wheel               |
| slip_ratio_peak      | dict[str, float]  | Peak abs slip ratio per wheel                  |
| peak_lat_g           | float             | Peak absolute lateral G                        |
| peak_lon_g           | float             | Peak absolute longitudinal G                   |

### DriverInputMetrics

| Field                | Type              | Description                                       |
| -------------------- | ----------------- | ------------------------------------------------- |
| full_throttle_pct    | float             | % of samples with throttle >= 0.95                |
| partial_throttle_pct | float             | % of samples with 0.05 < throttle < 0.95         |
| off_throttle_pct     | float             | % of samples with throttle <= 0.05               |
| braking_pct          | float             | % of samples with brake > 0.05                   |
| avg_steering_angle   | float             | Mean absolute steering angle                      |
| gear_distribution    | dict[int, float]  | % of time per gear (gear_number → percentage)    |

### SpeedMetrics

| Field        | Type  | Description                                        |
| ------------ | ----- | -------------------------------------------------- |
| max_speed    | float | Maximum speed_kmh                                  |
| min_speed    | float | Minimum speed_kmh (excluding < 10 km/h)           |
| avg_speed    | float | Average speed_kmh                                  |

### FuelMetrics

| Field              | Type  | Description                           |
| ------------------ | ----- | ------------------------------------- |
| fuel_start         | float | Fuel at first sample of lap           |
| fuel_end           | float | Fuel at last sample of lap            |
| consumption        | float | fuel_start - fuel_end                 |

### SuspensionMetrics

Per-wheel suspension data.

| Field           | Type              | Description                               |
| --------------- | ----------------- | ----------------------------------------- |
| travel_avg      | dict[str, float]  | Average suspension travel per wheel       |
| travel_peak     | dict[str, float]  | Peak suspension travel per wheel          |
| travel_range    | dict[str, float]  | max - min travel per wheel                |

### CornerMetrics

Per-corner-per-lap metrics.

| Field        | Type                    | Description                          |
| ------------ | ----------------------- | ------------------------------------ |
| corner_number| int                     | Session-consistent corner number     |
| performance  | CornerPerformance       | Speeds and duration                  |
| grip         | CornerGrip              | G-forces and balance                 |
| technique    | CornerTechnique         | Braking/throttle points              |
| loading      | CornerLoading \| None   | None if wheel_load unavailable       |

### CornerPerformance

| Field            | Type  | Description                                  |
| ---------------- | ----- | -------------------------------------------- |
| entry_speed_kmh  | float | Speed at entry_norm_pos (from time series)   |
| apex_speed_kmh   | float | Speed at apex_norm_pos (from time series)    |
| exit_speed_kmh   | float | Speed at exit_norm_pos (from time series)    |
| duration_s       | float | Time from entry to exit                      |

### CornerGrip

| Field              | Type  | Description                                             |
| ------------------ | ----- | ------------------------------------------------------- |
| peak_lat_g         | float | Peak abs lateral G in corner                            |
| avg_lat_g          | float | Average abs lateral G in corner                         |
| understeer_ratio   | float \| None | front_slip_avg / rear_slip_avg (>1 = understeer); None if rear slip < epsilon |

### CornerTechnique

| Field                | Type           | Description                                                     |
| -------------------- | -------------- | --------------------------------------------------------------- |
| brake_point_norm     | float \| None  | Normalized position where brake first > threshold; None if no braking |
| throttle_on_norm     | float \| None  | Normalized position where throttle > threshold after apex       |
| trail_braking_intensity | float       | Mean brake while braking + steering overlap (0 if none)         |

### CornerLoading

| Field           | Type              | Description                          |
| --------------- | ----------------- | ------------------------------------ |
| peak_wheel_load | dict[str, float]  | Peak load per wheel during corner    |

### StintMetrics

| Field              | Type                            | Description                                     |
| ------------------ | ------------------------------- | ----------------------------------------------- |
| stint_index        | int                             | 0-based index of this stint                     |
| setup_filename     | str \| None                     | Setup filename for this stint                   |
| lap_numbers        | list[int]                       | All lap numbers in this stint                   |
| flying_lap_count   | int                             | Count of flying laps in stint                   |
| aggregated         | AggregatedStintMetrics          | Mean/stddev across flying laps                  |
| trends             | StintTrends \| None             | None if < 2 flying laps                         |

### AggregatedStintMetrics

| Field                | Type              | Description                                    |
| -------------------- | ----------------- | ---------------------------------------------- |
| lap_time_mean_s      | float \| None     | Mean lap time of flying laps; None if 0 flying |
| lap_time_stddev_s    | float \| None     | Stddev of flying lap times; None if < 2        |
| tyre_temp_avg        | dict[str, float]  | Mean core temp per wheel across flying laps    |
| slip_angle_avg       | dict[str, float]  | Mean slip angle per wheel across flying laps   |
| slip_ratio_avg       | dict[str, float]  | Mean slip ratio per wheel across flying laps   |
| peak_lat_g_avg       | float \| None     | Mean peak lateral G across flying laps         |

### StintTrends

| Field                    | Type           | Description                                        |
| ------------------------ | -------------- | -------------------------------------------------- |
| lap_time_slope           | float          | Linear slope of lap times over stint (s/lap)       |
| tyre_temp_slope          | dict[str, float] | Core temp slope per wheel (°C/lap)               |
| fuel_consumption_slope   | float \| None  | Fuel consumption slope (L/lap²), None if unavailable |

### StintComparison

| Field              | Type                        | Description                                       |
| ------------------ | --------------------------- | ------------------------------------------------- |
| stint_a_index      | int                         | Index of first stint                              |
| stint_b_index      | int                         | Index of second stint                             |
| setup_changes      | list[SetupParameterDelta]   | Parameters that changed between stints            |
| metric_deltas      | MetricDeltas                | Aggregated metric differences (B - A)             |

### SetupParameterDelta

| Field     | Type         | Description                              |
| --------- | ------------ | ---------------------------------------- |
| section   | str          | INI section name                         |
| name      | str          | Parameter name                           |
| value_a   | float \| str | Value in stint A                         |
| value_b   | float \| str | Value in stint B                         |

### MetricDeltas

| Field                | Type              | Description                                    |
| -------------------- | ----------------- | ---------------------------------------------- |
| lap_time_delta_s     | float \| None     | B mean - A mean; None if either unavailable    |
| tyre_temp_delta      | dict[str, float]  | B avg - A avg per wheel                        |
| slip_angle_delta     | dict[str, float]  | B avg - A avg per wheel                        |
| slip_ratio_delta     | dict[str, float]  | B avg - A avg per wheel                        |
| peak_lat_g_delta     | float \| None     | B avg - A avg                                  |

### ConsistencyMetrics

| Field                  | Type                        | Description                                    |
| ---------------------- | --------------------------- | ---------------------------------------------- |
| flying_lap_count       | int                         | Number of flying laps analyzed                 |
| lap_time_stddev_s      | float                       | Standard deviation of flying lap times         |
| best_lap_time_s        | float                       | Fastest flying lap time                        |
| worst_lap_time_s       | float                       | Slowest flying lap time                        |
| lap_time_trend_slope   | float \| None               | Linear slope; None if < 2 flying laps          |
| corner_consistency     | list[CornerConsistency]     | Per-corner variance data                       |

### CornerConsistency

| Field                  | Type           | Description                                          |
| ---------------------- | -------------- | ---------------------------------------------------- |
| corner_number          | int            | Session-consistent corner number                     |
| apex_speed_variance    | float \| None  | Variance of apex speeds across laps; None if < 2     |
| apex_speed_stddev      | float \| None  | Stddev for readability                               |
| brake_point_variance   | float \| None  | Variance of brake points across laps; None if < 2    |
| sample_count           | int            | Number of laps that had this corner                  |

## Validation Rules

1. All `dict[str, ...]` keyed by wheel use lowercase keys: `"fl"`, `"fr"`, `"rl"`, `"rr"`
2. All percentage values are in range [0.0, 100.0]
3. All speed values are in km/h (matching parser convention)
4. All temperature values are in °C
5. All pressure values are in PSI (matching AC telemetry output)
6. All time values are in seconds
7. Normalized positions are in range [0.0, 1.0]
8. Understeer ratio > 0.0 (ratio of positive values)
9. Gear distribution values sum to ~100.0 (within floating point tolerance)
