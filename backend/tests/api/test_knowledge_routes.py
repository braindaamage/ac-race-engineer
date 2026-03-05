"""Tests for knowledge route endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
import httpx

from ac_engineer.analyzer import analyze_session
from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import save_session

from api.analysis.cache import get_cache_dir, save_analyzed_session
from api.jobs.manager import JobManager
from api.main import create_app

from tests.analyzer.conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    SETUP_A,
    make_corner,
    make_lap_segment,
    make_parsed_session,
)


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
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "config.json"


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


def _make_analyzed_session():
    """Build a minimal AnalyzedSession with flying laps."""
    base_ts = BASE_TIMESTAMP
    outlap = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL

    flying1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[make_corner(1), make_corner(2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60)],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
    )
    base_ts += 200 * SAMPLE_INTERVAL

    flying2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[make_corner(1), make_corner(2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60)],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
    )
    base_ts += 200 * SAMPLE_INTERVAL

    inlap = make_lap_segment(
        lap_number=3, classification="inlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )

    parsed = make_parsed_session(
        laps=[outlap, flying1, flying2, inlap],
        setups=[SETUP_A],
    )
    return analyze_session(parsed)


# ---------------------------------------------------------------------------
# GET /knowledge/search
# ---------------------------------------------------------------------------


class TestKnowledgeSearch:
    @pytest.mark.asyncio
    async def test_search_returns_results(self, client):
        resp = await client.get("/knowledge/search", params={"q": "camber"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "camber"
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], int)
        if data["results"]:
            r = data["results"][0]
            assert "source_file" in r
            assert "section_title" in r
            assert "content" in r
            assert "tags" in r

    @pytest.mark.asyncio
    async def test_search_no_match_returns_empty(self, client):
        resp = await client.get("/knowledge/search", params={"q": "xyznonexistent9999"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_empty_query_returns_empty(self, client):
        resp = await client.get("/knowledge/search", params={"q": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == ""
        assert data["results"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_whitespace_only_returns_empty(self, client):
        resp = await client.get("/knowledge/search", params={"q": "   "})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_results_capped_at_10(self, client):
        # Use a very broad query to get many results
        resp = await client.get("/knowledge/search", params={"q": "setup"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) <= 10
        # total reflects the unfiltered count
        assert data["total"] >= len(data["results"])

    @pytest.mark.asyncio
    async def test_response_includes_query_echo(self, client):
        resp = await client.get("/knowledge/search", params={"q": "understeer"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "understeer"


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/knowledge
# ---------------------------------------------------------------------------


class TestSessionKnowledge:
    @pytest.mark.asyncio
    async def test_returns_fragments_for_analyzed_session(
        self, client, db_path, sessions_dir
    ):
        session = _session(state="analyzed")
        save_session(db_path, session)
        analyzed = _make_analyzed_session()
        cache_dir = get_cache_dir(sessions_dir, session.session_id)
        save_analyzed_session(cache_dir, analyzed)

        resp = await client.get(f"/sessions/{session.session_id}/knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session.session_id
        assert isinstance(data["signals"], list)
        assert isinstance(data["fragments"], list)

    @pytest.mark.asyncio
    async def test_returns_fragments_for_engineered_session(
        self, client, db_path, sessions_dir
    ):
        session = _session(state="engineered")
        save_session(db_path, session)
        analyzed = _make_analyzed_session()
        cache_dir = get_cache_dir(sessions_dir, session.session_id)
        save_analyzed_session(cache_dir, analyzed)

        resp = await client.get(f"/sessions/{session.session_id}/knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session.session_id

    @pytest.mark.asyncio
    async def test_404_for_nonexistent_session(self, client):
        resp = await client.get("/sessions/nonexistent_session/knowledge")
        assert resp.status_code == 404
        assert "not found" in resp.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_409_for_discovered_session(self, client, db_path):
        session = _session(state="discovered")
        save_session(db_path, session)
        resp = await client.get(f"/sessions/{session.session_id}/knowledge")
        assert resp.status_code == 409
        assert "not been analyzed" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_409_when_cache_missing(self, client, db_path):
        session = _session(state="analyzed")
        save_session(db_path, session)
        # No cache file saved
        resp = await client.get(f"/sessions/{session.session_id}/knowledge")
        assert resp.status_code == 409
        assert "re-process" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_returns_signals_list(self, client, db_path, sessions_dir):
        session = _session(state="analyzed")
        save_session(db_path, session)
        analyzed = _make_analyzed_session()
        cache_dir = get_cache_dir(sessions_dir, session.session_id)
        save_analyzed_session(cache_dir, analyzed)

        resp = await client.get(f"/sessions/{session.session_id}/knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)

    @pytest.mark.asyncio
    async def test_empty_signals_when_none_detected(
        self, client, db_path, sessions_dir
    ):
        session = _session(state="analyzed")
        save_session(db_path, session)
        analyzed = _make_analyzed_session()
        cache_dir = get_cache_dir(sessions_dir, session.session_id)
        save_analyzed_session(cache_dir, analyzed)

        with patch(
            "api.routes.knowledge.detect_signals", return_value=[]
        ), patch(
            "api.routes.knowledge.get_knowledge_for_signals", return_value=[]
        ):
            resp = await client.get(f"/sessions/{session.session_id}/knowledge")

        assert resp.status_code == 200
        data = resp.json()
        assert data["signals"] == []
        assert data["fragments"] == []
