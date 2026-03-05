# Feature Specification: Session Discovery

**Feature Branch**: `011-session-discovery`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Build the Session Discovery module for AC Race Engineer (Phase 6.2) -- automatic file watcher, manual sync, session registry with lifecycle states, session list/detail endpoints, and session deletion."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Session Appearance (Priority: P1)

The user finishes a session in Assetto Corsa, closes the game, and opens the AC Race Engineer desktop app. Without doing anything, their new session appears in the session list showing the car, track, date, lap count, session type, and a "discovered" state. The file watcher detected the new CSV + meta.json pair and registered it automatically.

**Why this priority**: This is the core value proposition. The user expects zero-friction discovery -- play AC, open the app, see your session. Everything else depends on sessions being registered.

**Independent Test**: Can be fully tested by creating a CSV + meta.json pair in the sessions directory while the server is running, then verifying the session appears in the database.

**Acceptance Scenarios**:

1. **Given** the server is running and monitoring the sessions directory, **When** a new CSV and matching meta.json appear in the directory, **Then** a new session record is created in the database with state "discovered" and metadata extracted from the meta.json (car, track, date, lap count, session type).
2. **Given** the server is running, **When** only a CSV file appears without a matching meta.json, **Then** no session record is created.
3. **Given** the server is running, **When** only a meta.json file appears without a matching CSV, **Then** no session record is created.
4. **Given** the server is running, **When** a CSV + meta.json pair appears for a session that is already registered, **Then** no duplicate record is created.

---

### User Story 2 - Session List and Detail (Priority: P1)

The user opens the app and sees a list of all their past sessions. Each entry shows the car name, track name, session date, number of laps, session type, and current processing state. The user clicks on a session to see its full details.

**Why this priority**: Equally critical to discovery -- without a way to view sessions, discovery has no visible value. The session list is the primary UI surface of the app.

**Independent Test**: Can be tested by pre-populating the database with session records and calling the list and detail endpoints, verifying correct data is returned.

**Acceptance Scenarios**:

1. **Given** the database contains multiple session records, **When** the user requests the session list, **Then** all sessions are returned ordered by date (newest first) with car, track, date, lap count, session type, and state.
2. **Given** the database contains multiple session records, **When** the user requests the session list filtered by car, **Then** only sessions for that car are returned.
3. **Given** a session exists in the database, **When** the user requests that session's detail by ID, **Then** the full session record is returned including file paths on disk.
4. **Given** a session ID that does not exist, **When** the user requests its detail, **Then** a 404 response is returned.

---

### User Story 3 - Manual Sync (Priority: P2)

The user started the app after the file watcher was not running (e.g., app was closed while they played AC, or the watcher missed files). They trigger a manual rescan from the UI. The system scans the sessions directory, finds all CSV + meta.json pairs that are not yet registered, and adds them to the database. Already-registered sessions are not duplicated.

**Why this priority**: Important safety net when automatic discovery misses sessions, but secondary to the primary auto-discovery path.

**Independent Test**: Can be tested by placing session files in the directory while the server is stopped, starting the server, calling the sync endpoint, and verifying all pairs are registered.

**Acceptance Scenarios**:

1. **Given** the sessions directory contains 5 CSV + meta.json pairs and 2 are already registered, **When** the user triggers a manual sync, **Then** exactly 3 new session records are created and a summary is returned (3 discovered, 2 already known, 0 incomplete).
2. **Given** the sessions directory does not exist, **When** the user triggers a manual sync, **Then** zero sessions are discovered and no error is raised.
3. **Given** the sessions directory contains a CSV without a matching meta.json, **When** the user triggers a manual sync, **Then** that orphan file is reported as incomplete and no session record is created.

---

### User Story 4 - Session Deletion (Priority: P3)

The user decides they no longer want a session in their list (perhaps a test session with bad data). They remove it from the app. The database record is deleted, but the CSV and meta.json files remain on disk untouched -- the app never deletes the user's telemetry data.

**Why this priority**: Nice-to-have for list management, but not blocking any core workflows.

**Independent Test**: Can be tested by creating a session record, calling the delete endpoint, verifying the record is gone from the database, and confirming the files still exist on disk.

**Acceptance Scenarios**:

1. **Given** a session is registered in the database, **When** the user deletes it, **Then** the session record and all associated recommendations, setup changes, and messages are removed from the database (cascade delete), but the CSV and meta.json files remain on disk.
2. **Given** a session ID that does not exist, **When** the user tries to delete it, **Then** a 404 response is returned.

---

### User Story 5 - File Watcher Lifecycle (Priority: P2)

The file watcher starts automatically when the server starts and stops cleanly when the server shuts down. It integrates with the existing FastAPI lifespan pattern. If the sessions directory doesn't exist yet, the watcher waits gracefully until it appears.

**Why this priority**: Essential for Story 1 to work, but the implementation is infrastructure rather than user-facing.

**Independent Test**: Can be tested by starting the server, verifying the watcher is active, stopping the server, and verifying no background tasks remain.

**Acceptance Scenarios**:

