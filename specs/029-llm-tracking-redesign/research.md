# Research: LLM Tracking Redesign + Chat Fixes

**Branch**: `029-llm-tracking-redesign` | **Date**: 2026-03-10

## R1: Current Storage Schema and Migration Strategy

**Decision**: Replace migrations 6-7 (agent_usage, tool_call_details) with new migrations creating llm_events and llm_tool_calls. No backward compatibility — fresh DB.

**Rationale**: The current `agent_usage` table has a hard FK to `recommendations(recommendation_id)` and a `domain` column constrained to specialist agent domains. This makes it impossible to store chat usage without adding nullable columns or violating constraints. A clean replacement is simpler and the user description explicitly states no data migration.

**Alternatives considered**:
- Adding nullable `message_id` column to existing table: rejected — accumulates nullable FKs for each new origin, messy schema.
- Creating a separate `chat_usage` table: rejected — duplicates structure, queries become harder for cross-type reporting.

**Implementation detail**: The `_MIGRATIONS` list in `db.py` currently has 7 entries (indices 0-6). Replace indices 5-6 (agent_usage, tool_call_details) with new DDL for llm_events and llm_tool_calls. Migration numbering doesn't matter since DB is recreated from scratch.

## R2: Pydantic AI Usage Extraction for Chat Agent

**Decision**: Use `result.usage()` from the Pydantic AI `RunResult` object returned by `agent.run()` in the chat pipeline, same as the analysis pipeline does.

**Rationale**: The analysis pipeline already extracts usage via `result.usage()` in `agents.py` (line ~583). The chat pipeline's `agent.run()` returns the same `RunResult` type. The existing `_extract_tool_calls()` helper iterates `result.all_messages()` to find `ToolReturnPart` instances and estimate token counts. This helper can be reused directly for chat.

**Key fields available from `result.usage()`**:
- `input_tokens` (or 0)
- `output_tokens` (or 0)
- `requests` → maps to `request_count`
- `tool_calls` → maps to `tool_call_count` (available on some providers)

**Tool calls in chat**: The chat agent in `make_chat_job()` currently creates a bare `Agent(model, system_prompt=...)` with no tools registered. To capture tool calls, the agent needs `get_lap_detail` and `get_corner_metrics` tools registered (per the spec requirement). However, examining the current code, the chat agent does NOT have tools — it's a plain text agent. The user description says "the principal agent has access to get_lap_detail and get_corner_metrics", so these tools need to be added to the chat agent as part of this change.

**Correction**: Re-reading the user description more carefully — it says to "Include tool call detail rows in llm_tool_calls (the principal agent has access to get_lap_detail and get_corner_metrics)." This means the chat agent should already have or should be given these tools. Currently it does not. This is a prerequisite change.

## R3: Response Schema Reuse for Message Usage Endpoint

**Decision**: Create a shared `UsageResponse` base model (or rename/generalize `RecommendationUsageResponse`) that both the recommendation usage endpoint and the new message usage endpoint return.

**Rationale**: The `RecommendationUsageResponse` currently contains a `recommendation_id` field which is recommendation-specific. Options:
1. Create a generic `UsageResponse` with `context_id` instead — but this changes the existing contract.
2. Keep `RecommendationUsageResponse` as-is and create a `MessageUsageResponse` with `message_id` — some duplication but no breaking change.
3. Have the message endpoint return `RecommendationUsageResponse` but with `recommendation_id` repurposed — confusing.

**Decision**: Option 2 — create `MessageUsageResponse` with `message_id` field, sharing `UsageTotals` and `AgentUsageDetail` models. The `AgentUsageDetail` model needs a minor update: rename `domain` to `agent_name` (or add `agent_name` alongside) since chat agents don't have "domains". Actually, looking at the frontend, `AgentUsageDetail.domain` is displayed as the agent identifier. For chat, it would be "principal". The field name `domain` is somewhat misleading for chat, but changing it would break the existing recommendation flow. Keep `domain` as-is and populate it with `agent_name` from the llm_events table — the field serves as "agent identifier" in practice.

## R4: Frontend Message Usage Fetching Strategy

**Decision**: Fetch message usage lazily per assistant message using the existing `useQueries` pattern, similar to how recommendation usage is fetched.

**Rationale**: The EngineerView already fetches recommendation usage via `useQueries` keyed by recommendation IDs. For messages, the approach is the same: collect all assistant message IDs, create a query for each, and pass the results as a map to MessageList.

**Key consideration**: Messages are fetched via `useMessages(sessionId)` which returns the full conversation. Filter for `role === "assistant"` messages, then `useQueries` to fetch `/sessions/{sid}/messages/{mid}/usage` for each. Messages without usage data will get a 404 or empty response — the UI simply doesn't render UsageSummaryBar for those.

## R5: DriverFeedbackCard Duplicate Render Location

**Decision**: Remove lines 116-118 from `MessageList.tsx` (the map over `rec.driver_feedback` that renders `DriverFeedbackCard` outside RecommendationCard).

**Rationale**: `RecommendationCard` already renders `DriverFeedbackCard` at its lines 96-102 inside a `.ace-recommendation-card__feedback` div. The MessageList additionally renders the same feedback cards at lines 116-118, causing duplication. The fix is straightforward removal.

## R6: Chat Agent Tool Registration

**Decision**: Register `get_lap_detail` and `get_corner_metrics` tools on the chat agent in `make_chat_job()`.

**Rationale**: Currently the chat agent is a plain `Agent(model, system_prompt=...)` with no tools. For the principal agent to have access to these tools (as stated in the spec), they need to be registered. The tools are defined in `backend/ac_engineer/engineer/tools.py`. The chat pipeline needs to import and register them, and provide the necessary `AgentDeps` context.

**AgentDeps construction in make_chat_job()**: The chat job already has access to `session_id` and the analyzed session cache (`analyzed.json`). To construct `AgentDeps`:

1. Load the `AnalyzedSession` from the JSON cache via `load_analyzed_session(cache_dir)` — the same call the engineer pipeline makes.
2. Load `parameter_ranges` via `resolve_parameters(ac_install_path, car_name, db_path, session_setup=...)` using the car name from session metadata.
3. Build `AgentDeps` with: `analyzed_session`, `parameter_ranges`, `knowledge_fragments=[]`. Chat doesn't need pre-loaded knowledge — the `search_kb` tool could handle it dynamically, but the principal agent's `DOMAIN_TOOLS["principal"]` only includes `get_lap_detail` and `get_corner_metrics`, not `search_kb`.
4. Change the chat agent from `Agent[None, str]` to `Agent[AgentDeps, str]` and register only the tools in `DOMAIN_TOOLS["principal"]`.

**Graceful degradation**: If loading the `AnalyzedSession` or `parameter_ranges` fails (e.g., cache missing, resolver error), the chat job should proceed without tools — fall back to a plain `Agent[None, str]`. Tools are a capability enhancement, not a requirement for chat responses. This keeps the non-critical contract: tool registration failure must never prevent message delivery.
