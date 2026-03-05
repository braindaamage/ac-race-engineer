# Tasks: Desktop App Scaffolding, Design System & Backend Integration

**Input**: Design documents from `/specs/015-desktop-scaffold/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — spec mandates "All 10 design system components must have tests covering every documented variant and both themes." Backend changes also require pytest tests.

**Organization**: Tasks are grouped by user story. US2 (theming) and US5 (component library) are placed before US1/US3 because the startup flow and sidebar depend on tokens and components being available.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Scaffold)

**Purpose**: Initialize the Tauri v2 + React + TypeScript project structure

- [ ] T001 Initialize React + TypeScript + Vite project in `frontend/` — create `package.json`, `tsconfig.json`, `vite.config.ts` with strict mode enabled, Tauri-specific Vite settings (`server.port: 5173`, `server.strictPort: true`, `server.host: process.env.TAURI_DEV_HOST`, build target `chrome105`, exclude `src-tauri/**`)
- [ ] T002 Initialize Tauri v2 shell in `frontend/src-tauri/` — run `cargo tauri init`, configure `tauri.conf.json` (app name "AC Race Engineer", window title, default size 1280x720, `build.beforeDevCommand`, `build.devUrl`, `build.frontendDist`), set up `Cargo.toml` with tauri + tauri-plugin-shell dependencies
- [ ] T003 Install frontend npm dependencies — `@tauri-apps/api`, `@tauri-apps/plugin-shell`, `@tanstack/react-query` v5, `zustand` v5, `react` 18, `react-dom` 18, and dev deps: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `typescript`, `@types/react`, `@types/react-dom`
- [ ] T004 Configure Vitest in `frontend/vitest.config.ts` — jsdom environment, setup files pointing to `tests/setup.ts`, coverage config, include `src/**/*.{test,spec}.{ts,tsx}` and `tests/**/*.{test,spec}.{ts,tsx}`
- [ ] T005 [P] Configure Tauri shell plugin permissions in `frontend/src-tauri/capabilities/default.json` — add `core:default`, `shell:allow-spawn` with sidecar scope for `binaries/api-server` with validated `--port` arg, `shell:allow-kill`
- [ ] T006 [P] Configure Tauri `lib.rs` in `frontend/src-tauri/src/lib.rs` — minimal Rust: register `tauri_plugin_shell::init()`, build and run app
- [ ] T007 [P] Download and place font files in `frontend/src/assets/fonts/` — JetBrains Mono Regular + Bold `.woff2`, Inter Regular + Medium + SemiBold + Bold `.woff2`
- [ ] T008 Create directory structure per plan — `frontend/src/components/ui/`, `frontend/src/components/layout/`, `frontend/src/hooks/`, `frontend/src/store/`, `frontend/src/lib/`, `frontend/src/views/{sessions,analysis,compare,engineer,settings}/`

**Checkpoint**: Project compiles with `npm run build` and `tsc --noEmit` passes with zero errors. Tauri compiles with `cargo build` in `src-tauri/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend changes + core frontend infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Changes

- [ ] T009 Add `ui_theme` field to ACConfig model in `backend/ac_engineer/config/models.py` — add `ui_theme: str = "dark"` field with validator restricting to `"dark"` | `"light"`, update `_serialize` method to include `ui_theme`
- [ ] T010 Update config API models in `backend/api/routes/config.py` — add `ui_theme: str` to `ConfigResponse`, add `ui_theme: str | None = None` to `ConfigUpdateRequest`, update `_config_to_response` helper
- [ ] T011 [P] Add `POST /shutdown` endpoint in `backend/api/routes/health.py` — accept POST, trigger graceful Uvicorn shutdown (set `server.should_exit = True` via app state or signal), return `{"status": "shutting_down"}` immediately
- [ ] T012 [P] Write pytest tests for `ui_theme` config field in `backend/tests/config/test_models_ui_theme.py` — test default value, valid values, invalid value rejection, serialization, round-trip read/write
- [ ] T013 [P] Write pytest tests for `ui_theme` in config API in `backend/tests/api/test_config_ui_theme.py` — test GET returns `ui_theme`, PATCH updates `ui_theme`, PATCH rejects invalid values
- [ ] T014 [P] Write pytest tests for shutdown endpoint in `backend/tests/api/test_shutdown.py` — test POST /shutdown returns 200, test GET /shutdown returns 405

