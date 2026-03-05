# Implementation Plan: Desktop App Scaffolding, Design System & Backend Integration

**Branch**: `015-desktop-scaffold` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/015-desktop-scaffold/spec.md`

## Summary

Phase 7.1 delivers the structural foundation for the AC Race Engineer desktop application. It scaffolds a Tauri v2 + React 18 + TypeScript project, implements a complete design system with two themes (Night Grid / Garage Floor) using CSS custom properties, builds 10 reusable UI components, creates the sidebar navigation shell with 5 sections, implements the backend sidecar lifecycle (launch, health poll, shutdown), integrates WebSocket job tracking with a toast notification system, and adds two small backend changes (`POST /shutdown` endpoint, `ui_theme` config field). All subsequent phases (7.2-7.6) build on this foundation.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode) + React 18 + Rust (Tauri shell only, minimal)
**Primary Dependencies**: Tauri v2, @tauri-apps/plugin-shell, TanStack Query v5, Zustand v5, Vite
**Storage**: In-memory only (TanStack Query cache + Zustand store); backend persists config via SQLite
**Testing**: Vitest + React Testing Library (frontend), pytest (backend changes)
**Target Platform**: Windows (native Tauri app)
**Project Type**: Desktop application (Tauri + React)
**Performance Goals**: Splash-to-main transition < 5s, instant theme switching, 60fps UI
**Constraints**: No localStorage/sessionStorage, no hardcoded colors, no CSS Modules/Tailwind, JetBrains Mono must be local asset, TypeScript strict with zero `any`
**Scale/Scope**: 10 UI components, 5 navigation views (empty states), 3 layout components, 3 custom hooks, 5 Zustand stores, ~45 source files, ~30-40 component tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | N/A | Phase 7.1 has no telemetry data handling |
| II. Car-Agnostic Design | N/A | No car-specific logic in frontend |
| III. Setup File Autonomy | N/A | No setup file access from frontend |
| IV. LLM as Interpreter | N/A | No LLM calls from frontend |
| V. Educational Explanations | N/A | No setup recommendations in this phase |
| VI. Incremental Changes | N/A | No setup modifications in this phase |
| VII. Desktop App as Primary Interface | PASS | Frontend communicates exclusively via localhost HTTP API; no analysis logic, no direct file access, no LLM calls |
| VIII. API-First Design | PASS | All data comes from backend API endpoints |
| IX. Separation of Concerns | PASS | Frontend layer: visualization and user interaction only; no business logic |
| X. Desktop App Stack | PASS | Tauri v2 shell (minimal Rust), React + TypeScript UI, sidecar on port 57832, health poll (30×500ms), splash screen, POST /shutdown on exit |
| XI. LLM Provider Abstraction | N/A | No LLM interaction in frontend |
| XII. Frontend Architecture Constraints | PASS | TanStack Query v5 for server state, Zustand v5 for UI state, CSS custom properties only, JetBrains Mono for numerics, no localStorage, TypeScript strict, component reuse mandate |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/015-desktop-scaffold/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-integration.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend changes (small — 2 additions)
backend/
├── ac_engineer/
│   └── config/
│       └── models.py            # Add ui_theme field to ACConfig
├── api/
│   └── routes/
│       ├── config.py            # Add ui_theme to request/response models
│       └── health.py            # Add POST /shutdown endpoint
└── tests/
    ├── config/                  # Tests for ui_theme field
    └── api/
        └── test_health.py       # Tests for shutdown endpoint
        └── test_config.py       # Tests for ui_theme in config API

# Frontend (new — Tauri v2 + React scaffold)
frontend/
├── src/
│   ├── assets/
│   │   └── fonts/               # JetBrains Mono .woff2 files
│   ├── components/
│   │   ├── ui/                  # 10 design system components
│   │   │   ├── Button.tsx + Button.css
│   │   │   ├── Card.tsx + Card.css
│   │   │   ├── Badge.tsx + Badge.css
│   │   │   ├── DataCell.tsx + DataCell.css
│   │   │   ├── ProgressBar.tsx + ProgressBar.css
│   │   │   ├── Tooltip.tsx + Tooltip.css
│   │   │   ├── Skeleton.tsx + Skeleton.css
│   │   │   ├── EmptyState.tsx + EmptyState.css
│   │   │   ├── Toast.tsx + Toast.css
│   │   │   ├── Modal.tsx + Modal.css
│   │   │   └── index.ts         # Barrel export
│   │   └── layout/              # 3 layout components
│   │       ├── AppShell.tsx + AppShell.css
│   │       ├── Sidebar.tsx + Sidebar.css
│   │       └── SplashScreen.tsx + SplashScreen.css
│   ├── hooks/                   # 3 custom hooks
│   │   ├── useBackendStatus.ts
│   │   ├── useJobProgress.ts
│   │   └── useTheme.ts
│   ├── store/
│   │   ├── uiStore.ts           # Zustand: activeSection, sidebar state
│   │   ├── sessionStore.ts      # Zustand: selectedSessionId
│   │   ├── themeStore.ts        # Zustand: theme ID, setTheme
│   │   ├── notificationStore.ts # Zustand: notifications[], add/remove
│   │   └── jobStore.ts          # Zustand: jobProgress{}, tracking
│   ├── lib/
│   │   ├── api.ts               # HTTP fetch wrapper for backend API
│   │   └── constants.ts         # API_BASE_URL, WS_BASE_URL, timing constants
│   ├── views/                   # 5 section views (empty states)
│   │   ├── sessions/index.tsx
│   │   ├── analysis/index.tsx
│   │   ├── compare/index.tsx
│   │   ├── engineer/index.tsx
│   │   └── settings/index.tsx
│   ├── tokens.css               # Design tokens (Night Grid + Garage Floor)
│   ├── index.css                # Global styles + @font-face
│   ├── App.tsx                  # Root: splash → app shell routing
│   └── main.tsx                 # Entry point: QueryClientProvider + React root
├── src-tauri/
│   ├── src/lib.rs               # Tauri app builder (minimal Rust)
│   ├── capabilities/default.json # Shell plugin permissions
│   ├── tauri.conf.json          # App metadata, window config, bundle
│   └── Cargo.toml               # Rust deps: tauri + tauri-plugin-shell
├── tests/
│   ├── setup.ts                 # Test utilities (theme wrapper, providers)
│   └── components/ui/           # Component unit tests (10 files)
├── package.json
├── vite.config.ts
├── tsconfig.json
└── vitest.config.ts
```

