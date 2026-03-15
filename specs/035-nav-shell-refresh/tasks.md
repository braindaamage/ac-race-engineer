# Tasks: Navigation Shell & Visual Refresh

**Input**: Design documents from `/specs/035-nav-shell-refresh/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/routes.md, contracts/tokens.md, quickstart.md

**Tests**: Included — the spec requires SC-006 (all existing tests pass) and the plan identifies 6 new + 1 rewritten + 7 modified test files.

**Organization**: Tasks are grouped by user story. US1+US2 (both P1) are combined because they share the same routing/layout infrastructure. US4 (Settings access) and US5 (Placeholder views) are folded into US1+US2 as they are structural prerequisites of the navigation shell.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Install dependencies, copy assets, prepare imports

- [x] T001 Install react-router-dom v7 and @fortawesome/fontawesome-free via npm in `frontend/`
- [x] T002 Copy `frontend/prototypes/logo.png` to `frontend/src/assets/logo.png` (create `assets/` directory if needed)
- [x] T003 Import `@fortawesome/fontawesome-free/css/all.min.css` at the top of `frontend/src/main.tsx`

---

## Phase 2: Foundational (Design Tokens)

**Purpose**: Update the visual foundation — palette and undefined token fixes. MUST complete before any user story work begins.

- [x] T004 Update primitive color values in `frontend/src/tokens.css` — replace all color and gray-scale hex values per contracts/tokens.md Color Primitives and Gray Scale Primitives tables (22 token values)
- [x] T005 Add light theme semantic overrides in `frontend/src/tokens.css` — in the `[data-theme="light"]` block, override `--bg` to `#F8F9FA`, `--text-primary` to `#111827`, `--text-secondary` to `#6B7280`, and `--border` to `#E5E7EB` using explicit hex values per contracts/tokens.md Semantic Layer Impact section
- [x] T006 [P] Fix undefined token references in `frontend/src/views/analysis/AnalysisView.css` — replace `--spacing-lg` → `--space-6` (2×), `--border-primary` → `--border-strong` (1×), `--border-subtle` → `--border` (1×), `--color-success` → `--color-positive` (1×)
- [x] T007 [P] Fix undefined token references in `frontend/src/views/compare/CompareView.css` — replace `--spacing-lg` → `--space-6` (2×), `--border-subtle` → `--border` (1×), `--color-success` → `--color-positive` (1×)
- [x] T008 [P] Fix undefined token references in `frontend/src/views/sessions/SessionsView.css` — replace `--spacing-lg` → `--space-6` (2×)
- [x] T009 [P] Fix undefined token references in `frontend/src/views/settings/Settings.css` — replace `--brand` → `--color-brand` (1×), `--font-size-md` → `--font-size-base` (1×); and in `frontend/src/views/settings/CarDataSection.css` — replace `--font-size-md` → `--font-size-base` (1×)
- [x] T010 [P] Fix undefined token references in `frontend/src/components/onboarding/OnboardingWizard.css` — replace `--brand` → `--color-brand` (4×), `--success` → `--color-positive` (1×), `--error` → `--color-error` (1×), `--font-size-md` → `--font-size-base` (1×)

**Checkpoint**: All tokens resolve correctly. Foundation ready for layout work.

---

## Phase 3: US1+US2 — Navigation Shell & Session Tabs (Priority: P1) 🎯 MVP

**Goal**: Replace sidebar navigation with hierarchical car-centric routing. Fixed header with breadcrumb and contextual tab bar. Session detail view with three work tabs. Placeholder views for Garage Home and Car Tracks. Settings accessible from header. All existing views render correctly inside the new layout.

**Independent Test**: Navigate the full path (Garage Home → Car → Track → Session → Tab) and back via breadcrumb. Switch between session tabs. Access Settings from header. Browser back/forward works at every level. URLs are bookmarkable.

**Includes**: US4 (Settings access from header — the settings gear icon is built into the Header component), US5 (Placeholder views — GarageView and CarTracksView are structural prerequisites of the navigation hierarchy)