### Frontend Core Infrastructure

- [ ] T015 Create constants in `frontend/src/lib/constants.ts` — `API_BASE_URL = 'http://127.0.0.1:57832'`, `WS_BASE_URL = 'ws://127.0.0.1:57832'`, `HEALTH_POLL_INTERVAL = 500`, `HEALTH_MAX_RETRIES = 30`, `NOTIFICATION_DURATION = 5000`, `WS_MAX_RETRIES = 3`, `WS_BASE_DELAY = 1000`
- [ ] T016 Create API client in `frontend/src/lib/api.ts` — typed fetch wrapper with `apiGet<T>(path)`, `apiPatch<T>(path, body)`, `apiPost<T>(path, body?)` functions that prepend `API_BASE_URL`, handle JSON serialization, and throw on non-OK responses
- [ ] T017 Create design tokens in `frontend/src/tokens.css` — three-layer architecture: primitive values (raw colors, spacing scale `--space-1` through `--space-12` on 4px base), `[data-theme="dark"]` semantic tokens (Night Grid: dark backgrounds, light text, red brand, cyan AI, green positive, amber warning), `[data-theme="light"]` semantic tokens (Garage Floor: light backgrounds, dark text, same semantic colors adjusted for contrast), typography tokens (`--font-ui`, `--font-mono`, `--font-size-*`, `--font-weight-*`, `--line-height-*`), radius (`--radius-sm/md/lg`), shadows (`--shadow-sm/md/lg`), transitions (`--transition-fast/normal`)
- [ ] T018 Create global styles in `frontend/src/index.css` — import `tokens.css`, `@font-face` declarations for JetBrains Mono and Inter referencing `./assets/fonts/`, CSS reset, base body styles using tokens, `.ace-mono` utility class for monospaced font
- [ ] T019 Create test setup in `frontend/tests/setup.ts` — import `@testing-library/jest-dom`, configure cleanup after each test, create `renderWithProviders` helper that wraps components in `QueryClientProvider` (fresh client per test with `retry: false`), set `document.documentElement.dataset.theme = 'dark'` as default

### Zustand Stores

- [ ] T020 [P] Create UI store in `frontend/src/store/uiStore.ts` — Zustand v5 store with `activeSection: string` (default `"sessions"`), `sidebarCollapsed: boolean` (default `false`), actions `setActiveSection(id: string)`, `toggleSidebar()`
- [ ] T021 [P] Create session store in `frontend/src/store/sessionStore.ts` — Zustand v5 store with `selectedSessionId: string | null` (default `null`), actions `selectSession(id: string)`, `clearSession()`
- [ ] T022 [P] Create theme store in `frontend/src/store/themeStore.ts` — Zustand v5 store with `theme: string` (default `"dark"`), action `setTheme(id: string)` that updates `document.documentElement.dataset.theme` and calls `apiPatch('/config', { ui_theme: id })` fire-and-forget
- [ ] T023 [P] Create notification store in `frontend/src/store/notificationStore.ts` — Zustand v5 store with `notifications: Notification[]` (typed with `id`, `type`, `message`, `createdAt`), actions `addNotification(type, message)` (generates unique id, auto-schedules removal for non-error types after `NOTIFICATION_DURATION`), `removeNotification(id)`
- [ ] T024 [P] Create job store in `frontend/src/store/jobStore.ts` — Zustand v5 store with `jobProgress: Record<string, JobProgress>` (typed with `jobId`, `status`, `progress`, `currentStep`, `result`, `error`), actions `updateJobProgress(jobId, update)`, `removeJob(jobId)`

