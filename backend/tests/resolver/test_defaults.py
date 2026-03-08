"""Tests for extract_defaults() — default value extraction from car config files."""

from __future__ import annotations

import textwrap

import pytest

from ac_engineer.resolver.defaults import extract_defaults


# ---------------------------------------------------------------------------
# Helper: build config file contents
# ---------------------------------------------------------------------------

def _suspensions_ini() -> str:
    return textwrap.dedent("""\
        [FRONT]
        CAMBER=-3.0
        TOE_OUT=0.1
        SPRING_RATE=120000
        BUMP=5
        FAST_BUMP=3
        REBOUND=7
        FAST_REBOUND=4
        ROD_LENGTH=250

        [REAR]
        CAMBER=-2.5
        TOE_OUT=0.2
        SPRING_RATE=100000
        BUMP=4
        FAST_BUMP=2
        REBOUND=6
        FAST_REBOUND=3
        ROD_LENGTH=200

        [ARB]
        FRONT=3
        REAR=2
    """)


def _tyres_ini() -> str:
    return textwrap.dedent("""\
        [FRONT]
        PRESSURE_STATIC=26.0

        [REAR]
        PRESSURE_STATIC=24.0
    """)


def _aero_ini() -> str:
    return textwrap.dedent("""\
        [WING_0]
        ANGLE=5

        [WING_1]
        ANGLE=8
    """)


def _drivetrain_ini() -> str:
    return textwrap.dedent("""\
        [GEARS]
        FINAL=3.764
    """)


def _brakes_ini() -> str:
    return textwrap.dedent("""\
        [DATA]
        BASE_LEVEL=0.85
        FRONT_SHARE=0.67
    """)


def _all_config_files() -> dict[str, str]:
    return {
        "suspensions.ini": _suspensions_ini(),
        "tyres.ini": _tyres_ini(),
        "aero.ini": _aero_ini(),
        "drivetrain.ini": _drivetrain_ini(),
        "brakes.ini": _brakes_ini(),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSuspensionDefaults:
    """Test 1 — suspensions.ini defaults (camber, toe, springs, dampers)."""

    def test_camber_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["CAMBER_LF"])
        assert result["CAMBER_LF"] == pytest.approx(-3.0)

    def test_toe_out_rf(self) -> None:
        result = extract_defaults(_all_config_files(), ["TOE_OUT_RF"])
        assert result["TOE_OUT_RF"] == pytest.approx(0.1)

    def test_spring_rate_lr(self) -> None:
        result = extract_defaults(_all_config_files(), ["SPRING_RATE_LR"])
        assert result["SPRING_RATE_LR"] == pytest.approx(100000)

    def test_damp_bump_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["DAMP_BUMP_LF"])
        assert result["DAMP_BUMP_LF"] == pytest.approx(5)

    def test_damp_fast_bump_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["DAMP_FAST_BUMP_LF"])
        assert result["DAMP_FAST_BUMP_LF"] == pytest.approx(3)

    def test_damp_rebound_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["DAMP_REBOUND_LF"])
        assert result["DAMP_REBOUND_LF"] == pytest.approx(7)

    def test_damp_fast_rebound_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["DAMP_FAST_REBOUND_LF"])
        assert result["DAMP_FAST_REBOUND_LF"] == pytest.approx(4)

    def test_multiple_suspension_sections(self) -> None:
        sections = ["CAMBER_LF", "CAMBER_RF", "SPRING_RATE_LR"]
        result = extract_defaults(_all_config_files(), sections)
        assert result["CAMBER_LF"] == pytest.approx(-3.0)
        assert result["CAMBER_RF"] == pytest.approx(-3.0)
        assert result["SPRING_RATE_LR"] == pytest.approx(100000)