### Router & App Integration

- [x] T012 [US1] Create route tree in `frontend/src/router.tsx` using `createBrowserRouter` — define all 9 routes per contracts/routes.md Route Tree: root redirect to /garage, /garage, /garage/:carId/tracks, /garage/:carId/tracks/:trackId/sessions, /session/:sessionId redirect to laps, /session/:sessionId/laps, /session/:sessionId/setup, /session/:sessionId/engineer, /settings, catch-all redirect to /garage. Use `Navigate` for redirects, `Outlet` for layout nesting per contracts/routes.md Layout Hierarchy.
- [x] T013 [US1] Modify `frontend/src/App.tsx` — replace the `<AppShell />` render with `<RouterProvider router={router} />` from router.tsx. Keep the existing backend status check, config loading, theme setup, and onboarding gate logic. The router should only render when the app is ready (backend up, config loaded, onboarding completed).

### Layout Components

- [x] T014 [US1] Rewrite `frontend/src/components/layout/AppShell.tsx` and `AppShell.css` — new root layout component: fixed Header (64px) at top, contextual TabBar below header, main content area (max-width 1920px centered, overflow-y auto) with `<Outlet />`, ToastContainer at bottom-right. No sidebar. Use `ace-` CSS prefix per project convention. Reference only semantic tokens for all colors.
- [x] T015 [US1] Create `frontend/src/components/layout/Header.tsx` and `Header.css` — fixed 64px header: logo image (`src/assets/logo.png`) + "AC Race Engineer" text on left, dynamic Breadcrumb component in center-left, settings gear icon (`fa-solid fa-gear`) as a Link to `/settings` on right. Use `ace-header` CSS prefix.
- [x] T016 [US1] Create `frontend/src/components/layout/Breadcrumb.tsx` and `Breadcrumb.css` — reads current route via `useMatches()` or `useLocation()` + `useParams()`, generates BreadcrumbSegment array per contracts/routes.md Breadcrumb Contract. Home icon (`fa-solid fa-house`), chevron separators (`fa-solid fa-chevron-right`), clickable Link segments for ancestors, plain text for current level. For session-level breadcrumbs, resolve car/track names from TanStack Query cache (useSessions data) or format raw params with `formatCarTrack` from `views/sessions/utils.ts`. Use `ace-breadcrumb` CSS prefix.
- [x] T017 [US1] Create `frontend/src/components/layout/TabBar.tsx` and `TabBar.css` — contextual tab bar per contracts/routes.md Tab Bar Contract: at garage/tracks/sessions/settings levels shows global nav tabs (Garage Home, Tracks, Sessions, Settings) with active state from current route; at session detail level shows work tabs (Lap Analysis, Setup Compare, Engineer) with active state from route suffix. Tabs are NavLink components. Active tab has visual indicator (red underline or background per prototype style). Use `ace-tabbar` CSS prefix. Global nav tabs that lack sufficient route context (e.g., "Tracks" at the /garage level where no carId exists, "Sessions" at /garage/:carId/tracks where no trackId exists) MUST be rendered as disabled/non-clickable (dimmed opacity) — similar to the existing sidebar pattern where items without a selected session are dimmed. Only tabs with full route context are clickable.
- [x] T018 [US2] Create `frontend/src/components/layout/SessionLayout.tsx` and `SessionLayout.css` — nested layout for `/session/:sessionId/*` routes. Renders `<Outlet />` for the active tab's view component. The tab bar rendering is handled by TabBar reading the route, so SessionLayout is a thin wrapper. Use `ace-session-layout` CSS prefix.

### Placeholder Views

