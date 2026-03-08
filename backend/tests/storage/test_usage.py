"""Tests for agent usage storage."""

from __future__ import annotations

import sqlite3

import pytest
from pydantic import ValidationError

from ac_engineer.storage.db import init_db, _connect
from ac_engineer.storage.models import AgentUsage, ToolCallDetail
from ac_engineer.storage.sessions import save_session
from ac_engineer.storage.recommendations import save_recommendation
from ac_engineer.storage.models import SessionRecord, SetupChange
from ac_engineer.storage.usage import save_agent_usage, get_agent_usage


def _setup_session(db_path):
    """Create a prerequisite session and return its ID."""
    session = SessionRecord(
        session_id="usage_test_session",
        car="ks_ferrari_488_gt3",
        track="monza",
        session_date="2026-03-08T10:00:00",
        lap_count=5,
        best_lap_time=90.0,
    )
    save_session(db_path, session)
    return session.session_id


def _setup_recommendation(db_path, session_id=None):
    """Create a prerequisite session + recommendation and return the recommendation_id."""
    if session_id is None:
        session_id = _setup_session(db_path)
    rec = save_recommendation(
        db_path,
        session_id=session_id,
        summary="Test recommendation",
        changes=[
            SetupChange(
                section="TYRES",
                parameter="PRESSURE_LF",
                old_value="26.0",
                new_value="25.5",
                reasoning="Lower pressure for more grip",
            )
        ],
    )
    return rec.recommendation_id


def _sample_tool_calls():
    """Return a list of sample ToolCallDetail objects for testing."""
    return [
        ToolCallDetail(tool_name="search_kb", token_count=150),
        ToolCallDetail(tool_name="get_setup_range", token_count=80),
        ToolCallDetail(tool_name="get_current_value", token_count=45),
    ]


class TestSaveAgentUsage:
    """Tests for save_agent_usage (US1 + US2)."""

    def test_creates_record_with_all_fields(self, db_path):
        """T003: Save a usage record with tool calls, verify all fields populated."""
        rec_id = _setup_recommendation(db_path)
        tool_calls = _sample_tool_calls()

        usage = AgentUsage(
            recommendation_id=rec_id,
            domain="balance",
            model="claude-sonnet-4-20250514",
            input_tokens=1200,
            output_tokens=350,
            tool_call_count=3,
            turn_count=2,
            duration_ms=4500,
            tool_calls=tool_calls,
        )
        result = save_agent_usage(db_path, usage)

        assert len(result.usage_id) == 32
        assert result.recommendation_id == rec_id
        assert result.domain == "balance"
        assert result.model == "claude-sonnet-4-20250514"
        assert result.input_tokens == 1200
        assert result.output_tokens == 350
        assert result.tool_call_count == 3
        assert result.turn_count == 2
        assert result.duration_ms == 4500
        assert result.created_at != ""
        assert len(result.tool_calls) == 3
        for tc in result.tool_calls:
            assert len(tc.detail_id) == 32
            assert tc.usage_id == result.usage_id
            assert tc.called_at != ""

    def test_auto_generates_ids(self, db_path):
        """T004: Verify usage_id and detail_ids are unique 32-char hex strings."""
        rec_id = _setup_recommendation(db_path)
        tool_calls = _sample_tool_calls()

        usage = AgentUsage(
            recommendation_id=rec_id,
            domain="tyre",
            model="gpt-4o",
            input_tokens=500,
            output_tokens=200,
            tool_call_count=3,
            turn_count=1,
            duration_ms=2000,
            tool_calls=tool_calls,
        )
        result = save_agent_usage(db_path, usage)

        all_ids = [result.usage_id] + [tc.detail_id for tc in result.tool_calls]
        # All 32-char hex
        for id_val in all_ids:
            assert len(id_val) == 32
            int(id_val, 16)  # raises if not hex
        # All unique
        assert len(set(all_ids)) == len(all_ids)

    def test_invalid_recommendation_raises(self, db_path):
        """T005: Save with nonexistent recommendation_id, expect IntegrityError."""
        usage = AgentUsage(
            recommendation_id="nonexistent_rec_id_1234567890ab",
            domain="aero",
            model="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=50,
            tool_call_count=0,
            turn_count=1,
            duration_ms=1000,
        )
        with pytest.raises(sqlite3.IntegrityError):
            save_agent_usage(db_path, usage)

    def test_invalid_domain_raises(self):
        """T006: Attempt to create AgentUsage with invalid domain, expect ValidationError."""
        with pytest.raises(ValidationError):
            AgentUsage(
                recommendation_id="some_rec_id",
                domain="invalid",
                model="some-model",
                input_tokens=100,
                output_tokens=50,
                tool_call_count=0,
                turn_count=1,
                duration_ms=1000,
            )

    def test_tool_calls_persisted_atomically(self, db_path):
        """T007: Save with multiple tool calls, verify all rows in tool_call_details."""
        rec_id = _setup_recommendation(db_path)
        tool_calls = _sample_tool_calls()

        usage = AgentUsage(
            recommendation_id=rec_id,
            domain="technique",
            model="claude-sonnet-4-20250514",
            input_tokens=800,
            output_tokens=300,
            tool_call_count=3,
            turn_count=1,
            duration_ms=3000,
            tool_calls=tool_calls,
        )
        result = save_agent_usage(db_path, usage)

        # Verify directly in the database
        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM tool_call_details WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchall()
            assert len(rows) == 3
            tool_names = {dict(r)["tool_name"] for r in rows}
            assert tool_names == {"search_kb", "get_setup_range", "get_current_value"}
            for row in rows:
                assert dict(row)["usage_id"] == result.usage_id
        finally:
            conn.close()

    def test_saves_without_tool_calls(self, db_path):
        """T008: Save with empty tool_calls, verify agent_usage row exists and no details."""
        rec_id = _setup_recommendation(db_path)

        usage = AgentUsage(
            recommendation_id=rec_id,
            domain="balance",
            model="gpt-4o",
            input_tokens=600,
            output_tokens=200,
            tool_call_count=0,
            turn_count=1,
            duration_ms=1500,
            tool_calls=[],
        )
        result = save_agent_usage(db_path, usage)

        assert len(result.usage_id) == 32
        assert result.tool_calls == []

        # Verify no tool_call_details rows
        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM tool_call_details WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchall()
            assert len(rows) == 0
        finally:
            conn.close()