**Structure Decision**: The frontend follows the directory structure specified in the user input. The backend receives two small additions (shutdown endpoint + ui_theme config field) without structural changes.

## Complexity Tracking

No constitution violations to justify. All design choices align with Principles VII, VIII, IX, X, XII.

## Design Decisions

### D1: Sidecar Management — Development vs Production

**Development mode** (`npm run tauri dev`): The sidecar is launched via `@tauri-apps/plugin-shell` using a configured scope that allows running `python -m api.server --port 57832`. During pure UI development (`npm run dev`), the backend must be started manually.

**Production mode** (`npm run tauri build`): The backend is pre-packaged as a standalone executable via PyInstaller (`api-server.exe`), declared in `tauri.conf.json` under `bundle.externalBin`, and spawned as a true sidecar.

### D2: Theme Application Flow

1. App starts → splash screen renders with dark theme (hardcoded default)
2. Backend becomes ready → `GET /config` fetches `ui_theme`
3. Theme is applied to `document.documentElement.dataset.theme`
4. Main UI renders with correct theme
5. User switches theme → immediate CSS update + `PATCH /config { ui_theme }` (fire-and-forget)

### D3: Notification Lifecycle

1. Notification created → added to Zustand `notifications[]` with unique ID
2. Rendered by `Toast` component in fixed bottom-right container
3. Non-error types: `setTimeout(5000)` triggers removal from store
4. Error types: remain until user clicks dismiss (removes from store)
5. New notifications stack below existing ones (newest at bottom)

### D4: WebSocket Job Integration

1. When a job is started (in later phases), `useJobProgress(jobId)` opens a WebSocket
2. Each `progress` message updates `Zustand.jobProgress[jobId]`
3. On `completed` event: `addNotification("success", ...)` + close WebSocket
4. On `error` event: `addNotification("error", ...)` + close WebSocket
5. On unexpected disconnect: exponential backoff reconnect (1s, 2s, 4s, max 3 retries)
6. After 3 failed retries: `addNotification("error", "Live updates unavailable")`

### D5: Component Styling Strategy

- Each component has a co-located `.css` file (e.g., `Button.css`)
- CSS classes use a `ace-` prefix to avoid collisions (e.g., `.ace-button`, `.ace-card--ai`)
- All colors/spacing/fonts reference CSS custom properties from `tokens.css`
- No CSS Modules, no Tailwind, no CSS-in-JS
- Global reset and base styles in `index.css`

### D6: Backend Changes Scope

Two minimal backend additions, both backward-compatible:

1. **`POST /shutdown`**: Added to health router. Sets a flag that triggers graceful Uvicorn shutdown. Returns `{"status": "shutting_down"}` immediately.

2. **`ui_theme` in ACConfig**: New string field with default `"dark"`, validator for `"dark"|"light"`, added to serializer, ConfigResponse, and ConfigUpdateRequest. Existing config.json files without `ui_theme` get the default on read.
