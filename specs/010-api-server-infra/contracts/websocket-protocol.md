# WebSocket Protocol Contract: Job Progress

**Feature**: 010-api-server-infra
**Date**: 2026-03-05

## Connection

**Endpoint**: `ws://localhost:{port}/ws/jobs/{job_id}`

**Path parameters**:
- `job_id` (string, UUID4): The job to subscribe to.

**Connection behavior**:
- If `job_id` is not found, the server closes the WebSocket immediately with code 4004 and reason "Job not found".
- If the job exists, the server sends events as JSON messages until the job reaches a terminal state (`completed` or `failed`), then closes the connection with code 1000 (normal closure).

## Server → Client Messages

All messages are JSON objects with the following shape:

### Progress Event

Sent each time the job's progress or step changes.

```json
{
  "event": "progress",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 45,
  "current_step": "Segmenting laps"
}
```

### Completed Event

Sent once when the job finishes successfully. This is the last message before the connection closes.

```json
{
  "event": "completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "current_step": null,
  "result": { "session_id": "abc123", "laps": 15 }
}
```

### Error Event

Sent once when the job fails. This is the last message before the connection closes.

```json
{
  "event": "error",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 45,
  "current_step": "Segmenting laps",
  "error": "Failed to parse CSV: unexpected column count at row 1234"
}
```

## Client → Server Messages

No client-to-server messages are expected. The WebSocket is unidirectional (server pushes only). Any messages sent by the client are ignored.

## Reconnection Behavior

- If the client disconnects and reconnects to the same `job_id`:
  - If the job is still `running`, the client resumes receiving progress events from the current state.
  - If the job has already `completed` or `failed`, the server sends the terminal event immediately and closes.
  - If the job has been evicted from memory, the server closes with code 4004.

## Close Codes

| Code | Meaning                                    |
|------|--------------------------------------------|
| 1000 | Normal closure (job reached terminal state) |
| 4004 | Job not found or evicted                   |
