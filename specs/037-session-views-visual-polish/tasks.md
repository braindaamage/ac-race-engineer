# Tasks: Session Views Visual Polish

**Input**: Design documents from `/specs/037-session-views-visual-polish/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/design.md, quickstart.md

**Tests**: Included — one new test file for SessionHeader. Existing tests must continue passing (regression check).

**Organization**: Tasks grouped by user story. US1 (Session Detail Header) is foundational — the header component lives in SessionLayout and must be built before the view CSS updates can be visually verified in context. US2/US3 (Analysis/Compare CSS) can run in parallel. US4/US5 (Engineer/Settings CSS) can run in parallel after US2/US3 or concurrently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup — Token Audit & Baseline

**Purpose**: Verify existing tokens cover all needed values, fix any gaps, establish baseline test pass

- [x] T001 Run full frontend test suite (`cd frontend && npm run test`) and TypeScript check (`npx tsc --noEmit`) to establish baseline — all tests must pass before any changes
- [x] T002 [P] Audit `frontend/src/tokens.css` for completeness against contracts/design.md token mapping. Verify all referenced tokens exist. If any tokens are missing (unlikely), add them following the existing primitive → semantic pattern.
- [x] T003 [P] Fix the hardcoded `rgba(255, 255, 255, 0.7)` in `frontend/src/views/engineer/EngineerView.css` (line ~84, `.ace-message--user .ace-message__timestamp`) — replace with `color-mix(in srgb, white 70%, transparent)` for token compliance per constitution Principle XII.

---

## Phase 2: User Story 1 — Session Detail Context Header (Priority: P1) 🎯 MVP

**Goal**: Driver sees car/track context, session stats, and status badge above the tab content on every session detail view

**Independent Test**: Navigate to any session → header shows correct car badge/name, track preview/name, date, laps, best time, status badge

### Implementation

- [x] T004 [US1] Create `frontend/src/components/layout/SessionHeader.tsx` — new component that renders the session detail context header:
  - Props: receives `sessionId` from router params
  - Data: calls `useSessions()` to find the SessionRecord by session_id, calls `useCarTracks(session.car)` to resolve display names and image URLs
  - Layout: horizontal bar with:
    - Left: car badge image (48×48, onError fallback to fa-car icon) + car display name + brand/class subtitle
    - Center: track preview image (80×48, onError fallback to fa-road icon) + track display name (with layout suffix if track_config is non-empty)
    - Right: session date (formatted), lap count, best lap time (formatted mm:ss.SSS or "—" if null), status Badge
  - Uses existing components: Badge (for status), existing image fallback pattern from GarageView/CarTracksView
  - Handles loading state: show Skeleton while data fetches
  - Handles missing data: raw identifiers as fallback for display names, placeholder icons for images

- [x] T005 [US1] Create `frontend/src/components/layout/SessionHeader.css` — styles for the session header:
  - `.ace-session-header` — flex row, items-center, padding space-4/space-6, bg-surface, border-bottom border, gap space-6
  - `.ace-session-header__car` — flex row, items-center, gap space-3
  - `.ace-session-header__track` — flex row, items-center, gap space-3
  - `.ace-session-header__stats` — flex row, items-center, gap space-4, margin-left auto
  - `.ace-session-header__badge` — image container with border-radius, object-fit cover, fallback icon circle
  - `.ace-session-header__name` — text-primary, font-weight-semibold
  - `.ace-session-header__subtitle` — text-secondary, font-size-xs
  - `.ace-session-header__stat` — flex column, items-center, font-mono for numeric values
  - `.ace-session-header__stat-label` — text-muted, font-size-xs, uppercase
  - Responsive: stack vertically on narrow viewports
  - All colors from design tokens, JetBrains Mono for numeric values

- [x] T006 [US1] Modify `frontend/src/components/layout/SessionLayout.tsx` — add SessionHeader above the Outlet:
  - Import SessionHeader
  - Read `sessionId` from `useParams()`
  - Render `<SessionHeader sessionId={sessionId} />` above `<Outlet />`
  - Keep existing flex-column layout, SessionHeader is non-scrollable, Outlet area scrolls

- [x] T007 [US1] Update `frontend/src/components/layout/SessionLayout.css` — ensure the layout accommodates the new header:
  - SessionLayout remains flex column, height 100%
  - SessionHeader is fixed-height (non-scrollable)
  - Outlet wrapper gets flex: 1 and overflow-y: auto

### Tests

- [x] T008 [US1] Create `frontend/tests/components/layout/SessionHeader.test.tsx`:
  - Test renders car display name and track display name when data is available
  - Test renders session date, lap count, best lap time (formatted)
  - Test renders status badge with correct variant for each state (analyzed→info, engineered→success)
  - Test shows "—" for best lap time when null
  - Test shows car placeholder icon when badge image fails to load
  - Test shows track placeholder icon when preview image fails to load
  - Test shows raw identifiers when useCarTracks returns no data
  - Mock useSessions, useCarTracks, useParams
  - Provide QueryClientProvider wrapper

**Checkpoint**: Session header is visible on all session detail tabs. Tests pass. Existing tests unaffected.

---

## Phase 3: User Story 2 — Lap Analysis Visual Redesign (Priority: P1)

**Goal**: Lap Analysis view matches the prototype design language — updated cards, spacing, tables, charts

**Independent Test**: Open Laps tab → all sections use updated styling, all interactions work identically

### Implementation

- [x] T009 [US2] Update `frontend/src/views/analysis/AnalysisView.css` — apply prototype-aligned styling:
  - Card containers: `border-radius: var(--radius-lg)` (12px, was radius-md/8px)
  - Section gaps: `gap: var(--space-6)` between major sections
  - Sidebar background: ensure consistent with bg-surface
  - Main content padding: `var(--space-6)`
  - Lap item improvements: updated padding (`var(--space-3) var(--space-4)`), hover background `var(--bg-hover)`, selected state with left border accent `var(--color-brand)`
  - Summary panel: card wrapper with bg-surface, border, radius-lg, padding space-6
  - Corner table: updated header (uppercase, font-size-xs, text-secondary, letter-spacing), row hover (bg-hover), border patterns (border-strong for header, border for rows)
  - Telemetry chart containers: card wrapper with bg-surface, border, radius-lg
  - Sector times: consistent spacing and badge styling

- [x] T010 [P] [US2] Update `frontend/src/views/analysis/TelemetryChart.tsx` — align chart stroke colors with brand palette:
  - Throttle: `#22C55E` (green-500)
  - Brake: `#EF4444` (red-500)
  - Steering: `#06B6D4` (cyan-500)
  - Speed: `#F59E0B` (amber-500)
  - Gear: `#6B7280` (gray-500)
  - Add comment documenting the token references for each color
  - Chart grid/axis colors: use prototype grid color pattern (match --border token value)
  - Tooltip: ensure bg-surface, border, font-size-xs, font-mono for values

