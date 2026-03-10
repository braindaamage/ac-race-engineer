# Implementation Plan: Agent Tool Scoping

**Branch**: `028-agent-tool-scoping` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-agent-tool-scoping/spec.md`

## Summary

Restrict each specialist AI agent to only the tools relevant to its domain by introducing an explicit `DOMAIN_TOOLS` mapping. Currently `_build_specialist_agent()` registers all 4 tools on every agent. The fix replaces the hardcoded tool registration with a lookup from a centralized dictionary that matches each skill prompt's documented tool set.

## Technical Context

**Language/Version**: Python 3.11+ (conda env `ac-race-engineer`)
**Primary Dependencies**: Pydantic AI (agent framework with `agent.tool()` registration)
**Storage**: N/A (no storage changes)
**Testing**: pytest (conda env `ac-race-engineer`)
**Target Platform**: Windows desktop (backend component)
**Project Type**: Desktop app backend (AI agent orchestration)
**Performance Goals**: Reduce technique agent input tokens from ~37K to ~21K by eliminating irrelevant tool calls
**Constraints**: No changes to tool implementations, skill prompts, models, API, or frontend
**Scale/Scope**: 3 files modified (agents.py, __init__.py, test_agents.py)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | No change to data processing |
| II. Car-Agnostic Design | PASS | No car-specific logic |
| III. Setup File Autonomy | PASS | No change to setup file handling |
| IV. LLM as Interpreter | PASS | Reinforces this — agents get only tools they need for their interpretive role |
| V. Educational Explanations | PASS | No change to explanation generation |
| VI. Incremental Changes | PASS | Minimal, focused change |
| VII. Desktop App as Primary Interface | PASS | No UI changes |
| VIII. API-First Design | PASS | No API changes |
| IX. Separation of Concerns | PASS | Change is within `ac_engineer/engineer/` only |
| X. Desktop App Stack | PASS | No Tauri/React changes |
| XI. LLM Provider Abstraction | PASS | Pydantic AI tools still used; only registration scope changes |
| XII. Frontend Architecture | PASS | No frontend changes |

**Pre-design result**: All gates pass. No violations.
**Post-design result**: All gates still pass. The `DOMAIN_TOOLS` constant is pure Python data at module level — no framework coupling, no provider specifics.

## Project Structure

### Documentation (this feature)

```text
specs/028-agent-tool-scoping/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: research findings
├── data-model.md        # Phase 1: data model (DOMAIN_TOOLS constant)
├── quickstart.md        # Phase 1: verification instructions
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
  ac_engineer/
    engineer/
      agents.py          # MODIFIED: add DOMAIN_TOOLS, update _build_specialist_agent()
      __init__.py         # MODIFIED: export DOMAIN_TOOLS
  tests/
    engineer/
      test_agents.py     # MODIFIED: update tool registration assertions
```

**Structure Decision**: This is a surgical change to 3 existing files in the backend. No new files, no new directories, no frontend changes.

## Complexity Tracking

No constitution violations. Table intentionally left empty.
