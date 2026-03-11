# API Contract: Trace Endpoints

**Feature**: 032-agent-diagnostic-traces | **Date**: 2026-03-11

## New Endpoints

### GET /sessions/{session_id}/recommendations/{recommendation_id}/trace

Retrieve the diagnostic trace for an engineer analysis recommendation.

**Path Parameters**:
- `session_id` (string, required) — Session identifier
- `recommendation_id` (string, required) — Recommendation identifier (UUID4)

**Response** `200 OK` (trace available):

```json
{
  "available": true,
  "content": "# Diagnostic Trace: recommendation\n\n**ID**: abc-123...\n\n## Agent: balance\n\n### System Prompt\n\nYou are a suspension and balance specialist...\n\n### User Prompt\n\n## Session Analysis Request\n\n**Car**: ks_ferrari_488_gt3...\n\n### Conversation\n\n#### Assistant\n\nLet me analyze the suspension data...\n\n#### Tool Call: get_setup_range\n\n```json\n{\"section\": \"SPRING_RATE_LF\"}\n```\n\n#### Tool Response: get_setup_range\n\n```json\n{\"min\": 80000, \"max\": 200000, \"step\": 5000}\n```\n\n#### Assistant\n\nBased on the spring rate range...\n\n### Structured Output\n\n```json\n{\"setup_changes\": [...], \"driver_feedback\": [...]}\n```\n\n---\n\n## Agent: tyre\n\n...",
  "trace_type": "recommendation",
  "id": "abc-123-def-456"
}
```

**Response** `200 OK` (no trace available):

```json
{
  "available": false,
  "content": null,
  "trace_type": "recommendation",
  "id": "abc-123-def-456"
}
```

**Error Responses**:
- `404 Not Found` — Recommendation does not exist in the database

**Notes**:
- Returns 200 with `available: false` when the recommendation exists but has no trace (diagnostic mode was off, trace was deleted, or feature predates this implementation)
- Returns 404 only when the recommendation itself does not exist
- The `content` field contains the full Markdown text of the trace file

---

### GET /sessions/{session_id}/messages/{message_id}/trace

Retrieve the diagnostic trace for a chat message.

**Path Parameters**:
- `session_id` (string, required) — Session identifier
- `message_id` (string, required) — Message identifier (UUID4)

**Response** `200 OK` (trace available):

```json
{
  "available": true,
  "content": "# Diagnostic Trace: message\n\n**ID**: msg-789...\n\n## Agent: principal\n\n### System Prompt\n\nYou are an AI race engineer...\n\n### User Prompt\n\nWhat should I change about my braking?\n\n### Conversation\n\n#### Assistant\n\nLooking at your braking data...\n\n### Structured Output\n\nnull\n\n---",
  "trace_type": "message",
  "id": "msg-789-ghi-012"
}
```

**Response** `200 OK` (no trace available):

```json
{
  "available": false,
  "content": null,
  "trace_type": "message",
  "id": "msg-789-ghi-012"
}
```

**Error Responses**:
- `404 Not Found` — Message does not exist in the database

---

### PATCH /config (modified — existing endpoint)

The existing config PATCH endpoint now accepts the `diagnostic_mode` field.

**New accepted field**:

| Field | Type | Description |
|-------|------|-------------|
| `diagnostic_mode` | `bool` | Enable/disable diagnostic trace capture |

**Example request**:

```json
{
  "diagnostic_mode": true
}
```

**Response**: Same as existing — returns the updated config object, now including `diagnostic_mode`.

## Backward Compatibility

- New endpoints return 200 with `available: false` for all recommendations/messages created before this feature
- Existing endpoints are unmodified
- Config changes are backward compatible — missing `diagnostic_mode` in `config.json` defaults to `false`
