# API Contract Changes: Phase 7.4 — Lap Analysis View

**Branch**: `018-lap-analysis-view` | **Date**: 2026-03-06

## New Endpoint

### GET /sessions/{session_id}/laps/{lap_number}/telemetry

Returns per-sample telemetry trace data for one lap, suitable for charting against track position.

**Path Parameters:**
- `session_id` (string, required) — session identifier
- `lap_number` (integer, required) — lap number within the session

**Query Parameters:**
- `max_samples` (integer, optional, default=500) — maximum number of samples to return. If the lap has more samples, evenly downsample. Set to 0 for all samples.

**Response (200 OK):**
```json
{
  "session_id": "abc123",
  "lap_number": 3,
  "sample_count": 500,
  "channels": {
    "normalized_position": [0.0, 0.002, 0.004, ...],
    "throttle": [0.95, 0.98, 1.0, ...],
    "brake": [0.0, 0.0, 0.0, ...],
    "steering": [0.02, 0.01, -0.03, ...],
    "speed_kmh": [245.3, 246.1, 247.0, ...],
    "gear": [6.0, 6.0, 6.0, ...]
  }
}
```

**Channel value ranges:**
- `normalized_position`: 0.0 – 1.0 (fraction of track length)
- `throttle`: 0.0 – 1.0 (0% – 100%)
- `brake`: 0.0 – 1.0 (0% – 100%)
- `steering`: approximately -1.0 – 1.0 (normalized, negative = left)
- `speed_kmh`: 0.0+ (km/h)
- `gear`: 0.0+ (integer values as float: 0=neutral, 1-7 typical range)

**Error Responses:**
- `404` — session not found
- `409` — session not in "analyzed" or "engineered" state
- `404` — lap number not found in session

**Data Source:** Reads from `{sessions_dir}/{session_id}/{csv_base}/telemetry.parquet` (cached by processing pipeline).

---

## Modified Endpoints

### GET /sessions/{session_id}/laps (LapSummary changes)

**Added fields to each LapSummary object:**
```json
{
  "max_speed": 267.4,
  "sector_times_s": [32.1, 45.7, 28.9]
}
```

- `max_speed` (float) — peak speed in km/h during the lap
- Source: `LapMetrics.speed.max_speed`
- `sector_times_s` (array of floats or null) — sector times in seconds, null if not available for the track
- Source: `LapMetrics.timing.sector_times_s`
- Both are backwards-compatible additions

### GET /sessions/{session_id}/laps/{lap_number} (LapDetailResponse changes)

**Added field:**
```json
{
  "corners": [
    {
      "corner_number": 1,
      "performance": {
        "entry_speed_kmh": 185.3,
        "apex_speed_kmh": 112.5,
        "exit_speed_kmh": 145.7,
        "duration_s": 3.2
      },
      "grip": {
        "peak_lat_g": 2.1,
        "avg_lat_g": 1.8,
        "understeer_ratio": 0.15
      },
      "technique": {
        "brake_point_norm": 0.12,
        "throttle_on_norm": 0.65,
        "trail_braking_intensity": 0.4
      }
    }
  ]
}
```

- `corners` (array of CornerMetrics, default `[]`) — per-corner metrics for this lap
- Source: `AnalyzedLap.corners`
- Backwards-compatible addition (new field with default empty list)

---

## UI Contract: View Component Interface

### AnalysisView

**Inputs (from stores/props):**
- `selectedSessionId: string | null` — from `useSessionStore`
- Navigation: already wired in AppShell VIEW_MAP as `"analysis"` key

**Internal state:**
- `selectedLaps: number[]` — local `useState`, max length 2

**Data dependencies (TanStack Query):**
- `["laps", sessionId]` → `LapListResponse`
- `["lap-detail", sessionId, lapNumber]` → `LapDetailResponse` (fetched per selected lap)
- `["telemetry", sessionId, lapNumber]` → `LapTelemetryResponse` (fetched per selected lap)

**Empty states:**
- No session selected → prompt to go to Sessions view
- Session not analyzed → prompt indicating analysis is required
- No flying laps → message about no valid laps available
