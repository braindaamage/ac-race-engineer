# Data Model: Usage UI

**Branch**: `025-usage-ui` | **Date**: 2026-03-09

## Frontend Type Definitions

These TypeScript types mirror the backend Pydantic models from `backend/api/engineer/serializers.py`. They are added to `frontend/src/lib/types.ts`.

### ToolCallInfo

Individual tool call within an agent's execution.

| Field | Type | Description |
|-------|------|-------------|
| tool_name | string | Name of the tool called (e.g. "search_kb", "get_setup_range") |
| token_count | number | Number of tokens returned by this tool call |

### AgentUsageDetail

Per-agent usage breakdown for a single specialist domain.

| Field | Type | Description |
|-------|------|-------------|
| domain | string | Agent specialist domain: "balance", "tyre", "aero", or "technique" |
| model | string | LLM model identifier used by this agent |
| input_tokens | number | Total input tokens consumed by this agent |
| output_tokens | number | Total output tokens produced by this agent |
| tool_call_count | number | Number of tool calls made by this agent |
| turn_count | number | Number of conversation turns in this agent's execution |
| duration_ms | number | Wall-clock duration of this agent's execution in milliseconds |
| tool_calls | ToolCallInfo[] | Detailed list of each tool call made |

### UsageTotals

Aggregated usage across all agents for a recommendation.

| Field | Type | Description |
|-------|------|-------------|
| input_tokens | number | Sum of input tokens across all agents |
| output_tokens | number | Sum of output tokens across all agents |
| total_tokens | number | Sum of input + output tokens |
| tool_call_count | number | Sum of tool calls across all agents |
| agent_count | number | Number of agents that participated |

### RecommendationUsageResponse

Top-level response from `GET /sessions/{session_id}/recommendations/{recommendation_id}/usage`.

| Field | Type | Description |
|-------|------|-------------|
| recommendation_id | string | UUID of the recommendation |
| totals | UsageTotals | Aggregated totals across all agents |
| agents | AgentUsageDetail[] | Per-agent breakdown, one entry per domain |

## Data Flow

```
Backend API                        Frontend
─────────────────────────────────────────────────────
GET /sessions/{sid}/               useRecommendationUsage(sid, rid)
  recommendations/{rid}/usage        → TanStack Query (staleTime: Infinity)
                                       → RecommendationUsageResponse
                                         → passed as prop to RecommendationCard
                                           → UsageSummaryBar (renders totals)
                                           → UsageDetailModal (renders agents[])
```

## Relationships

- `RecommendationUsageResponse` has exactly one `UsageTotals` (1:1)
- `RecommendationUsageResponse` has zero or more `AgentUsageDetail` (1:N)
- `AgentUsageDetail` has zero or more `ToolCallInfo` (1:N)
- `RecommendationUsageResponse.recommendation_id` references `RecommendationDetailResponse.recommendation_id` (foreign key relationship via API)

## Formatting Rules

Token counts use compact notation via `formatTokenCount()`:

| Input Range | Output Format | Example |
|-------------|---------------|---------|
| 0–999 | Raw number as string | "0", "42", "999" |
| 1,000–999,999 | One decimal + "K" | "1.0K", "847.3K", "999.9K" |
| 1,000,000+ | One decimal + "M" | "1.0M", "1.4M", "12.5M" |

Duration uses millisecond-to-second conversion: `(duration_ms / 1000).toFixed(1) + "s"` → e.g. "2.3s"
