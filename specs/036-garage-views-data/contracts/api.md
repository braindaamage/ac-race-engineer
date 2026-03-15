# API Contracts: Garage Views Data Population

**Branch**: `036-garage-views-data` | **Date**: 2026-03-15

## New Endpoints

### GET /sessions/grouped/cars

Returns all cars that have session data, with aggregated statistics and AC metadata.

**Response** `200 OK`:
```json
{
  "cars": [
    {
      "car_name": "ks_ferrari_488_gt3",
      "display_name": "Ferrari 488 GT3",
      "brand": "Ferrari",
      "car_class": "GT3",
      "badge_url": "/cars/ks_ferrari_488_gt3/badge",
      "track_count": 4,
      "session_count": 12,
      "last_session_date": "2026-03-15T14:30:00"
    },
    {
      "car_name": "some_modded_car",
      "display_name": "some modded car",
      "brand": "",
      "car_class": "",
      "badge_url": null,
      "track_count": 1,
      "session_count": 2,
      "last_session_date": "2026-03-10T09:00:00"
    }
  ]
}
```

**Notes**:
- Cars ordered by `last_session_date` DESC (most recent first)
- `badge_url` is null when the badge image file does not exist
- `display_name` falls back to formatted car_name (strip known prefixes, replace underscores with spaces) when ui_car.json is missing
- If AC install path is not configured, all metadata fields use fallback values

---

### GET /sessions/grouped/cars/{car_name}/tracks

Returns all tracks driven with a specific car, with aggregated statistics and AC metadata. Also includes car info for the header section.

**Path Parameters**:
- `car_name` (string, required): Car folder identifier

**Response** `200 OK`:
```json
{
  "car_name": "ks_ferrari_488_gt3",
  "car_display_name": "Ferrari 488 GT3",
  "car_brand": "Ferrari",
  "car_class": "GT3",
  "badge_url": "/cars/ks_ferrari_488_gt3/badge",
  "track_count": 4,
  "session_count": 12,
  "last_session_date": "2026-03-15T14:30:00",
  "tracks": [
    {
      "track_name": "ks_nurburgring",
      "track_config": "gp",
      "display_name": "Nürburgring - GP",
      "country": "Germany",
      "length_m": 5137.0,
      "preview_url": "/tracks/ks_nurburgring/preview?config=gp",
      "session_count": 3,
      "best_lap_time": 102.35,
      "last_session_date": "2026-03-15T14:30:00"
    },
    {
      "track_name": "ks_monza",
      "track_config": "",
      "display_name": "Autodromo Nazionale Monza",
      "country": "Italy",
      "length_m": 5793.0,
      "preview_url": "/tracks/ks_monza/preview",
      "session_count": 2,
      "best_lap_time": null,
      "last_session_date": "2026-03-12T18:00:00"
    }
  ]
}
```

**Response** `200 OK` (car has no sessions):
```json
{
  "car_name": "unknown_car",
  "car_display_name": "unknown car",
  "car_brand": "",
  "car_class": "",
  "badge_url": null,
  "track_count": 0,
  "session_count": 0,
  "last_session_date": "",
  "tracks": []
}
```

**Notes**:
- Tracks ordered by `last_session_date` DESC
- `best_lap_time` is null when no valid lap times exist
- `preview_url` includes `?config=` query param only when track_config is non-empty
- `preview_url` is null when the preview image file does not exist
- If the car has no sessions at all, returns empty tracks list with zeroed stats (not 404)

---

### GET /cars/{car_name}/badge

Serves the car badge image file from the AC install directory.

**Path Parameters**:
- `car_name` (string, required): Car folder identifier

**Response** `200 OK`:
- Content-Type: `image/png`
- Cache-Control: `max-age=86400`
- Body: Raw image bytes

**Response** `404 Not Found`:
```json
{
  "detail": "Badge not found for car: ks_ferrari_488_gt3"
}
```

**Notes**:
- File path: `{ac_cars_path}/{car_name}/ui/badge.png`
- Returns 404 if AC install path not configured, car folder doesn't exist, or badge.png is missing
- Path traversal protection: car_name must not contain `/`, `\`, or `..`

---

### GET /tracks/{track_name}/preview

Serves the track preview image file from the AC install directory.

**Query Parameters**:
- `config` (string, optional, default `""`): Track layout identifier

**Path Parameters**:
- `track_name` (string, required): Track folder identifier

**Response** `200 OK`:
- Content-Type: `image/png` (or detected type)
- Cache-Control: `max-age=86400`
- Body: Raw image bytes

**Response** `404 Not Found`:
```json
{
  "detail": "Preview not found for track: ks_nurburgring (config: gp)"
}
```

**Notes**:
- File path (no config): `{ac_tracks_path}/{track_name}/ui/preview.png`
- File path (with config): `{ac_tracks_path}/{track_name}/ui/layout_{config}/preview.png`
- Path traversal protection on both track_name and config

---

## Modified Endpoints

### GET /sessions

**New Query Parameters** (in addition to existing `car`):
- `track` (string, optional): Filter by track folder identifier
- `track_config` (string, optional): Filter by track layout. Only applied when `track` is also provided.

**Response**: Same as before, but `SessionRecord` objects now include `track_config` field:
```json
{
  "sessions": [
    {
      "session_id": "...",
      "car": "ks_ferrari_488_gt3",
      "track": "ks_nurburgring",
      "track_config": "gp",
      "session_date": "2026-03-15T14:30:00",
      "lap_count": 15,
      "best_lap_time": 102.35,
      "state": "analyzed",
      "session_type": "practice",
      "csv_path": "...",
      "meta_path": "..."
    }
  ]
}
```

**Notes**:
- Existing `?car=` filter continues to work unchanged
- `track_config` defaults to empty string for sessions that predate the feature
- When `track` is provided without `track_config`, returns all sessions for that track regardless of layout
