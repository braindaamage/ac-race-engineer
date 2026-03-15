# Research: Navigation Shell & Visual Refresh

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15

## R1: React Router v7 Integration in Tauri Desktop App

**Decision**: Use `react-router-dom` v7 with `createBrowserRouter` and `RouterProvider`.

**Rationale**:
- React Router v7 supports the data router pattern with `createBrowserRouter`, `Outlet` for nested layouts, and `Navigate` for redirects — all needed for the hierarchical route structure.
- `useParams()` provides type-safe access to route parameters (carId, trackId, sessionId), replacing the Zustand-based session selection.
- `createMemoryRouter` is available for testing, allowing route-aware test rendering without a DOM history API.
- Tauri v2 uses a webview that supports the History API, so `createBrowserRouter` works natively. No special configuration needed beyond ensuring the webview serves the SPA correctly (Tauri already does this via `distDir`).

**Alternatives considered**:
- **TanStack Router**: More type-safe but heavier migration, smaller ecosystem, overkill for this route count.
- **Wouter**: Lightweight but lacks nested layout routes and the data router pattern.
- **Keep Zustand-based navigation**: Does not support deep-linking, bookmarking, or browser back/forward — directly contradicts spec requirements.

**Key patterns**:
- Route tree defined in `router.tsx` using `createBrowserRouter([...])`.
- `AppShell` is the root layout route, renders `<Outlet />` for child routes.
- `SessionLayout` is a nested layout route for `/session/:sessionId/*`, renders tab bar + `<Outlet />`.
- Redirects via `<Navigate to="/garage" replace />` for `/` and `<Navigate to="laps" replace />` for `/session/:sessionId`.
- Tests use `createMemoryRouter` + `RouterProvider` instead of `MemoryRouter` (the latter is for legacy non-data routers).

## R2: Undefined CSS Token Resolution

**Decision**: Fix all 8 undefined token references by mapping to existing defined tokens.

**Rationale**: The current codebase has 23 references across 11 CSS files to 8 custom properties that are not defined in `tokens.css`. These silently fall through to browser defaults, causing inconsistent styling.

**Mappings**:

| Undefined Token | Replacement | Rationale |
|----------------|-------------|-----------|
| `--spacing-lg` | `--space-6` (24px) | Matches the intent of "large spacing" in layout contexts |
| `--brand` | `--color-brand` | Naming convention alignment |
| `--success` | `--color-positive` | Naming convention alignment |
| `--error` | `--color-error` | Already defined with `--color-` prefix in tokens.css |
| `--border-primary` | `--border-strong` | Intent matches "primary/strong" border |
| `--border-subtle` | `--border` | Default border is the subtle variant |
| `--color-success` | `--color-positive` | tokens.css uses "positive" not "success" |
| `--font-size-md` | `--font-size-base` | "md" = "base" in the scale (xs, sm, base, lg, xl, 2xl) |

**Files requiring fixes** (23 references):
- `views/compare/CompareView.css` (4 refs: --spacing-lg ×2, --border-subtle, --color-success)
- `views/analysis/AnalysisView.css` (5 refs: --spacing-lg ×2, --border-primary, --border-subtle, --color-success)
- `views/sessions/SessionsView.css` (2 refs: --spacing-lg ×2)
- `views/settings/Settings.css` (2 refs: --brand, --font-size-md)
- `views/settings/CarDataSection.css` (1 ref: --font-size-md, has fallback)
- `components/onboarding/OnboardingWizard.css` (6 refs: --brand ×4, --success, --error)
- `components/layout/AppShell.css` (1 ref: --font-size-md)

## R3: Design Token Palette Migration

**Decision**: Update primitive layer values in `tokens.css` to match prototype palette. Semantic layer mappings remain unchanged (they reference primitives).

**Rationale**: The prototypes define a specific color palette that differs from the current values. Since the semantic layer references primitives, updating primitives propagates automatically.

**Changes to primitives**:

