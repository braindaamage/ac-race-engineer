"""Tests for engineer pipeline factories."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ac_engineer.config.models import ACConfig
from ac_engineer.engineer.models import (
    DriverFeedback,
    EngineerResponse,
    SessionSummary,
    SetupChange as EngSetupChange,
)
from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord, SetupChange as StorageSetupChange
from ac_engineer.storage.recommendations import save_recommendation
from ac_engineer.storage.sessions import save_session

from api.analysis.cache import get_cache_dir, save_analyzed_session
from api.engineer.cache import load_engineer_response
from api.engineer.pipeline import make_chat_job, make_engineer_job


# We need an AnalyzedSession for caching
from tests.analyzer.conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    SETUP_A,
    make_corner,
    make_lap_segment,
    make_parsed_session,
)
from ac_engineer.analyzer import analyze_session


def _make_config(tmp_path: Path) -> ACConfig:
    return ACConfig(
        ac_install_path=tmp_path / "ac",
        llm_provider="anthropic",
        llm_model="claude-sonnet-4-5",
    )


def _make_analyzed_session():
    """Build a simple AnalyzedSession with flying laps."""
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


def _setup_analyzed_cache(sessions_dir: Path, session_id: str):
    """Cache an analyzed session."""
    analyzed = _make_analyzed_session()
    cache_dir = get_cache_dir(sessions_dir, session_id)
    save_analyzed_session(cache_dir, analyzed)
    return analyzed


def _fake_engineer_response(session_id: str) -> EngineerResponse:
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
                area="braking",
                observation="Late braking in T1",
                suggestion="Brake earlier",
                corners_affected=[1],
                severity="medium",
            )
        ],
        signals_addressed=["high_understeer"],
        summary="Reduce front ARB to fix understeer.",
        explanation="Analysis shows understeer in medium-speed corners.",
        confidence="high",
    )


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


class TestMakeEngineerJob:
    @pytest.mark.asyncio
    async def test_pipeline_runs_full_cycle(self, tmp_path, db_path, sessions_dir) -> None:
        session_id = "test_session"
        config = _make_config(tmp_path)
        active_jobs: dict[str, str] = {session_id: "job123"}

        # Setup: save session and analyzed cache
        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw_m235i_racing", track="mugello",
            session_date="2026-03-05", lap_count=2, state="analyzed",
            csv_path="/path/to.csv", meta_path="/path/to.meta.json",
        ))
        _setup_analyzed_cache(sessions_dir, session_id)

        fake_response = _fake_engineer_response(session_id)

        pipeline = make_engineer_job(
            session_id=session_id,
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
            active_jobs=active_jobs,
        )

        progress_calls: list[tuple[int, str]] = []

        async def track_progress(pct: int, step: str) -> None:
            progress_calls.append((pct, step))

        with patch(
            "api.engineer.pipeline.analyze_with_engineer",
            new_callable=AsyncMock,
            return_value=fake_response,
        ):
            result = await pipeline(track_progress)

        assert result["session_id"] == session_id
        assert result["state"] == "engineered"
        assert len(progress_calls) >= 5
        # Active jobs should be cleaned up
        assert session_id not in active_jobs

    @pytest.mark.asyncio
    async def test_pipeline_caches_response(self, tmp_path, db_path, sessions_dir) -> None:
        session_id = "test_session"
        config = _make_config(tmp_path)
        active_jobs: dict[str, str] = {session_id: "job123"}

        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw_m235i_racing", track="mugello",
            session_date="2026-03-05", lap_count=2, state="analyzed",
            csv_path="/path/to.csv", meta_path="/path/to.meta.json",
        ))
        _setup_analyzed_cache(sessions_dir, session_id)

        fake_response = _fake_engineer_response(session_id)

        # Pre-save a recommendation so the pipeline can find it for caching
        save_recommendation(
            db_path, session_id, "Test summary",
            [StorageSetupChange(section="ARB", parameter="FRONT", old_value="5", new_value="3", reasoning="test")],
        )

        pipeline = make_engineer_job(
            session_id=session_id,
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
            active_jobs=active_jobs,
        )

        async def noop(pct: int, step: str) -> None:
            pass

        with patch(
            "api.engineer.pipeline.analyze_with_engineer",
            new_callable=AsyncMock,
            return_value=fake_response,
        ):
            await pipeline(noop)

        # Verify cache exists
        from ac_engineer.storage.recommendations import get_recommendations

        recs = get_recommendations(db_path, session_id)
        assert len(recs) >= 1
        # The recommendation saved by analyze_with_engineer mock won't exist,
        # but the one we pre-saved does; check cache exists for it
        cache_dir = get_cache_dir(sessions_dir, session_id)
        cached = load_engineer_response(cache_dir, recs[-1].recommendation_id)
        assert cached is not None

    @pytest.mark.asyncio
    async def test_active_jobs_cleaned_on_error(self, tmp_path, db_path, sessions_dir) -> None:
        session_id = "test_session"
        config = _make_config(tmp_path)
        active_jobs: dict[str, str] = {session_id: "job123"}

        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw_m235i_racing", track="mugello",
            session_date="2026-03-05", lap_count=2, state="analyzed",
            csv_path="/path/to.csv", meta_path="/path/to.meta.json",
        ))
        # Don't setup cache → will fail with FileNotFoundError

        pipeline = make_engineer_job(
            session_id=session_id,
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
            active_jobs=active_jobs,
        )

        async def noop(pct: int, step: str) -> None:
            pass

        with pytest.raises((FileNotFoundError, ValueError)):
            await pipeline(noop)

        # Active jobs should still be cleaned up
        assert session_id not in active_jobs


class TestMakeChatJob:
    @pytest.mark.asyncio
    async def test_chat_pipeline_saves_assistant_message(self, tmp_path, db_path, sessions_dir) -> None:
        session_id = "test_session"
        config = _make_config(tmp_path)

        save_session(db_path, SessionRecord(
            session_id=session_id, car="bmw_m235i_racing", track="mugello",
            session_date="2026-03-05", lap_count=2, state="analyzed",
            csv_path="/path/to.csv", meta_path="/path/to.meta.json",
        ))
        _setup_analyzed_cache(sessions_dir, session_id)

        # Save user message first (like the route does)
        from ac_engineer.storage.messages import save_message, get_messages

        user_msg = save_message(db_path, session_id, "user", "Why reduce ARB?")

        chat_pipeline = make_chat_job(
            session_id=session_id,
            message_id=user_msg.message_id,
            user_content="Why reduce ARB?",
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
        )

        progress_calls: list[tuple[int, str]] = []

        async def track_progress(pct: int, step: str) -> None:
            progress_calls.append((pct, step))

        # Mock the Pydantic AI Agent.run to return a fixed response
        mock_result = MagicMock()
        mock_result.output = "Because reducing the front ARB allows more front grip."

        with patch("api.engineer.pipeline.Agent") as MockAgent:
            instance = MockAgent.return_value
            instance.run = AsyncMock(return_value=mock_result)
            result = await chat_pipeline(track_progress)

        assert result["session_id"] == session_id
        assert len(progress_calls) >= 4

        # Verify assistant message was saved
        msgs = get_messages(db_path, session_id)
        assert len(msgs) == 2  # user + assistant
        assert msgs[1].role == "assistant"
        assert "front ARB" in msgs[1].content
