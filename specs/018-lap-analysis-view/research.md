# Research: Phase 7.4 — Lap Analysis View

**Branch**: `018-lap-analysis-view` | **Date**: 2026-03-06

## R1: Telemetry Trace Data Availability

### Decision: A new backend endpoint is required for per-lap telemetry traces

### Context

The spec requires telemetry traces (throttle, brake, steering, speed, gear) plotted against normalized track position (FR-004). The user initially stated "no new backend endpoints needed," but research reveals the existing API does not expose raw per-position telemetry data.

### Findings

**What the existing API provides:**

| Endpoint | Returns | Raw Traces? |
|----------|---------|-------------|
| `GET /sessions/{id}/laps` | LapSummary (lap_time, peak_g, throttle_pct, etc.) | No — aggregated only |
| `GET /sessions/{id}/laps/{n}` | LapDetailResponse (full LapMetrics) | No — aggregated only |
| `GET /sessions/{id}/corners` | AggregatedCorner (avg speeds, understeer ratio) | No |
| `GET /sessions/{id}/corners/{n}` | CornerLapEntry (per-lap corner metrics) | No |
| `GET /sessions/{id}/stints` | StintMetrics (means, trends) | No |
| `GET /sessions/{id}/consistency` | ConsistencyMetrics (stddev, variance) | No |

**Where the raw data lives:**

The processing pipeline (`api/analysis/pipeline.py`, line 44) saves the parsed session to disk via `parser.cache.save_session()`. This creates:

- `{sessions_dir}/{session_id}/{csv_base}/telemetry.parquet` — full per-sample time series with `lap_number` column
- `{sessions_dir}/{session_id}/{csv_base}/session.json` — metadata + lap/corner/setup structures

The Parquet file contains all channels per sample: `normalized_position`, `throttle`, `brake`, `steering`, `speed_kmh`, `gear`, `rpm`, `g_lat`, `g_lon`, tyre temps, pressures, etc. This is exactly what the frontend needs for trace charts.

### Proposed Solution

Add one new endpoint: `GET /sessions/{session_id}/laps/{lap_number}/telemetry`

- Reads from the already-cached `telemetry.parquet` file
- Filters to the requested lap number
- Returns only the 5 channels needed for traces: `normalized_position`, `throttle`, `brake`, `steering`, `speed_kmh`, `gear`
- Optionally downsamples to ~500 points per lap to keep payload size manageable (a 2-minute lap at 20Hz = ~2400 samples; downsampled to 500 keeps visual fidelity while reducing transfer size)
- Response shape: `{ session_id, lap_number, sample_count, channels: { normalized_position: [...], throttle: [...], brake: [...], steering: [...], speed_kmh: [...], gear: [...] } }`

### Rationale

- The data already exists on disk (Parquet cache). No new computation needed.
- The endpoint is thin: read Parquet, filter by lap, select columns, return JSON. This follows Constitution Principle VIII (thin API wrappers).
- Without this endpoint, the spec's core requirement (FR-004: telemetry traces vs track position) cannot be fulfilled.
- The alternative — having the frontend fetch the raw Parquet file — violates Constitution Principle VII (communicate via HTTP API only) and Principle IX (frontend must not access data files directly).

### Alternatives Considered

1. **Embed traces in LapDetailResponse**: Rejected — would bloat the existing endpoint for consumers that only need aggregated metrics.
2. **Frontend reads Parquet directly**: Rejected — violates Constitution Principles VII and IX.
3. **Return all channels**: Rejected — only 5 channels are needed for the view; sending all ~30+ channels wastes bandwidth.

---

## R2: Recharts Integration for Synchronized Multi-Channel Charts

### Decision: Use Recharts LineChart with `syncId` for cross-channel synchronized crosshair

### Findings

- Recharts is already installed in the project (confirmed in package.json).
- Recharts `syncId` prop on `<LineChart>` synchronizes tooltip/crosshair across multiple charts sharing the same `syncId` value. This is exactly the pattern needed: 5 sub-charts (one per channel) with synchronized hover position.
- Each sub-chart is a `<LineChart>` with:
  - X-axis: `normalized_position` (0–1, displayed as 0–100%)
  - Y-axis: channel value (throttle 0–1, brake 0–1, steering, speed_kmh, gear)
  - For two-lap comparison: two `<Line>` elements per chart — primary (solid) and secondary (dashed, `strokeDasharray="5 5"`)
- Recharts `<Tooltip>` can be customized to show both laps' values.

### Rationale

- Built-in `syncId` eliminates custom crosshair synchronization code.
- Recharts is already a project dependency — no new libraries needed.
- LineChart with discrete data points (position-indexed) works well for telemetry.

---

## R3: Existing Frontend Patterns

