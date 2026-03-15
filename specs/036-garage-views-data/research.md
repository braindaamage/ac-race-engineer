# Research: Garage Views Data Population

**Branch**: `036-garage-views-data` | **Date**: 2026-03-15

## R1: Assetto Corsa Car Metadata File Format

**Decision**: Parse `content/cars/{car_id}/ui/ui_car.json` as JSON with fields: `name` (display name), `brand`, `class`, `tags` (array, unused). Badge image at `content/cars/{car_id}/ui/badge.png`.

**Rationale**: AC's standard file format is well-documented and consistent across official cars. The JSON file uses UTF-8 encoding with optional BOM. The `class` field is a direct string (e.g., "GT3", "street"), not nested.

**Alternatives considered**:
- Parsing `data.acd` archives for metadata: Rejected — the resolver already handles ACD for setup parameters, but ui_car.json is plaintext and always available alongside the ACD file. No need for decryption.
- Reading `brand` from directory naming conventions: Rejected — unreliable for mods.

**Key details**:
- ui_car.json may contain non-standard characters (accented names, Japanese text for some mods)
- Some mods omit `brand` or `class` fields entirely — must handle missing keys
- Badge images are typically 128×128 PNG but some mods use different sizes or JPG
- The `tags` array contains strings like "#gt3", "#race" — not useful for our purposes; `class` field is the correct source for car classification

## R2: Assetto Corsa Track Metadata File Format

**Decision**: Parse track metadata from `content/tracks/{track_id}/ui/ui_track.json` for single-layout tracks, or `content/tracks/{track_id}/ui/layout_{config}/ui_track.json` for multi-layout tracks. Fields: `name` (display name), `country`, `length` (string with unit, e.g., "5793 m"), `city`. Preview image at `preview.png` in the same directory as ui_track.json.

**Rationale**: AC uses the `layout_` prefix convention for track layout subdirectories. The `length` field is a string that needs parsing (strip unit suffix, convert to float).

**Alternatives considered**:
- Using track_config="" to always read from base ui/ui_track.json: Incorrect — multi-layout tracks may have different names per layout (e.g., "Nürburgring - GP" vs "Nürburgring - Nordschleife").
- Serving track outlines instead of previews: Rejected — outline images are less recognizable for users. preview.png provides the visual experience seen in the prototypes.

**Key details**:
- `length` field is inconsistent: some tracks use "5793 m", others "5.793 km", some mods omit it entirely. Parse defensively.
- Multi-layout tracks: the base `ui/ui_track.json` describes the track overall; each `ui/layout_{config}/ui_track.json` describes the specific layout. We read the layout-specific file when track_config is non-empty.
- Preview images are typically wide landscape (e.g., 355×200) — frontend should use object-fit: cover.

## R3: Database Migration Strategy for track_config

**Decision**: Add `track_config TEXT NOT NULL DEFAULT ''` column via ALTER TABLE in the existing migrations list. Add covering indexes for common query patterns.

**Rationale**: SQLite supports ALTER TABLE ADD COLUMN with defaults. Existing rows automatically get the default empty string. This is backwards-compatible — no data migration needed.

**Alternatives considered**:
- Creating a separate track_layouts table: Rejected — over-normalized for this use case. track_config is a simple attribute of the session, not a separate entity.
- Using NULL instead of empty string: Rejected — empty string is more ergonomic for GROUP BY queries and avoids NULL comparison pitfalls.

**Key details**:
- Migration SQL: `ALTER TABLE sessions ADD COLUMN track_config TEXT NOT NULL DEFAULT ''`
- Index: `CREATE INDEX IF NOT EXISTS idx_sessions_car_track ON sessions(car, track, track_config)` — covers car listing (GROUP BY car), track listing (WHERE car = ? GROUP BY track, track_config), and session filtering (WHERE car = ? AND track = ? AND track_config = ?)
- Separate car index: `CREATE INDEX IF NOT EXISTS idx_sessions_car ON sessions(car)` — optimizes the common car-only filter on list_sessions

## R4: Image Serving Strategy