**Checkpoint**: Lap Analysis view has updated styling. All existing analysis tests pass.

---

## Phase 4: User Story 3 — Setup Compare Visual Redesign (Priority: P1)

**Goal**: Setup Compare view matches the prototype design language

**Independent Test**: Open Setup tab → stint selector, diff sections, metrics panel all use updated styling

### Implementation

- [x] T011 [US3] Update `frontend/src/views/compare/CompareView.css` — apply prototype-aligned styling:
  - Card containers: `border-radius: var(--radius-lg)`
  - Section gaps: `gap: var(--space-6)`
  - Stint items: updated padding, hover, selected left-border accent
  - Diff section headers: bg-surface, padding, border-bottom, font-weight-semibold
  - Diff rows: 4-column grid with consistent spacing, hover state, alternating subtle bg
  - Diff arrow column: color coding (positive green, negative red, neutral muted)
  - Metrics panel: card wrapper, consistent with analysis summary panel
  - Wheel grid: updated cell padding, font-mono for values, delta colors
  - Collapsible section toggle: consistent icon styling

**Checkpoint**: Setup Compare view has updated styling. All existing compare tests pass.

---

## Phase 5: User Story 4 — Engineer View Visual Redesign (Priority: P2)

**Goal**: Engineer view matches the prototype design language

**Independent Test**: Open Engineer tab → chat, recommendations, modals all use updated styling

### Implementation

