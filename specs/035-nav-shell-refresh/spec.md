# Feature Specification: Navigation Shell & Visual Refresh

**Feature Branch**: `035-nav-shell-refresh`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Phase 14.1 — Replace flat sidebar navigation with hierarchical car-centric flow, update visual identity, introduce URL-based routing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hierarchical Car-Centric Navigation (Priority: P1)

A driver opens the application and lands on the Garage Home view showing all cars they have session data for. They select a car to see tracks driven with that car, select a track to see sessions for that car+track combination, and enter a session to access the Lap Analysis, Setup Compare, and Engineer tabs. At every level, the breadcrumb in the header shows their position in the hierarchy and lets them click any segment to navigate back to that level.

**Why this priority**: This is the core structural change — every other feature depends on the navigation hierarchy existing and working correctly. Without it, the new layout has no content to display.

**Independent Test**: Can be fully tested by navigating the full path (Garage Home → Car → Track → Session → Tab) and back via breadcrumb, confirming correct view rendering and URL updates at each level.

**Acceptance Scenarios**:

1. **Given** the app has loaded and the user has completed onboarding, **When** the app reaches the main interface, **Then** the Garage Home view is displayed (not the old Sessions list) and the URL reflects the home route.
2. **Given** the user is on Garage Home, **When** they select a car, **Then** the Car Tracks view is displayed showing tracks for that car, the breadcrumb shows "Home / Car Name", and the URL updates to include the car identifier.
3. **Given** the user is on Car Tracks, **When** they select a track, **Then** the Sessions view is displayed showing sessions for that car+track, the breadcrumb shows "Home / Car Name / Track Name", and the URL updates accordingly.
4. **Given** the user is on Sessions for a car+track, **When** they select a session, **Then** the Session Detail view is displayed with the Lap Analysis tab active by default, the breadcrumb shows "Home / Car Name / Track Name / Session", and the URL includes the session identifier.
5. **Given** the user is in Session Detail, **When** they click the "Car Name" segment in the breadcrumb, **Then** they navigate back to the Car Tracks view for that car, the URL updates, and no session is selected.
6. **Given** the user is anywhere in the hierarchy, **When** they click "Home" in the breadcrumb, **Then** they navigate back to Garage Home.
7. **Given** the user is at the Garage/Tracks/Sessions level, **When** they view the tab bar below the header, **Then** the tab bar shows contextual navigation tabs for the current level (e.g., Garage Home, Tracks, Sessions). **When** the user is in Session Detail, **Then** the tab bar shows the three work tabs (Lap Analysis, Setup Compare, Engineer).

---

### User Story 2 - Session Detail Tabs (Priority: P1)

When a driver enters a session from the sessions list, they see a tab bar with three tabs: Lap Analysis, Setup Compare, and Engineer. Clicking a tab switches the content below without leaving the session context. The active tab is visually distinguished.

**Why this priority**: Equal to navigation because the existing views must render correctly inside the new tabbed layout — this validates that the migration preserves all existing functionality.

**Independent Test**: Can be tested by entering a session and switching between all three tabs, confirming each renders its existing content identically to the current sidebar-based approach.

**Acceptance Scenarios**:

1. **Given** the user navigates to a session, **When** the Session Detail view loads, **Then** a tab bar with "Lap Analysis", "Setup Compare", and "Engineer" is visible, and "Lap Analysis" is active by default.
2. **Given** the user is on the Lap Analysis tab, **When** they click the "Setup Compare" tab, **Then** the Setup Compare content replaces the Lap Analysis content and the tab's active state moves.
3. **Given** the user is on any session tab, **When** they click a different tab, **Then** the URL updates to reflect the active tab, enabling deep-linking directly to a specific tab.
4. **Given** a deep-link URL pointing to the Engineer tab of a specific session, **When** the user navigates to that URL, **Then** the app loads directly into that session's Engineer tab with the correct breadcrumb showing.

---

### User Story 3 - Updated Visual Identity (Priority: P2)

The application adopts a new brand color palette, the new logo, and icon-font icons replacing emoji-based icons. The look and feel matches the visual language established in the HTML prototypes.

**Why this priority**: Important for the polished feel but does not block navigation functionality — the app works correctly with old tokens, it just looks outdated.

**Independent Test**: Can be tested by comparing the rendered application against the prototype screenshots — verifying colors, logo placement, icon rendering, and overall visual consistency.

**Acceptance Scenarios**:

1. **Given** the app loads in dark mode, **When** the user views any screen, **Then** the background, surface, text, and accent colors match the new brand palette (dark background #0B1015, surface #171E27, brand red #E60000, brand blue #00CCFF).
2. **Given** the app loads in light mode, **When** the user views any screen, **Then** the light theme colors are correctly applied (background #F8F9FA, surface #FFFFFF).
3. **Given** the header is visible, **When** the user looks at the top-left, **Then** the new logo image is displayed alongside the application name — not a text-only placeholder.
4. **Given** any navigation element or UI control that previously used emoji icons, **When** the user views it, **Then** an icon-font icon (Font Awesome) is displayed instead of emoji.
5. **Given** any component in the application, **When** it references a CSS custom property, **Then** the property resolves to a defined value — no tokens fall through to browser defaults.
6. **Given** the application is installed on the desktop, **When** the user views the application icon in the taskbar, start menu, or file explorer, **Then** the icon displays the new logo (not the previous default Tauri icon).

---

### User Story 4 - Settings Access from Header (Priority: P2)

The driver can access Settings from any point in the application via a persistent icon in the header, without the sidebar.

**Why this priority**: Settings must remain accessible after sidebar removal, but the feature is small and self-contained.

**Independent Test**: Can be tested by clicking the settings icon from multiple locations in the hierarchy and confirming the Settings view opens correctly each time.

**Acceptance Scenarios**:

1. **Given** the user is on any view in the application, **When** they click the settings icon in the header, **Then** the Settings view is displayed.
2. **Given** the user is in Settings, **When** they navigate back (via breadcrumb, browser back, or a close/back action), **Then** they return to the view they were on before entering Settings.

---

### User Story 5 - Placeholder Views for Garage Home and Car Tracks (Priority: P3)

The Garage Home and Car Tracks views display skeleton/placeholder content with indicative text showing what will be populated in Phase 14.2. They are navigable and correctly positioned in the hierarchy, but do not yet show real data.

**Why this priority**: These are explicitly deferred to Phase 14.2 for real content — in 14.1 they exist only to validate the navigation shell.

**Independent Test**: Can be tested by navigating to Garage Home and Car Tracks, confirming placeholder content renders and navigation in/out works correctly.

**Acceptance Scenarios**:

1. **Given** the app loads, **When** the Garage Home view is displayed, **Then** it shows placeholder content indicating it will list cars with session data (not a blank screen).
2. **Given** the user selects a car, **When** the Car Tracks view is displayed, **Then** it shows placeholder content indicating it will list tracks for that car.
3. **Given** the placeholder views, **When** the user navigates through them, **Then** the breadcrumb, URL, and back-navigation all function correctly despite the views having no real data.

---

### User Story 6 - Onboarding within New Layout (Priority: P3)

A first-time user completes the onboarding wizard. The wizard renders inside the new layout (without the old sidebar) and transitions to the Garage Home view upon completion.

**Why this priority**: Onboarding is a one-time flow — important but low frequency. The existing wizard logic is unchanged; only the container changes.

**Independent Test**: Can be tested by resetting onboarding state, launching the app, completing all wizard steps, and confirming the user lands on Garage Home.

**Acceptance Scenarios**:

1. **Given** onboarding has not been completed, **When** the app loads, **Then** the onboarding wizard is displayed within the new layout (no sidebar visible, no breadcrumb).
2. **Given** the user completes the final onboarding step, **When** they confirm, **Then** they are navigated to the Garage Home view with the full header and navigation visible.

---

### User Story 7 - Updated Splash Screen (Priority: P2)

When the application starts, the driver sees a splash screen while the backend initializes. The splash screen displays the new application logo and a loading indicator, matching the visual style of the new brand identity.

**Why this priority**: The splash screen is the first thing every user sees on every launch. It must reflect the new identity, but it does not block navigation functionality.

**Independent Test**: Can be tested by launching the app (or simulating backend unavailability) and confirming the new logo, loading animation, and brand colors appear.

**Acceptance Scenarios**:

1. **Given** the application is starting, **When** the splash screen is displayed, **Then** the new logo image is shown prominently (not the old text-based branding).
2. **Given** the splash screen is visible, **When** the backend is still initializing, **Then** a loading indicator and status text are displayed using the new brand palette.
3. **Given** the backend becomes ready, **When** the splash screen transitions to the main interface, **Then** the transition is smooth and lands on Garage Home (or onboarding if first run).

---

### Edge Cases

- What happens when a user navigates to a URL with a car identifier that has no session data? The app shows an empty state with a way to navigate back to Garage Home.
- What happens when a user navigates to a URL with an invalid session identifier? The app shows an error/empty state and provides breadcrumb navigation back to a valid level.
- What happens when the user resizes the window to a very narrow width? The breadcrumb truncates gracefully (e.g., collapsing intermediate segments or showing only the current level with a back action) and the tab bar remains usable.
- What happens when the user uses browser back/forward buttons? The navigation state (breadcrumb, active view, URL) stays consistent — no stale views or broken states.
- What happens when the user is in a session and the session data is deleted or becomes unavailable? The app shows an appropriate empty state rather than crashing.
- What happens when the user navigates directly to a tab URL without going through the hierarchy? The breadcrumb reconstructs the full path from the URL parameters and the view loads correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST use URL-based routing with a hierarchical structure: home, car, car+track, session, and session+tab levels.
- **FR-002**: The application MUST display a fixed header containing the application logo, a dynamic breadcrumb reflecting the current navigation position, and a settings access icon.
- **FR-003**: Each breadcrumb segment MUST be clickable and navigate the user to that level of the hierarchy.
- **FR-004**: The session detail view MUST display a tab bar with three tabs: Lap Analysis, Setup Compare, and Engineer.
- **FR-005**: The active tab MUST be reflected in the URL, enabling direct deep-linking to a specific session tab.
- **FR-006**: The sidebar MUST be removed entirely from the application layout.
- **FR-007**: Session identity for views MUST come from the URL route parameters, not from a shared in-memory store.
- **FR-008**: The application MUST apply the new brand color palette via updated design system tokens, covering both dark and light themes.
- **FR-009**: The application MUST display the new logo image in the header.
- **FR-010**: All navigation and UI icons MUST use an icon font instead of emoji characters.
- **FR-011**: All CSS custom properties referenced by components MUST resolve to defined values — no undefined tokens falling through to browser defaults.
- **FR-012**: The Garage Home view MUST render placeholder content indicating future car listing functionality.
- **FR-013**: The Car Tracks view MUST render placeholder content indicating future track listing functionality.
- **FR-014**: The Settings view MUST be accessible from a persistent header element on every screen.
- **FR-015**: The onboarding wizard MUST render within the new layout without the sidebar and transition to Garage Home upon completion.
- **FR-016**: The existing views (Lap Analysis, Setup Compare, Engineer, Settings) MUST retain their current internal content and functionality without modification.
- **FR-017**: Browser back/forward navigation MUST correctly update the view, breadcrumb, and URL in sync.
- **FR-018**: Application desktop icons MUST be regenerated from the new logo asset.
- **FR-019**: The splash screen MUST display the new logo image and use the updated brand color palette during backend initialization.
- **FR-020**: The tab bar below the header MUST be contextual — showing navigation tabs at the garage/tracks/sessions levels and work tabs (Lap Analysis, Setup Compare, Engineer) at the session detail level.

### Key Entities

- **Navigation Route**: Represents a position in the hierarchy (level, car identifier, track identifier, session identifier, active tab). Derived entirely from the URL.
- **Breadcrumb Segment**: A clickable element representing one level of the hierarchy (label, target route). Generated from the current navigation route.
- **Tab Definition**: A named tab within the session detail view (label, icon, associated view component).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can navigate from Garage Home to a specific session tab in 4 clicks or fewer (Home → Car → Track → Session, with default tab).
- **SC-002**: Every screen in the application has a unique, bookmarkable URL — copying and pasting a URL loads the exact same view.
- **SC-003**: All existing views (Lap Analysis, Setup Compare, Engineer, Settings) render identically to their pre-migration state — no visual regressions or broken functionality.
- **SC-004**: Zero CSS custom properties referenced by components resolve to browser defaults — all tokens are defined.
- **SC-005**: The application renders correctly at viewport widths from 1024px to 2560px, with the breadcrumb and tabs remaining usable at all sizes.
- **SC-006**: All existing frontend tests continue to pass after the migration, adapted only for the new routing/layout container.
- **SC-007**: The onboarding wizard completes successfully and lands the user on Garage Home within the new layout.
- **SC-008**: Browser back/forward buttons produce correct, consistent navigation at every level of the hierarchy.

## Assumptions

- The HTML prototypes in `frontend/prototypes/` are the authoritative visual reference for the new design.
- Font Awesome 6.x is the icon font to be used (as seen in the prototypes).
- The Inter and JetBrains Mono fonts used in prototypes will be adopted for the application typography.
- Garage Home and Car Tracks views are intentionally placeholder skeletons in this phase — real content comes in Phase 14.2.
- No backend changes are required — the existing API provides sufficient data (sessions list includes car and track identifiers that can be used for grouping).
- The session store (Zustand) will be reduced in role or removed, since session identity now comes from the URL.
- The Tauri shell configuration may need minor updates to ensure the webview handles client-side routing correctly.
- The application minimum supported viewport width is 1024px (desktop application, not mobile).

## Out of Scope

- Real content and data fetching for Garage Home and Car Tracks views (Phase 14.2).
- Any backend API changes or new endpoints.
- Changes to the internal logic of Lap Analysis, Setup Compare, Engineer, or Settings views.
- Mobile or tablet responsive layouts (this is a desktop application).
- Real-time telemetry dashboard (shown in prototype 1 but not part of the current application scope).
- Analysis Queue and Import Data views (shown in prototypes but not part of the current application).
