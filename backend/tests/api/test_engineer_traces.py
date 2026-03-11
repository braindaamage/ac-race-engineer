"""Tests for diagnostic trace API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from ac_engineer.engineer.trace import write_trace
from ac_engineer.storage.db import init_db
from ac_engineer.storage.messages import save_message
from ac_engineer.storage.models import SessionRecord, SetupChange as StorageSetupChange
from ac_engineer.storage.recommendations import save_recommendation
from ac_engineer.storage.sessions import save_session
from api.jobs.manager import JobManager
from api.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def traces_dir(tmp_path: Path) -> Path:
    d = tmp_path / "traces"
    d.mkdir()
    return d


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    p = tmp_path / "config.json"
    p.write_text(json.dumps({
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-5",
    }), encoding="utf-8")
    return p


@pytest.fixture()
def app(db_path: Path, sessions_dir: Path, config_path: Path):
    a = create_app()
    a.state.db_path = db_path
    a.state.sessions_dir = sessions_dir
    a.state.config_path = config_path
    a.state.job_manager = JobManager()
    a.state.active_processing_jobs = {}
    a.state.active_engineer_jobs = {}
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
        "session_id": "test_session",
        "car": "bmw_m235i_racing",
        "track": "mugello",
        "session_date": "2026-03-02T14:30:00",
        "lap_count": 4,
        "best_lap_time": 90.0,
        "state": "analyzed",
        "session_type": "practice",
        "csv_path": "/path/to/session.csv",
        "meta_path": "/path/to/session.meta.json",
    }
    defaults.update(overrides)
    return SessionRecord(**defaults)


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations/{recommendation_id}/trace
# ---------------------------------------------------------------------------


class TestRecommendationTrace:
    @pytest.mark.asyncio
    async def test_trace_available(
        self, client, db_path, traces_dir, app,
    ) -> None:
        """Returns available=true with content when trace file exists."""
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Test summary",
            [StorageSetupChange(section="SPRING_RATE_LF", parameter="VALUE",
                                old_value="100000", new_value="110000",
                                reasoning="test")],
        )
        rec_id = rec.recommendation_id

        # Write a trace file
        from unittest.mock import patch
        with patch("api.paths.get_traces_dir", return_value=traces_dir):
            trace_content = "# Diagnostic Trace\nTest content"
            write_trace(traces_dir, "rec", rec_id, trace_content)

            resp = await client.get(
                f"/sessions/test_session/recommendations/{rec_id}/trace",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["content"] == trace_content
        assert data["trace_type"] == "recommendation"
        assert data["id"] == rec_id

    @pytest.mark.asyncio
    async def test_trace_not_available(
        self, client, db_path, traces_dir, app,
    ) -> None:
        """Returns available=false when no trace file exists."""
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Test summary",
            [StorageSetupChange(section="SPRING_RATE_LF", parameter="VALUE",
                                old_value="100000", new_value="110000",
                                reasoning="test")],
        )
        rec_id = rec.recommendation_id

        from unittest.mock import patch
        with patch("api.paths.get_traces_dir", return_value=traces_dir):
            resp = await client.get(
                f"/sessions/test_session/recommendations/{rec_id}/trace",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["content"] is None

    @pytest.mark.asyncio
    async def test_recommendation_not_found(
        self, client, db_path,
    ) -> None:
        """Returns 404 when recommendation doesn't exist."""
        save_session(db_path, _session())

        resp = await client.get(
            "/sessions/test_session/recommendations/nonexistent/trace",
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_session_not_found(
        self, client,
    ) -> None:
        """Returns 404 when session doesn't exist."""
        resp = await client.get(
            "/sessions/nonexistent/recommendations/some-id/trace",
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages/{message_id}/trace
# ---------------------------------------------------------------------------


class TestMessageTrace:
    @pytest.mark.asyncio
    async def test_trace_available(
        self, client, db_path, traces_dir, app,
    ) -> None:
        """Returns available=true with content when trace file exists."""
        save_session(db_path, _session())
        msg = save_message(db_path, "test_session", "assistant", "Hello")
        msg_id = msg.message_id

        from unittest.mock import patch
        with patch("api.paths.get_traces_dir", return_value=traces_dir):
            trace_content = "# Diagnostic Trace\nChat trace"
            write_trace(traces_dir, "msg", msg_id, trace_content)

            resp = await client.get(
                f"/sessions/test_session/messages/{msg_id}/trace",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["content"] == trace_content
        assert data["trace_type"] == "message"
        assert data["id"] == msg_id

    @pytest.mark.asyncio
    async def test_trace_not_available(
        self, client, db_path, traces_dir, app,
    ) -> None:
        """Returns available=false when no trace file exists."""
        save_session(db_path, _session())
        msg = save_message(db_path, "test_session", "assistant", "Hello")

        from unittest.mock import patch
        with patch("api.paths.get_traces_dir", return_value=traces_dir):
            resp = await client.get(
                f"/sessions/test_session/messages/{msg.message_id}/trace",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False
        assert data["content"] is None

    @pytest.mark.asyncio
    async def test_message_not_found(
        self, client, db_path,
    ) -> None:
        """Returns 404 when message doesn't exist."""
        save_session(db_path, _session())

        resp = await client.get(
            "/sessions/test_session/messages/nonexistent/trace",
        )
        assert resp.status_code == 404