- [x] T012 [US4] Update `frontend/src/views/engineer/EngineerView.css` — apply prototype-aligned styling:
  - Engineer header: consistent with other view headers, bg-surface, border-bottom, padding space-4/space-6
  - Message list: gap space-4, padding space-4
  - User messages: rounded-lg (not xl), brand bg, consistent padding
  - Assistant messages: bg-surface, border, rounded-lg, consistent padding
  - Message timestamps: font-size-xs, text-muted (user timestamps use color-mix fix from T003)
  - Recommendation cards: border-radius-lg, bg-surface, border, padding space-6
  - Setup change items: bg (not bg-surface), border, radius-md, padding space-4
  - Driver feedback cards: left 3px border (warning color), bg-surface, padding space-4
  - Typing indicator: consistent dot sizing and animation
  - Analysis progress: consistent bar and label styling
  - Chat input: textarea matches form element contract (border, radius-md, focus state), send button matches primary button style
  - Apply modal table: matches table styling contract (header uppercase, row hover, border patterns)
  - Usage summary bar: consistent spacing, font-mono for token counts
  - Usage detail modal: consistent card sections, metric grid, tool list
  - Trace modal: consistent monospace block styling

**Checkpoint**: Engineer view has updated styling. All existing engineer tests pass.

---

## Phase 6: User Story 5 — Settings Visual Redesign (Priority: P2)

**Goal**: Settings view matches the prototype design language

**Independent Test**: Open Settings → all config sections use updated styling

### Implementation

- [x] T013 [US5] Update `frontend/src/views/settings/Settings.css` — apply prototype-aligned styling:
  - Settings container: keep max-width 720px centered layout
  - Section cards: bg-surface, border, radius-lg, padding space-6, gap space-6 between cards
  - Section headers: font-size-lg, font-weight-semibold, border-bottom border, padding-bottom space-4
  - Form fields: inputs and selects match form element contract (bg, border, radius-md, focus color-ai)
  - Theme toggle buttons: updated active state (brand bg), inactive state (border, secondary text, hover bg-hover)
  - API key input: font-mono, consistent with other inputs
  - Test connection row: consistent button and result styling
  - Footer: border-top, padding-top space-4, flex gap space-3

- [x] T014 [P] [US5] Update `frontend/src/views/settings/CarDataSection.css` — apply prototype-aligned styling:
  - Table: matches table styling contract
  - Status badges: consistent with Badge component variants (resolved → success, unresolved → neutral)
  - Invalidate buttons: consistent with ghost/secondary button styling
  - Scroll container: max-height 400px, subtle scrollbar styling
  - Empty/error states: consistent with EmptyState component

**Checkpoint**: Settings view has updated styling. All existing settings tests pass.

---

## Phase 7: User Story 6 — Visual Consistency Polish (Priority: P3)

**Purpose**: Cross-view audit, dead code removal, final verification

- [x] T015 [US6] Audit all 10 UI component CSS files for token compliance — verify no hardcoded hex colors in:
  - `frontend/src/components/ui/Card.css`
  - `frontend/src/components/ui/Badge.css`
  - `frontend/src/components/ui/Button.css`
  - `frontend/src/components/ui/Modal.css`
  - `frontend/src/components/ui/DataCell.css`
  - `frontend/src/components/ui/EmptyState.css`
  - `frontend/src/components/ui/ProgressBar.css`
  - `frontend/src/components/ui/Skeleton.css`
  - `frontend/src/components/ui/Toast.css`
  - `frontend/src/components/ui/Tooltip.css`
  - Fix: Modal backdrop `rgba(0,0,0,0.5)` — acceptable as a universal backdrop overlay, document as exception. Skeleton fallback `rgba(255,255,255,0.08)` — acceptable as a fallback value after a token reference.

- [x] T016 [P] [US6] Search for and remove any dead CSS or unused code from pre-redesign navigation system. Check:
  - Old sidebar references in layout CSS
  - Unused CSS classes in any view file
  - Commented-out code blocks related to removed navigation
  - Orphaned imports in layout components

- [x] T017 [US6] Verify both themes work correctly — switch between Night Grid (dark) and Garage Floor (light) themes and confirm:
  - SessionHeader renders correctly in both themes
  - All updated view CSS uses semantic tokens that adapt to both themes
  - No color contrast issues introduced
  - Form focus states visible in both themes

---

## Phase 8: Regression & Verification

