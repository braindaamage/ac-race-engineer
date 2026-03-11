"""Tests for agent diagnostic trace serialization and I/O."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

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

from ac_engineer.engineer.trace import (
    format_trace_markdown,
    read_trace,
    serialize_agent_trace,
    write_trace,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_result(messages: list, output=None) -> MagicMock:
    """Build a mock Pydantic AI result with ``all_messages()`` and ``output``."""
    result = MagicMock()
    result.all_messages.return_value = messages
    result.output = output
    return result


# ---------------------------------------------------------------------------
# serialize_agent_trace
# ---------------------------------------------------------------------------


class TestSerializeAgentTrace:
    def test_basic_text_response(self) -> None:
        messages = [
            ModelRequest(parts=[
                SystemPromptPart(content="system"),
                UserPromptPart(content="user"),
            ]),
            ModelResponse(parts=[
                TextPart(content="Hello, I can help with that."),
            ]),
        ]
        result = _make_mock_result(messages)

        trace = serialize_agent_trace("balance", "sys prompt", "user prompt", result)

        assert trace["domain"] == "balance"
        assert trace["system_prompt"] == "sys prompt"
        assert trace["user_prompt"] == "user prompt"
        assert len(trace["messages"]) == 1
        assert trace["messages"][0]["role"] == "assistant"
        assert trace["messages"][0]["content"] == "Hello, I can help with that."

    def test_tool_call_and_response(self) -> None:
        messages = [
            ModelRequest(parts=[UserPromptPart(content="user")]),
            ModelResponse(parts=[
                ToolCallPart(
                    tool_name="get_setup_range",
                    args={"section": "SPRING_RATE_LF"},
                    tool_call_id="tc-1",
                ),
            ]),
            ModelRequest(parts=[
                ToolReturnPart(
                    tool_name="get_setup_range",
                    content='{"min": 80000, "max": 200000}',
                    tool_call_id="tc-1",
                ),
            ]),
            ModelResponse(parts=[
                TextPart(content="Based on the range..."),
            ]),
        ]
        result = _make_mock_result(messages)

        trace = serialize_agent_trace("tyre", "sys", "usr", result)

        assert len(trace["messages"]) == 3
        assert trace["messages"][0]["role"] == "tool_call"
        assert trace["messages"][0]["tool_name"] == "get_setup_range"
        assert "SPRING_RATE_LF" in trace["messages"][0]["content"]
        assert trace["messages"][1]["role"] == "tool_response"
        assert trace["messages"][1]["tool_name"] == "get_setup_range"
        assert trace["messages"][2]["role"] == "assistant"

    def test_structured_output_with_model_dump(self) -> None:
        output = MagicMock()
        output.model_dump.return_value = {"setup_changes": [], "driver_feedback": []}

        messages = [
            ModelResponse(parts=[TextPart(content="done")]),
        ]
        result = _make_mock_result(messages, output=output)

        trace = serialize_agent_trace("aero", "sys", "usr", result)

        assert trace["structured_output"] == {"setup_changes": [], "driver_feedback": []}

    def test_no_structured_output(self) -> None:
        messages = [
            ModelResponse(parts=[TextPart(content="reply")]),
        ]
        result = _make_mock_result(messages, output="plain string")

        trace = serialize_agent_trace("principal", "sys", "usr", result)

        # Plain string has no model_dump
        assert trace["structured_output"] is None

    def test_tool_return_with_non_string_content(self) -> None:
        messages = [
            ModelRequest(parts=[
                ToolReturnPart(
                    tool_name="search_kb",
                    content={"results": ["fragment1"]},
                    tool_call_id="tc-2",
                ),
            ]),
        ]
        result = _make_mock_result(messages)

        trace = serialize_agent_trace("balance", "sys", "usr", result)

        assert len(trace["messages"]) == 1
        assert trace["messages"][0]["role"] == "tool_response"
        assert "fragment1" in trace["messages"][0]["content"]

    def test_tool_call_with_dict_args(self) -> None:
        messages = [
            ModelResponse(parts=[
                ToolCallPart(
                    tool_name="get_lap_detail",
                    args={"lap_number": 3},
                    tool_call_id="tc-3",
                ),
            ]),
        ]
        result = _make_mock_result(messages)

        trace = serialize_agent_trace("technique", "sys", "usr", result)

        assert trace["messages"][0]["role"] == "tool_call"
        assert "3" in trace["messages"][0]["content"]


# ---------------------------------------------------------------------------
# format_trace_markdown
# ---------------------------------------------------------------------------


class TestFormatTraceMarkdown:
    def test_contains_expected_headings(self) -> None:
        agent_traces = [{
            "domain": "balance",
            "system_prompt": "You are a specialist.",
            "user_prompt": "Analyze this.",
            "messages": [
                {"role": "assistant", "content": "Analysis done.", "tool_name": None, "tool_call_id": None},
            ],
            "structured_output": None,
        }]

        md = format_trace_markdown(
            "sess-1", "recommendation", "rec-1", agent_traces,
            timestamp=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert "# Diagnostic Trace: recommendation" in md
        assert "**ID**: rec-1" in md
        assert "**Session**: sess-1" in md
        assert "## Agent: balance" in md
        assert "### System Prompt" in md
        assert "### User Prompt" in md
        assert "### Conversation" in md
        assert "#### Assistant" in md
        assert "Analysis done." in md

    def test_tool_call_formatted_as_json_block(self) -> None:
        agent_traces = [{
            "domain": "tyre",
            "system_prompt": "sys",
            "user_prompt": "usr",
            "messages": [
                {"role": "tool_call", "content": '{"section": "PRESSURE_LF"}', "tool_name": "get_setup_range", "tool_call_id": "tc-1"},
                {"role": "tool_response", "content": '{"min": 20}', "tool_name": "get_setup_range", "tool_call_id": "tc-1"},
            ],
            "structured_output": None,
        }]

        md = format_trace_markdown("sess-1", "recommendation", "rec-1", agent_traces)

        assert "#### Tool Call: get_setup_range" in md
        assert "```json" in md
        assert "#### Tool Response: get_setup_range" in md

    def test_structured_output_rendered(self) -> None:
        agent_traces = [{
            "domain": "aero",
            "system_prompt": "sys",
            "user_prompt": "usr",
            "messages": [],
            "structured_output": {"setup_changes": [{"section": "WING_1"}]},
        }]

        md = format_trace_markdown("sess-1", "recommendation", "rec-1", agent_traces)

        assert "### Structured Output" in md
        assert "WING_1" in md

    def test_multiple_agents(self) -> None:
        traces = [
            {"domain": "balance", "system_prompt": "s1", "user_prompt": "u1", "messages": [], "structured_output": None},
            {"domain": "tyre", "system_prompt": "s2", "user_prompt": "u2", "messages": [], "structured_output": None},
        ]

        md = format_trace_markdown("sess-1", "recommendation", "rec-1", traces)

        assert "## Agent: balance" in md
        assert "## Agent: tyre" in md
        assert "**Agents**: balance, tyre" in md


# ---------------------------------------------------------------------------
# write_trace / read_trace
# ---------------------------------------------------------------------------


class TestWriteReadTrace:
    def test_round_trip(self, tmp_path: Path) -> None:
        content = "# Diagnostic Trace\nSome content here."
        path = write_trace(tmp_path / "traces", "rec", "abc-123", content)

        assert path.is_file()
        assert path.name == "rec_abc-123.md"

        read_back = read_trace(tmp_path / "traces", "rec", "abc-123")
        assert read_back == content

    def test_read_missing_returns_none(self, tmp_path: Path) -> None:
        result = read_trace(tmp_path, "rec", "nonexistent")
        assert result is None

    def test_write_creates_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested" / "traces"
        write_trace(nested, "msg", "xyz-789", "content")
        assert (nested / "msg_xyz-789.md").is_file()

    def test_write_overwrites_existing(self, tmp_path: Path) -> None:
        write_trace(tmp_path, "rec", "id-1", "first")
        write_trace(tmp_path, "rec", "id-1", "second")

        assert read_trace(tmp_path, "rec", "id-1") == "second"
