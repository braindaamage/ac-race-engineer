# Tasks: Token Optimization

**Input**: Design documents from `/specs/026-token-optimization/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Required — FR-017 mandates all existing tests pass with affected tests updated for new signatures.

**Organization**: Tasks are grouped by user story. Since all changes touch only 2 source files and 2 test files, stories are ordered by implementation dependency to avoid file conflicts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Foundational — Remove Redundant Tool (US4, Priority: P2)

**Goal**: Delete `get_current_value` from tools and agents, simplifying both files before batch/knowledge changes.

**Independent Test**: Confirm no agent has access to `get_current_value`, user prompt still contains all setup parameter values, all remaining tests pass.

- [x] T001 [US4] Delete `get_current_value` function (lines 47-64) from `backend/ac_engineer/engineer/tools.py`
- [x] T002 [US4] Remove `get_current_value` from imports and tool registration in `backend/ac_engineer/engineer/agents.py` — delete from `from .tools import (...)` block (line 37) and remove `agent.tool(get_current_value)` (line 217) in `_build_specialist_agent`
- [x] T003 [US4] Update `backend/tests/engineer/test_tools.py` — delete `TestGetCurrentValue` class (2 tests: `test_returns_current_value`, `test_returns_not_found_for_unknown`)
- [x] T004 [US4] Update `backend/tests/engineer/test_agents.py` — remove any assertions that reference `get_current_value` in tool registration tests; verify `_build_specialist_agent` registers exactly 4 tools instead of 5

**Checkpoint**: `get_current_value` fully removed. Run `pytest backend/tests/engineer/ -v` — all tests pass with updated expectations.

---

## Phase 2: Batch Tool Calls (US2, Priority: P1)

**Goal**: Replace three single-item tools with batch versions accepting lists. Each returns a multi-block formatted string with one block per item, separated by blank lines.

**Independent Test**: Call each batch tool with multiple items and verify the response contains all items' data with identical formatting to the old single-item output.

- [x] T005 [P] [US2] Rewrite `get_setup_range` in `backend/ac_engineer/engineer/tools.py` — change parameter from `section: str` to `sections: list[str]`, iterate sections, build one formatted block per section (same fields: Section/Min/Max/Step/Default), join with `\n\n`, return empty string for empty list, include "not found" line for missing sections (per D2)
- [x] T006 [P] [US2] Rewrite `get_lap_detail` in `backend/ac_engineer/engineer/tools.py` — change parameter from `lap_number: int` to `lap_numbers: list[int]`, iterate lap numbers, build one formatted block per lap (same fields: time, best marker, gap, temps, understeer ratio, lat G, speed), join with `\n\n`, return empty string for empty list (per D3)
- [x] T007 [P] [US2] Rewrite `get_corner_metrics` in `backend/ac_engineer/engineer/tools.py` — change parameter from `corner_number: int` to `corner_numbers: list[int]`, keep `lap_number: int | None = None` as shared filter, iterate corner numbers, build one formatted block per corner (same fields: issue type, severity, understeer ratio, apex speed loss, lat G), join with `\n\n`, return empty string for empty list (per D4)
- [x] T008 [US2] Update `backend/tests/engineer/test_tools.py` — rewrite `TestGetSetupRange` tests to pass `sections=[...]` lists: single-item list returns same data, multi-item list returns all blocks, unknown section in batch returns "not found" without failing valid items, empty list returns empty string
- [x] T009 [US2] Update `backend/tests/engineer/test_tools.py` — rewrite `TestGetLapDetail` tests to pass `lap_numbers=[...]` lists: single-item returns same data, multi-item returns all laps, unknown lap in batch returns "not found", empty list returns empty string
- [x] T010 [US2] Update `backend/tests/engineer/test_tools.py` — rewrite `TestGetCornerMetrics` tests to pass `corner_numbers=[...]` lists: single-item returns same data, multi-item returns all corners, unknown corner in batch returns "not found", empty list returns empty string

**Checkpoint**: All three batch tools work with list parameters. Run `pytest backend/tests/engineer/test_tools.py -v` — all tests pass.

---

## Phase 3: Fallback Search Tool Reduction (US6, Priority: P3)

**Goal**: Reduce `search_kb` max results from 5 to 2 and update its docstring to reflect that primary knowledge is pre-loaded.

**Independent Test**: Call `search_kb` and confirm it returns at most 2 fragments with updated description.

- [x] T011 [US6] Update `search_kb` in `backend/ac_engineer/engineer/tools.py` — change `fragments[:5]` to `fragments[:2]`, update docstring to: "Search the vehicle dynamics knowledge base for supplementary information. Primary knowledge is already pre-loaded in your context. Use this only if you need additional details not covered above. Returns up to 2 fragments with source attribution."
- [x] T012 [US6] Update `backend/tests/engineer/test_tools.py` — in `TestSearchKbFormatting`, update any assertions that depend on the result count limit (verify max 2 fragments returned, not 5)

**Checkpoint**: `search_kb` returns max 2 results with updated docstring. Run `pytest backend/tests/engineer/test_tools.py -v` — all tests pass.

---

## Phase 4: Knowledge Pre-loading (US3, Priority: P1)

**Goal**: Select domain-relevant knowledge fragments deterministically and inject them into each agent's user prompt before reasoning begins. Cap at 8 fragments per agent.

**Independent Test**: Build a user prompt for a domain with known signals and verify the prompt contains the expected knowledge fragments in deterministic order.

- [x] T013 [US3] Add `_select_knowledge_fragments` private helper function in `backend/ac_engineer/engineer/agents.py` — accepts `signals: list[str]`, uses `SIGNAL_MAP` from `ac_engineer.knowledge.index` and `get_docs_cache()` from `ac_engineer.knowledge.loader` to look up (doc, section) pairs for each signal, deduplicate by (doc, section) in insertion order, build `KnowledgeFragment` objects, return first 8. Add required imports: `from ac_engineer.knowledge.index import SIGNAL_MAP` and `from ac_engineer.knowledge.loader import get_docs_cache`
- [x] T014 [US3] Modify `_build_user_prompt` in `backend/ac_engineer/engineer/agents.py` — add `knowledge_fragments: list` parameter (default `[]`), insert a "### Vehicle Dynamics Knowledge" section after "### Detected Signals" and before "### Corner Issues". Format each fragment as `**[source_file > section_title]**\ncontent`. If list is empty, include note: "No pre-loaded knowledge for these signals. Use the search_kb tool if you need vehicle dynamics information." (per D6)
- [x] T015 [US3] Update `analyze_with_engineer` in `backend/ac_engineer/engineer/agents.py` — replace the `search_knowledge(signal)` loop (lines 473-480) with per-domain fragment selection: inside the domain loop, call `domain_fragments = _select_knowledge_fragments(domain_signals)` and pass `domain_fragments` to `_build_user_prompt`. Remove the now-unused `all_knowledge` list and `search_knowledge` import (`from ac_engineer.knowledge import ... search_knowledge`). Remove unused `from ac_engineer.knowledge.models import KnowledgeFragment` from the TYPE_CHECKING block if it's also imported at runtime now. Clean up the `from ac_engineer.knowledge import get_knowledge_for_signals, search_knowledge` import at line 473 (move deterministic imports to top-level per D9)
- [x] T016 [US3] Update `backend/tests/engineer/test_agents.py` — add tests for `_select_knowledge_fragments`: returns empty list for unknown signals, returns deterministic fragments for known signals (same input → same output), caps at 8 fragments, handles empty signal list. Add test that `_build_user_prompt` includes "### Vehicle Dynamics Knowledge" section when fragments are provided, and includes fallback note when fragments list is empty

**Checkpoint**: Knowledge fragments injected into user prompt deterministically. Run `pytest backend/tests/engineer/ -v` — all tests pass.

---

## Phase 5: Agent Execution Turn Limit (US5, Priority: P2)

**Goal**: Enforce `max_turns=5` on every specialist agent execution with per-agent error isolation.

**Independent Test**: Simulate an agent exceeding the turn limit and verify it is caught gracefully, logged as a warning, and other agents continue.

- [x] T017 [US5] Update `agent.run()` call in `analyze_with_engineer` in `backend/ac_engineer/engineer/agents.py` — add `max_turns=5` parameter, add `from pydantic_ai.exceptions import UnexpectedModelBehavior` import at top of file, restructure the existing try/except to catch `UnexpectedModelBehavior` first with `logger.warning("Agent '%s' exceeded turn limit (max_turns=5)", domain)` then `continue`, followed by existing generic `Exception` catch with `logger.exception` then `continue` (per D8)
- [x] T018 [US5] Update `backend/tests/engineer/test_agents.py` — add test that `analyze_with_engineer` passes `max_turns=5` to `agent.run()` (verify via FunctionModel or mock). Add test that when one agent raises `UnexpectedModelBehavior`, the remaining agents still execute and their results are included in the final response. Add test that when all agents hit the turn limit, the "all specialists failed" fallback response is returned

**Checkpoint**: Turn limit enforced with per-agent isolation. Run `pytest backend/tests/engineer/ -v` — all tests pass.

---

## Phase 6: Polish & Integration Verification (US1)

**Goal**: Verify all optimizations work together, all tests pass across the full backend suite, and no regressions exist.

- [x] T019 Run full backend test suite `pytest backend/tests/ -v` and verify all tests pass (parser 143, analyzer 141, knowledge 48, config 34, storage 28, engineer core 68, engineer agents updated, API 209, acd_reader 20, resolver 81, watcher+jobs 47)
- [x] T020 Verify import cleanliness in `backend/ac_engineer/engineer/agents.py` — confirm: no `get_current_value` import, no `search_knowledge as kb_search` import, `UnexpectedModelBehavior` imported, `SIGNAL_MAP` and `get_docs_cache` imported, no unused imports remain

**Checkpoint**: All backend tests pass. Token optimization complete and invisible to users.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US4 — Remove Tool)**: No dependencies — start here to simplify files before other changes
- **Phase 2 (US2 — Batch Tools)**: Depends on Phase 1 (tools.py must have get_current_value removed first to avoid merge conflicts)
- **Phase 3 (US6 — Search KB)**: Depends on Phase 1 (tools.py cleanup), can run in parallel with Phase 2
- **Phase 4 (US3 — Knowledge Pre-loading)**: Depends on Phase 1 (agents.py import cleanup); independent of Phase 2/3 (different functions in agents.py)
- **Phase 5 (US5 — Turn Limit)**: Depends on Phase 4 (agents.py `analyze_with_engineer` is modified in Phase 4, turn limit is added to the same function)
- **Phase 6 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US4 (P2)**: Foundational — no story dependencies, simplifies both files
- **US2 (P1)**: Independent of other stories (tools.py only, different functions than US3/US5)
- **US6 (P3)**: Independent of other stories (tools.py only, `search_kb` function)
- **US3 (P1)**: Independent of US2/US6 (agents.py only)
- **US5 (P2)**: Depends on US3 (modifies same function in agents.py)
- **US1 (P1)**: Integration outcome — verified when all other stories complete

### Within Each User Story

- Source code changes before test updates
- Test updates verify the source changes
- Run story-specific tests at each checkpoint

### Parallel Opportunities

- **Phase 2 tasks T005, T006, T007**: All three batch tool rewrites can run in parallel (different functions in same file)
- **Phase 2 + Phase 3**: US6 (search_kb) can run in parallel with US2 (batch tools) — different functions in tools.py
- **Phase 2 + Phase 4**: US2 (tools.py) and US3 (agents.py) can run in parallel — different files entirely

---

## Parallel Example: Phase 2 (Batch Tools)

```bash
# Launch all three batch tool rewrites in parallel (different functions, same file):
Task T005: "Rewrite get_setup_range to accept sections: list[str] in tools.py"
Task T006: "Rewrite get_lap_detail to accept lap_numbers: list[int] in tools.py"
Task T007: "Rewrite get_corner_metrics to accept corner_numbers: list[int] in tools.py"
```

## Parallel Example: Cross-Phase

```bash
# After Phase 1 completes, launch tools.py and agents.py changes in parallel:
# Stream 1 (tools.py): T005-T012 (US2 + US6)
# Stream 2 (agents.py): T013-T016 (US3)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Remove `get_current_value` (US4)
2. Complete Phase 2: Batch tools (US2)
3. **STOP and VALIDATE**: Run `pytest backend/tests/engineer/ -v`
4. At this point, the highest-impact optimization (batch tools) is live

### Incremental Delivery

1. Phase 1 (US4) → Remove redundant tool → validate
2. Phase 2 (US2) → Batch tools → validate (biggest token savings)
3. Phase 3 (US6) → Reduce search_kb → validate
4. Phase 4 (US3) → Knowledge pre-loading → validate (second biggest savings)
5. Phase 5 (US5) → Turn limit safety net → validate
6. Phase 6 → Full suite validation → done

---

## Notes

- All 4 files already exist — no file creation needed
- [P] tasks = different functions in same file or different files, no conflicts
- FR-017: every checkpoint MUST include running the test suite
- Batch tools return `str` (not dict) — formatted multi-block strings matching existing single-item format
- `_select_knowledge_fragments` uses `SIGNAL_MAP` + `get_docs_cache` for deterministic results
- `max_turns=5` raises `UnexpectedModelBehavior` which is caught per-agent