- [x] T019 [P] [US1] Create `frontend/src/views/garage/index.tsx` and `GarageView.css` — placeholder Garage Home view with heading "My Garage", descriptive text "Your cars with session data will appear here", and a car icon (`fa-solid fa-car`). Use the EmptyState component from `components/ui/`. Include a `data-testid="garage-view"` attribute.
- [x] T020 [P] [US1] Create `frontend/src/views/tracks/index.tsx` and `CarTracksView.css` — placeholder Car Tracks view that reads `carId` from `useParams()`, shows heading "Tracks for {formatCar(carId)}", descriptive text "Tracks driven with this car will appear here", and a road icon (`fa-solid fa-road`). Use the EmptyState component. Include a `data-testid="tracks-view"` attribute.

### Existing View Adaptations

- [x] T021 [US1] Adapt `frontend/src/views/sessions/index.tsx` — read `carId` and `trackId` from `useParams()` instead of showing all sessions. Filter sessions by carId+trackId (using existing `useSessions` hook data). Replace `selectSession(id)` calls with `useNavigate()` to `/session/${id}/laps`. Replace `useUIStore.getState().setActiveSection("sessions")` calls with `useNavigate()`. Remove all `useSessionStore` and `useUIStore` imports.
- [x] T022 [P] [US2] Adapt `frontend/src/views/analysis/index.tsx` — read `sessionId` from `useParams()` instead of `useSessionStore`. Replace the no-session empty state with route-based check (if `!sessionId`, navigate to /garage). Replace `useUIStore.getState().setActiveSection("sessions")` with `useNavigate()` to appropriate route. Remove all `useSessionStore` and `useUIStore` imports.
- [x] T023 [P] [US2] Adapt `frontend/src/views/compare/index.tsx` — same pattern as T022: read `sessionId` from `useParams()`, replace store-based navigation with `useNavigate()`, remove `useSessionStore` and `useUIStore` imports.
- [x] T024 [P] [US2] Adapt `frontend/src/views/engineer/index.tsx` — same pattern as T022: read `sessionId` from `useParams()`, replace store-based navigation with `useNavigate()`, remove `useSessionStore` and `useUIStore` imports.
- [x] T025 [US1] Adapt `frontend/src/views/settings/index.tsx` — remove the `useUIStore` import and the `activeSection`-based dirty-state navigation interception logic. Settings is now a route (`/settings`), so browser back handles "return to previous view". Remove `useUIStore` and `useSessionStore` imports. Keep all existing settings functionality unchanged.
- [x] T026 [US1] Delete `frontend/src/components/layout/Sidebar.tsx` and `frontend/src/components/layout/Sidebar.css`

### State Store Cleanup

> Store deletion happens here — after all consumers (T021-T025) have been migrated away from uiStore and sessionStore.

- [x] T011 [US1] Delete `frontend/src/store/uiStore.ts` and `frontend/src/store/sessionStore.ts`. Remove their exports from any store barrel/index file if one exists.

### Tests for US1+US2

