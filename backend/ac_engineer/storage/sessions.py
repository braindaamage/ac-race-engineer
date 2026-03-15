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
               (session_id, car, track, track_config, session_date, lap_count,
                best_lap_time, state, session_type, csv_path, meta_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.session_id,
                session.car,
                session.track,
                session.track_config,
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
    db_path: str | Path,
    *,
    car: str | None = None,
    track: str | None = None,
    track_config: str | None = None,
) -> list[SessionRecord]:
    """Return all sessions ordered by session_date DESC, optionally filtered."""
    conn = _connect(db_path)
    try:
        clauses: list[str] = []
        params: list[str] = []
        if car is not None:
            clauses.append("car = ?")
            params.append(car)
        if track is not None:
            clauses.append("track = ?")
            params.append(track)
            if track_config is not None:
                clauses.append("track_config = ?")
                params.append(track_config)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM sessions{where} ORDER BY session_date DESC",
            params,
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


def list_car_stats(db_path: str | Path) -> list[dict]:
    """Return aggregated stats per car, ordered by most recent session."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT car, "
            "COUNT(DISTINCT track || char(0) || track_config) AS track_count, "
            "COUNT(*) AS session_count, "
            "MAX(session_date) AS last_session_date "
            "FROM sessions GROUP BY car ORDER BY last_session_date DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def list_track_stats(db_path: str | Path, car: str) -> list[dict]:
    """Return aggregated stats per track+config for a given car."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT track, track_config, "
            "COUNT(*) AS session_count, "
            "MIN(best_lap_time) AS best_lap_time, "
            "MAX(session_date) AS last_session_date "
            "FROM sessions WHERE car = ? "
            "GROUP BY track, track_config ORDER BY last_session_date DESC",
            (car,),
        ).fetchall()
        return [dict(row) for row in rows]
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
