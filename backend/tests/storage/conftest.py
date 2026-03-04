"""Storage test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.storage.db import init_db
from ac_engineer.storage.models import SessionRecord


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    """Create a temporary database and return its path."""
    path = tmp_path / "test.db"
    init_db(path)
    return path


def make_session(**overrides: object) -> SessionRecord:
    """Build a SessionRecord with sensible defaults, applying overrides."""
    defaults = {
        "session_id": "test_session_001",
        "car": "ks_ferrari_488_gt3",
        "track": "monza",
        "session_date": "2026-03-04T14:30:00",
        "lap_count": 12,
        "best_lap_time": 108.432,
    }
    defaults.update(overrides)
    return SessionRecord(**defaults)
