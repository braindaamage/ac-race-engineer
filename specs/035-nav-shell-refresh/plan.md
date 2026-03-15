# Implementation Plan: Navigation Shell & Visual Refresh

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/035-nav-shell-refresh/spec.md`

## Summary

Replace the flat sidebar-based navigation with a hierarchical car-centric flow powered by react-router-dom v7. Introduce a fixed header with dynamic breadcrumb and contextual tab bar. Update the design system tokens to a new brand palette, replace emoji icons with Font Awesome, and regenerate Tauri desktop icons from the new logo. Session identity migrates from Zustand store to URL route parameters. Existing views (Analysis, Compare, Engineer, Settings) are preserved unchanged inside the new layout shell. Garage Home and Car Tracks views are placeholder skeletons for Phase 14.2.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode) + React 18.3 + Rust (Tauri shell, minimal)
**Primary Dependencies**: react-router-dom v7, @fortawesome/fontawesome-free, TanStack Query v5, Zustand v5, Recharts v3
**Storage**: N/A (no backend changes; existing SQLite + config.json untouched)
**Testing**: Vitest 3.0 + @testing-library/react 16.0 (48 test files, ~394 tests)
**Target Platform**: Windows 11 desktop (Tauri v2)
**Project Type**: Desktop app (Tauri + React frontend)
**Performance Goals**: Instant route transitions (<100ms perceived), no layout shift during navigation
**Constraints**: Min viewport 1024px, no localStorage/sessionStorage, all colors via CSS tokens, TypeScript strict with no untyped any
**Scale/Scope**: 9 routes, 7 views (2 new placeholders + 5 existing), ~50 component files affected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | No telemetry/analysis changes |
| II. Car-Agnostic Design | PASS | Route params use raw car/track identifiers from API, no hardcoded car names |
| III. Setup File Autonomy | N/A | No setup file changes |
| IV. LLM as Interpreter | N/A | No LLM changes |
| V. Educational Explanations | N/A | No explanation changes |
| VI. Incremental Changes | N/A | No setup recommendation changes |
| VII. Desktop App as Primary Interface | PASS | Frontend communicates with backend exclusively via localhost HTTP API |
| VIII. API-First Design | N/A | No backend changes |
| IX. Separation of Concerns | PASS | Frontend remains visualization-only; no analysis logic, no LLM calls, no direct file access |
| X. Desktop App Stack | PASS | Tauri shell remains minimal config; React + TS for UI; backend launched as sidecar on port 57832 |
| XI. LLM Provider Abstraction | N/A | No LLM changes |
| XII. Frontend Architecture | PASS | TanStack Query for server state, Zustand for UI state (reduced), design tokens as sole color source, JetBrains Mono for numeric data, no localStorage, TypeScript strict, component reuse |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/035-nav-shell-refresh/
├── plan.md              # This file
├── research.md          # Phase 0: routing, token, and migration research
├── data-model.md        # Phase 1: route/entity model
├── quickstart.md        # Phase 1: developer quick start
├── contracts/           # Phase 1: UI contracts (route map, token contract)
│   ├── routes.md
│   └── tokens.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── assets/
│   │   └── logo.png                          # NEW — brand logo image
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx                   # REWRITE — header + Outlet + toast
│   │   │   ├── AppShell.css                   # REWRITE — new layout styles
│   │   │   ├── Header.tsx                     # NEW — logo + breadcrumb + settings icon
│   │   │   ├── Header.css                     # NEW
│   │   │   ├── Breadcrumb.tsx                 # NEW — dynamic breadcrumb from route
│   │   │   ├── Breadcrumb.css                 # NEW
│   │   │   ├── TabBar.tsx                     # NEW — contextual tab bar
│   │   │   ├── TabBar.css                     # NEW
│   │   │   ├── SessionLayout.tsx              # NEW — session detail layout (tabs + Outlet)
│   │   │   ├── SessionLayout.css              # NEW
│   │   │   ├── Sidebar.tsx                    # DELETE
│   │   │   ├── Sidebar.css                    # DELETE
│   │   │   ├── SplashScreen.tsx               # MODIFY — new logo + brand colors
│   │   │   ├── SplashScreen.css               # MODIFY — updated styles
│   │   │   └── ToastContainer.tsx             # UNCHANGED
│   │   ├── onboarding/
│   │   │   ├── OnboardingWizard.tsx           # MINOR — remove sidebar dependency
│   │   │   └── OnboardingWizard.css           # MODIFY — fix undefined tokens
│   │   └── ui/                                # UNCHANGED (all 10 components)
│   ├── router.tsx                             # NEW — route definitions + createBrowserRouter
│   ├── store/
│   │   ├── uiStore.ts                         # DELETE
│   │   ├── sessionStore.ts                    # DELETE
│   │   ├── themeStore.ts                      # UNCHANGED
│   │   ├── notificationStore.ts               # UNCHANGED
│   │   └── jobStore.ts                        # UNCHANGED
│   ├── views/
│   │   ├── garage/
│   │   │   ├── index.tsx                      # NEW — placeholder Garage Home
│   │   │   └── GarageView.css                 # NEW
│   │   ├── tracks/
│   │   │   ├── index.tsx                      # NEW — placeholder Car Tracks
│   │   │   └── CarTracksView.css              # NEW
│   │   ├── sessions/
│   │   │   ├── index.tsx                      # MODIFY — receive carId+trackId from route params
│   │   │   └── SessionsView.css               # MODIFY — fix undefined tokens
│   │   ├── analysis/
│   │   │   ├── index.tsx                      # MODIFY — get sessionId from useParams
│   │   │   └── AnalysisView.css               # MODIFY — fix undefined tokens
│   │   ├── compare/
│   │   │   ├── index.tsx                      # MODIFY — get sessionId from useParams
│   │   │   └── CompareView.css                # MODIFY — fix undefined tokens
│   │   ├── engineer/
│   │   │   └── index.tsx                      # MODIFY — get sessionId from useParams
│   │   └── settings/
│   │       ├── index.tsx                      # MODIFY — remove uiStore navigation interception
│   │       └── Settings.css                   # MODIFY — fix undefined tokens
│   ├── tokens.css                             # MODIFY — new palette values + missing token defs
│   ├── App.tsx                                # MODIFY — integrate RouterProvider
│   └── main.tsx                               # MINOR — may need router setup
├── src-tauri/
│   ├── icons/                                 # REGENERATE — from new logo
│   └── tauri.conf.json                        # MODIFY — icon paths if changed
└── tests/
    ├── components/layout/
    │   ├── AppShell.test.tsx                   # REWRITE — test new layout
    │   ├── Sidebar.test.tsx                    # DELETE
    │   ├── Header.test.tsx                     # NEW
    │   ├── Breadcrumb.test.tsx                 # NEW
    │   ├── TabBar.test.tsx                     # NEW
    │   ├── SessionLayout.test.tsx              # NEW
    │   └── SplashScreen.test.tsx               # MODIFY — test new logo
    ├── router.test.tsx                         # NEW — route rendering + navigation
    ├── views/
    │   ├── sessions/SessionsView.test.tsx      # MODIFY — route params instead of store
    │   ├── analysis/AnalysisView.test.tsx       # MODIFY — route params instead of store
    │   ├── compare/CompareView.test.tsx         # MODIFY — route params instead of store
    │   ├── engineer/EngineerView.test.tsx       # MODIFY — route params instead of store
    │   └── settings/SettingsView.test.tsx       # MODIFY — remove uiStore mocks
    └── App.test.tsx                            # MODIFY — integrate router
```

**Structure Decision**: This is a frontend-only change within the existing `frontend/` directory. No backend files are created or modified. The existing directory structure is preserved; new files are added under existing conventions (`components/layout/`, `views/`, `tests/`). A new `router.tsx` file at `src/` root defines all route configuration.

## Complexity Tracking

> No constitution violations. No entries needed.
