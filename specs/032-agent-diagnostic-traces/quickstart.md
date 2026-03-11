# Quickstart: Agent Diagnostic Traces

**Feature**: 032-agent-diagnostic-traces | **Date**: 2026-03-11

## Overview

This feature adds a diagnostic mode that captures complete AI agent conversation traces as Markdown files. The change spans 4 layers: config (1 field), trace capture (1 new module + 2 pipeline integrations), API (2 new endpoints), and frontend (toggle + indicator + modal viewer). Approximately 12 files modified or created.

## Implementation Order

### Layer 1: Configuration

1. **backend/ac_engineer/config/models.py** — Add `diagnostic_mode: bool = False` field to `ACConfig`. Add to `_serialize()` method.

### Layer 2: Trace Serialization (core module)

2. **backend/ac_engineer/engineer/trace.py** (NEW) — Core trace module:
   - `serialize_agent_trace(domain, system_prompt, user_prompt, result) -> dict` — Extract all messages from a Pydantic AI result into a structured dict. Iterate `result.all_messages()`, handle `SystemPromptPart`, `UserPromptPart`, `TextPart`, `ToolCallPart`, `ToolReturnPart`.
   - `format_trace_markdown(session_id, trace_type, context_id, agent_traces, timestamp) -> str` — Format a list of agent trace dicts into a single Markdown string with headings, code blocks, and clear structure.
   - `write_trace(traces_dir, trace_type, context_id, content) -> Path` — Write the Markdown string to `{traces_dir}/{type}_{id}.md`. Create directory if needed. Return file path.
   - `read_trace(traces_dir, trace_type, context_id) -> str | None` — Read trace file if it exists, return content or None.

### Layer 3: Trace Capture Integration

3. **backend/ac_engineer/engineer/agents.py** — In `analyze_with_engineer()`:
   - Accept new optional parameter `diagnostic_mode: bool = False`
   - After each `agent.run()` in the specialist loop (~line 610-616), if `diagnostic_mode` is true, call `serialize_agent_trace()` with the domain, system prompt, user prompt, and result. Collect into a list.
   - After recommendation persistence (~line 702), if diagnostic_mode and traces were collected, call `format_trace_markdown()` + `write_trace()` wrapped in try-except.
   - System prompt: access via `_load_skill_prompt(domain)` (already called during agent build)
   - User prompt: already built as `user_prompt` variable in the loop

4. **backend/api/engineer/pipeline.py** — In both pipeline functions:
   - **`make_engineer_job()`**: Read `config.diagnostic_mode` at pipeline start. Pass it to `analyze_with_engineer()` as the new parameter.
   - **`make_chat_job()`**: After `agent.run()` and `save_message()`, if `config.diagnostic_mode` is true, call `serialize_agent_trace()` for the chat agent, then `format_trace_markdown()` + `write_trace()`. Wrapped in try-except.

5. **backend/api/paths.py** — Add `get_traces_dir() -> Path` returning `get_data_dir() / "traces"`.

### Layer 4: API Endpoints

6. **backend/api/routes/engineer.py** — Add two new endpoints:
   - `GET /sessions/{session_id}/recommendations/{recommendation_id}/trace` — Read trace file for recommendation, return `TraceResponse`
   - `GET /sessions/{session_id}/messages/{message_id}/trace` — Read trace file for message, return `TraceResponse`
   - Both return `{"available": false, ...}` when no trace file exists (200 OK, not 404)

### Layer 5: Frontend — Settings Toggle

7. **frontend/src/views/settings/index.tsx** — Add diagnostic mode toggle in the Advanced section:
   - Add `diagnosticMode` local state initialized from `config.diagnostic_mode`
   - Add toggle control (checkbox or button pair) with label "Diagnostic Mode"
   - Include in `isDirty` check and `handleSave()` flow

### Layer 6: Frontend — Trace Display

8. **frontend/src/lib/types.ts** — Add `TraceResponse` interface and `diagnostic_mode` to config type
9. **frontend/src/hooks/useTrace.ts** (NEW) — `useTrace(sessionId, traceType, id)` hook using TanStack Query to fetch trace data
10. **frontend/src/views/engineer/TraceModal.tsx** (NEW) — Modal component that displays formatted trace Markdown content as preformatted text
11. **frontend/src/views/engineer/RecommendationCard.tsx** — Add trace indicator button; on click, open TraceModal
12. **frontend/src/views/engineer/MessageList.tsx** — Add trace indicator on assistant messages; on click, open TraceModal

## Testing

### Backend Tests

- **test_trace.py** (NEW): Test `serialize_agent_trace()` with mock Pydantic AI result objects, `format_trace_markdown()` output structure, `write_trace()`/`read_trace()` round-trip, missing file returns None
- **test_engineer_traces.py** (NEW): Test trace API endpoints — available trace returns content, missing trace returns `{available: false}`, verify correct file path resolution

### Frontend Tests

- **TraceModal.test.tsx** (NEW): Test modal renders trace content, handles empty/null content, close behavior
- **useTrace.test.ts** (NEW): Test hook fetches from correct endpoint, handles available/unavailable responses
- **Settings toggle**: Test diagnostic_mode toggle appears in Advanced section, isDirty reflects changes

## Commands

```bash
# Backend tests
conda run -n ac-race-engineer pytest backend/tests/ -v

# Frontend type check + tests
cd frontend && npx tsc --noEmit && npm run test
```
