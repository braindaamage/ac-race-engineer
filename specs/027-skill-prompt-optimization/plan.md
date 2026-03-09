# Implementation Plan: Skill Prompt Optimization

**Branch**: `027-skill-prompt-optimization` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/027-skill-prompt-optimization/spec.md`

## Summary

Rewrite the 5 markdown skill prompts in `backend/ac_engineer/engineer/skills/` to constrain agent output verbosity. Each specialist gets explicit output limits (max 3 changes, 1-2 sentence reasoning with mandatory data citation, 1 sentence expected_effect), a priority tiers section for signal confirmation, and corrected tool usage instructions. The orchestrator prompt gets synthesis constraints preventing physics re-explanation. No Python code, tests, API, or frontend changes are required.

## Technical Context

**Language/Version**: N/A — this feature modifies only markdown prompt files, no source code
**Primary Dependencies**: Pydantic AI (reads these files as system prompts at agent startup)
**Storage**: N/A
**Testing**: Existing 167 engineer tests (pytest) must continue to pass unchanged
**Target Platform**: Windows desktop app (unchanged)
**Project Type**: Desktop app with LLM agents (unchanged)
**Performance Goals**: Output tokens reduced from ~14,400 to under 7,000 per analysis (SC-001)
**Constraints**: Skill files must remain human-readable markdown (end users may customize)
**Scale/Scope**: 5 files modified: principal.md, balance.md, tyre.md, aero.md, technique.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | Signal confirmation tiers strengthen data integrity by requiring multi-lap evidence |
| II. Car-Agnostic Design | PASS | No car-specific logic introduced; prompts remain generic |
| III. Setup File Autonomy | PASS | No changes to setup file handling |
| IV. LLM as Interpreter | PASS | Agents still receive pre-processed metrics; no calculations requested |
| V. Educational Explanations | PASS | Each change still explains why and what driver will feel; just more concise |
| VI. Incremental Changes | PASS | Max 3 changes per domain aligns with "1-3 related parameters per iteration" |
| VII. Desktop App as Primary Interface | PASS | No UI changes |
| VIII. API-First Design | PASS | No API changes |
| IX. Separation of Concerns | PASS | Changes stay in ac_engineer/engineer/skills/ layer |
| X. Desktop App Stack | PASS | No desktop app changes |
| XI. LLM Provider Abstraction | PASS | Still using Pydantic AI agents; prompts are provider-agnostic |
| XII. Frontend Architecture Constraints | PASS | No frontend changes |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/027-skill-prompt-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── spec.md              # Feature specification
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/ac_engineer/engineer/skills/
├── principal.md         # MODIFIED — orchestrator synthesis constraints
├── balance.md           # MODIFIED — output limits, priority tiers, tool usage fix
├── tyre.md              # MODIFIED — output limits, priority tiers, tool usage fix
├── aero.md              # MODIFIED — output limits, priority tiers, tool usage fix
└── technique.md         # MODIFIED — output limits, priority tiers
```

**Structure Decision**: No new files or directories. All changes are in-place edits to 5 existing markdown files in the skills/ directory.
