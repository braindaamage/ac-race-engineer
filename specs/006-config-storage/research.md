# Research: Config + Storage (Phase 5.1)

**Feature**: 006-config-storage | **Date**: 2026-03-04

## R-001: Atomic Config File Writes on Windows

**Decision**: Write to `config.json.tmp` in the same directory, then `os.replace()` to the final path.

**Rationale**: `os.replace()` is atomic on POSIX and near-atomic on Windows (NTFS MoveFileEx with MOVEFILE_REPLACE_EXISTING). It ensures that a crash mid-write never leaves a truncated `config.json`. Writing to the same directory guarantees same-filesystem rename.

**Alternatives considered**:
- `shutil.move()` — not atomic, involves copy + delete across filesystems
- Write-in-place with truncate — leaves corrupted file on crash
- Advisory file locking (`fcntl`/`msvcrt`) — overkill for single-user desktop; adds complexity

## R-002: SQLite Journal Mode

**Decision**: Enable WAL (Write-Ahead Logging) journal mode via `PRAGMA journal_mode=WAL` on each connection.

**Rationale**: WAL mode allows concurrent readers while a writer is active, provides better crash recovery than the default rollback journal, and is the recommended mode for desktop applications. It persists once set on a database file.

**Alternatives considered**:
- Default rollback journal — locks entire DB on writes, slower for our mixed read/write pattern
- WAL2 — not available in stdlib sqlite3

## R-003: SQLite Connection Management

**Decision**: Each public function opens its own connection, executes, and closes. No connection pooling or shared connection objects.

**Rationale**: The user constraint specifies "pure query functions (open connection, execute, close)." For a single-user desktop app with < 1,000 records, connection overhead is negligible (< 1ms). This avoids threading issues, leaked connections, and simplifies testing with `tmp_path`.

**Alternatives considered**:
- Connection pool (e.g., via context manager) — adds complexity for no measurable benefit at this scale
- Module-level singleton connection — complicates testing and parallel test execution

## R-004: Foreign Key Enforcement

**Decision**: Every connection executes `PRAGMA foreign_keys = ON` immediately after opening.

**Rationale**: SQLite disables foreign keys by default for backward compatibility. We need them to enforce session → recommendation → setup_change and session → message referential integrity. The pragma must be set per-connection (not persistent).

**Alternatives considered**:
- Application-level validation only — fragile, doesn't protect against direct DB edits or bugs
- Triggers — more complex, same effect

## R-005: Pydantic v2 Path Serialization

**Decision**: Config model stores paths as `str | None` (not `Path` objects). Consumers construct `Path` objects from the string if needed.

**Rationale**: The user constraint requires "Paths serialize as strings in JSON." Using `str` directly avoids custom serializers, keeps the JSON human-readable, and matches the existing pattern where paths come from user input as strings. Validation only checks that the value is a non-empty string when present.

**Alternatives considered**:
- `Path` fields with custom `json_serializer` — adds complexity for no benefit; JSON doesn't have a Path type
- `DirectoryPath` validator — would reject paths that don't exist yet (user may configure before installing AC)

## R-006: ID Generation Strategy

**Decision**: Session IDs are caller-provided strings (from the parser's session identifier). Recommendation, setup_change, and message IDs are generated via `uuid.uuid4().hex` at save time.

**Rationale**: Sessions already have natural identifiers from the parser (derived from filename/metadata). Other entities are system-generated and have no natural key. UUID4 hex (32 chars, no dashes) is compact, collision-free, and stdlib.

**Alternatives considered**:
- SQLite AUTOINCREMENT — ties IDs to a single database; UUIDs are portable
- ULID — not in stdlib; would require an external dependency

## R-007: Setup Changes Storage Model

**Decision**: Store setup_changes in a separate table with a foreign key to recommendations, not as JSON blob in the recommendations table.

**Rationale**: Enables querying individual parameter changes, filtering by section/parameter, and avoids JSON parsing overhead. Follows relational best practices. Each setup_change row has its own UUID.

**Alternatives considered**:
- JSON column in recommendations — simpler schema but loses queryability and type safety
- Separate Pydantic model serialized to JSON — same issue as JSON column

## R-008: Timestamp Format

**Decision**: Store timestamps as ISO 8601 strings (`datetime.isoformat()`) in SQLite TEXT columns.

**Rationale**: Human-readable, timezone-aware capable, and natively supported by Python's `datetime.fromisoformat()`. SQLite has no native datetime type; TEXT with ISO format is the recommended approach per SQLite documentation.

**Alternatives considered**:
- Unix epoch integers — less readable, loses timezone info
- SQLite datetime functions — limited and not needed for our simple chronological ordering
