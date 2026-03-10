# Tasks: Skill Prompt Optimization

**Input**: Design documents from `/specs/027-skill-prompt-optimization/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: No new tests required. Existing 167 engineer tests must continue to pass unchanged (no Python code is modified).

**Organization**: Tasks are grouped by user story. Since all changes are to separate files, most tasks are parallelizable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: User Story 1 - Concise Setup Recommendations (Priority: P1) — MVP

**Goal**: Rewrite balance.md, tyre.md, and aero.md with explicit output limits (max 3 SetupChanges, 1-2 sentence reasoning with mandatory data citation, 1 sentence expected_effect), priority tiers for signal confirmation, corrected tool usage, and domain boundary enforcement.

**Independent Test**: Run an analysis on any session and verify each specialist outputs at most 3 setup changes, each with a one-sentence data-cited reasoning and one-sentence expected_effect. No domain exceeds 3 changes.

**Implements**: FR-001, FR-002, FR-003, FR-006, FR-007, FR-011, US4 (priority tiers embedded)

### Implementation for User Story 1

- [x] T001 [P] [US1] Rewrite Output Requirements section in `backend/ac_engineer/engineer/skills/balance.md`: max 3 SetupChanges; reasoning is 1-2 sentences with mandatory data citation (corner number + metric name + value); expected_effect is 1 sentence describing driver-felt outcome; domain_summary is 1-2 sentences. Add Priority Tiers section: Propose (signal in majority of flying laps, or both if 2-3 laps), Mention with low confidence (signal in 1 lap or partial data), Omit (marginal, absent, or out-of-domain). Rewrite Tool Usage: remove `get_current_value` (current values are in prompt under `### Current Setup Parameters`), move `search_kb` to end with note that knowledge is pre-loaded in context. Add explicit domain boundary: omit findings outside balance domain.
- [x] T002 [P] [US1] Rewrite Output Requirements section in `backend/ac_engineer/engineer/skills/tyre.md`: same structure as T001 — max 3 SetupChanges, 1-2 sentence reasoning with data citation, 1 sentence expected_effect, 1-2 sentence domain_summary, Priority Tiers section, corrected Tool Usage (remove `get_current_value`, move `search_kb` to end), domain boundary enforcement (tyre domain only).
- [x] T003 [P] [US1] Rewrite Output Requirements section in `backend/ac_engineer/engineer/skills/aero.md`: same structure as T001 — max 3 SetupChanges, 1-2 sentence reasoning with data citation, 1 sentence expected_effect, 1-2 sentence domain_summary, Priority Tiers section, corrected Tool Usage (remove `get_current_value`, move `search_kb` to end), domain boundary enforcement (aero domain only). Preserve existing "small changes only — 1-2 clicks at a time" constraint.

**Checkpoint**: Balance, tyre, and aero specialists produce concise, data-cited output. All three files can be edited in parallel since they are independent.

---

## Phase 2: User Story 2 - Focused Driving Technique Feedback (Priority: P2)

**Goal**: Rewrite technique.md with explicit output limits (max 3 DriverFeedback entries, 1 sentence observation with data citation, 1-2 sentence suggestion) and priority tiers.

**Independent Test**: Run an analysis on a session with technique signals and verify each feedback entry has a one-sentence data-cited observation and one-to-two sentence suggestion. No more than 3 entries.

**Implements**: FR-004, FR-005, FR-010, US4 (priority tiers embedded)

### Implementation for User Story 2

- [x] T004 [P] [US2] Rewrite Output Requirements section in `backend/ac_engineer/engineer/skills/technique.md`: max 3 DriverFeedback entries; observation is 1 sentence citing specific data (metric + value + corners); suggestion is 1-2 sentences of actionable advice; corners_affected is a list of corner numbers; severity is high/medium/low; domain_summary is 1-2 sentences. Add Priority Tiers section (same three tiers as specialists). Reinforce: NO SetupChanges, only DriverFeedback. Omit marginal observations — if no significant technique issue, produce no feedback.

