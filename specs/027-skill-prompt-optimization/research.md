# Research: Skill Prompt Optimization

**Feature**: 027-skill-prompt-optimization
**Date**: 2026-03-09

## Research Summary

This feature has no unknowns requiring research. The implementation scope is fully defined by the user's detailed instructions and the existing codebase. All decisions are documented below.

## R1: Current Prompt Structure and Verbosity Sources

**Decision**: Rewrite all 5 skill markdown files with explicit output constraints.

**Rationale**: The current prompts give qualitative guidance ("keep changes incremental", "concise but complete") without hard limits. LLMs, especially capable ones like Gemini 2.5 Flash, interpret "complete" as permission to be exhaustive. Adding explicit numerical limits (max 3 changes, 1-2 sentence reasoning) is the most direct way to constrain output.

**Current state of each file**:
- `balance.md` (33 lines): Has Output Requirements but no count limit. References `get_current_value` tool (no longer exists). `search_kb` listed first in Tool Usage.
- `tyre.md` (32 lines): Same structure as balance. References `get_current_value`. No count limit.
- `aero.md` (31 lines): Same structure. References `get_current_value`. Has "small changes only" but no count limit.
- `technique.md` (32 lines): Has DriverFeedback format but no count limit. No priority tiers.
- `principal.md` (23 lines): General orchestration guidance. No output length constraints. No explicit prohibition on re-explaining specialist physics.

## R2: Tool Availability

**Decision**: Remove all references to `get_current_value` from specialist prompts. Current setup values are provided in the user prompt under `### Current Setup Parameters`.

**Rationale**: The `get_current_value` tool was removed in a previous phase. The `_build_user_prompt()` function in `agents.py` already injects current setup parameter values directly into the prompt context. Referencing a non-existent tool wastes agent turns attempting failed tool calls.

**Alternatives considered**: Adding a stub tool that reads from context — rejected as unnecessary complexity when the data is already in the prompt.

## R3: Priority Tiers Design

**Decision**: Use a three-tier system: Propose / Mention with low confidence / Omit.

**Rationale**: Aligns with FR-006's signal confirmation rules. The "Mention with low confidence" tier preserves potentially useful information (e.g., signal in 1 lap only) without the weight of a full recommendation. The "Omit" tier handles marginal, absent, or out-of-domain findings.

**Signal confirmation thresholds** (from FR-006):
- Sessions with 2-3 flying laps: signal must appear in at least 2 laps
- Sessions with >3 flying laps: signal must appear in the majority

## R4: Orchestrator Constraints

**Decision**: Add explicit Output Requirements and Tool Usage sections to principal.md. Make explicit that the orchestrator does not propose setup changes and does not repeat specialist reasoning.

**Rationale**: The current principal.md is 23 lines of general guidance with no structural constraints. Adding the same Output Requirements pattern used by specialists creates consistency and enforceable limits. Adding available tools (get_lap_detail, get_corner_metrics) for contextual verification gives the orchestrator data access without encouraging it to re-analyze from scratch.

## R5: search_kb Tool Positioning

**Decision**: Move `search_kb` to the end of Tool Usage in all specialist prompts, with a note that relevant knowledge is pre-loaded in context.

**Rationale**: The `_build_user_prompt()` function already injects up to 8 knowledge fragments based on detected signals. Listing `search_kb` first encourages agents to call it before reading the pre-loaded context, wasting API calls. Moving it last with a "pre-loaded" note reduces unnecessary tool calls.
