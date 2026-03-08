# Data Model: Usage Storage

**Feature**: 023-usage-storage | **Date**: 2026-03-08

## Entities

### AgentUsage

Represents a single specialist agent execution within an engineer recommendation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| usage_id | TEXT | PK, auto-generated (uuid4 hex) | Unique identifier |
| recommendation_id | TEXT | FK → recommendations.recommendation_id, ON DELETE CASCADE | Parent recommendation |
| domain | TEXT | CHECK IN ('balance', 'tyre', 'aero', 'technique') | Specialist agent domain |
| model | TEXT | NOT NULL | Full LLM model identifier (e.g., "claude-sonnet-4-20250514") |
| input_tokens | INTEGER | NOT NULL, ≥ 0 | Tokens in prompt |
| output_tokens | INTEGER | NOT NULL, ≥ 0 | Tokens in response |
| tool_call_count | INTEGER | NOT NULL, ≥ 0 | Number of tool invocations |
| turn_count | INTEGER | NOT NULL, ≥ 0 | Number of conversation turns |
| duration_ms | INTEGER | NOT NULL, ≥ 0 | Execution time in milliseconds |
| created_at | TEXT | NOT NULL, ISO 8601 UTC | Record creation timestamp |
| tool_calls | list[ToolCallDetail] | In-memory only (not a DB column) | Nested child records |

### ToolCallDetail

Represents a single tool invocation within an agent execution.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| detail_id | TEXT | PK, auto-generated (uuid4 hex) | Unique identifier |
| usage_id | TEXT | FK → agent_usage.usage_id, ON DELETE CASCADE | Parent usage record |
| tool_name | TEXT | NOT NULL | Name of the tool function called |
| token_count | INTEGER | NOT NULL, ≥ 0 | Tokens in the tool's response |
| called_at | TEXT | NOT NULL, ISO 8601 UTC | Timestamp of the tool call |

## Relationships

```text
sessions (1) ──── (N) recommendations (1) ──── (N) agent_usage (1) ──── (N) tool_call_details
                                              │                        │
                                              └── setup_changes        └── (cascade delete)
```

- A **recommendation** has 0-4 **agent_usage** records (one per specialist domain that ran).
- An **agent_usage** record has 0-N **tool_call_details** (one per tool invocation during execution).
- Deleting a **recommendation** cascades to its **agent_usage** records, which cascades to their **tool_call_details**.

## Pydantic Models (in storage/models.py)

### ToolCallDetail

```python
class ToolCallDetail(BaseModel):
    detail_id: str = ""
    usage_id: str = ""
    tool_name: str = Field(..., min_length=1)
    token_count: int = Field(..., ge=0)
    called_at: str = ""
```

### AgentUsage

```python
from typing import Literal

VALID_DOMAINS = ("balance", "tyre", "aero", "technique")

class AgentUsage(BaseModel):
    usage_id: str = ""
    recommendation_id: str = ""
    domain: Literal['balance', 'tyre', 'aero', 'technique']
    model: str = Field(..., min_length=1)
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    tool_call_count: int = Field(..., ge=0)
    turn_count: int = Field(..., ge=0)
    duration_ms: int = Field(..., ge=0)
    created_at: str = ""
    tool_calls: list[ToolCallDetail] = Field(default_factory=list)
```

## DDL (appended to _MIGRATIONS in db.py)

```sql
CREATE TABLE IF NOT EXISTS agent_usage (
    usage_id          TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    domain            TEXT NOT NULL CHECK(domain IN ('balance', 'tyre', 'aero', 'technique')),
    model             TEXT NOT NULL,
    input_tokens      INTEGER NOT NULL CHECK(input_tokens >= 0),
    output_tokens     INTEGER NOT NULL CHECK(output_tokens >= 0),
    tool_call_count   INTEGER NOT NULL CHECK(tool_call_count >= 0),
    turn_count        INTEGER NOT NULL CHECK(turn_count >= 0),
    duration_ms       INTEGER NOT NULL CHECK(duration_ms >= 0),
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_call_details (
    detail_id   TEXT PRIMARY KEY,
    usage_id    TEXT NOT NULL REFERENCES agent_usage(usage_id) ON DELETE CASCADE,
    tool_name   TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK(token_count >= 0),
    called_at   TEXT NOT NULL
);
```

## State Transitions

None — records are immutable. Once created, they are never updated or individually deleted (only cascade-deleted when parent recommendation is removed).
