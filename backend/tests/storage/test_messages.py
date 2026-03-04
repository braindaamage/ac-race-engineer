"""Tests for message CRUD operations."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.storage.messages import clear_messages, get_messages, save_message
from ac_engineer.storage.models import SessionRecord
from ac_engineer.storage.sessions import save_session


def _setup_session(db_path: Path, session_id: str = "sess1") -> None:
    save_session(
        db_path,
        SessionRecord(
            session_id=session_id,
            car="ferrari",
            track="monza",
            session_date="2026-03-04T14:00:00",
            lap_count=10,
        ),
    )


class TestSaveMessage:
    def test_creates_with_auto_id(self, db_path: Path) -> None:
        _setup_session(db_path)
        msg = save_message(db_path, "sess1", "user", "Hello")
        assert len(msg.message_id) == 32
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.created_at  # non-empty

    def test_invalid_session_raises(self, db_path: Path) -> None:
        with pytest.raises(ValueError, match="Session not found"):
            save_message(db_path, "nonexistent", "user", "Hello")

    def test_invalid_role_raises(self, db_path: Path) -> None:
        _setup_session(db_path)
        with pytest.raises(ValueError, match="Role must be"):
            save_message(db_path, "sess1", "system", "Hello")


class TestGetMessages:
    def test_chronological_order(self, db_path: Path) -> None:
        _setup_session(db_path)
        save_message(db_path, "sess1", "user", "First")
        save_message(db_path, "sess1", "assistant", "Second")
        save_message(db_path, "sess1", "user", "Third")
        msgs = get_messages(db_path, "sess1")
        assert len(msgs) == 3
        assert msgs[0].content == "First"
        assert msgs[1].content == "Second"
        assert msgs[2].content == "Third"

    def test_empty_returns_empty(self, db_path: Path) -> None:
        _setup_session(db_path)
        assert get_messages(db_path, "sess1") == []


class TestClearMessages:
    def test_deletes_only_target_session(self, db_path: Path) -> None:
        _setup_session(db_path, "sess1")
        _setup_session(db_path, "sess2")
        save_message(db_path, "sess1", "user", "A")
        save_message(db_path, "sess1", "assistant", "B")
        save_message(db_path, "sess2", "user", "C")

        count = clear_messages(db_path, "sess1")
        assert count == 2
        assert get_messages(db_path, "sess1") == []
        assert len(get_messages(db_path, "sess2")) == 1

    def test_returns_count(self, db_path: Path) -> None:
        _setup_session(db_path)
        save_message(db_path, "sess1", "user", "A")
        save_message(db_path, "sess1", "assistant", "B")
        save_message(db_path, "sess1", "user", "C")
        assert clear_messages(db_path, "sess1") == 3