**Decision**: Serve images via dedicated FastAPI FileResponse endpoints. Return 404 when image doesn't exist. Frontend uses `<img>` with `onError` fallback to placeholder icon.

**Rationale**: FileResponse streams files efficiently without loading into memory. The AC install directory is local, so latency is negligible. 404 is the standard HTTP response for missing resources, and the frontend handles it gracefully via the img onError event.

**Alternatives considered**:
- Base64 encoding images in JSON responses: Rejected — increases payload size by ~33%, complicates caching, and breaks browser image caching.
- Proxying through a catch-all static file server: Rejected — exposes arbitrary file system access. Dedicated endpoints with path validation are safer.
- Returning a default placeholder image from the backend: Rejected — the frontend already has design system components for placeholder states; handling it client-side is simpler and avoids returning misleading 200 responses.

**Key details**:
- Badge endpoint: `GET /cars/{car_name}/badge` → FileResponse with `media_type="image/png"`
- Preview endpoint: `GET /tracks/{track_name}/preview?config=` → FileResponse with detected media type
- Path traversal protection: validate car_name and track_name contain no path separators before constructing file paths
- Cache-Control header: `max-age=86400` (images don't change frequently)

## R5: Aggregation Query Patterns

**Decision**: Use SQL GROUP BY queries in storage/sessions.py returning lists of dicts. The API layer enriches these with AC metadata from the resolver/ac_assets module.

**Rationale**: SQL aggregation is efficient and happens at the storage layer (Principle VIII). The API layer merges session statistics with AC metadata — this is composition, not business logic, so it's appropriate for the route layer.

**Alternatives considered**:
- Client-side aggregation from the full sessions list: Rejected — wastes bandwidth and pushes aggregation logic into the frontend (violates Principle IX).
- Aggregation in a new ac_engineer module: Considered but rejected — the aggregation queries are simple SQL GROUP BY operations, not business logic. They belong in the storage layer alongside existing session CRUD.

**Key details**:
- `list_car_stats(db_path)`: SELECT car, COUNT(DISTINCT track || char(0) || track_config) as track_count, COUNT(*) as session_count, MAX(session_date) as last_session_date FROM sessions GROUP BY car ORDER BY last_session_date DESC
  - Note: `char(0)` (null byte) is used as the separator instead of a printable character like `|` because the separator could theoretically appear in modded track folder names. Null bytes cannot appear in filesystem names.
- `list_track_stats(db_path, car)`: SELECT track, track_config, COUNT(*) as session_count, MIN(best_lap_time) as best_lap_time, MAX(session_date) as last_session_date FROM sessions WHERE car = ? GROUP BY track, track_config ORDER BY last_session_date DESC
- Both return lists of dicts (not Pydantic models) — the API layer creates response models that merge stats with metadata

## R6: URL Encoding for track_config

**Decision**: Encode track_config as a query parameter `?config=` on the sessions route. The route remains `/garage/:carId/tracks/:trackId/sessions?config=gp`. Empty config (default layout) omits the query parameter.

**Rationale**: track_config is a filter/modifier, not a hierarchical segment. Query parameters are the correct HTTP semantic for filters. This avoids adding a 4th path segment and keeps the URL structure clean.

**Alternatives considered**:
- Encoding as `trackId~config` in the path: Rejected — introduces a custom encoding convention that's non-standard and brittle.
- Adding a 4th path segment `/garage/:carId/tracks/:trackId/:config/sessions`: Rejected — makes the URL deeper and config="" would require a special sentinel value.
- Encoding in the trackId itself (e.g., `ks_nurburgring--gp`): Rejected — conflates two distinct identifiers and could collide with actual track names containing `--`.

**Key details**:
- Frontend reads via `useSearchParams()`: `const [searchParams] = useSearchParams(); const config = searchParams.get("config") ?? ""`
- Navigation: `navigate(\`/garage/${carId}/tracks/${trackId}/sessions${config ? \`?config=${config}\` : ""}\`)`
- Breadcrumb and TabBar must also read searchParams for the config value when constructing links
