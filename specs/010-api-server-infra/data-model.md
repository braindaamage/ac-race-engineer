# Data Model: API Server Infrastructure

**Feature**: 010-api-server-infra
**Date**: 2026-03-05

## Entities

### JobStatus (Enum)

Represents the lifecycle state of a background job.

| Value       | Description                                    |
|-------------|------------------------------------------------|
| `pending`   | Job created but not yet started                |
| `running`   | Job is actively executing                      |
| `completed` | Job finished successfully, result available    |
| `failed`    | Job finished with error, error details available |

### Job

Represents a single background operation tracked by the job manager.

| Field         | Type                  | Required | Description                                      |
|---------------|-----------------------|----------|--------------------------------------------------|
| `job_id`      | string (UUID4)        | yes      | Unique identifier assigned at creation           |
| `job_type`    | string                | yes      | Label describing the operation (e.g., "parse", "analyze") |
| `status`      | JobStatus             | yes      | Current lifecycle state                          |
| `progress`    | integer (0-100)       | yes      | Completion percentage, starts at 0               |
| `current_step`| string or null        | no       | Human-readable description of what is happening now |
| `result`      | any (JSON-serializable) or null | no | Final output on successful completion          |
| `error`       | string or null        | no       | Error description on failure                     |
| `created_at`  | datetime (ISO 8601)   | yes      | Timestamp of job creation                        |

**State transitions**:
```
pending → running → completed
                  → failed
```
- A job starts as `pending` when created.
- Transitions to `running` when the worker begins execution.
- Ends as `completed` (with `result`) or `failed` (with `error`).
- No transition back from terminal states (`completed`, `failed`).

### JobEvent

A message sent over WebSocket to a subscribed client, representing a snapshot of job state at a point in time.

| Field         | Type        | Required | Description                                      |
|---------------|-------------|----------|--------------------------------------------------|
| `event`       | string      | yes      | Event type: `"progress"`, `"completed"`, or `"error"` |
| `job_id`      | string      | yes      | The job this event refers to                     |
| `status`      | JobStatus   | yes      | Current job status at time of event              |
| `progress`    | integer     | yes      | Current progress percentage                      |
| `current_step`| string or null | no    | Current step description (for progress events)   |
| `result`      | any or null | no       | Job result (only for completed events)           |
| `error`       | string or null | no    | Error description (only for error events)        |

### ErrorResponse

The uniform error envelope returned by all API error handlers.

| Field     | Type               | Required | Description                                      |
|-----------|--------------------|----------|--------------------------------------------------|
| `type`    | string             | yes      | Machine-readable error category (e.g., `"not_found"`, `"validation_error"`, `"internal_error"`) |
| `message` | string             | yes      | Human-readable error description for display     |
| `detail`  | object or null     | no       | Structured context (e.g., validation field errors) |

### HealthResponse

The response from the health check endpoint.

| Field     | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| `status`  | string | yes      | Always `"ok"` when the server is healthy         |
| `version` | string | yes      | Application version string                       |

## Relationships

- **JobManager** holds a dictionary of `Job` objects keyed by `job_id`.
- **JobManager** holds an `asyncio.Event` per `job_id` for WebSocket notification.
- **WebSocket handler** reads `Job` state and emits `JobEvent` messages.
- **Error handlers** produce `ErrorResponse` for all HTTP error paths.

## Validation Rules

- `job_id` must be a valid UUID4 string.
- `progress` must be an integer in the range [0, 100].
- `status` transitions are one-directional: `pending` → `running` → `completed`/`failed`.
- `result` is only set when `status` is `completed`.
- `error` is only set when `status` is `failed`.
- `job_type` must be a non-empty string.
