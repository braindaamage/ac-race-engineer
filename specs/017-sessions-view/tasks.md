# Tasks: Sessions List & Processing View

**Input**: Design documents from `/specs/017-sessions-view/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/frontend-components.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Infrastructure (Blocking Prerequisites)

**Purpose**: Shared types, API utilities, and data-fetching hook that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 [P] Create shared session types in `frontend/src/lib/types.ts` — export interfaces: `SessionRecord` (session_id, car, track, session_date, lap_count, best_lap_time, state, session_type, csv_path, meta_path), `SessionListResponse` ({ sessions: SessionRecord[] }), `ProcessResponse` ({ job_id, session_id }), `SyncResult` ({ discovered, already_known, incomplete }), `ProcessingJobInfo` ({ jobId: string, error: string | null }), and type `UISessionState = "new" | "processing" | "ready" | "engineered" | "failed"`
- [x] T002 [P] Add `apiDelete` function to `frontend/src/lib/api.ts` — the existing `apiFetch` always calls `resp.json()` which fails on 204 No Content. Add a dedicated `apiDelete(path: string): Promise<void>` that does a DELETE fetch and does NOT parse the response body. Export it alongside apiGet/apiPatch/apiPost
- [x] T003 Create `useSessions` TanStack Query hook in `frontend/src/hooks/useSessions.ts` — import `apiGet` and `SessionListResponse`/`SessionRecord` from types.ts. Use `useQuery` with `queryKey: ["sessions"]`, `queryFn: () => apiGet<SessionListResponse>("/sessions")`, `refetchInterval: 5000`, `select: (data) => data.sessions`. Return `{ sessions: SessionRecord[], isLoading, error, refetch }`. Handle `sessions` defaulting to `[]` when data is undefined

**Checkpoint**: Types defined, API layer complete, sessions hook ready for use

---

## Phase 2: User Story 1 — View All Sessions (Priority: P1)

**Goal**: Display all sessions in a scrollable list sorted by date descending, with state badges and empty/error states

**Independent Test**: Open the Sessions view and verify all sessions appear with correct metadata, badges show correct state labels, empty state shows guidance when no sessions exist

### Tests for User Story 1

- [x] T004 [P] [US1] Write SessionCard unit tests in `frontend/tests/views/sessions/SessionCard.test.tsx` — mock no external modules (pure presentational). Test: renders car name, track name, formatted date, and lap count from session prop; renders Badge with variant "info" and text "New" when uiState="new"; renders Badge "success"/"Ready" for uiState="ready"; renders Badge "success"/"Engineered" for uiState="engineered"; adds CSS class `ace-session-card--selected` when isSelected=true; calls onSelect when card is clicked and uiState is "ready" or "engineered"; does NOT call onSelect when uiState is "new"/"processing"/"failed"; calls onDelete when delete button is clicked; shows "Process" button when uiState is "new" that calls onProcess. Use test pattern: `import { render, screen, fireEvent } from "@testing-library/react"`
- [x] T005 [P] [US1] Write SessionsView integration tests in `frontend/tests/views/sessions/SessionsView.test.tsx` — mock `frontend/src/lib/api` (apiGet, apiPost, apiDelete), mock `frontend/src/hooks/useJobProgress`, mock `frontend/src/store/sessionStore` (useSessionStore). Tests: renders session list from mocked GET /sessions response; sessions sorted by date descending; shows Skeleton components while loading (first fetch); shows EmptyState with "No sessions recorded yet" when sessions array is empty; shows error EmptyState with retry button when query fails; Sync button is visible. Use `renderWithQuery` pattern from SettingsView.test.tsx (inline QueryClientProvider with retry:false)

### Implementation for User Story 1

- [x] T006 [US1] Create `getUISessionState()` utility in `frontend/src/views/sessions/utils.ts` (new file). Export a single function: `getUISessionState(session: SessionRecord, processingJobs: Map<string, ProcessingJobInfo>): UISessionState`. Logic: check `processingJobs.get(session.session_id)` first — if entry exists with `error !== null` return `"failed"`, if entry exists with `error === null` return `"processing"`; then switch on `session.state`: `"analyzed"` → `"ready"`, `"engineered"` → `"engineered"`, default (including `"discovered"` and `"parsed"`) → `"new"`. T007 and T009 import `getUISessionState` from `./utils`
- [x] T007 [P] [US1] Create SessionCard component in `frontend/src/views/sessions/SessionCard.tsx` — props: `SessionCardProps` per contracts (session, uiState, isSelected, jobProgress, jobError, onProcess, onSelect, onDelete). Wrap in existing `Card` component. Display: car name (format: replace underscores with spaces, strip "ks_" prefix if present), track name (same formatting), session_date (format as locale date string), lap_count with "laps" label, Badge for state (variant mapping: new→info, processing→neutral, ready→success, engineered→success, failed→error; label mapping: new→"New", processing→"Processing", ready→"Ready", engineered→"Engineered", failed→"Failed"). Show "Process" Button when uiState is "new", show ProgressBar + currentStep text when "processing", show error text + "Retry" Button when "failed". Card click calls onSelect only when uiState is "ready" or "engineered". Delete icon button in top-right corner calls onDelete (use "x" or trash icon character). CSS class prefix: `ace-session-card`
- [x] T008 [P] [US1] Create styles in `frontend/src/views/sessions/SessionsView.css` — classes: `.ace-sessions` (container, max-width ~960px, margin auto, padding), `.ace-sessions__header` (flex row, space-between, title + sync button), `.ace-sessions__list` (flex column, gap using --spacing-md token), `.ace-session-card` (cursor pointer, transition border-color), `.ace-session-card--selected` (border-left: 3px solid var(--color-brand), background var(--bg-elevated)), `.ace-session-card__meta` (flex row, gap, secondary text color), `.ace-session-card__actions` (flex row, gap), `.ace-session-card__delete` (ghost button, top-right absolute or flex-end), `.ace-session-card__error` (color var(--color-error), font-size small), `.ace-session-card__progress` (flex column, gap-sm for progress bar + step text). All colors via design tokens, `ace-` prefix. Note: `.ace-session-strip` styles go in AppShell.css (see T018), not here
- [x] T009 [US1] Replace SessionsView in `frontend/src/views/sessions/index.tsx` — import useSessions, SessionCard, getUISessionState, CSS. Add `useState<Map<string, ProcessingJobInfo>>` for processingJobs (initially empty), `useState<string | null>` for pendingDeleteId, `useState<boolean>` for isSyncing. Render: header with "Sessions" title + Sync button. If `isLoading` (first fetch): render 3 Skeleton cards (variant="rect", height ~100px). If `error`: render EmptyState with error message and action button calling `refetch()`. If `sessions.length === 0`: render EmptyState with icon, title "No sessions recorded yet", description about in-game app recording. If sessions exist: sort by `session_date` descending, map to SessionCard with `uiState` from getUISessionState, `isSelected` from sessionStore comparison. Import SessionsView.css

**Checkpoint**: Sessions appear in a list with metadata and state badges. Empty and error states work. Loading shows skeletons.

---

## Phase 3: User Story 2 — Process a Session (Priority: P1)

**Goal**: Trigger processing on "New" sessions, show real-time progress via WebSocket, handle success/failure with toasts

**Independent Test**: Click Process on a New session, observe progress bar updating in real-time, verify session transitions to Ready on completion or shows Failed with error on failure

### Tests for User Story 2

- [x] T010 [P] [US2] Add processing tests to `frontend/tests/views/sessions/SessionsView.test.tsx` — tests: clicking "Process" button on a New session card calls `apiPost` with `/sessions/{id}/process`; after successful process call, `jobWSManager.trackJob` is called with the returned job_id (mock `frontend/src/lib/wsManager`); when job completes (mock jobStore state to show completed), sessions query is refetched; when job fails, error toast appears (verify via notificationStore). Also test: Process button is not rendered on "Ready" sessions; clicking Retry on failed sessions triggers a new process call
- [x] T011 [P] [US2] Add processing state tests to `frontend/tests/views/sessions/SessionCard.test.tsx` — tests: renders ProgressBar when uiState="processing" with correct value from jobProgress.progress; renders currentStep text below progress bar; renders error message text when uiState="failed" showing jobError string; renders "Retry" button when uiState="failed" that calls onProcess; "Process" button is not rendered when uiState="processing" (replaced by progress bar)

### Implementation for User Story 2

- [x] T012 [US2] Add processing job management to SessionsView in `frontend/src/views/sessions/index.tsx` — import `jobWSManager` from `frontend/src/lib/wsManager`, `useJobStore` from `frontend/src/store/jobStore`, `useNotificationStore` from `frontend/src/store/notificationStore`, `useQueryClient` from `@tanstack/react-query`, `apiPost` and `ProcessResponse` type. Add `handleProcess(sessionId: string)` async function: call `apiPost<ProcessResponse>(\`/sessions/${sessionId}/process\`)`, on success store `{ jobId: response.job_id, error: null }` in processingJobs map and call `jobWSManager.trackJob(response.job_id)`. Read all job progress from `useJobStore(s => s.jobProgress)`. Add a `useEffect` that watches jobProgress entries: for each entry in processingJobs map, check if jobProgress[jobId] has status "completed" → call `queryClient.invalidateQueries({ queryKey: ["sessions"] })`, remove from processingJobs map, call `jobWSManager.stopTracking(jobId)`; if status "failed" → update processingJobs map entry with error from jobProgress, call `jobWSManager.stopTracking(jobId)`, show error notification. Pass `handleProcess` as `onProcess` prop to SessionCard. Dependency array for the useEffect: `[jobProgress]`. Do NOT include `processingJobs` in the dependency array. Read the current processingJobs value inside the effect using the functional updater form of setProcessingJobs: `setProcessingJobs(prev => { const next = new Map(prev); /* mutations on next */ return next; })`. This avoids the stale closure / infinite re-render cycle that would occur if processingJobs were both a dependency and mutated inside the effect
- [x] T013 [US2] Wire processing UI in SessionCard — in `frontend/src/views/sessions/SessionCard.tsx`: when `uiState === "processing"` and `jobProgress` is defined, render ProgressBar with `value={jobProgress.progress}` and show `jobProgress.currentStep` as text below. When `uiState === "failed"`, render error message from `jobError` prop in `ace-session-card__error` div, and render "Retry" Button that calls `onProcess`. When `uiState === "new"`, render "Process" Button that calls `onProcess`

**Checkpoint**: Full processing flow works end-to-end: click Process → real-time progress bar → success toast + transition to Ready, or error toast + Failed state with Retry.

---

## Phase 4: User Story 3 — Select a Session (Priority: P1)

**Goal**: Click a Ready/Engineered session to select it as active, highlight it, unlock sidebar items, show session identity in AppShell strip

**Independent Test**: Click a Ready session — it's highlighted, sidebar Lap Analysis/Setup Compare/Engineer items are enabled, session strip shows car + track

### Tests for User Story 3

- [x] T014 [P] [US3] Add selection tests to `frontend/tests/views/sessions/SessionsView.test.tsx` — tests: clicking a "Ready" session card calls `useSessionStore.getState().selectSession(id)`; clicking a "New" session card does NOT call selectSession; the session matching selectedSessionId has `isSelected=true` passed to its SessionCard
- [x] T015 [P] [US3] Write AppShell session strip tests in `frontend/tests/components/layout/AppShell.test.tsx` — mock `frontend/src/store/sessionStore` and `frontend/src/store/uiStore`. The strip is self-contained: it reads selectedSessionId from sessionStore and resolves session data from the TanStack Query cache via `useQueryClient().getQueryData(["sessions"])`. In tests, pre-populate the QueryClient cache with test session data using `queryClient.setQueryData(["sessions"], { sessions: [...] })` before rendering. Tests: when selectedSessionId is null, no element with class `ace-session-strip` is rendered; when selectedSessionId is set and matching session exists in cache, strip shows car name and track name; clicking close button in strip calls `clearSession()`; strip renders between sidebar and content area. Use renderWithQuery pattern (pass the pre-populated queryClient)

### Implementation for User Story 3

- [x] T016 [US3] Add selection handling to SessionsView in `frontend/src/views/sessions/index.tsx` — import `useSessionStore`. Read `selectedSessionId` and `selectSession` from store. In the SessionCard map, pass `isSelected={session.session_id === selectedSessionId}`. Define `handleSelect(sessionId: string)` that calls `selectSession(sessionId)`. Pass `onSelect={() => handleSelect(session.session_id)}` — SessionCard already prevents selection for non-ready states via its internal click logic
- [x] T017 [US3] Add self-contained SelectedSessionStrip to `frontend/src/components/layout/AppShell.tsx` — define a `SelectedSessionStrip` function component inline in AppShell.tsx (~10 lines). It imports `useSessionStore`, `useQueryClient` from `@tanstack/react-query`, and `SessionListResponse` from types.ts. Implementation: read `selectedSessionId` and `clearSession` from sessionStore; read session data from query cache via `const sessions = queryClient.getQueryData<SessionListResponse>(["sessions"])?.sessions ?? []`; find matching session with `sessions.find(s => s.session_id === selectedSessionId)`; if `selectedSessionId` is null or session not found in cache, return `null`. Otherwise render `<div className="ace-session-strip">` with car name, track name (formatted: replace underscores with spaces, strip "ks_" prefix), and a close button calling `clearSession()`. In the AppShell component, render `<SelectedSessionStrip />` unconditionally between Sidebar and the content div — no props, no conditional rendering in AppShell itself. The strip handles its own visibility internally
- [x] T018 [US3] Add strip styles to `frontend/src/components/layout/AppShell.css` — add: `.ace-session-strip` (height ~36px, display flex, align-items center, gap var(--spacing-md), padding 0 var(--spacing-md), background var(--bg-elevated), border-bottom 1px solid var(--border), font-size var(--font-size-sm), color var(--text-secondary)). `.ace-session-strip__label` (font-weight 500, color var(--text-primary)). `.ace-session-strip__close` (margin-left auto, background none, border none, cursor pointer, color var(--text-muted), hover color var(--text-primary))

**Checkpoint**: Selecting a Ready/Engineered session highlights it in the list, shows car+track in the persistent strip, and enables sidebar items (sidebar already reads from sessionStore).

---

## Phase 5: User Story 4 — Auto-Detect New Sessions (Priority: P2)

**Goal**: Session list auto-refreshes every 5 seconds (already configured in T003); Sync button forces immediate backend rescan

**Independent Test**: Sync button triggers `POST /sessions/sync`, list updates, toast shows result count

### Tests for User Story 4

- [x] T019 [P] [US4] Add sync button tests to `frontend/tests/views/sessions/SessionsView.test.tsx` — tests: clicking "Sync" button calls `apiPost` with `/sessions/sync`; Sync button shows loading/disabled state while request is in-flight; after sync completes, sessions query is refetched; toast notification appears with sync result (e.g., "Found 2 new sessions" when discovered > 0, "All sessions up to date" when discovered === 0)
- [x] T020 [P] [US4] Add auto-refresh test to `frontend/tests/hooks/useSessions.test.tsx` — mock `frontend/src/lib/api`. Test: useSessions hook returns sessions from mocked apiGet; verify the hook is configured with refetchInterval (test by checking that after the interval, apiGet is called again — use fake timers). Use `renderHook` from `@testing-library/react` with QueryClientProvider wrapper

### Implementation for User Story 4

- [x] T021 [US4] Add Sync button handler to SessionsView in `frontend/src/views/sessions/index.tsx` — `handleSync` async function: set `isSyncing` to true, call `apiPost<SyncResult>("/sessions/sync")`, on success call `queryClient.invalidateQueries({ queryKey: ["sessions"] })` and show notification (if discovered > 0: `"Found ${result.discovered} new session(s)"` as "success", else `"All sessions up to date"` as "info"), set `isSyncing` to false in finally block. Render Sync Button in header: variant="secondary", disabled when isSyncing, text "Sync" (or "Syncing..." when isSyncing)

**Checkpoint**: Auto-refresh already works from T003 (refetchInterval: 5000). Sync button provides manual override with feedback.

---

## Phase 6: User Story 5 — Delete a Session (Priority: P3)

**Goal**: Delete sessions with confirmation Modal dialog, clear active selection if the deleted session was selected

**Independent Test**: Click delete on a session, confirm in Modal, session disappears from list, files remain on disk

### Tests for User Story 5

- [x] T022 [P] [US5] Add delete tests to `frontend/tests/views/sessions/SessionsView.test.tsx` — tests: clicking delete button on a session card sets pendingDeleteId and opens Modal with confirmation text (e.g., "Delete session [car] at [track]?"); clicking confirm in Modal calls `apiDelete` with `/sessions/{id}`; after successful delete, sessions query is refetched and Modal closes; clicking cancel in Modal closes it without calling apiDelete; if the deleted session was selectedSessionId, `clearSession()` is called after deletion

### Implementation for User Story 5

- [x] T023 [US5] Add delete flow to SessionsView in `frontend/src/views/sessions/index.tsx` — import `apiDelete` from api.ts and `Modal` from components/ui. Define `handleDelete(sessionId: string)` that sets `pendingDeleteId` state. Define `confirmDelete` async function: call `apiDelete(\`/sessions/${pendingDeleteId}\`)`, on success invalidate `["sessions"]` query, check if `pendingDeleteId === selectedSessionId` and call `clearSession()` if so, set `pendingDeleteId` to null. Define `cancelDelete` that sets `pendingDeleteId` to null. Render `<Modal open={pendingDeleteId !== null} onClose={cancelDelete} title="Delete Session" actions={{ confirm: { label: "Delete", onClick: confirmDelete, variant: "primary" }, cancel: { label: "Cancel", onClick: cancelDelete } }}>` with body text showing the session car/track being deleted. Pass `onDelete={() => handleDelete(session.session_id)}` to each SessionCard

**Checkpoint**: Delete flow complete with confirmation Modal. Active selection cleared if needed.

---

## Phase 7: Polish & Validation

**Purpose**: Final validation across the entire feature

- [x] T024 Run `cd /c/Users/leona/Development/ac-race-engineer/frontend && npx tsc --noEmit` — fix any TypeScript strict mode errors across all new and modified files
- [x] T025 Run `cd /c/Users/leona/Development/ac-race-engineer/frontend && npm run test` — verify all tests pass (existing 146 + new session tests). Fix any failures
- [x] T026 Run `conda run -n ac-race-engineer pytest backend/tests/ -v` — verify no backend regressions (779 tests should all pass, no changes expected)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Infrastructure)**: No dependencies — start immediately
- **Phase 2 (US1 - View)**: Depends on Phase 1 (needs types.ts and useSessions hook)
- **Phase 3 (US2 - Process)**: Depends on Phase 2 (needs SessionCard component and SessionsView structure)
- **Phase 4 (US3 - Select)**: Depends on Phase 2 (needs SessionCard and SessionsView). Can run in parallel with Phase 3 if different developer, but both modify SessionsView — serialize for single developer
- **Phase 5 (US4 - Sync)**: Depends on Phase 2 (needs SessionsView header area). Auto-refresh already configured in T003
- **Phase 6 (US5 - Delete)**: Depends on Phase 2 (needs SessionCard and SessionsView). Can run after Phase 3/4/5
- **Phase 7 (Polish)**: Depends on all previous phases

