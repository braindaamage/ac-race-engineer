# Quickstart: Phase 7.4 — Lap Analysis View

**Branch**: `018-lap-analysis-view` | **Date**: 2026-03-06

## Prerequisites

- Node.js 20 LTS
- conda env `ac-race-engineer` (Python 3.11+)
- Backend running: `conda run -n ac-race-engineer python -m api.server --port 57832`

## Development

### Backend (new endpoint + model changes)

```bash
# Run backend tests
conda run -n ac-race-engineer pytest backend/tests/ -v

# Run only analysis-related tests
conda run -n ac-race-engineer pytest backend/tests/api/test_analysis.py -v
```

### Frontend

```bash
cd frontend

# Install dependencies (if needed)
npm install

# Dev server
npm run dev

# TypeScript check
npx tsc --noEmit

# Run all tests
npm run test

# Run analysis view tests only
npx vitest run tests/views/analysis/
```

## Key Files to Modify

### Backend
- `backend/api/analysis/models.py` — add `max_speed` to LapSummary, `corners` to LapDetailResponse, new LapTelemetryResponse
- `backend/api/analysis/serializers.py` — update `summarize_lap()`, add telemetry serializer
- `backend/api/routes/analysis.py` — add `GET /laps/{n}/telemetry` endpoint
- `backend/tests/api/test_analysis.py` — tests for new/changed endpoints

### Frontend
- `frontend/src/lib/types.ts` — add LapSummary, LapTelemetryResponse, LapDetailResponse, CornerMetrics types
- `frontend/src/hooks/useLaps.ts` — new TanStack Query hooks (useLaps, useLapDetail, useLapTelemetry)
- `frontend/src/views/analysis/index.tsx` — replace placeholder with full AnalysisView
- `frontend/src/views/analysis/LapList.tsx` — lap list sidebar component
- `frontend/src/views/analysis/TelemetryChart.tsx` — Recharts multi-channel trace chart
- `frontend/src/views/analysis/CornerTable.tsx` — corner data table
- `frontend/src/views/analysis/LapSummaryPanel.tsx` — metrics + sector times panel
- `frontend/src/views/analysis/AnalysisView.css` — view styles
- `frontend/tests/views/analysis/` — test files

## Architecture Notes

- Telemetry trace data is immutable — use `staleTime: Infinity` in TanStack Query
- Selected laps (max 2) are local `useState`, not Zustand
- Recharts `syncId` synchronizes crosshair across the 5 channel sub-charts
- Two-lap overlay: solid line for primary lap, dashed for secondary
- All colors from `tokens.css` — no hardcoded hex values
- Numeric data uses JetBrains Mono font
- All class names use `ace-` prefix with BEM pattern
