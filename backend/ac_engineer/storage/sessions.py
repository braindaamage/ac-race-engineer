"""Session CRUD operations."""

from __future__ import annotations

from pathlib import Path

from .db import _connect
from .models import VALID_SESSION_STATES, SessionRecord


def save_session(db_path: str | Path, session: SessionRecord) -> None:
    """Upsert a session record."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, car, track, session_date, lap_count, best_lap_time,
                state, session_type, csv_path, meta_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.session_id,
                session.car,
                session.track,
                session.session_date,
                session.lap_count,
                session.best_lap_time,
                session.state,
                session.session_type,
                session.csv_path,
                session.meta_path,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_sessions(
    db_path: str | Path, *, car: str | None = None
) -> list[SessionRecord]:
    """Return all sessions ordered by session_date DESC, optionally filtered by car."""
    conn = _connect(db_path)
    try:
        if car is not None:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE car = ? ORDER BY session_date DESC",
                (car,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY session_date DESC"
            ).fetchall()
        return [SessionRecord(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_session(db_path: str | Path, session_id: str) -> SessionRecord | None:
    """Return a single session by ID, or None if not found."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None
        return SessionRecord(**dict(row))
    finally:
        conn.close()


def session_exists(db_path: str | Path, session_id: str) -> bool:
    """Check if a session record exists."""
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def delete_session(db_path: str | Path, session_id: str) -> bool:
    """Delete a session by ID. Returns True if deleted, False if not found."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM sessions WHERE session_id = ?", (session_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_session_state(db_path: str | Path, session_id: str, state: str) -> bool:
    """Update the lifecycle state of a session. Returns True if updated, False if not found."""
    if state not in VALID_SESSION_STATES:
        raise ValueError(f"Invalid state '{state}'. Must be one of {VALID_SESSION_STATES}")
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE sessions SET state = ? WHERE session_id = ?",
            (state, session_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
