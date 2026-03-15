# Feature Specification: Session Views Visual Polish

**Feature Branch**: `037-session-views-visual-polish`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Phase 14.3 — Visual redesign of session detail views (Lap Analysis, Setup Compare, Engineer), Settings view, and a new session detail header to match the design language established in Phases 14.1 and 14.2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session Detail Context Header (Priority: P1)

A driver navigates into a session and immediately sees the full context of that session displayed in a header bar above the tab content. The header shows the car's badge image and display name, the track's preview image and display name (with layout suffix if applicable), the session date and time, total lap count, best lap time, and the session's current status (e.g., analyzed, engineered). This replaces the minimal session identifier that currently appears and gives the driver confidence they are looking at the right session without needing to check the breadcrumb.

**Why this priority**: The session detail header is the visual anchor for all three session tabs. Without it, the driver enters a session and loses context about which car, track, and date they are examining. This is the single most impactful addition for perceived quality of the session detail area.

**Independent Test**: Can be fully tested by navigating to any session and confirming the header shows the correct car badge/name, track preview/name, date, lap count, best time, and status. Verify the header persists across tab switches (Laps, Setup, Engineer).

**Acceptance Scenarios**:

1. **Given** a driver navigates to a session for "Ferrari 488 GT3" at "Monza", **When** the session detail loads, **Then** a header bar is visible above the tab content showing the car's badge image and "Ferrari 488 GT3" display name, the track's preview image and "Monza" display name, the session date formatted as a readable date, the total lap count, the best lap time formatted as mm:ss.SSS, and a status badge showing the session state.
2. **Given** a session at a track with a layout (e.g., Nurburgring GP), **When** the header renders, **Then** the track display name includes the layout suffix (e.g., "Nurburgring - GP").
3. **Given** a car or track has no image available, **When** the header renders, **Then** a placeholder icon is shown instead — no broken image.
4. **Given** a driver switches between the Laps, Setup, and Engineer tabs, **When** each tab loads, **Then** the session header remains visible and unchanged above the tab content.
5. **Given** a session has no best lap time (e.g., no valid laps), **When** the header renders, **Then** the best lap time shows a dash or "N/A" instead of a broken value.

---

### User Story 2 - Lap Analysis Visual Redesign (Priority: P1)

A driver opens the Lap Analysis tab and sees a view that matches the polished visual style of the garage and tracks views. The card surfaces, border styles, spacing, typography, and color accents are consistent with the design language from the prototypes. The lap list sidebar, telemetry charts, corner metrics table, and summary panels all use the updated styling. All data, charts, and interactive behavior remain exactly the same — only the visual presentation changes.

**Why this priority**: Lap Analysis is the most data-dense view in the application. Visual inconsistency here is the most jarring because the driver transitions directly from the polished garage views into this view. It also contains the most CSS surface area to update.

**Independent Test**: Can be tested by opening Lap Analysis for a session with telemetry data, confirming all sections (lap list, charts, corners, summary) render with updated styling, and verifying that all data values, chart behavior, and interactions (selecting laps, comparing) work identically to before.

**Acceptance Scenarios**:

1. **Given** a session with analyzed telemetry, **When** the Lap Analysis tab is active, **Then** all card surfaces use the updated background, border, and border-radius styles matching the prototype design language.
2. **Given** the lap list sidebar, **When** it renders, **Then** lap items use the updated spacing, hover states, and selected states consistent with the prototype styling.
3. **Given** telemetry charts are displayed, **When** the charts render, **Then** their container cards, axis labels, and legend use the updated visual treatment.
4. **Given** the corner metrics table, **When** it renders, **Then** the table uses the updated row hover states, header styling, and border patterns from the prototypes.
5. **Given** the summary panel with metrics, **When** it renders, **Then** metric cards use the updated grid spacing, typography, and color coding.
6. **Given** any interactive action (selecting a lap, comparing two laps, scrolling), **When** the action is performed, **Then** the behavior is identical to the current implementation — no functional regressions.

---

### User Story 3 - Setup Compare Visual Redesign (Priority: P1)

A driver opens the Setup Compare tab and sees the stint selector, setup diff sections, and metrics panel rendered with the updated visual style. Collapsible sections, parameter diffs with directional indicators, and wheel position grids all use the new card styles, spacing, and color conventions. All comparison logic and data remain unchanged.

**Why this priority**: Setup Compare is the second most data-dense view. Its current styling stands out against the polished garage views.

**Independent Test**: Can be tested by opening Setup Compare for a session with stint data, confirming the stint list, diff sections, and metrics panel render with updated styling, and verifying that stint selection and section toggling work identically.

**Acceptance Scenarios**:

