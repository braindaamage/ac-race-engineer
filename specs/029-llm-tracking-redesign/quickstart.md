# Quickstart: LLM Tracking Redesign + Chat Fixes

**Branch**: `029-llm-tracking-redesign` | **Date**: 2026-03-10

## Prerequisites

- conda env `ac-race-engineer` with Python 3.11+
- Node.js 20 LTS + npm
- Existing backend tests passing: `conda run -n ac-race-engineer pytest backend/tests/ -v`
- Existing frontend tests passing: `cd frontend && npm run test`

## Implementation Order

### Step 1: Storage Layer (backend/ac_engineer/storage/)

1. **models.py**: Replace `AgentUsage` + `ToolCallDetail` with `LlmEvent` + `LlmToolCall` Pydantic v2 models. Remove `VALID_DOMAINS`.
2. **db.py**: Replace migrations 5-6 (agent_usage, tool_call_details) with llm_events + llm_tool_calls DDL. No CHECK constraints on event_type/context_type.
3. **usage.py**: Replace `save_agent_usage()` / `get_agent_usage()` with `save_llm_event()` / `get_llm_events(context_type, context_id)`.
4. **__init__.py**: Update exports.
5. **Tests**: Update `backend/tests/storage/test_usage.py` for new models, functions, and table schema.

### Step 2: Engineer Pipeline (backend/ac_engineer/engineer/)

6. **agents.py**: Update `analyze_with_engineer()` to build `LlmEvent` instead of `AgentUsage`. Set `event_type="analysis"`, `context_type="recommendation"`, `context_id=recommendation_id`. Call `save_llm_event()`.
7. **Tests**: Update `backend/tests/engineer/test_usage_capture.py`.

### Step 3: Chat Pipeline (backend/api/engineer/)

8. **pipeline.py**: Construct `AgentDeps` and register tools on the chat agent, then capture usage:
   - **Before `agent.run()`** — build AgentDeps with graceful fallback:
     1. Load `AnalyzedSession` from JSON cache via `load_analyzed_session(cache_dir)` (already loaded for summarization).
     2. Load `parameter_ranges` via `resolve_parameters(ac_install_path, car_name, db_path, session_setup=...)` — import from `ac_engineer.resolver`.
     3. Build `AgentDeps(analyzed_session=analyzed, parameter_ranges=parameter_ranges, knowledge_fragments=[])`.
     4. Create `Agent[AgentDeps, str]` with tools from `DOMAIN_TOOLS["principal"]` (`get_lap_detail`, `get_corner_metrics`).
     5. If loading AnalyzedSession or parameter_ranges fails, fall back to plain `Agent[None, str]` without tools — tools are a capability enhancement, not a requirement.
   - **After `agent.run()`** — capture usage:
     - Extract usage via `result.usage()` and tool calls via `_extract_tool_calls()`.
     - Build `LlmEvent` with `event_type="chat"`, `agent_name="principal"`, `context_type="message"`, `context_id=message_id`.
     - Wrap `save_llm_event()` in try/except so tracking failure doesn't block message delivery.

### Step 4: API Endpoint (backend/api/)

9. **serializers.py**: Add `MessageUsageResponse` model (mirrors `RecommendationUsageResponse` with `message_id`).
10. **routes/engineer.py**: Update `get_recommendation_usage()` to call `get_llm_events("recommendation", rec_id)`. Add new endpoint `GET /sessions/{sid}/messages/{mid}/usage` calling `get_llm_events("message", mid)`.
11. **Tests**: Update `backend/tests/api/test_usage_routes.py`, add message usage endpoint tests.

### Step 5: Frontend — Message Usage Display

12. **types.ts**: Add `MessageUsageResponse` type.
13. **EngineerView (index.tsx)**: Add `useQueries` for assistant message usage alongside existing recommendation usage queries.
14. **MessageList.tsx**: Accept `messageUsageMap` prop, render `UsageSummaryBar` below assistant messages that have usage data.

### Step 6: Frontend — Driver Feedback Fix

15. **MessageList.tsx**: Remove the `rec.driver_feedback.map(...)` block (lines 116-118) that duplicates DriverFeedbackCard rendering outside RecommendationCard.
16. **Tests**: Add/update frontend tests for the fix and for message usage display.

## Verification

```bash
# Backend tests
conda run -n ac-race-engineer pytest backend/tests/storage/test_usage.py -v
conda run -n ac-race-engineer pytest backend/tests/engineer/test_usage_capture.py -v
conda run -n ac-race-engineer pytest backend/tests/api/test_usage_routes.py -v
conda run -n ac-race-engineer pytest backend/tests/ -v  # Full suite

# Frontend tests
cd frontend && npm run test
cd frontend && npx tsc --noEmit

# Delete DB to force recreation with new schema
rm data/ac_engineer.db
```

## Key Files to Modify

| File | Change |
|------|--------|
| `backend/ac_engineer/storage/models.py` | Replace AgentUsage/ToolCallDetail with LlmEvent/LlmToolCall |
| `backend/ac_engineer/storage/db.py` | Replace migrations 5-6 with llm_events/llm_tool_calls DDL |
| `backend/ac_engineer/storage/usage.py` | Replace save/get functions with new signatures |
| `backend/ac_engineer/storage/__init__.py` | Update exports |
| `backend/ac_engineer/engineer/agents.py` | Update usage capture to use LlmEvent |
| `backend/api/engineer/pipeline.py` | Add chat usage capture + tool registration |
| `backend/api/engineer/serializers.py` | Add MessageUsageResponse |
| `backend/api/routes/engineer.py` | Update rec usage endpoint, add message usage endpoint |
| `frontend/src/lib/types.ts` | Add MessageUsageResponse type |
| `frontend/src/views/engineer/index.tsx` | Add message usage queries |
| `frontend/src/views/engineer/MessageList.tsx` | Add usage bar, remove duplicate feedback render |
| `backend/tests/storage/test_usage.py` | Rewrite for new schema |
| `backend/tests/engineer/test_usage_capture.py` | Update for LlmEvent |
| `backend/tests/api/test_usage_routes.py` | Update + add message usage tests |
