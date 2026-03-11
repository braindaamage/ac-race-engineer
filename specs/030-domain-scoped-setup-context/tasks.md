# Tasks: Domain-Scoped Setup Context

**Input**: Design documents from `specs/030-domain-scoped-setup-context/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — spec requires new tests (SC-004) and zero regressions (SC-003).

**Organization**: Tasks grouped by user story. All changes in two files: `backend/ac_engineer/engineer/agents.py` and `backend/tests/engineer/test_agents.py`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Foundational

**Purpose**: Add the DOMAIN_PARAMS constant and export it. This blocks all user story work.

- [x] T001 Add `DOMAIN_PARAMS` constant after `DOMAIN_TOOLS` in `backend/ac_engineer/engineer/agents.py` — map each domain to a tuple of section name prefixes per data-model.md: balance → `("SPRING_RATE", "DAMP_BUMP", "DAMP_FAST_BUMP", "DAMP_REBOUND", "DAMP_FAST_REBOUND", "ARB_", "RIDE_HEIGHT", "BRAKE_POWER", "BRAKE_BIAS")`, tyre → `("PRESSURE_", "CAMBER_", "TOE_OUT_", "TOE_IN_")`, aero → `("WING_", "SPLITTER_")`, technique → `()`, principal → `()`

**Checkpoint**: `DOMAIN_PARAMS` importable from `agents.py`. No behavior change yet.

---

## Phase 2: User Story 1 — Reduced Token Cost Per Analysis (Priority: P1) 🎯 MVP

**Goal**: Each specialist agent receives only its domain-relevant setup parameters in the prompt. Technique and principal agents receive no setup parameters.

**Independent Test**: Call `_build_user_prompt()` with each domain and verify the prompt contains only the expected section prefixes.

### Implementation for User Story 1

- [x] T002 [US1] Add `domain: str | None = None` parameter to `_build_user_prompt()` in `backend/ac_engineer/engineer/agents.py` — when `domain` is `None`, include all parameters (backward compatible); when `domain` has empty prefixes in `DOMAIN_PARAMS`, skip the "Current Setup Parameters" block entirely and emit the existing "WARNING: No setup parameters available" message; when `domain` has prefixes, filter `summary.active_setup_parameters` to include only sections where the section name starts with one of the domain's prefixes (use `str.startswith()`), plus for `"balance"` domain include any section not matching ANY domain's prefixes (FR-009 fallback). Never mutate `summary.active_setup_parameters` — build a local filtered dict.

- [x] T003 [US1] Pass `domain=domain` from `analyze_with_engineer()` to `_build_user_prompt()` in `backend/ac_engineer/engineer/agents.py` — in the specialist loop (line ~574), change `_build_user_prompt(summary, domain_signals, domain_fragments)` to `_build_user_prompt(summary, domain_signals, domain_fragments, domain=domain)`

### Tests for User Story 1

- [x] T004 [US1] Add `TestDomainScopedParams` class to `backend/tests/engineer/test_agents.py` with the following tests. Import `DOMAIN_PARAMS` from `agents.py`. Use a `SessionSummary` fixture with sections spanning all domains (e.g., `SPRING_RATE_LF`, `DAMP_BUMP_LF`, `ARB_FRONT`, `PRESSURE_LF`, `CAMBER_LF`, `TOE_OUT_LF`, `WING_1`, `WING_2`, `RIDE_HEIGHT_0`, `BRAKE_BIAS`). Tests:
  - `test_balance_domain_gets_only_balance_sections`: call `_build_user_prompt(summary, signals, domain="balance")`, assert prompt contains `SPRING_RATE_LF`, `DAMP_BUMP_LF`, `ARB_FRONT`, `RIDE_HEIGHT_0`, `BRAKE_BIAS` and does NOT contain `PRESSURE_LF`, `CAMBER_LF`, `TOE_OUT_LF`, `WING_1`, `WING_2`
  - `test_tyre_domain_gets_only_tyre_sections`: call with `domain="tyre"`, assert prompt contains `PRESSURE_LF`, `CAMBER_LF`, `TOE_OUT_LF` and does NOT contain `SPRING_RATE_LF`, `ARB_FRONT`, `WING_1`
  - `test_aero_domain_gets_only_aero_sections`: call with `domain="aero"`, assert prompt contains `WING_1`, `WING_2` and does NOT contain `SPRING_RATE_LF`, `PRESSURE_LF`, `ARB_FRONT`
  - `test_technique_domain_gets_no_setup_params`: call with `domain="technique"`, assert prompt does NOT contain `### Current Setup Parameters` and DOES contain `No setup parameters available`
  - `test_principal_domain_gets_no_setup_params`: call with `domain="principal"`, assert prompt does NOT contain `### Current Setup Parameters` and DOES contain `No setup parameters available`
  - `test_domain_none_includes_all_params`: call with `domain=None` (or omit), assert prompt contains ALL sections from the fixture (backward compatibility)

**Checkpoint**: `_build_user_prompt()` filters correctly per domain. All existing tests still pass since they don't pass `domain`.

---

