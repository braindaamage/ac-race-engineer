# Implementation Plan: Usage UI

**Branch**: `025-usage-ui` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-usage-ui/spec.md`

## Summary

Add token usage visibility to the existing RecommendationCard component in the frontend. Two UI elements: (1) an inline summary bar at the bottom of each recommendation card showing agent count, input/output tokens, tool calls, and a details button; (2) a modal with per-agent breakdown including domain, tokens, turns, duration, and tool call details. A new `useRecommendationUsage` hook fetches immutable usage data from the existing backend endpoint. A pure `formatTokenCount` utility handles compact number formatting (K/M suffixes). Frontend-only changes — no backend modifications.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode) with React 18
**Primary Dependencies**: React 18, TanStack Query v5, Zustand v5
**Storage**: N/A (data fetched from backend API, cached in TanStack Query with staleTime: Infinity)
**Testing**: Vitest + Testing Library (tests in `frontend/tests/`, mirroring `frontend/src/`)
**Target Platform**: Windows desktop via Tauri v2
**Project Type**: Desktop app (frontend layer only for this feature)
**Performance Goals**: N/A (static display of small data payloads)
**Constraints**: No hardcoded colors (design tokens only), no CSS Modules/Tailwind, `ace-` prefix on all CSS classes, JetBrains Mono for numeric data, no explicit `any`
**Scale/Scope**: 2 new components, 1 new hook, 1 utility function, ~4 modified files, ~6 new/modified test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | No telemetry processing — display only |
| II. Car-Agnostic Design | N/A | No car-specific logic |
| III. Setup File Autonomy | N/A | No setup file access |
| IV. LLM as Interpreter | N/A | No LLM interaction |
| V. Educational Explanations | N/A | No setup change explanations |
| VI. Incremental Changes | N/A | No setup modifications |
| VII. Desktop App as Primary Interface | PASS | Frontend communicates via API only; no local file access or analysis logic |
| VIII. API-First Design | PASS | Usage data fetched from existing backend endpoint; no logic duplication |
| IX. Separation of Concerns | PASS | Frontend layer only — visualization of API data |
| X. Desktop App Stack | PASS | React + TypeScript in `frontend/src/`, no Rust changes |
| XI. LLM Provider Abstraction | N/A | No LLM calls |
| XII. Frontend Architecture Constraints | PASS | TanStack Query for server state, design tokens for colors, JetBrains Mono for numbers, no localStorage, TypeScript strict, reuses Modal from design system |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/025-usage-ui/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── lib/
│   │   ├── types.ts              # MODIFY — add usage type definitions
│   │   └── format.ts             # NEW — formatTokenCount utility
│   ├── hooks/
│   │   └── useRecommendations.ts # MODIFY — add useRecommendationUsage hook
│   └── views/engineer/
│       ├── index.tsx             # MODIFY — wire usage data into RecommendationCard
│       ├── RecommendationCard.tsx # MODIFY — add UsageSummaryBar render
│       ├── UsageSummaryBar.tsx   # NEW — inline summary bar component
│       ├── UsageDetailModal.tsx  # NEW — detail modal component
│       └── EngineerView.css     # MODIFY — add usage summary + modal styles
└── tests/
    ├── lib/
    │   └── format.test.ts        # NEW — formatTokenCount unit tests
    ├── hooks/
    │   └── useRecommendationUsage.test.ts  # NEW — hook tests
    └── views/engineer/
        ├── UsageSummaryBar.test.tsx   # NEW — summary bar tests
        └── UsageDetailModal.test.tsx  # NEW — detail modal tests
```

**Structure Decision**: Frontend-only feature. All new files live within the existing `frontend/src/views/engineer/` directory (components), `frontend/src/lib/` (utility), and `frontend/src/hooks/` (hook). Tests mirror the source structure in `frontend/tests/`. No new directories needed — the pattern follows existing conventions exactly.

## Complexity Tracking

> No constitution violations — this section is intentionally empty.