**Checkpoint**: Backend tests pass (`pytest backend/tests/config/ backend/tests/api/test_config*.py backend/tests/api/test_shutdown.py -v`). Frontend compiles. Stores are importable. `tokens.css` defines both themes. All existing backend tests still pass.

---

## Phase 3: User Story 2 — Design System and Theming (Priority: P1)

**Goal**: Two themes (Night Grid / Garage Floor) switch instantly; preference persists via backend config.

**Independent Test**: Open the app, verify dark theme is default. Switch to light theme — all elements update. Restart — light theme persists.

### Implementation

- [ ] T025 [US2] Create `useTheme` hook in `frontend/src/hooks/useTheme.ts` — on mount, call `GET /config` via TanStack Query to fetch `ui_theme`, apply result to `themeStore.setTheme()`. Expose `theme` (from store), `toggleTheme()` (switches between "dark"/"light"), `isLoading` (from query). Handle failure gracefully: if config fetch fails, keep default "dark" theme
- [ ] T026 [US2] Create entry point in `frontend/src/main.tsx` — create `QueryClient` with sensible defaults (`staleTime: 60_000` for config, `retry: 1`), render `<QueryClientProvider>` wrapping `<App />`, mount to `#root`
- [ ] T027 [US2] Create root app component in `frontend/src/App.tsx` — use `useTheme` to initialize theme on mount, render a minimal shell (placeholder div) that applies the theme. This will be extended in US1 and US3.

**Checkpoint**: Running `npm run dev` shows a page. Changing `data-theme` attribute manually in dev tools switches all token values. `useTheme` hook fetches config and applies theme.

---

## Phase 4: User Story 5 — Reusable UI Component Library (Priority: P2)

**Goal**: All 10 design system components exist, render correctly in both themes, and are tested.

**Independent Test**: Import any component — verify it renders in both themes with all variants. Run `npm run test` — all component tests pass.

### Implementation

