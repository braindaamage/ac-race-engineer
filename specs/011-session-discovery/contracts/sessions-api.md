# Sessions API Contract

**Branch**: `011-session-discovery` | **Date**: 2026-03-05

All endpoints are prefixed with the API base URL (default: `http://localhost:8000`).

## GET /sessions

List all registered sessions, ordered by date (newest first).

**Query Parameters**:

| Parameter | Type   | Required | Description                        |
| --------- | ------ | -------- | ---------------------------------- |
| car       | string | No       | Filter sessions by car identifier  |

**Response** `200 OK`:

```json
{
  "sessions": [
    {
      "session_id": "2026-03-05_1430_ks_ferrari_488_gt3_monza",
      "car": "ks_ferrari_488_gt3",
      "track": "monza",
      "session_date": "2026-03-05T14:30:00",
      "lap_count": 15,
      "best_lap_time": null,
      "state": "discovered",
      "session_type": "practice",
      "csv_path": "C:\\Users\\leo\\Documents\\ac-race-engineer\\sessions\\2026-03-05_1430_ks_ferrari_488_gt3_monza.csv",
      "meta_path": "C:\\Users\\leo\\Documents\\ac-race-engineer\\sessions\\2026-03-05_1430_ks_ferrari_488_gt3_monza.meta.json"
    }
  ]
}
```

## GET /sessions/{session_id}

Retrieve full detail of a single session.

**Path Parameters**:

| Parameter  | Type   | Required | Description                        |
| ---------- | ------ | -------- | ---------------------------------- |
| session_id | string | Yes      | Base filename of the session       |

**Response** `200 OK`:

```json
{
  "session_id": "2026-03-05_1430_ks_ferrari_488_gt3_monza",
  "car": "ks_ferrari_488_gt3",
  "track": "monza",
  "session_date": "2026-03-05T14:30:00",
  "lap_count": 15,
  "best_lap_time": null,
  "state": "discovered",
  "session_type": "practice",
  "csv_path": "C:\\Users\\leo\\Documents\\ac-race-engineer\\sessions\\2026-03-05_1430_ks_ferrari_488_gt3_monza.csv",
  "meta_path": "C:\\Users\\leo\\Documents\\ac-race-engineer\\sessions\\2026-03-05_1430_ks_ferrari_488_gt3_monza.meta.json"
}
```

**Response** `404 Not Found`:

```json
{
  "error": {
    "type": "not_found",
    "message": "Session not found: 2026-03-05_1430_ks_ferrari_488_gt3_monza",
    "detail": null
  }
}
```

## POST /sessions/sync

Trigger a manual scan of the sessions directory. Discovers new CSV + meta.json pairs and registers them.

**Request body**: None

**Response** `200 OK`:

```json
{
  "discovered": 3,
  "already_known": 7,
  "incomplete": 1
}
```

**Field descriptions**:
- `discovered`: Number of new sessions registered by this scan
- `already_known`: Number of file pairs that were already in the database
- `incomplete`: Number of orphan files (CSV without meta.json or vice versa)

## DELETE /sessions/{session_id}

Remove a session record from the database. Does NOT delete files from disk.

**Path Parameters**:

| Parameter  | Type   | Required | Description                        |
| ---------- | ------ | -------- | ---------------------------------- |
| session_id | string | Yes      | Base filename of the session       |

**Response** `204 No Content`: Session deleted successfully (no body).

**Response** `404 Not Found`:

```json
{
  "error": {
    "type": "not_found",
    "message": "Session not found: 2026-03-05_1430_ks_ferrari_488_gt3_monza",
    "detail": null
  }
}
```

## Error Format

All error responses follow the existing uniform error format from Phase 6.1:

```json
{
  "error": {
    "type": "string",
    "message": "string",
    "detail": null
  }
}
```

Error types used by this module:
- `not_found` (404): Session ID does not exist in database
- `validation_error` (422): Invalid query parameters or path parameters
- `internal_error` (500): Unexpected server error (handled by catch-all middleware)
