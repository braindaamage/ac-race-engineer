# Research: Session Discovery (Phase 6.2)

**Branch**: `011-session-discovery` | **Date**: 2026-03-05

## R-001: File Watcher Library Selection

**Decision**: Use `watchdog` (PyPI: `watchdog>=4.0`)

**Rationale**:
- Cross-platform (Windows, macOS, Linux) with native OS-level filesystem event APIs
- Windows: uses `ReadDirectoryChangesW` via the built-in `WindowsApiObserver`
- Mature library (10+ years), well-maintained, 6k+ GitHub stars
- Supports recursive and non-recursive directory watching
- Thread-based observer model integrates cleanly with asyncio via thread-safe callbacks
- Already used extensively in Python projects for file monitoring (Django autoreload, Sphinx, etc.)

**Alternatives considered**:
- `watchfiles` (Rust-based): Faster event delivery, but requires Rust compilation toolchain. Async-native but less flexible for debouncing/stabilization. Overkill for monitoring a single directory with infrequent writes.
- `aiofiles` + polling: No native OS events, wastes CPU on polling intervals. Unreliable for detecting new files promptly.
- `asyncinotify`: Linux-only, not viable for Windows-targeted project.

## R-002: Stabilization Delay Strategy

**Decision**: 2-second debounce after last modification event before processing a file pair.

**Rationale**:
- AC writes the CSV continuously during a session (20-30Hz = ~1500-2250 rows/min)
- The meta.json is rewritten at session start, each pit exit, and session end
- Both files are finalized when the session ends (AC writes final values and closes files)
- A 2-second gap after the last modification event reliably indicates writing is complete
- The watcher handler tracks pending files with timestamps; a timer thread checks for stabilized pairs

**Implementation approach**:
- `watchdog` `FileSystemEventHandler.on_modified` / `on_created` events update a dict of `{base_name: last_seen_timestamp}`
- A separate check (either periodic or triggered by events) processes entries where `now - last_seen > 2s`
- Only processes entries where both `.csv` and `.meta.json` exist on disk

**Alternatives considered**:
- File lock checking: Windows file locks are unreliable for detecting write completion from another process
- File size polling: Requires repeated stat() calls and doesn't detect meta.json rewrites (same size)
- inotify `IN_CLOSE_WRITE`: Linux-only, not available on Windows

## R-003: Database Schema Migration Strategy

**Decision**: Idempotent `ALTER TABLE` statements in `init_db()`, guarded by column existence checks.

**Rationale**:
- The existing `init_db()` is already idempotent (uses `CREATE TABLE IF NOT EXISTS`)
- Adding columns via `ALTER TABLE ... ADD COLUMN` is also idempotent when wrapped in try/except for "duplicate column" errors
- SQLite does not support `ADD COLUMN IF NOT EXISTS`, so we catch `OperationalError` on duplicate
- No need for a migration framework (Alembic) for simple additive changes
- New columns have defaults or are nullable, so existing rows are unaffected

**New columns**:
- `state TEXT NOT NULL DEFAULT 'discovered'` — lifecycle state
- `session_type TEXT` — from meta.json (practice, qualify, race, etc.)
- `csv_path TEXT` — absolute path to CSV file
- `meta_path TEXT` — absolute path to meta.json file

**Note**: `best_lap_time` already exists in the schema. No migration needed for it.

## R-004: Sessions Directory Resolution

**Decision**: Default path is `Path.home() / "Documents" / "ac-race-engineer" / "sessions"`. No config field needed — the AC in-game app always writes to this fixed location.

**Rationale**:
- The AC in-game app (Phase 1) writes to `Documents/ac-race-engineer/sessions/` using the user's home directory
- This path is deterministic on Windows where Assetto Corsa runs
- Adding a config field would add complexity for a path the user never needs to change
- The path can be passed as a parameter to functions for testability, with the default resolved at the API layer

**Alternatives considered**:
- Config field in `ACConfig`: Adds a field the user never configures. AC always writes to the same place.
- Environment variable: Over-engineering for a single-user desktop app.

## R-005: Watcher Integration with FastAPI Lifespan

**Decision**: Start the `watchdog.Observer` in the existing `lifespan()` async context manager, store on `app.state`.

**Rationale**:
- The existing lifespan in `api/main.py` already manages `JobManager` — same pattern
- `watchdog.Observer` is a daemon thread, started with `.start()` and stopped with `.stop()` + `.join()`
- Thread-based observer works well alongside asyncio — events are delivered on the observer thread, and we use thread-safe mechanisms to communicate with the async API
- The observer is stored on `app.state.session_watcher` for endpoint access (e.g., sync endpoint needs the sessions directory path)

## R-006: Meta.json Parsing for Discovery

**Decision**: Minimal JSON parsing — read only the 5 fields needed for the session record. Do NOT use the full parser pipeline.

**Rationale**:
- Discovery only needs: `car_name`, `track_name`, `session_start`, `laps_completed`, `session_type`
- The full `parse_session()` pipeline (Phase 2) is expensive and unnecessary at discovery time
- Parsing happens in Phase 6.3 when the session transitions from "discovered" to "parsed"
- Using `json.load()` directly keeps the discovery module independent of the parser package
- Malformed JSON is caught and logged; the session is skipped

## R-007: Session ID from Filename

**Decision**: Use the base filename (stem) as `session_id` — e.g., `2026-03-05_1430_ks_ferrari_488_gt3_monza`.

**Rationale**:
- Filenames are already unique by construction (include timestamp + car + track)
- Generated by `ac_app/ac_race_engineer/modules/writer.py:generate_filename()`
- No need for UUIDs or database-generated IDs — the filename IS the natural key
- The `.meta.json` extension is stripped by using `.stem` on the meta file (which yields the base without `.meta.json` via a custom strip since `.stem` only removes last extension)
- Specifically: for `foo.meta.json`, the session_id is extracted as `foo` (strip `.meta.json` suffix)