1. **Given** the server starts, **When** the lifespan context enters, **Then** the file watcher begins monitoring the sessions directory.
2. **Given** the server is shutting down, **When** the lifespan context exits, **Then** the file watcher stops and all background tasks are cleaned up.
3. **Given** the sessions directory does not exist at server start, **When** the watcher starts, **Then** it handles the missing directory gracefully (no crash, no error logs) and begins watching once the directory appears.

---

### Edge Cases

- What happens when the meta.json is malformed or contains invalid JSON? The session is skipped with a warning log, and other valid sessions continue to be processed.
- What happens when two sessions have the same base filename? This cannot happen by construction (filename includes timestamp, car, and track), but if it did, the upsert behavior of `save_session()` would update the existing record.
- What happens when a session file is being written (AC is still active) and the watcher detects an incomplete file? The watcher uses a stabilization delay -- it waits until the file size stops changing before attempting to register the session.
- What happens if the database is locked when the watcher tries to register a session? SQLite WAL mode handles concurrent reads; the write retries with a reasonable timeout.
- What happens when the sessions directory path contains special characters or spaces (common on Windows with user directories)? Paths are handled as `Path` objects throughout, supporting spaces and Unicode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST continuously monitor the configured sessions directory for new CSV + meta.json file pairs.
- **FR-002**: System MUST require BOTH a CSV file and a matching `.meta.json` sidecar (same base filename) to consider a session valid for registration.
- **FR-003**: System MUST extract session metadata from the `.meta.json` file: car name (`car_name`), track name (`track_name`), session date (`session_start`), lap count (`laps_completed`), and session type (`session_type`).
- **FR-004**: System MUST register discovered sessions in the SQLite database with an initial state of "discovered".
- **FR-005**: System MUST NOT create duplicate records when a session is already registered (identified by the base filename as session_id).
- **FR-006**: System MUST provide an endpoint to list all registered sessions, ordered by date (newest first), with optional car filter.
- **FR-007**: System MUST provide an endpoint to retrieve the full detail of a single session by its ID.
- **FR-008**: System MUST provide an endpoint to trigger a manual rescan of the sessions directory, returning a summary of results (newly discovered count, already known count, incomplete/orphan count).
- **FR-009**: System MUST provide an endpoint to delete a session record from the database without deleting files from disk.
- **FR-010**: Session deletion MUST cascade to all related records (recommendations, setup changes, messages) as defined by the existing database schema.
- **FR-011**: System MUST support a session lifecycle with four states: "discovered", "parsed", "analyzed", "engineered". This phase only sets "discovered"; subsequent phases advance the state.
- **FR-012**: The file watcher MUST start automatically during server startup and stop cleanly during server shutdown, integrating with the existing FastAPI lifespan pattern.
- **FR-013**: System MUST handle a missing sessions directory gracefully (no errors, no crashes) and begin watching when the directory appears.
- **FR-014**: System MUST use a stabilization delay before registering files to avoid reading incomplete files that AC is still writing.
- **FR-015**: System MUST store the file paths (CSV path and meta.json path) in the session record so downstream phases can locate the files.

### Key Entities

- **Session**: A telemetry recording from one Assetto Corsa session. Identified by base filename (unique by construction). Contains: session_id, car, track, session_date, lap_count, session_type, state, csv_path, meta_path, best_lap_time. Lifecycle states: discovered -> parsed -> analyzed -> engineered.
- **Session File Pair**: A CSV file and its `.meta.json` sidecar on disk. Both must exist for the pair to be valid. The base filename (without extensions) ties them together.
- **Sync Result**: The outcome of a manual directory scan. Contains: count of newly discovered sessions, count of already-known sessions, count of incomplete pairs (orphan CSV or meta.json without a partner).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New sessions appear in the session list within 5 seconds of both files being fully written to disk.
- **SC-002**: Manual sync discovers and registers all valid session file pairs in the directory with zero duplicates.
- **SC-003**: The session list loads and displays all registered sessions within 1 second for up to 500 sessions.
- **SC-004**: Session deletion removes the database record while 100% of original files remain intact on disk.
- **SC-005**: The file watcher starts and stops cleanly with the server, with no orphaned background tasks or resource leaks.
- **SC-006**: The system handles edge cases (missing directory, malformed metadata, incomplete files) without crashes or data corruption.

## Assumptions

- The sessions directory is located at `Documents\ac-race-engineer\sessions\` relative to the user's home directory (Windows). The exact path is resolved via the user's home directory.
- Session filenames follow the pattern `{YYYY-MM-DD}_{HHMM}_{car}_{track}` with extensions `.csv` and `.meta.json`. The base filename (without extension) serves as the unique session_id.
- The meta.json follows the v2.0 schema as defined in `specs/002-setup-stint-tracking/contracts/meta-json.md`.
- The existing `save_session()` function performs an upsert (INSERT OR REPLACE), making idempotent registration safe.
- The existing database schema will need minor extension to support the new fields (state, session_type, csv_path, meta_path). This is an additive, non-breaking change.
