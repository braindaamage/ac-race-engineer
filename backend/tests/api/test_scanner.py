"""Tests for session directory scanner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ac_engineer.storage.db import init_db
from ac_engineer.storage.sessions import get_session, save_session
from ac_engineer.storage.models import SessionRecord
from api.watcher.scanner import scan_sessions_dir


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    init_db(path)
    return path


@pytest.fixture()
def sessions_dir(tmp_path: Path) -> Path:
    d = tmp_path / "sessions"
    d.mkdir()
    return d


def _create_pair(sessions_dir: Path, name: str, meta: dict | None = None) -> None:
    """Create a CSV + meta.json pair in the sessions dir."""
    csv_path = sessions_dir / f"{name}.csv"
    meta_path = sessions_dir / f"{name}.meta.json"
    csv_path.write_text("header\n")
    meta_data = meta or {
        "car_name": "test_car",
        "track_name": "test_track",
        "session_start": "2026-03-05T14:30:00",
        "laps_completed": 5,
        "session_type": "practice",
    }
    meta_path.write_text(json.dumps(meta_data), encoding="utf-8")


class TestScanSessionsDir:
    def test_empty_dir(self, sessions_dir: Path, db_path: Path) -> None:
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.already_known == 0
        assert result.incomplete == 0

    def test_valid_pair_registered(self, sessions_dir: Path, db_path: Path) -> None:
        _create_pair(sessions_dir, "session_001")
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 1
        assert result.already_known == 0
        session = get_session(db_path, "session_001")
        assert session is not None
        assert session.car == "test_car"
        assert session.track == "test_track"
        assert session.state == "discovered"
        assert session.session_type == "practice"

    def test_orphan_csv_skipped(self, sessions_dir: Path, db_path: Path) -> None:
        (sessions_dir / "orphan.csv").write_text("data\n")
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.incomplete == 1

    def test_orphan_meta_skipped(self, sessions_dir: Path, db_path: Path) -> None:
        (sessions_dir / "orphan.meta.json").write_text('{"car_name":"x"}')
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.incomplete == 1

    def test_already_registered_not_duplicated(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(sessions_dir, "session_001")
        scan_sessions_dir(sessions_dir, db_path)
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.already_known == 1

    def test_malformed_json_skipped(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        (sessions_dir / "bad.csv").write_text("data\n")
        (sessions_dir / "bad.meta.json").write_text("not json{{{")
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.incomplete >= 1

    def test_missing_dir_returns_empty(self, tmp_path: Path, db_path: Path) -> None:
        nonexistent = tmp_path / "does_not_exist"
        result = scan_sessions_dir(nonexistent, db_path)
        assert result.discovered == 0
        assert result.already_known == 0
        assert result.incomplete == 0

    def test_multiple_pairs_mixed(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(sessions_dir, "good_001")
        _create_pair(sessions_dir, "good_002")
        (sessions_dir / "orphan.csv").write_text("data\n")
        (sessions_dir / "bad.csv").write_text("data\n")
        (sessions_dir / "bad.meta.json").write_text("not json")
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 2
        assert result.incomplete >= 1  # orphan csv + bad json pair

    def test_meta_missing_required_fields(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(
            sessions_dir,
            "incomplete",
            meta={"car_name": "x"},  # missing track_name and session_start
        )
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 0
        assert result.incomplete >= 1

    def test_laps_completed_null_defaults_to_zero(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(
            sessions_dir,
            "no_laps",
            meta={
                "car_name": "car",
                "track_name": "track",
                "session_start": "2026-03-05T14:30:00",
                "laps_completed": None,
            },
        )
        result = scan_sessions_dir(sessions_dir, db_path)
        assert result.discovered == 1
        session = get_session(db_path, "no_laps")
        assert session is not None
        assert session.lap_count == 0