class TestGetAgentUsage:
    """Tests for get_agent_usage (US3)."""

    def test_returns_with_tool_calls(self, db_path):
        """T010: Save 2 usage records, verify retrieval with tool calls."""
        rec_id = _setup_recommendation(db_path)

        for domain in ("balance", "tyre"):
            usage = AgentUsage(
                recommendation_id=rec_id,
                domain=domain,
                model="claude-sonnet-4-20250514",
                input_tokens=500,
                output_tokens=200,
                tool_call_count=2,
                turn_count=1,
                duration_ms=2000,
                tool_calls=[
                    ToolCallDetail(tool_name="search_kb", token_count=100),
                    ToolCallDetail(tool_name="get_setup_range", token_count=80),
                ],
            )
            save_agent_usage(db_path, usage)

        results = get_agent_usage(db_path, rec_id)
        assert len(results) == 2
        # Ordered by created_at ASC
        assert results[0].domain == "balance"
        assert results[1].domain == "tyre"
        for r in results:
            assert len(r.tool_calls) == 2
            assert r.recommendation_id == rec_id

    def test_empty_returns_empty(self, db_path):
        """T011: No usage records for recommendation returns empty list."""
        rec_id = _setup_recommendation(db_path)
        results = get_agent_usage(db_path, rec_id)
        assert results == []

    def test_does_not_return_other_recommendations(self, db_path):
        """T012: Verify get_agent_usage only returns records for the given recommendation."""
        session_id = _setup_session(db_path)
        rec_a = _setup_recommendation(db_path, session_id=session_id)
        rec_b = _setup_recommendation(db_path, session_id=session_id)

        for rec_id, domain in [(rec_a, "balance"), (rec_b, "tyre")]:
            usage = AgentUsage(
                recommendation_id=rec_id,
                domain=domain,
                model="gpt-4o",
                input_tokens=300,
                output_tokens=100,
                tool_call_count=0,
                turn_count=1,
                duration_ms=1000,
            )
            save_agent_usage(db_path, usage)

        results_a = get_agent_usage(db_path, rec_a)
        assert len(results_a) == 1
        assert results_a[0].domain == "balance"

        results_b = get_agent_usage(db_path, rec_b)
        assert len(results_b) == 1
        assert results_b[0].domain == "tyre"


class TestMigration:
    """Tests for migration idempotency."""

    def test_fresh_db_creates_all_tables(self, tmp_path):
        """T015: init_db on fresh path creates all 7 tables."""
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
                "agent_usage",
                "tool_call_details",
            }
            assert expected.issubset(tables)
        finally:
            conn.close()

    def test_idempotent_on_existing_db(self, tmp_path):
        """T016: init_db twice on same path causes no errors."""
        db_path = tmp_path / "idem.db"
        init_db(db_path)
        init_db(db_path)  # Should not raise

        conn = _connect(db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
            tables = {dict(r)["name"] for r in rows}
            assert "agent_usage" in tables
            assert "tool_call_details" in tables
        finally:
            conn.close()


class TestCascade:
    """Tests for cascade delete behavior."""

    def test_delete_recommendation_cascades_to_usage_and_details(self, db_path):
        """T017: Deleting recommendation cascades to agent_usage and tool_call_details."""
        rec_id = _setup_recommendation(db_path)

        usage = AgentUsage(
            recommendation_id=rec_id,
            domain="balance",
            model="claude-sonnet-4-20250514",
            input_tokens=500,
            output_tokens=200,
            tool_call_count=2,
            turn_count=1,
            duration_ms=2000,
            tool_calls=[
                ToolCallDetail(tool_name="search_kb", token_count=100),
                ToolCallDetail(tool_name="get_setup_range", token_count=80),
            ],
        )
        result = save_agent_usage(db_path, usage)

        # Verify rows exist
        conn = _connect(db_path)
        try:
            assert conn.execute(
                "SELECT COUNT(*) FROM agent_usage WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchone()[0] == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM tool_call_details WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchone()[0] == 2

            # Delete the recommendation
            conn.execute(
                "DELETE FROM recommendations WHERE recommendation_id = ?",
                (rec_id,),
            )
            conn.commit()

            # Verify cascade
            assert conn.execute(
                "SELECT COUNT(*) FROM agent_usage WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM tool_call_details WHERE usage_id = ?",
                (result.usage_id,),
            ).fetchone()[0] == 0
        finally:
            conn.close()
