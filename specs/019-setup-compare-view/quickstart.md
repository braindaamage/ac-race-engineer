# Quickstart: Setup Compare View

**Feature**: 019-setup-compare-view
**Date**: 2026-03-06

## Prerequisites

- Node.js 20 LTS
- Backend running at `http://127.0.0.1:57832` (or use mock data for frontend-only dev)
- An analyzed session with 2+ stints in the database

## Development

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd frontend
npm run test                        # Run all tests
npx vitest run tests/views/compare  # Run only compare view tests
npx tsc --noEmit                    # TypeScript strict check
```

## Key Files

| File | Purpose |
|------|---------|
| `src/hooks/useStints.ts` | TanStack Query hooks for stints and comparison |
| `src/lib/types.ts` | TypeScript interfaces for stint/comparison data |
| `src/views/compare/index.tsx` | Main CompareView component (replaces placeholder) |
| `src/views/compare/StintSelector.tsx` | Stint list with two-selection mechanism |
| `src/views/compare/SetupDiff.tsx` | Grouped parameter diff display |
| `src/views/compare/MetricsPanel.tsx` | Performance metric deltas |
| `src/views/compare/CompareView.css` | View-specific styles |
| `src/views/compare/utils.ts` | Formatting helpers (delta sign, direction indicators) |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /sessions/{id}/stints` | Fetch all stints for a session |
| `GET /sessions/{id}/compare?stint_a=X&stint_b=Y` | Fetch setup diff and metric deltas |

## Architecture Notes

- **No new backend code** — all endpoints exist from Phase 6
- **State layers**: Zustand (selected session) → TanStack Query (stints + comparison) → useState (stint pair selection)
- **Immutable data**: Both hooks use `staleTime: Infinity` since analysis data never changes
- **CSS**: All classes use `ace-` prefix, colors via design tokens only, JetBrains Mono for all numeric values
