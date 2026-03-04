# Research: Telemetry Analyzer

**Feature**: 004-telemetry-analyzer
**Date**: 2026-03-04

## R1: NaN Handling Strategy for Optional Metrics

**Decision**: Use `None` (Optional) at the Pydantic model level for metrics that cannot be computed. Use `numpy.nanmean`/`numpy.nanmax` internally so a few NaN samples within an otherwise valid channel don't break computation — only set to None when the entire channel is NaN.

**Rationale**: The parser already marks reduced-mode sessions where 28 sim_info channels are NaN. The analyzer must degrade gracefully. Using `float | None` in Pydantic models makes it explicit which metrics are unavailable vs. zero. Internal numpy nan-aware functions prevent individual bad samples from poisoning an entire metric.

**Alternatives considered**:
- Sentinel values (e.g., -1.0): Rejected — ambiguous, could be confused with real values
- Raising exceptions: Rejected — spec requires graceful degradation (FR-021)
- Separate "availability" flags: Rejected — `None` already communicates unavailability without adding complexity

## R2: Understeer/Oversteer Tendency Calculation

**Decision**: Compute as ratio of average absolute front slip angle to average absolute rear slip angle during cornering: `mean(|slip_angle_fl|, |slip_angle_fr|) / mean(|slip_angle_rl|, |slip_angle_rr|)`. Ratio > 1.0 = understeer, < 1.0 = oversteer, ~1.0 = neutral.

**Rationale**: This is the standard definition used in vehicle dynamics (Milliken & Milliken). Slip angles are already captured per-wheel. Using the mean of left+right per axle normalizes for asymmetric loading. Using absolute values handles sign convention differences.

**Edge case**: When rear axle slip angle average is below epsilon (e.g., 0.01 rad), understeer_ratio is set to None rather than a misleading default. A near-zero denominator means there is insufficient rear slip data to compute a meaningful ratio — reporting None (per FR-021) is more honest than defaulting to 1.0 which would falsely imply neutral balance.

**Alternatives considered**:
- Yaw rate vs. expected yaw rate: More accurate but requires vehicle model parameters not available generically
- Steering angle vs. lateral G: Simpler but less precise and varies with steering ratio across cars
- Default to 1.0 (neutral) when rear slip ≈ 0: Rejected — violates FR-021 (unavailable metrics must be None) and misleads the AI Engineer into thinking the car is balanced when there's simply no data

## R3: Linear Trend Computation Method

**Decision**: Use `scipy.stats.linregress` for slope calculation in stint trends (lap time trend, tyre temp trend, fuel trend). The slope value alone is stored (intercept, r-value, p-value discarded). Requires scipy dependency addition.

**Rationale**: `linregress` is simple, fast for small N (2-15 laps per stint), and returns the slope directly. The slope sign and magnitude are what matter: positive slope = increasing (degrading for lap times, heating for tyres), negative = improving/cooling.

**Alternatives considered**:
- numpy polyfit: Equally valid, but linregress is more semantically clear for "trend"
- Manual slope calculation: Error-prone, linregress handles edge cases
- scipy curve_fit with exponential: Over-engineering for stint-length data (2-15 points)

## R4: Corner Time Series Extraction

**Decision**: Extract corner data by filtering the lap DataFrame where `entry_norm_pos <= normalized_position <= exit_norm_pos`. Handle position wrap-around (corner spanning 0.95→0.05) by splitting the filter into two ranges.

**Rationale**: The parser's CornerSegment provides entry/apex/exit normalized positions (0.0-1.0). The time series data has a `normalized_position` column. Filtering by position range gives us the exact samples within each corner.

**Alternatives considered**:
- Index-based extraction: Fragile — depends on sample rate and position distribution
- Time-based extraction: Would need to compute corner start/end timestamps first, adding unnecessary complexity

## R5: Stint Grouping Strategy

**Decision**: Group laps by identity of `active_setup` (the SetupEntry object reference or its `lap_start` + `filename` as key). Consecutive laps with the same active_setup form a stint. A change in active_setup starts a new stint.

**Rationale**: The parser already associates each lap with its active setup via the `active_setup` field on LapSegment. Grouping by consecutive runs of the same setup is the natural definition of a stint. The real session data shows 2 setup snapshots (session_start at lap 0, pit_exit at lap 2), which should produce 2 stints.

**Alternatives considered**:
- Group by pit stops (in_pit_lane transitions): Less precise — a pit stop without setup change shouldn't create a new stint
- Group by fixed lap count: Arbitrary and meaningless

## R6: Sector Time Computation

**Decision**: Define 3 equal sectors by normalized position (0.0-0.333, 0.333-0.667, 0.667-1.0) as a sensible default when no track-specific sector boundaries are available. Compute sector time as timestamp delta between sector boundary crossings (interpolated).

**Rationale**: Assetto Corsa does not expose official sector boundaries in the telemetry data. Equal-thirds is a reasonable approximation used by many telemetry tools. Interpolation between samples gives sub-sample accuracy for the boundary crossing timestamps.

**Alternatives considered**:
- Skip sector times entirely: Loses useful diagnostic data
- Use speed minima to define sectors: Track-dependent, unreliable for fast tracks
- Configurable sector boundaries: Over-engineering for Phase 3; can be added later if needed

## R7: Brake/Throttle Threshold Values

**Decision**: Use 0.05 as the threshold for "brake applied" and "throttle applied" (5% of pedal travel). Use 0.95 as the threshold for "full throttle" (95% of pedal travel). These are configurable constants at the module level.

**Rationale**: AC telemetry reports throttle and brake as 0.0-1.0 normalized values. Small residual values (< 5%) can come from dead zones in hardware or resting foot on pedal. 5% threshold filters these out. The parser tests already use similar thresholds.

**Alternatives considered**:
- Zero/one thresholds: Too strict — real hardware rarely hits exactly 0.0 or 1.0
- Per-session calibration: Over-engineering, and 5% is standard practice