- [ ] T028 [P] [US5] Create Button component in `frontend/src/components/ui/Button.tsx` + `Button.css` — props: `variant` ("primary" | "secondary" | "ghost"), `size` ("sm" | "md" | "lg"), `disabled`, `onClick`, `children`, `type`. CSS classes: `.ace-button`, `.ace-button--primary` (red bg, white text), `.ace-button--secondary` (transparent, border), `.ace-button--ghost` (transparent, no border), size modifiers, hover/active/disabled states. All colors from tokens.
- [ ] T029 [P] [US5] Create Card component in `frontend/src/components/ui/Card.tsx` + `Card.css` — props: `variant` ("default" | "ai"), `children`, `title?`, `padding?` ("sm" | "md" | "lg"). CSS: `.ace-card` (surface bg, border, radius), `.ace-card--ai` (cyan/blue 3px left border accent). Title renders as heading inside card.
- [ ] T030 [P] [US5] Create Badge component in `frontend/src/components/ui/Badge.tsx` + `Badge.css` — props: `variant` ("info" | "success" | "warning" | "error" | "neutral"), `children`. CSS: `.ace-badge` with variant modifiers using semantic color tokens for background/text.
- [ ] T031 [P] [US5] Create DataCell component in `frontend/src/components/ui/DataCell.tsx` + `DataCell.css` — props: `value` (string | number), `delta?` (number), `unit?` (string), `align?` ("left" | "right"). Always renders value in `--font-mono` (JetBrains Mono). Delta coloring: positive → green, negative → amber, zero/undefined → neutral. Unit renders as muted suffix.
- [ ] T032 [P] [US5] Create ProgressBar component in `frontend/src/components/ui/ProgressBar.tsx` + `ProgressBar.css` — props: `value` (0-100), `variant?` ("default" | "success" | "error"). CSS: `.ace-progress` track with `.ace-progress__fill` animated width transition. Variant colors: default (red brand), success (green), error (red).
- [ ] T033 [P] [US5] Create Tooltip component in `frontend/src/components/ui/Tooltip.tsx` + `Tooltip.css` — props: `content` (string), `position?` ("top" | "bottom" | "left" | "right", default "top"), `children`. Show tooltip on hover with ~200ms delay. CSS: `.ace-tooltip` absolutely positioned relative to wrapper, with arrow.
- [ ] T034 [P] [US5] Create Skeleton component in `frontend/src/components/ui/Skeleton.tsx` + `Skeleton.css` — props: `width?` (string), `height?` (string), `variant?` ("text" | "circle" | "rect"). CSS: `.ace-skeleton` with `@keyframes shimmer` animation (gradient sweep left to right). Variant shapes: text (rounded, full width, 1em height), circle (border-radius 50%), rect (rounded corners).
- [ ] T035 [P] [US5] Create EmptyState component in `frontend/src/components/ui/EmptyState.tsx` + `EmptyState.css` — props: `icon` (ReactNode), `title` (string), `description` (string), `action?` ({ label: string, onClick: () => void }). CSS: `.ace-empty-state` centered flex column with icon, title, description text, optional action Button (secondary variant).
- [ ] T036 [P] [US5] Create Toast component in `frontend/src/components/ui/Toast.tsx` + `Toast.css` — props: `notification` (Notification type from store), `onDismiss` (id: string) => void. CSS: `.ace-toast` with variant modifiers (`.ace-toast--info`, `--success` green accent, `--warning` amber accent, `--error` red accent). Includes dismiss button (X). Entry/exit CSS animation (slide in from right, fade out).
- [ ] T037 [P] [US5] Create Modal component in `frontend/src/components/ui/Modal.tsx` + `Modal.css` — props: `open` (boolean), `onClose`, `title` (string), `children`, `actions?` ({ confirm?: { label, onClick, variant? }, cancel?: { label, onClick } }). CSS: `.ace-modal-backdrop` (semi-transparent overlay), `.ace-modal` (centered dialog, surface bg, shadow). Renders via portal. Closes on backdrop click and Escape key. Focus trap within modal.
- [ ] T038 [US5] Create barrel export in `frontend/src/components/ui/index.ts` — re-export all 10 components: Button, Card, Badge, DataCell, ProgressBar, Tooltip, Skeleton, EmptyState, Toast, Modal

### Tests

- [ ] T039 [P] [US5] Write tests for Button in `frontend/tests/components/ui/Button.test.tsx` — test all 3 variants render with correct CSS classes, all 3 sizes, disabled state, click handler, renders in both themes (set `data-theme` attribute)
- [ ] T040 [P] [US5] Write tests for Card in `frontend/tests/components/ui/Card.test.tsx` — test default and AI variants (AI has `.ace-card--ai` class), title renders, padding variants, renders in both themes
- [ ] T041 [P] [US5] Write tests for Badge in `frontend/tests/components/ui/Badge.test.tsx` — test all 5 variants render with correct CSS classes, text content, renders in both themes
- [ ] T042 [P] [US5] Write tests for DataCell in `frontend/tests/components/ui/DataCell.test.tsx` — test value renders in mono font class, positive delta shows green class, negative delta shows amber class, no delta shows neutral, unit suffix renders, alignment prop, renders in both themes
- [ ] T043 [P] [US5] Write tests for ProgressBar in `frontend/tests/components/ui/ProgressBar.test.tsx` — test value 0/50/100 sets correct width style, all 3 variants, renders in both themes
- [ ] T044 [P] [US5] Write tests for Tooltip in `frontend/tests/components/ui/Tooltip.test.tsx` — test tooltip hidden by default, shows on hover, hides on mouse leave, all 4 positions set correct class, content renders, renders in both themes
- [ ] T045 [P] [US5] Write tests for Skeleton in `frontend/tests/components/ui/Skeleton.test.tsx` — test all 3 variants render with correct classes, custom width/height applied, shimmer animation class present, renders in both themes
- [ ] T046 [P] [US5] Write tests for EmptyState in `frontend/tests/components/ui/EmptyState.test.tsx` — test icon, title, description render, action button renders when provided, action button click calls handler, no action button when not provided, renders in both themes
- [ ] T047 [P] [US5] Write tests for Toast in `frontend/tests/components/ui/Toast.test.tsx` — test all 4 notification types render with correct variant class, dismiss button calls onDismiss, message content renders, renders in both themes
- [ ] T048 [P] [US5] Write tests for Modal in `frontend/tests/components/ui/Modal.test.tsx` — test open/closed state, title and content render, confirm/cancel buttons render and fire handlers, backdrop click calls onClose, Escape key calls onClose, renders in both themes

