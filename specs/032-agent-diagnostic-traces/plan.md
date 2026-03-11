# Implementation Plan: Agent Diagnostic Traces

**Branch**: `032-agent-diagnostic-traces` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/032-agent-diagnostic-traces/spec.md`

## Summary

Add a diagnostic mode that captures complete multi-turn agent conversation traces during engineer analysis and chat interactions. When enabled via a config toggle, the system serializes every Pydantic AI message (system prompts, user prompts, assistant messages, tool calls with parameters, tool responses, structured outputs) into human-readable Markdown files stored in `data/traces/`. Traces are keyed by recommendation ID (analysis) or message ID (chat), exposed via two new API endpoints, and viewable in the frontend with a trace indicator and modal viewer.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, Pydantic AI, React 18, TanStack Query v5, Zustand v5
**Storage**: Files on disk (`data/traces/`); no database changes. Config field in `config.json`.
**Testing**: pytest (backend, conda env `ac-race-engineer`), Vitest + Testing Library (frontend)
**Target Platform**: Windows desktop (Tauri v2 shell)
**Project Type**: Desktop app (Tauri + React frontend, FastAPI backend sidecar)
**Performance Goals**: Zero overhead when diagnostic mode is off. Trace writing is fire-and-forget after the primary result.
**Constraints**: Trace capture must never block or fail the engineer/chat pipeline. No database storage.
**Scale/Scope**: ~12 files modified/created across 4 layers (config, trace capture, API, frontend)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Traces are supplementary files; no telemetry/setup data modified |
| II. Car-Agnostic Design | PASS | No car-specific logic |
| III. Setup File Autonomy | N/A | No setup file changes |
| IV. LLM as Interpreter | PASS | Captures LLM interactions for debugging, no LLM behavior changes |
| V. Educational Explanations | N/A | No user-facing explanations affected |
| VI. Incremental Changes | PASS | Additive feature; all existing functionality unchanged |
| VII. Desktop App as Primary Interface | PASS | UI displays trace data from API |
| VIII. API-First Design | PASS | New trace module in `ac_engineer/`, thin API endpoints |
| IX. Separation of Concerns | PASS | Trace serialization in core package, API routes wrap it, frontend displays |
| X. Desktop App Stack | PASS | No sidecar lifecycle changes |
| XI. LLM Provider Abstraction | PASS | Uses Pydantic AI message types (provider-agnostic) |
| XII. Frontend Architecture | PASS | TanStack Query for trace data, design tokens for styling |

No violations. Gate passes.

## Project Structure

### Documentation (this feature)

```text
specs/032-agent-diagnostic-traces/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-traces.md    # New trace endpoint contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    config/
      models.py          # ADD diagnostic_mode: bool = False to ACConfig
    engineer/
      trace.py           # NEW — serialize_trace(), write_trace() functions
      agents.py          # ADD trace capture after each specialist agent.run()
    __init__.py          # ADD trace to public exports (if needed)
  api/
    engineer/
      pipeline.py        # ADD trace capture in make_engineer_job and make_chat_job
    routes/
      engineer.py        # ADD GET .../recommendations/{id}/trace and .../messages/{id}/trace
    paths.py             # ADD get_traces_dir() helper
  tests/
    engineer/
      test_trace.py      # NEW — tests for serialize/write functions
    api/
      test_engineer_traces.py  # NEW — tests for trace API endpoints

frontend/
  src/
    lib/
      types.ts           # ADD TraceResponse type
    hooks/
      useTrace.ts        # NEW — useTrace(type, id) hook
    views/
      engineer/
        TraceModal.tsx    # NEW — modal to display formatted trace content
        MessageList.tsx   # ADD trace indicator on assistant messages
        RecommendationCard.tsx  # ADD trace indicator on recommendations
      settings/
        index.tsx         # ADD diagnostic mode toggle in Advanced section
  tests/
    views/
      engineer/
        TraceModal.test.tsx  # NEW — trace modal tests
    hooks/
      useTrace.test.ts       # NEW — trace hook tests
```

**Structure Decision**: Extends existing web application structure (backend + frontend). Core trace serialization logic lives in `ac_engineer/engineer/trace.py` (new file — justified because trace serialization is a distinct concern). All other changes modify existing files.

## Complexity Tracking

> No constitution violations. Table intentionally left empty.
