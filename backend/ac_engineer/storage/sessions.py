"""Session CRUD operations."""

from __future__ import annotations

from pathlib import Path

from .db import _connect
from .models import SessionRecord


def save_session(db_path: str | Path, session: SessionRecord) -> None:
    """Upsert a session record."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, car, track, session_date, lap_count, best_lap_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session.session_id,
                session.car,
                session.track,
                session.session_date,
                session.lap_count,
                session.best_lap_time,
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
