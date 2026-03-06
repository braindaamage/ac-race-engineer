# Feature Specification: Phase 7.4 — Lap Analysis View

**Feature Branch**: `018-lap-analysis-view`
**Created**: 2026-03-06
**Status**: Draft
**Input**: User description: "Phase 7.4 — Lap Analysis view for the AC Race Engineer desktop application. A read-only telemetry exploration view where the user inspects laps from a selected session, views telemetry traces, overlays laps for comparison, and reviews per-lap and per-corner metrics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Lap List and Summary Metrics (Priority: P1)

As a driver, I select a session from the Sessions view and navigate to the Lap Analysis view. I immediately see a list of all laps from that session, each showing its lap time, peak speed, average throttle percentage, and tyre temperatures. The best lap is visually highlighted. I can see at a glance how consistent my driving was across the session.

**Why this priority**: This is the entry point to all analysis. Without the lap list and summary metrics, no further exploration is possible. It delivers standalone value — just seeing lap times and key metrics already helps the driver understand their session.

**Independent Test**: Can be fully tested by selecting any analyzed session and verifying the lap list renders with correct metrics. Delivers immediate value as a session overview.

**Acceptance Scenarios**:

1. **Given** a session with analyzed data is selected, **When** the user opens the Lap Analysis view, **Then** all laps from that session are displayed in a scrollable list within 2 seconds, each showing lap number, lap time, peak speed, average throttle percentage, and average tyre temperatures (FL/FR/RL/RR).
2. **Given** a session with multiple laps, **When** the lap list is displayed, **Then** the fastest lap is visually distinguished from the others (e.g., highlighted badge or color).
3. **Given** a session with laps classified as invalid (pit laps, incomplete laps), **When** the lap list is displayed, **Then** invalid laps are shown but visually de-emphasized and labeled with their classification (pit-in, pit-out, incomplete).
4. **Given** a session that has not been analyzed yet, **When** the user navigates to Lap Analysis, **Then** the view shows a clear message indicating analysis is required and does not display empty or broken data.

---

### User Story 2 - View Telemetry Traces for a Single Lap (Priority: P1)

As a driver, I select a lap from the list and see its telemetry traces plotted against track position. The traces include throttle, brake, steering, speed, and gear. I can see exactly what I was doing at every point on the circuit — where I braked, how much throttle I applied, my steering inputs, and what speed I carried through each section.

**Why this priority**: Telemetry traces are the core analytical tool. A driver cannot understand their on-track behavior without them. This is the primary reason users open the Lap Analysis view.

**Independent Test**: Can be fully tested by selecting any lap and verifying that five trace channels render correctly against track position. Delivers the core analytical capability.

**Acceptance Scenarios**:

