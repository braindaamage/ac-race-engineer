"""Tests for AC asset metadata reader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ac_engineer.resolver.ac_assets import (
    CarInfo,
    TrackInfo,
    _format_name,
    _parse_length,
    _validate_identifier,
    car_badge_path,
    read_car_info,
    read_track_info,
    track_preview_path,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# _format_name
# ---------------------------------------------------------------------------


class TestFormatName:
    def test_strips_ks_prefix(self):
        assert _format_name("ks_ferrari_488_gt3") == "ferrari 488 gt3"

    def test_strips_ac_prefix(self):
        assert _format_name("ac_legends_fiat_131") == "legends fiat 131"

    def test_replaces_underscores(self):
        assert _format_name("some_modded_car") == "some modded car"

    def test_no_prefix(self):
        assert _format_name("ferrari") == "ferrari"


# ---------------------------------------------------------------------------
# _validate_identifier
# ---------------------------------------------------------------------------


class TestValidateIdentifier:
    def test_valid_name(self):
        _validate_identifier("ks_ferrari_488_gt3")  # no exception

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            _validate_identifier("")

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError):
            _validate_identifier("../../etc/passwd")

    def test_rejects_forward_slash(self):
        with pytest.raises(ValueError):
            _validate_identifier("foo/bar")

    def test_rejects_backslash(self):
        with pytest.raises(ValueError):
            _validate_identifier("foo\\bar")


# ---------------------------------------------------------------------------
# _parse_length
# ---------------------------------------------------------------------------


class TestParseLength:
    def test_meters(self):
        assert _parse_length("5793 m") == 5793.0

    def test_kilometers(self):
        assert _parse_length("5.793 km") == 5793.0

    def test_no_unit(self):
        assert _parse_length("1234") == 1234.0

    def test_invalid(self):
        assert _parse_length("unknown") is None

    def test_empty(self):
        assert _parse_length("") is None


# ---------------------------------------------------------------------------
# read_car_info
# ---------------------------------------------------------------------------


class TestReadCarInfo:
    def test_valid_json(self, tmp_path):
        car_dir = tmp_path / "ks_ferrari_488_gt3" / "ui"
        car_dir.mkdir(parents=True)
        (car_dir / "ui_car.json").write_text(
            json.dumps(FIXTURES.joinpath("ui_car_valid.json").read_text()),
        )
        # Use the actual fixture directly
        import shutil
        shutil.copy(FIXTURES / "ui_car_valid.json", car_dir / "ui_car.json")
        info = read_car_info(tmp_path, "ks_ferrari_488_gt3")
        assert info.display_name == "Ferrari 488 GT3"
        assert info.brand == "Ferrari"
        assert info.car_class == "GT3"

    def test_missing_json_falls_back(self, tmp_path):
        info = read_car_info(tmp_path, "ks_ferrari_488_gt3")
        assert info.display_name == "ferrari 488 gt3"
        assert info.brand == ""

    def test_missing_fields(self, tmp_path):
        car_dir = tmp_path / "some_mod" / "ui"
        car_dir.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "ui_car_minimal.json", car_dir / "ui_car.json")
        info = read_car_info(tmp_path, "some_mod")
        assert info.display_name == "Some Mod Car"
        assert info.brand == ""
        assert info.car_class == ""

    def test_none_path(self):
        info = read_car_info(None, "ks_ferrari_488_gt3")
        assert info.display_name == "ferrari 488 gt3"


# ---------------------------------------------------------------------------
# read_track_info
# ---------------------------------------------------------------------------


class TestReadTrackInfo:
    def test_base_layout(self, tmp_path):
        track_dir = tmp_path / "ks_monza" / "ui"
        track_dir.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "ui_track_valid.json", track_dir / "ui_track.json")
        info = read_track_info(tmp_path, "ks_monza")
        assert info.display_name == "Autodromo Nazionale Monza"
        assert info.country == "Italy"
        assert info.length_m == 5793.0

    def test_layout_specific(self, tmp_path):
        layout_dir = tmp_path / "ks_nurburgring" / "ui" / "layout_gp"
        layout_dir.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "ui_track_layout.json", layout_dir / "ui_track.json")
        info = read_track_info(tmp_path, "ks_nurburgring", "gp")
        assert info.display_name == "Nürburgring - GP"
        assert info.country == "Germany"
        assert info.length_m == 5137.0

    def test_missing_falls_back(self, tmp_path):
        info = read_track_info(tmp_path, "ks_monza")
        assert info.display_name == "monza"

    def test_none_path(self):
        info = read_track_info(None, "ks_monza")
        assert info.display_name == "monza"


# ---------------------------------------------------------------------------
# car_badge_path / track_preview_path
# ---------------------------------------------------------------------------


class TestBadgePath:
    def test_exists(self, tmp_path):
        badge = tmp_path / "ks_ferrari_488_gt3" / "ui" / "badge.png"
        badge.parent.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "badge.png", badge)
        result = car_badge_path(tmp_path, "ks_ferrari_488_gt3")
        assert result is not None
        assert result.name == "badge.png"

    def test_missing(self, tmp_path):
        assert car_badge_path(tmp_path, "nonexistent") is None

    def test_none_path(self):
        assert car_badge_path(None, "anything") is None

    def test_path_traversal(self):
        assert car_badge_path("/some/path", "../etc") is None


class TestPreviewPath:
    def test_base_layout(self, tmp_path):
        preview = tmp_path / "ks_monza" / "ui" / "preview.png"
        preview.parent.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "preview.png", preview)
        result = track_preview_path(tmp_path, "ks_monza")
        assert result is not None
        assert result.name == "preview.png"

    def test_layout_specific(self, tmp_path):
        preview = tmp_path / "ks_nurburgring" / "ui" / "layout_gp" / "preview.png"
        preview.parent.mkdir(parents=True)
        import shutil
        shutil.copy(FIXTURES / "preview.png", preview)
        result = track_preview_path(tmp_path, "ks_nurburgring", "gp")
        assert result is not None

    def test_missing(self, tmp_path):
        assert track_preview_path(tmp_path, "nonexistent") is None

    def test_none_path(self):
        assert track_preview_path(None, "anything") is None
