# Feature Specification: Desktop App Scaffolding, Design System & Backend Integration

**Feature Branch**: `015-desktop-scaffold`
**Created**: 2026-03-05
**Status**: Draft
**Input**: Phase 7.1 — Build the foundational layer of the AC Race Engineer desktop application: Tauri+React scaffold, unified design system (two themes), sidebar navigation, notification system, loading/empty states, and backend sidecar lifecycle management.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application Startup with Backend Sidecar (Priority: P1)

When the user opens the AC Race Engineer desktop app, a loading screen appears showing the app name ("AC Race Engineer") and an animated progress indicator. Behind the scenes, the app launches the backend server as a subprocess and polls its health endpoint until it responds. Once the backend is ready, the loading screen fades out and the main interface appears with the sidebar and a default empty-state view.

**Why this priority**: Nothing else in the app works without a running backend. This is the foundation for every subsequent feature.

**Independent Test**: Launch the app with the backend available — verify the splash screen appears, transitions to the main layout within a few seconds, and the sidebar is visible. Launch the app with no backend executable — verify the error state appears after 15 seconds with a retry button.

**Acceptance Scenarios**:

1. **Given** the app is launched for the first time, **When** the backend starts successfully, **Then** the splash screen shows for the duration of backend startup and transitions to the main interface once `GET /health` returns a success response
2. **Given** the app is launched, **When** the backend fails to respond within 15 seconds (30 polls at 500ms intervals), **Then** the splash screen transitions to an error state displaying a clear message and a "Retry" button
3. **Given** the error state is shown, **When** the user clicks "Retry", **Then** the app restarts the health-check polling sequence from the beginning
4. **Given** the app is running, **When** the user closes the app, **Then** the app signals the backend to shut down and terminates the sidecar process cleanly

---

### User Story 2 - Design System and Theming (Priority: P1)

Every visual element in the application uses a unified design system with design tokens as the single source of truth for colors, spacing, and typography. Two themes exist: "Night Grid" (dark, default) and "Garage Floor" (light). The user can switch between them, and the preference persists across app restarts via the backend configuration.

**Why this priority**: Every screen built in Phases 7.2-7.6 depends on these tokens and components existing. Without them, nothing can be built consistently.

**Independent Test**: Open the app, verify the dark theme is active by default. Switch to the light theme — verify all visible elements update immediately. Close and reopen the app — verify the light theme persists.

**Acceptance Scenarios**:

1. **Given** a fresh install, **When** the app loads, **Then** the "Night Grid" (dark) theme is active
2. **Given** the dark theme is active, **When** the user switches to "Garage Floor" (light), **Then** all UI elements update their colors instantly without a page reload
3. **Given** the user selected the light theme, **When** they close and reopen the app, **Then** the light theme is still active (preference stored via backend configuration)
4. **Given** either theme is active, **When** viewing any screen, **Then** all colors come exclusively from design tokens — no hardcoded color values in components

---

### User Story 3 - Sidebar Navigation (Priority: P1)

A persistent left sidebar provides navigation between five sections: Sessions, Lap Analysis, Setup Compare, Engineer, and Settings. The sidebar shows which section is active. Sections that require a session to be selected (Lap Analysis, Setup Compare, Engineer) are visually indicated as unavailable when no session is selected, though they remain clickable and show an empty state explaining why content is unavailable.

**Why this priority**: Navigation is the skeleton of the app. Every feature view in later phases needs to be reachable through the sidebar.

**Independent Test**: Click each sidebar item — verify the active indicator moves and the corresponding view placeholder appears. With no session selected, click "Lap Analysis" — verify an empty state appears explaining that a session must be selected first.

**Acceptance Scenarios**:

1. **Given** the main interface is loaded, **When** the user views the sidebar, **Then** they see the app logo at the top followed by five navigation items: Sessions, Lap Analysis, Setup Compare, Engineer, Settings
2. **Given** the user is on any section, **When** they click a different sidebar item, **Then** the active indicator moves to the clicked item and the main content area shows the corresponding view
3. **Given** no session is selected, **When** the user views the sidebar, **Then** Lap Analysis, Setup Compare, and Engineer items are visually distinguished (dimmed or with a lock icon) to indicate they need a session
4. **Given** no session is selected, **When** the user clicks "Lap Analysis", **Then** the main content area shows an empty state with a message explaining that a session must be selected first and suggesting they go to Sessions

---

### User Story 4 - Notification System with Job Tracking (Priority: P2)

Background operations report their completion status through toast notifications in the bottom-right corner. Notifications come in four types (info, success, warning, error), each visually distinct. Non-error notifications auto-dismiss after 5 seconds. Error notifications persist until manually dismissed. The notification system integrates with WebSocket job tracking so that when a background job completes or fails, a notification appears automatically.

**Why this priority**: Background operations (session processing, AI analysis) are core to the app experience in later phases. The notification infrastructure must exist before those features are built.