**Checkpoint**: `npm run test` passes for all 10 component test files. All components can be imported from `frontend/src/components/ui/index.ts`. TypeScript strict mode passes.

---

## Phase 5: User Story 1 — Application Startup with Backend Sidecar (Priority: P1)

**Goal**: App shows splash screen, polls health endpoint, transitions to main interface when backend is ready, shows error state after 15s timeout, shuts down cleanly on exit.

**Independent Test**: Launch app — see splash screen → main UI transition. Kill backend before launch — see error state after 15s with retry button.

### Implementation

- [ ] T049 [US1] Create `useBackendStatus` hook in `frontend/src/hooks/useBackendStatus.ts` — manages sidecar lifecycle: spawns `Command.sidecar('binaries/api-server', ['--port', '57832'])` via `@tauri-apps/plugin-shell` (with fallback for Vite-only dev mode where backend is started manually), polls `GET /health` at 500ms intervals (max 30 retries) using `setInterval` + fetch. Exposes `status: 'polling' | 'ready' | 'error'`, `retry()` (resets counter and restarts polling), `shutdown()` (calls `POST /shutdown`, waits up to 2s, then kills child process). Handles both Tauri and browser environments (detects `window.__TAURI__`).
- [ ] T050 [US1] Create SplashScreen component in `frontend/src/components/layout/SplashScreen.tsx` + `SplashScreen.css` — props: `status: 'polling' | 'error'`, `onRetry: () => void`. Polling state: centered layout with app name "AC Race Engineer", animated progress indicator (CSS spinner or pulsing bar), "Starting backend..." text. Error state: same layout but red error icon, "Backend failed to start" message, "Retry" button (primary variant). CSS: `.ace-splash` full-viewport centered flex, dark theme background.
- [ ] T051 [US1] Update `App.tsx` in `frontend/src/App.tsx` — use `useBackendStatus` hook. When `status === 'polling'` or `status === 'error'`, render `<SplashScreen>`. When `status === 'ready'`, fetch config for theme (via `useTheme`), then render main app shell (placeholder for now, replaced in US3). Register `onCloseRequested` handler from `@tauri-apps/api/window` that calls `shutdown()` before allowing close.
- [ ] T052 [US1] Write tests for SplashScreen in `frontend/tests/components/layout/SplashScreen.test.tsx` — test polling state shows app name and progress indicator, error state shows error message and retry button, retry button click calls onRetry, renders in both themes

**Checkpoint**: Running `npm run dev` with backend started manually shows splash screen briefly then transitions. Running without backend shows error state after 15s.

---

## Phase 6: User Story 3 — Sidebar Navigation (Priority: P1)

**Goal**: Persistent left sidebar with 5 sections, active indicator, session-dependent section visual cues, routing between views.

**Independent Test**: Click each sidebar item — active indicator moves, corresponding view appears. Session-dependent items dimmed when no session selected.

### Implementation

