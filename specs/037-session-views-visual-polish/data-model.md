# Data Model: Session Views Visual Polish

**Branch**: `037-session-views-visual-polish` | **Date**: 2026-03-15

## Overview

This feature adds no new database tables, columns, or backend models. It introduces one new frontend component (SessionHeader) that derives all its data from existing API responses and query caches. No new API endpoints or response types are created.

## Database Schema Changes

None.

## Backend Models

No changes.

## API Response Models

No changes. The SessionHeader component consumes existing response types:

- **SessionRecord** (existing in `lib/types.ts`): Provides `car`, `track`, `track_config`, `session_date`, `lap_count`, `best_lap_time`, `state` for the header's session statistics.
- **TrackStatsListResponse** (existing, from Phase 14.2): Provides `car_display_name`, `car_brand`, `car_class`, `badge_url` at the top level, and per-track `display_name`, `preview_url` for the matching track entry.

## Frontend Types

No new TypeScript types or interfaces are needed. The SessionHeader component uses existing types from `lib/types.ts`:

| Type | Source | Used For |
|------|--------|----------|
| `SessionRecord` | `lib/types.ts` | Session metadata (car, track, date, laps, best time, state) |
| `TrackStatsListResponse` | `lib/types.ts` | Car display name, badge URL, track display names, preview URLs |

## New CSS Tokens

One potential addition to `tokens.css` (only if needed for the user message timestamp fix):

| Token | Dark Value | Light Value | Purpose |
|-------|-----------|-------------|---------|
| *(none expected)* | — | — | The `color-mix()` CSS function will be used instead of a new token for semi-transparent text on brand backgrounds |

## Component Data Flow

```
SessionLayout
  ├─ useParams() → sessionId
  ├─ useSessions() → find SessionRecord by session_id
  ├─ useCarTracks(session.car) → car metadata + track list
  │
  ├─ <SessionHeader>
  │    Props: session, carDisplayName, carBadgeUrl, trackDisplayName, trackPreviewUrl
  │    Renders: car badge + name, track preview + name, date, laps, best time, status badge
  │
  └─ <Outlet />  (child routes: AnalysisView, CompareView, EngineerView)
```

## Validation Rules

No new validation rules. All data displayed in the SessionHeader is read-only and comes from validated API responses.

## State Transitions

No new state transitions. The session `state` field displayed in the header badge follows the existing state machine:

```
discovered → parsed → analyzed → engineered
```

The header displays this as a Badge component with variant mapping:
- `discovered` / `parsed` → neutral badge
- `analyzed` → info badge
- `engineered` → success badge
