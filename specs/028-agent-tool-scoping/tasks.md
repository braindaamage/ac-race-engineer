# Tasks: Agent Tool Scoping

**Input**: Design documents from `/specs/028-agent-tool-scoping/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Included — the existing test must be updated to reflect per-domain tool sets (SC-004).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/ac_engineer/engineer/` for source, `backend/tests/engineer/` for tests

---

## Phase 1: User Story 1 — Domain-Restricted Tool Access (Priority: P1) 🎯 MVP

**Goal**: Each specialist agent receives only the tools documented in its skill prompt. The technique agent can no longer call `get_setup_range`.

**Independent Test**: Build each specialist agent and verify its registered tool set matches the skill prompt exactly.

### Implementation for User Story 1

- [x] T001 [US1] Add `DOMAIN_TOOLS` constant mapping each domain to its tool functions in `backend/ac_engineer/engineer/agents.py` — place after `AERO_SECTIONS`, mapping: balance→[get_setup_range, get_corner_metrics, search_kb], tyre→[get_setup_range, get_lap_detail, search_kb], aero→[get_setup_range, get_corner_metrics, search_kb], technique→[get_lap_detail, get_corner_metrics, search_kb], principal→[get_lap_detail, get_corner_metrics]
- [x] T002 [US1] Update `_build_specialist_agent()` in `backend/ac_engineer/engineer/agents.py` to register tools from `DOMAIN_TOOLS[domain]` instead of hardcoding all 4 tools
- [x] T003 [US1] Update `test_agent_registers_4_tools` in `backend/tests/engineer/test_agents.py` — replace the single all-4-tools assertion with per-domain assertions: build each domain's agent and verify its tool set matches `DOMAIN_TOOLS`

**Checkpoint**: All 4 specialist agents have domain-scoped tools. Run `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v` — all tests pass.

---

## Phase 2: User Story 2 — Auditable Tool-to-Agent Mapping (Priority: P2)

**Goal**: `DOMAIN_TOOLS` is publicly exported so developers can import and inspect the mapping without reading internal code.

**Independent Test**: `from ac_engineer.engineer import DOMAIN_TOOLS` succeeds and returns the expected dictionary.

### Implementation for User Story 2

- [x] T004 [US2] Export `DOMAIN_TOOLS` in `backend/ac_engineer/engineer/__init__.py` — add to imports from `.agents` and to `__all__` list under the Constants section

**Checkpoint**: `DOMAIN_TOOLS` is importable. Run `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v` — all tests still pass.

---

## Phase 3: User Story 3 — Principal Agent Tool Access (Priority: P3)

**Goal**: The principal domain entry in `DOMAIN_TOOLS` is defined for forward-compatibility. No code currently builds a principal agent, so this is documentation/readiness only.

**Independent Test**: `DOMAIN_TOOLS["principal"]` returns `[get_lap_detail, get_corner_metrics]`.

*Note: The principal entry was already added in T001. This phase confirms it exists and is correct — no additional implementation tasks needed.*

**Checkpoint**: Verify `DOMAIN_TOOLS["principal"]` contains exactly `get_lap_detail` and `get_corner_metrics`.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [x] T005 Run full backend test suite: `conda run -n ac-race-engineer pytest backend/tests/ -v` — all 900+ tests pass with no regressions
- [x] T006 Run quickstart.md validation steps to confirm verification instructions are accurate

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US2)**: Depends on T001 (DOMAIN_TOOLS must exist before exporting)
- **Phase 3 (US3)**: Depends on T001 (principal entry must exist)
- **Phase 4 (Polish)**: Depends on all previous phases

### Within Phase 1

- T001 → T002 (constant must exist before factory uses it)
- T002 → T003 (implementation before test update, since old test would fail after T002)

### Parallel Opportunities

- T001 and T004 cannot be parallelized (T004 exports what T001 creates)
- T003 can be written concurrently with T002 if tool names are known (they are, from data-model.md)
- T005 and T006 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: T001 → T002 → T003
2. **STOP and VALIDATE**: Run engineer tests — all pass, technique agent has no `get_setup_range`
3. This is a fully functional MVP — the core problem is solved

### Incremental Delivery

1. Phase 1 (US1): Tool scoping works → MVP
2. Phase 2 (US2): Mapping is publicly exported → auditable
3. Phase 3 (US3): Principal entry confirmed → forward-compatible
4. Phase 4: Full regression test → ship-ready

---

## Notes

- Total tasks: 6
- Tasks per user story: US1=3, US2=1, US3=0 (covered by T001), Polish=2
- This is a minimal, surgical change — the smallest possible diff that solves the problem
- All tasks modify existing files only — no new files created
