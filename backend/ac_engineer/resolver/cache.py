"""SQLite cache CRUD for resolved parameter data."""

from __future__ import annotations

import json
from pathlib import Path

from ac_engineer.engineer.models import ParameterRange
from ac_engineer.storage.db import _connect

from .models import ResolvedParameters, ResolutionTier


def _serialize_parameters(parameters: dict[str, ParameterRange]) -> str:
    """Serialize parameter ranges to JSON string."""
    data = {
        key: rng.model_dump(mode="json")
        for key, rng in parameters.items()
    }
    return json.dumps(data)


def _deserialize_parameters(json_str: str) -> dict[str, ParameterRange]:
    """Deserialize JSON string to parameter ranges."""
    data = json.loads(json_str)
    return {
        key: ParameterRange(**val)
        for key, val in data.items()
    }


def get_cached_parameters(
    db_path: str | Path, car_name: str
) -> ResolvedParameters | None:
    """Retrieve cached parameter data for a car.

    Returns None if no cache entry exists.
    """
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT car_name, tier, has_defaults, parameters_json, resolved_at "
            "FROM parameter_cache WHERE car_name = ?",
            (car_name,),
        ).fetchone()
        if row is None:
            return None
        return ResolvedParameters(
            car_name=row["car_name"],
            tier=ResolutionTier(row["tier"]),
            parameters=_deserialize_parameters(row["parameters_json"]),
            has_defaults=bool(row["has_defaults"]),
            resolved_at=row["resolved_at"],
        )
    finally:
        conn.close()


def save_to_cache(db_path: str | Path, resolved: ResolvedParameters) -> None:
    """Persist a resolution result to the cache (INSERT OR REPLACE)."""
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO parameter_cache "
            "(car_name, tier, has_defaults, parameters_json, resolved_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                resolved.car_name,
                int(resolved.tier),
                1 if resolved.has_defaults else 0,
                _serialize_parameters(resolved.parameters),
                resolved.resolved_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def invalidate_cache(db_path: str | Path, car_name: str) -> bool:
    """Delete a single car's cache entry. Returns True if a row was deleted."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM parameter_cache WHERE car_name = ?",
            (car_name,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def invalidate_all_caches(db_path: str | Path) -> int:
    """Delete all cache entries. Returns the number of rows deleted."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute("DELETE FROM parameter_cache")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