### Within Each Phase

- Tasks marked [P] can run in parallel (different files, no dependencies)
- Test tasks and their corresponding implementation tasks are within the same phase — write tests first, then implement
- Implementation tasks within a phase are sequential unless marked [P]

### Parallel Opportunities

- T001, T002 can run in parallel (different files: types.ts vs api.ts)
- T004, T005 can run in parallel (different test files)
- T007, T008 can run in parallel (different files: SessionCard.tsx vs SessionsView.css)
- T010, T011 can run in parallel (different test files)
- T014, T015 can run in parallel (different test files)
- T019, T020 can run in parallel (different test files)

### Implementation Strategy

#### MVP First (User Story 1 Only)

1. Complete Phase 1: Infrastructure (T001-T003)
2. Complete Phase 2: US1 View (T004-T009)
3. **STOP and VALIDATE**: Session list renders, empty state works, skeletons show during loading

#### Incremental Delivery

1. Phase 1 + Phase 2 → Sessions visible in list (MVP)
2. Add Phase 3 → Processing works with real-time progress
3. Add Phase 4 → Session selection unlocks sidebar + strip shows
4. Add Phase 5 → Sync button works, auto-refresh confirmed
5. Add Phase 6 → Delete with confirmation
6. Phase 7 → Full validation pass

Each story adds value without breaking previous stories.
