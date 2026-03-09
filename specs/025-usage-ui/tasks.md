# Tasks: Usage UI

**Input**: Design documents from `/specs/025-usage-ui/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — the project has established testing conventions (Vitest + Testing Library) and the spec references testable acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend source**: `frontend/src/`
- **Frontend tests**: `frontend/tests/` (mirrors `frontend/src/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Type definitions and shared utilities that both user stories depend on

- [ ] T001 Add usage type definitions (ToolCallInfo, AgentUsageDetail, UsageTotals, RecommendationUsageResponse) to `frontend/src/lib/types.ts`
- [ ] T002 [P] Create `formatTokenCount` utility function in `frontend/src/lib/format.ts` — three-tier compact notation: raw (<1000), K suffix (1000–999999), M suffix (1000000+), one decimal for K/M, trailing zeros preserved
- [ ] T003 [P] Write unit tests for `formatTokenCount` in `frontend/tests/lib/format.test.ts` — cover boundaries (0, 999, 1000, 999999, 1000000), rounding (1450→"1.5K", 1440→"1.4K"), trailing zeros (1000→"1.0K"), large values (12500000→"12.5M")
- [ ] T004 Add `useRecommendationUsage(sessionId, recommendationId)` hook to `frontend/src/hooks/useRecommendations.ts` — follows `useRecommendationDetail` pattern, uses `staleTime: Infinity`, query key `["recommendation-usage", sessionId, recommendationId]`, returns `RecommendationUsageResponse`
- [ ] T005 Write unit tests for `useRecommendationUsage` hook in `frontend/tests/hooks/useRecommendationUsage.test.ts` — mock `apiGet`, verify query key, verify `staleTime: Infinity`, verify `enabled` flag when sessionId/recommendationId are null

**Checkpoint**: Types, formatting utility, and data hook are ready. Both user stories can now proceed.

---

## Phase 2: User Story 1 - Glance at Usage Summary (Priority: P1) 🎯 MVP

**Goal**: Display an inline summary bar at the bottom of each recommendation card showing agent count, input tokens, output tokens, tool calls, and a details button. Hidden when no usage data exists.

**Independent Test**: Render a RecommendationCard with usage data and verify the summary bar appears with correct formatted numbers. Render without usage data and verify no summary bar.

### Tests for User Story 1

- [ ] T006 [P] [US1] Write component tests for UsageSummaryBar in `frontend/tests/views/engineer/UsageSummaryBar.test.tsx` — renders all totals fields with formatted values, uses monospace font class, renders details button, does not render when usage is undefined/null, handles zero-value totals, verifies compact formatting in rendered output

### Implementation for User Story 1

- [ ] T007 [P] [US1] Create UsageSummaryBar component in `frontend/src/views/engineer/UsageSummaryBar.tsx` — accepts `UsageTotals` and `onViewDetails` callback as props, renders agent count, formatted input/output tokens, tool call count, and a ghost-variant details button. Uses `formatTokenCount` for token values. All numeric values use `--font-mono` class
- [ ] T008 [US1] Add `.ace-usage-summary` styles to `frontend/src/views/engineer/EngineerView.css` — top border separator with `--border` token, `--text-muted` color, `--font-size-xs` size, flex layout with gap, minimal padding (`--space-2`), visually secondary to card content
- [ ] T009 [US1] Modify RecommendationCard in `frontend/src/views/engineer/RecommendationCard.tsx` — accept optional `usage?: RecommendationUsageResponse` prop, render UsageSummaryBar between the content section and the actions section (below setup changes and driver feedback, above the Apply button) when `usage` is defined, manage local `showUsageModal` state via `useState`
- [ ] T010 [US1] Wire usage data in EngineerView in `frontend/src/views/engineer/index.tsx` — add `useRecommendationUsage` calls for each recommendation (via `useQueries` pattern matching existing recommendation detail fetching), pass usage data as prop to RecommendationCard

**Checkpoint**: Summary bar is visible on recommendation cards with usage data. Details button renders but modal not yet implemented.

---

## Phase 3: User Story 2 - View Detailed Agent Breakdown (Priority: P2)

**Goal**: Open a modal from the details button showing a totals row and per-agent rows with domain, tokens, turns, duration, and tool call details.

**Independent Test**: Click the details button on a recommendation with multi-agent usage data and verify the modal shows correct per-agent breakdown with all metrics formatted correctly.

**Dependency**: Requires US1 (T009) for the details button and modal state management in RecommendationCard.

### Tests for User Story 2

