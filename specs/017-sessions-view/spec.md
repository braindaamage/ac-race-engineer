# Feature Specification: Sessions List & Processing View

**Feature Branch**: `017-sessions-view`
**Created**: 2026-03-06
**Status**: Draft
**Input**: Phase 7.3 — Sessions List & Processing view for the AC Race Engineer desktop application

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View All Sessions (Priority: P1)

The user opens the desktop application and navigates to the Sessions section. They see a list of all their recorded driving sessions, sorted by date with the newest session at the top. Each session card shows the car name, track name, date, number of laps, and the session's current processing state. The list loads quickly and gives the user an immediate overview of all their recorded data.

**Why this priority**: This is the foundation of the entire view — without a visible session list, nothing else works. Every other feature depends on the user being able to see and identify their sessions.

**Independent Test**: Can be fully tested by verifying that all sessions returned by the backend appear in the list with correct metadata displayed in the right order.

**Acceptance Scenarios**:

1. **Given** the backend has 5 recorded sessions, **When** the user opens the Sessions view, **Then** all 5 sessions appear in the list sorted by date (newest first), each showing car, track, date, lap count, and state
2. **Given** the backend has sessions in different states (discovered, analyzed, engineered), **When** the user views the list, **Then** each session displays a visual state indicator using user-friendly labels: "New" for discovered, "Ready" for analyzed, "Engineered" for engineered
3. **Given** the backend has no sessions, **When** the user opens the Sessions view, **Then** an empty state is shown explaining that sessions are recorded automatically by the in-game app while driving in Assetto Corsa, with guidance on how to get started

---

### User Story 2 - Process a Session (Priority: P1)

The user sees a session in the "New" state and wants to analyze it. They click the session and are offered a "Process" action. Once triggered, the session enters a "Processing" state with a progress indicator that updates in real time as backend steps complete. When processing finishes, the session transitions to "Ready" and a success notification appears. If processing fails, the session shows a "Failed" state with an error message and a "Retry" button.

**Why this priority**: Processing is the gateway to all analytical features. Without it, sessions stay in "New" forever and the user cannot do any analysis, compare setups, or talk to the Engineer.

**Independent Test**: Can be tested by triggering processing on a "New" session, observing real-time progress updates, and verifying the session transitions to "Ready" on success or "Failed" on error.

**Acceptance Scenarios**:

1. **Given** a session in "New" state, **When** the user clicks the session, **Then** a "Process" action is available
2. **Given** processing has been triggered, **When** the backend reports progress, **Then** the session card shows a progress indicator (percentage and/or current step name) that updates in real time
3. **Given** processing completes successfully, **When** the backend signals completion, **Then** the session transitions to "Ready" and a success notification appears
4. **Given** processing fails, **When** the backend signals an error, **Then** the session shows a "Failed" state with the error message and a "Retry" button
5. **Given** a session in "Failed" state, **When** the user clicks "Retry", **Then** processing starts again from scratch
6. **Given** processing is already running for a session, **When** the user attempts to process it again, **Then** a duplicate request is prevented (the action is disabled or hidden)

---

### User Story 3 - Select a Session (Priority: P1)

The user clicks on a session that has been processed ("Ready" or "Engineered") to select it as the active session. The selected session is visually highlighted in the list. Once a session is selected, the Lap Analysis, Setup Compare, and Engineer sections in the sidebar become accessible (no longer dimmed). The selected session's car and track name appear in the interface so the user always knows what they're working with.

**Why this priority**: Session selection is what connects the Sessions view to every other view in the app. Without selection, the rest of the app remains locked.

**Independent Test**: Can be tested by clicking a "Ready" session and verifying it becomes highlighted, sidebar items are enabled, and the session identity is shown.

**Acceptance Scenarios**:

1. **Given** a session in "Ready" or "Engineered" state, **When** the user clicks it, **Then** the session is visually highlighted as selected
2. **Given** a session has been selected, **When** the user looks at the sidebar, **Then** Lap Analysis, Setup Compare, and Engineer items are no longer dimmed and are clickable
3. **Given** a session is selected, **When** the user selects a different session, **Then** the previous selection is deselected and the new one is highlighted
4. **Given** a session in "New", "Processing", or "Failed" state, **When** the user clicks it, **Then** it is NOT selected as the active session (only process/retry actions are available)

---

### User Story 4 - Auto-Detect New Sessions (Priority: P2)

When the user records a new session in Assetto Corsa, the session appears in the list automatically without requiring the user to manually refresh. A manual "Sync" button is also available if the user wants to force a rescan of the sessions directory.

**Why this priority**: Automatic detection is important for a smooth user experience, but the core functionality works without it (the user can always use the Sync button). This is enhancement-level priority.

**Independent Test**: Can be tested by placing a new session file on disk and verifying it appears in the list, or by clicking Sync and verifying the list updates.

**Acceptance Scenarios**:

1. **Given** the user is on the Sessions view, **When** a new session file appears in the sessions directory on disk, **Then** the list updates automatically to include the new session within a few seconds
2. **Given** the list may be stale, **When** the user clicks the "Sync" button, **Then** the backend rescans the sessions directory and the list updates to reflect any newly found or removed sessions
3. **Given** a sync is in progress, **When** the user clicks "Sync" again, **Then** the button is disabled or ignored to prevent duplicate syncs

---

### User Story 5 - Delete a Session (Priority: P3)

