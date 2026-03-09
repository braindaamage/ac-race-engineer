# Data Model: Usage Capture

## Existing Entities (from Phase 9.1 — no changes)

### AgentUsage

Already defined in `backend/ac_engineer/storage/models.py`:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| usage_id | str | PK, auto-generated (uuid4) | Unique identifier |
| recommendation_id | str | FK → recommendations | Links to the recommendation this agent contributed to |
| domain | Literal["balance","tyre","aero","technique"] | NOT NULL | Specialist agent domain |
| model | str | NOT NULL, min_length=1 | LLM model identifier used |
| input_tokens | int | >= 0 | Input/prompt tokens consumed |
| output_tokens | int | >= 0 | Output/completion tokens consumed |
| tool_call_count | int | >= 0 | Number of tool calls made |
| turn_count | int | >= 0 | Number of LLM request turns |
| duration_ms | int | >= 0 | Wall-clock execution time in milliseconds |
| created_at | str | auto-generated (ISO 8601 UTC) | Timestamp of record creation |
| tool_calls | list[ToolCallDetail] | default=[] | Nested tool call details |

### ToolCallDetail

Already defined in `backend/ac_engineer/storage/models.py`:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| detail_id | str | PK, auto-generated (uuid4) | Unique identifier |
| usage_id | str | FK → agent_usage | Parent usage record |
| tool_name | str | NOT NULL, min_length=1 | Name of the tool called |
| token_count | int | >= 0 | Estimated tokens in tool response |
| called_at | str | auto-generated (ISO 8601 UTC) | Timestamp |

## New Entities (API response models)

### UsageTotals (API response sub-model)

Computed aggregation across all agents for a recommendation.

| Field | Type | Description |
|-------|------|-------------|
| input_tokens | int | Sum of input_tokens across all agents |
| output_tokens | int | Sum of output_tokens across all agents |
| total_tokens | int | input_tokens + output_tokens |
| tool_call_count | int | Sum of tool_call_count across all agents |
| agent_count | int | Number of specialist agents that ran |

### AgentUsageDetail (API response sub-model)

Per-agent breakdown in the API response.

| Field | Type | Description |
|-------|------|-------------|
| domain | str | Agent domain name (balance, tyre, aero, technique) |
| model | str | LLM model identifier |
| input_tokens | int | Input tokens for this agent |
| output_tokens | int | Output tokens for this agent |
| tool_call_count | int | Number of tool calls |
| turn_count | int | Number of LLM request turns |
| duration_ms | int | Execution time in milliseconds |
| tool_calls | list[ToolCallInfo] | Per-tool-call details |

### ToolCallInfo (API response sub-model)

Individual tool call in the API response.

| Field | Type | Description |
|-------|------|-------------|
| tool_name | str | Name of the tool |
| token_count | int | Estimated tokens in tool response |

### RecommendationUsageResponse (API response — top level)

Full response for the usage endpoint.

| Field | Type | Description |
|-------|------|-------------|
| recommendation_id | str | The queried recommendation |
| totals | UsageTotals | Aggregated totals across all agents |
| agents | list[AgentUsageDetail] | Per-agent breakdown |

## Relationships

```
Recommendation (1) ──── (0..*) AgentUsage ──── (0..*) ToolCallDetail
                                    │
                                    ▼
                        RecommendationUsageResponse
                        ├── totals: UsageTotals (computed from AgentUsage list)
                        └── agents: list[AgentUsageDetail] (mapped from AgentUsage)
```

## Data Flow

1. **Collection phase** (during agent loop in `analyze_with_engineer`):
   - Before `agent.run()`: record `start_time = time.perf_counter()`
   - After `agent.run()`: extract `result.usage()` and `result.all_messages()`
   - Build `AgentUsage` model (without recommendation_id yet)
   - Append to a collection list

2. **Persistence phase** (after `save_recommendation()`):
   - Get `recommendation_id` from the returned `Recommendation`
   - Set `recommendation_id` on each collected `AgentUsage`
   - Call `save_agent_usage()` for each record
   - Log a summary line per agent

3. **Query phase** (API endpoint):
   - Call `get_agent_usage(db_path, recommendation_id)` → list of `AgentUsage`
   - Compute `UsageTotals` by summing fields
   - Map each `AgentUsage` to `AgentUsageDetail`
   - Return `RecommendationUsageResponse`