- [ ] T053 [US3] Create Sidebar component in `frontend/src/components/layout/Sidebar.tsx` + `Sidebar.css` — renders logo placeholder ("AC RE" text) at top, 5 navigation items from a `NAVIGATION_SECTIONS` constant array (id, label, icon placeholder, path, requiresSession). Uses `useUIStore` for `activeSection` and `setActiveSection`. Uses `useSessionStore` for `selectedSessionId` to dim session-dependent items (Lap Analysis, Setup Compare, Engineer) when null. Active item has highlighted style. CSS: `.ace-sidebar` fixed-width left column, `.ace-sidebar__item` with `--active` modifier, `--dimmed` modifier for session-dependent items. Collapsible to icon-only mode via `sidebarCollapsed` store state.
- [ ] T054 [US3] Create AppShell component in `frontend/src/components/layout/AppShell.tsx` + `AppShell.css` — layout with `<Sidebar>` on the left and a content area on the right. Content area renders the active view based on `activeSection` from `useUIStore`. CSS: `.ace-app-shell` flex row, sidebar fixed width (240px expanded, 64px collapsed), content area fills remaining space with `overflow-y: auto`.
- [ ] T055 [US3] Update `App.tsx` in `frontend/src/App.tsx` — when backend is ready, render `<AppShell>` instead of placeholder. AppShell renders the correct view component based on `activeSection`.
- [ ] T056 [US3] Create stub view components — create minimal placeholder component in each of: `frontend/src/views/sessions/index.tsx`, `frontend/src/views/analysis/index.tsx`, `frontend/src/views/compare/index.tsx`, `frontend/src/views/engineer/index.tsx`, `frontend/src/views/settings/index.tsx`. Each renders a `<div>` with the section name (these will be replaced with EmptyState components in US6).
- [ ] T057 [US3] Write tests for Sidebar in `frontend/tests/components/layout/Sidebar.test.tsx` — test 5 nav items render, clicking item calls `setActiveSection`, active item has active class, session-dependent items have dimmed class when no session selected, session-dependent items not dimmed when session is selected, renders in both themes

**Checkpoint**: App shows sidebar + content area. Clicking sidebar items switches the content view. Session-dependent items are visually dimmed.

---

## Phase 7: User Story 4 — Notification System with Job Tracking (Priority: P2)

**Goal**: Toast notifications (4 types) with auto-dismiss, WebSocket job tracking integration with automatic notifications on job completion/failure.

**Independent Test**: Trigger each notification type programmatically — verify correct styling and dismiss behavior. Connect to WebSocket job stream — verify notifications on job completion.

### Implementation

- [ ] T058 [US4] Create ToastContainer component in `frontend/src/components/layout/ToastContainer.tsx` + `ToastContainer.css` — reads `notifications` from `useNotificationStore`, renders a `<Toast>` for each notification stacked bottom-right. Passes `onDismiss` that calls `removeNotification`. CSS: `.ace-toast-container` fixed position bottom-right, flex column-reverse, gap between toasts.
- [ ] T059 [US4] Create WebSocket manager in `frontend/src/lib/wsManager.ts` — module-level singleton class `JobWSManager` with methods: `trackJob(jobId: string)` (opens `ws://.../ws/jobs/{jobId}`, listens for messages, updates `useJobStore.getState().updateJobProgress()` on progress, triggers `useNotificationStore.getState().addNotification()` on completed/failed, closes on terminal state), `stopTracking(jobId: string)` (closes connection). Implements exponential backoff reconnection: delays 1000ms, 2000ms, 4000ms with random jitter 0-500ms, max 3 retries. After 3 failures: adds error notification "Live updates unavailable for this job". Export singleton `jobWSManager`.
- [ ] T060 [US4] Create `useJobProgress` hook in `frontend/src/hooks/useJobProgress.ts` — thin React wrapper around `jobWSManager`. Accepts `jobId: string | null`. On mount with non-null jobId, calls `jobWSManager.trackJob(jobId)`. On unmount or jobId change, calls `stopTracking`. Returns current `JobProgress` from `useJobStore` for the given jobId.
- [ ] T061 [US4] Integrate ToastContainer in AppShell — import and render `<ToastContainer />` at the bottom of `frontend/src/components/layout/AppShell.tsx` so notifications are visible on every screen.
- [ ] T062 [US4] Write tests for notification store in `frontend/tests/store/notificationStore.test.ts` — test addNotification creates notification with unique id, removeNotification removes by id, addNotification for non-error types schedules auto-removal (use `vi.useFakeTimers`), addNotification for error type does NOT schedule auto-removal
- [ ] T063 [US4] Write tests for WebSocket manager in `frontend/tests/lib/wsManager.test.ts` — test trackJob opens WebSocket, progress message updates job store, completed message triggers success notification and closes connection, failed message triggers error notification, reconnection on unexpected close with backoff, max 3 retries then error notification. Mock WebSocket API.