- [ ] T011 [P] [US2] Write component tests for UsageDetailModal in `frontend/tests/views/engineer/UsageDetailModal.test.tsx` — renders totals row with formatted values, renders one row per agent with domain/tokens/turns/duration/tools, formats duration as seconds with one decimal (e.g. "2.3s"), handles agent with zero tool calls (empty tools section), uses Modal component with correct title, calls onClose when closed, verifies monospace font on all numeric values

### Implementation for User Story 2

- [ ] T012 [US2] Create UsageDetailModal component in `frontend/src/views/engineer/UsageDetailModal.tsx` — accepts `open`, `onClose`, `usage: RecommendationUsageResponse` props. Uses Modal from `components/ui/Modal`. Renders totals row at top (input tokens, output tokens, tool calls, agent count). Renders agent rows with: domain name, formatted input/output tokens, turn count, duration converted from ms to seconds with one decimal + "s" suffix, tool calls list with tool name and formatted token count. All numeric values use `--font-mono` class
- [ ] T013 [US2] Add `.ace-usage-modal` styles to `frontend/src/views/engineer/EngineerView.css` — table-like layout for agent rows, totals row with stronger visual weight (`--text-primary`, `--font-weight-semibold`), agent rows with `--text-secondary`, tool calls as inline list with `--font-size-xs`, domain names capitalized via CSS `text-transform`, all using design tokens
- [ ] T014 [US2] Connect UsageDetailModal in RecommendationCard in `frontend/src/views/engineer/RecommendationCard.tsx` — render UsageDetailModal controlled by `showUsageModal` state (from T009), pass `onClose` to toggle state, pass usage data from prop

**Checkpoint**: Full usage flow works end-to-end — summary bar shows totals, clicking details opens modal with per-agent breakdown.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Validation and cleanup across both user stories

- [ ] T015 Run TypeScript strict mode check — `cd frontend && npx tsc --noEmit` must pass with zero errors
- [ ] T016 Run full frontend test suite — `cd frontend && npm run test` must pass with all existing + new tests green
- [ ] T017 Verify no hardcoded colors or font values in new/modified files — all colors via CSS custom properties, all numeric fonts via `--font-mono`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on T001 (types), T002 (format utility), T004 (hook)
- **US2 (Phase 3)**: Depends on T009 (RecommendationCard with usage prop and modal state)
- **Polish (Phase 4)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — no dependency on US2
- **User Story 2 (P2)**: Depends on US1's T009 (RecommendationCard modifications provide the modal state and details button callback)

### Within Each Phase

- Tests (T006, T011) can run in parallel with implementation since they test different files
- T007 and T008 can run in parallel (component vs CSS, different files)
- T009 depends on T007 (imports UsageSummaryBar) and T008 (uses CSS classes)
- T010 depends on T009 (passes usage prop to RecommendationCard)
- T012 and T013 can run in parallel (component vs CSS)
- T014 depends on T012 (imports UsageDetailModal)

### Parallel Opportunities

- T002 and T003 can run in parallel (utility implementation + tests in different files)
- T006 and T007 can run in parallel (test file + component file)
- T011 and T012 can run in parallel (test file + component file)

---

## Parallel Example: Phase 1

```
# These can all run in parallel (different files, no dependencies):
T002: Create formatTokenCount in frontend/src/lib/format.ts
T003: Write format tests in frontend/tests/lib/format.test.ts

# Then sequentially:
T001: Add types to frontend/src/lib/types.ts (needed by T004)
T004: Add hook to frontend/src/hooks/useRecommendations.ts (needs types from T001)
T005: Write hook tests in frontend/tests/hooks/useRecommendationUsage.test.ts
```

## Parallel Example: User Story 1

```
# These can run in parallel (different files):
T006: Tests for UsageSummaryBar in frontend/tests/views/engineer/UsageSummaryBar.test.tsx
T007: Create UsageSummaryBar in frontend/src/views/engineer/UsageSummaryBar.tsx
T008: Add CSS styles in frontend/src/views/engineer/EngineerView.css

# Then sequentially:
T009: Modify RecommendationCard (imports T007, uses T008 classes)
T010: Wire in EngineerView (depends on T009)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Types + format utility + hook
2. Complete Phase 2: UsageSummaryBar + RecommendationCard integration
3. **STOP and VALIDATE**: Summary bar visible with formatted token counts
4. Details button rendered but modal not yet functional

### Incremental Delivery

1. Phase 1 → Shared infrastructure ready
2. Add US1 → Summary bar visible on all recommendation cards (MVP)
3. Add US2 → Details modal opens with full agent breakdown
4. Polish → Type check + full test suite green

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable once its phase completes
- Commit after each task or logical group
- All new CSS must use existing design tokens — no hardcoded hex values
- All numeric display must use `--font-mono` (JetBrains Mono)
- Hook must use `staleTime: Infinity` — usage data is immutable
