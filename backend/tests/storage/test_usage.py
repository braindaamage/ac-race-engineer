"""Tests for LLM event storage (replaces agent usage tests)."""

from __future__ import annotations

import sqlite3

import pytest

from ac_engineer.storage.db import init_db, _connect
from ac_engineer.storage.models import LlmEvent, LlmToolCall
from ac_engineer.storage.usage import save_llm_event, get_llm_events


def _sample_tool_calls():
    """Return a list of sample LlmToolCall objects for testing."""
    return [
        LlmToolCall(tool_name="search_kb", response_tokens=150, call_index=0),
        LlmToolCall(tool_name="get_setup_range", response_tokens=80, call_index=1),
        LlmToolCall(tool_name="get_current_value", response_tokens=45, call_index=2),
    ]


def _sample_event(**overrides):
    """Build an LlmEvent with sensible defaults."""
    defaults = dict(
        session_id="test_session",
        event_type="analysis",
        agent_name="balance",
        model="claude-sonnet-4-20250514",
        input_tokens=1200,
        output_tokens=350,
        request_count=2,
        tool_call_count=3,
        duration_ms=4500,
        context_type="recommendation",
        context_id="rec_001",
        tool_calls=_sample_tool_calls(),
    )
    defaults.update(overrides)
    return LlmEvent(**defaults)


class TestSaveLlmEvent:
    """Tests for save_llm_event."""

    def test_creates_record_with_all_fields(self, db_path):
        """Save an event with tool calls, verify all fields populated."""
        event = _sample_event()
        result = save_llm_event(db_path, event)

        assert len(result.id) == 32
        assert result.session_id == "test_session"
        assert result.event_type == "analysis"
        assert result.agent_name == "balance"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.input_tokens == 1200
        assert result.output_tokens == 350
        assert result.request_count == 2
        assert result.tool_call_count == 3
        assert result.duration_ms == 4500
        assert result.created_at != ""
        assert result.context_type == "recommendation"
        assert result.context_id == "rec_001"
        assert len(result.tool_calls) == 3
        for tc in result.tool_calls:
            assert len(tc.id) == 32
            assert tc.event_id == result.id

    def test_auto_generates_ids(self, db_path):
        """Verify id and tool call ids are unique 32-char hex strings."""
        event = _sample_event()
        result = save_llm_event(db_path, event)

        all_ids = [result.id] + [tc.id for tc in result.tool_calls]
        for id_val in all_ids:
            assert len(id_val) == 32
            int(id_val, 16)  # raises if not hex
        assert len(set(all_ids)) == len(all_ids)

    def test_tool_calls_persisted_atomically(self, db_path):
        """Save with multiple tool calls, verify all rows in llm_tool_calls."""
        event = _sample_event()
        result = save_llm_event(db_path, event)

        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM llm_tool_calls WHERE event_id = ? ORDER BY call_index ASC",
                (result.id,),
            ).fetchall()
            assert len(rows) == 3
            tool_names = [dict(r)["tool_name"] for r in rows]
            assert tool_names == ["search_kb", "get_setup_range", "get_current_value"]
            for row in rows:
                assert dict(row)["event_id"] == result.id
        finally:
            conn.close()

    def test_saves_without_tool_calls(self, db_path):
        """Save with empty tool_calls, verify event row exists and no details."""
        event = _sample_event(tool_calls=[], tool_call_count=0)
        result = save_llm_event(db_path, event)

        assert len(result.id) == 32
        assert result.tool_calls == []

        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM llm_tool_calls WHERE event_id = ?",
                (result.id,),
            ).fetchall()
            assert len(rows) == 0
        finally:
            conn.close()

    def test_nullable_context_fields(self, db_path):
        """Save event with null context_type and context_id."""
        event = _sample_event(context_type=None, context_id=None, tool_calls=[])
        result = save_llm_event(db_path, event)

        assert result.context_type is None
        assert result.context_id is None

        conn = _connect(db_path)
        try:
            row = conn.execute(
                "SELECT context_type, context_id FROM llm_events WHERE id = ?",
                (result.id,),
            ).fetchone()
            assert dict(row)["context_type"] is None
            assert dict(row)["context_id"] is None
        finally:
            conn.close()

    def test_chat_event_type(self, db_path):
        """Save a chat event with principal agent and message context."""
        event = _sample_event(
            event_type="chat",
            agent_name="principal",
            context_type="message",
            context_id="msg_001",
            tool_calls=[],
        )
        result = save_llm_event(db_path, event)

        assert result.event_type == "chat"
        assert result.agent_name == "principal"
        assert result.context_type == "message"
        assert result.context_id == "msg_001"


