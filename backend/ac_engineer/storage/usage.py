"""LLM event CRUD operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import _connect
from .models import LlmEvent, LlmToolCall


def save_llm_event(db_path: str | Path, event: LlmEvent) -> LlmEvent:
    """Persist an LLM event record with tool call details atomically."""
    conn = _connect(db_path)
    try:
        event_id = event.id or uuid.uuid4().hex
        created_at = event.created_at or datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO llm_events
               (id, session_id, event_type, agent_name, model,
                input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                request_count, tool_call_count, duration_ms, created_at,
                context_type, context_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                event.session_id,
                event.event_type,
                event.agent_name,
                event.model,
                event.input_tokens,
                event.output_tokens,
                event.cache_read_tokens,
                event.cache_write_tokens,
                event.request_count,
                event.tool_call_count,
                event.duration_ms,
                created_at,
                event.context_type,
                event.context_id,
            ),
        )

        populated_tool_calls: list[LlmToolCall] = []
        for tc in event.tool_calls:
            tc_id = tc.id or uuid.uuid4().hex
            conn.execute(
                """INSERT INTO llm_tool_calls
                   (id, event_id, tool_name, response_tokens, call_index)
                   VALUES (?, ?, ?, ?, ?)""",
                (tc_id, event_id, tc.tool_name, tc.response_tokens, tc.call_index),
            )
            populated_tool_calls.append(
                tc.model_copy(
                    update={
                        "id": tc_id,
                        "event_id": event_id,
                    }
                )
            )

        conn.commit()

        return event.model_copy(
            update={
                "id": event_id,
                "created_at": created_at,
                "tool_calls": populated_tool_calls,
            }
        )
    finally:
        conn.close()


def get_llm_events(
    db_path: str | Path, context_type: str, context_id: str
) -> list[LlmEvent]:
    """Return all LLM event records for a context with tool calls populated."""
    conn = _connect(db_path)
    try:
        event_rows = conn.execute(
            "SELECT * FROM llm_events WHERE context_type = ? AND context_id = ? ORDER BY created_at ASC",
            (context_type, context_id),
        ).fetchall()

        results: list[LlmEvent] = []
        for event_row in event_rows:
            event_dict = dict(event_row)
            detail_rows = conn.execute(
                "SELECT * FROM llm_tool_calls WHERE event_id = ? ORDER BY call_index ASC",
                (event_dict["id"],),
            ).fetchall()
            tool_calls = [LlmToolCall(**dict(dr)) for dr in detail_rows]
            results.append(LlmEvent(**event_dict, tool_calls=tool_calls))

        return results
    finally:
        conn.close()
