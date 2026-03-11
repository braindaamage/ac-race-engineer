# Data Model: Cache Token Tracking

**Feature**: 031-cache-token-tracking | **Date**: 2026-03-11

## Entity Changes

### LlmEvent (modified)

Storage model in `backend/ac_engineer/storage/models.py`. Represents a single LLM interaction.

**New fields**:

| Field | Type | Default | Constraint | Description |
|-------|------|---------|------------|-------------|
| `cache_read_tokens` | `int` | `0` | `>= 0` | Tokens served from provider prompt cache |
| `cache_write_tokens` | `int` | `0` | `>= 0` | Tokens written to provider prompt cache |

**Existing fields** (unchanged): `id`, `session_id`, `event_type`, `agent_name`, `model`, `input_tokens`, `output_tokens`, `request_count`, `tool_call_count`, `duration_ms`, `created_at`, `context_type`, `context_id`, `tool_calls`

**Validation**: Both new fields use `Field(default=0, ge=0)` matching the pattern of `input_tokens` and `output_tokens`.

### UsageTotals (modified)

API serializer in `backend/api/engineer/serializers.py`. Aggregated totals across all agents.

**New fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cache_read_tokens` | `int` | `0` | Sum of cache_read_tokens across all agents |
| `cache_write_tokens` | `int` | `0` | Sum of cache_write_tokens across all agents |

**Existing fields** (unchanged): `input_tokens`, `output_tokens`, `total_tokens`, `tool_call_count`, `agent_count`

### AgentUsageDetail (modified)

API serializer in `backend/api/engineer/serializers.py`. Per-agent usage breakdown.

**New fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cache_read_tokens` | `int` | `0` | Cache read tokens for this agent |
| `cache_write_tokens` | `int` | `0` | Cache write tokens for this agent |

**Existing fields** (unchanged): `domain`, `model`, `input_tokens`, `output_tokens`, `tool_call_count`, `turn_count`, `duration_ms`, `tool_calls`

## Database Schema Change

### Migration 7

Two `ALTER TABLE` statements added to the `_MIGRATIONS` list in `backend/ac_engineer/storage/db.py`:

```sql
ALTER TABLE llm_events ADD COLUMN cache_read_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_read_tokens >= 0);
ALTER TABLE llm_events ADD COLUMN cache_write_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_write_tokens >= 0);
```

**Backward compatibility**: `DEFAULT 0` ensures all existing rows receive the value 0 without a data migration step. The `NOT NULL` + `CHECK` constraints match the pattern used by `input_tokens` and `output_tokens`.

## Frontend Type Changes

### UsageTotals (TypeScript)

```typescript
export interface UsageTotals {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  tool_call_count: number;
  agent_count: number;
  cache_read_tokens: number;   // NEW
  cache_write_tokens: number;  // NEW
}
```

### AgentUsageDetail (TypeScript)

```typescript
export interface AgentUsageDetail {
  domain: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  tool_call_count: number;
  turn_count: number;
  duration_ms: number;
  tool_calls: ToolCallInfo[];
  cache_read_tokens: number;   // NEW
  cache_write_tokens: number;  // NEW
}
```

## Data Flow

```
RunUsage.cache_read_tokens ──┐
RunUsage.cache_write_tokens ─┤
                             ▼
                    LlmEvent (model)
                             │
                    save_llm_event() ──► llm_events table
                             │
                    get_llm_events() ◄── llm_events table
                             │
               _compute_usage_response()
                        │         │
              UsageTotals    AgentUsageDetail
               (aggregated)    (per-agent)
                        │         │
                   JSON response
                        │         │
              UsageTotals    AgentUsageDetail
              (TypeScript)   (TypeScript)
                        │         │
             UsageSummaryBar  UsageDetailModal
```
