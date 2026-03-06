# Implementation Plan: Sessions List & Processing View

**Branch**: `017-sessions-view` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-sessions-view/spec.md`

## Summary

Phase 7.3 builds the Sessions view — the central hub of the desktop app. The frontend fetches and displays all recorded sessions from the existing backend API, enables processing (parse + analyze) with real-time progress via WebSocket, allows session selection to unlock other views, and supports deletion. No backend changes are needed — all endpoints exist from Phase 6. The frontend adds a TanStack Query hook with 5-second polling, a session card component, processing job tracking via existing JobWSManager, a delete flow with the existing Modal, and a selected session strip in the AppShell.

## Technical Context

**Language/Version**: TypeScript 5.7+ strict (frontend only)
**Primary Dependencies**: React 18, TanStack Query v5, Zustand v5, Vitest, React Testing Library
**Storage**: N/A (backend handles all persistence)
**Testing**: Vitest + React Testing Library
**Target Platform**: Windows 11 desktop (Tauri app)
**Project Type**: Desktop app (frontend changes only)
**Performance Goals**: Session list renders within 2 seconds, progress updates at least 1/second
**Constraints**: TypeScript strict, no localStorage, all colors via design tokens, `ace-` CSS prefix
**Scale/Scope**: 1 view (replaced), 1 new component, 1 new hook, 1 new types file, 2 modified files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | No telemetry data manipulation |
| II. Car-Agnostic Design | PASS | Session list shows any car — no car-specific logic |
| III. Setup File Autonomy | N/A | No setup file I/O |
| IV. LLM as Interpreter | N/A | No LLM interaction |
| V. Educational Explanations | N/A | No setup recommendations |
| VI. Incremental Changes | N/A | No setup modifications |
| VII. Desktop App as Primary Interface | PASS | Sessions view is the central hub — frontend only, all data from API |
| VIII. API-First Design | PASS | All data fetched via existing REST endpoints; no direct DB/file access |
| IX. Separation of Concerns | PASS | Frontend renders data from API; processing delegated to backend jobs |
| X. Desktop App Stack | PASS | React UI, TanStack Query, Zustand stores — all within existing stack |
| XI. LLM Provider Abstraction | N/A | No LLM interaction |
| XII. Frontend Architecture Constraints | PASS | Server state via TanStack Query, global selection via Zustand, local processing state via useState; design system components reused; no localStorage; TypeScript strict; colors via tokens |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/017-sessions-view/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Research findings
├── data-model.md        # Data model (frontend types)
├── quickstart.md        # Dev quickstart
├── contracts/
│   └── frontend-components.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── lib/
│   │   ├── api.ts              # MODIFY: add apiDelete function
│   │   └── types.ts            # NEW: SessionRecord, ProcessResponse, SyncResult, UISessionState types
│   ├── hooks/
│   │   └── useSessions.ts      # NEW: TanStack Query hook for GET /sessions with 5s refetch
│   ├── views/
│   │   └── sessions/
│   │       ├── index.tsx        # REPLACE: full sessions list view
│   │       ├── SessionCard.tsx  # NEW: individual session card component
│   │       └── SessionsView.css # NEW: sessions view styles
│   └── components/
│       └── layout/
│           ├── AppShell.tsx     # MODIFY: add selected session strip
│           └── AppShell.css     # MODIFY: add strip styles
└── tests/
    ├── views/
    │   ├── SessionsView.test.tsx  # NEW: sessions view tests
    │   └── SessionCard.test.tsx   # NEW: session card tests
    └── hooks/
        └── useSessions.test.tsx   # NEW: sessions hook tests
```

**Structure Decision**: Extends existing frontend structure. SessionCard is a new component inside `views/sessions/` (co-located with the view, not in `components/ui/` since it's session-specific). Types go in `lib/types.ts` as a shared types file. The selected session strip is simple enough to be inline in AppShell.tsx.

## Complexity Tracking

> No violations — table not needed.
