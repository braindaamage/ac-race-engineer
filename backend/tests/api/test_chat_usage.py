"""Tests for chat pipeline usage capture.

Covers:
- make_chat_job() persists LlmEvent with event_type="chat" and context_type="message"
- Usage capture failure still delivers the message
- Fallback: if AgentDeps construction fails, chat proceeds without tools
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from ac_engineer.config.models import ACConfig
from ac_engineer.storage.db import init_db
from ac_engineer.storage.messages import get_messages, save_message
from ac_engineer.storage.models import LlmEvent, SessionRecord
from ac_engineer.storage.sessions import save_session
from ac_engineer.storage.usage import get_llm_events

from api.engineer.pipeline import make_chat_job


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
    d = tmp_path / "sessions" / "test_session"
    d.mkdir(parents=True)
    return d.parent


@pytest.fixture()
def config(tmp_path: Path) -> ACConfig:
    return ACConfig(ac_install_path=tmp_path, llm_provider="anthropic")


def _setup_session(db_path, sessions_dir):
    """Create a session and the necessary cache files."""
    save_session(
        db_path,
        SessionRecord(
            session_id="test_session",
            car="test_car",
            track="test_track",
            session_date="2026-03-02T14:00:00",
            lap_count=5,
            state="analyzed",
        ),
    )
    # Save user message first (as the route does)
    save_message(db_path, "test_session", "user", "What about Turn 3?")


def _chat_model_handler(messages, info):
    """FunctionModel handler that returns a plain text response."""
    return ModelResponse(
        parts=[TextPart(content="Turn 3 shows understeer in entry phase.")],
        model_name="function:test",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_persists_usage_event(db_path, sessions_dir, config):
    """make_chat_job persists an LlmEvent with event_type='chat' after agent.run()."""
    _setup_session(db_path, sessions_dir)
    user_msg = save_message(db_path, "test_session", "user", "Tell me about Turn 3")
    model = FunctionModel(_chat_model_handler)

    with (
        patch("api.engineer.pipeline.build_model", return_value=model),
        patch("api.engineer.pipeline.load_analyzed_session", return_value={}),
        patch("api.engineer.pipeline.summarize_session", return_value=_minimal_summary()),
        patch("api.engineer.pipeline.resolve_parameters", side_effect=RuntimeError("No car data")),
    ):
        pipeline = make_chat_job(
            session_id="test_session",
            message_id=user_msg.message_id,
            user_content="Tell me about Turn 3",
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
        )
        await pipeline(AsyncMock())

    # Find the assistant message that was saved
    msgs = get_messages(db_path, "test_session")
    assistant_msgs = [m for m in msgs if m.role == "assistant"]
    assert len(assistant_msgs) >= 1

    # Check usage was persisted for the assistant message
    for amsg in assistant_msgs:
        events = get_llm_events(db_path, "message", amsg.message_id)
        if events:
            assert events[0].event_type == "chat"
            assert events[0].agent_name == "principal"
            assert events[0].context_type == "message"
            assert events[0].context_id == amsg.message_id
            break
    else:
        pytest.fail("No LlmEvent found for any assistant message")


@pytest.mark.asyncio
async def test_chat_usage_failure_still_delivers_message(db_path, sessions_dir, config):
    """If save_llm_event raises, the assistant message is still saved."""
    _setup_session(db_path, sessions_dir)
    user_msg = save_message(db_path, "test_session", "user", "Hello")
    model = FunctionModel(_chat_model_handler)

    with (
        patch("api.engineer.pipeline.build_model", return_value=model),
        patch("api.engineer.pipeline.load_analyzed_session", return_value={}),
        patch("api.engineer.pipeline.summarize_session", return_value=_minimal_summary()),
        patch("api.engineer.pipeline.resolve_parameters", side_effect=RuntimeError("No car")),
        patch("api.engineer.pipeline.save_llm_event", side_effect=RuntimeError("DB error")),
    ):
        pipeline = make_chat_job(
            session_id="test_session",
            message_id=user_msg.message_id,
            user_content="Hello",
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
        )
        result = await pipeline(AsyncMock())

    # Message should still be delivered
    msgs = get_messages(db_path, "test_session")
    assistant_msgs = [m for m in msgs if m.role == "assistant"]
    assert len(assistant_msgs) >= 1
    assert result["session_id"] == "test_session"


@pytest.mark.asyncio
async def test_chat_fallback_without_tools(db_path, sessions_dir, config):
    """If AgentDeps construction fails, chat proceeds without tools."""
    _setup_session(db_path, sessions_dir)
    user_msg = save_message(db_path, "test_session", "user", "Quick question")
    model = FunctionModel(_chat_model_handler)

    with (
        patch("api.engineer.pipeline.build_model", return_value=model),
        patch("api.engineer.pipeline.load_analyzed_session", return_value={}),
        patch("api.engineer.pipeline.summarize_session", return_value=_minimal_summary()),
        patch("api.engineer.pipeline.resolve_parameters", side_effect=RuntimeError("No resolver")),
    ):
        pipeline = make_chat_job(
            session_id="test_session",
            message_id=user_msg.message_id,
            user_content="Quick question",
            sessions_dir=sessions_dir,
            db_path=db_path,
            config=config,
        )
        result = await pipeline(AsyncMock())

    # Chat should succeed even without tools
    msgs = get_messages(db_path, "test_session")
    assistant_msgs = [m for m in msgs if m.role == "assistant"]
    assert len(assistant_msgs) >= 1
    assert "Turn 3" in assistant_msgs[-1].content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_summary():
    """Return a minimal SessionSummary for testing."""
    from ac_engineer.engineer.models import SessionSummary, LapSummary, StintSummary

    return SessionSummary(
        session_id="test_session",
        car_name="test_car",
        track_name="test_track",
        track_config="default",
        recorded_at="2026-03-02T14:00:00",
        total_lap_count=3,
        flying_lap_count=2,
        best_lap_time_s=89.5,
        worst_lap_time_s=91.0,
        lap_time_stddev_s=0.6,
        avg_understeer_ratio=1.2,
        active_setup_filename="race_setup.ini",
        active_setup_parameters={},
        laps=[
            LapSummary(lap_number=1, lap_time_s=89.5, gap_to_best_s=0.0, is_best=True),
        ],
        signals=[],
        corner_issues=[],
        stints=[
            StintSummary(
                stint_index=0, flying_lap_count=2, lap_time_mean_s=90.25,
                lap_time_stddev_s=0.6, lap_time_trend="stable",
            ),
        ],
    )
