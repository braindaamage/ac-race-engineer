# Contract: LLM Events Storage Functions

## save_llm_event(db_path, event: LlmEvent) → LlmEvent

Persists an LLM event record with its tool call details atomically.

**Input**: `LlmEvent` with required fields populated. `id` and `created_at` may be empty (auto-generated).

**Output**: `LlmEvent` with `id`, `created_at`, and all `tool_calls[].id` / `tool_calls[].event_id` populated.

**Behavior**:
1. Generate `id` (uuid4 hex) and `created_at` (ISO timestamp) if empty.
2. Insert row into `llm_events` table.
3. For each tool call: generate `id`, set `event_id`, insert into `llm_tool_calls`.
4. All inserts are atomic (single transaction).
5. Returns the fully populated `LlmEvent`.

**Error handling**: Raises on DB errors. Callers are responsible for try/except if tracking is non-critical.

## get_llm_events(db_path, context_type: str, context_id: str) → list[LlmEvent]

Retrieves all LLM event records matching a context.

**Input**: `context_type` (e.g., "recommendation", "message") and `context_id` (the linked entity ID).

**Output**: List of `LlmEvent` with `tool_calls` populated, ordered by `created_at ASC`.

**Behavior**:
1. Query `llm_events` WHERE `context_type = ?` AND `context_id = ?`.
2. For each event, fetch related `llm_tool_calls` rows ordered by `call_index ASC`.
3. Returns empty list if no events match.

## Notes

- These functions replace `save_agent_usage()` and `get_agent_usage()`.
- The query interface uses `context_type` + `context_id` instead of a direct `recommendation_id` parameter, making it reusable for any context.
- The existing recommendation usage endpoint calls `get_llm_events(db_path, "recommendation", recommendation_id)`.
- The new message usage endpoint calls `get_llm_events(db_path, "message", message_id)`.