### Decision: Follow Sessions View patterns for hooks, state management, and styling

### Findings

**View creation pattern:**
- Views live in `frontend/src/views/{name}/index.tsx` with optional sub-components
- CSS uses `ace-` prefix with BEM naming, no CSS Modules, no Tailwind
- All colors from `tokens.css` custom properties
- Numeric data uses JetBrains Mono font (Constitution Principle XII)

**State management:**
- Selected session: `useSessionStore((s) => s.selectedSessionId)` from Zustand
- Selected laps: local `useState` in the view (user requirement — max 2 laps, not Zustand)
- API data: TanStack Query with `staleTime: Infinity` for immutable analysis data (Constitution Principle XII)

**Data fetching pattern:**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["laps", sessionId],
  queryFn: () => apiGet<LapListResponse>(`/sessions/${sessionId}/laps`),
  enabled: !!sessionId,
  staleTime: Infinity,  // immutable analysis data
});
```

**Design system components available:**
Button, Card, Badge, DataCell, ProgressBar, Tooltip, Skeleton, EmptyState, Toast, Modal

**Navigation:** Already wired — `analysis` section in Sidebar with `requiresSession: true`. AppShell maps to AnalysisView (currently a placeholder).

---

## R4: Corner Data Availability

### Decision: Use existing `GET /sessions/{id}/corners/{corner_number}` endpoint for per-lap corner metrics

### Findings

The corner detail endpoint returns per-lap corner metrics including:
- `entry_speed_kmh`, `apex_speed_kmh`, `exit_speed_kmh` (CornerPerformance)
- `understeer_ratio` (CornerGrip — float or null)
- `brake_point_norm`, `throttle_on_norm`, `trail_braking_intensity` (CornerTechnique)

However, this endpoint returns data for ONE corner across all laps. The view needs all corners for one (or two) laps.

**Two options:**
1. Fetch all corners aggregated (`GET /corners`), then for each selected lap, fetch corner detail per corner number. This requires N+1 requests.
2. Use the already-loaded `AnalyzedLap.corners` from the lap detail. But `LapDetailResponse` doesn't include corners — it only has `LapMetrics`.

**Proposed approach:** The `AnalyzedSession` cached data includes `AnalyzedLap.corners: list[CornerMetrics]`. A simple extension to the existing `LapDetailResponse` could add the corners list. Alternatively, a dedicated query combining corner data per lap avoids modifying existing contracts.

**Simplest solution:** Extend `LapDetailResponse` to include `corners: list[CornerMetrics]` — this is a backwards-compatible addition (new optional field). The serializer already has access to `AnalyzedLap.corners`.

### Rationale

- Avoids N+1 API calls per lap selection
- Backwards-compatible (additive field)
- Data already exists in the cached AnalyzedSession

---

## R5: Sector Times Availability

### Decision: Sector times come from `LapMetrics.timing.sector_times_s`

### Findings

- `TimingMetrics.sector_times_s: list[float] | None` — 3 equal-thirds sectors, or None
- Already included in `LapDetailResponse.metrics.timing.sector_times_s`
- No additional endpoint needed
- Session-best sectors must be computed client-side by comparing across all laps (or pre-computed in the lap list)

### Rationale

Sector data is already available in the existing lap detail endpoint. Best-in-session computation is trivial client-side (min across laps per sector index).

---

## R6: LapSummary Missing Fields

### Decision: Extend LapSummary with `max_speed` and `avg_speed` fields

### Findings

The current `LapSummary` model includes: `lap_number`, `classification`, `is_invalid`, `lap_time_s`, `tyre_temps_avg`, `peak_lat_g`, `peak_lon_g`, `full_throttle_pct`, `braking_pct`.

The spec requires the lap list to show: lap time, **peak speed**, **average throttle percentage**, and tyre temperatures. The summary already has `full_throttle_pct` (close to average throttle %) and `tyre_temps_avg`. But **peak speed** (`max_speed`) is missing from LapSummary — it exists in `LapMetrics.speed.max_speed`.

### Proposed Solution

Add `max_speed: float` to `LapSummary`. This is a backwards-compatible additive change. The serializer (`summarize_lap`) already has access to `LapMetrics.speed.max_speed`.

---

## Summary of Required Backend Changes

| Change | Type | Justification |
|--------|------|--------------|
| New endpoint `GET /sessions/{id}/laps/{n}/telemetry` | New endpoint | Raw trace data not exposed by any existing endpoint (FR-004) |
| Add `corners` field to `LapDetailResponse` | Additive field | Avoid N+1 corner queries per lap selection |
| Add `max_speed` field to `LapSummary` | Additive field | Spec requires peak speed in lap list |

All changes are backwards-compatible and follow Constitution Principle VIII (thin API wrappers over existing data).
