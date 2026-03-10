# Data Model: LLM Tracking Redesign + Chat Fixes

**Branch**: `029-llm-tracking-redesign` | **Date**: 2026-03-10

## Entities

### LlmEvent (replaces AgentUsage)

| Field          | Type           | Constraints                          | Notes                                    |
|----------------|----------------|--------------------------------------|------------------------------------------|
| id             | string (PK)    | Auto-generated UUID hex              |                                          |
| session_id     | string         | Required, non-empty                  | Links to session (logical, not FK)       |
| event_type     | string         | Required, non-empty                  | Initial values: "analysis", "chat"       |
| agent_name     | string         | Required, non-empty                  | e.g. "balance", "tyre", "principal"      |
| model          | string         | Required, non-empty                  | LLM model identifier                    |
| input_tokens   | integer        | >= 0                                 |                                          |
| output_tokens  | integer        | >= 0                                 |                                          |
| request_count  | integer        | >= 0                                 | Number of LLM API requests              |
| tool_call_count| integer        | >= 0                                 |                                          |
| duration_ms    | integer        | >= 0                                 |                                          |
| created_at     | string (ISO)   | Auto-generated                       |                                          |
| context_type   | string or null | Nullable                             | Initial values: "recommendation", "message" |
| context_id     | string or null | Nullable                             | ID of the linked recommendation or message |

**Validation rules**:
- `event_type` and `context_type` are open strings — no CHECK constraints in DB.
- Application-layer validation ensures known values at write time.
- `context_type` and `context_id` are both null or both non-null (application-enforced).

### LlmToolCall (replaces ToolCallDetail)

| Field           | Type           | Constraints                          | Notes                                    |
|-----------------|----------------|--------------------------------------|------------------------------------------|
| id              | string (PK)    | Auto-generated UUID hex              |                                          |
| event_id        | string (FK)    | References LlmEvent.id, cascade del  |                                          |
| tool_name       | string         | Required, non-empty                  | e.g. "search_kb", "get_lap_detail"       |
| response_tokens | integer        | >= 0                                 | Estimated tokens in tool response        |
| call_index      | integer        | >= 0                                 | Zero-based order within event            |

## Entity Relationships

```
LlmEvent 1 ──── * LlmToolCall
   │
   │ context_type="recommendation"
   │ context_id → recommendations.recommendation_id
   │
   │ context_type="message"
   │ context_id → messages.message_id
```

- One LlmEvent has zero or more LlmToolCall records.
- LlmEvent optionally links to a recommendation or message via `context_type` + `context_id` (polymorphic association — no DB-level FK on context_id).
- Cascade delete on LlmToolCall when parent LlmEvent is deleted.

## Migration from Previous Schema

| Old Table            | New Table       | Key Differences                                    |
|----------------------|-----------------|----------------------------------------------------|
| agent_usage          | llm_events      | No FK to recommendations; polymorphic context_type/context_id; domain→agent_name; turn_count→request_count; no CHECK on domain |
| tool_call_details    | llm_tool_calls  | token_count→response_tokens; called_at→call_index; usage_id→event_id |

## Pydantic Models

### LlmEvent (storage model)

```
LlmEvent:
  id: str = ""
  session_id: str (required)
  event_type: str (required)
  agent_name: str (required)
  model: str (required)
  input_tokens: int >= 0
  output_tokens: int >= 0
  request_count: int >= 0
  tool_call_count: int >= 0
  duration_ms: int >= 0
  created_at: str = ""
  context_type: str | None = None
  context_id: str | None = None
  tool_calls: list[LlmToolCall] = []
```

### LlmToolCall (storage model)

```
LlmToolCall:
  id: str = ""
  event_id: str = ""
  tool_name: str (required)
  response_tokens: int >= 0
  call_index: int >= 0
```

### API Response Models

**MessageUsageResponse** (new, for GET /sessions/{sid}/messages/{mid}/usage):
```
MessageUsageResponse:
  message_id: str
  totals: UsageTotals
  agents: list[AgentUsageDetail] = []
```

**UsageTotals** (unchanged):
```
UsageTotals:
  input_tokens: int
  output_tokens: int
  total_tokens: int
  tool_call_count: int
  agent_count: int
```

**AgentUsageDetail** (field rename: domain stays for backward compat):
```
AgentUsageDetail:
  domain: str          # populated from agent_name
  model: str
  input_tokens: int
  output_tokens: int
  tool_call_count: int
  turn_count: int      # populated from request_count
  duration_ms: int
  tool_calls: list[ToolCallInfo] = []
```

**ToolCallInfo** (field rename):
```
ToolCallInfo:
  tool_name: str
  token_count: int     # populated from response_tokens
```
