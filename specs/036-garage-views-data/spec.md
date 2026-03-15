# Feature Specification: Garage Views Data Population

**Feature Branch**: `036-garage-views-data`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Phase 14.2 — Populate Garage Home and Car Tracks placeholder views with real data from sessions and Assetto Corsa asset files. Add track layout persistence, aggregation queries, and AC metadata/image serving.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Cars in Garage (Priority: P1)

A driver opens the application and sees their garage — a grid of car cards, one per distinct car that has at least one recorded session. Each card shows the car's badge image (from the sim's assets), its display name, brand and class, the number of tracks driven, total session count, and how long ago the last session was. The driver can type in a search box or use a class filter to narrow the list. Clicking a car card navigates to that car's tracks view.

**Why this priority**: This is the entry point of the entire car-centric navigation. Without real data on Garage Home, the navigation shell delivers no value — the user sees a placeholder instead of their cars.

**Independent Test**: Can be fully tested by having session data for 2+ cars, loading Garage Home, confirming all cards appear with correct stats, searching/filtering, and clicking through to the tracks view.

**Acceptance Scenarios**:

1. **Given** the application has sessions for 3 different cars, **When** the Garage Home view loads, **Then** 3 car cards are displayed, each showing the car's display name (from AC metadata) or the raw folder name if metadata is unavailable.
2. **Given** a car has sessions on 4 distinct tracks totaling 12 sessions, **When** its card is displayed, **Then** the card shows "4 tracks" and "12 sessions" with the time since the most recent session.
3. **Given** the car's badge image exists in the AC install directory, **When** the card is rendered, **Then** the badge image is displayed on the card.
4. **Given** the car has no badge image (e.g., a mod without assets), **When** the card is rendered, **Then** a placeholder icon is shown instead — no broken image.
5. **Given** 10 cars are listed, **When** the driver types "ferrari" in the search box, **Then** only cars whose display name, brand, or class contain "ferrari" (case-insensitive) are shown.
6. **Given** the driver clicks a car card, **When** the navigation occurs, **Then** the Car Tracks view for that car is displayed and the URL updates to include the car identifier.
7. **Given** no sessions exist at all, **When** the Garage Home loads, **Then** an empty state is shown with guidance explaining that the user needs to record sessions in Assetto Corsa.

---

### User Story 2 - Browse Tracks for a Car (Priority: P1)

A driver selects a car from the garage and sees a grid of track cards for every track they have driven with that car. A header section displays the car's information (badge image, display name, aggregate stats). Each track card shows the track preview image, display name (with layout suffix when applicable), number of sessions, best lap time across all sessions, and time since the last session. Clicking a track card navigates to the sessions list for that car+track combination.

**Why this priority**: This is the second level of the car-centric navigation. Combined with User Story 1, it completes the drill-down experience from car to track to sessions.

**Independent Test**: Can be fully tested by selecting a car that has sessions on 3+ tracks, confirming all track cards appear with correct stats and images, and clicking through to the sessions view.

**Acceptance Scenarios**:

1. **Given** a car has sessions on 3 tracks (including one track with 2 different layouts), **When** the Car Tracks view loads, **Then** 4 track cards are displayed (one per track+layout combination), each showing the track's display name from AC metadata or the raw folder name as fallback.
2. **Given** a track has a layout-specific configuration (e.g., Nurburgring GP vs Nordschleife), **When** the track card is displayed, **Then** the layout name is shown as a suffix or subtitle on the card.
3. **Given** a track card represents 5 sessions with a best lap of 1:42.350, **When** the card is rendered, **Then** the session count, best lap time (formatted as mm:ss.SSS), and time since last session are visible.
4. **Given** the track's preview image exists in the AC install directory, **When** the card is rendered, **Then** the preview image is displayed.
5. **Given** the driver clicks a track card, **When** the navigation occurs, **Then** the Sessions view is displayed filtered to that car+track+layout combination.
6. **Given** the car header section at the top of the view, **When** it renders, **Then** it shows the car's badge image, display name, brand/class, and aggregate stats (total sessions, total tracks, last session date).

---

### User Story 3 - Track Layout Distinction in Session Data (Priority: P1)

When sessions are recorded or synced, the track layout information from the session metadata is persisted alongside the track identifier. All views that group or filter by track correctly distinguish between different layouts of the same physical circuit.

**Why this priority**: Without this, sessions at different layouts of the same track (e.g., Nurburgring GP and Nordschleife) are incorrectly grouped together. This data integrity fix is foundational for correct aggregation.

**Independent Test**: Can be tested by syncing sessions from different layouts of the same track and confirming they appear as separate entries in the tracks view.

**Acceptance Scenarios**:

1. **Given** two sessions exist at "ks_nurburgring" — one with layout "gp" and one with layout "nordschleife", **When** the Car Tracks view for that car loads, **Then** two separate track cards appear: "Nurburgring - GP" and "Nurburgring - Nordschleife".
2. **Given** a session's metadata contains a `track_config` field, **When** the session is saved to the database, **Then** the track layout value is persisted in the session record.
3. **Given** existing sessions that were saved before track layout support, **When** they are displayed, **Then** they are treated as having no layout (empty string) and grouped together under the base track name.
4. **Given** the sessions list is filtered by track, **When** the filter includes a layout, **Then** only sessions matching both the track identifier and the layout are shown.

---

### User Story 4 - Human-Readable Names in Breadcrumb (Priority: P2)

As the driver navigates the hierarchy, the breadcrumb shows human-readable display names (from AC metadata) for the car and track segments, instead of raw folder identifiers like "ks_mazda_mx5_cup".

**Why this priority**: Improves usability but does not block core data display. The application is functional with raw identifiers; display names are a polish improvement.

**Independent Test**: Can be tested by navigating to a session and checking that the breadcrumb shows "Mazda MX-5 Cup" instead of "ks_mazda_mx5_cup" for the car segment.

**Acceptance Scenarios**:

1. **Given** the user navigates to Car Tracks for "ks_ferrari_488_gt3", **When** the breadcrumb renders, **Then** it shows "Home / Ferrari 488 GT3" (display name from AC metadata).
2. **Given** the car has no AC metadata (e.g., a mod), **When** the breadcrumb renders, **Then** it shows the formatted raw identifier (e.g., "Home / ferrari 488 gt3" with vendor prefix stripped and underscores replaced).
3. **Given** the user navigates to Sessions for a specific track with layout, **When** the breadcrumb renders, **Then** the track segment shows the display name with layout suffix (e.g., "Nurburgring - GP").

---

### User Story 5 - Sessions View Contextual Header (Priority: P2)

When the driver navigates to the sessions list for a specific car+track, a header section at the top of the Sessions view shows contextual information: the car name and badge alongside the track name and preview image, with aggregate stats for that car+track combination.

**Why this priority**: Adds context to the existing sessions list but the list already works without it. This is an enhancement, not a core requirement.

**Independent Test**: Can be tested by navigating to a car+track sessions list and confirming the header section shows correct car and track information.

**Acceptance Scenarios**:

1. **Given** the user navigates to sessions for "Ferrari 488 GT3" at "Monza", **When** the Sessions view loads, **Then** a header section shows the car badge, car display name, track preview image, track display name, session count, and best lap time.
2. **Given** the car or track has no images available, **When** the header renders, **Then** placeholder icons are shown — no broken images.

---

### Edge Cases

- What happens when the AC install path is not configured or is invalid? All metadata reads return fallback values (raw identifiers, no images). The views still render using data from the sessions database.
- What happens when a car folder exists in sessions but not in the AC install directory? Display name falls back to the formatted raw identifier. Badge image shows a placeholder.
- What happens when a track has an empty `track_config` value? It is treated as the default/only layout. No layout suffix is shown on the display name.
- What happens when session sync discovers sessions that were saved before track layout support? Old sessions have NULL/empty track_config. They are grouped as if they have no layout and are still fully functional.
- What happens when the search box on Garage Home matches no cars? An empty state is shown indicating no results match the filter, with a way to clear the search.
- What happens when a car has sessions but all of them have been deleted? That car no longer appears in the garage (cars are derived from sessions, not from the AC install).

## Requirements *(mandatory)*

### Functional Requirements

**Data Layer**

- **FR-001**: The system MUST store the track layout identifier (`track_config` from session metadata) alongside the track identifier when a session is saved.
- **FR-002**: The system MUST provide a query that returns all distinct cars that have at least one session, with aggregated statistics per car: number of distinct tracks driven, total session count, and the date of the most recent session.
- **FR-003**: The system MUST provide a query that, given a car identifier, returns all distinct tracks (grouped by track identifier + track layout) for that car, with aggregated statistics per track: session count, best lap time across all sessions, and the date of the most recent session.
- **FR-004**: The existing session list query MUST support filtering by track identifier and track layout, in addition to the existing car filter.
- **FR-005**: Existing sessions that were saved before track layout support MUST remain functional and be treated as having an empty/null layout.

**AC Metadata Reading**

- **FR-006**: The system MUST read car metadata (display name, brand, class) from the Assetto Corsa install directory for a given car identifier.
- **FR-007**: The system MUST read track metadata (display name, country, length) from the Assetto Corsa install directory for a given track identifier and optional layout.
- **FR-008**: Every metadata read MUST fall back gracefully when files are missing — returning the raw identifier as the display name with empty values for other fields.
- **FR-009**: The system MUST serve car badge images from the AC install directory, returning a fallback response when the image does not exist.
- **FR-010**: The system MUST serve track preview images from the AC install directory (layout-specific when applicable), returning a fallback response when the image does not exist.

