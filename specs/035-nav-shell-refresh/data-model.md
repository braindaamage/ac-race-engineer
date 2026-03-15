# Data Model: Navigation Shell & Visual Refresh

**Branch**: `035-nav-shell-refresh` | **Date**: 2026-03-15

## Overview

This feature introduces no new persistent data or backend entities. All new "entities" are frontend-only runtime constructs derived from URL routes and existing API data. No database migrations, no new API endpoints, no new Pydantic models.

## Frontend Route Model

### NavigationLevel (enum)

Represents the depth in the navigation hierarchy.

| Value | Route Pattern | Description |
|-------|--------------|-------------|
| `GARAGE` | `/garage` | Car listing (home) |
| `TRACKS` | `/garage/:carId/tracks` | Tracks for a car |
| `SESSIONS` | `/garage/:carId/tracks/:trackId/sessions` | Sessions for car+track |
| `SESSION_DETAIL` | `/session/:sessionId/:tab` | Session work tabs |
| `SETTINGS` | `/settings` | Global settings |

### RouteParams (derived from URL)

| Field | Type | Present At | Source |
|-------|------|-----------|--------|
| `carId` | `string` | TRACKS, SESSIONS | URL param `:carId` |
| `trackId` | `string` | SESSIONS | URL param `:trackId` |
| `sessionId` | `string` | SESSION_DETAIL | URL param `:sessionId` |
| `tab` | `"laps" \| "setup" \| "engineer"` | SESSION_DETAIL | URL param `:tab` (via path) |

### BreadcrumbSegment

| Field | Type | Description |
|-------|------|-------------|
| `label` | `string` | Display text (formatted identifier or icon) |
| `to` | `string` | Route path for navigation |
| `isCurrent` | `boolean` | True for the last segment (not clickable) |

**Generation rule**: Built from current route match. Each ancestor level produces one segment. Home is always first.

### SessionTab

| Value | Label | Route Suffix | View Component |
|-------|-------|-------------|----------------|
| `laps` | Lap Analysis | `/session/:id/laps` | AnalysisView |
| `setup` | Setup Compare | `/session/:id/setup` | CompareView |
| `engineer` | Engineer | `/session/:id/engineer` | EngineerView |

### Contextual Tab Configuration

The tab bar content changes based on navigation level:

| Navigation Level | Tab Items |
|-----------------|-----------|
| GARAGE | Global nav tabs: Garage Home (active), Tracks, Sessions, Settings |
| TRACKS | Global nav tabs: Garage Home, Tracks (active), Sessions, Settings |
| SESSIONS | Global nav tabs: Garage Home, Tracks, Sessions (active), Settings |
| SESSION_DETAIL | Work tabs: Lap Analysis, Setup Compare, Engineer |
| SETTINGS | Global nav tabs: Garage Home, Tracks, Sessions, Settings (active) |

## Existing Entities (Unchanged)

These existing types from `frontend/src/lib/types.ts` are consumed by the navigation shell but not modified:

- **SessionRecord**: Provides `session_id`, `car_name`, `track_name`, `timestamp` — used for breadcrumb label resolution at session detail level.
- **UISessionState**: Existing enum (New, Processing, Ready, Error) — used by SessionsView, unchanged.

## State Store Changes

### Removed: uiStore

| Removed Field | Replaced By |
|---------------|-------------|
| `activeSection: string` | Router location (current route determines active view) |
| `sidebarCollapsed: boolean` | N/A (sidebar deleted) |
| `setActiveSection()` | `useNavigate()` from react-router-dom |
| `toggleSidebar()` | N/A (sidebar deleted) |

### Removed: sessionStore

| Removed Field | Replaced By |
|---------------|-------------|
| `selectedSessionId: string \| null` | `useParams().sessionId` from route |
| `selectSession(id)` | `navigate(\`/session/${id}/laps\`)` |
| `clearSession()` | `navigate(backToSessionsList)` |

## Validation Rules

- `carId`: Non-empty string, URL-safe (existing car identifiers from API are already safe)
- `trackId`: Non-empty string, URL-safe (existing track identifiers from API are already safe)
- `sessionId`: Non-empty string matching existing session IDs from API
- `tab`: Must be one of `"laps"`, `"setup"`, `"engineer"` — invalid values redirect to `"laps"`
- Invalid routes: Show empty state or redirect to `/garage`
