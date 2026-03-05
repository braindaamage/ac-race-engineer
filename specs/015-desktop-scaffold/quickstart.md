# Quickstart: Desktop App Development

**Branch**: `015-desktop-scaffold` | **Date**: 2026-03-05

## Prerequisites

- Node.js 20 LTS or higher
- Rust toolchain (for Tauri compilation)
- conda env `ac-race-engineer` with backend dependencies installed
- Backend API running (or let Tauri launch it as sidecar)

## Setup

```bash
# Clone and switch to feature branch
git checkout 015-desktop-scaffold

# Install frontend dependencies
cd frontend
npm install

# Start development
npm run dev          # Vite dev server only (for UI work without Tauri)
npm run tauri dev    # Full Tauri + Vite + sidecar (for integration testing)
```

## Development Modes

### UI-only development (fast iteration)
```bash
cd frontend
npm run dev
```
- Vite dev server at `http://localhost:5173`
- Requires backend running separately: `conda activate ac-race-engineer && python -m api.server --port 57832`
- Hot module replacement for instant feedback

### Full app development (with Tauri shell)
```bash
cd frontend
npm run tauri dev
```
- Tauri launches the native window + sidecar backend
- Slower rebuild but tests the full integration

## Project Structure

```
frontend/
├── src/
│   ├── assets/
│   │   └── fonts/           # JetBrains Mono .woff2 files
│   ├── components/
│   │   ├── ui/              # Design system components
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
│   │   │   └── index.ts     # Barrel export
│   │   └── layout/
│   │       ├── AppShell.tsx + AppShell.css
│   │       ├── Sidebar.tsx + Sidebar.css
│   │       └── SplashScreen.tsx + SplashScreen.css
│   ├── hooks/
│   │   ├── useBackendStatus.ts
│   │   ├── useJobProgress.ts
│   │   └── useTheme.ts
│   ├── store/
│   │   ├── uiStore.ts       # activeSection, sidebar state
│   │   ├── sessionStore.ts  # selectedSessionId
│   │   ├── themeStore.ts    # theme ID, setTheme
│   │   ├── notificationStore.ts # notifications[], add/remove
│   │   └── jobStore.ts      # jobProgress tracking
│   ├── lib/
│   │   ├── api.ts           # HTTP client (fetch wrapper)
│   │   └── constants.ts     # API base URL, ports, timing constants
│   ├── views/
│   │   ├── sessions/
│   │   │   └── index.tsx
│   │   ├── analysis/
│   │   │   └── index.tsx
│   │   ├── compare/
│   │   │   └── index.tsx
│   │   ├── engineer/
│   │   │   └── index.tsx
│   │   └── settings/
│   │       └── index.tsx
│   ├── tokens.css           # Design tokens (both themes)
│   ├── index.css            # Global styles + font-face
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
├── src-tauri/
│   ├── src/
│   │   └── lib.rs           # Tauri app builder (minimal)
│   ├── capabilities/
│   │   └── default.json     # Plugin permissions
│   ├── tauri.conf.json      # App config
│   └── Cargo.toml           # Rust dependencies
├── tests/
│   ├── setup.ts             # Test setup (theme injection, providers)
│   └── components/
│       └── ui/              # Component tests
├── package.json
├── vite.config.ts
├── tsconfig.json
└── vitest.config.ts
```

## Key Commands

```bash
npm run dev          # Start Vite dev server
npm run build        # Build frontend for production
npm run tauri dev    # Launch full Tauri app in dev mode
npm run tauri build  # Build distributable app
npm run test         # Run Vitest tests
npm run test:watch   # Run tests in watch mode
npm run typecheck    # Run tsc --noEmit (strict mode validation)
```

## Running Tests

```bash
cd frontend
npm run test                    # All tests
npm run test -- Button          # Tests matching "Button"
npm run test -- --coverage      # With coverage report
```

## Adding a New Design System Component

1. Create `src/components/ui/NewComponent.tsx` and `NewComponent.css`
2. Use only design tokens from `tokens.css` for colors/spacing
3. Export from `src/components/ui/index.ts`
4. Add tests in `tests/components/ui/NewComponent.test.tsx`
5. Test all variants in both themes
