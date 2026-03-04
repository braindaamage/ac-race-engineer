# Feature Specification: Telemetry Analyzer

**Feature Branch**: `004-telemetry-analyzer`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Build a telemetry analyzer module that takes ParsedSession objects from the Phase 2 parser and computes structured performance metrics per lap, per corner, and per stint — ready for the AI Engineer (Phase 5) to reason about and the Desktop App (Phase 7) to visualize."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze a Single Lap's Performance (Priority: P1)

The AI Engineer or Desktop App passes a ParsedSession to the analyzer and receives per-lap metrics for every analyzable lap. For each lap, the output includes timing data, tyre temperatures and pressures, grip indicators (slip angles and ratios), driver input statistics, speed profile, fuel consumption, and suspension travel — all computed from the raw time series data in the lap segment.

**Why this priority**: Per-lap metrics are the foundational building block. Every other analysis (corner, stint, consistency) depends on having lap-level data computed first. A single lap's metrics already deliver value for understanding car behavior.

**Independent Test**: Can be fully tested by passing a ParsedSession with one flying lap and verifying all metric categories are populated with correct values derived from the time series data.

**Acceptance Scenarios**:

1. **Given** a ParsedSession with 2 flying laps (full telemetry), **When** the analyzer processes it, **Then** each flying lap has a complete LapMetrics object with timing, tyre, grip, driver input, speed, fuel, and suspension metrics — all values derived from the lap's time series data.
2. **Given** a ParsedSession with an invalid lap that has usable data, **When** the analyzer processes it, **Then** the invalid lap also receives a LapMetrics object with an `is_invalid` flag set to true, and all computable metrics are present.
3. **Given** a ParsedSession in reduced mode (tyre_wear, fuel channels are NaN), **When** the analyzer processes it, **Then** fuel consumption and tyre wear metrics are marked as unavailable (None/null), while all other metrics are computed normally.
4. **Given** a ParsedSession with an outlap and an inlap, **When** the analyzer processes it, **Then** outlaps and inlaps also receive metrics (they contain useful data like tyre warm-up behavior), each flagged with their classification.

---

### User Story 2 - Analyze Corner-by-Corner Performance (Priority: P1)

For each corner on each lap, the analyzer computes detailed metrics: entry/apex/exit speeds recalculated from the time series, time spent in the corner, lateral G statistics, understeer/oversteer tendency, braking and throttle application points, trail braking intensity, and tyre loading data. These corner metrics allow the AI Engineer to pinpoint specific corners where the car behaves poorly.

**Why this priority**: Corner-level analysis is equally critical to lap-level — it's where the AI Engineer correlates setup parameters to specific handling problems ("understeer in corner 3 suggests more front downforce").

**Independent Test**: Can be tested by passing a ParsedSession with one lap containing detected corners and verifying each corner has accurate performance, grip, technique, and loading metrics derived from the time series data within the corner's normalized position boundaries.

**Acceptance Scenarios**:

