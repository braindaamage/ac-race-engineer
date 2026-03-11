"""Database initialization and connection helper."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    car           TEXT NOT NULL,
    track         TEXT NOT NULL,
    session_date  TEXT NOT NULL,
    lap_count     INTEGER NOT NULL,
    best_lap_time REAL
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id TEXT PRIMARY KEY,
    session_id        TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    status            TEXT NOT NULL DEFAULT 'proposed'
                      CHECK(status IN ('proposed', 'applied', 'rejected')),
    summary           TEXT NOT NULL,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS setup_changes (
    change_id         TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL REFERENCES recommendations(recommendation_id) ON DELETE CASCADE,
    section           TEXT NOT NULL,
    parameter         TEXT NOT NULL,
    old_value         TEXT NOT NULL,
    new_value         TEXT NOT NULL,
    reasoning         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


_MIGRATIONS = [
    "ALTER TABLE sessions ADD COLUMN state TEXT NOT NULL DEFAULT 'discovered'",
    "ALTER TABLE sessions ADD COLUMN session_type TEXT",
    "ALTER TABLE sessions ADD COLUMN csv_path TEXT",
    "ALTER TABLE sessions ADD COLUMN meta_path TEXT",
    (
        "CREATE TABLE IF NOT EXISTS parameter_cache ("
        "car_name TEXT PRIMARY KEY, "
        "tier INTEGER NOT NULL CHECK(tier IN (1, 2)), "
        "has_defaults INTEGER NOT NULL DEFAULT 0, "
        "parameters_json TEXT NOT NULL, "
        "resolved_at TEXT NOT NULL"
        ")"
    ),
    (
        "CREATE TABLE IF NOT EXISTS llm_events ("
        "id TEXT PRIMARY KEY, "
        "session_id TEXT NOT NULL, "
        "event_type TEXT NOT NULL, "
        "agent_name TEXT NOT NULL, "
        "model TEXT NOT NULL, "
        "input_tokens INTEGER NOT NULL CHECK(input_tokens >= 0), "
        "output_tokens INTEGER NOT NULL CHECK(output_tokens >= 0), "
        "request_count INTEGER NOT NULL CHECK(request_count >= 0), "
        "tool_call_count INTEGER NOT NULL CHECK(tool_call_count >= 0), "
        "duration_ms INTEGER NOT NULL CHECK(duration_ms >= 0), "
        "created_at TEXT NOT NULL, "
        "context_type TEXT, "
        "context_id TEXT"
        ")"
    ),
    (
        "CREATE TABLE IF NOT EXISTS llm_tool_calls ("
        "id TEXT PRIMARY KEY, "
        "event_id TEXT NOT NULL REFERENCES llm_events(id) ON DELETE CASCADE, "
        "tool_name TEXT NOT NULL, "
        "response_tokens INTEGER NOT NULL CHECK(response_tokens >= 0), "
        "call_index INTEGER NOT NULL CHECK(call_index >= 0)"
        ")"
    ),
    "ALTER TABLE llm_events ADD COLUMN cache_read_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_read_tokens >= 0)",
    "ALTER TABLE llm_events ADD COLUMN cache_write_tokens INTEGER NOT NULL DEFAULT 0 CHECK(cache_write_tokens >= 0)",
    "ALTER TABLE recommendations ADD COLUMN explanation TEXT NOT NULL DEFAULT ''",
]


def init_db(db_path: str | Path) -> None:
    """Create database file and all tables. Idempotent."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(path)
    try:
        conn.executescript(_SCHEMA)
        for stmt in _MIGRATIONS:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()
    finally:
        conn.close()
