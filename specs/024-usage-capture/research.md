# Research: Usage Capture

## R1: How to extract token usage from Pydantic AI result

**Decision**: Use `result.usage()` which returns a `RunUsage` object with `input_tokens`, `output_tokens`, `requests` (turns), and `tool_calls` (count) fields.

**Rationale**: This is the documented Pydantic AI API. The `RunUsage` object aggregates all token counts across the entire agent run, including multi-turn exchanges with tool calls.

**Alternatives considered**:
- Summing per-request `RequestUsage` from individual `ModelResponse.usage` — more granular but unnecessary; `result.usage()` already aggregates.
- Estimating from message content length — inaccurate and fragile.

**Key imports**:
```python
from pydantic_ai.usage import RunUsage
```

**Key attributes**:
- `usage.input_tokens: int`
- `usage.output_tokens: int`
- `usage.requests: int` → maps to `turn_count`
- `usage.tool_calls: int` → maps to `tool_call_count`

## R2: How to extract per-tool-call details from message history

**Decision**: Iterate `result.all_messages()`, find `ToolReturnPart` instances in `ModelRequest` messages, and estimate token count from `len(str(part.content)) // 4`.

**Rationale**: Pydantic AI does not provide per-tool-call token breakdowns. Tool return parts are found in `ModelRequest` messages (as the tool response is sent back to the model in the next request). The `ToolReturnPart` has `tool_name` and `content` fields. A rough 4-chars-per-token estimate is standard for English text and gives a useful approximation.

**Alternatives considered**:
- Counting exact tokens via a tokenizer — adds a heavy dependency (tiktoken) for marginal accuracy gain on an observability feature.

**Key imports**:
```python
from pydantic_ai.messages import ModelRequest, ToolReturnPart
```

**Message structure**:
- `ModelRequest.parts` contains `ToolReturnPart` objects (tool results sent back to the model)
- `ToolReturnPart` fields: `tool_name: str`, `content: str | dict | list`, `tool_call_id: str`

## R3: Where to capture — timing the agent execution

**Decision**: Wrap the `agent.run()` call with `time.perf_counter()` before and after, compute `duration_ms = int((end - start) * 1000)`.

**Rationale**: `time.perf_counter()` is the standard high-resolution timer for measuring elapsed time in Python. It is monotonic and not affected by system clock changes.

**Alternatives considered**:
- `time.time()` — lower resolution and subject to clock adjustments.
- `time.monotonic()` — adequate but `perf_counter` has higher precision.

## R4: Recommendation ID availability for foreign key

**Decision**: The `save_recommendation()` call already exists in `analyze_with_engineer()` and returns a `Recommendation` object with `recommendation_id`. Usage capture must happen after `save_recommendation()` succeeds, using the returned `recommendation_id` as the foreign key.

**Rationale**: The `agent_usage` table has a foreign key constraint `REFERENCES recommendations(recommendation_id) ON DELETE CASCADE`. The recommendation must exist in the database before usage records can reference it.

**Implementation note**: This means usage data must be collected during agent execution (in the per-domain loop) but persisted after the recommendation is saved. We collect usage data into a list during the loop, then persist all records after `save_recommendation()`.

## R5: Error isolation for usage capture

**Decision**: Wrap all usage capture and persistence code in try/except blocks that log warnings but never raise. The outer agent pipeline's existing try/except for `save_recommendation` already handles recommendation persistence failures.

**Rationale**: FR-007 requires that usage tracking failures never prevent recommendation delivery. Usage is observability, not critical functionality.

## R6: Model string for usage records

**Decision**: Use `get_model_string(config)` which is already available in `analyze_with_engineer()` and returns strings like `"anthropic:claude-sonnet-4-20250514"`. Alternatively, use `config.llm_model` or `get_effective_model(config)` for the model name.

**Rationale**: The `AgentUsage.model` field stores the model identifier. Using the effective model name (from `get_effective_model`) gives a clean, readable string.

## R7: API endpoint design

**Decision**: Add `GET /sessions/{session_id}/recommendations/{recommendation_id}/usage` to the existing engineer router. Return a response with aggregated totals and per-agent breakdown.

**Rationale**: Follows the existing REST hierarchy — usage is a sub-resource of a recommendation. The engineer router already has the recommendation lookup pattern with 404 guards.

**Alternatives considered**:
- Standalone `/usage/{recommendation_id}` route — breaks the existing URL hierarchy.
- Including usage inline in `GET /recommendations/{id}` response — bloats the existing response with optional data.
