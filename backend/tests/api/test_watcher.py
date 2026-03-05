"""Tests for session file watcher handler and lifecycle."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from ac_engineer.storage.db import init_db
from ac_engineer.storage.sessions import get_session
from api.watcher.handler import SessionEventHandler, DEBOUNCE_SECONDS
from api.watcher.observer import SessionWatcher


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


def _create_pair(sessions_dir: Path, name: str) -> None:
    csv_path = sessions_dir / f"{name}.csv"
    meta_path = sessions_dir / f"{name}.meta.json"
    csv_path.write_text("header\n")
    meta_data = {
        "car_name": "test_car",
        "track_name": "test_track",
        "session_start": "2026-03-05T14:30:00",
        "laps_completed": 5,
        "session_type": "practice",
    }
    meta_path.write_text(json.dumps(meta_data), encoding="utf-8")


class TestSessionEventHandler:
    def test_tracks_csv_events(self, sessions_dir: Path, db_path: Path) -> None:
        handler = SessionEventHandler(sessions_dir, db_path)
        handler._track(str(sessions_dir / "test.csv"))
        assert "test" in handler._pending
        handler.stop()

    def test_tracks_meta_events(self, sessions_dir: Path, db_path: Path) -> None:
        handler = SessionEventHandler(sessions_dir, db_path)
        handler._track(str(sessions_dir / "test.meta.json"))
        assert "test" in handler._pending
        handler.stop()

    def test_ignores_irrelevant_files(self, sessions_dir: Path, db_path: Path) -> None:
        handler = SessionEventHandler(sessions_dir, db_path)
        assert handler._is_relevant(str(sessions_dir / "test.csv")) is True
        assert handler._is_relevant(str(sessions_dir / "test.meta.json")) is True
        assert handler._is_relevant(str(sessions_dir / "test.txt")) is False
        assert handler._is_relevant(str(sessions_dir / "test.json")) is False
        handler.stop()

    def test_debounce_prevents_premature_processing(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(sessions_dir, "debounce_test")
        handler = SessionEventHandler(sessions_dir, db_path)

        # Track the file — it should be pending, not yet processed
        handler._track(str(sessions_dir / "debounce_test.csv"))
        assert "debounce_test" in handler._pending
        # Session should not yet be registered
        assert get_session(db_path, "debounce_test") is None
        handler.stop()

    def test_stabilized_pair_triggers_registration(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(sessions_dir, "stable_test")
        handler = SessionEventHandler(sessions_dir, db_path)

        # Simulate a tracked event that's already stabilized
        handler._pending["stable_test"] = time.monotonic() - DEBOUNCE_SECONDS - 1
        handler._check_stabilized()

        session = get_session(db_path, "stable_test")
        assert session is not None
        assert session.car == "test_car"
        handler.stop()

    def test_handler_ignores_incomplete_pair(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        # Only CSV, no meta.json
        (sessions_dir / "orphan.csv").write_text("data\n")
        handler = SessionEventHandler(sessions_dir, db_path)
        handler._pending["orphan"] = time.monotonic() - DEBOUNCE_SECONDS - 1
        handler._check_stabilized()
        assert get_session(db_path, "orphan") is None
        handler.stop()


class TestSessionWatcher:
    def test_start_creates_missing_dir(self, tmp_path: Path, db_path: Path) -> None:
        missing_dir = tmp_path / "new_sessions"
        watcher = SessionWatcher()
        watcher.start(missing_dir, db_path)
        assert missing_dir.is_dir()
        watcher.stop()

    def test_start_and_stop(self, sessions_dir: Path, db_path: Path) -> None:
        watcher = SessionWatcher()
        watcher.start(sessions_dir, db_path)
        assert watcher._observer is not None
        assert watcher._observer.is_alive()
        watcher.stop()

    def test_stop_without_start(self) -> None:
        watcher = SessionWatcher()
        watcher.stop()  # Should not raise


class TestLifespanIntegration:
    @pytest.mark.asyncio
    async def test_lifespan_starts_watcher(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        from api.main import create_app
        import httpx

        app = create_app()
        app.state.db_path = db_path
        app.state.sessions_dir = sessions_dir

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            # Verify the app starts (lifespan runs)
            resp = await client.get("/health")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_initial_scan_runs_on_startup(
        self, sessions_dir: Path, db_path: Path
    ) -> None:
        _create_pair(sessions_dir, "pre_existing")

        from api.main import create_app, lifespan
        import httpx

        app = create_app()
        app.state.db_path = db_path
        app.state.sessions_dir = sessions_dir

        async with lifespan(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                resp = await client.get("/sessions/pre_existing")
                assert resp.status_code == 200
                data = resp.json()
                assert data["session_id"] == "pre_existing"
