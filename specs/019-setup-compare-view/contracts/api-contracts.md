# API Contracts: Setup Compare View

**Feature**: 019-setup-compare-view
**Date**: 2026-03-06

## Consumed Endpoints (already exist — no changes needed)

### GET /sessions/{session_id}/stints

Returns all stints for an analyzed session.

**Request**: `GET /sessions/{session_id}/stints`

**Response** (200):
```json
{
  "session_id": "abc123",
  "stint_count": 3,
  "stints": [
    {
      "stint_index": 0,
      "setup_filename": "baseline.ini",
      "lap_numbers": [1, 2, 3, 4, 5],
      "flying_lap_count": 3,
      "aggregated": {
        "lap_time_mean_s": 82.45,
        "lap_time_stddev_s": 0.32,
        "tyre_temp_avg": { "FL": 91.2, "FR": 92.1, "RL": 88.5, "RR": 89.1 },
        "slip_angle_avg": { "FL": 3.2, "FR": 3.1, "RL": 2.8, "RR": 2.9 },
        "slip_ratio_avg": { "FL": 0.05, "FR": 0.05, "RL": 0.04, "RR": 0.04 },
        "peak_lat_g_avg": 1.42
      },
      "trends": {
        "lap_time_slope": 0.15,
        "tyre_temp_slope": { "FL": 0.8, "FR": 0.9, "RL": 0.5, "RR": 0.6 },
        "fuel_consumption_slope": null
      }
    }
  ]
}
```

**Error** (404): Session not found or not analyzed.

---

### GET /sessions/{session_id}/compare

Returns setup diff and metric deltas between two stints.

**Request**: `GET /sessions/{session_id}/compare?stint_a=0&stint_b=1`

**Query Parameters**:
- `stint_a` (required, int): First stint index
- `stint_b` (required, int): Second stint index

**Response** (200):
```json
{
  "session_id": "abc123",
  "comparison": {
    "stint_a_index": 0,
    "stint_b_index": 1,
    "setup_changes": [
      {
        "section": "WING",
        "name": "REAR",
        "value_a": 12,
        "value_b": 10
      },
      {
        "section": "TYRES",
        "name": "PRESSURE_LF",
        "value_a": 26.5,
        "value_b": 27.0
      }
    ],
    "metric_deltas": {
      "lap_time_delta_s": -0.45,
      "tyre_temp_delta": { "FL": -1.2, "FR": -0.8, "RL": -0.5, "RR": -0.3 },
      "slip_angle_delta": { "FL": -0.2, "FR": -0.1, "RL": 0.0, "RR": 0.1 },
      "slip_ratio_delta": { "FL": 0.0, "FR": 0.0, "RL": 0.0, "RR": 0.0 },
      "peak_lat_g_delta": 0.05
    }
  }
}
```

**Error** (404): Stint index not found or no comparison available.

## UI Component Contracts

### CompareView (index.tsx)

**Props**: None (reads session from Zustand store)
**State**: `selectedStints: [number, number | null]`
**Behavior**:
- Reads `selectedSessionId` from `sessionStore`
- Fetches stints via `useStints(sessionId)`
- On load with 2+ stints, defaults selection to `[0, 1]`
- Fetches comparison via `useStintComparison(sessionId, stintA, stintB)` when both selected
- Renders empty states for: no session, not analyzed, single stint, loading

### StintSelector

**Props**:
- `stints: StintMetrics[]` — all stints
- `selectedStints: [number, number | null]` — currently selected pair
- `onSelect: (stintIndex: number) => void` — callback when a stint is clicked

**Behavior**:
- Displays each stint as a selectable card/row
- Shows stint index (1-indexed), setup filename, flying lap count, average lap time
- Highlights selected stints (up to 2)
- Clicking a stint: if already selected, deselect; if 2 already selected, replace oldest

### SetupDiff

**Props**:
- `changes: SetupParameterDelta[]` — changed parameters
- `stintAIndex: number` — for column headers
- `stintBIndex: number` — for column headers

**Behavior**:
- Groups changes by `section` field
- Each section is a collapsible group (default: expanded)
- Within each group, rows show parameter name, value A, arrow, value B
- Numeric values show directional arrow (up/down)
- Empty `changes` array shows "No setup changes" message

### MetricsPanel

**Props**:
- `deltas: MetricDeltas` — performance metric deltas
- `stintAIndex: number` — for labels
- `stintBIndex: number` — for labels

**Behavior**:
- Displays each metric delta as a labeled card
- Sign prefix: `+` for positive, `-` for negative (minus sign from number itself)
- Color: green for improvement, red for degradation (varies by metric)
- Null values displayed as "N/A"
- Lap time: negative delta = green (faster), positive = red (slower)
- Peak lateral G: positive delta = green (more grip), negative = red (less grip)
- Tyre temps: displayed per wheel, no color coding (context-dependent)