class TestGetLlmEvents:
    """Tests for get_llm_events."""

    def test_returns_with_tool_calls(self, db_path):
        """Save 2 events for same context, verify retrieval with tool calls."""
        for agent in ("balance", "tyre"):
            event = _sample_event(agent_name=agent)
            save_llm_event(db_path, event)

        results = get_llm_events(db_path, "recommendation", "rec_001")
        assert len(results) == 2
        assert results[0].agent_name == "balance"
        assert results[1].agent_name == "tyre"
        for r in results:
            assert len(r.tool_calls) == 3
            assert r.context_type == "recommendation"
            assert r.context_id == "rec_001"

    def test_empty_returns_empty(self, db_path):
        """No events for context returns empty list."""
        results = get_llm_events(db_path, "recommendation", "nonexistent")
        assert results == []

    def test_does_not_return_other_contexts(self, db_path):
        """Verify get_llm_events only returns records for the given context."""
        save_llm_event(db_path, _sample_event(context_id="rec_a", agent_name="balance"))
        save_llm_event(db_path, _sample_event(context_id="rec_b", agent_name="tyre"))

        results_a = get_llm_events(db_path, "recommendation", "rec_a")
        assert len(results_a) == 1
        assert results_a[0].agent_name == "balance"

        results_b = get_llm_events(db_path, "recommendation", "rec_b")
        assert len(results_b) == 1
        assert results_b[0].agent_name == "tyre"

    def test_tool_calls_ordered_by_call_index(self, db_path):
        """Tool calls in retrieved events are ordered by call_index."""
        event = _sample_event()
        save_llm_event(db_path, event)

        results = get_llm_events(db_path, "recommendation", "rec_001")
        assert len(results) == 1
        indices = [tc.call_index for tc in results[0].tool_calls]
        assert indices == [0, 1, 2]

    def test_different_context_types_isolated(self, db_path):
        """Events with different context_types are isolated."""
        save_llm_event(db_path, _sample_event(
            context_type="recommendation", context_id="id_1", tool_calls=[],
        ))
        save_llm_event(db_path, _sample_event(
            event_type="chat", agent_name="principal",
            context_type="message", context_id="id_1", tool_calls=[],
        ))

        recs = get_llm_events(db_path, "recommendation", "id_1")
        msgs = get_llm_events(db_path, "message", "id_1")
        assert len(recs) == 1
        assert recs[0].event_type == "analysis"
        assert len(msgs) == 1
        assert msgs[0].event_type == "chat"


class TestMigration:
    """Tests for migration idempotency."""

    def test_fresh_db_creates_all_tables(self, tmp_path):
        """init_db on fresh path creates all tables including llm_events/llm_tool_calls."""
        db_path = tmp_path / "fresh.db"
        init_db(db_path)

        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            tables = {dict(r)["name"] for r in rows}
            expected = {
                "sessions",
                "recommendations",
                "setup_changes",
                "messages",
                "parameter_cache",
                "llm_events",
                "llm_tool_calls",
            }
            assert expected.issubset(tables)
        finally:
            conn.close()

    def test_idempotent_on_existing_db(self, tmp_path):
        """init_db twice on same path causes no errors."""
        db_path = tmp_path / "idem.db"
        init_db(db_path)
        init_db(db_path)  # Should not raise

        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            tables = {dict(r)["name"] for r in rows}
            assert "llm_events" in tables
            assert "llm_tool_calls" in tables
        finally:
            conn.close()


class TestCascade:
    """Tests for cascade delete behavior."""

    def test_delete_event_cascades_to_tool_calls(self, db_path):
        """Deleting an llm_event cascades to llm_tool_calls."""
        event = _sample_event()
        result = save_llm_event(db_path, event)

        conn = _connect(db_path)
        try:
            assert conn.execute(
                "SELECT COUNT(*) FROM llm_events WHERE id = ?",
                (result.id,),
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM llm_tool_calls WHERE event_id = ?",
                (result.id,),
            ).fetchone()[0] == 3

            # Delete the event
            conn.execute(
                "DELETE FROM llm_events WHERE id = ?",
                (result.id,),
            )
            conn.commit()

            # Verify cascade
            assert conn.execute(
                "SELECT COUNT(*) FROM llm_events WHERE id = ?",
                (result.id,),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM llm_tool_calls WHERE event_id = ?",
                (result.id,),
            ).fetchone()[0] == 0
        finally:
            conn.close()