**Checkpoint**: Notifications can be triggered from browser console via `useNotificationStore.getState().addNotification('success', 'Test')`. Toast appears bottom-right and auto-dismisses. WebSocket manager connects to job endpoints.

---

## Phase 8: User Story 6 — Empty State Views for All Sections (Priority: P3)

**Goal**: Each navigation section shows a meaningful empty state when no content is available.

**Independent Test**: Navigate to each section — verify unique empty state with relevant icon, message, and suggestion.

### Implementation

- [ ] T064 [P] [US6] Create Sessions empty view in `frontend/src/views/sessions/index.tsx` — replace stub with `<EmptyState>` component: icon (list/folder icon), title "No sessions recorded yet", description "Record a session in Assetto Corsa and it will appear here automatically.", no action button (sessions are discovered automatically by backend watcher).
- [ ] T065 [P] [US6] Create Lap Analysis empty view in `frontend/src/views/analysis/index.tsx` — replace stub with `<EmptyState>` component: icon (chart icon), title "Select a session to analyze laps", description "Go to Sessions and select a session to view detailed lap analysis.", action button "Go to Sessions" that calls `useUIStore.getState().setActiveSection('sessions')`.
- [ ] T066 [P] [US6] Create Setup Compare empty view in `frontend/src/views/compare/index.tsx` — replace stub with `<EmptyState>` component: icon (compare/diff icon), title "Select a session to compare setups", description "Go to Sessions and select a session to compare setup configurations.", action button "Go to Sessions".
- [ ] T067 [P] [US6] Create Engineer empty view in `frontend/src/views/engineer/index.tsx` — replace stub with `<EmptyState>` component: icon (chat/AI icon), title "Select a session to talk with your engineer", description "Go to Sessions and select a session to get AI-powered setup recommendations.", action button "Go to Sessions".
- [ ] T068 [P] [US6] Create Settings placeholder view in `frontend/src/views/settings/index.tsx` — replace stub with a basic settings layout: Card with title "Settings", theme toggle row (label "Theme" + two buttons or toggle for Night Grid / Garage Floor) using `useTheme` hook. This is the only Phase 7.1 settings content; full settings will be added in Phase 7.2.

**Checkpoint**: Navigate to each section — every section shows its unique empty state. Settings shows theme toggle that works. No blank screens anywhere.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and cross-cutting improvements

- [ ] T069 Run TypeScript strict validation — execute `npx tsc --noEmit` from `frontend/`, fix any type errors, ensure zero errors under strict mode with no explicit `any`
- [ ] T070 Run all frontend tests — execute `npm run test` from `frontend/`, ensure all component tests pass, fix any failures
- [ ] T071 Run all backend tests — execute `conda run -n ac-race-engineer pytest backend/tests/ -v`, ensure all 744+ existing tests still pass plus new tests for ui_theme and shutdown
- [ ] T072 Verify design token compliance — grep all `.tsx` and `.css` files in `frontend/src/components/` for hardcoded hex color values (e.g., `#[0-9a-fA-F]{3,8}`), fix any violations to use tokens instead
- [ ] T073 Add npm scripts to `frontend/package.json` — ensure `dev` (vite), `build` (tsc && vite build), `test` (vitest run), `test:watch` (vitest), `typecheck` (tsc --noEmit), `tauri` (tauri) scripts are all present and working

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US2 Theming (Phase 3)**: Depends on Foundational (tokens + stores)
- **US5 Components (Phase 4)**: Depends on Foundational (tokens). Can overlap with US2 since components only need tokens.css, not the theme hook
- **US1 Startup (Phase 5)**: Depends on Foundational (api client, constants). Can overlap with US5 components
- **US3 Navigation (Phase 6)**: Depends on US1 (App.tsx exists) and partially US5 (EmptyState for views)
- **US4 Notifications (Phase 7)**: Depends on US5 (Toast component) and Foundational (stores)
- **US6 Empty States (Phase 8)**: Depends on US5 (EmptyState component) and US3 (views exist)
- **Polish (Phase 9)**: Depends on all phases complete