The user can delete a session they no longer need. Deleting shows a confirmation dialog before proceeding. Deletion removes the session from the application's records but does not delete the original CSV telemetry files on disk. If the deleted session was the currently active selection, the selection is cleared.

**Why this priority**: Deletion is a housekeeping feature. It's useful but not blocking for any core workflow. Users can function perfectly without ever deleting sessions.

**Independent Test**: Can be tested by deleting a session, confirming the dialog, and verifying it disappears from the list and original files remain on disk.

**Acceptance Scenarios**:

1. **Given** a session exists in the list, **When** the user initiates deletion, **Then** a confirmation dialog appears asking the user to confirm
2. **Given** the confirmation dialog is shown, **When** the user confirms, **Then** the session is removed from the list
3. **Given** the confirmation dialog is shown, **When** the user cancels, **Then** the session remains in the list unchanged
4. **Given** the deleted session was the active selection, **When** deletion completes, **Then** the active selection is cleared and sidebar items requiring a session become dimmed again
5. **Given** a session is deleted, **When** the user checks the file system, **Then** the original CSV and metadata files are still present on disk

---

### Edge Cases

- What happens when the backend is unreachable? The view shows an error state explaining the backend is not connected, with guidance to check if it's running.
- What happens when a session has 0 laps? The session still appears in the list showing "0 laps" — it can be processed but may yield limited analysis results.
- What happens when the user switches away from Sessions view during processing? Processing continues in the background; when the user returns, the session reflects its current state.
- What happens when multiple sessions are processing simultaneously? Each session independently tracks its own processing job and progress.
- What happens when a session is in the "parsed" intermediate state but has no active processing job? It is treated as incomplete and shown as "New" with the option to process (or retry).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display all sessions from the backend in a scrollable list, sorted by date descending (newest first)
- **FR-002**: Each session entry MUST display car name, track name, session date, lap count, and processing state
- **FR-003**: System MUST map backend session states to user-friendly labels: "discovered" to "New", "analyzed" to "Ready", "engineered" to "Engineered"
- **FR-004**: System MUST display a "Processing" state with real-time progress for sessions with an active processing job
- **FR-005**: System MUST display a "Failed" state with the error message for sessions whose processing job failed
- **FR-006**: System MUST allow the user to trigger processing on a "New" session
- **FR-007**: System MUST show real-time progress updates during processing via the existing live job tracking infrastructure
- **FR-008**: System MUST show a success notification when processing completes
- **FR-009**: System MUST allow the user to retry processing on a "Failed" session
- **FR-010**: System MUST prevent duplicate processing requests for the same session
- **FR-011**: System MUST allow the user to select a "Ready" or "Engineered" session as the active session
- **FR-012**: System MUST visually highlight the selected session in the list
- **FR-013**: When a session is selected, the sidebar MUST enable (un-dim) the Lap Analysis, Setup Compare, and Engineer navigation items
- **FR-014**: System MUST display the selected session's identity (car and track) in a persistent location in the interface
- **FR-015**: System MUST automatically update the session list when new session files appear on disk
- **FR-016**: System MUST provide a "Sync" button to manually trigger a rescan of the sessions directory
- **FR-017**: System MUST allow deletion of any session with a confirmation dialog
- **FR-018**: Deleting a session MUST only remove the application record, not the underlying files on disk
- **FR-019**: Deleting the active session MUST clear the current selection
- **FR-020**: System MUST display an empty state when no sessions exist, explaining how sessions are recorded via the in-game app
- **FR-021**: System MUST handle backend connectivity errors gracefully, showing an appropriate error state

### Key Entities

- **Session**: A recorded driving session identified by a unique ID, with metadata (car, track, date, lap count, best lap time, session type) and a processing state (New, Processing, Ready, Engineered, Failed)
- **Processing Job**: A background task that parses and analyzes a session's telemetry data, identified by a job ID with progress (0-100%), current step name, and completion/error status
- **Active Selection**: The currently selected session that unlocks the analytical views. At most one session can be selected at a time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All recorded sessions appear in the list within 2 seconds of opening the Sessions view
- **SC-002**: New session files detected on disk appear in the list automatically without user action
- **SC-003**: Processing a session shows real-time progress that updates at least once per second during active processing steps
- **SC-004**: Once processing completes, the session is immediately selectable without page refresh
- **SC-005**: Selecting a session unlocks the Lap Analysis, Setup Compare, and Engineer sidebar items within the same interaction (no reload needed)
- **SC-006**: Deleting a session requires exactly one confirmation step before removal
- **SC-007**: Failed sessions display a specific, human-readable error message and a retry action
- **SC-008**: The empty state provides clear guidance on how to record sessions using the in-game app

## Assumptions

- The backend API is already fully implemented: session listing, detail, sync, deletion, processing, and WebSocket job tracking are all functional
- The frontend already has a design system (Button, Card, Badge, ProgressBar, Modal, EmptyState, Toast, Skeleton), Zustand stores (sessionStore, jobStore, uiStore, notificationStore), a fetch wrapper, and a WebSocket manager
- Session auto-detection relies on the backend's file watcher; the frontend polls the session list periodically to pick up changes
- The "parsed" backend state is transient (occurs during processing between discovered and analyzed) and is mapped to "Processing" in the UI only when an active job exists; otherwise it's treated as incomplete and equivalent to "New" for retry purposes
- Best lap time, if available in the session record, may be displayed on the session card as supplementary info but is not a required field