- [x] T027 [US1] Create test helper `renderWithRouter` in `frontend/tests/helpers/renderWithRouter.tsx` — wraps component in `createMemoryRouter` + `RouterProvider` + `QueryClientProvider` per research.md R7 test helper pattern. Accept `route`, `path`, and optionally full route array for nested layouts.
- [x] T028 [US1] Create `frontend/tests/router.test.tsx` — test route rendering: / redirects to /garage, /garage renders GarageView, /garage/:carId/tracks renders CarTracksView, /session/:sessionId redirects to laps, /session/:sessionId/laps renders AnalysisView, /settings renders SettingsView, unknown routes redirect to /garage. Use `createMemoryRouter`.
- [x] T029 [P] [US1] Create `frontend/tests/components/layout/Header.test.tsx` — test logo image renders, breadcrumb renders, settings gear icon links to /settings
- [x] T030 [P] [US1] Create `frontend/tests/components/layout/Breadcrumb.test.tsx` — test breadcrumb segments at each route level per contracts/routes.md Breadcrumb Contract: home-only at /garage, home + car at tracks, home + car + track at sessions, full path at session detail, home + settings at /settings. Test segment click navigates correctly.
- [x] T031 [P] [US1] Create `frontend/tests/components/layout/TabBar.test.tsx` — test global nav tabs at garage/tracks/sessions/settings levels, work tabs at session detail level. Test active tab highlighting matches current route.
- [x] T032 [P] [US2] Create `frontend/tests/components/layout/SessionLayout.test.tsx` — test that SessionLayout renders child route (Outlet) for laps/setup/engineer paths
- [x] T033 [US1] Rewrite `frontend/tests/components/layout/AppShell.test.tsx` — test new layout structure: Header renders, TabBar renders, Outlet renders child content, ToastContainer present. Remove all uiStore and sessionStore mocks.
- [x] T034 [US1] Delete `frontend/tests/components/layout/Sidebar.test.tsx`
- [x] T035 [US2] Adapt `frontend/tests/views/analysis/AnalysisView.test.tsx` — replace `useSessionStore` mock with `renderWithRouter` at route `/session/test-id/laps` with path `/session/:sessionId/laps`. Replace `useUIStore` mocks with route navigation assertions. Keep all existing test coverage for laps, telemetry, corners.
- [x] T036 [P] [US2] Adapt `frontend/tests/views/compare/CompareView.test.tsx` — same pattern as T035: replace store mocks with router rendering at `/session/test-id/setup`
- [x] T037 [P] [US2] Adapt `frontend/tests/views/engineer/EngineerView.test.tsx` — same pattern as T035: replace store mocks with router rendering at `/session/test-id/engineer`
- [x] T038 [US1] Adapt `frontend/tests/views/sessions/SessionsView.test.tsx` — replace `useSessionStore` mock with router rendering at `/garage/test-car/tracks/test-track/sessions`. Replace `selectSession` assertions with navigation assertions. Replace `useUIStore` mocks.
- [x] T039 [US1] Adapt `frontend/tests/views/settings/SettingsView.test.tsx` — remove `useUIStore` mocks. Render via router at `/settings`. Keep all existing settings functionality tests.
- [x] T040 [US1] Adapt `frontend/tests/App.test.tsx` — integrate router into test rendering. Test that app shows splash screen → onboarding or main interface flow. Update to expect /garage route instead of sessions view.

**Checkpoint**: Full navigation hierarchy works. All 9 routes render correctly. Breadcrumb and tab bar are contextual. Session tabs switch views. Settings accessible from header. Browser back/forward works. All existing view tests pass with router-based rendering.

---

## Phase 4: US3 — Visual Identity (Priority: P2)

**Goal**: Replace all emoji icons with Font Awesome equivalents across all view files.

**Independent Test**: Visually inspect all views — no emoji characters visible, all icons render as Font Awesome glyphs.

- [x] T041 [P] [US3] Replace emoji icons with Font Awesome in `frontend/src/views/analysis/index.tsx` — replace `&#9888;` warning with `<i className="fa-solid fa-triangle-exclamation" />`, replace `&#128202;` chart with `<i className="fa-solid fa-chart-line" />`, and any other emoji in empty states per research.md R4 icon mapping
- [x] T042 [P] [US3] Replace emoji icons with Font Awesome in `frontend/src/views/compare/index.tsx` — replace `&#9888;` and `&#128260;` with appropriate FA icons per research.md R4 icon mapping
- [x] T043 [P] [US3] Replace emoji icons with Font Awesome in `frontend/src/views/engineer/index.tsx` — replace `&#129302;` robot with `<i className="fa-solid fa-robot" />`, `&#128269;` magnifier with `<i className="fa-solid fa-magnifying-glass" />`, `&#9888;` warning with FA equivalent
- [x] T044 [P] [US3] Replace emoji icons with Font Awesome in `frontend/src/views/sessions/index.tsx` — replace `&#9888;` and `&#128203;` with appropriate FA icons
- [x] T045 [P] [US3] Replace emoji icons with Font Awesome in `frontend/src/views/analysis/CornerTable.tsx` — replace `&#128739;` with appropriate FA icon (e.g., `fa-solid fa-location-dot`)
- [x] T046 [P] [US3] Replace emoji/warning characters in `frontend/src/components/onboarding/PathInput.tsx` (⚠ character) and `frontend/src/components/onboarding/StepReview.tsx` (⚠ characters) with `<i className="fa-solid fa-triangle-exclamation" />`

