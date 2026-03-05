# Data Model: Analysis Endpoints

**Feature**: 012-analysis-endpoints | **Date**: 2026-03-05

## Existing Entities (Not Modified)

### SessionRecord (SQLite)
Already defined in `ac_engineer.storage.models`. Fields used by this phase:
- `session_id` — primary key, used to locate session files
- `state` — lifecycle: "discovered" → "analyzed" (advanced by processing)
- `csv_path` — absolute path to CSV file (validated before processing)
- `meta_path` — absolute path to meta.json file (validated before processing)

### AnalyzedSession (Pydantic v2)
Already defined in `ac_engineer.analyzer.models`. Top-level output of the analysis pipeline:
- `metadata: SessionMetadata`
- `laps: list[AnalyzedLap]` — per-lap metrics with corners
- `stints: list[StintMetrics]` — per-stint aggregated metrics
- `stint_comparisons: list[StintComparison]` — adjacent stint deltas
- `consistency: ConsistencyMetrics | None` — session-wide consistency

### AnalyzedLap
- `lap_number: int`
- `classification: LapClassification` — "flying", "outlap", "inlap", "incomplete"
- `is_invalid: bool`
- `metrics: LapMetrics` — timing, tyres, grip, driver_inputs, speed, fuel, suspension
- `corners: list[CornerMetrics]` — per-corner metrics for this lap

### CornerMetrics
- `corner_number: int`
- `performance: CornerPerformance` — entry/apex/exit speed, duration
- `grip: CornerGrip` — lateral G, understeer ratio
- `technique: CornerTechnique` — brake point, throttle on, trail braking
- `loading: CornerLoading | None` — peak wheel loads

### StintMetrics
- `stint_index: int`
- `setup_filename: str | None`
- `lap_numbers: list[int]`
- `flying_lap_count: int`
- `aggregated: AggregatedStintMetrics`
- `trends: StintTrends | None`

### StintComparison
- `stint_a_index: int`, `stint_b_index: int`
- `setup_changes: list[SetupParameterDelta]`
- `metric_deltas: MetricDeltas`

### ConsistencyMetrics
- `flying_lap_count: int`
- `lap_time_stddev_s: float`
- `best_lap_time_s: float`, `worst_lap_time_s: float`
- `lap_time_trend_slope: float | None`
- `corner_consistency: list[CornerConsistency]`

## New Entities

### Cache File: analyzed.json
On-disk JSON representation of AnalyzedSession, stored at `{sessions_dir}/{session_id}/analyzed.json`.

**Schema**: Exact JSON output of `AnalyzedSession.model_dump(mode="json")`.

**Lifecycle**:
- Created by the processing pipeline after successful analysis
- Overwritten on re-processing (idempotent)
- Read by all metric query endpoints
- Never modified by metric queries

### Active Processing Jobs (In-Memory)
A `dict[str, str]` on `app.state.active_processing_jobs` mapping `session_id → job_id`.

**Lifecycle**:
- Entry added when POST /process creates a job
- Entry removed when the job completes (success or failure)
- Checked before creating a new job to enforce one-job-per-session

## API Response Models (New Pydantic v2 Models)

### LapSummary
Summary of one lap for the lap list endpoint.
- `lap_number: int`
- `classification: str`
- `is_invalid: bool`
- `lap_time_s: float`
- `tyre_temps_avg: dict[str, float]` — FL/FR/RL/RR core temps
- `peak_lat_g: float`
- `peak_lon_g: float`
- `full_throttle_pct: float`
- `braking_pct: float`

### LapListResponse
- `session_id: str`
- `lap_count: int`
- `laps: list[LapSummary]`

### LapDetailResponse
- `session_id: str`
- `lap_number: int`
- `classification: str`
- `is_invalid: bool`
- `metrics: LapMetrics` — full 7-group breakdown (re-uses existing model)

### AggregatedCorner
Aggregated metrics for one corner across flying laps.
- `corner_number: int`
- `sample_count: int` — number of flying laps with this corner
- `avg_apex_speed_kmh: float`
- `avg_entry_speed_kmh: float`
- `avg_exit_speed_kmh: float`
- `avg_duration_s: float`
- `avg_understeer_ratio: float | None`
- `avg_trail_braking_intensity: float`
- `avg_peak_lat_g: float`

### CornerListResponse
- `session_id: str`
- `corner_count: int`
- `corners: list[AggregatedCorner]`

### CornerLapEntry
One lap's metrics for a specific corner.
- `lap_number: int`
- `metrics: CornerMetrics` — re-uses existing model

### CornerDetailResponse
- `session_id: str`
- `corner_number: int`
- `laps: list[CornerLapEntry]`

### StintListResponse
- `session_id: str`
- `stint_count: int`
- `stints: list[StintMetrics]` — re-uses existing model

### StintComparisonResponse
- `session_id: str`
- `comparison: StintComparison` — re-uses existing model

### ConsistencyResponse
- `session_id: str`
- `consistency: ConsistencyMetrics` — re-uses existing model

### ProcessResponse
- `job_id: str`
- `session_id: str`

## State Transitions

```
Session State Machine (this phase adds the discovered → analyzed transition):

  discovered ──[POST /process]──→ (processing job runs) ──→ analyzed
       │                                    │
       │                                    └── on failure: stays discovered
       │
  analyzed ──[POST /process]──→ (re-processing job) ──→ analyzed (cache overwritten)
```

The intermediate "parsed" state is not exposed to the user — the pipeline atomically transitions from "discovered" to "analyzed". If a session is already "analyzed" and re-processed, it stays "analyzed" throughout.