| Token | Current Value | New Value | Source |
|-------|--------------|-----------|--------|
| `--red-500` | #ef4444 | #FF1A1A | Lighter red for hover/active states |
| `--red-600` | #dc2626 | #E60000 | Brand red primary |
| `--red-700` | #b91c1c | #CC0000 | Brand red dark |
| `--cyan-400` | #22d3ee | #33D6FF | Lighter cyan |
| `--cyan-500` | #06b6d4 | #00CCFF | Brand blue/AI primary |
| `--cyan-600` | #0891b2 | #00A3CC | Darker cyan |
| `--green-400` | #4ade80 | #2ECC71 | Lighter green |
| `--green-500` | #22c55e | #1AB866 | Brand green primary |
| `--green-600` | #16a34a | #159652 | Darker green |
| `--amber-400` | #fbbf24 | #FFC733 | Lighter amber |
| `--amber-500` | #f59e0b | #FFB917 | Brand amber primary |
| `--amber-600` | #d97706 | #CC9412 | Darker amber |
| `--gray-950` | #020617 | #0B1015 | Dark background |
| `--gray-900` | #0f172a | #171E27 | Dark surface |
| `--gray-800` | #1e293b | #222D38 | Dark elevated |
| `--gray-700` | #334155 | #2A333D | Dark border |
| `--gray-500` | #64748b | #7A8B99 | Brand grey/muted |
| `--gray-300` | #cbd5e1 | #9CA3AF | Dark subtext |
| `--gray-50` | #f8fafc | #F3F4F6 | Dark text primary / Light bg |

**Light theme semantic layer overrides**:

Because the gray primitives shifted, three light-theme semantic tokens no longer resolve to the prototype's intended values. These require explicit hex overrides in the light theme block of `tokens.css` (not primitive references):

| Token | Current mapping | New explicit value | Reason |
|-------|----------------|-------------------|--------|
| Light `--bg` | var(--gray-50) → #F3F4F6 | #F8F9FA | Prototype specifies #F8F9FA, not the shifted gray-50 |
| Light `--bg-surface` | white | #FFFFFF (unchanged) | No override needed |
| Light `--text-primary` | var(--gray-900) → #171E27 | #111827 | Prototype specifies #111827 for light text |
| Light `--text-secondary` | var(--gray-600) → #4B5563 | #6B7280 | Prototype specifies #6B7280 for light subtext |
| Light `--border` | var(--gray-200) → #D1D5DB | #E5E7EB | Prototype specifies #E5E7EB for light borders |

## R4: Font Awesome Integration

**Decision**: Install `@fortawesome/fontawesome-free` via npm and use CSS classes (`fa-solid fa-*`) in JSX.

**Rationale**: The prototypes use Font Awesome 6.4.0 via CDN. For a Tauri desktop app, bundling via npm is more reliable than CDN (app may be offline). The free tier includes all icons used in the prototypes.

**Alternatives considered**:
- **CDN link in index.html**: Requires internet; fragile for desktop app.
- **React Icons**: Would work but prototypes specifically use FA classes, and FA's CSS approach is simpler for this use case.
- **SVG sprite**: More control but higher effort for equivalent result.

**Icon mapping** (emoji → Font Awesome):

| Location | Current Emoji | FA Icon | FA Class |
|----------|--------------|---------|----------|
| Sessions nav | 📋 `\u{1F4CB}` | clipboard-list | `fa-solid fa-clipboard-list` |
| Analysis nav | 📊 `\u{1F4CA}` | chart-line | `fa-solid fa-chart-line` |
| Compare nav | 🔄 `\u{1F504}` | code-compare | `fa-solid fa-code-compare` |
| Engineer nav | 🤖 `\u{129302}` | robot | `fa-solid fa-robot` |
| Settings nav | ⚙️ `\u2699` | gear | `fa-solid fa-gear` |
| Warning icons | ⚠ `&#9888;` | triangle-exclamation | `fa-solid fa-triangle-exclamation` |
| Empty states | Various | Contextual | Per-view appropriate icons |
| Header logo | Text "AC RE" | N/A | Logo image replaces text |
| Header settings | N/A (in sidebar) | gear | `fa-solid fa-gear` |
| Breadcrumb home | N/A | house | `fa-solid fa-house` |
| Breadcrumb separator | N/A | chevron-right | `fa-solid fa-chevron-right` |

**Import strategy**: Import `@fortawesome/fontawesome-free/css/all.min.css` once in `main.tsx` or `App.tsx`.

## R5: Session Store Migration

**Decision**: Remove `sessionStore` entirely. Session detail views get `sessionId` from `useParams()`. No remaining consumers need the store after migration.

**Rationale**: After analysis, `sessionStore` is used in:
- 6 source files (layout + 4 views + sidebar)
- 6 test files

The `jobStore` tracks job progress keyed by job ID, not session ID. The `wsManager` doesn't reference sessionStore. However, the EngineerView and SessionsView use `selectedSessionId` for:
1. **Data fetching** (messages, recommendations) — migrates to `useParams().sessionId`
2. **Job submission** (engineer analysis, chat) — needs a session ID to submit jobs

