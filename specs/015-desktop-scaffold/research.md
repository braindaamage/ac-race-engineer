# Research: Desktop App Scaffolding, Design System & Backend Integration

**Branch**: `015-desktop-scaffold` | **Date**: 2026-03-05

## R1: Tauri v2 Sidecar Management

**Decision**: Use `@tauri-apps/plugin-shell` with `Command.sidecar().spawn()` to launch the backend as a long-running process, and `getCurrentWindow().onCloseRequested()` for clean shutdown.

**Rationale**: Tauri v2 replaced `@tauri-apps/api/shell` with `@tauri-apps/plugin-shell`. The sidecar pattern is the official way to bundle and manage external processes.

**Key findings**:

- **Sidecar declaration**: In `tauri.conf.json`, add `"externalBin": ["binaries/api-server"]` under `bundle`. Tauri expects the binary at `src-tauri/binaries/api-server-{target-triple}{ext}` (e.g., `api-server-x86_64-pc-windows-msvc.exe`). Get the target triple via `rustc --print host-tuple`.
- **For Python sidecars**: Since our backend is Python (not a compiled binary), production uses PyInstaller to bundle `python -m api.server` into a standalone `.exe` placed at the sidecar path. During development, a custom shell scope allows running Python directly.
- **Spawning** (use `.spawn()`, NOT `.execute()`):
  ```typescript
  const command = Command.sidecar('binaries/api-server', ['--port', '57832']);
  command.stdout.on('data', (line) => console.log(`[api-server] ${line}`));
  command.stderr.on('data', (line) => console.error(`[api-server] ${line}`));
  const child = await command.spawn();
  ```
- **Killing**: `await child.kill()` — called in the `onCloseRequested` handler.
- **Permissions**: Requires `shell:allow-spawn` + `shell:allow-kill` in `src-tauri/capabilities/default.json`. The spawn permission must include a sidecar scope with validated args:
  ```json
  {
    "identifier": "shell:allow-spawn",
    "allow": [{
      "name": "binaries/api-server",
      "sidecar": true,
      "args": ["--port", { "validator": "\\d+" }]
    }]
  }
  ```
- **Plugin installation**: `npm run tauri add shell` — adds Rust dep, registers plugin in `lib.rs`, installs npm package.
- **Clean shutdown flow**: `onCloseRequested` → `POST /shutdown` → brief wait → `child.kill()` → window closes.
- **Safety net**: Tauri auto-kills sidecar children on process exit, but explicit cleanup is more reliable.
- **Caveat**: `onCloseRequested` fires on user-initiated close (X button, Alt+F4) but NOT on programmatic `appWindow.close()`. If closing programmatically, kill child explicitly first.

**Alternatives considered**:
- Using Tauri's Rust `Command` in `src-tauri/src/main.rs`: More complex, requires Rust knowledge. Rejected per constitution (Principle X: minimal Rust config only).
- Spawning Python directly without sidecar packaging: Works for development only. Production needs PyInstaller bundling.

---

## R2: Project Initialization (Tauri v2 + React + TypeScript + Vite)

**Decision**: Use `cargo tauri init` inside the existing `frontend/` directory to add `src-tauri/` without regenerating the React scaffold.

**Rationale**: The project already has a `frontend/` directory designated for React. `cargo tauri init` adds only the Tauri shell (`src-tauri/`) to an existing frontend project, unlike `npm create tauri-app` which scaffolds the entire project from scratch.

**Key config files**:
- `frontend/src-tauri/tauri.conf.json` — app metadata, window config, bundle settings, build commands
- `frontend/src-tauri/Cargo.toml` — Rust dependencies (Tauri + plugins)
- `frontend/src-tauri/capabilities/default.json` — permission grants for plugins
- `frontend/src-tauri/src/lib.rs` — Tauri app builder (minimal Rust, plugin registration)
- `frontend/package.json` — npm dependencies
- `frontend/vite.config.ts` — Vite bundler config
- `frontend/tsconfig.json` — TypeScript strict mode config

**Critical vite.config.ts settings**:
- `server.port: 5173`, `server.strictPort: true`
- `server.host: process.env.TAURI_DEV_HOST`
- Build target: `'chrome105'` on Windows
- Exclude `src-tauri/**` from file watching

**Critical tauri.conf.json build section**:
```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  }
}
```

---

## R3: State Management Architecture

**Decision**: Three strictly separated layers as mandated by constitution Principle XII. Multiple small Zustand stores for independent UI concerns.

**Rationale**: Each layer has a clear responsibility and they must not be mixed. Multiple small Zustand stores give scoped subscriptions and fewer unnecessary re-renders versus a single monolithic store.

