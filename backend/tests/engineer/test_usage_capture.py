"""Tests for usage capture logic in the engineer pipeline.

Covers:
- extract_tool_calls() helper with mocked message history
- extract_tool_calls() with no tool calls returns empty list
- Token estimation matches len(str(content)) // 4
- Full analyze_with_engineer() pipeline with FunctionModel verifying usage persistence
- Usage persistence failure does not prevent recommendation delivery
- Logging output includes expected fields
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RunUsage

from ac_engineer.config import ACConfig
from ac_engineer.engineer.agents import extract_tool_calls, analyze_with_engineer
from ac_engineer.engineer.models import (
    ParameterRange,
    SessionSummary,
    SpecialistResult,
)
from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import LlmEvent, LlmToolCall
from ac_engineer.storage.sessions import save_session
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.usage import get_llm_events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeResult:
    """Minimal result object mimicking Pydantic AI RunResult for testing."""

    def __init__(self, messages=None):
        self._messages = messages or []

    def all_messages(self):
        return self._messages


# ---------------------------------------------------------------------------
# extract_tool_calls with ToolReturnPart objects
# ---------------------------------------------------------------------------


class TestExtractToolCalls:
    def test_extracts_tool_calls_from_messages(self):
        messages = [
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name="search_kb",
                        content="Some knowledge base content here",
                        tool_call_id="call_1",
                    ),
                    ToolReturnPart(
                        tool_name="get_setup_range",
                        content="min=0, max=20",
                        tool_call_id="call_2",
                    ),
                ]
            ),
            ModelRequest(
                parts=[
                    UserPromptPart(content="next question"),
                ]
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name="get_current_value",
                        content="5.0",
                        tool_call_id="call_3",
                    ),
                ]
            ),
        ]
        fake_result = _FakeResult(messages=messages)
        tool_calls = extract_tool_calls(fake_result)

        assert len(tool_calls) == 3
        assert tool_calls[0].tool_name == "search_kb"
        assert tool_calls[1].tool_name == "get_setup_range"
        assert tool_calls[2].tool_name == "get_current_value"
        # Verify call_index ordering
        assert tool_calls[0].call_index == 0
        assert tool_calls[1].call_index == 1
        assert tool_calls[2].call_index == 2

    def test_no_tool_calls_returns_empty(self):
        messages = [
            ModelRequest(parts=[UserPromptPart(content="hello")]),
        ]
        fake_result = _FakeResult(messages=messages)
        tool_calls = extract_tool_calls(fake_result)
        assert tool_calls == []

    def test_empty_messages_returns_empty(self):
        fake_result = _FakeResult(messages=[])
        tool_calls = extract_tool_calls(fake_result)
        assert tool_calls == []

    def test_token_estimation(self):
        content = "This is a test content with some words in it"
        messages = [
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name="search_kb",
                        content=content,
                        tool_call_id="call_1",
                    ),
                ]
            ),
        ]
        fake_result = _FakeResult(messages=messages)
        tool_calls = extract_tool_calls(fake_result)

        expected_tokens = len(str(content)) // 4
        assert tool_calls[0].response_tokens == expected_tokens

    def test_token_estimation_dict_content(self):
        content = {"key": "value", "nested": {"a": 1}}
        messages = [
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name="get_setup_range",
                        content=content,
                        tool_call_id="call_1",
                    ),
                ]
            ),
        ]
        fake_result = _FakeResult(messages=messages)
        tool_calls = extract_tool_calls(fake_result)

        expected_tokens = len(str(content)) // 4
        assert tool_calls[0].response_tokens == expected_tokens

    def test_ignores_non_model_request_messages(self):
        """ModelResponse messages should not be scanned for tool returns."""
        messages = [
            ModelResponse(
                parts=[TextPart(content="I will help you")],
                usage=RunUsage(),
                model_name="test",
            ),
        ]
        fake_result = _FakeResult(messages=messages)
        tool_calls = extract_tool_calls(fake_result)
        assert tool_calls == []


# ---------------------------------------------------------------------------
# Full pipeline with FunctionModel
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.db"
    init_db(path)
    return path


@pytest.fixture
def sample_config(tmp_path: Path) -> ACConfig:
    return ACConfig(ac_install_path=tmp_path)


@pytest.fixture
def sample_summary() -> SessionSummary:
    from ac_engineer.engineer.models import LapSummary, StintSummary

    return SessionSummary(
        session_id="test_session_001",
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
        active_setup_parameters={
            "PRESSURE_LF": {"VALUE": 26.5},
        },
        laps=[
            LapSummary(lap_number=1, lap_time_s=89.5, gap_to_best_s=0.0, is_best=True),
            LapSummary(lap_number=2, lap_time_s=91.0, gap_to_best_s=1.5, is_best=False),
        ],
        signals=["high_understeer"],
        corner_issues=[],
        stints=[
            StintSummary(
                stint_index=0, flying_lap_count=2, lap_time_mean_s=90.25,
                lap_time_stddev_s=0.6, lap_time_trend="stable",
            ),
        ],
    )


def _function_model_handler(messages, info):
    """FunctionModel handler that returns a valid SpecialistResult."""
    from pydantic_ai.messages import ModelResponse, TextPart

    from ac_engineer.engineer.models import DriverFeedback

    result_json = SpecialistResult(
        domain_summary="Test analysis complete",
        setup_changes=[],
        driver_feedback=[
            DriverFeedback(
                area="balance",
                observation="Slight understeer in mid-corner",
                suggestion="Try trail braking deeper",
                severity="low",
            ),
        ],
    ).model_dump_json()

    return ModelResponse(
        parts=[TextPart(content=result_json)],
        model_name="function:test",
    )


@pytest.mark.asyncio
async def test_pipeline_persists_usage(db_path, sample_config, sample_summary):
    """Full analyze_with_engineer pipeline persists LlmEvent records."""
    save_session(
        db_path,
        SessionRecord(
            session_id="test_session_001",
            car="test_car",
            track="test_track",
            session_date="2026-03-02T14:00:00",
            lap_count=3,
            state="analyzed",
        ),
    )

    ranges = {
        "PRESSURE_LF": ParameterRange(
            section="PRESSURE_LF", parameter="VALUE",
            min_value=20.0, max_value=35.0, step=0.5,
        ),
    }

    model = FunctionModel(_function_model_handler)

    with patch(
        "ac_engineer.engineer.agents.build_model",
        return_value=model,
    ):
        response = await analyze_with_engineer(
            summary=sample_summary,
            config=sample_config,
            db_path=db_path,
            parameter_ranges=ranges,
        )

    assert response.session_id == "test_session_001"

    # Verify usage was persisted — find the recommendation_id
    from ac_engineer.storage.recommendations import get_recommendations

    recs = get_recommendations(db_path, "test_session_001")
    assert len(recs) >= 1
    rec_id = recs[0].recommendation_id

    usage_records = get_llm_events(db_path, "recommendation", rec_id)
    assert len(usage_records) >= 1

    # Check the balance agent was captured
    agent_names = [u.agent_name for u in usage_records]
    assert "balance" in agent_names

    balance_usage = next(u for u in usage_records if u.agent_name == "balance")
    assert balance_usage.event_type == "analysis"
    assert balance_usage.context_type == "recommendation"
    assert balance_usage.context_id == rec_id
    assert balance_usage.input_tokens >= 0
    assert balance_usage.output_tokens >= 0
    assert balance_usage.duration_ms >= 0
    assert balance_usage.model != ""


# ---------------------------------------------------------------------------
# Usage persistence failure does not prevent recommendation delivery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_usage_failure_does_not_block_recommendation(
    db_path, sample_config, sample_summary
):
    """If save_llm_event raises, the recommendation is still returned."""
    save_session(
        db_path,
        SessionRecord(
            session_id="test_session_001",
            car="test_car",
            track="test_track",
            session_date="2026-03-02T14:00:00",
            lap_count=3,
            state="analyzed",
        ),
    )

    ranges = {
        "PRESSURE_LF": ParameterRange(
            section="PRESSURE_LF", parameter="VALUE",
            min_value=20.0, max_value=35.0, step=0.5,
        ),
    }

    model = FunctionModel(_function_model_handler)

    with (
        patch("ac_engineer.engineer.agents.build_model", return_value=model),
        patch(
            "ac_engineer.storage.usage.save_llm_event",
            side_effect=RuntimeError("DB error"),
        ),
    ):
        response = await analyze_with_engineer(
            summary=sample_summary,
            config=sample_config,
            db_path=db_path,
            parameter_ranges=ranges,
        )

    # Recommendation should still be returned successfully
    assert response.session_id == "test_session_001"
    assert response.summary != ""


# ---------------------------------------------------------------------------
# Logging output includes expected fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logging_includes_usage_fields(
    db_path, sample_config, sample_summary, caplog
):
    """Verify logger.info is called with domain, token counts, and duration."""
    save_session(
        db_path,
        SessionRecord(
            session_id="test_session_001",
            car="test_car",
            track="test_track",
            session_date="2026-03-02T14:00:00",
            lap_count=3,
            state="analyzed",
        ),
    )

    ranges = {
        "PRESSURE_LF": ParameterRange(
            section="PRESSURE_LF", parameter="VALUE",
            min_value=20.0, max_value=35.0, step=0.5,
        ),
    }

    model = FunctionModel(_function_model_handler)

    with (
        patch("ac_engineer.engineer.agents.build_model", return_value=model),
        caplog.at_level(logging.INFO, logger="ac_engineer.engineer.agents"),
    ):
        await analyze_with_engineer(
            summary=sample_summary,
            config=sample_config,
            db_path=db_path,
            parameter_ranges=ranges,
        )

    # Check that usage logging occurred
    usage_logs = [r for r in caplog.records if "Agent usage" in r.message]
    assert len(usage_logs) >= 1

    log_msg = usage_logs[0].message
    assert "domain=balance" in log_msg
    assert "input_tokens=" in log_msg
    assert "output_tokens=" in log_msg
    assert "duration_ms=" in log_msg
