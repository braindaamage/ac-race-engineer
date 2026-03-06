# Tasks: Setup Compare View

**Input**: Design documents from `/specs/019-setup-compare-view/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — spec requires frontend tests for all components.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript types and data-fetching hooks shared by all user stories

- [ ] T001 Add stint and comparison TypeScript interfaces (StintMetrics, AggregatedStintMetrics, StintTrends, SetupParameterDelta, MetricDeltas, StintComparison, StintListResponse, StintComparisonResponse) to `frontend/src/lib/types.ts`
- [ ] T002 Create `useStints(sessionId)` and `useStintComparison(sessionId, stintA, stintB)` TanStack Query hooks in `frontend/src/hooks/useStints.ts` — both with `staleTime: Infinity`, comparison enabled only when both stints non-null
- [ ] T003 Create formatting utility functions in `frontend/src/views/compare/utils.ts` — `formatDelta(value, precision)` with sign prefix, `formatLapTime(seconds)`, `deltaDirection(value)` returning "increase"/"decrease"/"unchanged", `isImprovement(metricKey, delta)` returning boolean (negative lap_time = good, positive peak_lat_g = good)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: CSS file and test infrastructure that MUST be in place before component work

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `frontend/src/views/compare/CompareView.css` with layout styles: `ace-compare` (grid layout with sidebar + main), `ace-compare__sidebar`, `ace-compare__main`, stint selector item styles (`ace-stint-item`, `ace-stint-item--selected`), setup diff styles (`ace-diff-section`, `ace-diff-row`, `ace-diff-arrow`), metrics panel styles (`ace-metrics-panel`, `ace-metrics-delta`, `ace-metrics-delta--positive`, `ace-metrics-delta--negative`). All colors via design tokens, all numerics use `var(--font-mono)`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Compare Two Stints Side-by-Side (Priority: P1) MVP

**Goal**: Driver selects two stints from an analyzed session and sees setup parameter diff + performance metric deltas

**Independent Test**: Select two stints from a multi-stint session and verify that changed parameters and metric deltas render correctly

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Create test file `frontend/tests/views/compare/utils.test.ts` — test `formatDelta` (positive/negative/zero/null), `formatLapTime`, `deltaDirection`, `isImprovement` for each metric type
- [ ] T006 [P] [US1] Create test file `frontend/tests/views/compare/StintSelector.test.tsx` — test: renders all stints with 1-indexed labels and metadata (setup filename, lap count, avg time), highlights selected stints, clicking a stint calls onSelect, shows "no setup" when setup_filename is null
- [ ] T007 [P] [US1] Create test file `frontend/tests/views/compare/SetupDiff.test.tsx` — test: groups parameters by section, shows value_a → value_b with directional arrow for numerics, renders "No setup changes" when changes array is empty, handles mixed numeric/string values, shows "—" for missing values
- [ ] T008 [P] [US1] Create test file `frontend/tests/views/compare/MetricsPanel.test.tsx` — test: displays each metric delta with sign prefix, applies green color for improvements (negative lap_time_delta), applies red for degradations, shows "N/A" for null values, renders tyre/slip deltas per wheel position
- [ ] T009 [P] [US1] Create test file `frontend/tests/views/compare/CompareView.test.tsx` — test: renders stint list and comparison when session has 2+ stints, defaults selection to first two stints, fetches comparison when both stints selected, shows setup diff and metrics panel with comparison data

### Implementation for User Story 1

- [ ] T010 [P] [US1] Create `StintSelector` component in `frontend/src/views/compare/StintSelector.tsx` — props: `stints: StintMetrics[]`, `selectedStints: [number, number | null]`, `onSelect: (index: number) => void`. Render each stint as a selectable row showing stint number (1-indexed), setup filename (or "No setup"), flying lap count, average lap time (formatted). Highlight up to 2 selected stints with `ace-stint-item--selected` class
- [ ] T011 [P] [US1] Create `SetupDiff` component in `frontend/src/views/compare/SetupDiff.tsx` — props: `changes: SetupParameterDelta[]`, `stintAIndex: number`, `stintBIndex: number`. Group changes by `section` field, render each section as a collapsible group (default expanded). Each row: parameter name, value A, directional arrow (up/down unicode for numeric deltas, dash for string changes), value B. If changes is empty, show "No setup changes between these stints" message
- [ ] T012 [P] [US1] Create `MetricsPanel` component in `frontend/src/views/compare/MetricsPanel.tsx` — props: `deltas: MetricDeltas`, `stintAIndex: number`, `stintBIndex: number`. Display lap_time_delta_s, peak_lat_g_delta as primary metrics. Display tyre_temp_delta, slip_angle_delta, slip_ratio_delta as per-wheel grids. Format with sign prefix and color coding (green = improvement, red = degradation per `isImprovement`). Null values render as "N/A"
- [ ] T013 [US1] Replace placeholder in `frontend/src/views/compare/index.tsx` with full `CompareView` component — read `selectedSessionId` from `sessionStore`, fetch stints via `useStints`, manage stint selection with `useState<[number, number | null]>` defaulting to `[0, 1]` when 2+ stints load, fetch comparison via `useStintComparison` when both selected. Selection logic: clicking selected stint deselects it, clicking new stint when 2 selected replaces the oldest. Render: StintSelector sidebar + SetupDiff + MetricsPanel main area. Import CompareView.css

**Checkpoint**: User Story 1 fully functional — driver can compare any two stints and see setup diff + metric deltas

---

## Phase 4: User Story 2 — Single-Stint and Empty State Handling (Priority: P2)

**Goal**: Graceful handling of edge cases: no session, session not analyzed, single stint

**Independent Test**: Open Compare view with no session, with an unanalyzed session, and with a single-stint session — each shows appropriate message

### Tests for User Story 2

- [ ] T014 [US2] Add tests to `frontend/tests/views/compare/CompareView.test.tsx` — test: shows "select a session" EmptyState when no session is selected, shows "analysis required" EmptyState when session state is not "analyzed"/"engineered", shows "comparison needs two stints" EmptyState when session has only 1 stint, shows Skeleton loading state while stints are loading

### Implementation for User Story 2

- [ ] T015 [US2] Add empty state handling to `CompareView` in `frontend/src/views/compare/index.tsx` — add early returns (following AnalysisView pattern): (1) no selectedSessionId → EmptyState with "Go to Sessions" action, (2) session not analyzed → EmptyState explaining analysis required, (3) stints loading → Skeleton placeholders, (4) single stint → EmptyState explaining comparison requires 2+ stints. Use `useSessions()` to check session state, `useUIStore` for navigation

**Checkpoint**: All empty/edge states handled gracefully with informative messages

---

## Phase 5: User Story 3 — Toggle Unchanged Parameters (Priority: P3)

**Goal**: Toggle to show all setup parameters (changed + unchanged) alongside the diff

**Note**: Per research.md decision D6, this is descoped. The backend `GET /compare` endpoint only returns changed parameters — showing all parameters would require a full setup endpoint that doesn't exist. This phase documents the limitation and adds a "changes only" indicator to the UI.

### Implementation for User Story 3

- [ ] T016 [US3] Add a "Showing changed parameters only" informational label below the SetupDiff header in `frontend/src/views/compare/SetupDiff.tsx` — styled as subtle secondary text. This communicates to the user that they are seeing a focused diff, not the full setup

**Checkpoint**: User understands they're seeing changes only; full toggle deferred to future backend enhancement

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T017 Run `cd frontend && npx tsc --noEmit` to verify zero TypeScript errors
- [ ] T018 Run `cd frontend && npm run test` to verify all tests pass (existing + new)
- [ ] T019 Verify CSS uses only design token variables (no hardcoded colors), `ace-` prefix on all classes, `var(--font-mono)` on all numeric values

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (types must exist for CSS to reference patterns)
- **User Story 1 (Phase 3)**: Depends on Phase 1 + Phase 2 — BLOCKS on types, hooks, CSS, utils
- **User Story 2 (Phase 4)**: Depends on Phase 3 — adds empty states to the CompareView built in US1
- **User Story 3 (Phase 5)**: Depends on Phase 3 — adds label to SetupDiff built in US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (adds early returns to CompareView created in US1)
- **User Story 3 (P3)**: Depends on US1 (adds label to SetupDiff created in US1)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Components before integration (CompareView)
- Core implementation before edge case handling

### Parallel Opportunities

**Phase 1** (3 tasks):
- T001, T002, T003 are sequential: types → hooks → utils (hooks import types, utils import types)
- T001 first, then T002 and T003 in parallel

**Phase 3 — US1 Tests** (5 tasks):
- T005, T006, T007, T008, T009 — all [P], different test files, can run in parallel

**Phase 3 — US1 Implementation** (4 tasks):
- T010, T011, T012 — all [P], different component files, can run in parallel
- T013 — depends on T010, T011, T012 (CompareView integrates all components)

---

## Parallel Example: User Story 1

```text
# Batch 1 — All test files in parallel:
T005: utils.test.ts
T006: StintSelector.test.tsx
T007: SetupDiff.test.tsx
T008: MetricsPanel.test.tsx
T009: CompareView.test.tsx

# Batch 2 — All leaf components in parallel:
T010: StintSelector.tsx
T011: SetupDiff.tsx
T012: MetricsPanel.tsx

# Batch 3 — Integration (sequential):
T013: CompareView index.tsx (imports T010, T011, T012)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (types + hooks + utils)
2. Complete Phase 2: Foundational (CSS)
3. Complete Phase 3: User Story 1 (tests → components → integration)
4. **STOP and VALIDATE**: Test that selecting two stints shows diff + metrics
5. Deploy/demo if ready — core comparison works

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 → Full comparison works (MVP!)
3. User Story 2 → Empty states handled gracefully
4. User Story 3 → Informational label added (descoped toggle)
5. Polish → TypeScript check, all tests green, CSS audit

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US3 (toggle unchanged params) is descoped per research.md D6 — backend only returns changed params
- No backend changes needed — all endpoints exist from Phase 6
- Total: 19 tasks (3 setup + 1 foundational + 10 US1 + 2 US2 + 1 US3 + 3 polish)
