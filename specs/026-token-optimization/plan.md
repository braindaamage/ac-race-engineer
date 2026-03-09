# Implementation Plan: Token Optimization

**Branch**: `026-token-optimization` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-token-optimization/spec.md`

## Summary

Eliminate four token inefficiency patterns in the AI engineer pipeline: remove the redundant `get_current_value` tool, replace three single-item tools with batch versions accepting lists, inject pre-selected knowledge fragments into agent prompts, and enforce a hard turn limit (`max_turns=5`) on agent execution. All changes are confined to two existing files: `tools.py` and `agents.py`.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: Pydantic AI (pydantic-ai-slim[anthropic,openai,google]), Pydantic v2
**Storage**: N/A (no storage changes)
**Testing**: pytest with `pydantic_ai.models.test.TestModel` and `FunctionModel` — `ALLOW_MODEL_REQUESTS = False`
**Target Platform**: Windows desktop (backend component)
**Project Type**: Desktop app backend (pure Python library layer)
**Performance Goals**: ≥50% token reduction per analysis vs. pre-optimization baseline
**Constraints**: No new dependencies, no new files, no API/frontend changes, only 2 source files modified
**Scale/Scope**: 2 source files (`tools.py`, `agents.py`), 2 test files (`test_tools.py`, `test_agents.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity First | PASS | No telemetry processing changes. Batch tools return identical data to single-item versions. |
| II. Car-Agnostic Design | PASS | No car-specific logic introduced. All changes are generic across car types. |
| III. Setup File Autonomy | PASS | No setup file read/write changes. |
| IV. LLM as Interpreter | PASS | LLM still receives pre-processed metrics only. Knowledge injection adds domain context, not raw data. Tools remain Pydantic AI tools. |
| V. Educational Explanations | PASS | No changes to explanation generation. |
| VI. Incremental Changes | PASS | No changes to recommendation strategy. |
| VII. Desktop App as Primary Interface | PASS | No UI changes. |
| VIII. API-First Design | PASS | No API changes. All changes in `ac_engineer/` layer. |
| IX. Separation of Concerns | PASS | Changes confined to `ac_engineer/engineer/`. No cross-layer violations. |
| X. Desktop App Stack | N/A | No Tauri/frontend changes. |
| XI. LLM Provider Abstraction | PASS | Still uses Pydantic AI agents. `max_turns` is provider-agnostic. |
| XII. Frontend Architecture | N/A | No frontend changes. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-token-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── ac_engineer/
│   └── engineer/
│       ├── tools.py          # MODIFIED: remove get_current_value, batch tools, search_kb limit
│       └── agents.py         # MODIFIED: knowledge injection, max_turns, import cleanup
└── tests/
    └── engineer/
        ├── test_tools.py     # MODIFIED: update for batch signatures, remove get_current_value tests
        └── test_agents.py    # MODIFIED: update for max_turns, knowledge injection, removed tool
```

**Structure Decision**: No new files or directories. All changes are modifications to 4 existing files (2 source + 2 test).

## Design Decisions

### D1: tools.py — Remove get_current_value

Delete the `get_current_value` function entirely. Remove its import from `agents.py` and its registration in `_build_specialist_agent`. Remove corresponding tests from `test_tools.py`.

**Current state** (tools.py lines 47-64):
```python
async def get_current_value(ctx: RunContext[AgentDeps], section: str) -> str:
    ...