1. **Given** a session with stint data, **When** the Setup Compare tab is active, **Then** all card surfaces and containers use the updated styling.
2. **Given** the stint selector sidebar, **When** it renders, **Then** stint items use the updated spacing and hover/selected states.
3. **Given** the setup diff with collapsible sections, **When** a section is expanded, **Then** parameter rows use the updated grid layout, spacing, and diff indicators (arrows, color coding).
4. **Given** the metrics panel with wheel grids, **When** it renders, **Then** the four-position wheel grid and metric values use the updated typography and spacing.
5. **Given** any interactive action (selecting a stint, toggling a section), **When** the action is performed, **Then** the behavior is identical to the current implementation.

---

### User Story 4 - Engineer View Visual Redesign (Priority: P2)

A driver opens the Engineer tab and sees the chat interface, recommendation cards, analysis progress, usage summaries, and modals rendered with the updated visual style. Message bubbles, setup change cards, driver feedback sections, and the apply-changes confirmation modal all match the prototype design language. All engineer logic, LLM interactions, and data remain unchanged.

**Why this priority**: The engineer view is less frequently visited than Lap Analysis or Setup Compare. It is also more visually distinct (chat interface), so minor differences are less jarring. Still important for overall polish.

**Independent Test**: Can be tested by triggering an engineer analysis, confirming message bubbles, recommendation cards, and usage bars render with updated styling, and verifying that chat input, apply flow, and modal interactions work identically.

**Acceptance Scenarios**:

1. **Given** a session with engineer messages, **When** the Engineer tab is active, **Then** message bubbles use updated styling with correct alignment (user right, assistant left) and updated surface colors.
2. **Given** a recommendation card with setup changes, **When** it renders, **Then** the card uses updated border, spacing, and typography matching the prototype style.
3. **Given** the chat input area, **When** it renders, **Then** the textarea and send button use updated styling consistent with other form elements in the application.
4. **Given** the apply-changes confirmation modal, **When** it opens, **Then** the modal and its change preview table use updated styling.
5. **Given** the usage summary bar, **When** it renders, **Then** token counts and agent details use the updated typography and spacing.
6. **Given** any interactive action (sending a message, applying changes, viewing traces), **When** the action is performed, **Then** the behavior is identical to the current implementation.

---

### User Story 5 - Settings Visual Redesign (Priority: P2)

A driver opens Settings and sees the configuration cards rendered with the updated visual style. The path settings, AI provider selection, theme toggle, diagnostic options, and car data cache table all use the new card layout, spacing, and form element styling. All settings functionality, validation, and API calls remain unchanged.

**Why this priority**: Settings is infrequently visited but should still feel cohesive. The prototype shows a more structured layout with a side navigation pattern.

**Independent Test**: Can be tested by opening Settings, confirming all configuration sections render with updated styling, and verifying that all interactions (changing paths, selecting provider, toggling theme, invalidating cache) work identically.

**Acceptance Scenarios**:

1. **Given** the Settings view, **When** it loads, **Then** all settings cards use the updated surface, border, and spacing styles.
2. **Given** form elements (text inputs, selects, toggles), **When** they render, **Then** they use the updated visual treatment consistent with the prototype styling.
3. **Given** the car data cache table, **When** it renders, **Then** the table uses the updated row styling, status badges, and button styles.
4. **Given** the save/discard footer, **When** changes are pending, **Then** the footer buttons use the updated button styles.
5. **Given** any settings interaction (changing values, saving, validating), **When** the action is performed, **Then** the behavior is identical to the current implementation.

---

### User Story 6 - Visual Consistency Polish (Priority: P3)

After updating all session detail views and Settings, a final review ensures visual consistency across the entire application. All design system components (buttons, badges, modals, toasts, empty states, progress bars, skeletons) look correct with the updated palette in all contexts. Any dead CSS or unused code from the pre-redesign navigation system is removed. Any CSS that references undefined tokens or old patterns is fixed.

**Why this priority**: This is cleanup and polish work that can only happen after the primary view updates are complete. It catches edge cases and inconsistencies that might be missed when focusing on individual views.

**Independent Test**: Can be tested by navigating through every screen in the application, triggering all modal types, toast notifications, loading states, and empty states, and confirming consistent visual treatment throughout.

**Acceptance Scenarios**:

1. **Given** the full application, **When** the driver navigates through all views (Garage, Tracks, Sessions, Laps, Setup, Engineer, Settings), **Then** the visual style is consistent across all screens — no jarring transitions between updated and outdated styling.
2. **Given** all modal types in the application (apply changes, usage details, trace viewer), **When** each is opened, **Then** they all use consistent card styling, spacing, and button patterns.
3. **Given** toast notifications, **When** they appear, **Then** they use styling consistent with the updated palette.
4. **Given** loading and empty states, **When** they appear in any view, **Then** skeletons and empty state components use the updated surface colors and spacing.
5. **Given** the application's CSS files, **When** they are audited, **Then** no CSS rules reference undefined tokens, no dead code from removed navigation patterns remains, and all color values come from design tokens (no hardcoded hex values in view CSS files).

---

### Edge Cases

