# API Contract: Recommendation Usage Endpoint

## GET /sessions/{session_id}/recommendations/{recommendation_id}/usage

Returns token usage data for a specific recommendation, including aggregated totals and per-agent breakdown.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | string | Session identifier |
| recommendation_id | string | Recommendation identifier |

### Response: 200 OK

```json
{
  "recommendation_id": "abc123def456",
  "totals": {
    "input_tokens": 15200,
    "output_tokens": 3800,
    "total_tokens": 19000,
    "tool_call_count": 8,
    "agent_count": 3
  },
  "agents": [
    {
      "domain": "balance",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 5400,
      "output_tokens": 1200,
      "tool_call_count": 3,
      "turn_count": 2,
      "duration_ms": 4500,
      "tool_calls": [
        { "tool_name": "search_kb", "token_count": 350 },
        { "tool_name": "get_setup_range", "token_count": 45 },
        { "tool_name": "get_current_value", "token_count": 20 }
      ]
    },
    {
      "domain": "tyre",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 5100,
      "output_tokens": 1400,
      "tool_call_count": 3,
      "turn_count": 2,
      "duration_ms": 5200,
      "tool_calls": [
        { "tool_name": "search_kb", "token_count": 310 },
        { "tool_name": "get_setup_range", "token_count": 50 },
        { "tool_name": "get_lap_detail", "token_count": 80 }
      ]
    },
    {
      "domain": "aero",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 4700,
      "output_tokens": 1200,
      "tool_call_count": 2,
      "turn_count": 1,
      "duration_ms": 3800,
      "tool_calls": [
        { "tool_name": "get_setup_range", "token_count": 45 },
        { "tool_name": "get_current_value", "token_count": 20 }
      ]
    }
  ]
}
```

### Response: 404 Not Found

When the session or recommendation does not exist.

```json
{
  "detail": "Session not found: {session_id}"
}
```

```json
{
  "detail": "Recommendation not found: {recommendation_id}"
}
```

### Response: 200 OK (no usage data)

When the recommendation exists but has no usage records.

```json
{
  "recommendation_id": "abc123def456",
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
