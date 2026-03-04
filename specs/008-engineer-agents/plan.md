# Implementation Plan: Engineer Agents

**Branch**: `008-engineer-agents` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-engineer-agents/spec.md`

## Summary

Build the AI reasoning layer for AC Race Engineer using Pydantic AI agents. A principal orchestrator receives a SessionSummary, routes detected signals to domain-specific specialist agents (balance, tyres, aero, technique), and combines their outputs into a single EngineerResponse with validated setup changes and driver-friendly explanations. All agent interactions go through Pydantic AI with provider-agnostic model selection (Anthropic/OpenAI/Gemini). Setup changes are validated against parameter ranges before inclusion.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: pydantic-ai (new), pydantic>=2.0, existing ac_engineer modules
**Storage**: SQLite via existing storage module (save_recommendation, update_recommendation_status)
**Testing**: pytest with Pydantic AI TestModel/FunctionModel (no real LLM calls)
**Target Platform**: Windows (desktop app backend)
**Project Type**: Library module within existing backend package
**Performance Goals**: Complete analysis within 60 seconds end-to-end
**Constraints**: No direct provider SDK calls; all LLM via Pydantic AI; testable without AC installation
**Scale/Scope**: 5 system prompt files, 2 Python modules (agents.py, tools.py), ~40 tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Agents receive pre-validated SessionSummary from deterministic summarizer; LLM never sees raw telemetry |
| II. Car-Agnostic Design | PASS | No car-specific logic; parameter ranges read dynamically from car's data/setup.ini |
| III. Setup File Autonomy | PASS | apply_recommendation() uses existing atomic write pipeline (backup → validate → write) |
| IV. LLM as Interpreter | PASS | All metrics pre-computed; LLM only interprets and proposes via tool calls; no calculations |
| V. Educational Explanations | PASS | Every SetupChange requires reasoning + expected_effect in plain language |
| VI. Incremental Changes | PASS | Specialists propose targeted changes per domain, not wholesale rewrites |
| VII. CLI-First MVP | PASS | analyze_with_engineer() is a pure function callable from CLI/API/tests |
| VIII. API-First Design | PASS | All logic in ac_engineer/ as pure Python; no HTTP awareness |
| IX. Separation of Concerns | PASS | Agents live in ac_engineer/engineer/; no web framework imports |
| X. Desktop App Stack | N/A | Phase 7 |
| XI. LLM Provider Abstraction | PASS | Pydantic AI agents with model string from get_effective_model(); no direct SDK calls |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/008-engineer-agents/
├── plan.md              # This file
├── research.md          # Phase 0: Pydantic AI patterns, testing strategy
├── data-model.md        # Phase 1: Agent deps, tool schemas, response flow
├── quickstart.md        # Phase 1: How to run and test the agents
├── contracts/           # Phase 1: Public API contracts
│   └── agents-api.md   # analyze_with_engineer() and apply_recommendation()
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    engineer/
      agents.py          # NEW: PrincipalAgent orchestrator + specialist agent definitions
      tools.py           # NEW: Pydantic AI tool implementations (knowledge search, validation)
      skills/            # NEW: System prompt markdown files
      │ ├── principal.md # Orchestrator prompt
      │ ├── balance.md   # Balance specialist prompt
      │ ├── tyre.md      # Tyre specialist prompt
      │ ├── aero.md      # Aero specialist prompt
      │ └── technique.md # Technique specialist prompt
      __init__.py        # UPDATED: Add analyze_with_engineer(), apply_recommendation()
      models.py          # EXISTING: SessionSummary, EngineerResponse, SetupChange, etc.
      summarizer.py      # EXISTING: summarize_session()
      setup_reader.py    # EXISTING: read_parameter_ranges()
      setup_writer.py    # EXISTING: validate_changes(), apply_changes(), create_backup()
  tests/
    engineer/
      test_agents.py     # NEW: Agent orchestration tests (~20 tests)
      test_tools.py      # NEW: Tool function tests (~10 tests)
      test_integration.py # NEW: End-to-end pipeline tests (~10 tests)
      conftest.py        # UPDATED: Add agent test fixtures, mock models
```

**Structure Decision**: Extends existing `backend/ac_engineer/engineer/` module. New files (`agents.py`, `tools.py`, `skills/`) sit alongside existing Phase 5.2 files. Tests go in existing `backend/tests/engineer/` directory.

## Complexity Tracking

No constitution violations to justify.