**Independent Test**: Programmatically trigger each notification type — verify they appear with correct styling. Trigger an info notification — verify it auto-dismisses after approximately 5 seconds. Trigger an error notification — verify it persists until the user clicks the dismiss button.

**Acceptance Scenarios**:

1. **Given** the app is running, **When** an info notification is triggered, **Then** a toast appears in the bottom-right with an informational style and auto-dismisses after 5 seconds
2. **Given** the app is running, **When** a success notification is triggered, **Then** a toast appears with a green accent and auto-dismisses after 5 seconds
3. **Given** the app is running, **When** a warning notification is triggered, **Then** a toast appears with an amber accent and auto-dismisses after 5 seconds
4. **Given** the app is running, **When** an error notification is triggered, **Then** a toast appears with a red accent and remains visible until the user dismisses it
5. **Given** a WebSocket connection to the backend job stream, **When** a job transitions to "completed", **Then** a success notification appears with the job's summary
6. **Given** a WebSocket connection to the backend job stream, **When** a job transitions to "failed", **Then** an error notification appears with the failure reason
7. **Given** multiple notifications are active, **When** a new notification arrives, **Then** it stacks below existing notifications without overlapping

---

### User Story 5 - Reusable UI Component Library (Priority: P2)

A complete set of design system components exists for use across all future phases. These include: Button (primary, secondary, ghost variants), Card (standard and AI-accent), Badge (status labels with semantic colors), DataCell (monospaced numeric display with optional delta coloring), ProgressBar, Tooltip, Skeleton loader (shimmer animation), EmptyState (illustration + message + action), Toast (notification), and Modal dialog. All components respect the active theme and use only design tokens for styling.

**Why this priority**: Later phases will compose screens from these components. Having them pre-built ensures visual consistency and accelerates development of feature views.

**Independent Test**: Import any component into a test view — verify it renders correctly in both themes without additional styling. Verify all documented variants of each component render distinctly.

**Acceptance Scenarios**:

1. **Given** a developer needs a primary action button, **When** they import and use the Button component with the primary variant, **Then** it renders with the brand red color, correct padding, and hover/active states
2. **Given** a developer needs to display AI-generated content, **When** they use the Card component with the AI variant, **Then** it renders with a cyan/blue left border accent distinguishing it from standard cards
3. **Given** a developer needs to show a lap time, **When** they use the DataCell component, **Then** the value renders in a monospaced font and optionally shows a positive (green) or negative (amber) delta indicator
4. **Given** data is loading, **When** a Skeleton component is rendered, **Then** it shows a placeholder with an animated shimmer effect matching the expected content dimensions
5. **Given** a section has no content, **When** an EmptyState component is rendered, **Then** it shows an illustrative icon, a descriptive message, and an optional call-to-action button
6. **Given** a destructive action needs confirmation, **When** a Modal is triggered, **Then** it appears as an overlay with a backdrop, title, content, and confirm/cancel buttons

---

### User Story 6 - Empty State Views for All Sections (Priority: P3)

Each of the five navigation sections shows a meaningful empty state when there is no content to display. Empty states include a relevant icon, a clear message explaining why the section is empty, and guidance on what the user should do next. These are placeholder views that will be replaced by real content in later phases.

**Why this priority**: Users should never see a blank screen. Empty states communicate that the app is working correctly even when there is no data yet.

**Independent Test**: Navigate to each section with no data — verify each shows its unique empty state with a relevant message and suggestion.

**Acceptance Scenarios**:

1. **Given** no sessions exist, **When** the user navigates to Sessions, **Then** an empty state appears saying "No sessions recorded yet" with guidance to record a session in Assetto Corsa
2. **Given** no session is selected, **When** the user navigates to Lap Analysis, **Then** an empty state appears saying "Select a session to analyze laps" with a suggestion to go to Sessions first
3. **Given** no session is selected, **When** the user navigates to Setup Compare, **Then** an empty state appears saying "Select a session to compare setups" with a suggestion to go to Sessions first
4. **Given** no session is selected, **When** the user navigates to Engineer, **Then** an empty state appears saying "Select a session to talk with your engineer" with a suggestion to go to Sessions first
5. **Given** the user navigates to Settings, **Then** a placeholder settings view appears (this section always has content — configuration options — but in Phase 7.1 shows a basic placeholder with theme switching)

---

### Edge Cases