**Purpose**: Full test suite pass, TypeScript check, manual verification

- [x] T018 Run full frontend test suite: `cd frontend && npm run test` — verify all existing + new tests pass (target: ~435+ tests, 0 failures)
- [x] T019 Run TypeScript strict check: `cd frontend && npx tsc --noEmit` — verify zero type errors
- [x] T020 Manual verification walkthrough:
  1. Navigate Garage → Car → Tracks → Sessions → select a session
  2. Verify SessionHeader shows correct car/track/stats on Laps tab
  3. Switch to Setup tab — header persists, view styling consistent
  4. Switch to Engineer tab — header persists, view styling consistent
  5. Navigate to Settings — verify card/form styling
  6. Toggle theme — verify all views render correctly in both themes
  7. Narrow window — verify responsive layouts don't break

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Session Header (Phase 2)**: Depends on Phase 1 (token audit). The header must be built before views so visual testing has full context.
- **Lap Analysis CSS (Phase 3)**: Depends on Phase 1. Can run in parallel with Phase 2 (different files).
- **Setup Compare CSS (Phase 4)**: Depends on Phase 1. Can run in parallel with Phases 2 and 3 (different files).
- **Engineer CSS (Phase 5)**: Depends on Phase 1 (T003 hardcoded color fix). Can run in parallel with Phases 3 and 4.
- **Settings CSS (Phase 6)**: Depends on Phase 1. Can run in parallel with Phases 3, 4, 5.
- **Polish (Phase 7)**: Depends on all view updates (Phases 2-6) being complete.
- **Regression (Phase 8)**: Depends on all phases complete.

### Parallel Opportunities

**Phase 1** (all parallel):
- T001 (baseline), T002 (token audit), T003 (hardcoded color fix) can run simultaneously

**Phase 2** (sequential within, parallel with Phase 3/4):
- T004 → T005 → T006 → T007 → T008 (SessionHeader build is sequential)
- But Phase 2 as a whole can run in parallel with Phase 3 and Phase 4

**Phases 3 + 4 + 5 + 6** (all parallel with each other):
- T009, T010 (Analysis CSS) — different files from compare/engineer/settings
- T011 (Compare CSS) — independent
- T012 (Engineer CSS) — independent (T003 from Phase 1 must be done first)
- T013, T014 (Settings CSS) — independent, parallel with each other

**Phase 7** (partially parallel):
- T015, T016 can run in parallel

---

## Implementation Strategy

### MVP First (Phases 1-2: Token Audit + Session Header)

1. Complete Phase 1: Baseline + token audit + hardcoded color fix
2. Complete Phase 2: SessionHeader component + tests
3. **STOP and VALIDATE**: Header renders on all session tabs with correct data
4. This delivers the most impactful visual improvement (session context)

### Incremental Delivery

1. Phase 1 → Baseline clean, tokens verified
2. + Phase 2 (US1) → Session header visible (MVP!)
3. + Phase 3 (US2) → Lap Analysis updated (most data-dense view)
4. + Phase 4 (US3) → Setup Compare updated
5. + Phase 5 (US4) → Engineer view updated
6. + Phase 6 (US5) → Settings updated
7. + Phase 7 (US6) → Cross-view polish and cleanup
8. + Phase 8 → Full regression pass

### Aggressive Parallel Strategy

With all file changes independent:

```
Phase 1: T001 + T002 + T003 (parallel)
Phase 2: T004→T005→T006→T007→T008 (sequential)
  ↕ (parallel with)
Phase 3: T009 + T010 (parallel)
Phase 4: T011
Phase 5: T012
Phase 6: T013 + T014 (parallel)
Phase 7: T015 + T016 (parallel after Phases 2-6)
Phase 8: T018→T019→T020 (sequential verification)
```

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All CSS changes are non-breaking — they update visual properties, not DOM structure or class names
- Recharts hex colors are the only permitted exception to the no-hardcoded-hex rule (documented in contracts/design.md)
- The Modal backdrop rgba(0,0,0,0.5) and Skeleton fallback rgba are acceptable existing patterns, not regressions
- JetBrains Mono font required for all numeric data per constitution Principle XII
- Both dark (Night Grid) and light (Garage Floor) themes must be verified for every CSS change
