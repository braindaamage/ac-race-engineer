"""Save/load AnalyzedSession JSON cache."""

from __future__ import annotations

import json
from pathlib import Path

from ac_engineer.analyzer.models import AnalyzedSession

CACHE_FILENAME = "analyzed.json"


def get_cache_dir(sessions_dir: str | Path, session_id: str) -> Path:
    """Return the cache directory for a session."""
    return Path(sessions_dir) / session_id


def save_analyzed_session(cache_dir: str | Path, analyzed: AnalyzedSession) -> Path:
    """Write AnalyzedSession to analyzed.json in cache_dir."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / CACHE_FILENAME
    data = analyzed.model_dump(mode="json")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_analyzed_session(cache_dir: str | Path) -> AnalyzedSession:
    """Load AnalyzedSession from analyzed.json in cache_dir.

    Raises FileNotFoundError if the file does not exist.
    Raises ValueError if the JSON is corrupted or validation fails.
    """
    path = Path(cache_dir) / CACHE_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Analyzed cache not found: {path}")
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return AnalyzedSession.model_validate(data)
    except (json.JSONDecodeError, Exception) as exc:
        if isinstance(exc, FileNotFoundError):
            raise
        raise ValueError(f"Corrupted or invalid analyzed cache: {path}: {exc}") from exc
