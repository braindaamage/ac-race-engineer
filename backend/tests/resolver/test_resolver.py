"""Tests for resolve_parameters() — tiered parameter resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ac_engineer.acd_reader import AcdResult
from ac_engineer.resolver.models import ResolvedParameters, ResolutionTier
from ac_engineer.resolver.resolver import list_cars, resolve_parameters


class TestTier1OpenData:
    """Test 1 — car with open data/setup.ini returns ranges with defaults and tier=1."""

    def test_returns_tier_1(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert isinstance(result, ResolvedParameters)
        assert result.tier == ResolutionTier.OPEN_DATA
        assert result.car_name == "ks_test_car"

    def test_has_parameters(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert len(result.parameters) > 0

    def test_has_defaults(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.has_defaults is True

    def test_parameter_ranges_populated(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        # sample_car_dir fixture has CAMBER_LF with MIN=-4.0, MAX=0.0, STEP=0.1
        assert "CAMBER_LF" in result.parameters
        pr = result.parameters["CAMBER_LF"]
        assert pr.min_value == pytest.approx(-4.0)
        assert pr.max_value == pytest.approx(0.0)
        assert pr.step == pytest.approx(0.1)


class TestTier2AcdArchive:
    """Test 2 — car with only data.acd returns ranges with defaults and tier=2."""

    def test_returns_tier_2(
        self, sample_acd_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_acd_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert isinstance(result, ResolvedParameters)
        assert result.tier == ResolutionTier.ACD_ARCHIVE

    def test_has_parameters(
        self, sample_acd_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_acd_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert len(result.parameters) > 0

    def test_has_defaults(
        self, sample_acd_car_dir: Path, db_path: Path
    ) -> None:
        result = resolve_parameters(
            ac_install_path=sample_acd_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.has_defaults is True


class TestTier2FallthroughOnFailure:
    """Test 3 — ACD with third-party encryption falls through to Tier 3."""

    def test_falls_to_tier_3_on_acd_failure(
        self, sample_acd_car_dir: Path, db_path: Path
    ) -> None:
        with patch(
            "ac_engineer.acd_reader.read_acd",
            return_value=AcdResult.failure("Unsupported encryption scheme"),
        ):
            result = resolve_parameters(
                ac_install_path=sample_acd_car_dir,
                car_name="ks_test_car",
                db_path=db_path,
            )
        assert result.tier == ResolutionTier.SESSION_FALLBACK


class TestTier3SessionFallback:
    """Test 4 — car with neither open data nor decryptable archive uses session_setup."""

    def test_returns_tier_3(
        self,
        tmp_path: Path,
        db_path: Path,
        sample_session_setup: dict[str, dict[str, float | str]],
    ) -> None:
        # Create a car directory with no data/ and no data.acd
        car_dir = tmp_path / "content" / "cars" / "mod_car"
        car_dir.mkdir(parents=True)
        result = resolve_parameters(
            ac_install_path=tmp_path,
            car_name="mod_car",
            db_path=db_path,
            session_setup=sample_session_setup,
        )
        assert result.tier == ResolutionTier.SESSION_FALLBACK

    def test_uses_session_setup_values(
        self,
        tmp_path: Path,
        db_path: Path,
        sample_session_setup: dict[str, dict[str, float | str]],
    ) -> None:
        car_dir = tmp_path / "content" / "cars" / "mod_car"
        car_dir.mkdir(parents=True)
        result = resolve_parameters(
            ac_install_path=tmp_path,
            car_name="mod_car",
            db_path=db_path,
            session_setup=sample_session_setup,
        )
        assert len(result.parameters) > 0


class TestTier3NoSessionSetup:
    """Test 5 — Tier 3 with no session_setup returns empty parameters."""

    def test_empty_parameters(self, tmp_path: Path, db_path: Path) -> None:
        car_dir = tmp_path / "content" / "cars" / "mod_car"
        car_dir.mkdir(parents=True)
        result = resolve_parameters(
            ac_install_path=tmp_path,
            car_name="mod_car",
            db_path=db_path,
            session_setup=None,
        )
        assert result.tier == ResolutionTier.SESSION_FALLBACK
        assert len(result.parameters) == 0


class TestTier1Precedence:
    """Test 6 — car with both data/ folder and data.acd uses Tier 1 only."""

    def test_prefers_open_data_over_acd(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        # sample_car_dir already has data/ folder; add a data.acd too
        car_path = sample_car_dir / "content" / "cars" / "ks_test_car"
        (car_path / "data.acd").write_bytes(b"dummy acd content")
        result = resolve_parameters(
            ac_install_path=sample_car_dir,
            car_name="ks_test_car",
            db_path=db_path,
        )
        assert result.tier == ResolutionTier.OPEN_DATA


class TestOpenDataMissingSetupIni:
    """Test 7 — open data folder exists but setup.ini missing falls through to Tier 2."""

    def test_falls_to_next_tier(self, tmp_path: Path, db_path: Path) -> None:
        data_dir = tmp_path / "content" / "cars" / "mod_car" / "data"
        data_dir.mkdir(parents=True)
        # data/ folder exists but no setup.ini inside it
        (data_dir / "car.ini").write_text("[HEADER]\nVERSION=1\n", encoding="utf-8")
        result = resolve_parameters(
            ac_install_path=tmp_path,
            car_name="mod_car",
            db_path=db_path,
        )
        # Should fall through Tier 1 (no setup.ini) and Tier 2 (no data.acd) to Tier 3
        assert result.tier != ResolutionTier.OPEN_DATA


class TestNullInstallPath:
    """Test 8 — ac_install_path=None goes directly to Tier 3."""

    def test_none_path_tier_3(
        self,
        db_path: Path,
        sample_session_setup: dict[str, dict[str, float | str]],
    ) -> None:
        result = resolve_parameters(
            ac_install_path=None,
            car_name="any_car",
            db_path=db_path,
            session_setup=sample_session_setup,
        )
        assert result.tier == ResolutionTier.SESSION_FALLBACK

    def test_none_path_no_session(self, db_path: Path) -> None:
        result = resolve_parameters(
            ac_install_path=None,
            car_name="any_car",
            db_path=db_path,
        )
        assert result.tier == ResolutionTier.SESSION_FALLBACK
        assert len(result.parameters) == 0


class TestNeverRaises:
    """Test 9 — resolve_parameters() never raises, always returns ResolvedParameters."""

    def test_bad_install_path(self, db_path: Path) -> None:
        result = resolve_parameters(
            ac_install_path=Path("/nonexistent/path/that/does/not/exist"),
            car_name="fake_car",
            db_path=db_path,
        )
        assert isinstance(result, ResolvedParameters)

    def test_empty_car_name(self, db_path: Path) -> None:
        result = resolve_parameters(
            ac_install_path=Path("/some/path"),
            car_name="",
            db_path=db_path,
        )
        assert isinstance(result, ResolvedParameters)

    def test_corrupt_acd_file(self, tmp_path: Path, db_path: Path) -> None:
        car_dir = tmp_path / "content" / "cars" / "bad_car"
        car_dir.mkdir(parents=True)
        (car_dir / "data.acd").write_bytes(b"\x00\x01\x02corrupt")
        result = resolve_parameters(
            ac_install_path=tmp_path,
            car_name="bad_car",
            db_path=db_path,
        )
        assert isinstance(result, ResolvedParameters)

    def test_db_path_nonexistent_dir(self, tmp_path: Path) -> None:
        bad_db = tmp_path / "no" / "such" / "dir" / "test.db"
        result = resolve_parameters(
            ac_install_path=None,
            car_name="any_car",
            db_path=bad_db,
        )
        assert isinstance(result, ResolvedParameters)


# -- US3: list_cars tests --

class TestListCars:
    """Tests for list_cars() function."""

    def test_returns_sorted_car_names(self, sample_car_dir: Path, db_path: Path) -> None:
        # Create additional car dirs
        cars_base = sample_car_dir / "content" / "cars"
        (cars_base / "zzz_car").mkdir()
        (cars_base / "aaa_car").mkdir()

        result = list_cars(sample_car_dir, db_path)
        names = [c.car_name for c in result]
        assert names == sorted(names)

    def test_cached_car_shows_resolved(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        # Resolve the car first to populate cache
        resolve_parameters(sample_car_dir, "ks_test_car", db_path)

        result = list_cars(sample_car_dir, db_path)
        car = next(c for c in result if c.car_name == "ks_test_car")
        assert car.status == "resolved"
        assert car.tier is not None
        assert car.resolved_at is not None

    def test_uncached_car_shows_unresolved(
        self, sample_car_dir: Path, db_path: Path
    ) -> None:
        # Create a car dir that's not cached
        (sample_car_dir / "content" / "cars" / "uncached_car").mkdir()

        result = list_cars(sample_car_dir, db_path)
        car = next(c for c in result if c.car_name == "uncached_car")
        assert car.status == "unresolved"
        assert car.tier is None
        assert car.resolved_at is None

    def test_none_path_raises_value_error(self, db_path: Path) -> None:
        with pytest.raises(ValueError):
            list_cars(None, db_path)

    def test_missing_cars_dir_raises_value_error(
        self, tmp_path: Path, db_path: Path
    ) -> None:
        with pytest.raises(ValueError):
            list_cars(tmp_path, db_path)