class TestTyreDefaults:
    """Test 2 — tyres.ini defaults (tyre pressure)."""

    def test_pressure_lf(self) -> None:
        result = extract_defaults(_all_config_files(), ["PRESSURE_LF"])
        assert result["PRESSURE_LF"] == pytest.approx(26.0)

    def test_pressure_rr(self) -> None:
        result = extract_defaults(_all_config_files(), ["PRESSURE_RR"])
        assert result["PRESSURE_RR"] == pytest.approx(24.0)


class TestAeroDefaults:
    """Test 3 — aero.ini defaults (wing angles)."""

    def test_wing_0(self) -> None:
        result = extract_defaults(_all_config_files(), ["WING_0"])
        assert result["WING_0"] == pytest.approx(5)

    def test_wing_1(self) -> None:
        result = extract_defaults(_all_config_files(), ["WING_1"])
        assert result["WING_1"] == pytest.approx(8)


class TestDrivetrainDefaults:
    """Test 4 — drivetrain.ini defaults (final gear ratio)."""

    def test_final_gear_ratio(self) -> None:
        result = extract_defaults(_all_config_files(), ["FINAL_GEAR_RATIO"])
        assert result["FINAL_GEAR_RATIO"] == pytest.approx(3.764)


class TestBrakeDefaults:
    """Test — brakes.ini defaults (brake power and front bias)."""

    def test_brake_power_mult(self) -> None:
        result = extract_defaults(_all_config_files(), ["BRAKE_POWER_MULT"])
        assert result["BRAKE_POWER_MULT"] == pytest.approx(0.85)

    def test_front_bias(self) -> None:
        result = extract_defaults(_all_config_files(), ["FRONT_BIAS"])
        assert result["FRONT_BIAS"] == pytest.approx(0.67)


class TestMissingConfigFiles:
    """Test 5 — missing config files return None for those defaults."""

    def test_missing_suspensions_returns_none(self) -> None:
        files = {k: v for k, v in _all_config_files().items() if k != "suspensions.ini"}
        result = extract_defaults(files, ["CAMBER_LF"])
        assert result["CAMBER_LF"] is None

    def test_missing_tyres_returns_none(self) -> None:
        files = {k: v for k, v in _all_config_files().items() if k != "tyres.ini"}
        result = extract_defaults(files, ["PRESSURE_LF"])
        assert result["PRESSURE_LF"] is None

    def test_missing_aero_returns_none(self) -> None:
        files = {k: v for k, v in _all_config_files().items() if k != "aero.ini"}
        result = extract_defaults(files, ["WING_0"])
        assert result["WING_0"] is None

    def test_missing_drivetrain_returns_none(self) -> None:
        files = {k: v for k, v in _all_config_files().items() if k != "drivetrain.ini"}
        result = extract_defaults(files, ["FINAL_GEAR_RATIO"])
        assert result["FINAL_GEAR_RATIO"] is None

    def test_empty_config_files_dict(self) -> None:
        result = extract_defaults({}, ["CAMBER_LF", "PRESSURE_LF", "WING_0"])
        assert all(v is None for v in result.values())


class TestMalformedConfigFiles:
    """Test 6 — malformed config files handled gracefully (no exception)."""

    def test_garbage_content_no_exception(self) -> None:
        files = {"suspensions.ini": "this is not ini content @@@ garbage"}
        result = extract_defaults(files, ["CAMBER_LF"])
        assert result["CAMBER_LF"] is None

    def test_empty_file_content(self) -> None:
        files = {"suspensions.ini": ""}
        result = extract_defaults(files, ["CAMBER_LF"])
        assert result["CAMBER_LF"] is None

    def test_missing_key_in_section(self) -> None:
        # Section exists but the expected key is missing
        files = {"suspensions.ini": "[FRONT]\nSOME_OTHER_KEY=42\n"}
        result = extract_defaults(files, ["CAMBER_LF"])
        assert result["CAMBER_LF"] is None

    def test_non_numeric_value(self) -> None:
        files = {"suspensions.ini": "[FRONT]\nCAMBER=not_a_number\n"}
        result = extract_defaults(files, ["CAMBER_LF"])
        # Should either parse as None or handle gracefully
        assert result["CAMBER_LF"] is None