**Layer 1 — TanStack Query v5 (server/API state)**:
- All HTTP calls to the backend go through TanStack Query
- `queryClient` created once in the app root
- Analysis data uses `staleTime: Infinity` (immutable once fetched, per constitution Principle XII)
- Config data uses a shorter stale time since it can change
- Custom hooks: `useConfig()`, `useHealth()` — wrapping `useQuery`/`useMutation`
- **Critical anti-pattern to avoid**: Never copy server data into Zustand — read from `useQuery` hooks directly

**Layer 2 — Zustand v5 (global UI state)**:
- Multiple small independent stores:
  - `useUIStore` — `activeSection`, sidebar collapsed state
  - `useSessionStore` — `selectedSessionId`, selected lap index
  - `useThemeStore` — `theme` ID, `setTheme()` action
  - `useNotificationStore` — `notifications[]`, `addNotification()`, `removeNotification()`
  - `useJobStore` — `jobProgress{}`, `updateJobProgress()`, `removeJob()`
- No server data in Zustand — only UI concerns
- Subscriptions: components subscribe via selectors (e.g., `useUIStore(s => s.activeSection)`)
- When a Zustand value (e.g., `selectedSessionId`) drives a query, components read the ID from Zustand and pass it to `useQuery`

**Layer 3 — React useState (component-local)**:
- Hover states, dropdown open/closed, form inputs, animation states
- Never lifted to Zustand unless needed globally

**Alternatives considered**:
- Redux Toolkit: Heavier, not mandated by constitution. Rejected.
- Jotai/Recoil: Atomic state — good but constitution specifies Zustand. Rejected.
- Single Zustand store with slices: Viable but creates unnecessary coupling between independent domains. Multiple stores is cleaner when state domains are independent.

---

## R4: CSS Custom Properties Theming

**Decision**: Three-layer token architecture (primitives → semantic → component) in `tokens.css`. Two `[data-theme]` blocks redefine semantic tokens. Components use plain `.css` files with `ace-` class prefix for scoping.

**Rationale**: Constitution Principle XII mandates CSS custom properties as the only source of color values. A `data-theme` attribute on `<html>` switches the entire token set.

**Token architecture**:

| Layer | Purpose | Example |
|-------|---------|---------|
| Primitive | Raw values, no semantic meaning | `--gray-800: #1e293b` |
| Semantic | Purpose-driven, reference primitives | `--bg: var(--gray-800)` |
| Component | Scoped to a specific component (optional) | `--button-bg: var(--color-red)` |

Primitives are defined once globally. Semantic tokens are redefined per theme in `[data-theme="dark"]` and `[data-theme="light"]` selectors. Components reference semantic tokens so they automatically adapt.

**Token categories**:
- **Colors**: `--color-red`, `--color-blue-ai`, `--color-green`, `--color-amber`, `--bg`, `--bg-surface`, `--bg-elevated`, `--text-primary`, `--text-secondary`, `--text-muted`, `--border`, `--border-strong`
- **Typography**: `--font-ui` (Inter), `--font-mono` (JetBrains Mono), `--font-size-*`, `--font-weight-*`, `--line-height-*`
- **Spacing**: `--space-1` through `--space-12` (4px base scale)
- **Radius**: `--radius-sm`, `--radius-md`, `--radius-lg`
- **Shadows**: `--shadow-sm`, `--shadow-md`, `--shadow-lg` (redefined in dark theme for subtler shadows)
- **Transitions**: `--transition-fast`, `--transition-normal`

**Component styling**: Each component has a co-located `.css` file (e.g., `Button.css`) with `ace-` prefixed classes (e.g., `.ace-button`, `.ace-card--ai`). Global styles are in `index.css` which imports `tokens.css`.

**Alternatives considered**:
- CSS `@scope`: Now Baseline as of Dec 2025, provides native scoping without build tools. Considered but `ace-` prefix convention is simpler and doesn't require browser baseline assumptions in Tauri's webview.
- CSS Modules: Adds build-step coupling, hash-mangled class names make debugging harder. Rejected.
- Tailwind: Explicitly excluded by user input.
- Styled-components/Emotion: Runtime CSS-in-JS adds bundle size and complexity. Rejected.

---

## R5: Font Bundling

**Decision**: Bundle JetBrains Mono as `.woff2` files in `frontend/src/assets/fonts/`. Load via `@font-face` in `index.css`. Bundle Inter as well for offline reliability.

**Rationale**: JetBrains Mono must be a local asset (user requirement — no CDN). Tauri's webview runs with `tauri://localhost` origin, so only bundled fonts are accessible — CDN loading works but bundling is more reliable for a desktop app.

