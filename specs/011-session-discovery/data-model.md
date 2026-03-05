# Data Model: Session Discovery

**Branch**: `011-session-discovery` | **Date**: 2026-03-05

## Entities

### SessionRecord (extended)

Extends the existing `SessionRecord` Pydantic model in `backend/ac_engineer/storage/models.py`.

| Field          | Type           | Required | Default       | Description                                          |
| -------------- | -------------- | -------- | ------------- | ---------------------------------------------------- |
| session_id     | str            | Yes      | —             | Base filename without extensions (natural key)       |
| car            | str            | Yes      | —             | Car identifier from meta.json `car_name`             |
| track          | str            | Yes      | —             | Track identifier from meta.json `track_name`         |
| session_date   | str            | Yes      | —             | ISO 8601 datetime from meta.json `session_start`     |
| lap_count      | int            | Yes      | —             | From meta.json `laps_completed` (0 if null/crashed)  |
| best_lap_time  | float or None  | No       | None          | Populated in Phase 6.3 after parsing                 |
| state          | str            | Yes      | "discovered"  | Lifecycle: discovered, parsed, analyzed, engineered  |
| session_type   | str or None    | No       | None          | From meta.json: practice, qualify, race, hotlap, etc |
| csv_path       | str or None    | No       | None          | Absolute path to the CSV file on disk                |
| meta_path      | str or None    | No       | None          | Absolute path to the meta.json file on disk          |

**Validation rules**:
- `session_id`: min_length=1
- `car`: min_length=1
- `track`: min_length=1
- `session_date`: min_length=1
- `lap_count`: ge=0
- `best_lap_time`: ge=0 if not None
- `state`: must be one of "discovered", "parsed", "analyzed", "engineered"

**State transitions**:
```
discovered → parsed → analyzed → engineered
```
- Only forward transitions are valid (no going back)
- This phase only sets "discovered"; subsequent phases advance the state

### SyncResult

New model for the manual sync endpoint response.

| Field          | Type | Description                                      |
| -------------- | ---- | ------------------------------------------------ |
| discovered     | int  | Number of new sessions registered in this scan   |
| already_known  | int  | Number of sessions already in the database       |
| incomplete     | int  | Number of orphan files (CSV or meta.json alone)  |

## Database Schema Changes

### Existing `sessions` table (current)

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    car           TEXT NOT NULL,
    track         TEXT NOT NULL,
    session_date  TEXT NOT NULL,
    lap_count     INTEGER NOT NULL,
    best_lap_time REAL
);
```

### Migration (additive columns)

```sql
ALTER TABLE sessions ADD COLUMN state TEXT NOT NULL DEFAULT 'discovered';
ALTER TABLE sessions ADD COLUMN session_type TEXT;
ALTER TABLE sessions ADD COLUMN csv_path TEXT;
ALTER TABLE sessions ADD COLUMN meta_path TEXT;
```

Each `ALTER TABLE` is wrapped in a try/except to handle the case where the column already exists (idempotent). SQLite does not support `IF NOT EXISTS` for columns.

### Related tables (unchanged, cascade delete via FK)

- `recommendations` — FK to `sessions(session_id) ON DELETE CASCADE`
- `setup_changes` — FK to `recommendations(recommendation_id) ON DELETE CASCADE`
- `messages` — FK to `sessions(session_id) ON DELETE CASCADE`

## Storage Functions

### Existing (unchanged signatures, extended behavior)

- `save_session(db_path, session)` — upserts a SessionRecord. Now includes new fields in INSERT.
- `list_sessions(db_path, *, car=None)` — returns all sessions, filtered optionally. Now includes new fields.
- `get_session(db_path, session_id)` — returns single session. Now includes new fields.

### New functions

- `session_exists(db_path, session_id) -> bool` — quick existence check for idempotent registration.
- `delete_session(db_path, session_id) -> bool` — deletes session by ID. Returns True if deleted, False if not found. Cascade deletes related records via FK constraints.
- `update_session_state(db_path, session_id, state) -> bool` — updates lifecycle state. Returns True if updated, False if not found. Validates state value.
