# Data Model: Setup Compare View

**Feature**: 019-setup-compare-view
**Date**: 2026-03-06

## TypeScript Types (Frontend)

All types below are added to `frontend/src/lib/types.ts` and mirror the backend Pydantic models serialized as JSON.

### AggregatedStintMetrics

Aggregated performance metrics for a single stint's flying laps.

| Field | Type | Description |
|-------|------|-------------|
| lap_time_mean_s | `number \| null` | Mean lap time in seconds |
| lap_time_stddev_s | `number \| null` | Lap time standard deviation |
| tyre_temp_avg | `Record<string, number>` | Average tyre temp per wheel position (FL, FR, RL, RR) |
| slip_angle_avg | `Record<string, number>` | Average slip angle per wheel |
| slip_ratio_avg | `Record<string, number>` | Average slip ratio per wheel |
| peak_lat_g_avg | `number \| null` | Average peak lateral G |

### StintTrends

| Field | Type | Description |
|-------|------|-------------|
| lap_time_slope | `number` | Trend slope of lap times within the stint |
| tyre_temp_slope | `Record<string, number>` | Tyre temp trend per wheel |
| fuel_consumption_slope | `number \| null` | Fuel consumption trend |

### StintMetrics

One stint's metadata and metrics. Returned in the stints list.

| Field | Type | Description |
|-------|------|-------------|
| stint_index | `number` | 0-based stint index |
| setup_filename | `string \| null` | Setup .ini filename, null if unknown |
| lap_numbers | `number[]` | Lap numbers in this stint |
| flying_lap_count | `number` | Number of flying laps |
| aggregated | `AggregatedStintMetrics` | Aggregated stint performance |
| trends | `StintTrends \| null` | Trend data within stint |

### SetupParameterDelta

A single parameter that changed between two stints.

| Field | Type | Description |
|-------|------|-------------|
| section | `string` | INI section name (e.g., "SUSPENSION", "TYRES") |
| name | `string` | Parameter name within the section |
| value_a | `number \| string` | Value in stint A |
| value_b | `number \| string` | Value in stint B |

### MetricDeltas

Performance metric differences between two stints (B - A).

| Field | Type | Description |
|-------|------|-------------|
| lap_time_delta_s | `number \| null` | Lap time difference (positive = slower) |
| tyre_temp_delta | `Record<string, number>` | Tyre temp difference per wheel |
| slip_angle_delta | `Record<string, number>` | Slip angle difference per wheel |
| slip_ratio_delta | `Record<string, number>` | Slip ratio difference per wheel |
| peak_lat_g_delta | `number \| null` | Peak lateral G difference |

### StintComparison

Full comparison payload between two stints.

| Field | Type | Description |
|-------|------|-------------|
| stint_a_index | `number` | First stint index |
| stint_b_index | `number` | Second stint index |
| setup_changes | `SetupParameterDelta[]` | Parameters that differ |
| metric_deltas | `MetricDeltas` | Performance metric differences |

### API Response Wrappers

**StintListResponse** — `GET /sessions/{id}/stints`

| Field | Type | Description |
|-------|------|-------------|
| session_id | `string` | Session identifier |
| stint_count | `number` | Total number of stints |
| stints | `StintMetrics[]` | All stints in the session |

**StintComparisonResponse** — `GET /sessions/{id}/compare?stint_a=X&stint_b=Y`

| Field | Type | Description |
|-------|------|-------------|
| session_id | `string` | Session identifier |
| comparison | `StintComparison` | The comparison result |

## Entity Relationships

```
Session (selected via sessionStore)
  └── has many StintMetrics (via GET /stints)
        └── pair of two StintMetrics → StintComparison (via GET /compare)
              ├── setup_changes: SetupParameterDelta[]
              └── metric_deltas: MetricDeltas
```

## State Management

| State | Layer | Location | Description |
|-------|-------|----------|-------------|
| Selected session ID | Zustand | `sessionStore.selectedSessionId` | Already exists from Phase 7.3 |
| Stints list | TanStack Query | `["stints", sessionId]` | Immutable, staleTime: Infinity |
| Stint comparison | TanStack Query | `["stint-comparison", sessionId, stintA, stintB]` | Immutable, enabled only when both stints selected |
| Selected stint pair | React useState | `CompareView` component | `[stintA: number, stintB: number \| null]` tuple |
| Show all params toggle | React useState | `SetupDiff` component | Boolean, default false (descoped — future enhancement) |
