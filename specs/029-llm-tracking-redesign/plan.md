# Implementation Plan: LLM Tracking Redesign + Chat Fixes

**Branch**: `029-llm-tracking-redesign` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-llm-tracking-redesign/spec.md`

## Summary

Replace the recommendation-coupled `agent_usage` and `tool_call_details` tables with decoupled `llm_events` and `llm_tool_calls` tables that support any LLM call origin via polymorphic `context_type`/`context_id`. Add token tracking to the chat pipeline (principal agent), expose a message usage API endpoint, display UsageSummaryBar on assistant chat messages, and fix the duplicate DriverFeedbackCard render in MessageList.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, Pydantic AI, React 18, TanStack Query v5, Zustand v5
**Storage**: SQLite via `backend/ac_engineer/storage/` module (stdlib sqlite3, WAL mode)
**Testing**: pytest (backend, 900+ tests), Vitest + Testing Library (frontend, 341 tests)
**Target Platform**: Windows desktop (Tauri v2 shell)
**Project Type**: Desktop app (Tauri + React frontend, FastAPI backend sidecar)
**Performance Goals**: N/A — tracking is non-critical, must not block main flows
**Constraints**: Usage capture failure must never prevent message/recommendation delivery
**Scale/Scope**: Single user, local SQLite, ~5 modified backend files, ~5 modified frontend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Usage tracking is non-critical; failures don't block data flows |
| II. Car-Agnostic Design | PASS | No car-specific logic involved |
| III. Setup File Autonomy | PASS | No setup file changes |
| IV. LLM as Interpreter | PASS | Chat agent uses Pydantic AI tools, not direct SDK calls |
| V. Educational Explanations | PASS | No changes to explanation generation |
| VI. Incremental Changes | PASS | Small, focused storage + API + UI changes |
| VII. Desktop App as Primary Interface | PASS | Frontend consumes API, no direct data access |
| VIII. API-First Design | PASS | New endpoint follows thin-wrapper pattern; storage logic in ac_engineer/ |
| IX. Separation of Concerns | PASS | Storage in ac_engineer/storage/, route in api/routes/, UI in frontend/ |
| X. Desktop App Stack | PASS | No changes to Tauri shell or sidecar lifecycle |
| XI. LLM Provider Abstraction | PASS | Chat agent uses Pydantic AI Agent, provider-agnostic |
| XII. Frontend Architecture | PASS | TanStack Query for server state, design tokens for colors, TypeScript strict |

**Post-design re-check**: All gates still pass. The chat agent tool registration uses existing Pydantic AI patterns. The polymorphic context_type/context_id avoids coupling to specific features.

## Project Structure

### Documentation (this feature)

```text
specs/029-llm-tracking-redesign/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research decisions
├── data-model.md        # Entity definitions and migration mapping
├── quickstart.md        # Implementation steps and verification
├── contracts/
│   ├── message-usage-endpoint.md   # GET /sessions/{sid}/messages/{mid}/usage
│   └── llm-events-storage.md       # save_llm_event / get_llm_events
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   ├── storage/
│   │   ├── models.py          # LlmEvent, LlmToolCall (replace AgentUsage, ToolCallDetail)
│   │   ├── db.py              # New migrations for llm_events, llm_tool_calls tables
│   │   ├── usage.py           # save_llm_event(), get_llm_events() (replace old functions)
│   │   └── __init__.py        # Updated exports
│   └── engineer/
│       └── agents.py          # Updated usage capture in analyze_with_engineer()
├── api/
│   ├── engineer/
│   │   ├── pipeline.py        # Chat usage capture + tool registration (imports resolve_parameters from ac_engineer.resolver)
│   │   └── serializers.py     # MessageUsageResponse model
│   └── routes/
│       └── engineer.py        # Updated rec usage + new message usage endpoint
└── tests/
    ├── storage/
    │   └── test_usage.py      # Rewritten for new schema
    ├── engineer/
    │   └── test_usage_capture.py  # Updated for LlmEvent
    └── api/
        └── test_usage_routes.py   # Updated + message usage tests

frontend/
├── src/
│   ├── lib/
│   │   └── types.ts           # MessageUsageResponse type
│   └── views/engineer/
│       ├── index.tsx           # Message usage queries
│       └── MessageList.tsx     # Usage bar on messages + remove duplicate feedback
└── tests/
    └── views/engineer/
        ├── MessageList.test.tsx     # Updated tests
        └── EngineerView.test.tsx    # Updated tests
```

**Structure Decision**: Existing web application structure (backend/ + frontend/). All changes are modifications to existing files — no new source directories.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
