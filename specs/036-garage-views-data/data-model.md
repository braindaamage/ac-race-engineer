# Data Model: Garage Views Data Population

**Branch**: `036-garage-views-data` | **Date**: 2026-03-15

## Overview

This feature adds one new column to the existing `sessions` table, two new aggregation query functions, a new AC metadata reader module, and corresponding API response models. No new tables are created.

## Database Schema Changes

### sessions table — new column

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `track_config` | TEXT NOT NULL | `''` | Track layout identifier from session metadata. Empty string for single-layout tracks. |

**Migration**: `ALTER TABLE sessions ADD COLUMN track_config TEXT NOT NULL DEFAULT ''`

### New indexes

| Index Name | Columns | Purpose |
|------------|---------|---------|
| `idx_sessions_car` | `(car)` | Optimizes car-only filter on list_sessions and GROUP BY car |
| `idx_sessions_car_track` | `(car, track, track_config)` | Covers track listing and session filtering by car+track+config |

## Backend Models

### SessionRecord (modified)

Existing Pydantic model in `storage/models.py`. Add one field:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `track_config` | `str` | `""` | Track layout identifier |

### CarStats (new, storage return type)

Returned by `list_car_stats()`. Plain dict, not a Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| `car` | `str` | Car folder identifier |
| `track_count` | `int` | Count of distinct track+config combinations |
| `session_count` | `int` | Total sessions for this car |
| `last_session_date` | `str` | ISO date of most recent session |

### TrackStats (new, storage return type)

Returned by `list_track_stats()`. Plain dict, not a Pydantic model.

| Field | Type | Description |
|-------|------|-------------|
| `track` | `str` | Track folder identifier |
| `track_config` | `str` | Layout identifier (empty string if none) |
| `session_count` | `int` | Sessions at this track+config |
| `best_lap_time` | `float | None` | Best lap time in seconds across all sessions |
| `last_session_date` | `str` | ISO date of most recent session |

### CarInfo (new, ac_assets return type)

Returned by `read_car_info()`. Pydantic model in `resolver/ac_assets.py`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `display_name` | `str` | *(required)* | Human-readable name from ui_car.json or formatted fallback |
| `brand` | `str` | `""` | Manufacturer name |
| `car_class` | `str` | `""` | Class (GT3, street, etc.) |

### TrackInfo (new, ac_assets return type)

Returned by `read_track_info()`. Pydantic model in `resolver/ac_assets.py`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `display_name` | `str` | *(required)* | Human-readable name from ui_track.json or formatted fallback |
| `country` | `str` | `""` | Country name |
| `length_m` | `float | None` | `None` | Track length in meters |

## API Response Models

### CarStatsResponse (new, in api/routes/sessions.py)

Pydantic model for a single car in the grouped response.

| Field | Type | Description |
|-------|------|-------------|
| `car_name` | `str` | Car folder identifier |
| `display_name` | `str` | From CarInfo |
| `brand` | `str` | From CarInfo |
| `car_class` | `str` | From CarInfo |
| `badge_url` | `str | None` | Relative URL `/cars/{car_name}/badge` or null if no image |
| `track_count` | `int` | From CarStats |
| `session_count` | `int` | From CarStats |
| `last_session_date` | `str` | From CarStats |

### CarStatsListResponse (new)

| Field | Type | Description |
|-------|------|-------------|
| `cars` | `list[CarStatsResponse]` | All cars with session data |

### TrackStatsResponse (new, in api/routes/sessions.py)

| Field | Type | Description |
|-------|------|-------------|
| `track_name` | `str` | Track folder identifier |
| `track_config` | `str` | Layout identifier |
| `display_name` | `str` | From TrackInfo |
| `country` | `str` | From TrackInfo |
| `length_m` | `float | None` | From TrackInfo |
| `preview_url` | `str | None` | Relative URL or null |
| `session_count` | `int` | From TrackStats |
| `best_lap_time` | `float | None` | From TrackStats |
| `last_session_date` | `str` | From TrackStats |

### TrackStatsListResponse (new)

| Field | Type | Description |
|-------|------|-------------|
| `car_name` | `str` | Car identifier for context |
| `car_display_name` | `str` | Car display name for header |
| `car_brand` | `str` | Car brand for header |
| `car_class` | `str` | Car class for header |
| `badge_url` | `str | None` | Car badge URL for header |
| `track_count` | `int` | Total track count for this car |
| `session_count` | `int` | Total session count for this car |
| `last_session_date` | `str` | Last session date for this car |
| `tracks` | `list[TrackStatsResponse]` | Tracks for this car |

## Frontend Types

### CarStatsRecord (new, in lib/types.ts)

```typescript
interface CarStatsRecord {
  car_name: string;
  display_name: string;
  brand: string;
  car_class: string;
  badge_url: string | null;
  track_count: number;
  session_count: number;
  last_session_date: string;
}

interface CarStatsListResponse {
  cars: CarStatsRecord[];
}
```

### TrackStatsRecord (new, in lib/types.ts)

```typescript
interface TrackStatsRecord {
  track_name: string;
  track_config: string;
  display_name: string;
  country: string;
  length_m: number | null;
  preview_url: string | null;
  session_count: number;
  best_lap_time: number | null;
  last_session_date: string;
}

interface TrackStatsListResponse {
  car_name: string;
  car_display_name: string;
  car_brand: string;
  car_class: string;
  badge_url: string | null;
  track_count: number;
  session_count: number;
  last_session_date: string;
  tracks: TrackStatsRecord[];
}
```

### SessionRecord (modified)

Add field:

```typescript
track_config: string;  // added
```

## Entity Relationships

```
sessions table (existing + track_config)
    ↓ GROUP BY car
CarStats (aggregated)
    + CarInfo (from AC files)
    = CarStatsResponse (API)

sessions table
    ↓ WHERE car = ? GROUP BY track, track_config
TrackStats (aggregated)
    + TrackInfo (from AC files)
    = TrackStatsResponse (API)
```

## Validation Rules

- `car_name`: Non-empty string, no path separators (`/`, `\`, `..`)
- `track_name`: Non-empty string, no path separators
- `track_config`: String, may be empty. No path separators when non-empty.
- Image paths: Constructed from validated identifiers, never from raw user input. Path traversal protection via identifier validation.
- `length_m` parsing: Strip non-numeric suffix, attempt float conversion, default to None on failure.

## State Transitions

No state transitions introduced. Sessions continue using the existing state machine (discovered → parsed → analyzed → engineered).
