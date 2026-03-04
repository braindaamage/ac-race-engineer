"""Recommendation CRUD operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import _connect
from .models import Recommendation, SetupChange


def save_recommendation(
    db_path: str | Path,
    session_id: str,
    summary: str,
    changes: list[SetupChange],
) -> Recommendation:
    """Create a new recommendation with setup changes. Returns populated Recommendation."""
    conn = _connect(db_path)
    try:
        # Verify session exists
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Session not found: {session_id!r}")

        recommendation_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO recommendations
               (recommendation_id, session_id, status, summary, created_at)
               VALUES (?, ?, 'proposed', ?, ?)""",
            (recommendation_id, session_id, summary, created_at),
        )

        populated_changes: list[SetupChange] = []
        for change in changes:
            change_id = uuid.uuid4().hex
            conn.execute(
                """INSERT INTO setup_changes
                   (change_id, recommendation_id, section, parameter, old_value, new_value, reasoning)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    change_id,
                    recommendation_id,
                    change.section,
                    change.parameter,
                    change.old_value,
                    change.new_value,
                    change.reasoning,
                ),
            )
            populated_changes.append(
                change.model_copy(
                    update={"change_id": change_id, "recommendation_id": recommendation_id}
                )
            )

        conn.commit()

        return Recommendation(
            recommendation_id=recommendation_id,
            session_id=session_id,
            status="proposed",
            summary=summary,
            created_at=created_at,
            changes=populated_changes,
        )
    finally:
        conn.close()


def get_recommendations(
    db_path: str | Path, session_id: str
) -> list[Recommendation]:
    """Return all recommendations for a session with changes populated."""
    conn = _connect(db_path)
    try:
        rec_rows = conn.execute(
            "SELECT * FROM recommendations WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()

        results: list[Recommendation] = []
        for rec_row in rec_rows:
            rec_dict = dict(rec_row)
            change_rows = conn.execute(
                "SELECT * FROM setup_changes WHERE recommendation_id = ?",
                (rec_dict["recommendation_id"],),
            ).fetchall()
            changes = [SetupChange(**dict(cr)) for cr in change_rows]
            results.append(
                Recommendation(**rec_dict, changes=changes)
            )

        return results
    finally:
        conn.close()


def update_recommendation_status(
    db_path: str | Path, recommendation_id: str, status: str
) -> None:
    """Update a recommendation's status. Must be 'applied' or 'rejected'."""
    if status not in ("applied", "rejected"):
        raise ValueError(f"Status must be 'applied' or 'rejected', got {status!r}")

    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE recommendations SET status = ? WHERE recommendation_id = ?",
            (status, recommendation_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Recommendation not found: {recommendation_id!r}")
        conn.commit()
    finally:
        conn.close()
