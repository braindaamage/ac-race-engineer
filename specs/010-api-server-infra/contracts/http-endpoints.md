# HTTP Endpoint Contracts: API Server Infrastructure

**Feature**: 010-api-server-infra
**Date**: 2026-03-05

## GET /health

Health check endpoint to confirm the server is alive and operational.

**Request**: No parameters.

**Response** (200):
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Error responses**: None expected (always returns 200 if the server is reachable).

---

## GET /jobs/{job_id}

Retrieve the current state of a job by its identifier.

**Path parameters**:
- `job_id` (string, UUID4): The unique job identifier.

**Response** (200):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "parse",
  "status": "running",
  "progress": 45,
  "current_step": "Segmenting laps",
  "result": null,
  "error": null,
  "created_at": "2026-03-05T14:30:00Z"
}
```

**Error responses**:

- 404 Not Found:
```json
{
  "error": {
    "type": "not_found",
    "message": "Job 550e8400-... not found",
    "detail": null
  }
}
```

---

## Error Envelope (all error responses)

Every error response from any endpoint uses this format:

```json
{
  "error": {
    "type": "<error_type>",
    "message": "<human-readable message>",
    "detail": null
  }
}
```

**Error types**:

| Type               | HTTP Status | When                                           |
|--------------------|-------------|-------------------------------------------------|
| `not_found`        | 404         | Resource does not exist                         |
| `validation_error` | 422         | Request body or parameters failed validation    |
| `internal_error`   | 500         | Unexpected server exception                     |

---

## Notes

- No business endpoints (sessions, analysis, engineer, config) are defined in this phase.
- Future phases (6.2-6.5) will add POST endpoints that create jobs and return `job_id` for the client to track via WebSocket.