**Garage Home View**

- **FR-011**: The Garage Home view MUST display a grid of car cards, one per distinct car with session data.
- **FR-012**: Each car card MUST display: badge image (or placeholder), display name, brand and class, track count, session count, and time since last session.
- **FR-013**: The Garage Home view MUST provide a search/filter mechanism that filters cars by display name, brand, or class (case-insensitive).
- **FR-014**: When no sessions exist, the Garage Home view MUST show an empty state with guidance text.
- **FR-015**: Clicking a car card MUST navigate to the Car Tracks view for that car.

**Car Tracks View**

- **FR-016**: The Car Tracks view MUST display a header section with the car's badge image, display name, brand/class, and aggregate statistics.
- **FR-017**: The Car Tracks view MUST display a grid of track cards, one per distinct track+layout combination for the selected car.
- **FR-018**: Each track card MUST display: preview image (or placeholder), display name (with layout suffix if applicable), session count, best lap time (formatted as mm:ss.SSS), and time since last session.
- **FR-019**: Clicking a track card MUST navigate to the sessions list filtered by car + track + layout.

**Sessions View Enhancement**

- **FR-020**: The Sessions view MUST display a contextual header section showing car and track information when navigated from the car-centric hierarchy.
- **FR-021**: The breadcrumb MUST show human-readable display names (from AC metadata) for car and track segments, falling back to formatted raw identifiers.

### Key Entities

- **Car Summary**: Represents a distinct car with session data. Attributes: car identifier, display name, brand, class, badge image URL, track count, session count, last session date.
- **Track Summary**: Represents a distinct track+layout for a given car. Attributes: track identifier, track layout, display name, layout display name, preview image URL, session count, best lap time, last session date.
- **Car Metadata**: Information read from AC install files for a car. Attributes: display name, brand, class.
- **Track Metadata**: Information read from AC install files for a track. Attributes: display name, country, length (meters).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A driver with session data for multiple cars sees all their cars listed on Garage Home within 2 seconds of navigating to the view.
- **SC-002**: Aggregated statistics (track count, session count, last session) on each car card match the actual session data — zero discrepancies.
- **SC-003**: Track+layout combinations are correctly separated — sessions at different layouts of the same circuit never appear grouped together.
- **SC-004**: Cars and tracks with AC metadata files show their human-readable display names; cars and tracks without metadata show a usable formatted fallback — no raw folder identifiers with vendor prefixes displayed to the user.
- **SC-005**: All image references (car badges, track previews) either display the actual image from AC install or a clean placeholder — zero broken image indicators.
- **SC-006**: The search/filter on Garage Home correctly narrows results and shows an appropriate state when no results match.
- **SC-007**: Clicking through the full hierarchy (Garage Home → Car → Track → Sessions) produces correct, non-empty views at every level with matching data.
- **SC-008**: Existing sessions saved before track layout support continue to appear and function correctly in all views.

## Assumptions

- The AC install path is configured via the existing `ac_install_path` setting in the application config. If not configured, all metadata reads return fallback values.
- Car metadata files follow the standard Assetto Corsa structure: `content/cars/{car_id}/ui/ui_car.json` for metadata and `content/cars/{car_id}/ui/badge.png` for the badge image.
- Track metadata files follow the standard Assetto Corsa structure: `content/tracks/{track_id}/ui/ui_track.json` for single-layout tracks, or `content/tracks/{track_id}/ui/layout_{layout}/ui_track.json` for multi-layout tracks (note the `layout_` prefix in the directory name). Preview images are at `preview.png` in the same directory.
- The `track_config` field in session metadata is an empty string for single-layout tracks and a layout identifier (e.g., "gp", "nordschleife") for multi-layout tracks.
- Car metadata JSON files contain at minimum a `name` field (display name), and optionally `brand` and `class` fields. A separate `tags` array may also exist but is not used. Track metadata JSON files contain at minimum a `name` field and optionally `country` and `length` fields.
- Image files served from AC install are standard formats (PNG/JPG) suitable for display in a web view.
- The database migration adding the `track_config` column is backwards-compatible — existing rows get a default empty string value.
- The HTML prototypes (files 3, 4, 5) are the visual reference for card layout, grid spacing, and overall page structure.

## Out of Scope

- Reading car or track data from ACD encrypted archives (only plain-text metadata files and images).
- Adding new session metadata fields beyond track layout (e.g., weather, car skin).
- Editing or managing sessions from the garage views (these are read-only browsing views).
- Sorting or advanced filtering on the Car Tracks view (search/filter is only on Garage Home).
- Lazy-loading or pagination of car/track cards (the number of distinct cars and tracks is expected to be manageable — typically under 50).
- Changes to the navigation shell structure, header, breadcrumb mechanics, or tab bar from Phase 14.1.
- Changes to session detail views (Lap Analysis, Setup Compare, Engineer).
