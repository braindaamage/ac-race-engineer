"""Tests for session endpoints (GET /sessions, GET /sessions/{id}, POST /sessions/sync, DELETE /sessions/{id})."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import get_session, save_session
from ac_engineer.storage.db import _connect
from api.main import create_app


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


@pytest.fixture()
def app(db_path: Path, sessions_dir: Path):
    a = create_app()
    a.state.db_path = db_path
    a.state.sessions_dir = sessions_dir
    return a


@pytest_asyncio.fixture
async def client(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


def _session(**overrides) -> SessionRecord:
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


def _create_pair(sessions_dir: Path, name: str, meta: dict | None = None) -> None:
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


# --- GET /sessions ---


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_empty(self, client, db_path) -> None:
        resp = await client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []

    @pytest.mark.asyncio
    async def test_list_with_sessions(self, client, db_path) -> None:
        save_session(db_path, _session(session_id="s1"))
        save_session(db_path, _session(session_id="s2"))
        resp = await client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 2

    @pytest.mark.asyncio
    async def test_list_filtered_by_car(self, client, db_path) -> None:
        save_session(db_path, _session(session_id="s1", car="ferrari"))
        save_session(db_path, _session(session_id="s2", car="porsche"))
        resp = await client.get("/sessions", params={"car": "ferrari"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["car"] == "ferrari"


# --- GET /sessions/{session_id} ---


class TestGetSession:
    @pytest.mark.asyncio
    async def test_get_existing(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.get("/sessions/test_session_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session_001"
        assert data["state"] == "discovered"

    @pytest.mark.asyncio
    async def test_get_nonexistent_404(self, client) -> None:
        resp = await client.get("/sessions/nonexistent")
        assert resp.status_code == 404


# --- POST /sessions/sync ---


class TestSyncSessions:
    @pytest.mark.asyncio
    async def test_sync_empty_dir(self, client, sessions_dir) -> None:
        resp = await client.post("/sessions/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered"] == 0

    @pytest.mark.asyncio
    async def test_sync_with_new_pairs(
        self, client, sessions_dir, db_path
    ) -> None:
        _create_pair(sessions_dir, "new_session")
        resp = await client.post("/sessions/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered"] == 1
        session = get_session(db_path, "new_session")
        assert session is not None

    @pytest.mark.asyncio
    async def test_sync_already_known(
        self, client, sessions_dir, db_path
    ) -> None:
        _create_pair(sessions_dir, "known_session")
        await client.post("/sessions/sync")
        resp = await client.post("/sessions/sync")
        data = resp.json()
        assert data["discovered"] == 0
        assert data["already_known"] == 1

    @pytest.mark.asyncio
    async def test_sync_with_orphans(self, client, sessions_dir) -> None:
        (sessions_dir / "orphan.csv").write_text("data\n")
        resp = await client.post("/sessions/sync")
        data = resp.json()
        assert data["incomplete"] >= 1

    @pytest.mark.asyncio
    async def test_sync_nonexistent_dir(
        self, client, app, tmp_path
    ) -> None:
        app.state.sessions_dir = tmp_path / "nonexistent"
        resp = await client.post("/sessions/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovered"] == 0


# --- DELETE /sessions/{session_id} ---


class TestDeleteSession:
    @pytest.mark.asyncio
    async def test_delete_existing(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.delete("/sessions/test_session_001")
        assert resp.status_code == 204
        assert get_session(db_path, "test_session_001") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_404(self, client) -> None:
        resp = await client.delete("/sessions/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cascades(self, client, db_path) -> None:
        save_session(db_path, _session())
        conn = _connect(db_path)
        try:
            conn.execute(
                "INSERT INTO recommendations (recommendation_id, session_id, status, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                ("rec1", "test_session_001", "proposed", "test", "2026-03-04T15:00:00"),
            )
            conn.execute(
                "INSERT INTO messages (message_id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                ("msg1", "test_session_001", "user", "test", "2026-03-04T15:00:00"),
            )
            conn.commit()
        finally:
            conn.close()

        resp = await client.delete("/sessions/test_session_001")
        assert resp.status_code == 204

        conn = _connect(db_path)
        try:
            recs = conn.execute("SELECT * FROM recommendations").fetchall()
            msgs = conn.execute("SELECT * FROM messages").fetchall()
            assert len(recs) == 0
            assert len(msgs) == 0
        finally:
            conn.close()

    @pytest.mark.asyncio
    async def test_delete_does_not_remove_files(
        self, client, db_path, sessions_dir
    ) -> None:
        csv_file = sessions_dir / "test_session_001.csv"
        meta_file = sessions_dir / "test_session_001.meta.json"
        csv_file.write_text("data\n")
        meta_file.write_text("{}")
        save_session(
            db_path,
            _session(
                csv_path=str(csv_file),
                meta_path=str(meta_file),
            ),
        )
        resp = await client.delete("/sessions/test_session_001")
        assert resp.status_code == 204
        assert csv_file.exists()
        assert meta_file.exists()