```

**After**: Function deleted. No replacement needed — data is already in user prompt (agents.py `_build_user_prompt` lines 286-299).

### D2: tools.py — Batch get_setup_range

Replace `get_setup_range(ctx, section: str)` with `get_setup_range(ctx, sections: list[str])`.

Returns a formatted string with one block per section, separated by blank lines. Each block uses the same format as the current single-item version. Sections not found get a "not found" line. Empty list returns empty string.

```python
async def get_setup_range(ctx: RunContext[AgentDeps], sections: list[str]) -> str:
```

### D3: tools.py — Batch get_lap_detail

Replace `get_lap_detail(ctx, lap_number: int)` with `get_lap_detail(ctx, lap_numbers: list[int])`.

Returns formatted string with one block per lap, separated by blank lines. Laps not found get a "not found" line. Empty list returns empty string.

```python
async def get_lap_detail(ctx: RunContext[AgentDeps], lap_numbers: list[int]) -> str:
```

### D4: tools.py — Batch get_corner_metrics

Replace `get_corner_metrics(ctx, corner_number: int, ...)` with `get_corner_metrics(ctx, corner_numbers: list[int], ...)`.

The optional `lap_number` parameter remains a single `int | None` (applies to all corners in the batch). Returns formatted string with one block per corner. Corners with no issues get a "not found" line. Empty list returns empty string.

```python
async def get_corner_metrics(
    ctx: RunContext[AgentDeps],
    corner_numbers: list[int],
    lap_number: int | None = None,
) -> str:
```

### D5: tools.py — search_kb Result Limit

Change `fragments[:5]` to `fragments[:2]`. Update docstring to indicate primary knowledge is pre-loaded and this tool is for supplementary searches only.

### D6: agents.py — Knowledge Pre-loading into User Prompt

Modify `_build_user_prompt` to accept an additional `knowledge_fragments: list[KnowledgeFragment]` parameter. Insert a "### Vehicle Dynamics Knowledge" section into the prompt after the signals section and before corner issues.

Each fragment is formatted as:
```
**[source_file > section_title]**
content
```

Fragments are capped at 8 (enforced at call site in `analyze_with_engineer`).

If the fragment list is empty, the section header is still included with a note: "No pre-loaded knowledge for these signals. Use the search_kb tool if you need vehicle dynamics information."

### D7: agents.py — Deterministic Knowledge Selection per Domain

Replace the current `search_knowledge(signal)` loop with a deterministic approach using `SIGNAL_MAP` from `ac_engineer.knowledge.index`. For each domain's signals, look up the (doc, section) pairs in `SIGNAL_MAP`, deduplicate by (doc, section) in insertion order, retrieve fragments from the docs cache, and cap at 8 per agent.

This replaces the current code at lines 473-480:
```python
# Current (non-deterministic search_knowledge)
all_knowledge: list[KnowledgeFragment] = []
for signal in summary.signals:
    frags = search_knowledge(signal)
    for frag in frags[:3]:
        if frag not in all_knowledge:
            all_knowledge.append(frag)
```

With a per-domain fragment selection inside the domain loop:
```python
# New (deterministic SIGNAL_MAP lookup, per domain)
domain_fragments = _select_knowledge_fragments(domain_signals)  # ≤ 8
```

The helper function `_select_knowledge_fragments` is a private function in `agents.py`:
```python
def _select_knowledge_fragments(signals: list[str]) -> list[KnowledgeFragment]:
    """Select knowledge fragments for a set of signals using SIGNAL_MAP.

    Deterministic: same signals always produce same fragments in same order.
    Capped at 8 fragments.
    """
```

### D8: agents.py — max_turns and Error Isolation

Add `max_turns=5` to the `agent.run()` call. Wrap the call in `try/except` that catches `UnexpectedModelBehavior` (from `pydantic_ai.exceptions`) in addition to the existing generic `Exception`. Log a warning when the turn limit is hit. The agent's results are excluded (same as current behavior for any exception), and remaining agents continue.

**Current** (line 516):
```python
result = await agent.run(user_prompt, deps=deps)
```

**After**:
```python
from pydantic_ai.exceptions import UnexpectedModelBehavior

try:
    result = await agent.run(user_prompt, deps=deps, max_turns=5)
except UnexpectedModelBehavior:
    logger.warning("Agent '%s' exceeded turn limit (max_turns=5)", domain)
    continue
except Exception:
    logger.exception("Specialist '%s' failed", domain)
    continue
```

### D9: agents.py — Import Cleanup

- Remove `get_current_value` from the tools import
- Remove `search_knowledge as kb_search` import (replaced by SIGNAL_MAP-based lookup)
- Add `from pydantic_ai.exceptions import UnexpectedModelBehavior`
- Add `from ac_engineer.knowledge.index import SIGNAL_MAP`
- Add `from ac_engineer.knowledge.loader import get_docs_cache`

### D10: agents.py — _build_specialist_agent Tool Registration

Remove `agent.tool(get_current_value)` from line 217. The agent now registers 4 tools instead of 5:
1. `search_kb` (fallback, reduced to 2 results)
2. `get_setup_range` (batch)
3. `get_lap_detail` (batch)
4. `get_corner_metrics` (batch)

## Post-Design Constitution Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| IV. LLM as Interpreter | PASS | Knowledge injection provides context, not raw data. LLM still reasons over pre-computed metrics. |
| VIII. API-First Design | PASS | `ac_engineer/` remains HTTP-free. No web framework imports. |
| IX. Separation of Concerns | PASS | Knowledge module accessed via its public API (`SIGNAL_MAP`, `get_docs_cache`). No cross-layer violations. |
| XI. LLM Provider Abstraction | PASS | `max_turns` is Pydantic AI built-in, provider-agnostic. |

**Gate result**: PASS — no violations post-design.