**Implementation**:
- Download JetBrains Mono Regular + Bold `.woff2` files
- Download Inter Regular + Medium + SemiBold + Bold `.woff2` files
- Place in `frontend/src/assets/fonts/`
- Declare `@font-face` in `index.css` with relative paths
- Vite includes font assets in the build output automatically
- Use `font-display: swap` for both fonts

**Caveat**: Do NOT try to load fonts from the OS filesystem at runtime — Tauri's sandboxed webview context prevents this.

---

## R6: Testing Strategy

**Decision**: Vitest + React Testing Library + jsdom. Fresh QueryClient per test. Zustand auto-reset via `vi.mock('zustand')`. Theme testing via `data-theme` attribute verification.

**Rationale**: Vitest integrates natively with Vite. React Testing Library tests user-facing behavior, not implementation details.

**Key patterns**:

- **TanStack Query testing**: Create a `createTestQueryClient()` utility returning `new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } })`. Each test gets its own client + `QueryClientProvider` wrapper for full isolation.
- **Zustand testing**: Use `vi.mock('zustand')` in a setup file with auto-reset between tests (official Zustand testing pattern). Create a `__mocks__/zustand.ts` file. Each test starts with clean store state.
- **Theme testing**: CSS custom properties are not computed in jsdom. Test at the behavioral level: verify `data-theme` attribute is set correctly, verify correct CSS classes are applied. Visual regression testing (Playwright screenshots) can cover actual appearance later.
- **Component variant testing**: Parameterized tests for each variant × both themes.
- **Shared test utilities**: `test-utils.ts` exports a custom `render` function that wraps components in all necessary providers.

**Alternatives considered**:
- Jest: slower, less native ESM support, conflicts with Vite. Rejected.
- Vitest Browser Mode: Would give real CSS computation but adds complexity; reserve for visual tests only.

---

## R7: WebSocket Reconnection

**Decision**: WebSocket manager as a module-level singleton (outside React), integrated with Zustand job/notification stores. Exponential backoff: 1s base, 2x multiplier, max 3 retries.

**Rationale**: The backend WebSocket is per-job (`/ws/jobs/{job_id}`), not a global stream. Each job gets its own connection. The WS manager must live outside React to avoid lifecycle issues from component mount/unmount.

**Pattern**:
- On job start, open `ws://127.0.0.1:57832/ws/jobs/{jobId}`
- On message: call `useJobStore.getState().updateJobProgress()` directly (Zustand supports external access)
- On `completed`/`failed` event: trigger notification via `useNotificationStore.getState().addNotification()`, close connection
- On unexpected close: retry with exponential backoff (delays: 1000ms, 2000ms, 4000ms) + random jitter (0-500ms)
- After 3 failed retries: add error notification "Live updates unavailable"
- On successful reconnect: reset retry counter

**`useJobProgress` hook**: Thin React wrapper that subscribes to `useJobStore` for a specific `jobId` and provides `startTracking(jobId)` / `stopTracking(jobId)` actions that delegate to the singleton WS manager.

**Alternatives considered**:
- `reconnecting-websocket` library: Adds a dependency for ~50 lines of code. Less control over Zustand integration. Rejected.
- Socket.IO: Overkill; backend uses raw WebSocket. Rejected.
- Managing WS inside a React hook: Anti-pattern — component unmount/remount causes spurious disconnections. Rejected.

---

## R8: Backend Changes Required

**Decision**: Two small backend additions are needed before the frontend can function fully.

### R8.1: POST /shutdown endpoint

The constitution (Principle X) mandates `POST /shutdown` before sidecar termination. This endpoint does not exist yet. It needs to:
- Trigger graceful server shutdown (call `server.should_exit = True` on the Uvicorn server)
- Return 200 immediately
- Be added to the health router (or a new lifecycle router)

### R8.2: `ui_theme` field in ACConfig

The config model has no `ui_theme` field. The frontend needs to persist theme preference. Options:
- **Add `ui_theme: str = "dark"` to ACConfig model** — requires updating the model, serializer, and API request model
- Use a separate preference store — over-engineered for one field

**Decision**: Add `ui_theme` to ACConfig. It's a user preference like `llm_provider`. Valid values: `"dark"`, `"light"`. Default: `"dark"`.

Changes needed:
- `backend/ac_engineer/config/models.py`: Add `ui_theme: str = "dark"` field + validator
- `backend/api/routes/config.py`: Add `ui_theme` to `ConfigResponse` and `ConfigUpdateRequest`
- Tests for both changes