1. **Given** a lap is selected from the lap list, **When** the telemetry panel loads, **Then** five traces are displayed: throttle (0-100%), brake (0-100%), steering (normalized range), speed (in the session's unit), and gear (integer values) — all plotted against normalized track position (0-100%).
2. **Given** telemetry traces are displayed, **When** the user hovers over any point on any trace, **Then** a crosshair or tooltip shows the exact values of all five channels at that track position.
3. **Given** telemetry traces are displayed, **When** the user views the chart area, **Then** each trace channel is visually distinct (unique color per channel) and has a labeled legend identifying it.
4. **Given** a lap with missing or partial telemetry data for a channel, **When** traces are rendered, **Then** available channels display normally and missing channels show a "no data" indicator rather than a broken chart.

---

### User Story 3 - Overlay Two Laps for Comparison (Priority: P2)

As a driver, I select two laps from the lap list and their telemetry traces are overlaid on the same chart. I can directly compare where I braked earlier on one lap, where I carried more speed, where I lifted off the throttle. The two laps are visually distinguishable through different line styles or opacity. This is essential for understanding what changed between a fast lap and a slow lap.

**Why this priority**: Lap comparison is the most powerful analysis tool, but it builds on the single-lap trace capability. It requires the foundation of Story 2 and adds the overlay interaction.

**Independent Test**: Can be fully tested by selecting two laps, verifying both trace sets render simultaneously with visual distinction, and confirming values from both laps appear in the tooltip.

**Acceptance Scenarios**:

1. **Given** the lap list is displayed, **When** the user selects two laps (via multi-select interaction such as checkbox or Ctrl+click), **Then** both laps' telemetry traces are overlaid on the same chart with distinct visual styling (solid vs dashed lines, or different opacity levels).
2. **Given** two laps are overlaid, **When** the user hovers over a track position, **Then** the tooltip shows values from both laps side by side, labeled by lap number.
3. **Given** two laps are overlaid, **When** the user selects a third lap, **Then** the oldest selection is deselected (maximum 2 laps overlaid at once) or the user is informed that only two laps can be compared at a time.
4. **Given** two laps are overlaid, **When** the user deselects one lap, **Then** the view returns to showing the single remaining lap's traces.

---

### User Story 4 - View Corner-Level Data for a Lap (Priority: P2)

As a driver, I select a lap and see a breakdown of every detected corner: entry speed, apex speed, exit speed, and whether the car exhibited understeer or oversteer behavior. This helps me identify specific corners that are costing time — maybe I'm braking too early into Turn 3, or I'm getting oversteer on exit of Turn 7.

**Why this priority**: Corner data provides the most actionable insight at a granular level. However, it complements rather than replaces the full telemetry trace, so it is P2.

**Independent Test**: Can be fully tested by selecting a lap with detected corners and verifying each corner displays correct speed and balance data. Delivers targeted diagnostic value.

**Acceptance Scenarios**:

1. **Given** a lap is selected, **When** the corner data panel loads, **Then** a list or table of all detected corners is displayed, each showing: corner number/name, entry speed, apex speed, exit speed, and balance behavior (understeer/oversteer/neutral indicator).
2. **Given** corner data is displayed for a lap, **When** two laps are selected for comparison, **Then** corner data shows both laps' values side by side for each corner, with delta values highlighting where one lap was faster or slower.
3. **Given** a session from a track with many corners, **When** corner data is displayed, **Then** all corners are visible via scrolling without requiring additional navigation or page changes.
4. **Given** a lap where corner detection found no corners (e.g., very short or anomalous data), **When** the user views corner data, **Then** a message indicates no corners were detected rather than showing an empty table.

---

### User Story 5 - View Sector Times (Priority: P3)

As a driver, I see sector time breakdowns for each lap, allowing me to identify which sections of the track I'm gaining or losing time. The best sector times across the session are highlighted, showing the theoretical best lap.

**Why this priority**: Sector times are useful supplementary information but are less critical than full telemetry traces and corner data. Some sessions may not have sector data if the track lacks sector markers.

**Independent Test**: Can be fully tested by selecting a lap with sector data and verifying sector times render correctly. Delivers quick time comparison across track sections.

**Acceptance Scenarios**:

1. **Given** a lap is selected and sector data is available, **When** the lap summary is displayed, **Then** sector times are shown for each sector, and the best sector time across the entire session is visually highlighted (e.g., purple or green badge).
2. **Given** two laps are selected for comparison, **When** sector times are displayed, **Then** each sector shows both laps' times with a delta indicator (faster/slower).
3. **Given** a session where sector data is not available (track has no sector markers), **When** the lap summary is displayed, **Then** the sector section is omitted entirely rather than showing empty data.

---

### Edge Cases

- What happens when a session has only one lap? The view displays that single lap; comparison mode is disabled with an appropriate message.
- What happens when a session has only invalid laps (all pit laps)? The view shows the lap list with all laps marked as invalid and displays a message that no flying laps are available for analysis.
- What happens when telemetry data is very large (long endurance stint with 50+ laps)? The lap list is scrollable and telemetry rendering handles large datasets without freezing the UI.
- What happens when the user navigates to Lap Analysis with no session selected? The view shows an empty state prompting the user to select a session first.
- What happens when the analyzed data is from a mod car with unusual telemetry channels? The view renders available standard channels and gracefully handles missing optional channels.
- What happens when two laps have different numbers of detected corners (e.g., one lap cut a corner)? Corner comparison shows data for the corners available in each lap, indicating where data is missing for one of the laps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The view MUST display all laps from the selected session with per-lap summary metrics: lap number, lap time, peak speed, average throttle percentage, and average tyre temperatures (FL/FR/RL/RR).
- **FR-002**: The view MUST visually distinguish the fastest lap from other laps in the lap list.
- **FR-003**: The view MUST show invalid laps (pit-in, pit-out, incomplete) as de-emphasized entries with their classification label.
- **FR-004**: The view MUST render telemetry traces for a selected lap: throttle, brake, steering, speed, and gear — plotted against normalized track position.
- **FR-005**: Each telemetry trace channel MUST be visually distinct (unique color) with a labeled legend.
- **FR-006**: The view MUST provide an interactive hover/crosshair that shows exact values of all channels at the hovered track position.
- **FR-007**: The view MUST support selecting up to two laps simultaneously for overlay comparison on the same chart.
- **FR-008**: When two laps are overlaid, traces MUST be visually distinguishable (e.g., solid vs dashed lines, or different opacity).
- **FR-009**: When two laps are overlaid, the hover tooltip MUST show values from both laps side by side.
- **FR-010**: The view MUST display corner-level data for the selected lap(s): corner identifier, entry speed, apex speed, exit speed, and balance behavior (understeer/oversteer/neutral).
- **FR-011**: When two laps are selected, corner data MUST show both laps' values side by side with delta indicators.
- **FR-012**: The view MUST display sector times when sector data is available, and omit the section when not available.
- **FR-013**: The view MUST highlight the best sector times across the session.
- **FR-014**: The view MUST be entirely read-only — no modification of session data, no setup changes, no AI analysis triggers.
- **FR-015**: The view MUST work for any car and any track without hardcoded assumptions about circuit layout, number of corners, number of sectors, or car parameters.
- **FR-016**: The view MUST show an appropriate empty state when no session is selected, when the session has not been analyzed, or when no flying laps exist.
- **FR-017**: The view MUST enforce a maximum of two laps selected for comparison at any time.

### Key Entities

- **Lap**: A single circuit traversal within a session. Key attributes: lap number, lap time, classification (flying, pit-in, pit-out, incomplete), validity flag, sector times, peak speed, average throttle, tyre temperatures.
- **Telemetry Trace**: A time-series (or position-series) of a single channel for one lap. Key attributes: channel name (throttle, brake, steering, speed, gear), array of position-value pairs.
- **Corner**: A detected corner within a lap. Key attributes: corner identifier, entry speed, apex speed, exit speed, balance behavior (understeer/oversteer/neutral).
- **Sector**: A timed section of the track. Key attributes: sector number, sector time, is-best-in-session flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see all laps from the selected session within 2 seconds of opening the view.
- **SC-002**: Selecting a lap displays its telemetry traces within 1 second.
- **SC-003**: Overlaying two laps for comparison is achievable in a single interaction (select second lap) without requiring a separate "compare" mode or navigation.
- **SC-004**: Corner data for the selected lap is visible without additional navigation — it is present on the same view as the telemetry traces.
- **SC-005**: The view renders correctly for sessions with 1 to 100+ laps without UI degradation.
- **SC-006**: The view works for any car/track combination, including modded content with non-standard telemetry.
- **SC-007**: All displayed metrics (lap times, speeds, temperatures, corner data) match the values from the analyzed session data with no rounding errors beyond display formatting.

## Assumptions

- The session has already been parsed and analyzed by the backend (Phases 2-3). The Lap Analysis view consumes analyzed data; it does not trigger analysis.
- Telemetry trace data for individual laps is available from the backend API (the analysis endpoints provide per-lap detail including positional telemetry).
- Corner detection data is available from the backend as part of the analyzed session (Phase 2 CornerDetector + Phase 3 CornerAnalyzer).
- Sector data availability depends on the track — some tracks have sector markers, others do not. The view adapts to what is available.
- The normalized track position (0-100%) is computed by the backend and provided as part of the telemetry data.
- The maximum of 2 laps for overlay comparison is a deliberate design constraint to keep the UI readable. This may be revisited in future phases.
- Tyre temperatures displayed are the average surface temperatures per tyre, as computed by the analyzer.
