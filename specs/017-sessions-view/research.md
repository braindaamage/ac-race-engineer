# Research: Sessions List & Processing View

**Feature**: 017-sessions-view | **Date**: 2026-03-06

## R1: Session List Fetching & Auto-Refresh Strategy

**Decision**: Use TanStack Query with `queryKey: ["sessions"]` and `refetchInterval: 5000` for automatic list refresh. Manual sync triggers `POST /sessions/sync` then invalidates the query.

**Rationale**: The backend has a file watcher that detects new sessions on disk and saves them to the DB. The frontend doesn't receive push notifications for new sessions — it needs to poll. A 5-second refetch interval balances freshness with network efficiency. TanStack Query handles caching, deduplication, and background refetching automatically.

**Alternatives considered**:
- WebSocket for session list updates: The backend doesn't have a session discovery WebSocket — only job progress WebSockets exist. Adding one would be a backend change outside scope. Rejected.
- Manual refresh only: Poor UX — the user would have to click Sync every time they return from driving. Rejected.
- Longer polling interval (30s): Too slow — user expects to see new sessions quickly after a drive. 5s is responsive without being excessive.

## R2: Session State Mapping

**Decision**: Map backend states to UI states using a function that also considers active processing jobs and failed job state.

**State mapping**:

| Backend `state` | Active job? | Job failed? | UI Label | Badge Variant |
|----------------|-------------|-------------|----------|---------------|
| `discovered` | No | No | New | info |
| `discovered` | Yes | No | Processing | neutral |
| `parsed` | Yes | No | Processing | neutral |
| `parsed` | No | No | New | info |
| `parsed` | No | Yes | Failed | error |
| `analyzed` | - | - | Ready | success |
| `engineered` | - | - | Engineered | success |

**Rationale**: The `parsed` state is transient — it appears during processing between `discovered` and `analyzed`. If the job is still running, it's "Processing". If the job failed mid-way (after parsing but before analysis), the session is stuck in `parsed` with no active job — this should show as "New" (retryable) or "Failed" if the job error is known. The `discovered` state with an active job means processing just started (before the first DB state update).

**Job-to-session tracking**: A local `Map<sessionId, jobId>` in the SessionsView component tracks which sessions have active processing jobs. This is ephemeral — if the user refreshes the page, processing jobs are lost from the UI (but continue on the backend). This is acceptable because:
1. Processing is fast (seconds, not minutes)
2. The session's backend state will update to `analyzed` when done
3. The 5-second refetch will pick up the new state

## R3: Processing Flow

**Decision**: `POST /sessions/{id}/process` returns `{ job_id, session_id }`. The frontend stores the mapping and subscribes to the job via `useJobProgress(jobId)` which uses the existing `JobWSManager`.

**Flow**:
1. User clicks "Process" on a New session
2. Frontend calls `apiPost<ProcessResponse>("/sessions/{id}/process")`
3. On success: store `sessionId → jobId` mapping, start WebSocket tracking
4. WebSocket updates flow through `jobStore` → `useJobProgress` hook → UI re-renders
5. On job completion: invalidate `["sessions"]` query, show success toast, remove mapping
6. On job failure: show error toast, keep mapping so card shows Failed state with error

**Duplicate prevention**: The UI disables the Process button for sessions that have an active job in the local map. The backend also returns 409 if processing is already in progress for a session.

## R4: Selected Session Strip in AppShell

**Decision**: Add a small persistent bar between the Sidebar and the main content area in AppShell that shows the selected session's car and track when a session is active.

**Rationale**: FR-014 requires the selected session identity to be visible in a persistent location. The strip sits inside `AppShell.tsx` and reads from `useSessionStore`. When no session is selected, the strip is hidden (not rendered). The strip is minimal — just car name, track name, and a small "x" to deselect.

**Alternatives considered**:
- Show in Sidebar below the nav: Sidebar can be collapsed, making the info invisible. Rejected.
- Show in a breadcrumb at the top of each view: Would require changes to every view component. Rejected.

## R5: Delete Flow with apiDelete

**Decision**: Add `apiDelete` to `api.ts` (the existing fetch wrapper lacks a DELETE method). Delete flow uses `useState` for the pending-delete session ID and the existing `Modal` component for confirmation.

**Flow**:
1. User clicks delete icon on a session card
2. `pendingDeleteId` state is set, Modal opens with confirmation text
3. User confirms → `DELETE /sessions/{id}` (204 No Content)
4. On success: invalidate `["sessions"]`, clear `pendingDeleteId`, if deleted session was `selectedSessionId` call `clearSession()`
5. User cancels → clear `pendingDeleteId`, Modal closes

## R6: Empty State Content

**Decision**: When the session list is empty, show the existing `EmptyState` component with a message explaining that sessions are created by the in-game AC app during driving.

**Content**:
- Icon: clipboard/racing icon
- Title: "No sessions recorded yet"
- Description: "Sessions are recorded automatically while you drive in Assetto Corsa. Make sure the AC Race Engineer app is installed in your Assetto Corsa folder, then go for a drive!"
- Action button: None (there's no user action to take — sessions appear automatically)

## R7: Error Handling

**Decision**: Backend connectivity errors are handled by TanStack Query's error state. The view shows an error message with a "Retry" button when the query fails.

**Rationale**: TanStack Query provides `isError` and `error` on the query result. The UI renders an error state (using the existing EmptyState component with error styling) when `isError` is true. The refetch button maps to `refetch()` from the query.
