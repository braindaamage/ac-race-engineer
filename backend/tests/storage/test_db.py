"""Tests for database initialization."""

from __future__ import annotations

from pathlib import Path

from ac_engineer.storage.db import _connect, init_db


class TestInitDb:
    def test_idempotent(self, db_path: Path) -> None:
        # db_path fixture already called init_db once; call again
        init_db(db_path)  # should not raise

    def test_foreign_keys_enabled(self, db_path: Path) -> None:
        conn = _connect(db_path)
        try:
            result = conn.execute("PRAGMA foreign_keys").fetchone()
            assert result[0] == 1
        finally:
            conn.close()

    def test_wal_journal_mode(self, db_path: Path) -> None:
        conn = _connect(db_path)
        try:
            result = conn.execute("PRAGMA journal_mode").fetchone()
            assert result[0] == "wal"
        finally:
            conn.close()