For job submission, the view already has the sessionId from params, so it can pass it directly. The `selectSession`/`clearSession` actions are still useful in SessionsView for the transition from "sessions list" to "navigate to session detail" — but with routing, this becomes `navigate(`/session/${id}/laps`)` instead.

**Migration plan**:
- Remove `sessionStore.ts` file entirely — all consumers migrate to route params via `useParams()` or navigation via `useNavigate()`.
- Remove `uiStore.ts` file entirely — `activeSection` replaced by router, `sidebarCollapsed` removed with sidebar.

## R6: Tauri Icon Regeneration

**Decision**: Use `cargo tauri icon` CLI to regenerate all platform icons from `logo.png`.

**Rationale**: Tauri's built-in icon generation tool produces all required sizes and formats (ico for Windows, icns for macOS, png for Linux) from a single source image. The source must be at least 1024x1024 PNG with transparency.

**Steps**:
1. Copy `frontend/prototypes/logo.png` to `frontend/src/assets/logo.png` (for app header use)
2. Run `cd frontend && npx tauri icon src/assets/logo.png` — outputs to `src-tauri/icons/`
3. Verify `tauri.conf.json` icon paths still match (default `icons/` directory)

**Prerequisite**: `logo.png` must be at minimum 1024x1024. If smaller, upscale or use as-is (Tauri will warn but still generate).

## R7: Test Migration Strategy

**Decision**: Use `createMemoryRouter` + `RouterProvider` for all component tests that need routing context. Non-routing tests remain unchanged.

**Rationale**: React Router v7's data router pattern (`createBrowserRouter`) requires `RouterProvider` — the legacy `<BrowserRouter>` / `<MemoryRouter>` wrappers don't support data routers. For tests, `createMemoryRouter` provides the equivalent in-memory capability.

**Test helper pattern**:
```typescript
function renderWithRouter(
  ui: React.ReactElement,
  { route = "/", path = "/" }: { route?: string; path?: string } = {}
) {
  const router = createMemoryRouter(
    [{ path, element: ui }],
    { initialEntries: [route] }
  );
  return render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
```

**Migration categories**:
1. **DELETE**: `Sidebar.test.tsx` (component deleted)
2. **REWRITE**: `AppShell.test.tsx` (completely different component)
3. **NEW**: `Header.test.tsx`, `Breadcrumb.test.tsx`, `TabBar.test.tsx`, `SessionLayout.test.tsx`, `router.test.tsx`
4. **MODIFY (store→router)**: `AnalysisView.test.tsx`, `CompareView.test.tsx`, `EngineerView.test.tsx`, `SessionsView.test.tsx`, `SettingsView.test.tsx` — replace `useSessionStore` mocks with route param rendering, replace `useUIStore` mocks with navigation assertions
5. **MODIFY (minor)**: `SplashScreen.test.tsx` (verify new logo renders), `App.test.tsx` (integrate router)
6. **UNCHANGED**: All UI component tests, hook tests, store tests (notification, job), lib utility tests

## R8: Breadcrumb Data Resolution

**Decision**: Breadcrumb labels are derived from route params + API data. Use a combination of route matching and lightweight data fetching.

**Rationale**: Route params contain identifiers (e.g., `ks_bmw_m3_e30`, `magione`), but breadcrumb labels should display human-readable names. The sessions API already returns `car_name` and `track_name` fields which are the raw identifiers. For Phase 14.1, display these identifiers with cosmetic formatting (replace underscores with spaces, remove `ks_` prefix — matching the existing `formatCarTrack` utility in `views/sessions/utils.ts`). Phase 14.2 may introduce proper display names.

**Breadcrumb segments by route**:

| Route | Segments |
|-------|----------|
| `/garage` | Home |
| `/garage/:carId/tracks` | Home / {formatCar(carId)} |
| `/garage/:carId/tracks/:trackId/sessions` | Home / {formatCar(carId)} / {formatTrack(trackId)} |
| `/session/:sessionId/laps` | Home / {car} / {track} / {session date} |
| `/session/:sessionId/setup` | Same as above |
| `/session/:sessionId/engineer` | Same as above |
| `/settings` | Home / Settings |

For session-level breadcrumbs, the session's car/track info must be fetched (or read from TanStack Query cache if already loaded). This can use the existing `useSessions` hook data or a lightweight single-session fetch.
