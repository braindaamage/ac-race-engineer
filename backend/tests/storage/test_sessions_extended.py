"""Tests for extended session storage operations (Phase 6.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.storage.db import _connect, init_db
from ac_engineer.storage.models import VALID_SESSION_STATES, SessionRecord
from ac_engineer.storage.sessions import (
    delete_session,
    get_session,
    list_sessions,
    save_session,
    session_exists,
    update_session_state,
)


def _session(**overrides: object) -> SessionRecord:
    defaults = {
        "session_id": "test_session_001",
        "car": "ks_ferrari_488_gt3",
        "track": "monza",
        "session_date": "2026-03-04T14:30:00",
        "lap_count": 12,
        "best_lap_time": 108.432,
        "state": "discovered",
        "session_type": "practice",
        "csv_path": "/path/to/session.csv",
        "meta_path": "/path/to/session.meta.json",
    }
    defaults.update(overrides)
    return SessionRecord(**defaults)


class TestSaveWithNewFields:
    def test_save_includes_new_fields(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)
        loaded = get_session(db_path, session.session_id)
        assert loaded is not None
        assert loaded.state == "discovered"
        assert loaded.session_type == "practice"
        assert loaded.csv_path == "/path/to/session.csv"
        assert loaded.meta_path == "/path/to/session.meta.json"

    def test_save_with_null_optional_fields(self, db_path: Path) -> None:
        session = _session(session_type=None, csv_path=None, meta_path=None)
        save_session(db_path, session)
        loaded = get_session(db_path, session.session_id)
        assert loaded is not None
        assert loaded.session_type is None
        assert loaded.csv_path is None
        assert loaded.meta_path is None

    def test_list_sessions_returns_new_fields(self, db_path: Path) -> None:
        save_session(db_path, _session())
        sessions = list_sessions(db_path)
        assert len(sessions) == 1
        assert sessions[0].state == "discovered"
        assert sessions[0].session_type == "practice"


class TestSessionExists:
    def test_exists_true(self, db_path: Path) -> None:
        save_session(db_path, _session())
        assert session_exists(db_path, "test_session_001") is True

    def test_exists_false(self, db_path: Path) -> None:
        assert session_exists(db_path, "nonexistent") is False


class TestDeleteSession:
    def test_delete_found(self, db_path: Path) -> None:
        save_session(db_path, _session())
        assert delete_session(db_path, "test_session_001") is True
        assert get_session(db_path, "test_session_001") is None

    def test_delete_not_found(self, db_path: Path) -> None:
        assert delete_session(db_path, "nonexistent") is False

    def test_delete_cascades_to_recommendations(self, db_path: Path) -> None:
        session = _session()
        save_session(db_path, session)
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
        finally:
            conn.close()

        delete_session(db_path, session.session_id)

        conn = _connect(db_path)
        try:
            recs = conn.execute("SELECT * FROM recommendations").fetchall()
            msgs = conn.execute("SELECT * FROM messages").fetchall()
            assert len(recs) == 0
            assert len(msgs) == 0
        finally:
            conn.close()


class TestUpdateSessionState:
    def test_update_valid_state(self, db_path: Path) -> None:
        save_session(db_path, _session())
        assert update_session_state(db_path, "test_session_001", "parsed") is True
        loaded = get_session(db_path, "test_session_001")
        assert loaded is not None
        assert loaded.state == "parsed"

    def test_update_all_valid_states(self, db_path: Path) -> None:
        save_session(db_path, _session())
        for state in VALID_SESSION_STATES:
            assert update_session_state(db_path, "test_session_001", state) is True
            loaded = get_session(db_path, "test_session_001")
            assert loaded is not None
            assert loaded.state == state

    def test_update_invalid_state_raises(self, db_path: Path) -> None:
        save_session(db_path, _session())
        with pytest.raises(ValueError, match="Invalid state"):
            update_session_state(db_path, "test_session_001", "bogus")

    def test_update_not_found(self, db_path: Path) -> None:
        assert update_session_state(db_path, "nonexistent", "parsed") is False


class TestMigrationIdempotency:
    def test_init_db_twice_no_error(self, tmp_path: Path) -> None:
        path = tmp_path / "test.db"
        init_db(path)
        init_db(path)  # Should not raise
        save_session(path, _session())
        loaded = get_session(path, "test_session_001")
        assert loaded is not None
        assert loaded.state == "discovered"
