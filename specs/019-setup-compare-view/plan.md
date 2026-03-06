# Implementation Plan: Setup Compare View

**Branch**: `019-setup-compare-view` | **Date**: 2026-03-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-setup-compare-view/spec.md`

## Summary

Build the Setup Compare view (Phase 7.5) for the Tauri + React desktop app. The view lets drivers select two stints from an analyzed session and see a side-by-side comparison of setup parameter differences (organized by INI section) alongside performance metric deltas. No new backend endpoints are needed — the existing `GET /sessions/{id}/stints` and `GET /sessions/{id}/compare?stint_a=X&stint_b=Y` endpoints provide all required data.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode) + React 18
**Primary Dependencies**: React 18, TanStack Query v5 (server state), Zustand v5 (UI state), Vite (bundler)
**Storage**: N/A (all data fetched from backend API, no browser storage per constitution)
**Testing**: Vitest + React Testing Library
**Target Platform**: Windows desktop (Tauri v2 shell)
**Project Type**: Desktop app (frontend view within existing Tauri + React application)
**Performance Goals**: Stint list renders in <1s, comparison results display in <2s after selection
**Constraints**: No hardcoded CSS colors (design tokens only), no explicit `any`, JetBrains Mono for all numeric data, `ace-` CSS class prefix
**Scale/Scope**: 1 view (CompareView), 2 data hooks, ~5 presentational components, ~5 test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| II. Car-Agnostic Design | PASS | No hardcoded car names or parameters; section names and parameter names come from API data |
| VII. Desktop App as Primary Interface | PASS | All data comes from localhost HTTP API; no local analysis logic |
| IX. Separation of Concerns | PASS | Frontend does visualization only; no business logic, no direct file I/O |
| X. Desktop App Stack | PASS | Uses Tauri + React + TypeScript; communicates via localhost HTTP |
| XII. Frontend Architecture Constraints | PASS | TanStack Query for server state (staleTime: Infinity for immutable data), Zustand for UI state (selected session), useState for local state (stint selection). Design tokens for colors, JetBrains Mono for numerics, no browser storage, no explicit any |

No violations. Complexity Tracking section not needed.

## Project Structure

### Documentation (this feature)

```text
specs/019-setup-compare-view/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── hooks/
│   │   └── useStints.ts             # NEW — useStints + useStintComparison hooks
│   ├── lib/
│   │   └── types.ts                 # MODIFIED — add stint/comparison TypeScript types
│   └── views/
│       └── compare/
│           ├── index.tsx             # MODIFIED — replace placeholder with CompareView
│           ├── StintSelector.tsx     # NEW — stint list with two-selection mechanism
│           ├── SetupDiff.tsx         # NEW — grouped parameter diff display
│           ├── MetricsPanel.tsx      # NEW — performance metric deltas
│           ├── CompareView.css       # NEW — view-specific styles
│           └── utils.ts             # NEW — formatting helpers (delta sign, direction)
└── tests/
    └── views/
        └── compare/
            ├── CompareView.test.tsx       # NEW — integration test for full view
            ├── StintSelector.test.tsx      # NEW — stint selection behavior
            ├── SetupDiff.test.tsx          # NEW — diff rendering, toggle, edge cases
            ├── MetricsPanel.test.tsx       # NEW — delta display, null handling
            └── utils.test.ts              # NEW — formatting utility tests
```

**Structure Decision**: Frontend-only feature following the established pattern from Phase 7.4 (AnalysisView). New files live in `frontend/src/views/compare/` with hooks in `frontend/src/hooks/` and tests in `frontend/tests/views/compare/`.
