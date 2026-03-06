# Tasks: Phase 7.4 — Lap Analysis View

**Input**: Design documents from `/specs/018-lap-analysis-view/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api-changes.md

**Tests**: Included — the project has a strong testing culture (968 tests) and the plan explicitly lists test files.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript types, formatting utilities, and CSS foundation shared across all user stories

- [x] T001 Add all analysis TypeScript interfaces (LapSummary, LapListResponse, LapTelemetryResponse, LapMetrics, TimingMetrics, SpeedMetrics, DriverInputMetrics, TyreMetrics, GripMetrics, SuspensionMetrics, FuelMetrics, WheelTempZones, CornerMetrics, CornerPerformance, CornerGrip, CornerTechnique, LapDetailResponse) to frontend/src/lib/types.ts per data-model.md
- [x] T002 [P] Create formatting utility functions (formatLapTime, formatSpeed, formatDelta, formatTemperature, formatPercentage) in frontend/src/views/analysis/utils.ts — all numeric values use JetBrains Mono via CSS class
- [x] T003 [P] Create AnalysisView.css in frontend/src/views/analysis/AnalysisView.css with layout grid (sidebar lap list + main content area), all using ace- prefix BEM naming and design tokens from tokens.css

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend API changes and frontend data-fetching hooks that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Changes

- [x] T004 Add `max_speed: float` field to LapSummary model and update `summarize_lap()` serializer to populate it from `AnalyzedLap.metrics.speed.max_speed` in backend/api/analysis/models.py and backend/api/analysis/serializers.py. Also add `sector_times_s: list[float] | None` to LapSummary, populated from `AnalyzedLap.metrics.timing.sector_times_s`. This allows session-best sector computation client-side from the already-loaded lap list, avoiding N+1 detail queries.
- [x] T005 Add `corners: list[CornerMetrics] = []` field to LapDetailResponse model and update the lap detail route handler to populate it from `AnalyzedLap.corners` in backend/api/analysis/models.py, backend/api/analysis/serializers.py, and backend/api/routes/analysis.py
- [x] T006 Add LapTelemetryChannels and LapTelemetryResponse models to backend/api/analysis/models.py and create `telemetry_for_lap()` serializer in backend/api/analysis/serializers.py that reads telemetry.parquet, filters by lap_number, selects 6 channels (normalized_position, throttle, brake, steering, speed_kmh, gear), and downsamples to max_samples (default 500)
- [x] T007 Add GET /sessions/{session_id}/laps/{lap_number}/telemetry endpoint to backend/api/routes/analysis.py — uses same `_get_analyzed_session` guard, locates the Parquet cache via parser.cache path conventions, calls `telemetry_for_lap()`, returns LapTelemetryResponse. Handle 404 for missing lap and missing Parquet file.
- [x] T008 Add backend tests for: LapSummary now includes max_speed, LapDetailResponse now includes corners list, GET telemetry endpoint returns correct channels and sample count, telemetry endpoint returns 404 for invalid lap, telemetry endpoint returns 409 for unanalyzed session, downsampling produces correct sample count — in backend/tests/api/test_analysis.py

### Frontend Hooks

- [x] T009 Create TanStack Query hooks in frontend/src/hooks/useLaps.ts: `useLaps(sessionId)` with queryKey `["laps", sessionId]` and staleTime Infinity; `useLapDetail(sessionId, lapNumber, enabled)` with queryKey `["lap-detail", sessionId, lapNumber]` and staleTime Infinity; `useLapTelemetry(sessionId, lapNumber, enabled)` with queryKey `["telemetry", sessionId, lapNumber]` and staleTime Infinity — all using apiGet from lib/api.ts, enabled only when sessionId is truthy and lap is actively selected

**Checkpoint**: Backend serves all data needed by the view. Frontend can fetch lap lists, lap details with corners, and telemetry traces. All existing backend tests still pass.

---

## Phase 3: User Story 1 — View Lap List and Summary Metrics (Priority: P1) MVP

**Goal**: User sees all laps from the selected session with summary metrics (lap time, peak speed, throttle %, tyre temps). Fastest lap is highlighted. Invalid laps are de-emphasized.

**Independent Test**: Select any analyzed session → lap list renders with correct metrics within 2 seconds.

### Implementation for User Story 1

- [x] T010 [US1] Create LapList component in frontend/src/views/analysis/LapList.tsx — renders scrollable list of laps from LapListResponse. Each lap shows: lap number, formatted lap time, max_speed, full_throttle_pct, tyre_temps_avg (FL/FR/RL/RR). Fastest flying lap gets a Badge variant="success". Invalid laps are visually de-emphasized (reduced opacity) with classification label Badge. Accepts `selectedLaps: number[]` and `onToggleLap: (lapNumber: number) => void` props. Uses Card, Badge, DataCell components from design system.
- [x] T011 [US1] Replace AnalysisView placeholder in frontend/src/views/analysis/index.tsx with full layout: reads selectedSessionId from useSessionStore, manages local `selectedLaps: number[]` state via useState (max 2), calls useLaps(sessionId). Renders three empty states: (1) no session selected → EmptyState prompting "Go to Sessions", (2) session not analyzed (state !== "analyzed" and !== "engineered") → EmptyState "Analysis required", (3) no laps returned → EmptyState "No laps found". When laps exist, renders LapList in sidebar and main content area (placeholder for now, filled by US2-US5). Implements `handleToggleLap` that enforces max-2 selection by replacing oldest when a third is selected.
- [x] T012 [P] [US1] Write tests for LapList in frontend/tests/views/analysis/LapList.test.tsx — test: renders all laps with correct metrics, fastest lap has success badge, invalid laps show classification badge and reduced emphasis, clicking a lap calls onToggleLap, selected laps have visual selected state
- [x] T013 [P] [US1] Write tests for AnalysisView in frontend/tests/views/analysis/AnalysisView.test.tsx — test: shows "Go to Sessions" empty state when no session selected, shows "Analysis required" when session state is "discovered", renders lap list when laps are returned, selecting a third lap replaces the oldest selection, max 2 laps can be selected simultaneously

**Checkpoint**: User Story 1 is complete — lap list with metrics renders for any analyzed session. Can be demoed independently.

---

## Phase 4: User Story 2 — View Telemetry Traces for a Single Lap (Priority: P1)

**Goal**: Selecting a lap shows 5 telemetry trace charts (throttle, brake, steering, speed, gear) plotted against track position with synchronized crosshair.

**Independent Test**: Select any lap → 5 trace charts render with correct channel data, hovering shows crosshair with values.

### Implementation for User Story 2

- [x] T014 [US2] Create TelemetryChart component in frontend/src/views/analysis/TelemetryChart.tsx — accepts `primaryTelemetry: LapTelemetryResponse | undefined`, `primaryLapNumber: number`, and loading/error states. Renders 5 vertically stacked Recharts LineChart components (one per channel: throttle, brake, steering, speed_kmh, gear) all sharing `syncId="telemetry"` for synchronized crosshair. X-axis is normalized_position (0–1 displayed as 0–100% track position). Each chart has a unique color from design tokens (e.g., throttle=green, brake=red, steering=blue, speed=amber, gear=neutral). Custom Tooltip shows all channel values at hovered position. Chart data is transformed from columnar arrays to row-based format for Recharts. Shows Skeleton loading state when data is pending.
- [x] T015 [US2] Integrate TelemetryChart into AnalysisView in frontend/src/views/analysis/index.tsx — when selectedLaps has at least 1 entry, call useLapTelemetry for the first selected lap and pass the result to TelemetryChart in the main content area. Show EmptyState "Select a lap to view telemetry" when no lap is selected.
- [x] T016 [P] [US2] Write tests for TelemetryChart in frontend/tests/views/analysis/TelemetryChart.test.tsx — test: renders 5 chart containers (one per channel), shows loading skeleton when data is pending, shows channel labels/legends, renders with mock telemetry data without errors, handles missing channel data gracefully

**Checkpoint**: User Stories 1 + 2 complete — user can browse lap list and view telemetry traces for any selected lap.

---

## Phase 5: User Story 3 — Overlay Two Laps for Comparison (Priority: P2)

**Goal**: Selecting two laps overlays both on the same charts — primary lap as solid line, secondary as dashed. Tooltip shows both laps' values side by side.

**Independent Test**: Select two laps → both trace sets render simultaneously with distinct visual styling, tooltip shows values from both laps.

### Implementation for User Story 3

- [x] T017 [US3] Extend TelemetryChart in frontend/src/views/analysis/TelemetryChart.tsx to accept optional `secondaryTelemetry: LapTelemetryResponse | undefined` and `secondaryLapNumber: number | undefined` props. When secondary data is present, render a second Line on each sub-chart with `strokeDasharray="5 5"` and reduced opacity. Update custom Tooltip to show both laps' values side by side, labeled "Lap N" and "Lap M". Merge primary and secondary data rows by nearest normalized_position for aligned comparison.
- [x] T018 [US3] Update AnalysisView in frontend/src/views/analysis/index.tsx to call useLapTelemetry for both selectedLaps entries (when 2 are selected) and pass both to TelemetryChart as primaryTelemetry/secondaryTelemetry. First selected lap is primary (solid), second is secondary (dashed).
- [x] T019 [P] [US3] Write tests for two-lap overlay in frontend/tests/views/analysis/TelemetryChart.test.tsx — test: renders two Line elements per channel when secondary data is present, secondary lines use dashed styling, tooltip shows values from both laps when two are overlaid, deselecting second lap returns to single-lap display

**Checkpoint**: User Stories 1-3 complete — full lap browsing and two-lap telemetry comparison working.

---

## Phase 6: User Story 4 — View Corner-Level Data (Priority: P2)

**Goal**: Selected lap shows a corner data table with entry/apex/exit speeds and understeer/oversteer indicator. Two-lap comparison shows both laps' corner data with deltas.

**Independent Test**: Select a lap with detected corners → corner table shows correct speed and balance data per corner.

### Implementation for User Story 4

- [x] T020 [US4] Create CornerTable component in frontend/src/views/analysis/CornerTable.tsx — accepts `primaryCorners: CornerMetrics[]`, `primaryLapNumber: number`, optional `secondaryCorners: CornerMetrics[]`, optional `secondaryLapNumber: number`. Renders a table with columns: corner number, entry speed, apex speed, exit speed, understeer/oversteer indicator (Badge based on understeer_ratio: positive = understeer/amber, negative = oversteer/red, null or near-zero = neutral). When two laps are provided, show both laps' values per corner with delta (DataCell with delta prop). Handle mismatched corner counts (show data for corners present in each lap, indicate missing corners). Show EmptyState "No corners detected" when primaryCorners is empty. Uses DataCell for numeric values, JetBrains Mono for all numbers.
- [x] T021 [US4] Integrate CornerTable into AnalysisView in frontend/src/views/analysis/index.tsx — call useLapDetail for each selected lap (enabled when lap is selected), pass corners arrays to CornerTable below the TelemetryChart. CornerTable renders only when at least one lap is selected.
- [x] T022 [P] [US4] Write tests for CornerTable in frontend/tests/views/analysis/CornerTable.test.tsx — test: renders corner rows with correct speeds, shows understeer/oversteer badges based on understeer_ratio, shows delta values when two laps are compared, handles mismatched corner counts, shows empty state when no corners detected

**Checkpoint**: User Stories 1-4 complete — full telemetry analysis with corner-level diagnostics.

---

## Phase 7: User Story 5 — View Sector Times (Priority: P3)

**Goal**: Selected lap shows sector time breakdown with best-in-session highlighting. Two-lap comparison shows sector deltas.

**Independent Test**: Select a lap with sector data → sector times display correctly with best-in-session highlighted.

### Implementation for User Story 5

- [x] T023 [US5] Create LapSummaryPanel component in frontend/src/views/analysis/LapSummaryPanel.tsx — accepts `primaryDetail: LapDetailResponse | undefined`, optional `secondaryDetail: LapDetailResponse | undefined`, and `allLaps: LapSummary[]` (for computing session-best sectors). Displays: lap time, max speed, avg speed, full throttle %, braking %, tyre temps grid. Sector times section: renders each sector time, computes best-in-session per sector from `allLaps: LapSummary[]` using `allLaps.filter(l => !l.is_invalid).map(l => l.sector_times_s).filter(Boolean)` — sector_times_s is now available directly on LapSummary, no additional queries needed, highlights best sector with a Badge variant="success". When sector_times_s is null, omits the sector section entirely. When two laps are provided, shows both values with delta via DataCell. All numeric data uses JetBrains Mono CSS class.
- [x] T024 [US5] Integrate LapSummaryPanel into AnalysisView in frontend/src/views/analysis/index.tsx — renders above TelemetryChart when at least one lap is selected. Pass lap detail data and allLaps for session-best computation. Compute session-best sector times from all flying laps' sector data (iterate useLapDetail results or pre-fetch).
- [x] T025 [P] [US5] Write tests for LapSummaryPanel in frontend/tests/views/analysis/LapSummaryPanel.test.tsx — test: renders timing and speed metrics, shows sector times when available, omits sector section when sector_times_s is null, highlights best-in-session sectors, shows delta values when two laps compared

**Checkpoint**: All 5 user stories complete — full Lap Analysis view is functional.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, edge cases, and final quality checks

- [x] T026 Verify all edge cases in AnalysisView: single-lap session (comparison disabled), all-invalid-laps session (message shown), no session selected (empty state), session with 50+ laps (scrollable without UI degradation) — update frontend/src/views/analysis/index.tsx and frontend/src/views/analysis/LapList.tsx as needed
- [x] T027 [P] Run TypeScript strict check (`cd frontend && npx tsc --noEmit`) — fix any type errors across all new/modified files
- [x] T028 [P] Run full backend test suite (`conda run -n ac-race-engineer pytest backend/tests/ -v`) — verify all existing tests still pass alongside new tests
- [x] T029 Run full frontend test suite (`cd frontend && npm run test`) — verify all existing tests still pass alongside new tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on T001 (types) from Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion (hooks + backend changes)
- **US2 (Phase 4)**: Depends on US1 (needs AnalysisView layout and lap selection)
- **US3 (Phase 5)**: Depends on US2 (extends TelemetryChart with overlay)
- **US4 (Phase 6)**: Depends on US1 (needs AnalysisView layout). Can run in parallel with US2/US3.
- **US5 (Phase 7)**: Depends on US1 (needs AnalysisView layout). Can run in parallel with US2/US3/US4.
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no dependencies on other stories
- **US2 (P1)**: After US1 — needs AnalysisView layout and lap selection state
- **US3 (P2)**: After US2 — extends TelemetryChart component
- **US4 (P2)**: After US1 — independent of US2/US3 (different component)
- **US5 (P3)**: After US1 — independent of US2/US3/US4 (different component)

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, Setup phase)
- T004, T005, T006 are sequential — all modify the same backend files (models.py and serializers.py). Execute in order: T004 → T005 → T006.
- T012 and T013 can run in parallel (different test files)
- US4 and US2/US3 can proceed in parallel after US1 completes
- US5 and US2/US3/US4 can proceed in parallel after US1 completes
- T027, T028 can run in parallel (different toolchains)

---

## Parallel Example: After Phase 2

```
# Option A: Sequential (recommended for single developer)
US1 → US2 → US3 → US4 → US5

# Option B: Parallel after US1
US1 → US2 → US3     (telemetry trace pipeline)
US1 → US4            (corner table, parallel with US2/US3)
US1 → US5            (sector times, parallel with US2/US3/US4)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (types, utils, CSS)
2. Complete Phase 2: Foundational (backend changes + hooks)
3. Complete Phase 3: US1 — Lap List
4. **STOP and VALIDATE**: Lap list renders for any analyzed session with correct metrics
5. Demo-ready: user can see all laps with summary data

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Lap list with metrics → Demo (MVP)
3. Add US2 → Telemetry traces for single lap → Demo
4. Add US3 → Two-lap overlay comparison → Demo
5. Add US4 → Corner data table → Demo
6. Add US5 → Sector times panel → Demo
7. Polish → Edge cases, validation, full test pass

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- All backend changes (Phase 2) are backwards-compatible — existing tests must still pass
- Telemetry data is immutable — all TanStack Query hooks use staleTime: Infinity
- Selected laps (max 2) are local useState, NOT Zustand
- All colors from tokens.css — no hardcoded hex values
- All numeric data uses JetBrains Mono CSS class
- All class names use ace- prefix with BEM naming
- Recharts syncId="telemetry" synchronizes crosshair across all 5 channel charts
