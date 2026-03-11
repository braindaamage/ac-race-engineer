"""Tests for engineer route endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import httpx

from ac_engineer.engineer.models import EngineerResponse
from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import (
    Message,
    Recommendation,
    SessionRecord,
    SetupChange as StorageSetupChange,
)
from ac_engineer.storage.messages import get_messages, save_message
from ac_engineer.storage.recommendations import (
    get_recommendations,
    save_recommendation,
    update_recommendation_status,
)
from ac_engineer.storage.sessions import save_session

from api.analysis.cache import get_cache_dir, save_analyzed_session
from api.engineer.cache import save_engineer_response
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
from ac_engineer.analyzer import analyze_session


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


def _make_analyzed_session():
    base_ts = BASE_TIMESTAMP
    outlap = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL
    flying = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[make_corner(1)],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
    )
    parsed = make_parsed_session(laps=[outlap, flying], setups=[SETUP_A])
    return analyze_session(parsed)


def _setup_analyzed_session(db_path, sessions_dir, session_id="test_session"):
    save_session(db_path, _session(session_id=session_id))
    analyzed = _make_analyzed_session()
    cache_dir = get_cache_dir(sessions_dir, session_id)
    save_analyzed_session(cache_dir, analyzed)


def _fake_engineer_response(session_id: str) -> EngineerResponse:
    from ac_engineer.engineer.models import (
        DriverFeedback,
        SetupChange as EngSetupChange,
    )
    return EngineerResponse(
        session_id=session_id,
        setup_changes=[
            EngSetupChange(
                section="ARB", parameter="FRONT",
                value_before=5.0, value_after=3.0,
                reasoning="Reduce understeer",
                expected_effect="Better turn-in",
                confidence="high",
            )
        ],
        driver_feedback=[
            DriverFeedback(
                area="braking", observation="Late braking",
                suggestion="Brake earlier", corners_affected=[1],
                severity="medium",
            )
        ],
        signals_addressed=["high_understeer"],
        summary="Fix understeer",
        explanation="Detailed explanation",
        confidence="high",
    )


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/engineer
# ---------------------------------------------------------------------------


class TestRunEngineerEndpoint:
    @pytest.mark.asyncio
    async def test_returns_202_on_analyzed_session(self, client, db_path, sessions_dir) -> None:
        _setup_analyzed_session(db_path, sessions_dir)
        resp = await client.post("/sessions/test_session/engineer")
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["session_id"] == "test_session"

    @pytest.mark.asyncio
    async def test_404_nonexistent_session(self, client) -> None:
        resp = await client.post("/sessions/nonexistent/engineer")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_409_discovered_session(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.post("/sessions/test_session/engineer")
        assert resp.status_code == 409
        assert "not been analyzed" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_409_parsed_session(self, client, db_path) -> None:
        save_session(db_path, _session(state="parsed"))
        resp = await client.post("/sessions/test_session/engineer")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_409_already_running(self, client, db_path, sessions_dir, app) -> None:
        _setup_analyzed_session(db_path, sessions_dir)
        app.state.active_engineer_jobs["test_session"] = "existing_job"
        resp = await client.post("/sessions/test_session/engineer")
        assert resp.status_code == 409
        assert "already running" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_rerun_on_engineered_session(self, client, db_path, sessions_dir) -> None:
        save_session(db_path, _session(state="engineered"))
        analyzed = _make_analyzed_session()
        cache_dir = get_cache_dir(sessions_dir, "test_session")
        save_analyzed_session(cache_dir, analyzed)
        resp = await client.post("/sessions/test_session/engineer")
        assert resp.status_code == 202


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations
# ---------------------------------------------------------------------------


class TestListRecommendationsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.get("/sessions/test_session/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session"
        assert data["recommendations"] == []

    @pytest.mark.asyncio
    async def test_returns_recommendations(self, client, db_path) -> None:
        save_session(db_path, _session())
        save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )
        resp = await client.get("/sessions/test_session/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["change_count"] == 1
        assert data["recommendations"][0]["status"] == "proposed"

    @pytest.mark.asyncio
    async def test_404_nonexistent_session(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/recommendations")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/recommendations/{recommendation_id}
# ---------------------------------------------------------------------------


class TestRecommendationDetailEndpoint:
    @pytest.mark.asyncio
    async def test_detail_with_cache(self, client, db_path, sessions_dir) -> None:
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )
        # Cache the full EngineerResponse
        cache_dir = get_cache_dir(sessions_dir, "test_session")
        save_engineer_response(cache_dir, rec.recommendation_id, _fake_engineer_response("test_session"))

        resp = await client.get(f"/sessions/test_session/recommendations/{rec.recommendation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"] == "Detailed explanation"
        assert data["confidence"] == "high"
        assert len(data["setup_changes"]) == 1
        assert data["setup_changes"][0]["expected_effect"] == "Better turn-in"
        assert len(data["driver_feedback"]) == 1
        assert data["driver_feedback"][0]["area"] == "braking"
        assert data["signals_addressed"] == ["high_understeer"]

    @pytest.mark.asyncio
    async def test_detail_without_cache_fallback(self, client, db_path) -> None:
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )
        resp = await client.get(f"/sessions/test_session/recommendations/{rec.recommendation_id}")
        assert resp.status_code == 200
        data = resp.json()
        # Fallback: no explanation, default confidence
        assert data["explanation"] == ""
        assert data["confidence"] == "medium"
        assert len(data["setup_changes"]) == 1
        assert data["driver_feedback"] == []

    @pytest.mark.asyncio
    async def test_404_nonexistent_recommendation(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.get("/sessions/test_session/recommendations/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_404_nonexistent_session(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/recommendations/abc")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_explanation_from_db_when_cache_missing(self, client, db_path) -> None:
        """When JSON cache is missing, explanation is returned from DB."""
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
            explanation="Narrative explanation from principal agent.",
        )
        resp = await client.get(f"/sessions/test_session/recommendations/{rec.recommendation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"] == "Narrative explanation from principal agent."

    @pytest.mark.asyncio
    async def test_explanation_from_db_with_cache(self, client, db_path, sessions_dir) -> None:
        """When cache is available, explanation comes from DB (durable source)."""
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
            explanation="DB explanation text.",
        )
        cache_dir = get_cache_dir(sessions_dir, "test_session")
        save_engineer_response(cache_dir, rec.recommendation_id, _fake_engineer_response("test_session"))
        resp = await client.get(f"/sessions/test_session/recommendations/{rec.recommendation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"] == "DB explanation text."

    @pytest.mark.asyncio
    async def test_legacy_recommendation_empty_explanation(self, client, db_path) -> None:
        """Legacy recommendations (pre-migration) return explanation as empty string."""
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Old summary",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )
        resp = await client.get(f"/sessions/test_session/recommendations/{rec.recommendation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"] == ""


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/recommendations/{recommendation_id}/apply
# ---------------------------------------------------------------------------


class TestApplyRecommendationEndpoint:
    @pytest.mark.asyncio
    async def test_successful_apply(self, client, db_path, tmp_path) -> None:
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )

        # Create a real .ini file
        setup_file = tmp_path / "setup.ini"
        setup_file.write_text("[ARB]\nFRONT=5\n", encoding="utf-8")

        from ac_engineer.engineer.models import ChangeOutcome

        mock_outcomes = [
            ChangeOutcome(section="ARB", parameter="FRONT", old_value="5", new_value="3")
        ]

        with patch(
            "api.routes.engineer.apply_recommendation",
            new_callable=AsyncMock,
            return_value=mock_outcomes,
        ):
            resp = await client.post(
                f"/sessions/test_session/recommendations/{rec.recommendation_id}/apply",
                json={"setup_path": str(setup_file)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["recommendation_id"] == rec.recommendation_id
        assert data["status"] == "applied"
        assert data["changes_applied"] == 1

    @pytest.mark.asyncio
    async def test_409_already_applied(self, client, db_path, tmp_path) -> None:
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )
        update_recommendation_status(db_path, rec.recommendation_id, "applied")

        setup_file = tmp_path / "setup.ini"
        setup_file.write_text("[ARB]\nFRONT=5\n", encoding="utf-8")

        resp = await client.post(
            f"/sessions/test_session/recommendations/{rec.recommendation_id}/apply",
            json={"setup_path": str(setup_file)},
        )
        assert resp.status_code == 409
        assert "already applied" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_404_nonexistent_recommendation(self, client, db_path, tmp_path) -> None:
        save_session(db_path, _session())
        setup_file = tmp_path / "setup.ini"
        setup_file.write_text("[ARB]\nFRONT=5\n", encoding="utf-8")

        resp = await client.post(
            "/sessions/test_session/recommendations/nonexistent/apply",
            json={"setup_path": str(setup_file)},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_400_nonexistent_setup_path(self, client, db_path, tmp_path) -> None:
        save_session(db_path, _session())
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )

        resp = await client.post(
            f"/sessions/test_session/recommendations/{rec.recommendation_id}/apply",
            json={"setup_path": str(tmp_path / "nonexistent.ini")},
        )
        assert resp.status_code == 400
        assert "not found" in resp.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_apply_auto_resolves_setup_path(self, client, db_path, tmp_path, config_path) -> None:
        """Empty setup_path auto-resolves from session meta.json and config."""
        setups_dir = tmp_path / "setups"
        car_track_dir = setups_dir / "bmw_m235i_racing" / "mugello"
        car_track_dir.mkdir(parents=True)
        setup_file = car_track_dir / "my_setup.ini"
        setup_file.write_text("[ARB]\nFRONT=5\n", encoding="utf-8")

        # Write config with setups_path
        config_path.write_text(json.dumps({
            "llm_provider": "anthropic",
            "setups_path": str(setups_dir),
        }), encoding="utf-8")

        # Create meta.json with setup_history
        meta_file = tmp_path / "session.meta.json"
        meta_file.write_text(json.dumps({
            "setup_history": [
                {"trigger": "session_start", "filename": "my_setup.ini", "lap": 0},
            ],
            "track_name": "mugello",
        }), encoding="utf-8")

        save_session(db_path, _session(meta_path=str(meta_file)))
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )

        from ac_engineer.engineer.models import ChangeOutcome
        mock_outcomes = [
            ChangeOutcome(section="ARB", parameter="FRONT", old_value="5", new_value="3")
        ]

        with patch(
            "api.routes.engineer.apply_recommendation",
            new_callable=AsyncMock,
            return_value=mock_outcomes,
        ):
            resp = await client.post(
                f"/sessions/test_session/recommendations/{rec.recommendation_id}/apply",
                json={"setup_path": ""},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "applied"
        assert data["changes_applied"] == 1

    @pytest.mark.asyncio
    async def test_apply_no_setup_history_returns_400(self, client, db_path, tmp_path, config_path) -> None:
        """Empty setup_path with empty setup_history returns 400."""
        setups_dir = tmp_path / "setups"
        setups_dir.mkdir()

        config_path.write_text(json.dumps({
            "llm_provider": "anthropic",
            "setups_path": str(setups_dir),
        }), encoding="utf-8")

        # Create meta.json with empty setup_history
        meta_file = tmp_path / "session.meta.json"
        meta_file.write_text(json.dumps({
            "setup_history": [],
            "track_name": "mugello",
        }), encoding="utf-8")

        save_session(db_path, _session(meta_path=str(meta_file)))
        rec = save_recommendation(
            db_path, "test_session", "Fix understeer",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )

        resp = await client.post(
            f"/sessions/test_session/recommendations/{rec.recommendation_id}/apply",
            json={"setup_path": ""},
        )
        assert resp.status_code == 400
        assert "No setup file found" in resp.json()["error"]["message"]


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


class TestMessageEndpoints:
    @pytest.mark.asyncio
    async def test_get_messages_empty(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.get("/sessions/test_session/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session"
        assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_messages_chronological(self, client, db_path) -> None:
        save_session(db_path, _session())
        save_message(db_path, "test_session", "user", "Hello")
        save_message(db_path, "test_session", "assistant", "Hi there")

        resp = await client.get("/sessions/test_session/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_messages_404(self, client) -> None:
        resp = await client.get("/sessions/nonexistent/messages")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


class TestSendMessageEndpoint:
    @pytest.mark.asyncio
    async def test_returns_202(self, client, db_path, sessions_dir) -> None:
        _setup_analyzed_session(db_path, sessions_dir)
        resp = await client.post(
            "/sessions/test_session/messages",
            json={"content": "Why reduce ARB?"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert "message_id" in data

    @pytest.mark.asyncio
    async def test_saves_user_message_immediately(self, client, db_path, sessions_dir) -> None:
        _setup_analyzed_session(db_path, sessions_dir)
        resp = await client.post(
            "/sessions/test_session/messages",
            json={"content": "Test message"},
        )
        assert resp.status_code == 202

        msgs = get_messages(db_path, "test_session")
        assert len(msgs) >= 1
        assert msgs[0].role == "user"
        assert msgs[0].content == "Test message"

    @pytest.mark.asyncio
    async def test_404_nonexistent_session(self, client) -> None:
        resp = await client.post(
            "/sessions/nonexistent/messages",
            json={"content": "Hello"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_409_non_analyzed_session(self, client, db_path) -> None:
        save_session(db_path, _session(state="discovered"))
        resp = await client.post(
            "/sessions/test_session/messages",
            json={"content": "Hello"},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}/messages
# ---------------------------------------------------------------------------


class TestDeleteMessagesEndpoint:
    @pytest.mark.asyncio
    async def test_clears_messages(self, client, db_path) -> None:
        save_session(db_path, _session())
        save_message(db_path, "test_session", "user", "Hello")
        save_message(db_path, "test_session", "assistant", "Hi")

        resp = await client.delete("/sessions/test_session/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "test_session"
        assert data["deleted_count"] == 2

        # Verify messages actually cleared
        msgs = get_messages(db_path, "test_session")
        assert len(msgs) == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_empty(self, client, db_path) -> None:
        save_session(db_path, _session())
        resp = await client.delete("/sessions/test_session/messages")
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 0

    @pytest.mark.asyncio
    async def test_404_nonexistent_session(self, client) -> None:
        resp = await client.delete("/sessions/nonexistent/messages")
        assert resp.status_code == 404
