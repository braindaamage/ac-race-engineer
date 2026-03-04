"""Unit tests for setup_parser: parse_ini and associate_setup."""

import pytest

from ac_engineer.parser.models import SetupEntry, SetupParameter
from ac_engineer.parser.setup_parser import associate_setup, parse_ini


# ---------------------------------------------------------------------------
# parse_ini
# ---------------------------------------------------------------------------

class TestParseIni:
    def test_none_input_returns_empty(self):
        assert parse_ini(None) == []

    def test_empty_string_returns_empty(self):
        assert parse_ini("") == []

    def test_whitespace_only_returns_empty(self):
        assert parse_ini("   \n\t  ") == []

    def test_standard_ini_numeric(self):
        ini = "[FRONT]\nCAMBER=-2.5\nTOE=0.1\n"
        params = parse_ini(ini)
        assert len(params) == 2
        front_params = {p.name: p.value for p in params}
        assert front_params["CAMBER"] == -2.5
        assert front_params["TOE"] == 0.1

    def test_multi_section(self):
        ini = "[FRONT]\nCAMBER=-2.5\n\n[REAR]\nCAMBER=-1.8\nTOE=0.05\n"
        params = parse_ini(ini)
        sections = {p.section for p in params}
        assert "FRONT" in sections
        assert "REAR" in sections
        assert len(params) == 3

    def test_numeric_value_stored_as_float(self):
        ini = "[TYRES]\nPRESSURE=27.5\n"
        params = parse_ini(ini)
        assert isinstance(params[0].value, float)
        assert params[0].value == 27.5

    def test_non_numeric_value_stored_as_str(self):
        ini = "[TYRES]\nCOMPOUND=SOFT\n"
        params = parse_ini(ini)
        assert isinstance(params[0].value, str)
        assert params[0].value == "SOFT"

    def test_comments_ignored(self):
        ini = "; this is a comment\n[FRONT]\n# another comment\nCAMBER=-2.5\n"
        params = parse_ini(ini)
        assert len(params) == 1
        assert params[0].name == "CAMBER"

    def test_blank_lines_ignored(self):
        ini = "\n[FRONT]\n\nCAMBER=-2.5\n\n\n[REAR]\nCAMBER=-1.8\n"
        params = parse_ini(ini)
        assert len(params) == 2

    def test_40_parameter_mod_ini(self):
        lines = ["[SECTION_A]"]
        for i in range(20):
            lines.append(f"PARAM_{i}={i * 0.1:.1f}")
        lines.append("[SECTION_B]")
        for i in range(20):
            lines.append(f"PARAM_{i}={i * 0.2:.1f}")
        ini = "\n".join(lines)
        params = parse_ini(ini)
        assert len(params) == 40

    def test_section_casing_preserved(self):
        ini = "[MySection]\nmy_param=1.0\n"
        params = parse_ini(ini)
        assert params[0].section == "MySection"
        assert params[0].name == "my_param"

    def test_integer_value_stored_as_float(self):
        ini = "[MISC]\nGEAR_RATIO=5\n"
        params = parse_ini(ini)
        assert isinstance(params[0].value, float)
        assert params[0].value == 5.0

    def test_negative_float_value(self):
        ini = "[FRONT]\nCAMBER=-3.0\n"
        params = parse_ini(ini)
        assert params[0].value == -3.0


# ---------------------------------------------------------------------------
# associate_setup
# ---------------------------------------------------------------------------

def _make_entry(lap_start: int) -> SetupEntry:
    return SetupEntry(
        lap_start=lap_start,
        trigger="session_start" if lap_start == 0 else "pit_exit",
        timestamp="2026-03-02T14:30:00",
    )


class TestAssociateSetup:
    def test_empty_entries_returns_none(self):
        assert associate_setup(5, []) is None

    def test_single_entry_at_lap_0(self):
        entries = [_make_entry(0)]
        result = associate_setup(5, entries)
        assert result is not None
        assert result.lap_start == 0

    def test_lap_before_first_entry_returns_none(self):
        # No entry with lap_start <= 5 ... wait, entry at 0 covers all laps >= 0
        # Test: lap -1 (should not happen in practice, but guard it)
        entries = [_make_entry(0)]
        result = associate_setup(0, entries)
        assert result is not None
        assert result.lap_start == 0

    def test_exact_boundary_lap(self):
        entries = [_make_entry(0), _make_entry(6)]
        result = associate_setup(6, entries)
        assert result.lap_start == 6

    def test_lap_5_uses_entry_0_with_two_entries(self):
        entries = [_make_entry(0), _make_entry(6)]
        result = associate_setup(5, entries)
        assert result.lap_start == 0

    def test_lap_7_uses_entry_6_with_three_entries(self):
        entries = [_make_entry(0), _make_entry(6), _make_entry(12)]
        result = associate_setup(7, entries)
        assert result.lap_start == 6

    def test_lap_15_uses_entry_12_with_three_entries(self):
        entries = [_make_entry(0), _make_entry(6), _make_entry(12)]
        result = associate_setup(15, entries)
        assert result.lap_start == 12

    def test_lap_before_all_entries_returns_none(self):
        # Entry starts at lap 5, query lap 2 → None
        entries = [_make_entry(5)]
        result = associate_setup(2, entries)
        assert result is None

    def test_unsorted_input(self):
        entries = [_make_entry(12), _make_entry(0), _make_entry(6)]
        result = associate_setup(7, entries)
        assert result.lap_start == 6
