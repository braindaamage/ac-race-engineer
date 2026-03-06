# Feature Specification: Setup Compare View

**Feature Branch**: `019-setup-compare-view`
**Created**: 2026-03-06
**Status**: Draft
**Input**: User description: "Phase 7.5 — Setup Compare view for the AC Race Engineer desktop application."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare Two Stints Side-by-Side (Priority: P1)

The driver opens the Compare view with an analyzed session already selected. They see a list of the session's stints, each labeled with its stint index, setup filename (if available), lap count, and average lap time. They select two stints to compare. The view shows a setup diff — every parameter that changed between the two stints, organized by INI section (suspension, tyres, aerodynamics, differential, etc.). Each changed parameter shows its value in stint A, its value in stint B, and the direction of change. Unchanged parameters are hidden by default. Alongside the diff, the view shows performance metric deltas: average lap time difference, tyre temperature differences, consistency (lap time standard deviation), and peak lateral G difference between the two stints.

**Why this priority**: This is the core value of the view — understanding what changed and whether it helped.

**Independent Test**: Can be fully tested by selecting two stints from a multi-stint session and verifying that setup parameter differences and metric deltas appear correctly.

**Acceptance Scenarios**:

1. **Given** a session with 3 stints is selected and analyzed, **When** the driver opens Compare view, **Then** all 3 stints are listed with their stint index, setup filename, lap count, and average lap time.
2. **Given** the stint list is visible, **When** the driver selects stint 0 and stint 2, **Then** a setup diff shows only the parameters that differ between those two stints, organized by INI section.
3. **Given** two stints are selected, **When** the comparison loads, **Then** performance metric deltas (average lap time, tyre temperatures, consistency, peak lateral G) are displayed alongside the setup diff.
4. **Given** two stints have identical setups, **When** compared, **Then** the setup diff section shows an appropriate message indicating no parameters changed, while metric deltas are still displayed.

---

### User Story 2 - Single-Stint Session Handling (Priority: P2)

The driver opens the Compare view with a session that has only one stint (no pit stops). Instead of an empty or broken comparison, the view shows a clear message explaining that setup comparison requires at least two stints with different setups.

**Why this priority**: Prevents confusion when the feature cannot provide its core value.

**Independent Test**: Can be tested by selecting a single-stint session and verifying the explanatory message appears.

**Acceptance Scenarios**:

1. **Given** a session with only one stint is selected, **When** the driver opens Compare view, **Then** a message explains that comparison requires at least two stints.
2. **Given** no session is selected, **When** the driver opens Compare view, **Then** a message prompts them to select a session first.

---

### User Story 3 - Toggle Unchanged Parameters (Priority: P3)

By default, the setup diff hides unchanged parameters to keep the comparison focused. The driver can toggle a control to reveal all parameters, showing the full setup side-by-side. This is useful when the driver wants to understand the complete context of both setups, not just the differences.

**Why this priority**: Enhances the comparison but is not essential for understanding what changed.

**Independent Test**: Can be tested by toggling the "show all parameters" control and verifying unchanged parameters appear/disappear.

**Acceptance Scenarios**:

1. **Given** two stints are compared and some parameters are unchanged, **When** the "show all" toggle is off (default), **Then** only changed parameters are visible in the diff.
2. **Given** the "show all" toggle is turned on, **When** viewing the comparison, **Then** all parameters from both stints appear, with changed parameters visually distinguished from unchanged ones.

---

### Edge Cases

