"""Tests for session CRUD operations."""

from __future__ import annotations

from pathlib import Path

from ac_engineer.storage.db import _connect
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import get_session, list_sessions, save_session


def _session(**overrides: object) -> SessionRecord:
    defaults = {
        "session_id": "test_session_001",
        "car": "ks_ferrari_488_gt3",
        "track": "monza",
        "session_date": "2026-03-04T14:30:00",
        "lap_count": 12,
        "best_lap_time": 108.432,
    }
    defaults.update(overrides)
    return SessionRecord(**defaults)


class TestSaveSession:
    def test_insert(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)
        loaded = get_session(db_path, session.session_id)
        assert loaded is not None
        assert loaded.car == session.car
        assert loaded.track == session.track

    def test_upsert_updates_existing(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)
        updated = _session(lap_count=20, best_lap_time=105.0)
        save_session(db_path, updated)
        loaded = get_session(db_path, session.session_id)
        assert loaded is not None
        assert loaded.lap_count == 20
        assert loaded.best_lap_time == 105.0


class TestListSessions:
    def test_empty_db(self, db_path: Path) -> None:
        assert list_sessions(db_path) == []

    def test_ordering_most_recent_first(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", session_date="2026-03-01T10:00:00"))
        save_session(db_path, _session(session_id="s2", session_date="2026-03-03T10:00:00"))
        save_session(db_path, _session(session_id="s3", session_date="2026-03-02T10:00:00"))
        sessions = list_sessions(db_path)
        assert [s.session_id for s in sessions] == ["s2", "s3", "s1"]

    def test_filter_by_car(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari"))
        save_session(db_path, _session(session_id="s2", car="porsche"))
        save_session(db_path, _session(session_id="s3", car="ferrari"))
        result = list_sessions(db_path, car="ferrari")
        assert len(result) == 2
        assert all(s.car == "ferrari" for s in result)

    def test_filter_no_matches(self, db_path: Path) -> None:
        save_session(db_path, _session())
        assert list_sessions(db_path, car="nonexistent") == []


class TestGetSession:
    def test_found(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)
        loaded = get_session(db_path, session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_not_found(self, db_path: Path) -> None:
        assert get_session(db_path, "nonexistent") is None


class TestCascadeDelete:
    def test_delete_session_cascades(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)

        # Insert a recommendation and message directly
        conn = _connect(db_path)
        try:
            conn.execute(
                "INSERT INTO recommendations (recommendation_id, session_id, status, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                ("rec1", session.session_id, "proposed", "test", "2026-03-04T15:00:00"),
            )
            conn.execute(
                "INSERT INTO messages (message_id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                ("msg1", session.session_id, "user", "test", "2026-03-04T15:00:00"),
            )
            conn.commit()

            # Delete the session
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session.session_id,))
            conn.commit()

            # Verify cascaded deletes
            recs = conn.execute("SELECT * FROM recommendations").fetchall()
            msgs = conn.execute("SELECT * FROM messages").fetchall()
            assert len(recs) == 0
            assert len(msgs) == 0
        finally:
            conn.close()
