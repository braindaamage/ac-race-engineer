# Quickstart: Usage Capture

## What this feature does

Instruments the AI engineer pipeline to automatically capture and persist token usage data after each specialist agent executes. Adds one new API endpoint to retrieve usage data for a recommendation.

## Files to modify

1. **`backend/ac_engineer/engineer/agents.py`** — Add usage capture logic to the specialist agent loop in `analyze_with_engineer()`. Collect usage data per agent, persist after recommendation is saved.

2. **`backend/api/engineer/serializers.py`** — Add 4 new response models: `ToolCallInfo`, `AgentUsageDetail`, `UsageTotals`, `RecommendationUsageResponse`.

3. **`backend/api/routes/engineer.py`** — Add `GET /{session_id}/recommendations/{recommendation_id}/usage` route.

## Files to create

4. **`backend/tests/engineer/test_usage_capture.py`** — Tests for the usage extraction and persistence logic in agents.py.

5. **`backend/tests/api/test_usage_routes.py`** — Tests for the new usage endpoint.

## Key patterns to follow

- **Usage extraction**: `result.usage()` returns `RunUsage` with `input_tokens`, `output_tokens`, `requests`, `tool_calls`
- **Tool call extraction**: Iterate `result.all_messages()`, find `ToolReturnPart` in `ModelRequest.parts`, estimate tokens from `len(str(content)) // 4`
- **Error isolation**: All usage code wrapped in try/except, logs warning, never raises
- **Timing**: `time.perf_counter()` before/after `agent.run()`
- **Persistence order**: Collect during loop → persist after `save_recommendation()` → use returned `recommendation_id`
- **API guard pattern**: Same 404 check pattern as existing recommendation endpoints

## Running tests

```bash
conda activate ac-race-engineer
pytest backend/tests/engineer/test_usage_capture.py -v
pytest backend/tests/api/test_usage_routes.py -v
```
