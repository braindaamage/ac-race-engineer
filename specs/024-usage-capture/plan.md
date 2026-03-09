# Implementation Plan: Usage Capture

**Branch**: `024-usage-capture` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-usage-capture/spec.md`

## Summary

Instrument the AI engineer pipeline (`analyze_with_engineer()`) to capture token usage data from Pydantic AI result objects after each specialist agent executes, persist it via the existing `save_agent_usage()` storage function, log a summary per agent, and expose a new `GET /sessions/{session_id}/recommendations/{recommendation_id}/usage` endpoint that returns aggregated totals alongside per-agent breakdowns.

## Technical Context

**Language/Version**: Python 3.11 (conda env `ac-race-engineer`)
**Primary Dependencies**: FastAPI, Pydantic AI, pydantic v2, sqlite3 (stdlib)
**Storage**: SQLite — existing `agent_usage` and `tool_call_details` tables from Phase 9.1
**Testing**: pytest + pytest-asyncio + httpx (async test client)
**Target Platform**: Windows desktop (backend server)
**Project Type**: Desktop app backend (FastAPI server)
**Performance Goals**: Usage endpoint responds within 500ms
**Constraints**: Usage capture failures must never block the recommendation pipeline
**Scale/Scope**: 2 modified files, 2 new test files, 1 new test file + 4 new response models

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Usage data is observability; failures don't affect recommendations |
| II. Car-Agnostic Design | PASS | No car-specific logic; captures usage for any agent domain |
| III. Setup File Autonomy | N/A | No setup file operations |
| IV. LLM as Interpreter | PASS | No new LLM calls; only reading result metadata |
| V. Educational Explanations | N/A | No user-facing explanations |
| VI. Incremental Changes | PASS | Small, focused change to existing pipeline |
| VII. Desktop App as Primary Interface | N/A | Backend-only change |
| VIII. API-First Design | PASS | Pure functions in `ac_engineer/`, thin API route |
| IX. Separation of Concerns | PASS | Usage extraction in `ac_engineer/engineer/`, HTTP response models in `api/engineer/`, route in `api/routes/` |
| X. Desktop App Stack | N/A | No frontend changes |
| XI. LLM Provider Abstraction | PASS | Uses provider-agnostic `result.usage()` API |
| XII. Frontend Architecture | N/A | No frontend changes |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/024-usage-capture/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 quickstart guide
├── contracts/
│   └── usage-endpoint.md # API endpoint contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    engineer/
      agents.py            # MODIFY — add usage capture to analyze_with_engineer()
    storage/
      usage.py             # EXISTING — save_agent_usage(), get_agent_usage()
      models.py            # EXISTING — AgentUsage, ToolCallDetail
  api/
    engineer/
      serializers.py       # MODIFY — add 4 new response models
    routes/
      engineer.py          # MODIFY — add GET usage endpoint
  tests/
    engineer/
      test_usage_capture.py  # NEW — usage extraction + persistence tests
    api/
      test_usage_routes.py   # NEW — usage endpoint tests
```

**Structure Decision**: All changes fit within the existing backend structure. No new packages or directories needed. Tests follow the established pattern: `tests/engineer/` for core logic, `tests/api/` for route tests.

## Design Decisions

### D1: Collect-then-persist pattern

Usage data is collected into a list during the agent loop but persisted only after `save_recommendation()` completes successfully. This ensures the foreign key (`recommendation_id`) exists before inserting usage records.

**Alternative rejected**: Persisting usage inline during the loop would require the recommendation to already exist or would need deferred FK checks, which complicates the flow.

### D2: Tool call token estimation

Tool response tokens are estimated as `len(str(content)) // 4` from `ToolReturnPart.content`. This is an approximation since Pydantic AI doesn't provide per-tool-call token breakdowns.

**Alternative rejected**: Using a tokenizer library (tiktoken) for exact counts — adds a dependency for marginal accuracy gain on observability data.

### D3: Usage persistence after recommendation save

If `save_recommendation()` fails (already wrapped in try/except with warning log), usage records are skipped since they have no valid FK target. This is acceptable — usage data is worthless without the recommendation it belongs to.

### D4: Turn count from `usage.requests`

Pydantic AI's `RunUsage.requests` counts the number of LLM API requests made during the agent run. This maps directly to "conversation turns" — each request is one turn of the model processing input and generating output (possibly including tool calls).

## Complexity Tracking

No constitution violations to justify.