### User Story Dependencies

- **US2 (Theming)**: Can start after Foundational — no user story dependencies
- **US5 (Components)**: Can start after Foundational — no user story dependencies (can parallel with US2)
- **US1 (Startup)**: Can start after Foundational — no user story dependencies (can parallel with US2/US5)
- **US3 (Navigation)**: Depends on US1 (App.tsx) — soft dependency, mostly needs the app shell to exist
- **US4 (Notifications)**: Depends on US5 (Toast component exists)
- **US6 (Empty States)**: Depends on US5 (EmptyState component) and US3 (view stubs exist)

### Within Each User Story

- Implementation tasks before tests (tests reference the implemented components)
- Stores before hooks that use them (already done in Foundational)
- Components before views that use them
- Core logic before integration

### Parallel Opportunities

- **Phase 1**: T005, T006, T007 can all run in parallel
- **Phase 2 Backend**: T011, T012, T013, T014 can all run in parallel (after T009, T010)
- **Phase 2 Frontend**: T020-T024 (all stores) can run in parallel
- **Phase 4**: All 10 component tasks (T028-T037) can run in parallel; all 10 test tasks (T039-T048) can run in parallel
- **Phase 8**: All 5 view tasks (T064-T068) can run in parallel

---

## Parallel Example: Phase 4 (UI Components)

```bash
# Launch all 10 component implementations in parallel:
T028: Button.tsx + Button.css
T029: Card.tsx + Card.css
T030: Badge.tsx + Badge.css
T031: DataCell.tsx + DataCell.css
T032: ProgressBar.tsx + ProgressBar.css
T033: Tooltip.tsx + Tooltip.css
T034: Skeleton.tsx + Skeleton.css
T035: EmptyState.tsx + EmptyState.css
T036: Toast.tsx + Toast.css
T037: Modal.tsx + Modal.css

# Then barrel export:
T038: index.ts

# Then all 10 test files in parallel:
T039-T048: All component test files
```

---

## Implementation Strategy

### MVP First (US2 + US5 + US1 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (backend + core infra)
3. Complete Phase 3: US2 (theming)
4. Complete Phase 4: US5 (components + tests)
5. Complete Phase 5: US1 (startup/sidecar)
6. Complete Phase 6: US3 (sidebar navigation)
7. **STOP and VALIDATE**: App launches, shows splash → sidebar → views with theme switching

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. Add US2 (theming) → Theme switching works
3. Add US5 (components) → Full component library with tests
4. Add US1 (startup) → Sidecar lifecycle + splash screen
5. Add US3 (navigation) → Full app shell with sidebar
6. Add US4 (notifications) → Toast system + job tracking
7. Add US6 (empty states) → All sections have meaningful content
8. Polish → Zero type errors, all tests pass, no hardcoded colors

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US5 are placed before US1/US3 because tokens and components are prerequisites for the app shell
- Backend changes (T009-T014) are small and backward-compatible with existing 744 tests
- All component CSS uses `ace-` prefix for scoping (no CSS Modules)
- JetBrains Mono is bundled locally (not CDN) per constitution Principle XII
- No localStorage/sessionStorage anywhere — all state in-memory (TanStack Query + Zustand)
- Commit after each task or logical group
