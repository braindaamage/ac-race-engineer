"""Tests for setup change validation and file writing."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ac_engineer.engineer.models import (
    ParameterRange,
    SetupChange,
    ValidationResult,
)
from ac_engineer.engineer.setup_writer import apply_changes, create_backup, validate_changes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ranges() -> dict[str, ParameterRange]:
    return {
        "CAMBER_LF": ParameterRange(
            section="CAMBER_LF", parameter="VALUE",
            min_value=-5.0, max_value=0.0, step=0.1,
        ),
        "PRESSURE_LF": ParameterRange(
            section="PRESSURE_LF", parameter="VALUE",
            min_value=20.0, max_value=35.0, step=0.5,
        ),
    }


def _make_change(section: str, value_after: float) -> SetupChange:
    return SetupChange(
        section=section, parameter="VALUE",
        value_after=value_after,
        reasoning="test", expected_effect="test", confidence="medium",
    )


# ---------------------------------------------------------------------------
# T023: Validation logic
# ---------------------------------------------------------------------------


class TestValidateChanges:
    def test_within_range_valid(self):
        ranges = _make_ranges()
        results = validate_changes(ranges, [_make_change("CAMBER_LF", -2.0)])
        assert len(results) == 1
        assert results[0].is_valid is True
        assert results[0].clamped_value is None

    def test_below_min_clamped(self):
        ranges = _make_ranges()
        results = validate_changes(ranges, [_make_change("CAMBER_LF", -7.0)])
        assert results[0].is_valid is False
        assert results[0].clamped_value == -5.0

    def test_above_max_clamped(self):
        ranges = _make_ranges()
        results = validate_changes(ranges, [_make_change("CAMBER_LF", 2.0)])
        assert results[0].is_valid is False
        assert results[0].clamped_value == 0.0

    def test_no_range_data_valid_with_warning(self):
        ranges = _make_ranges()
        results = validate_changes(ranges, [_make_change("UNKNOWN_SECTION", 42.0)])
        assert results[0].is_valid is True
        assert results[0].clamped_value is None
        assert "no range" in results[0].warning.lower()

    def test_batch_returns_same_order(self):
        ranges = _make_ranges()
        changes = [
            _make_change("CAMBER_LF", -2.0),
            _make_change("PRESSURE_LF", 27.0),
            _make_change("UNKNOWN", 1.0),
            _make_change("CAMBER_LF", -6.0),
            _make_change("PRESSURE_LF", 40.0),
        ]
        results = validate_changes(ranges, changes)
        assert len(results) == 5
        assert results[0].section == "CAMBER_LF"
        assert results[1].section == "PRESSURE_LF"
        assert results[2].section == "UNKNOWN"

    def test_exact_boundary_values_valid(self):
        ranges = _make_ranges()
        # value == min
        r_min = validate_changes(ranges, [_make_change("CAMBER_LF", -5.0)])
        assert r_min[0].is_valid is True
        # value == max
        r_max = validate_changes(ranges, [_make_change("CAMBER_LF", 0.0)])
        assert r_max[0].is_valid is True


# ---------------------------------------------------------------------------
# T026: Backup tests
# ---------------------------------------------------------------------------


class TestCreateBackup:
    def test_backup_has_original_content(self, sample_setup_ini: Path):
        original = sample_setup_ini.read_text()
        backup_path = create_backup(sample_setup_ini)
        assert backup_path.exists()
        assert backup_path.read_text() == original

    def test_backup_nonexistent_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            create_backup(tmp_path / "nope.ini")

    def test_multiple_backups_different_names(self, sample_setup_ini: Path):
        b1 = create_backup(sample_setup_ini)
        time.sleep(1.1)  # Ensure different timestamps
        b2 = create_backup(sample_setup_ini)
        assert b1 != b2
        assert b1.exists()
        assert b2.exists()


# ---------------------------------------------------------------------------
# T027: Apply changes tests
# ---------------------------------------------------------------------------


class TestApplyChanges:
    def test_preserves_unchanged_params(self, sample_setup_ini: Path):
        ranges = _make_ranges()
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -3.0)])
        outcomes = apply_changes(sample_setup_ini, changes)

        # Read back and verify only CAMBER_LF changed
        import configparser
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(str(sample_setup_ini))

        assert cp.get("CAMBER_LF", "VALUE") == "-3.0"
        assert cp.get("CAMBER_RF", "VALUE") == "-2.0"  # unchanged
        assert cp.get("PRESSURE_LF", "VALUE") == "26.5"  # unchanged

    def test_backup_created_before_modify(self, sample_setup_ini: Path):
        import glob
        parent = sample_setup_ini.parent
        before = set(parent.iterdir())
        ranges = _make_ranges()
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -3.0)])
        apply_changes(sample_setup_ini, changes)
        after = set(parent.iterdir())
        new_files = after - before
        assert any(".bak." in f.name for f in new_files)

    def test_empty_changes_raises(self, sample_setup_ini: Path):
        with pytest.raises(ValueError):
            apply_changes(sample_setup_ini, [])

    def test_file_not_found_raises(self, tmp_path: Path):
        ranges = _make_ranges()
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -3.0)])
        with pytest.raises(FileNotFoundError):
            apply_changes(tmp_path / "nope.ini", changes)

    def test_last_change_wins_duplicate_section(self, sample_setup_ini: Path):
        ranges = _make_ranges()
        changes = validate_changes(ranges, [
            _make_change("CAMBER_LF", -1.0),
            _make_change("CAMBER_LF", -4.0),
        ])
        outcomes = apply_changes(sample_setup_ini, changes)

        import configparser
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(str(sample_setup_ini))
        assert cp.get("CAMBER_LF", "VALUE") == "-4.0"

    def test_other_sections_preserved(self, sample_setup_ini: Path):
        import configparser
        cp_before = configparser.ConfigParser()
        cp_before.optionxform = str
        cp_before.read(str(sample_setup_ini))
        sections_before = set(cp_before.sections())

        ranges = _make_ranges()
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -3.0)])
        apply_changes(sample_setup_ini, changes)

        cp_after = configparser.ConfigParser()
        cp_after.optionxform = str
        cp_after.read(str(sample_setup_ini))
        sections_after = set(cp_after.sections())
        assert sections_before == sections_after

    def test_change_outcome_values(self, sample_setup_ini: Path):
        ranges = _make_ranges()
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -3.0)])
        outcomes = apply_changes(sample_setup_ini, changes)
        assert len(outcomes) == 1
        assert outcomes[0].section == "CAMBER_LF"
        assert outcomes[0].old_value == "-2.0"
        assert outcomes[0].new_value == "-3.0"

    def test_clamped_value_used_when_invalid(self, sample_setup_ini: Path):
        ranges = _make_ranges()
        # -7.0 will be clamped to -5.0
        changes = validate_changes(ranges, [_make_change("CAMBER_LF", -7.0)])
        outcomes = apply_changes(sample_setup_ini, changes)

        import configparser
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(str(sample_setup_ini))
        assert cp.get("CAMBER_LF", "VALUE") == "-5.0"

    def test_nonexistent_section_skipped(self, sample_setup_ini: Path):
        """A change targeting a section not in the .ini is skipped, not added."""
        ranges = _make_ranges()
        changes = validate_changes(ranges, [
            _make_change("CAMBER_LF", -3.0),
            _make_change("NONEXISTENT_SECTION", 42.0),
        ])
        outcomes = apply_changes(sample_setup_ini, changes)
        assert len(outcomes) == 2

        applied = [o for o in outcomes if o.status == "applied"]
        skipped = [o for o in outcomes if o.status == "skipped"]
        assert len(applied) == 1
        assert applied[0].section == "CAMBER_LF"
        assert len(skipped) == 1
        assert skipped[0].section == "NONEXISTENT_SECTION"
        assert "not found" in skipped[0].reason

        # Verify the nonexistent section was NOT added to the file
        import configparser
        cp = configparser.ConfigParser()
        cp.optionxform = str
        cp.read(str(sample_setup_ini))
        assert not cp.has_section("NONEXISTENT_SECTION")

    def test_all_sections_nonexistent_skipped(self, sample_setup_ini: Path):
        """When all changes target nonexistent sections, all are skipped."""
        changes = [
            ValidationResult(
                section="FAKE_A", parameter="VALUE",
                proposed_value=1.0, is_valid=True,
            ),
            ValidationResult(
                section="FAKE_B", parameter="VALUE",
                proposed_value=2.0, is_valid=True,
            ),
        ]
        outcomes = apply_changes(sample_setup_ini, changes)
        assert all(o.status == "skipped" for o in outcomes)