**Checkpoint**: All emoji icons replaced with Font Awesome. Visual identity matches prototype brand language.

---

## Phase 5: US7 — Updated Splash Screen (Priority: P2)

**Goal**: Splash screen displays new logo and matches new brand identity.

**Independent Test**: Launch the app or simulate backend unavailability — new logo, loading animation, and brand colors appear.

- [x] T047 [US7] Update `frontend/src/components/layout/SplashScreen.tsx` and `SplashScreen.css` — replace the text-based "AC Race Engineer" heading with the new logo image (`src/assets/logo.png`). Update loading indicator styling to use brand red for the spinner/progress animation. Match visual style from `frontend/prototypes/2-Racing Engineering - Loading.html`. Keep existing polling/error/retry logic unchanged.
- [x] T048 [US7] Update `frontend/tests/components/layout/SplashScreen.test.tsx` — add test that logo image element is rendered (query by `alt` text or `role="img"`). Keep existing polling/error state tests.

**Checkpoint**: Splash screen shows new logo and brand colors.

---

## Phase 6: US6 — Onboarding within New Layout (Priority: P3)

**Goal**: Onboarding wizard renders inside the new layout without sidebar, transitions to Garage Home on completion.

**Independent Test**: Reset onboarding state, launch app, complete wizard, confirm landing on Garage Home.

- [x] T049 [US6] Adapt `frontend/src/components/onboarding/OnboardingWizard.tsx` — ensure the wizard works within the new layout (no sidebar dependency). On completion (`handleFinish`), navigate to `/garage` using `useNavigate()` instead of relying on `setActiveSection`. Remove any `useUIStore` imports if present.
- [x] T050 [US6] Verify `frontend/tests/components/onboarding/OnboardingWizard.test.tsx` still passes — if the wizard tests reference `useUIStore` or `setActiveSection`, replace with route navigation assertions. If tests don't reference stores, no changes needed.

**Checkpoint**: Onboarding completes and lands user on Garage Home via routing.

---

## Phase 7: Tauri Desktop Icons (FR-018)

**Purpose**: Regenerate application icons from new logo for Windows taskbar/start menu/explorer.

- [x] T051 Regenerate Tauri desktop icons — run `npx @tauri-apps/cli icon frontend/src/assets/logo.png` from `frontend/` directory to generate all platform icon sizes in `frontend/src-tauri/icons/`. Verify `frontend/src-tauri/tauri.conf.json` icon paths still reference the correct `icons/` directory. If logo.png is smaller than 1024×1024, the tool will generate at available sizes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T052 Run `npx tsc --noEmit` from `frontend/` — fix any TypeScript strict mode errors introduced by the migration
- [x] T053 Run `npm run test` from `frontend/` — verify all tests pass (existing adapted + new tests). Fix any remaining failures.
- [x] T054 Run quickstart.md verification checklist — manually verify: app starts and shows splash, navigate full hierarchy, breadcrumb clickable at each level, browser back/forward works, URLs are bookmarkable, settings accessible from header, dark+light themes show new colors, logo visible in header+splash, no emoji icons remain, taskbar icon shows new logo

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (npm deps installed). Token fixes only — BLOCKS all user stories
- **US1+US2 (Phase 3)**: Depends on Phase 2 — core navigation and layout
- **US3 (Phase 4)**: Depends on Phase 2 only — can run in parallel with Phase 3
- **US7 (Phase 5)**: Depends on Phase 2 only — can run in parallel with Phases 3-4
- **US6 (Phase 6)**: Depends on Phase 3 (needs router + new layout to exist)
- **Tauri Icons (Phase 7)**: Depends on Phase 1 only (logo file) — can run in parallel with everything else
- **Polish (Phase 8)**: Depends on all phases complete