- What happens when the backend process crashes mid-session? The app detects the health endpoint becoming unreachable and shows an error overlay with a restart option, without losing the user's current navigation state.
- What happens when the WebSocket connection drops? The notification system reconnects automatically with exponential backoff (max 3 retries). If reconnection fails, an error notification informs the user that live updates are unavailable.
- What happens when the user resizes the window to a very small size? The sidebar collapses to icon-only mode below a minimum width threshold. Content area maintains a minimum usable width.
- What happens when the theme preference cannot be saved to the backend? The theme change applies in-memory immediately, and a warning notification informs the user that the preference could not be saved and may not persist after restart.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST launch a backend sidecar process on startup and bind it to `127.0.0.1:57832`
- **FR-002**: The application MUST poll the backend health endpoint at 500ms intervals (max 30 retries) before displaying the main interface
- **FR-003**: The application MUST display a splash/loading screen during the health-check polling period showing the app name and an animated progress indicator
- **FR-004**: The application MUST display an error state with a "Retry" button if the backend does not respond within 15 seconds
- **FR-005**: The application MUST signal the backend to shut down and terminate the sidecar process when the user closes the app
- **FR-006**: The application MUST provide two color themes: "Night Grid" (dark, default) and "Garage Floor" (light)
- **FR-007**: All color values MUST be defined as design tokens; hardcoded color values in component files are forbidden
- **FR-008**: Theme switching MUST update all visible elements immediately without a page reload
- **FR-009**: The selected theme MUST persist across app restarts via the backend configuration
- **FR-010**: The application MUST display a persistent left sidebar with navigation items: Sessions, Lap Analysis, Setup Compare, Engineer, Settings
- **FR-011**: The sidebar MUST indicate the currently active section with a visual highlight
- **FR-012**: The sidebar MUST visually distinguish session-dependent sections (Lap Analysis, Setup Compare, Engineer) when no session is selected
- **FR-013**: The application MUST use a monospaced font for all numeric data displays (lap times, speeds, temperatures, setup values, deltas)
- **FR-014**: The application MUST provide a toast notification system with four types: info, success, warning, error
- **FR-015**: Non-error notifications MUST auto-dismiss after 5 seconds; error notifications MUST persist until manually dismissed
- **FR-016**: The notification system MUST integrate with WebSocket job tracking to display job completion/failure automatically
- **FR-017**: The application MUST provide the following reusable components: Button (primary, secondary, ghost), Card (standard, AI-accent), Badge (semantic status colors), DataCell (monospaced numeric with optional delta coloring), ProgressBar, Tooltip, Skeleton (shimmer animation), EmptyState (icon + message + optional action), Toast, Modal
- **FR-018**: Every navigation section MUST show a meaningful empty state when no content is available — never a blank screen
- **FR-019**: The application MUST manage server/API state separately from UI state, with a clear distinction between server cache, global UI state, and component-local state
- **FR-020**: The application MUST NOT use browser persistent storage mechanisms; all state is in-memory and rehydrated from the backend on launch
- **FR-021**: The application MUST build with zero type errors under strict type checking
- **FR-022**: The WebSocket connection MUST reconnect automatically with exponential backoff (max 3 retries) when the connection drops

### Key Entities

- **Theme**: A named color scheme ("Night Grid" or "Garage Floor") defining all design token values for the application's visual appearance
- **Navigation Section**: One of five app areas (Sessions, Lap Analysis, Setup Compare, Engineer, Settings) accessible from the sidebar, each with a label, icon, route, and session-dependency flag
- **Notification (Toast)**: A transient message with a type (info, success, warning, error), content text, auto-dismiss behavior, and optional link to a related resource
- **Design Token**: A named variable defining a single visual attribute (color, spacing, font) used consistently across all components and themes
- **Job Status Update**: A message from the backend indicating a background job's current state (queued, running, completed, failed) with optional progress and result data

## Assumptions

- The backend already exposes a health check endpoint, a shutdown endpoint, and a WebSocket endpoint for job streaming — all implemented in Phase 6
- The backend configuration endpoint supports storing arbitrary user preferences (such as theme selection) via the existing config model
- JetBrains Mono is freely available (open-source font by JetBrains) and can be bundled with the application
- The app targets Windows as the primary platform (consistent with Assetto Corsa being Windows-only)
- The minimum supported screen resolution is 1280x720; responsive behavior below that is best-effort
- The sidebar logo in Phase 7.1 is a text-based placeholder ("AC RE" or similar); a full logo asset is not required until later phases

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The app transitions from splash screen to main interface within 5 seconds when the backend is healthy (typical case under 3 seconds)
- **SC-002**: When the backend is unavailable, the user sees a clear error state with a retry option within 15 seconds — the app never crashes or shows a blank screen
- **SC-003**: All five navigation sections are reachable from the sidebar and each displays its designated empty state when no content exists
- **SC-004**: Switching between dark and light themes updates every visible element instantly; the preference persists across app restarts
- **SC-005**: All 10 base UI components (Button, Card, Badge, DataCell, ProgressBar, Tooltip, Skeleton, EmptyState, Toast, Modal) render correctly in both themes with all documented variants
- **SC-006**: Numeric data values (lap times, temperatures, setup parameters) always appear in a monospaced font, visually aligned when stacked
- **SC-007**: Background job completions and failures trigger automatic notifications via WebSocket integration
- **SC-008**: A developer can import and use any design system component in a new screen without writing additional CSS or defining new color values
- **SC-009**: The app builds with zero type errors under strict mode
- **SC-010**: The app closes cleanly — backend sidecar process is terminated and no orphan processes remain
