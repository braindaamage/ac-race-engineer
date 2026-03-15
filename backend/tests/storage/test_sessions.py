"""Tests for session CRUD operations."""

from __future__ import annotations

from pathlib import Path

from ac_engineer.storage.db import _connect
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import (
    get_session,
    list_car_stats,
    list_sessions,
    list_track_stats,
    save_session,
)


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


class TestListSessionsTrackFilter:
    def test_filter_by_track(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", track="monza"))
        save_session(db_path, _session(session_id="s2", track="spa"))
        result = list_sessions(db_path, track="monza")
        assert len(result) == 1
        assert result[0].track == "monza"

    def test_filter_by_track_and_config(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", track="nurburgring", track_config="gp"))
        save_session(db_path, _session(session_id="s2", track="nurburgring", track_config="nordschleife"))
        save_session(db_path, _session(session_id="s3", track="nurburgring"))
        result = list_sessions(db_path, track="nurburgring", track_config="gp")
        assert len(result) == 1
        assert result[0].session_id == "s1"

    def test_track_config_ignored_without_track(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", track_config="gp"))
        save_session(db_path, _session(session_id="s2"))
        result = list_sessions(db_path, track_config="gp")
        assert len(result) == 2  # track_config alone is ignored


class TestSaveSessionTrackConfig:
    def test_persists_track_config(self, db_path: Path) -> None:
        save_session(db_path, _session(track_config="gp"))
        loaded = get_session(db_path, "test_session_001")
        assert loaded is not None
        assert loaded.track_config == "gp"

    def test_default_empty_track_config(self, db_path: Path) -> None:
        save_session(db_path, _session())
        loaded = get_session(db_path, "test_session_001")
        assert loaded is not None
        assert loaded.track_config == ""


class TestListCarStats:
    def test_returns_correct_stats(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari", track="monza"))
        save_session(db_path, _session(session_id="s2", car="ferrari", track="spa"))
        save_session(db_path, _session(session_id="s3", car="porsche", track="monza"))
        stats = list_car_stats(db_path)
        assert len(stats) == 2
        ferrari = next(s for s in stats if s["car"] == "ferrari")
        assert ferrari["track_count"] == 2
        assert ferrari["session_count"] == 2

    def test_empty_db(self, db_path: Path) -> None:
        assert list_car_stats(db_path) == []

    def test_track_count_with_configs(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari", track="nurburgring", track_config="gp"))
        save_session(db_path, _session(session_id="s2", car="ferrari", track="nurburgring", track_config="nordschleife"))
        save_session(db_path, _session(session_id="s3", car="ferrari", track="monza"))
        stats = list_car_stats(db_path)
        ferrari = stats[0]
        assert ferrari["track_count"] == 3  # gp, nordschleife, monza

    def test_ordered_by_last_session(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="old_car", session_date="2026-01-01T00:00:00"))
        save_session(db_path, _session(session_id="s2", car="new_car", session_date="2026-03-01T00:00:00"))
        stats = list_car_stats(db_path)
        assert stats[0]["car"] == "new_car"


class TestListTrackStats:
    def test_groups_by_track_and_config(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari", track="nurburgring", track_config="gp", best_lap_time=120.0))
        save_session(db_path, _session(session_id="s2", car="ferrari", track="nurburgring", track_config="gp", best_lap_time=115.0))
        save_session(db_path, _session(session_id="s3", car="ferrari", track="nurburgring", track_config="nordschleife"))
        stats = list_track_stats(db_path, "ferrari")
        assert len(stats) == 2
        gp = next(s for s in stats if s["track_config"] == "gp")
        assert gp["session_count"] == 2
        assert gp["best_lap_time"] == 115.0

    def test_empty_for_unknown_car(self, db_path: Path) -> None:
        assert list_track_stats(db_path, "nonexistent") == []

    def test_best_lap_time_null_when_none(self, db_path: Path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari", best_lap_time=None))
        stats = list_track_stats(db_path, "ferrari")
        assert stats[0]["best_lap_time"] is None


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