### User Story Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (token fixes)
    ↓                    ↓                    ↓
Phase 3: US1+US2     Phase 4: US3         Phase 5: US7      Phase 7: Tauri Icons
(nav + tabs)         (emoji→FA)           (splash)           (parallel from Phase 1)
    ↓
Phase 6: US6
(onboarding)
    ↓
Phase 8: Polish (after all)
```

### Within Phase 3 (US1+US2)

Execution order within the MVP phase:

1. T012 (router.tsx) — must be first, everything depends on it
2. T013 (App.tsx) — integrates router into app
3. T014 (AppShell) — root layout
4. T015-T018 (Header, Breadcrumb, TabBar, SessionLayout) — [P] can be parallel
5. T019-T020 (placeholder views) — [P] can be parallel with T015-T018
6. T021-T025 (view adaptations) — after layout components exist
7. T026 (delete Sidebar) — after all references removed
8. T011 (delete uiStore + sessionStore) — after all store consumers migrated
9. T027 (test helper) — before any tests
10. T028-T034 (new/rewritten tests) — after implementation
11. T035-T040 (adapted tests) — after view adaptations

### Parallel Opportunities

**Phase 2** (all foundational token fixes run in parallel):
```
T006 (AnalysisView.css)  ||  T007 (CompareView.css)  ||  T008 (SessionsView.css)
T009 (Settings.css)      ||  T010 (OnboardingWizard.css)
```

**Phase 3** (layout components in parallel after router):
```
T015 (Header)  ||  T016 (Breadcrumb)  ||  T017 (TabBar)  ||  T018 (SessionLayout)
T019 (GarageView)  ||  T020 (CarTracksView)
T022 (AnalysisView)  ||  T023 (CompareView)  ||  T024 (EngineerView)
```

**Phase 3 tests** (new layout tests in parallel):
```
T029 (Header.test)  ||  T030 (Breadcrumb.test)  ||  T031 (TabBar.test)  ||  T032 (SessionLayout.test)
T035 (AnalysisView.test)  ||  T036 (CompareView.test)  ||  T037 (EngineerView.test)
```

**Phase 4** (all emoji replacements in parallel):
```
T041  ||  T042  ||  T043  ||  T044  ||  T045  ||  T046
```

**Cross-phase parallelism** (after Phase 2):
```
Phase 3 (US1+US2)  ||  Phase 4 (US3)  ||  Phase 5 (US7)  ||  Phase 7 (Tauri Icons)
```

---

## Implementation Strategy

### MVP First (Phase 3: US1+US2 Only)

1. Complete Phase 1: Setup (install deps, copy logo)
2. Complete Phase 2: Foundational (token fixes)
3. Complete Phase 3: US1+US2 (router, layout, views, tests)
4. **STOP and VALIDATE**: Navigate full hierarchy, switch tabs, test back/forward, verify URLs
5. The app is functionally complete with new navigation — visual polish follows

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1+US2 (Phase 3) → Navigation works → **MVP milestone**
3. US3 (Phase 4) → Emoji replaced with FA → **Visual milestone**
4. US7 (Phase 5) → Splash screen updated → **Brand milestone**
5. US6 (Phase 6) → Onboarding adapted → **Completeness milestone**
6. Tauri Icons (Phase 7) → Desktop icons updated → **Distribution milestone**
7. Polish (Phase 8) → All tests pass, TypeScript clean → **Release candidate**

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- US4 (Settings access) is integrated into US1 — the Header component includes the settings gear icon
- US5 (Placeholder views) is integrated into US1 — GarageView and CarTracksView are structural navigation targets
- Commit after each completed phase
- The `renderWithRouter` helper (T027) must be created before any new/adapted tests
- Existing tests for UI components (Badge, Button, Card, etc.), hooks, notification store, job store, and lib utilities require NO changes
