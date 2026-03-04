"""Message CRUD operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .db import _connect
from .models import Message


def save_message(
    db_path: str | Path,
    session_id: str,
    role: str,
    content: str,
) -> Message:
    """Save a new conversation message. Returns populated Message."""
    if role not in ("user", "assistant"):
        raise ValueError(f"Role must be 'user' or 'assistant', got {role!r}")

    conn = _connect(db_path)
    try:
        # Verify session exists
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Session not found: {session_id!r}")

        message_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """INSERT INTO messages
               (message_id, session_id, role, content, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (message_id, session_id, role, content, created_at),
        )
        conn.commit()

        return Message(
            message_id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            created_at=created_at,
        )
    finally:
        conn.close()


def get_messages(db_path: str | Path, session_id: str) -> list[Message]:
    """Return all messages for a session ordered by created_at ASC."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        return [Message(**dict(row)) for row in rows]
    finally:
        conn.close()


def clear_messages(db_path: str | Path, session_id: str) -> int:
    """Delete all messages for a session. Returns count of deleted messages."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM messages WHERE session_id = ?", (session_id,)
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
