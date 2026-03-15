"""Tests for parameter_cache CRUD and cache integration in resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from ac_engineer.engineer.models import ParameterRange
from ac_engineer.resolver.cache import (
    get_cached_parameters,
    invalidate_all_caches,
    invalidate_cache,
    save_to_cache,
)
from ac_engineer.resolver.models import ResolvedParameters, ResolutionTier
from ac_engineer.resolver.resolver import resolve_parameters


def _make_resolved(
    car_name: str = "test_car",
    tier: int = 1,
    include_show_clicks: bool = True,
) -> ResolvedParameters:
    if include_show_clicks:
        params = {
            "CAMBER_LF": ParameterRange(
                section="CAMBER_LF", parameter="VALUE",
                min_value=-4.0, max_value=0.0, step=0.1,
                default_value=-3.0,
                show_clicks=0, storage_convention="scaled",
            ),
            "WING_1": ParameterRange(
                section="WING_1", parameter="VALUE",
                min_value=0, max_value=11, step=1,
                default_value=6.0,
                show_clicks=1, storage_convention="direct",
            ),
        }
    else:
        params = {
            "CAMBER_LF": ParameterRange(
                section="CAMBER_LF", parameter="VALUE",
                min_value=-4.0, max_value=0.0, step=0.1,
                default_value=-3.0,
            ),
            "WING_1": ParameterRange(
                section="WING_1", parameter="VALUE",
                min_value=0, max_value=11, step=1,
                default_value=6.0,
            ),
        }
    return ResolvedParameters(
        car_name=car_name,
        tier=ResolutionTier(tier),
        parameters=params,
        has_defaults=True,
        resolved_at="2026-03-08T14:30:00+00:00",
    )


class TestCacheCRUD:
    """T015 — Cache CRUD operations."""

    def test_save_and_retrieve(self, db_path: Path) -> None:
        """save_to_cache persists and get_cached_parameters retrieves with correct fields."""
        original = _make_resolved()
        save_to_cache(db_path, original)

        loaded = get_cached_parameters(db_path, "test_car")
        assert loaded is not None
        assert loaded.car_name == original.car_name
        assert loaded.tier == original.tier
        assert loaded.has_defaults == original.has_defaults
        assert loaded.resolved_at == original.resolved_at
        assert set(loaded.parameters.keys()) == set(original.parameters.keys())
        for key in original.parameters:
            orig_p = original.parameters[key]
            load_p = loaded.parameters[key]
            assert load_p.section == orig_p.section
            assert load_p.parameter == orig_p.parameter
            assert load_p.min_value == orig_p.min_value
            assert load_p.max_value == orig_p.max_value
            assert load_p.step == orig_p.step
            assert load_p.default_value == orig_p.default_value

    def test_get_returns_none_for_nonexistent(self, db_path: Path) -> None:
        """get_cached_parameters returns None for car not in cache."""
        result = get_cached_parameters(db_path, "no_such_car")
        assert result is None

    def test_invalidate_single_entry(self, db_path: Path) -> None:
        """invalidate_cache deletes a single car entry and returns True; False for non-existent."""
        save_to_cache(db_path, _make_resolved("car_a"))

        assert invalidate_cache(db_path, "car_a") is True
        assert get_cached_parameters(db_path, "car_a") is None

        # Second call returns False — already gone
        assert invalidate_cache(db_path, "car_a") is False

    def test_invalidate_all(self, db_path: Path) -> None:
        """invalidate_all_caches deletes all entries and returns count."""
        save_to_cache(db_path, _make_resolved("car_a"))
        save_to_cache(db_path, _make_resolved("car_b"))
        save_to_cache(db_path, _make_resolved("car_c"))

        count = invalidate_all_caches(db_path)
        assert count == 3

        # All gone
        assert get_cached_parameters(db_path, "car_a") is None
        assert get_cached_parameters(db_path, "car_b") is None
        assert get_cached_parameters(db_path, "car_c") is None

        # Calling again returns 0
        assert invalidate_all_caches(db_path) == 0

    def test_upsert_replaces_previous(self, db_path: Path) -> None:
        """Saving second entry for same car_name replaces previous one."""
        first = _make_resolved("same_car", tier=1)
        save_to_cache(db_path, first)

        second = _make_resolved("same_car", tier=2)
        second = second.model_copy(update={"resolved_at": "2026-03-09T10:00:00+00:00"})
        save_to_cache(db_path, second)

        loaded = get_cached_parameters(db_path, "same_car")
        assert loaded is not None
        assert loaded.tier == ResolutionTier.ACD_ARCHIVE
        assert loaded.resolved_at == "2026-03-09T10:00:00+00:00"

    def test_json_roundtrip_float_precision(self, db_path: Path) -> None:
        """JSON round-trip preserves various float values exactly."""
        resolved = ResolvedParameters(
            car_name="float_car",
            tier=ResolutionTier.OPEN_DATA,
            parameters={
                "PARAM_A": ParameterRange(
                    section="PARAM_A",
                    parameter="VALUE",
                    min_value=-0.001,
                    max_value=99999.9999,
                    step=0.0001,
                    default_value=50000.12345,
                    show_clicks=0,
                    storage_convention="direct",
                ),
                "PARAM_B": ParameterRange(
                    section="PARAM_B",
                    parameter="VALUE",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.1,
                    default_value=None,
                    show_clicks=0,
                    storage_convention="direct",
                ),
            },
            has_defaults=True,
            resolved_at="2026-03-08T14:30:00+00:00",
        )
        save_to_cache(db_path, resolved)
        loaded = get_cached_parameters(db_path, "float_car")

        assert loaded is not None
        pa = loaded.parameters["PARAM_A"]
        assert pa.min_value == pytest.approx(-0.001)
        assert pa.max_value == pytest.approx(99999.9999)
        assert pa.step == pytest.approx(0.0001)
        assert pa.default_value == pytest.approx(50000.12345)

        pb = loaded.parameters["PARAM_B"]
        assert pb.default_value is None


class TestStaleCacheDetection:
    """T020-T021 — Stale cache entries with missing show_clicks are rejected."""

    def test_stale_entry_returns_none(self, db_path: Path) -> None:
        """T020: Cached params with show_clicks=None are detected as stale."""
        resolved = _make_resolved(include_show_clicks=False)
        assert all(pr.show_clicks is None for pr in resolved.parameters.values())
        save_to_cache(db_path, resolved)

        loaded = get_cached_parameters(db_path, "test_car")
        assert loaded is None  # stale detection triggered

    def test_fresh_entry_returns_cached(self, db_path: Path) -> None:
        """T021: Cached params with show_clicks set are returned normally."""
        resolved = ResolvedParameters(
            car_name="fresh_car",
            tier=ResolutionTier(1),
            parameters={
                "ARB_FRONT": ParameterRange(
                    section="ARB_FRONT", parameter="VALUE",
                    min_value=25500, max_value=48000, step=4500,
                    default_value=None,
                    show_clicks=2, storage_convention="index",
                ),
                "PRESSURE_LF": ParameterRange(
                    section="PRESSURE_LF", parameter="VALUE",
                    min_value=20.0, max_value=35.0, step=0.5,
                    default_value=None,
                    show_clicks=0, storage_convention="direct",
                ),
            },
            has_defaults=False,
            resolved_at="2026-03-11T10:00:00+00:00",
        )
        save_to_cache(db_path, resolved)

        loaded = get_cached_parameters(db_path, "fresh_car")
        assert loaded is not None
        assert loaded.car_name == "fresh_car"
        assert loaded.parameters["ARB_FRONT"].show_clicks == 2


class TestCacheIntegration:
    """T016 — Cache integration in resolve_parameters()."""

    def test_cache_hit_returns_cached_result(self, db_path: Path) -> None:
        """resolve_parameters returns cached result when cache hit exists."""
        cached = _make_resolved("ks_test_car", tier=1)
        save_to_cache(db_path, cached)

        # Resolve with no ac_install_path — would normally fall through to tier 3,
        # but cache hit should return tier 1 result.
        result = resolve_parameters(
            ac_install_path=None,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.tier == ResolutionTier.OPEN_DATA
        assert result.car_name == "ks_test_car"
        assert result.resolved_at == cached.resolved_at

    def test_tier1_writes_to_cache(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        """resolve_parameters writes to cache after successful Tier 1 resolution."""
        # Ensure cache is empty
        assert get_cached_parameters(db_path, "ks_test_car") is None

        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.tier == ResolutionTier.OPEN_DATA

        # Cache should now have the entry
        cached = get_cached_parameters(db_path, "ks_test_car")
        assert cached is not None
        assert cached.tier == ResolutionTier.OPEN_DATA
        assert set(cached.parameters.keys()) == set(result.parameters.keys())

    def test_tier2_writes_to_cache(
        self, sample_acd_car_dir: Path, db_path: Path
    ) -> None:
        """resolve_parameters writes to cache after successful Tier 2 resolution."""
        assert get_cached_parameters(db_path, "ks_test_car") is None

        result = resolve_parameters(
            ac_install_path=sample_acd_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.tier == ResolutionTier.ACD_ARCHIVE

        cached = get_cached_parameters(db_path, "ks_test_car")
        assert cached is not None
        assert cached.tier == ResolutionTier.ACD_ARCHIVE

    def test_tier3_not_cached(self, db_path: Path) -> None:
        """Tier 3 results are NOT written to cache."""
        session_setup = {
            "CAMBER_LF": {"VALUE": -3.2},
            "WING_1": {"VALUE": 6},
        }

        result = resolve_parameters(
            ac_install_path=None,
            car_name="unknown_car",
            db_path=db_path,
            session_setup=session_setup,
        )
        assert result.tier == ResolutionTier.SESSION_FALLBACK

        cached = get_cached_parameters(db_path, "unknown_car")
        assert cached is None

    def test_cached_tier_and_resolved_at_match(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        """Cached tier and resolved_at match the original resolution."""
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )

        cached = get_cached_parameters(db_path, "ks_test_car")
        assert cached is not None
        assert cached.tier == result.tier
        assert cached.resolved_at == result.resolved_at
