# Data Model: Sessions List & Processing View

**Feature**: 017-sessions-view | **Date**: 2026-03-06

## No Backend Entity Changes

This feature is frontend-only. All backend entities (SessionRecord, SyncResult, ProcessResponse) and API endpoints already exist from Phase 6. No backend modifications are needed.

## Frontend Types

### SessionRecord (mirrors backend)

Already defined by the backend. The frontend needs a corresponding TypeScript type.

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | Unique identifier |
| car | string | Car name (e.g., "ks_ferrari_488_gt3") |
| track | string | Track name (e.g., "spa") |
| session_date | string | ISO date string |
| lap_count | number | Number of laps in the session |
| best_lap_time | number or null | Best lap time in seconds |
| state | string | Backend state: "discovered", "parsed", "analyzed", "engineered" |
| session_type | string or null | Session type (practice, qualifying, race) |
| csv_path | string or null | Path to CSV file on disk |
| meta_path | string or null | Path to metadata JSON file |

### SessionListResponse (mirrors backend)

| Field | Type | Description |
|-------|------|-------------|
| sessions | SessionRecord[] | Array of all session records |

### ProcessResponse (mirrors backend)

| Field | Type | Description |
|-------|------|-------------|
| job_id | string | ID of the created processing job |
| session_id | string | ID of the session being processed |

### SyncResult (mirrors backend)

| Field | Type | Description |
|-------|------|-------------|
| discovered | number | Number of new sessions found |
| already_known | number | Number of sessions already in the DB |
| incomplete | number | Number of incomplete session files skipped |

### UISessionState (frontend-only, derived)

Derived from the backend `state` field combined with local job tracking state.

| Value | Meaning | Badge Variant |
|-------|---------|---------------|
| "new" | Unprocessed, ready to analyze | info |
| "processing" | Active processing job in progress | neutral |
| "ready" | Analyzed, selectable | success |
| "engineered" | Analyzed + AI recommendations exist | success |
| "failed" | Processing job failed | error |

### ProcessingJobInfo (frontend-only, component state)

Tracks the relationship between sessions and their active/failed processing jobs.

| Field | Type | Description |
|-------|------|-------------|
| jobId | string | The job ID from the process endpoint |
| error | string or null | Error message if the job failed |

## State Locations

| State | Location | Rationale |
|-------|----------|-----------|
| Session list | TanStack Query `["sessions"]` | Server state, auto-refreshed |
| Selected session | Zustand `sessionStore` | Global, persists across views |
| Processing jobs map | `useState` in SessionsView | Ephemeral, view-scoped |
| Pending delete ID | `useState` in SessionsView | Transient UI state |
| Sync loading | `useState` in SessionsView | Transient UI state |
