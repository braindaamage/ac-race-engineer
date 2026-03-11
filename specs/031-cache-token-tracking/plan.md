# Implementation Plan: Cache Token Tracking

**Branch**: `031-cache-token-tracking` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-cache-token-tracking/spec.md`

## Summary

Add `cache_read_tokens` and `cache_write_tokens` fields to the LLM usage tracking pipeline. The Pydantic AI `RunUsage` object already provides these values from all three providers (Anthropic, OpenAI, Gemini) — they are simply not being read. This feature threads the two new integer fields through every layer: storage model → database schema → capture code → API serializers → API response computation → frontend types → UI components. Existing records default to 0; the UI conditionally shows cache information only when non-zero.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, Pydantic AI, React 18, TanStack Query v5, Zustand v5
**Storage**: SQLite via stdlib sqlite3 (additive ALTER TABLE migrations, currently at migration 6)
**Testing**: pytest (backend, conda env `ac-race-engineer`), Vitest + Testing Library (frontend)
**Target Platform**: Windows desktop (Tauri v2 shell)
**Project Type**: Desktop app (Tauri + React frontend, FastAPI backend sidecar)
**Performance Goals**: N/A — two additional integer columns, negligible overhead
**Constraints**: No destructive migration; backward compatible with pre-existing records
**Scale/Scope**: 8 files modified across 4 layers (storage, capture, API, frontend)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | New fields default to 0; no bad data introduced |
| II. Car-Agnostic Design | PASS | No car-specific logic |
| III. Setup File Autonomy | N/A | No setup file changes |
| IV. LLM as Interpreter | PASS | No LLM calculation changes; just metadata tracking |
| V. Educational Explanations | N/A | No user-facing explanations affected |
| VI. Incremental Changes | PASS | Minimal additive change across all layers |
| VII. Desktop App as Primary Interface | PASS | UI displays data from API; no logic duplication |
| VIII. API-First Design | PASS | Pure functions in `ac_engineer/`, thin API wrappers |
| IX. Separation of Concerns | PASS | Storage model → API serializer → frontend type, correct direction |
| X. Desktop App Stack | PASS | No changes to sidecar lifecycle |
| XI. LLM Provider Abstraction | PASS | Uses Pydantic AI RunUsage (provider-agnostic) |
| XII. Frontend Architecture | PASS | TanStack Query for server state, design tokens for colors, no `any` |

No violations. Gate passes.

## Project Structure

### Documentation (this feature)

```text
specs/031-cache-token-tracking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-usage.md     # Updated usage endpoint contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    storage/
      models.py          # ADD cache_read_tokens, cache_write_tokens to LlmEvent
      usage.py           # ADD cache columns to INSERT/SELECT in save/get functions
      db.py              # ADD migration 7: ALTER TABLE llm_events ADD COLUMN x2
    engineer/
      agents.py          # READ cache fields from result.usage() into LlmEvent
  api/
    engineer/
      serializers.py     # ADD cache fields to AgentUsageDetail, UsageTotals
      pipeline.py        # READ cache fields from result.usage() into LlmEvent
    routes/
      engineer.py        # SUM cache fields in _compute_usage_response()
  tests/
    storage/             # Tests for new fields in save/get
    engineer/            # Tests for cache field extraction
    api/                 # Tests for usage endpoint cache fields

frontend/
  src/
    lib/
      types.ts           # ADD cache fields to AgentUsageDetail, UsageTotals
    views/
      engineer/
        UsageSummaryBar.tsx    # SHOW cache_read_tokens when > 0
        UsageDetailModal.tsx   # SHOW cache_read/write per agent when > 0
  tests/
    views/
      engineer/          # Tests for conditional cache display
```

**Structure Decision**: Extends existing web application structure (backend + frontend). All changes are additive modifications to existing files — no new files created in source code.

## Complexity Tracking

> No constitution violations. Table intentionally left empty.
