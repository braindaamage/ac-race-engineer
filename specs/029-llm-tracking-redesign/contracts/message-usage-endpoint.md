# Contract: Message Usage Endpoint

**Endpoint**: `GET /sessions/{session_id}/messages/{message_id}/usage`

## Request

- **Method**: GET
- **Path parameters**:
  - `session_id` (string, required): Session identifier
  - `message_id` (string, required): Message identifier
- **Authentication**: None (localhost only)

## Response

### 200 OK — Usage data found

```json
{
  "message_id": "abc123",
  "totals": {
    "input_tokens": 1520,
    "output_tokens": 340,
    "total_tokens": 1860,
    "tool_call_count": 2,
    "agent_count": 1
  },
  "agents": [
    {
      "domain": "principal",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 1520,
      "output_tokens": 340,
      "tool_call_count": 2,
      "turn_count": 3,
      "duration_ms": 4200,
      "tool_calls": [
        { "tool_name": "get_lap_detail", "token_count": 280 },
        { "tool_name": "get_corner_metrics", "token_count": 150 }
      ]
    }
  ]
}
```

### 200 OK — No usage data

```json
{
  "message_id": "abc123",
  "totals": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0,
    "tool_call_count": 0,
    "agent_count": 0
  },
  "agents": []
}
```

### 404 Not Found — Session or message does not exist

```json
{
  "detail": "Session not found: xyz789"
}
```

```json
{
  "detail": "Message not found: abc123"
}
```

## Notes

- Response schema mirrors `RecommendationUsageResponse` with `message_id` replacing `recommendation_id`.
- The `agents` array will contain at most one entry for chat (the "principal" agent). For analysis recommendations, it contains one entry per specialist domain.
- The `domain` field in `AgentUsageDetail` is populated from `agent_name` in the database. For chat, this is "principal".
- The `turn_count` field is populated from `request_count` in the database.
- If the message exists but has no associated usage record, returns 200 with zero totals and empty agents (not 404).
