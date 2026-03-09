# Research: Token Optimization

**Feature**: 026-token-optimization
**Date**: 2026-03-09

## R1: Pydantic AI Batch Tool Signatures

**Decision**: Batch tools accept `list[str]` or `list[int]` parameters directly. Pydantic AI serializes these as JSON arrays in the tool schema.

**Rationale**: Pydantic AI tools derive their JSON schema from Python type hints. `list[str]` maps to `{"type": "array", "items": {"type": "string"}}` which all LLM providers handle natively. No wrapper models needed.

**Alternatives considered**:
- Comma-separated string parameter: rejected — loses type safety, requires manual parsing, worse LLM tool-call accuracy.
- Pydantic model wrapper (`class BatchRequest(BaseModel): items: list[str]`): rejected — adds unnecessary complexity. Pydantic AI supports `list[str]` directly as a tool parameter.

## R2: Pydantic AI max_turns and UnexpectedModelBehavior

**Decision**: Pass `max_turns=5` to `agent.run()`. Catch `pydantic_ai.exceptions.UnexpectedModelBehavior` which is raised when the turn limit is exceeded.

**Rationale**: Pydantic AI's `Agent.run()` accepts `max_turns: int | None` parameter. When the agent exceeds this limit, it raises `UnexpectedModelBehavior` with a message indicating the model exceeded the turn limit. This is the documented behavior in Pydantic AI.

**Alternatives considered**:
- Custom middleware/callback to count turns: rejected — Pydantic AI has built-in support.
- Post-hoc truncation of message history: rejected — doesn't prevent token consumption, only masks it.

## R3: Knowledge Pre-loading via get_knowledge_for_signals

**Decision**: Use the existing `get_knowledge_for_signals()` function from `ac_engineer.knowledge` which takes an `AnalyzedSession` and returns deterministic `list[KnowledgeFragment]` via `SIGNAL_MAP` lookups. Filter to domain-relevant fragments and cap at 8 per agent.

**Rationale**: `get_knowledge_for_signals()` already implements deterministic signal-to-fragment mapping via `SIGNAL_MAP`. It uses set deduplication with insertion-order preservation. However, since `analyze_with_engineer()` receives a `SessionSummary` (not `AnalyzedSession`), and the signals are already detected and stored in `summary.signals`, we need to use the existing knowledge retrieval path differently.

The current code in `analyze_with_engineer()` already calls `search_knowledge(signal)` per signal and collects fragments. We will replace this with a call pattern that uses `SIGNAL_MAP` directly for deterministic results, or we filter the existing `all_knowledge` list per domain and inject it into the user prompt.

**Key insight**: The current `all_knowledge` pre-loading in `agents.py` already collects fragments via `search_knowledge()` per signal. The fragments are stored in `AgentDeps.knowledge_fragments` but never injected into the user prompt — the agent must call `search_kb` tool to access them. The fix is to:
1. Replace `search_knowledge()` with the deterministic `SIGNAL_MAP`-based lookup (already available via the knowledge index)
2. Filter fragments per domain based on `domain_signals`
3. Inject the filtered fragments into the user prompt text
4. Cap at 8 fragments per agent

**Alternatives considered**:
- Pass fragments only via AgentDeps (current approach): rejected — agent must call search_kb to see them, wasting a tool turn.
- Create a new knowledge retrieval function: rejected — existing infrastructure is sufficient, just needs to be used differently.

## R4: get_current_value Removal Safety

**Decision**: Remove `get_current_value` entirely. The data it returns (`active_setup_parameters[section]["VALUE"]`) is already present in the user prompt under "### Current Setup Parameters" section.

**Rationale**: `_build_user_prompt()` (line 286-299 of agents.py) already iterates `summary.active_setup_parameters` and outputs every `section.param = value` pair. The `get_current_value` tool reads the exact same data from `ctx.deps.session_summary.active_setup_parameters`. Every call is pure waste.

**Alternatives considered**:
- Keep tool but add "already in prompt" note: rejected — tool remains callable and wastes turns.
- Deprecation warning instead of removal: rejected — over-engineering for an internal tool that no user interacts with directly.

## R5: search_kb Result Limit Reduction

**Decision**: Reduce `search_kb` from 5 results to 2 results (`fragments[:2]`). Update tool docstring to note that primary knowledge is pre-loaded.

**Rationale**: With knowledge pre-loaded into the prompt (up to 8 fragments), the search tool becomes a supplementary fallback for edge cases. 2 results provide enough for targeted supplementary queries without the token overhead of 5 large fragments.

**Alternatives considered**:
- Remove search_kb entirely: rejected — spec requires it remain as fallback.
- Keep at 3 results: rejected — spec says "fewer than 5", and 2 is sufficient for a fallback.
