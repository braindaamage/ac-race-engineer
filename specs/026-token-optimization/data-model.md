# Data Model: Token Optimization

**Feature**: 026-token-optimization
**Date**: 2026-03-09

## Model Changes

No new models are introduced. No existing models are modified. All changes are confined to tool function signatures and agent orchestration logic.

## Affected Entities (unchanged structure)

### AgentDeps (no changes)

Already contains `knowledge_fragments: list[Any]` which stores pre-loaded fragments. This field continues to serve its existing purpose — the optimization changes how fragments are surfaced to agents (prompt injection vs. tool calls), not the data structure.

### KnowledgeFragment (no changes)

Structure: `source_file`, `section_title`, `content`, `tags`. Used as-is for prompt injection.

### SpecialistResult (no changes)

Output model for agent results. Unchanged.

### EngineerResponse (no changes)

Final combined response. Unchanged.

## Tool Signature Changes

### Removed

| Tool | Old Signature | Replacement |
|------|--------------|-------------|
| `get_current_value` | `(ctx, section: str) -> str` | None — data already in prompt |

### Modified (single-item → batch)

| Tool | Old Signature | New Signature |
|------|--------------|---------------|
| `get_setup_range` | `(ctx, section: str) -> str` | `(ctx, sections: list[str]) -> str` |
| `get_lap_detail` | `(ctx, lap_number: int) -> str` | `(ctx, lap_numbers: list[int]) -> str` |
| `get_corner_metrics` | `(ctx, corner_number: int, lap_number: int \| None = None) -> str` | `(ctx, corner_numbers: list[int], lap_number: int \| None = None) -> str` |

### Modified (reduced results)

| Tool | Change |
|------|--------|
| `search_kb` | `fragments[:5]` → `fragments[:2]`, updated docstring |

## Data Flow Changes

### Before (current)
```
signals → search_knowledge(signal) × N → all_knowledge in AgentDeps
                                          ↓ (not in prompt)
                                     agent calls search_kb tool → fragments in conversation history
                                     agent calls get_current_value → redundant data in history
                                     agent calls get_setup_range × N → N tool turns
```

### After (optimized)
```
signals → SIGNAL_MAP lookup → domain-filtered fragments (≤8)
                                          ↓ (injected into user prompt)
                                     agent has knowledge in initial context
                                     agent calls get_setup_ranges([...]) → 1 tool turn
                                     agent.run(max_turns=5) → bounded execution
```
