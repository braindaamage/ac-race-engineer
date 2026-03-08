"""Agent usage CRUD operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import _connect
from .models import AgentUsage, ToolCallDetail


def save_agent_usage(db_path: str | Path, usage: AgentUsage) -> AgentUsage:
    """Persist an agent usage record with tool call details atomically."""
    conn = _connect(db_path)
    try:
        usage_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO agent_usage
               (usage_id, recommendation_id, domain, model,
                input_tokens, output_tokens, tool_call_count,
                turn_count, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                usage_id,
                usage.recommendation_id,
                usage.domain,
                usage.model,
                usage.input_tokens,
                usage.output_tokens,
                usage.tool_call_count,
                usage.turn_count,
                usage.duration_ms,
                created_at,
            ),
        )

        populated_tool_calls: list[ToolCallDetail] = []
        for tc in usage.tool_calls:
            detail_id = uuid.uuid4().hex
            called_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """INSERT INTO tool_call_details
                   (detail_id, usage_id, tool_name, token_count, called_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (detail_id, usage_id, tc.tool_name, tc.token_count, called_at),
            )
            populated_tool_calls.append(
                tc.model_copy(
                    update={
                        "detail_id": detail_id,
                        "usage_id": usage_id,
                        "called_at": called_at,
                    }
                )
            )

        conn.commit()

        return usage.model_copy(
            update={
                "usage_id": usage_id,
                "created_at": created_at,
                "tool_calls": populated_tool_calls,
            }
        )
    finally:
        conn.close()


def get_agent_usage(
    db_path: str | Path, recommendation_id: str
) -> list[AgentUsage]:
    """Return all usage records for a recommendation with tool calls populated."""
    conn = _connect(db_path)
    try:
        usage_rows = conn.execute(
            "SELECT * FROM agent_usage WHERE recommendation_id = ? ORDER BY created_at ASC",
            (recommendation_id,),
        ).fetchall()

        results: list[AgentUsage] = []
        for usage_row in usage_rows:
            usage_dict = dict(usage_row)
            detail_rows = conn.execute(
                "SELECT * FROM tool_call_details WHERE usage_id = ?",
                (usage_dict["usage_id"],),
            ).fetchall()
            tool_calls = [ToolCallDetail(**dict(dr)) for dr in detail_rows]
            results.append(AgentUsage(**usage_dict, tool_calls=tool_calls))

        return results
    finally:
        conn.close()