- What happens when the session detail header is displayed for a session whose car or track metadata is unavailable? The header shows fallback icons and formatted identifiers — no broken images, no errors.
- What happens when a session has zero laps? The header shows "0 laps" and the best lap time shows a dash or "N/A".
- What happens in light theme mode? All updated styling must work correctly in both dark and light themes, using semantic tokens that adapt to the active theme.
- What happens when the window is narrow? All updated layouts must remain usable at narrow widths, with the same responsive breakpoints as the existing views.
- What happens to existing frontend tests? All existing tests must continue to pass after the visual changes. CSS class renaming may require test selector updates.

## Requirements *(mandatory)*

### Functional Requirements

**Session Detail Header**

- **FR-001**: The session detail area MUST display a contextual header bar above the tab content showing car badge image, car display name, track preview image, track display name (with layout suffix if applicable), session date, total lap count, best lap time, and session status.
- **FR-002**: The session detail header MUST use the same data sources for car/track metadata and images that are already available from Phase 14.2.
- **FR-003**: The session detail header MUST persist across tab switches within the same session (Laps, Setup, Engineer) without re-fetching.
- **FR-004**: The session detail header MUST handle missing images gracefully with placeholder icons.

**Visual Redesign (All Views)**

- **FR-005**: The Lap Analysis view MUST update its visual presentation to match the design language from the prototypes: updated surface colors, border styles, border-radius, spacing, typography, and hover states.
- **FR-006**: The Setup Compare view MUST update its visual presentation to match the design language from the prototypes.
- **FR-007**: The Engineer view MUST update its visual presentation to match the design language from the prototypes.
- **FR-008**: The Settings view MUST update its visual presentation to match the design language from the prototypes.
- **FR-009**: All visual updates MUST preserve existing interactive behavior — no functional regressions in any view.
- **FR-010**: All visual updates MUST work correctly in both dark and light themes using semantic design tokens.
- **FR-011**: All numeric data (lap times, telemetry values, setup parameters, deltas, token counts) MUST continue using the monospace font.
- **FR-012**: All color values in view CSS files MUST come from design tokens — no hardcoded hex values.

**Cleanup**

- **FR-013**: Any dead CSS or unused component code from the pre-redesign navigation system that was not cleaned up in Phases 14.1 or 14.2 MUST be removed.
- **FR-014**: Any CSS rules that reference undefined or obsolete tokens MUST be fixed.

### Key Entities

- **Session Detail Header**: A visual component rendered above the session tab content. Attributes: car badge URL, car display name, track preview URL, track display name, session date, lap count, best lap time, session status. Derives all data from existing data sources and session record.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A driver navigating from the Garage Home into any session detail tab perceives a consistent visual style — no jarring transitions between the garage views and the session detail views.
- **SC-002**: The session detail header displays correct car and track information (images, names, stats) for every session, with graceful fallbacks for missing data.
- **SC-003**: All existing frontend tests pass after the visual changes (zero test regressions).
- **SC-004**: Zero hardcoded hex color values exist in any view CSS file — all colors use design tokens.
- **SC-005**: Both dark and light themes render correctly across all updated views.
- **SC-006**: All interactive behaviors (lap selection, stint toggling, chat input, settings changes, modals) function identically to their pre-redesign behavior.
- **SC-007**: No dead CSS rules or unused component code from the pre-redesign navigation remains in the codebase.

## Assumptions

- The design tokens defined in `tokens.css` during Phase 14.1 provide all the semantic color, spacing, and typography tokens needed for the visual updates. If any new tokens are needed, they are added following the existing pattern.
- The HTML prototypes (files 6, 7, 8, 11) are the visual reference for style, not pixel-perfect specifications. The implementation matches the spirit and design language, not exact measurements.
- The session detail header fetches its car/track metadata using the same data sources built in Phase 14.2. No new data sources are needed.
- The session record already contains all necessary fields (car, track, track_config, session_date, lap_count, best_lap_time, state) for the header to display.
- CSS class names may be renamed or restructured as part of the visual update. Any test selectors that rely on CSS class names will be updated accordingly.
- The responsive breakpoints and layout patterns follow those established in the garage views (14.2) — primarily using the `lg` breakpoint for layout shifts.
- The prototypes use Tailwind CSS classes for rapid prototyping. The production implementation uses custom CSS with design tokens (the `ace-` prefix BEM convention), translating the prototype patterns into the project's established CSS approach.

## Out of Scope

- Backend changes of any kind. No new endpoints, no database changes, no server-side code modifications.
- Changes to hooks, data fetching logic, state management, or any business logic in view files.
- Changes to the navigation structure, routing, breadcrumb, or tab bar from Phase 14.1.
- Changes to the Garage Home or Car Tracks views from Phase 14.2.
- Changes to the onboarding wizard or splash screen (already updated in Phase 14.1).
- Adding new features, data displays, or interactions to any view — this is purely a visual update.
- Performance optimization of rendering or data loading.
- Accessibility improvements beyond maintaining current levels (a11y improvements are a separate effort).
