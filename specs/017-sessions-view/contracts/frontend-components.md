# Frontend Component Contracts: Sessions List & Processing View

**Feature**: 017-sessions-view | **Date**: 2026-03-06

## Component Tree

```
AppShell.tsx (MODIFIED — adds selected session strip)
├── Sidebar (existing, unchanged)
├── SelectedSessionStrip (NEW — shown when a session is selected)
└── Active View
    └── SessionsView (REPLACED — full sessions list)
        ├── SessionCard (NEW — individual session entry)
        │   ├── Badge (existing — state indicator)
        │   └── ProgressBar (existing — processing progress)
        ├── EmptyState (existing — no sessions)
        └── Modal (existing — delete confirmation)
```

## New Components

### SessionsView (replaced)

**Purpose**: Main sessions list view. Fetches sessions, manages processing jobs and deletions.

**File**: `frontend/src/views/sessions/index.tsx`

**Internal state** (useState):
```typescript
// Maps session IDs to their processing job info
processingJobs: Map<string, ProcessingJobInfo>

// Session ID pending deletion (null = modal closed)
pendingDeleteId: string | null

// Whether a sync is in progress
isSyncing: boolean
```

**Behavior**:
- Fetches sessions via `useSessions()` hook (TanStack Query, 5s refetch)
- Renders header with title + Sync button
- If loading (first fetch): renders skeleton cards
- If error: renders EmptyState with error message and retry button
- If empty: renders EmptyState with guidance text
- If data: renders SessionCard list sorted by date descending
- Manages processing job lifecycle: start, track via useJobProgress, handle completion/failure
- Manages delete flow: pending ID → Modal → confirm/cancel
- CSS class prefix: `ace-sessions`

### SessionCard

**Purpose**: Individual session entry in the list. Displays metadata, state, and actions.

**File**: `frontend/src/views/sessions/SessionCard.tsx`

**Props**:
```typescript
interface SessionCardProps {
  session: SessionRecord;
  uiState: UISessionState;
  isSelected: boolean;
  jobProgress: JobProgress | undefined;
  jobError: string | null;
  onProcess: () => void;
  onSelect: () => void;
  onDelete: () => void;
}
```

**Behavior**:
- Wraps content in the existing `Card` component
- Shows: car name, track name, formatted date, lap count, state Badge
- Selected state: adds `ace-session-card--selected` class (visual highlight)
- State-dependent content:
  - **New**: "Process" button visible
  - **Processing**: ProgressBar + current step text, Process button disabled
  - **Ready**: click anywhere on card to select; shows ready Badge
  - **Engineered**: same as Ready but with Engineered Badge
  - **Failed**: error message text + "Retry" button
- Delete button (icon) always visible in card corner
- CSS class prefix: `ace-session-card`

### SelectedSessionStrip

**Purpose**: Persistent bar showing the active session's identity.

**Location**: Rendered inside `AppShell.tsx` between Sidebar and content area.

**Implementation**: Inline in AppShell.tsx (not a separate file — it's ~10 lines of JSX).

**Behavior**:
- Reads `selectedSessionId` and `clearSession` from `useSessionStore`
- Resolves session data directly from the TanStack Query cache — no props from AppShell:
  ```typescript
  const queryClient = useQueryClient();
  const sessions = queryClient.getQueryData<SessionListResponse>(["sessions"])?.sessions ?? [];
  const selectedSession = sessions.find(s => s.session_id === selectedSessionId);
  ```
- If `selectedSessionId` is null or the session is not found in the cache, returns `null` (renders nothing)
- Displays: car name + track name + close button
- Close button calls `clearSession()`
- Self-contained: no prop drilling required. AppShell only needs to render `<SelectedSessionStrip />` unconditionally — the strip handles its own visibility
- CSS class: `ace-session-strip` (added to AppShell.css)

## Modified Components

### AppShell.tsx

**Changes**:
- Render `<SelectedSessionStrip />` between sidebar and content area (unconditionally — the strip handles its own visibility internally via query cache + sessionStore)

### api.ts

**Changes**:
- Add `apiDelete` function:
```typescript
export function apiDelete(path: string): Promise<void> {
  return apiFetch<void>(path, { method: "DELETE" });
}
```
Note: DELETE /sessions/{id} returns 204 No Content, so the response parsing needs to handle empty bodies.

## New Hook

### useSessions

**Purpose**: TanStack Query wrapper for the sessions list.

**File**: `frontend/src/hooks/useSessions.ts`

```typescript
function useSessions(): {
  sessions: SessionRecord[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}
```

**Query config**:
- `queryKey: ["sessions"]`
- `refetchInterval: 5000` (5 seconds)
- `select`: extract `.sessions` from `SessionListResponse`

## New Types

### types.ts

**Purpose**: Shared TypeScript types for session-related API responses.

**File**: `frontend/src/lib/types.ts`

```typescript
export interface SessionRecord {
  session_id: string;
  car: string;
  track: string;
  session_date: string;
  lap_count: number;
  best_lap_time: number | null;
  state: string;
  session_type: string | null;
  csv_path: string | null;
  meta_path: string | null;
}

export interface SessionListResponse {
  sessions: SessionRecord[];
}

export interface ProcessResponse {
  job_id: string;
  session_id: string;
}

export interface SyncResult {
  discovered: number;
  already_known: number;
  incomplete: number;
}

export type UISessionState = "new" | "processing" | "ready" | "engineered" | "failed";

export interface ProcessingJobInfo {
  jobId: string;
  error: string | null;
}
```

## State Derivation Function

```typescript
function getUISessionState(
  session: SessionRecord,
  processingJobs: Map<string, ProcessingJobInfo>,
): UISessionState {
  // Check for active/failed processing job first
  const jobInfo = processingJobs.get(session.session_id);
  if (jobInfo) {
    if (jobInfo.error !== null) return "failed";
    return "processing";
  }

  // Map backend state
  switch (session.state) {
    case "analyzed": return "ready";
    case "engineered": return "engineered";
    case "discovered":
    case "parsed":
    default: return "new";
  }
}
```
