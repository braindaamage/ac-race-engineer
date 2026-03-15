# Quick Start: Navigation Shell & Visual Refresh

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15

## Prerequisites

- Node.js 20 LTS
- npm (frontend package manager)
- Rust + Cargo (for Tauri icon generation)
- Tauri CLI: `cargo install tauri-cli` (or via `npx @tauri-apps/cli`)

## Setup

```bash
cd frontend
npm install
npm install react-router-dom@^7
npm install @fortawesome/fontawesome-free
```

## Development

```bash
cd frontend
npm run dev          # Vite dev server (hot reload)
npx tsc --noEmit     # TypeScript strict check
npm run test         # Vitest test suite
```

## Key Files to Edit (in order)

### 1. Design tokens & visual foundation
- `src/tokens.css` — Update primitive color values
- Fix undefined token refs in 7 CSS files (see contracts/tokens.md)
- Copy `prototypes/logo.png` → `src/assets/logo.png`
- Import `@fortawesome/fontawesome-free/css/all.min.css` in entry point

### 2. Router setup
- Create `src/router.tsx` — Route tree with `createBrowserRouter`
- Modify `src/App.tsx` — Integrate `RouterProvider`
- Modify `src/main.tsx` — Ensure router is inside `QueryClientProvider`

### 3. Layout components
- Rewrite `src/components/layout/AppShell.tsx` — Header + Outlet + Toast
- Create `src/components/layout/Header.tsx` — Logo + Breadcrumb + Settings
- Create `src/components/layout/Breadcrumb.tsx` — Dynamic path segments
- Create `src/components/layout/TabBar.tsx` — Contextual tabs
- Create `src/components/layout/SessionLayout.tsx` — Session tab wrapper
- Delete `src/components/layout/Sidebar.tsx` + `.css`
- Update `src/components/layout/SplashScreen.tsx` — New logo

### 4. View adaptations
- `src/views/garage/index.tsx` — New placeholder
- `src/views/tracks/index.tsx` — New placeholder
- Modify existing views to get sessionId from `useParams()` instead of sessionStore
- Modify SessionsView to receive carId+trackId from route params
- Modify SettingsView to remove uiStore navigation interception

### 5. State cleanup
- Remove or empty `src/store/uiStore.ts`
- Remove `src/store/sessionStore.ts`

### 6. Tauri icons
```bash
cd frontend
npx @tauri-apps/cli icon src/assets/logo.png
```

### 7. Tests
- Delete `tests/components/layout/Sidebar.test.tsx`
- Rewrite `tests/components/layout/AppShell.test.tsx`
- Create tests for Header, Breadcrumb, TabBar, SessionLayout, router
- Adapt view tests to use `createMemoryRouter` pattern

## Test Helper Pattern

```typescript
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";

function renderWithRouter(
  element: React.ReactElement,
  { route = "/", path = "/" }: { route?: string; path?: string } = {}
) {
  const router = createMemoryRouter(
    [{ path, element }],
    { initialEntries: [route] }
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
```

## Verification Checklist

- [ ] `npm run dev` — app starts, shows splash screen, then Garage Home
- [ ] Navigate full hierarchy: Garage → Car → Track → Session → Tab
- [ ] Breadcrumb updates at each level, each segment clickable
- [ ] Browser back/forward works at every level
- [ ] Copy URL, paste in new tab → same view loads
- [ ] Settings accessible from header icon on every page
- [ ] Dark and light themes show new brand colors
- [ ] Logo visible in header and splash screen
- [ ] No emoji icons visible — all replaced with Font Awesome
- [ ] `npx tsc --noEmit` — zero type errors
- [ ] `npm run test` — all tests pass
- [ ] Taskbar/start menu icon shows new logo (after Tauri icon regen)
