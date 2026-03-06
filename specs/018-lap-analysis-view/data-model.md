# Data Model: Phase 7.4 — Lap Analysis View

**Branch**: `018-lap-analysis-view` | **Date**: 2026-03-06

## Frontend TypeScript Types

### New Types (to add to `frontend/src/lib/types.ts`)

```typescript
/** Summary of one lap for the lap list. */
export interface LapSummary {
  lap_number: number;
  classification: "flying" | "outlap" | "inlap" | "invalid" | "incomplete";
  is_invalid: boolean;
  lap_time_s: number;
  tyre_temps_avg: Record<string, number>; // { fl, fr, rl, rr }
  peak_lat_g: number;
  peak_lon_g: number;
  full_throttle_pct: number;
  braking_pct: number;
  max_speed: number; // NEW — peak speed km/h
}

/** Response for GET /sessions/{id}/laps */
export interface LapListResponse {
  session_id: string;
  lap_count: number;
  laps: LapSummary[];
}

/** Per-lap telemetry trace channels indexed by normalized track position. */
export interface LapTelemetryResponse {
  session_id: string;
  lap_number: number;
  sample_count: number;
  channels: {
    normalized_position: number[];
    throttle: number[];
    brake: number[];
    steering: number[];
    speed_kmh: number[];
    gear: number[];
  };
}

/** Wheel temperature zones. */
export interface WheelTempZones {
  core: number;
  inner: number;
  mid: number;
  outer: number;
}

/** Timing metrics within LapMetrics. */
export interface TimingMetrics {
  lap_time_s: number;
  sector_times_s: number[] | null;
}

/** Speed metrics within LapMetrics. */
export interface SpeedMetrics {
  max_speed: number;
  min_speed: number;
  avg_speed: number;
}

/** Driver input metrics within LapMetrics. */
export interface DriverInputMetrics {
  full_throttle_pct: number;
  partial_throttle_pct: number;
  off_throttle_pct: number;
  braking_pct: number;
  avg_steering_angle: number;
  gear_distribution: Record<number, number>;
}

/** Tyre metrics within LapMetrics. */
export interface TyreMetrics {
  temps_avg: Record<string, WheelTempZones>;
  temps_peak: Record<string, WheelTempZones>;
  pressure_avg: Record<string, number>;
  temp_spread: Record<string, number>;
  front_rear_balance: number;
  wear_rate: Record<string, number> | null;
}

/** Grip metrics within LapMetrics. */
export interface GripMetrics {
  slip_angle_avg: Record<string, number>;
  slip_angle_peak: Record<string, number>;
  slip_ratio_avg: Record<string, number>;
  slip_ratio_peak: Record<string, number>;
  peak_lat_g: number;
  peak_lon_g: number;
}

/** Suspension metrics within LapMetrics. */
export interface SuspensionMetrics {
  travel_avg: Record<string, number>;
  travel_peak: Record<string, number>;
  travel_range: Record<string, number>;
}

/** Fuel metrics within LapMetrics. */
export interface FuelMetrics {
  fuel_start: number;
  fuel_end: number;
  consumption: number;
}

/** Complete metrics for one lap. */
export interface LapMetrics {
  timing: TimingMetrics;
  tyres: TyreMetrics;
  grip: GripMetrics;
  driver_inputs: DriverInputMetrics;
  speed: SpeedMetrics;
  fuel: FuelMetrics | null;
  suspension: SuspensionMetrics;
}

/** Corner performance data. */
export interface CornerPerformance {
  entry_speed_kmh: number;
  apex_speed_kmh: number;
  exit_speed_kmh: number;
  duration_s: number;
}

/** Corner grip data. */
export interface CornerGrip {
  peak_lat_g: number;
  avg_lat_g: number;
  understeer_ratio: number | null;
}

/** Corner technique data. */
export interface CornerTechnique {
  brake_point_norm: number | null;
  throttle_on_norm: number | null;
  trail_braking_intensity: number;
}

/** Per-corner-per-lap metrics. */
export interface CornerMetrics {
  corner_number: number;
  performance: CornerPerformance;
  grip: CornerGrip;
  technique: CornerTechnique;
}

/** Response for GET /sessions/{id}/laps/{n} (extended with corners). */
export interface LapDetailResponse {
  session_id: string;
  lap_number: number;
  classification: string;
  is_invalid: boolean;
  metrics: LapMetrics;
  corners: CornerMetrics[]; // NEW — per-corner data for this lap
}
```

## Backend Model Changes

### `backend/api/analysis/models.py`

1. **LapSummary** — add field:
   ```python
   max_speed: float  # from LapMetrics.speed.max_speed
   ```

2. **LapDetailResponse** — add field:
   ```python
   corners: list[CornerMetrics] = []  # from AnalyzedLap.corners
   ```

3. **New model — LapTelemetryResponse**:
   ```python
   class LapTelemetryChannels(BaseModel):
       normalized_position: list[float]
       throttle: list[float]
       brake: list[float]
       steering: list[float]
       speed_kmh: list[float]
       gear: list[float]

   class LapTelemetryResponse(BaseModel):
       session_id: str
       lap_number: int
       sample_count: int
       channels: LapTelemetryChannels
   ```

## Entity Relationships

```
Session (1) ──── (*) Lap
  │                   │
  │                   ├── LapMetrics (1:1, aggregated stats)
  │                   ├── CornerMetrics (1:*, per-corner)
  │                   └── TelemetryTrace (1:1, position-indexed arrays)
  │
  └── (*) Stint
        └── StintMetrics (1:1)
```

## State Management

| Data | Layer | Cache Strategy |
|------|-------|----------------|
| Selected session ID | Zustand (sessionStore) | In-memory, no stale |
| Selected lap numbers (max 2) | React useState | Component-local |
| Lap list | TanStack Query `["laps", sessionId]` | `staleTime: Infinity` |
| Lap detail + corners | TanStack Query `["lap-detail", sessionId, lapNumber]` | `staleTime: Infinity`, `enabled: !!sessionId && selectedLaps.includes(lapNumber)` — only fetched for actively selected laps |
| Telemetry traces | TanStack Query `["telemetry", sessionId, lapNumber]` | `staleTime: Infinity`, `enabled: !!sessionId && selectedLaps.includes(lapNumber)` — only fetched for actively selected laps |

> With a maximum of 2 laps selected simultaneously, at most 4 queries are in-flight at once (2 lap-detail + 2 telemetry). Queries are automatically cancelled and garbage-collected when a lap is deselected.
