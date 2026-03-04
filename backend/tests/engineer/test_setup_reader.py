"""Tests for setup parameter range reader."""

from __future__ import annotations

import textwrap
from pathlib import Path

from ac_engineer.engineer.models import ParameterRange
from ac_engineer.engineer.setup_reader import get_parameter_range, read_parameter_ranges


# ---------------------------------------------------------------------------
# T018: Valid data parsing
# ---------------------------------------------------------------------------


class TestValidDataParsing:
    def test_reads_complete_setup_ini(self, sample_car_data_dir: Path):
        ranges = read_parameter_ranges(sample_car_data_dir, "test_car")
        assert len(ranges) >= 4
        assert "CAMBER_LF" in ranges
        assert "PRESSURE_LF" in ranges
        assert "WING_1" in ranges

    def test_min_max_step_parsed_as_floats(self, sample_car_data_dir: Path):
        ranges = read_parameter_ranges(sample_car_data_dir, "test_car")
        cam = ranges["CAMBER_LF"]
        assert cam.min_value == -5.0
        assert cam.max_value == 0.0
        assert cam.step == 0.1

    def test_default_value_populated(self, sample_car_data_dir: Path):
        ranges = read_parameter_ranges(sample_car_data_dir, "test_car")
        spring = ranges["SPRING_RATE_LF"]
        assert spring.default_value == 80000.0

    def test_section_name_matches_key(self, sample_car_data_dir: Path):
        ranges = read_parameter_ranges(sample_car_data_dir, "test_car")
        for key, pr in ranges.items():
            assert pr.section == key


# ---------------------------------------------------------------------------
# T019: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_none_path_returns_empty(self):
        assert read_parameter_ranges(None, "any_car") == {}

    def test_nonexistent_path_returns_empty(self, tmp_path: Path):
        assert read_parameter_ranges(tmp_path / "nope", "car") == {}

    def test_missing_car_dir_returns_empty(self, tmp_path: Path):
        assert read_parameter_ranges(tmp_path, "nonexistent_car") == {}

    def test_missing_setup_ini_returns_empty(self, tmp_path: Path):
        car_dir = tmp_path / "content" / "cars" / "test_car" / "data"
        car_dir.mkdir(parents=True)
        # No setup.ini file
        assert read_parameter_ranges(tmp_path, "test_car") == {}

    def test_malformed_section_skipped(self, tmp_path: Path):
        data_dir = tmp_path / "content" / "cars" / "test_car" / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "setup.ini").write_text(
            textwrap.dedent("""\
                [GOOD]
                MIN=0.0
                MAX=10.0
                STEP=1.0

                [BAD_NO_MAX]
                MIN=0.0
                STEP=1.0

                [BAD_NAN]
                MIN=abc
                MAX=10.0
                STEP=1.0
            """),
            encoding="utf-8",
        )
        ranges = read_parameter_ranges(tmp_path, "test_car")
        assert "GOOD" in ranges
        assert "BAD_NO_MAX" not in ranges
        assert "BAD_NAN" not in ranges

    def test_get_parameter_range_unknown_section(self, sample_car_data_dir: Path):
        ranges = read_parameter_ranges(sample_car_data_dir, "test_car")
        assert get_parameter_range(ranges, "NONEXISTENT") is None
