# API Contract: Usage Endpoints (Cache Token Extension)

**Feature**: 031-cache-token-tracking | **Date**: 2026-03-11

## Modified Endpoints

Both existing usage endpoints return the same response shape with two new fields added to `UsageTotals` and `AgentUsageDetail`.

### GET /sessions/{session_id}/recommendations/{recommendation_id}/usage

**Response** `200 OK`:

```json
{
  "recommendation_id": "rec-abc123",
  "totals": {
    "input_tokens": 15000,
    "output_tokens": 2500,
    "total_tokens": 17500,
    "tool_call_count": 8,
    "agent_count": 3,
    "cache_read_tokens": 12000,
    "cache_write_tokens": 500
  },
  "agents": [
    {
      "domain": "balance",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 5000,
      "output_tokens": 800,
      "tool_call_count": 3,
      "turn_count": 1,
      "duration_ms": 4200,
      "tool_calls": [
        { "tool_name": "get_setup_range", "token_count": 150 }
      ],
      "cache_read_tokens": 4000,
      "cache_write_tokens": 200
    }
  ]
}
```

### GET /sessions/{session_id}/messages/{message_id}/usage

**Response** `200 OK`:

```json
{
  "message_id": "msg-xyz789",
  "totals": {
    "input_tokens": 8000,
    "output_tokens": 1200,
    "total_tokens": 9200,
    "tool_call_count": 2,
    "agent_count": 1,
    "cache_read_tokens": 6500,
    "cache_write_tokens": 0
  },
  "agents": [
    {
      "domain": "principal",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 8000,
      "output_tokens": 1200,
      "tool_call_count": 2,
      "turn_count": 1,
      "duration_ms": 3100,
      "tool_calls": [],
      "cache_read_tokens": 6500,
      "cache_write_tokens": 0
    }
  ]
}
```

## Backward Compatibility

- New fields `cache_read_tokens` and `cache_write_tokens` always present in responses (default `0`)
- Older records (pre-migration) return `0` for both cache fields
- No changes to request parameters, URL paths, or error responses
- No new endpoints added
