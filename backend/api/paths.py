"""Centralized path resolution — dev mode vs frozen (PyInstaller) mode."""

from __future__ import annotations

import sys
from pathlib import Path


def get_data_dir() -> Path:
    """Return the data directory as an absolute Path.

    In frozen (PyInstaller) mode: <exe_dir>/data/
    In dev mode: <repo_root>/data/
    """
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys.executable to the .exe path
        return Path(sys.executable).resolve().parent / "data"
    # Dev mode: backend/api/paths.py -> repo root is 3 levels up
    return Path(__file__).resolve().parent.parent.parent / "data"


def get_db_path() -> Path:
    """Return the SQLite database path."""
    return get_data_dir() / "ac_engineer.db"


def get_config_path() -> Path:
    """Return the config.json path."""
    return get_data_dir() / "config.json"


def get_sessions_dir() -> Path:
    """Return the sessions directory path."""
    return get_data_dir() / "sessions"