**Checkpoint**: Technique specialist produces concise, structured feedback. Can be done in parallel with Phase 1 tasks.

---

## Phase 3: User Story 3 - Lean Orchestrator Synthesis (Priority: P2)

**Goal**: Rewrite principal.md with output constraints preventing physics re-explanation, explicit prohibition on proposing setup changes, and available tools for contextual verification.

**Independent Test**: Run a full analysis and verify the combined summary is 2-3 sentences describing car state, changes are listed by impact without re-explaining physics, and no vehicle dynamics theory is duplicated from specialist reasoning.

**Implements**: FR-008, FR-009

### Implementation for User Story 3

- [x] T005 [P] [US3] Rewrite `backend/ac_engineer/engineer/skills/principal.md`: Add Output Requirements section — overall summary is 2-3 sentences max describing the car's current state; list changes by impact order without re-explaining the physics behind them (that reasoning is already in each change's reasoning field); confidence justification is 1 sentence. Add Tool Usage section listing `get_lap_detail` and `get_corner_metrics` as available tools for contextual verification only. Make explicit: the orchestrator does NOT propose setup changes, does NOT repeat reasoning from specialist outputs, and does NOT re-explain vehicle dynamics theory.

**Checkpoint**: Orchestrator produces a lean synthesis. Can be done in parallel with Phases 1 and 2.

---

## Phase 4: Verification

**Purpose**: Validate all changes against spec requirements and success criteria

- [x] T006 Run existing engineer tests: `conda run -n ac-race-engineer pytest backend/tests/engineer/ -v` — all 167 tests must pass unchanged
- [x] T007 Review all 5 modified skill files for consistency: verify all share the same Priority Tiers wording, all specialist files have matching Output Requirements structure, all tool usage sections are corrected

**Checkpoint**: All tests pass, all files are consistent, ready for real-session validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: No dependencies — can start immediately
- **Phase 2 (US2)**: No dependencies — can start immediately, in parallel with Phase 1
- **Phase 3 (US3)**: No dependencies — can start immediately, in parallel with Phases 1 and 2
- **Phase 4 (Verification)**: Depends on Phases 1, 2, and 3 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent — balance.md, tyre.md, aero.md
- **User Story 2 (P2)**: Independent — technique.md
- **User Story 3 (P2)**: Independent — principal.md
- **User Story 4 (P3)**: Embedded in US1-US3 via Priority Tiers section (no separate tasks)

### Parallel Opportunities

All implementation tasks (T001-T005) operate on different files and can run in parallel:

```text
T001 (balance.md) ─┐
T002 (tyre.md)   ──┤
T003 (aero.md)   ──┼── All parallel ──→ T006 (test) → T007 (review)
T004 (technique.md)┤
T005 (principal.md)┘
```

---

## Parallel Example: All User Stories

```bash
# All 5 file edits can launch simultaneously:
Task: "T001 - Rewrite balance.md"
Task: "T002 - Rewrite tyre.md"
Task: "T003 - Rewrite aero.md"
Task: "T004 - Rewrite technique.md"
Task: "T005 - Rewrite principal.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001, T002, T003 (balance, tyre, aero specialists)
2. Run T006 (tests pass)
3. **STOP and VALIDATE**: Run a real analysis — output should already be significantly shorter

### Full Delivery

1. Complete T001-T005 in parallel (all 5 files)
2. Run T006 (tests pass)
3. Run T007 (consistency review)
4. Validate against SC-001: output tokens under 7,000 on test session with Gemini 2.5 Flash

---

## Notes

- All tasks edit markdown files only — no Python, API, frontend, or test code changes
- Priority Tiers (US4) is embedded in each specialist's edit rather than being a separate phase
- Files must remain human-readable markdown (end users may customize agent behavior)
- The 3-change limit and format constraints are soft (prompt-based), not hard (code validators)
