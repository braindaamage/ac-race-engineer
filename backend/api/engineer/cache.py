"""Save/load EngineerResponse JSON cache for recommendation detail."""

from __future__ import annotations

import json
from pathlib import Path

from ac_engineer.engineer.models import EngineerResponse


def save_engineer_response(
    cache_dir: str | Path,
    recommendation_id: str,
    response: EngineerResponse,
) -> Path:
    """Save EngineerResponse to recommendation_{rec_id}.json in cache_dir."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"recommendation_{recommendation_id}.json"
    data = response.model_dump(mode="json")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def load_engineer_response(
    cache_dir: str | Path,
    recommendation_id: str,
) -> EngineerResponse | None:
    """Load EngineerResponse from cache. Returns None if file missing or corrupted."""
    path = Path(cache_dir) / f"recommendation_{recommendation_id}.json"
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return EngineerResponse.model_validate(data)
    except (json.JSONDecodeError, Exception):
        return None