- What happens when a stint has no associated setup file? The stint still appears in the list but is marked as "no setup data". Selecting it for comparison shows metric deltas only, with the setup diff section showing a message that setup data is unavailable.
- What happens when the two stints use setups with different parameter sets (e.g., one has aero parameters the other doesn't)? Parameters present in only one stint are shown as added/removed rather than changed.
- What happens when an analyzed session has stints but no stint comparisons are available from the backend? The view shows the stint list but displays an error when attempting to compare, explaining that comparison data could not be computed.
- What happens when metric deltas contain null values (e.g., no lap time data for a stint)? The metric is displayed as "N/A" rather than zero or blank.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The view MUST display all stints from the selected session, each showing stint index (1-indexed for display), setup filename (or "no setup" indicator), flying lap count, and average lap time.
- **FR-002**: The user MUST be able to select exactly two stints to compare, using a clear selection mechanism.
- **FR-003**: The setup diff MUST show every parameter that differs between the two selected stints, organized by INI section name.
- **FR-004**: Each changed parameter MUST display its section, name, value in stint A, value in stint B, and a visual indicator of the direction of change (increase/decrease).
- **FR-005**: Unchanged parameters MUST be hidden by default, with a toggle to reveal all parameters.
- **FR-006**: The view MUST display performance metric deltas between the two stints: average lap time difference, tyre temperature differences (per wheel position), lap time consistency (standard deviation difference), and peak lateral G difference.
- **FR-007**: The view MUST handle sessions with only one stint by showing an explanatory message instead of the comparison interface.
- **FR-008**: The view MUST handle the case where no session is selected by prompting the user to select one.
- **FR-009**: The view MUST work for any car — section names and parameter names come from the data, never hardcoded.
- **FR-010**: The view MUST be read-only — no ability to modify setup files or trigger recommendations.
- **FR-011**: Metric deltas with null or missing values MUST display as "N/A" rather than zero or blank.
- **FR-012**: Parameters present in only one stint's setup MUST be visually distinguished as added or removed.

### Key Entities

- **Stint**: A continuous run on a specific setup within a session, identified by stint index. Has an optional setup filename, a list of lap numbers, flying lap count, and aggregated metrics (average lap time, standard deviation, tyre temperatures, slip data, peak lateral G).
- **Setup Parameter Delta**: A single parameter that changed between two stints. Identified by INI section and parameter name, with the value from each stint.
- **Metric Deltas**: Aggregated performance differences between two stints — lap time, tyre temps, slip angles, slip ratios, peak lateral G. All values are nullable.
- **Stint Comparison**: The combination of setup parameter deltas and metric deltas between two specific stints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify all stints from a session and their setup filenames within 5 seconds of opening the Compare view.
- **SC-002**: Users can view the complete setup diff and performance deltas between any two stints within 2 seconds of selecting them.
- **SC-003**: The comparison correctly displays 100% of changed parameters between two stints — no omissions, no false changes.
- **SC-004**: The view renders correctly for any car model, including modded cars with non-standard setup parameters.
- **SC-005**: Sessions with a single stint clearly communicate that comparison is not available, with no broken UI elements.
- **SC-006**: All performance metric deltas are displayed with correct sign (positive = increase from stint A to stint B) and appropriate precision.

## Assumptions

- The backend already provides the required endpoints: `GET /sessions/{id}/stints` returns all stints with their metrics, and `GET /sessions/{id}/compare?stint_a=X&stint_b=Y` returns the setup diff and metric deltas.
- The session must be analyzed (parsed + analyzed) before comparison is available. The view does not trigger analysis.
- Stint indices are integers starting from 0. The user sees them labeled as "Stint 1", "Stint 2", etc. (1-indexed display).
- The existing design system components (Card, Badge, DataCell, EmptyState, etc.) and design token system are used for visual consistency with the rest of the application.
- The view replaces the current placeholder in the compare view.

## Scope Boundaries

**In scope**:
- Stint list display with metadata
- Two-stint selection mechanism
- Setup parameter diff (organized by section, changed-only by default, toggle for all)
- Performance metric deltas display
- Empty/single-stint state handling
- Frontend tests for all components

**Out of scope**:
- AI analysis or setup recommendations (Phase 7.6)
- Telemetry traces or per-lap detail (Phase 7.4)
- Modifying setup files
- Triggering session analysis from this view
- Comparing stints across different sessions