1. **Given** a lap with 5 detected corners (from the parser's CornerSegment data), **When** the analyzer processes it, **Then** 5 CornerMetrics objects are produced, each with performance (speeds, duration), grip (lateral G, understeer/oversteer tendency), technique (brake point, throttle point, trail braking), and tyre loading data.
2. **Given** a corner where the driver did not brake (e.g., a flat-out kink), **When** the analyzer computes corner metrics, **Then** brake point is None/null and trail braking intensity is 0.
3. **Given** a lap where a corner is missing (driver went off-track and the parser did not detect it), **When** compared with other laps that have that corner, **Then** the missing corner is simply absent from that lap's corner metrics — no placeholder or error.

---

### User Story 3 - Compare Performance Across Stints (Priority: P2)

The analyzer groups laps by their active setup (from the parser's setup-stint association) and computes aggregated metrics per stint: mean/stddev lap times, mean tyre temperatures and grip indicators. It also identifies trends within each stint (tyre temp evolution, lap time progression) and, when multiple stints exist, computes a cross-stint comparison highlighting which metrics changed significantly between setup changes.

**Why this priority**: Stint comparison is the key input for the AI Engineer to correlate setup changes with on-track behavior changes. However, it builds on top of lap-level metrics (P1) and requires at least 2 stints to provide cross-stint comparison value.

**Independent Test**: Can be tested by passing a ParsedSession with 2 stints (different active setups) containing at least 2 flying laps each, and verifying that aggregated metrics, within-stint trends, and cross-stint deltas are computed correctly.

**Acceptance Scenarios**:

1. **Given** a ParsedSession with 2 stints (setup A for laps 1-3, setup B for laps 4-6), **When** the analyzer processes it, **Then** 2 StintMetrics objects are produced, each with aggregated lap times (mean, stddev), mean tyre temperatures, and mean grip indicators.
2. **Given** a stint with 3 consecutive flying laps, **When** the analyzer computes trends, **Then** tyre temperature trend (slope over laps), lap time trend (slope over laps), and fuel consumption trend are included in the stint metrics.
3. **Given** 2 stints with different setups, **When** the analyzer computes cross-stint comparison, **Then** a StintComparison object shows the delta for each metric category (lap time delta, tyre temp deltas, grip deltas) between the two stints, plus the setup parameters that changed.
4. **Given** a session with only 1 stint, **When** the analyzer processes it, **Then** the single stint's aggregated metrics and trends are computed, but no cross-stint comparison is produced.
5. **Given** a stint with only 1 flying lap, **When** the analyzer computes stint metrics, **Then** aggregated metrics use that single lap's values, stddev is 0 or None, and trends are not computed (insufficient data).

---

### User Story 4 - Assess Driver Consistency (Priority: P3)

Across all flying laps in the session, the analyzer computes consistency metrics: lap time standard deviation, best vs worst lap time, lap time trend line, per-corner apex speed variance across laps, and per-corner brake point variance across laps.

**Why this priority**: Consistency analysis helps differentiate between car problems and driver problems. If corner speeds vary wildly, the issue may be driver inconsistency rather than setup. This is secondary to the core metrics but important for the AI Engineer's reasoning quality.

**Independent Test**: Can be tested by passing a ParsedSession with 3+ flying laps and verifying that consistency metrics (stddev, variance per corner, trend) are computed correctly.

**Acceptance Scenarios**:

1. **Given** a session with 4 flying laps, **When** the analyzer computes consistency, **Then** a ConsistencyMetrics object includes lap time stddev, best/worst lap time, lap time trend (slope), and per-corner apex speed variance.
2. **Given** a session with only 1 flying lap, **When** the analyzer attempts consistency analysis, **Then** consistency metrics report single-lap values (stddev=0, no variance, no trend) rather than failing.
3. **Given** a corner that exists in 3 out of 4 laps (missed once), **When** computing per-corner variance, **Then** the variance is computed from the 3 available data points without error.

---

### Edge Cases

- **All laps invalid**: Every lap receives metrics, all flagged as `is_invalid=True`. Stint and consistency analysis still computed from available data.
- **Reduced mode session**: Channels like `tyre_wear_*`, `fuel`, `wheel_load_*` are NaN. Metrics depending on these channels are `None`; all other metrics compute normally.
- **Very short stints (1-2 laps)**: Stint metrics are computed with available data. Trends require at least 2 data points; with 1 lap, trend is None.
- **Setup change with no measurable effect**: Cross-stint comparison reports deltas near zero honestly — no artificial correlation.
- **Lap with no corners detected**: Lap metrics are still computed; corner metrics list is empty for that lap.
- **Identical timestamps (degenerate data)**: Duration calculations handle zero-duration edge cases without division by zero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a ParsedSession object and return an AnalyzedSession object containing all computed metrics without modifying the input ParsedSession.
- **FR-002**: System MUST compute lap-level metrics for every lap in the session (flying, outlap, inlap, invalid, incomplete), with each metric set flagged by lap classification and is_invalid status.
- **FR-003**: System MUST compute timing metrics per lap: lap time (seconds, derived from end_timestamp - start_timestamp), and sector times when the session has sufficient normalized position data to define sector boundaries.
- **FR-004**: System MUST compute tyre analysis metrics per lap per wheel (FL, FR, RL, RR): average and peak temperatures for each zone (core, inner, mid, outer), average pressure, temperature spread (inner-outer delta), and front-to-rear temperature balance.
- **FR-005**: System MUST compute tyre wear rate per lap per wheel when tyre_wear channels contain valid (non-NaN) data. When unavailable, wear metrics MUST be None.
- **FR-006**: System MUST compute grip indicators per lap: average and peak slip angles per wheel, average and peak slip ratios per wheel, peak lateral G, and peak longitudinal G.
- **FR-007**: System MUST compute driver input metrics per lap: full-throttle percentage (throttle >= 0.95), partial-throttle percentage (0.05 < throttle < 0.95), off-throttle percentage (throttle <= 0.05), braking percentage (brake > 0.05), average absolute steering angle, and gear usage distribution (percentage of time in each gear).
- **FR-008**: System MUST compute speed profile per lap: maximum speed, minimum speed (excluding samples where speed < 10 km/h to filter pit/stationary), and average speed.
- **FR-009**: System MUST compute fuel consumption per lap (fuel at start of lap minus fuel at end of lap) when the fuel channel contains valid data. When unavailable, fuel metrics MUST be None.
- **FR-010**: System MUST compute suspension metrics per lap per wheel: average travel, peak travel, and travel range (max - min).
- **FR-011**: System MUST compute corner-level metrics for each CornerSegment on each lap, extracting the relevant time series data between the corner's entry_norm_pos and exit_norm_pos boundaries.
- **FR-012**: System MUST compute corner performance metrics: entry speed, apex speed, exit speed (recalculated from time series), and corner duration (time from entry to exit).
- **FR-013**: System MUST compute corner grip metrics: peak lateral G, average lateral G, and understeer/oversteer tendency (ratio of average front slip angle to average rear slip angle during the corner, where >1 indicates understeer and <1 indicates oversteer).
- **FR-014**: System MUST compute corner technique metrics: brake point (normalized position where brake first exceeds threshold), throttle-on point (normalized position where throttle first exceeds threshold after the apex), and trail braking intensity (mean brake pressure during samples where both brake > threshold and absolute steering angle > threshold).
- **FR-015**: System MUST compute corner tyre loading metrics when wheel_load channels are available: peak wheel load per wheel. When unavailable, loading metrics MUST be None.
- **FR-016**: System MUST group laps into stints based on the active_setup field of each LapSegment, and compute aggregated metrics per stint: mean and standard deviation of lap times (flying laps only), mean tyre temperatures, and mean grip indicators.
- **FR-017**: System MUST compute within-stint trends when a stint contains 2 or more flying laps: tyre temperature trend (linear slope over consecutive laps), lap time trend (linear slope), and fuel consumption trend (linear slope, when available).
- **FR-018**: System MUST compute cross-stint comparison when 2 or more stints exist: delta of each aggregated metric between consecutive stints, plus the list of setup parameters that changed.
- **FR-019**: System MUST compute session-wide consistency metrics across all flying laps: lap time standard deviation, best and worst lap times, lap time trend (linear slope), per-corner apex speed variance, and per-corner brake point variance.
- **FR-020**: System MUST be fully deterministic — identical ParsedSession input MUST always produce identical output. No randomness, no external calls, pure computation.
- **FR-021**: System MUST handle missing/NaN channels gracefully: when a channel required for a metric is entirely NaN, that metric MUST be set to None rather than raising an error.
- **FR-022**: System MUST work with any car and any track — no hardcoded channel names beyond the standard telemetry column names, no hardcoded corner counts or expected metric ranges.
- **FR-023**: System MUST NOT perform any file I/O. It receives ParsedSession objects and returns AnalyzedSession objects. No HTTP awareness.
- **FR-024**: System MUST NOT call any LLM or AI service. All computation is pure Python with numerical libraries (numpy, pandas, scipy).

### Key Entities

- **AnalyzedSession**: Top-level result containing session metadata reference, list of AnalyzedLap objects, list of StintMetrics objects, optional ConsistencyMetrics, and optional list of StintComparison objects.
- **AnalyzedLap**: Per-lap result containing lap reference (number, classification, is_invalid), LapMetrics, and list of CornerMetrics.
- **LapMetrics**: Structured collection of timing, tyre, grip, driver input, speed, fuel, and suspension metrics for one lap.
- **CornerMetrics**: Structured collection of performance, grip, technique, and loading metrics for one corner on one lap.
- **StintMetrics**: Aggregated metrics for a group of laps sharing the same active setup, including trends.
- **StintComparison**: Delta metrics between two consecutive stints, including the setup parameters that changed.
- **ConsistencyMetrics**: Session-wide variance and trend analysis across all flying laps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The analyzer produces complete lap-level metrics for 100% of laps in a ParsedSession, with no unhandled exceptions for any lap classification or data quality level.
- **SC-002**: Corner-level metrics are computed for every detected corner on every lap, with entry/apex/exit speeds within 2 km/h of values derived from direct time series inspection.
- **SC-003**: Stint comparison correctly identifies all setup parameter changes between stints and reports metric deltas that are arithmetically consistent with the per-stint aggregated values.
- **SC-004**: The analyzer gracefully handles reduced-mode sessions by producing all computable metrics and setting unavailable metrics to None, with zero exceptions raised.
- **SC-005**: Consistency metrics correctly identify the best and worst laps, and per-corner variance values match hand-calculated variance from the input data.
- **SC-006**: The analyzer processes the real example session (BMW M235i at Mugello, ~5 laps across 2 stints) and produces a complete AnalyzedSession with plausible values for all metric categories.
- **SC-007**: Output is fully deterministic — running the analyzer twice on the same ParsedSession produces byte-identical results.
- **SC-008**: The AnalyzedSession output structure contains sufficient information for the AI Engineer to reference specific metrics by name (e.g., "front slip angle average in corner 3") and for the Desktop App to render lap time charts, tyre temperature heatmaps, and corner comparison overlays.
