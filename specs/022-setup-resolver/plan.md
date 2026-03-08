# Implementation Plan: Tiered Setup Parameter Resolver

**Branch**: `022-setup-resolver` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/022-setup-resolver/spec.md`

## Summary

Replace the current single-path setup parameter lookup with a three-tier resolution strategy (open data → ACD decryption → session fallback) that provides complete parameter ranges and default values for all Assetto Corsa cars. Results from Tier 1 and 2 are cached in SQLite. A new resolver module orchestrates the tiers, a new API router exposes car status and cache management, and a new "Car Data" section in the Settings view gives users visibility and control.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, sqlite3 (stdlib), React 18, TanStack Query v5, Zustand v5
**Storage**: SQLite (`data/ac_engineer.db`) — new `parameter_cache` table
**Testing**: pytest (backend), Vitest + Testing Library (frontend)
**Target Platform**: Windows desktop (Tauri v2 shell)
**Project Type**: Desktop app (Tauri + React frontend, FastAPI backend sidecar)
**Performance Goals**: Cache hit resolution < 50ms; car list scan < 3 seconds for 200+ cars
**Constraints**: No startup scanning; resolution on-demand only; no modification of car data files
**Scale/Scope**: ~200-500 installed cars typical; 10-40 setup parameters per car

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Resolution never fabricates data; missing defaults left as null |
| II. Car-Agnostic Design | PASS | Resolver handles any car folder; default mapping is pattern-based, not car-specific |
| III. Setup File Autonomy | PASS | Read-only — never writes to car data files (FR-018) |
| IV. LLM as Interpreter | PASS | All resolution logic is deterministic Python; LLM receives pre-resolved data |
| V. Educational Explanations | PASS | Tier notice explains data quality to user in plain language |
| VI. Incremental Changes | N/A | Not relevant to resolution feature |
| VII. Desktop App as Primary Interface | PASS | Car data management integrated into Settings view |
| VIII. API-First Design | PASS | Resolver module is in `ac_engineer/`; API route is a thin wrapper |
| IX. Separation of Concerns | PASS | `resolver/` = pure computation; `api/routes/cars.py` = HTTP wrapper; `frontend/` = UI only |
| X. Desktop App Stack | PASS | Frontend consumes `/cars` endpoints via HTTP |
| XI. LLM Provider Abstraction | N/A | No LLM interaction in resolver |
| XII. Frontend Architecture Constraints | PASS | TanStack Query for server state; design tokens for colors; ace- CSS prefix; TypeScript strict |

**Post-Phase 1 re-check**: All principles still satisfied. The resolver module is pure Python in `ac_engineer/`, never imports from `api/`, and the frontend only communicates via HTTP. No constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/022-setup-resolver/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: research decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: getting started guide
├── contracts/
│   └── api-endpoints.md # Phase 1: API contract definitions
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   ├── resolver/                    # NEW — core resolution package
│   │   ├── __init__.py              # Public API exports
│   │   ├── models.py               # ResolvedParameters, ResolutionTier, CarStatus
│   │   ├── resolver.py             # resolve_parameters() — tier evaluation + orchestration
│   │   ├── defaults.py             # extract_defaults() — config file → default value mapping
│   │   └── cache.py                # SQLite cache CRUD (get/save/invalidate)
│   ├── engineer/
│   │   └── models.py               # MODIFIED — add resolution_tier, tier_notice to EngineerResponse + AgentDeps
│   └── storage/
│       └── db.py                   # MODIFIED — add parameter_cache table to migrations
├── api/
│   ├── main.py                     # MODIFIED — register cars_router
│   ├── routes/
│   │   └── cars.py                 # NEW — GET /cars, GET /cars/{car_name}/parameters, DELETE endpoints
│   └── engineer/
│       └── pipeline.py             # MODIFIED — use resolve_parameters() in engineer pipeline
└── tests/
    ├── resolver/                    # NEW — resolver test suite
    │   ├── conftest.py             # Fixtures: mock car dirs, ACD archives, DB
    │   ├── test_resolver.py        # Tier evaluation logic tests
    │   ├── test_defaults.py        # Default extraction tests
    │   └── test_cache.py           # Cache CRUD tests
    └── api/
        └── test_cars_route.py      # NEW — API endpoint tests

frontend/
├── src/
│   ├── views/settings/
│   │   ├── index.tsx               # MODIFIED — add CarDataSection card
│   │   ├── CarDataSection.tsx      # NEW — car data management UI component
│   │   ├── CarDataSection.css      # NEW — styles (ace-car-data prefix)
│   │   └── Settings.css            # UNCHANGED
│   ├── hooks/
│   │   └── useCars.ts              # NEW — TanStack Query hook for /cars endpoints
│   └── lib/
│       └── types.ts                # MODIFIED — add CarStatus, CarListResponse types
└── tests/
    ├── views/settings/
    │   └── CarDataSection.test.tsx  # NEW — component tests
    └── hooks/
        └── useCars.test.ts          # NEW — hook tests
```

**Structure Decision**: Follows the existing web application structure (backend + frontend). New `resolver/` package is a peer to `engineer/`, `parser/`, `acd_reader/` — each major capability is its own package. The API route follows the existing router pattern. The frontend extends the existing Settings view rather than creating a new top-level view.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
