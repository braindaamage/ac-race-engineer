# Implementation Plan: Principal Narrated Analysis

**Branch**: `033-principal-narrated-analysis` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/033-principal-narrated-analysis/spec.md`

## Summary

Replace the mechanical concatenation of specialist `domain_summary` fields with a principal-agent-authored narrative. After all specialist agents complete, a new synthesis step invokes the principal agent (no tools, structured output) to produce two distinct fields: `summary` (executive headline, 2–4 sentences) and `explanation` (detailed multi-paragraph narrative). Persist `explanation` in the SQLite recommendations table and display it in a collapsible section in the frontend's RecommendationCard.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: Pydantic AI (agents, structured output), FastAPI, React 18, TanStack Query v5, Zustand v5
**Storage**: SQLite (stdlib sqlite3) — add `explanation` column to `recommendations` table
**Testing**: pytest (backend, conda env `ac-race-engineer`), Vitest + Testing Library (frontend)
**Target Platform**: Windows desktop (Tauri v2)
**Project Type**: Desktop app with backend API
**Performance Goals**: Principal agent adds 1 LLM roundtrip per analysis; ≤5 request limit; summary ≤80 words, explanation ≤300 words
**Constraints**: Graceful fallback on principal agent failure; no changes to specialist agent prompts
**Scale/Scope**: ~12 files modified, ~8 new test files/sections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | ✅ PASS | Principal agent receives pre-validated specialist results; no raw telemetry processing |
| II. Car-Agnostic Design | ✅ PASS | No car-specific logic; operates on generic SpecialistResult data |
| III. Setup File Autonomy | ✅ PASS | No setup file reads/writes; narrative only |
| IV. LLM as Interpreter, Not Calculator | ✅ PASS | Principal agent synthesizes narrative from pre-computed metrics; no calculations. Uses Pydantic AI structured output. |
| V. Educational Explanations | ✅ PASS | Core purpose of the feature — explanation field is explicitly educational |
| VI. Incremental Changes | ✅ PASS | Narrative describes existing specialist-proposed changes; doesn't add new ones |
| VII. Desktop App as Primary Interface | ✅ PASS | Frontend displays explanation via API |
| VIII. API-First Design | ✅ PASS | Synthesis logic lives in `ac_engineer/engineer/agents.py`; API route is thin wrapper |
| IX. Separation of Concerns | ✅ PASS | LLM call in ac_engineer/, HTTP in api/, display in frontend/ |
| X. Desktop App Stack | ✅ PASS | No changes to Tauri/sidecar infrastructure |
| XI. LLM Provider Abstraction | ✅ PASS | Uses build_model() + Pydantic AI Agent; provider-agnostic |
| XII. Frontend Architecture Constraints | ✅ PASS | Uses existing TanStack Query data flow; CSS tokens for styling; TypeScript strict |

**Gate result**: ALL PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/033-principal-narrated-analysis/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions
├── data-model.md        # Phase 1: Data model changes
├── quickstart.md        # Phase 1: Implementation quickstart
├── contracts/
│   └── api.md           # API contract changes
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (files to modify)

```text
backend/
  ac_engineer/
    engineer/
      models.py              # Add PrincipalNarrative model
      agents.py              # Add _synthesize_with_principal(); update analyze_with_engineer()
      skills/
        principal.md         # Adapt prompt for structured summary + explanation output
    storage/
      db.py                  # Add migration for explanation column
      recommendations.py     # Add explanation param to save/get
  api/
    engineer/
      pipeline.py            # Pass explanation to save_recommendation()
    routes/
      engineer.py            # Read explanation from DB in get_recommendation_detail()
  tests/
    engineer/
      test_agents.py         # Tests for principal synthesis
    storage/
      test_recommendations.py # Tests for explanation column
    api/
      test_engineer_routes.py # Tests for explanation in response

frontend/
  src/
    views/engineer/
      RecommendationCard.tsx   # Collapsible explanation section
      RecommendationCard.css   # Styles for expandable section (if needed)
  tests/
    views/engineer/
      RecommendationCard.test.tsx  # Tests for expand/collapse and empty state
```

**Structure Decision**: Brownfield modification of existing project structure. No new packages or directories created beyond what already exists.

## Complexity Tracking

> No constitution violations — section intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