## Phase 3: User Story 2 — Fallback Access via Tools (Priority: P2)

**Goal**: Verify that `get_setup_range` tool still returns data for any parameter regardless of domain filtering.

**Independent Test**: Confirm that AgentDeps.parameter_ranges is not filtered — only the prompt text is filtered.

### Tests for User Story 2

- [x] T005 [US2] Add test `test_tool_fallback_access_unaffected` to `TestDomainScopedParams` in `backend/tests/engineer/test_agents.py` — create an `AgentDeps` with parameter_ranges containing both balance and tyre sections, build a prompt with `domain="tyre"` (so prompt excludes balance sections), then verify that `AgentDeps.parameter_ranges` still contains the balance section keys. This confirms the tool can still access any parameter via `get_setup_range` since it reads from `deps.parameter_ranges`, not from the prompt text.

**Checkpoint**: Tool fallback verified — `parameter_ranges` in deps is never filtered.

---

## Phase 4: User Story 3 — Mod Cars with Non-Standard Parameters (Priority: P2)

**Goal**: Unrecognized section names are included in the balance domain; recognized sections are correctly classified even with mod-style naming.

**Independent Test**: Build a SessionSummary with a mix of standard and unknown sections, filter for balance, and verify unknowns are included.

### Tests for User Story 3

- [x] T006 [US3] Add tests to `TestDomainScopedParams` in `backend/tests/engineer/test_agents.py`:
  - `test_unrecognized_section_falls_back_to_balance`: create a `SessionSummary` with an unknown section (e.g., `CUSTOM_MOD_PARAM`) alongside standard sections, call `_build_user_prompt(summary, signals, domain="balance")`, assert `CUSTOM_MOD_PARAM` appears in the prompt
  - `test_unrecognized_section_excluded_from_other_domains`: same summary, call with `domain="tyre"`, assert `CUSTOM_MOD_PARAM` does NOT appear in the prompt
  - `test_empty_setup_params_preserves_existing_behavior`: create a `SessionSummary` with `active_setup_parameters={}`, call with `domain="balance"`, assert prompt contains `No setup parameters available`
  - `test_summary_not_mutated_after_filtering`: create a `SessionSummary` with multiple sections, store a copy of `active_setup_parameters`, call `_build_user_prompt` with `domain="tyre"`, assert `summary.active_setup_parameters` still equals the original copy

**Checkpoint**: Mod car edge cases verified — unrecognized sections go to balance, no data mutation.

---

## Phase 5: Polish & Regression

**Purpose**: Verify zero regressions across the full engineer test suite.

- [x] T007 Run full engineer test suite: `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v` — all existing tests must pass without modification (SC-003). Verify the 3 existing `TestBuildUserPromptKnowledge` tests still pass (they call `_build_user_prompt` without `domain`, so backward compat).

- [x] T008 Run full backend test suite: `conda run -n ac-race-engineer pytest backend/tests/ -v` — verify zero regressions across all 962 backend tests.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on T001 (needs `DOMAIN_PARAMS`)
- **Phase 3 (US2)**: Depends on T002 (needs `domain` parameter working)
- **Phase 4 (US3)**: Depends on T002 (needs `domain` parameter working)
- **Phase 5 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Depends only on T001 — can start immediately after foundational
- **US2 (P2)**: Depends on US1 implementation (T002-T003) — verifies tool access is not broken
- **US3 (P2)**: Depends on US1 implementation (T002-T003) — verifies edge case handling

### Within User Story 1

- T002 (filtering logic) and T003 (caller update) are sequential — T003 depends on T002
- T004 (tests) depends on T002 and T003

### Parallel Opportunities

- T005 (US2 tests) and T006 (US3 tests) can run in parallel after T004 completes
- T007 and T008 are sequential (T008 is a superset but confirms broader scope)

---

## Parallel Example: After Phase 2

```bash
# After T004 completes, launch US2 and US3 tests in parallel:
Task: T005 "test_tool_fallback_access_unaffected in backend/tests/engineer/test_agents.py"
Task: T006 "Mod car edge case tests in backend/tests/engineer/test_agents.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001: Add `DOMAIN_PARAMS` constant
2. Complete T002: Add filtering logic to `_build_user_prompt()`
3. Complete T003: Wire `domain` parameter in `analyze_with_engineer()`
4. Complete T004: Verify with domain-specific tests
5. **STOP and VALIDATE**: Run `pytest backend/tests/engineer/test_agents.py -v`

### Full Delivery

1. T001 → T002 → T003 → T004 (MVP complete)
2. T005 + T006 in parallel (edge cases verified)
3. T007 → T008 (full regression check)

---

## Notes

- All implementation is in a single file (`agents.py`), so no [P] markers on implementation tasks
- Tests are all in a single file (`test_agents.py`), so US2/US3 tests can logically run in parallel but write to the same file
- The `domain=None` default ensures zero impact on existing callers (chat agent in `api/engineer/pipeline.py`, existing tests)
- `DOMAIN_PARAMS` must be exported in the import block of `test_agents.py` alongside existing `DOMAIN_TOOLS`