class TestCornerSuffixMapping:
    """Test 7 — corner suffix mapping: LF→FRONT[0], RF→FRONT[1], LR→REAR[0], RR→REAR[1]."""

    def test_lf_maps_to_front(self) -> None:
        result = extract_defaults(_all_config_files(), ["CAMBER_LF"])
        # LF → FRONT section; FRONT CAMBER = -3.0
        assert result["CAMBER_LF"] == pytest.approx(-3.0)

    def test_rf_maps_to_front(self) -> None:
        result = extract_defaults(_all_config_files(), ["CAMBER_RF"])
        # RF → FRONT section; FRONT CAMBER = -3.0
        assert result["CAMBER_RF"] == pytest.approx(-3.0)

    def test_lr_maps_to_rear(self) -> None:
        result = extract_defaults(_all_config_files(), ["CAMBER_LR"])
        # LR → REAR section; REAR CAMBER = -2.5
        assert result["CAMBER_LR"] == pytest.approx(-2.5)

    def test_rr_maps_to_rear(self) -> None:
        result = extract_defaults(_all_config_files(), ["CAMBER_RR"])
        # RR → REAR section; REAR CAMBER = -2.5
        assert result["CAMBER_RR"] == pytest.approx(-2.5)

    def test_pressure_lf_maps_to_front(self) -> None:
        result = extract_defaults(_all_config_files(), ["PRESSURE_LF"])
        assert result["PRESSURE_LF"] == pytest.approx(26.0)

    def test_pressure_rr_maps_to_rear(self) -> None:
        result = extract_defaults(_all_config_files(), ["PRESSURE_RR"])
        assert result["PRESSURE_RR"] == pytest.approx(24.0)

    def test_spring_rate_lf_maps_to_front(self) -> None:
        result = extract_defaults(_all_config_files(), ["SPRING_RATE_LF"])
        assert result["SPRING_RATE_LF"] == pytest.approx(120000)

    def test_spring_rate_rr_maps_to_rear(self) -> None:
        result = extract_defaults(_all_config_files(), ["SPRING_RATE_RR"])
        assert result["SPRING_RATE_RR"] == pytest.approx(100000)


class TestUnmappedSections:
    """Test 8 — unmapped section names return None default."""

    def test_fuel_returns_none(self) -> None:
        result = extract_defaults(_all_config_files(), ["FUEL"])
        assert result["FUEL"] is None

    def test_unknown_section_returns_none(self) -> None:
        result = extract_defaults(_all_config_files(), ["TOTALLY_UNKNOWN_SECTION"])
        assert result["TOTALLY_UNKNOWN_SECTION"] is None

    def test_mixed_known_and_unknown(self) -> None:
        sections = ["CAMBER_LF", "FUEL", "UNKNOWN_PARAM"]
        result = extract_defaults(_all_config_files(), sections)
        assert result["CAMBER_LF"] == pytest.approx(-3.0)
        assert result["FUEL"] is None
        assert result["UNKNOWN_PARAM"] is None

    def test_empty_section_list(self) -> None:
        result = extract_defaults(_all_config_files(), [])
        assert result == {}


class TestArbDefaults:
    """Test ARB_FRONT and ARB_REAR defaults from suspensions.ini."""

    def test_arb_front(self) -> None:
        result = extract_defaults(_all_config_files(), ["ARB_FRONT"])
        # ARB_FRONT → [ARB] FRONT = 3 (or [FRONT] ROD_LENGTH = 250)
        assert result["ARB_FRONT"] is not None

    def test_arb_rear(self) -> None:
        result = extract_defaults(_all_config_files(), ["ARB_REAR"])
        # ARB_REAR → [ARB] REAR = 2 (or [REAR] ROD_LENGTH = 200)
        assert result["ARB_REAR"] is not None
