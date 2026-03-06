"""Tests for analysis route endpoints."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
import httpx

from ac_engineer.analyzer import analyze_session
from ac_engineer.analyzer.models import AnalyzedSession
from ac_engineer.parser.cache import save_session as save_parsed_session
from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import save_session

from api.analysis.cache import save_analyzed_session, get_cache_dir
from api.jobs.manager import JobManager
from api.main import create_app

from tests.analyzer.conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    SETUP_A,
    SETUP_B,
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
def app(db_path: Path, sessions_dir: Path):
    a = create_app()
    a.state.db_path = db_path
    a.state.sessions_dir = sessions_dir
    a.state.job_manager = JobManager()
    a.state.active_processing_jobs = {}
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


def _make_multi_lap_analyzed() -> AnalyzedSession:
    """Build an AnalyzedSession: outlap + 2 flying (with corners) + inlap."""
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


def _make_two_stint_analyzed() -> AnalyzedSession:
    """Build an AnalyzedSession with 2 stints for comparison tests."""
    base_ts = BASE_TIMESTAMP

    lap0 = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL

    lap1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        speed=130.0, fuel_start=50.0, fuel_end=48.5,
        corners=[make_corner(1)],
    )
    base_ts += 200 * SAMPLE_INTERVAL

    lap2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_B,
        speed=125.0, fuel_start=45.0, fuel_end=43.0,
        corners=[make_corner(1)],
    )
    base_ts += 200 * SAMPLE_INTERVAL

    lap3 = make_lap_segment(
        lap_number=3, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_B,
        speed=126.0, fuel_start=43.0, fuel_end=41.0,
        corners=[make_corner(1)],
    )

    parsed = make_parsed_session(
        laps=[lap0, lap1, lap2, lap3],
        setups=[SETUP_A, SETUP_B],
    )
    return analyze_session(parsed)


def _setup_analyzed_session(
    db_path: Path, sessions_dir: Path, analyzed: AnalyzedSession, session_id: str = "test_session"
) -> None:
    """Save a session record in 'analyzed' state and cache the analyzed data."""
    save_session(db_path, _session(session_id=session_id))
    cache_dir = get_cache_dir(sessions_dir, session_id)
    save_analyzed_session(cache_dir, analyzed)


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/process
# ---------------------------------------------------------------------------


class TestProcessEndpoint:
    @pytest.mark.asyncio
    async def test_process_returns_202(self, client, db_path, sessions_dir) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.post("/sessions/test_session/process")
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["session_id"] == "test_session"

    @pytest.mark.asyncio
    async def test_process_404_nonexistent(self, client) -> None:
        resp = await client.post("/sessions/nonexistent/process")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_process_409_already_running(self, client, db_path, app) -> None:
        save_session(db_path, _session(state="discovered"))
        app.state.active_processing_jobs["test_session"] = "existing_job"
        resp = await client.post("/sessions/test_session/process")
        assert resp.status_code == 409
        assert "already in progress" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_409_missing_paths(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered", csv_path=None, meta_path=None))
        resp = await client.post("/sessions/test_session/process")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps
# ---------------------------------------------------------------------------


class TestLapEndpoints:
    @pytest.mark.asyncio
    async def test_list_laps_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session"
        assert data["lap_count"] == 4
        assert len(data["laps"]) == 4

    @pytest.mark.asyncio
    async def test_lap_detail_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lap_number"] == 1
        assert data["classification"] == "flying"
        assert "metrics" in data
        assert "timing" in data["metrics"]

    @pytest.mark.asyncio
    async def test_lap_detail_404_nonexistent_lap(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps/999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_laps_404_nonexistent_session(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/laps")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_laps_409_discovered_state(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.get("/sessions/test_session/laps")
        assert resp.status_code == 409
        assert "not been analyzed" in resp.json()["error"]["message"]


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/corners
# ---------------------------------------------------------------------------


class TestCornerEndpoints:
    @pytest.mark.asyncio
    async def test_list_corners_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/corners")
        assert resp.status_code == 200
        data = resp.json()
        assert data["corner_count"] == 2
        assert data["corners"][0]["corner_number"] == 1
        assert data["corners"][0]["sample_count"] == 2

    @pytest.mark.asyncio
    async def test_corner_detail_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/corners/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["corner_number"] == 1
        assert len(data["laps"]) >= 2

    @pytest.mark.asyncio
    async def test_corner_detail_404_nonexistent(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/corners/999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_corners_empty_session(self, client, db_path, sessions_dir) -> None:
        lap = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            active_setup=SETUP_A, corners=[],
        )
        parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/corners")
        assert resp.status_code == 200
        assert resp.json()["corner_count"] == 0

    @pytest.mark.asyncio
    async def test_corners_409_guard(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.get("/sessions/test_session/corners")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/stints
# ---------------------------------------------------------------------------


class TestStintEndpoints:
    @pytest.mark.asyncio
    async def test_list_stints_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_two_stint_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/stints")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stint_count"] >= 1
        assert len(data["stints"]) >= 1

    @pytest.mark.asyncio
    async def test_stints_404_guard(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/stints")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_stints_409_guard(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.get("/sessions/test_session/stints")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/compare
# ---------------------------------------------------------------------------


class TestCompareEndpoints:
    @pytest.mark.asyncio
    async def test_compare_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_two_stint_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)

        # Find available comparison indices
        if analyzed.stint_comparisons:
            comp = analyzed.stint_comparisons[0]
            resp = await client.get(
                f"/sessions/test_session/compare?stint_a={comp.stint_a_index}&stint_b={comp.stint_b_index}"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "comparison" in data

    @pytest.mark.asyncio
    async def test_compare_404_nonexistent_stint(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_two_stint_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/compare?stint_a=0&stint_b=99")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_compare_422_missing_params(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_two_stint_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/compare")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_compare_single_stint_404(self, client, db_path, sessions_dir) -> None:
        # Single stint session — no comparisons available
        lap = make_lap_segment(
            lap_number=1, classification="flying", n_samples=200,
            active_setup=SETUP_A,
        )
        parsed = make_parsed_session(laps=[lap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/compare?stint_a=0&stint_b=1")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/consistency
# ---------------------------------------------------------------------------


class TestConsistencyEndpoint:
    @pytest.mark.asyncio
    async def test_consistency_200(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/consistency")
        assert resp.status_code == 200
        data = resp.json()
        assert "consistency" in data
        assert data["consistency"]["flying_lap_count"] >= 0

    @pytest.mark.asyncio
    async def test_consistency_no_flying_laps(self, client, db_path, sessions_dir) -> None:
        outlap = make_lap_segment(
            lap_number=0, classification="outlap", n_samples=100,
            active_setup=SETUP_A,
        )
        parsed = make_parsed_session(laps=[outlap], setups=[SETUP_A])
        analyzed = analyze_session(parsed)
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/consistency")
        assert resp.status_code == 200
        data = resp.json()
        assert data["consistency"]["flying_lap_count"] == 0

    @pytest.mark.asyncio
    async def test_consistency_404_guard(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/consistency")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_consistency_409_guard(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.get("/sessions/test_session/consistency")
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Extended field tests (Phase 7.4)
# ---------------------------------------------------------------------------


class TestLapSummaryExtendedFields:
    @pytest.mark.asyncio
    async def test_lap_summary_includes_max_speed(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps")
        assert resp.status_code == 200
        for lap in resp.json()["laps"]:
            assert "max_speed" in lap
            assert isinstance(lap["max_speed"], (int, float))

    @pytest.mark.asyncio
    async def test_lap_summary_includes_sector_times(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps")
        assert resp.status_code == 200
        for lap in resp.json()["laps"]:
            assert "sector_times_s" in lap
            # sector_times_s may be null or a list
            if lap["sector_times_s"] is not None:
                assert isinstance(lap["sector_times_s"], list)


class TestLapDetailCorners:
    @pytest.mark.asyncio
    async def test_lap_detail_includes_corners(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "corners" in data
        assert isinstance(data["corners"], list)
        assert len(data["corners"]) == 2  # flying lap 1 has 2 corners

    @pytest.mark.asyncio
    async def test_lap_detail_corners_structure(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps/1")
        corner = resp.json()["corners"][0]
        assert "corner_number" in corner
        assert "performance" in corner
        assert "grip" in corner
        assert "technique" in corner
        assert "entry_speed_kmh" in corner["performance"]
        assert "understeer_ratio" in corner["grip"]

    @pytest.mark.asyncio
    async def test_lap_detail_no_corners_for_outlap(self, client, db_path, sessions_dir) -> None:
        analyzed = _make_multi_lap_analyzed()
        _setup_analyzed_session(db_path, sessions_dir, analyzed)
        resp = await client.get("/sessions/test_session/laps/0")
        assert resp.status_code == 200
        assert resp.json()["corners"] == []


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/laps/{lap_number}/telemetry
# ---------------------------------------------------------------------------


def _setup_with_parquet(
    db_path: Path,
    sessions_dir: Path,
    session_id: str = "test_session",
) -> AnalyzedSession:
    """Save session record, parsed parquet, and analyzed cache."""
    analyzed_data = _make_multi_lap_analyzed()
    save_session(db_path, _session(session_id=session_id))
    cache_dir = get_cache_dir(sessions_dir, session_id)

    # Save analyzed.json
    save_analyzed_session(cache_dir, analyzed_data)

    # Build a ParsedSession and save parquet
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
    save_parsed_session(parsed, cache_dir)
    return analyzed_data


class TestTelemetryEndpoint:
    @pytest.mark.asyncio
    async def test_telemetry_200(self, client, db_path, sessions_dir) -> None:
        _setup_with_parquet(db_path, sessions_dir)
        resp = await client.get("/sessions/test_session/laps/1/telemetry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session"
        assert data["lap_number"] == 1
        assert data["sample_count"] > 0
        channels = data["channels"]
        assert "normalized_position" in channels
        assert "throttle" in channels
        assert "brake" in channels
        assert "steering" in channels
        assert "speed_kmh" in channels
        assert "gear" in channels

    @pytest.mark.asyncio
    async def test_telemetry_channels_same_length(self, client, db_path, sessions_dir) -> None:
        _setup_with_parquet(db_path, sessions_dir)
        resp = await client.get("/sessions/test_session/laps/1/telemetry")
        channels = resp.json()["channels"]
        lengths = {len(v) for v in channels.values()}
        assert len(lengths) == 1  # all channels same length

    @pytest.mark.asyncio
    async def test_telemetry_downsample(self, client, db_path, sessions_dir) -> None:
        _setup_with_parquet(db_path, sessions_dir)
        resp = await client.get("/sessions/test_session/laps/1/telemetry?max_samples=50")
        assert resp.status_code == 200
        assert resp.json()["sample_count"] == 50

    @pytest.mark.asyncio
    async def test_telemetry_no_downsample(self, client, db_path, sessions_dir) -> None:
        _setup_with_parquet(db_path, sessions_dir)
        resp = await client.get("/sessions/test_session/laps/1/telemetry?max_samples=0")
        assert resp.status_code == 200
        assert resp.json()["sample_count"] == 200  # flying lap has 200 samples

    @pytest.mark.asyncio
    async def test_telemetry_404_invalid_lap(self, client, db_path, sessions_dir) -> None:
        _setup_with_parquet(db_path, sessions_dir)
        resp = await client.get("/sessions/test_session/laps/999/telemetry")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_telemetry_409_unanalyzed_session(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.get("/sessions/test_session/laps/1/telemetry")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_telemetry_404_nonexistent_session(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/laps/1/telemetry")
        assert resp.status_code == 404
