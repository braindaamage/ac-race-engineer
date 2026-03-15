"""Tiered setup parameter resolver for Assetto Corsa cars.

Public API
----------
resolve_parameters(ac_install_path, car_name, db_path, session_setup=None)
    Resolve parameter ranges and defaults using 3-tier fallback:
    Tier 1 (open data/) → Tier 2 (encrypted data.acd) → Tier 3 (session setup).
    Results from Tier 1/2 are cached in SQLite. Never raises.

list_cars(ac_install_path, db_path)
    List installed cars with resolution status. Raises ValueError if path invalid.

get_cached_parameters(db_path, car_name)
    Retrieve cached resolution data. Returns None if not cached.

invalidate_cache(db_path, car_name)
    Delete one car's cache. Returns True if deleted.

invalidate_all_caches(db_path)
    Delete all cache entries. Returns count.

Usage::

    from ac_engineer.resolver import resolve_parameters, ResolvedParameters
    resolved = resolve_parameters(ac_path, car_name, db_path)
    print(resolved.tier, len(resolved.parameters))
"""

from .ac_assets import (
    CarInfo,
    TrackInfo,
    car_badge_path,
    read_car_info,
    read_track_info,
    track_preview_path,
)
from .cache import get_cached_parameters, invalidate_all_caches, invalidate_cache
from .models import CarStatus, ResolvedParameters, ResolutionTier
from .resolver import list_cars, resolve_parameters

__all__ = [
    "CarInfo",
    "CarStatus",
    "ResolvedParameters",
    "ResolutionTier",
    "TrackInfo",
    "car_badge_path",
    "get_cached_parameters",
    "invalidate_all_caches",
    "invalidate_cache",
    "list_cars",
    "read_car_info",
    "read_track_info",
    "resolve_parameters",
    "track_preview_path",
]
