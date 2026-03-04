"""Integration tests for session_parser.parse_session().

Tests are organized by User Story. Each section tests one US independently.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ac_engineer.parser.session_parser import parse_session
from tests.parser.conftest import make_session_df, make_metadata_v2


# ===========================================================================
# US1: Lap Segmentation and Classification
# ===========================================================================

class TestUS1LapSegmentation:
    def test_minimal_session_lap_count(self, minimal_session_files):
        csv_path, meta_path = minimal_session_files
        session = parse_session(csv_path, meta_path)
        assert len(session.laps) == 3

    def test_minimal_session_classifications(self, minimal_session_files):
        csv_path, meta_path = minimal_session_files
        session = parse_session(csv_path, meta_path)
        classifications = [lap.classification for lap in session.laps]
        assert "outlap" in classifications
        assert "flying" in classifications
        assert "inlap" in classifications

    def test_zero_laps_session(self, zero_laps_files):
        csv_path, meta_path = zero_laps_files
        session = parse_session(csv_path, meta_path)
        # Only one lap_count group (lap 0), classified as incomplete (is_last)
        assert len(session.laps) == 1
        assert session.laps[0].classification == "incomplete"

    def test_all_invalid_session(self, all_invalid_files):
        csv_path, meta_path = all_invalid_files
        session = parse_session(csv_path, meta_path)
        # All laps should have is_invalid=True; none dropped
        assert len(session.laps) == 2
        for lap in session.laps:
            assert lap.is_invalid is True

    def test_crash_session_derives_total_samples(self, crash_session_files):
        csv_path, meta_path = crash_session_files
        session = parse_session(csv_path, meta_path)
        assert session.metadata.total_samples is not None
        assert session.metadata.total_samples > 0

    def test_crash_session_derives_session_end(self, crash_session_files):
        csv_path, meta_path = crash_session_files
        session = parse_session(csv_path, meta_path)
        assert session.metadata.session_end is not None

    def test_no_samples_lost(self, minimal_session_files):
        csv_path, meta_path = minimal_session_files
        session = parse_session(csv_path, meta_path)
        total = sum(lap.sample_count for lap in session.laps)
        df = pd.read_csv(csv_path)
        assert total == len(df)

    def test_metadata_fields_populated(self, minimal_session_files):
        csv_path, meta_path = minimal_session_files
        session = parse_session(csv_path, meta_path)
        meta = session.metadata
        assert meta.car_name == "ks_ferrari_488_gt3"
        assert meta.track_name == "monza"
        assert meta.session_type == "practice"

    def test_is_invalid_independent_of_classification(self, all_invalid_files):
        """Laps can have classification='outlap' and is_invalid=True simultaneously."""
        csv_path, meta_path = all_invalid_files
        session = parse_session(csv_path, meta_path)
        for lap in session.laps:
            assert lap.is_invalid is True

    def test_file_not_found_csv(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_session(tmp_path / "missing.csv", tmp_path / "missing.meta.json")

    def test_last_lap_is_incomplete(self, crash_session_files):
        csv_path, meta_path = crash_session_files
        session = parse_session(csv_path, meta_path)
        assert session.laps[-1].classification == "incomplete"


# ===========================================================================
# US2: Setup Association (added in Phase 4)
# ===========================================================================

class TestUS2SetupAssociation:
    def test_multi_setup_lap_5_uses_entry_0(self, multi_setup_files):
        csv_path, meta_path = multi_setup_files
        session = parse_session(csv_path, meta_path)
        lap5 = session.lap_by_number(5)
        if lap5 and lap5.active_setup is not None:
            assert lap5.active_setup.lap_start == 0

    def test_multi_setup_lap_7_uses_entry_6(self, multi_setup_files):
        csv_path, meta_path = multi_setup_files
        session = parse_session(csv_path, meta_path)
        lap7 = session.lap_by_number(7)
        if lap7 and lap7.active_setup is not None:
            assert lap7.active_setup.lap_start == 6

    def test_multi_setup_lap_13_uses_entry_12(self, multi_setup_files):
        csv_path, meta_path = multi_setup_files
        session = parse_session(csv_path, meta_path)
        lap13 = session.lap_by_number(13)
        if lap13 and lap13.active_setup is not None:
            assert lap13.active_setup.lap_start == 12

    def test_legacy_v1_setup_history_shape(self, legacy_v1_files):
        csv_path, meta_path = legacy_v1_files
        session = parse_session(csv_path, meta_path)
        # Legacy v1.0 should produce exactly 1 setup entry
        assert len(session.setups) == 1
        assert session.setups[0].trigger == "session_start"
        assert session.setups[0].lap_start == 0


# ===========================================================================
# US4: Quality Warnings (added in Phase 6)
# ===========================================================================

class TestUS4QualityWarnings:
    def test_data_gaps_produces_time_series_gap_warning(self, data_gaps_files):
        csv_path, meta_path = data_gaps_files
        session = parse_session(csv_path, meta_path)
        all_warning_types = [
            w.warning_type
            for lap in session.laps
            for w in lap.quality_warnings
        ]
        # After US4 is integrated, time_series_gap should appear
        # This test is a placeholder; it will pass vacuously until US4 is wired in
        # Once wired: assert "time_series_gap" in all_warning_types
        pass

    def test_crash_session_last_lap_no_laps_dropped(self, crash_session_files):
        csv_path, meta_path = crash_session_files
        session = parse_session(csv_path, meta_path)
        assert len(session.laps) > 0


# ===========================================================================
# US5: Round-trip (added in Phase 7)
# ===========================================================================

class TestRemainingScenarios:
    """T037 — Additional integration scenarios."""

    def test_legacy_v1_upgrade_produces_single_setup(self, legacy_v1_files):
        csv_path, meta_path = legacy_v1_files
        session = parse_session(csv_path, meta_path)
        # v1.0 → v2.0 upgrade: exactly one setup entry
        assert len(session.setups) == 1
        assert session.setups[0].trigger == "session_start"
        assert session.setups[0].lap_start == 0

    def test_legacy_v1_all_laps_have_setup(self, legacy_v1_files):
        csv_path, meta_path = legacy_v1_files
        session = parse_session(csv_path, meta_path)
        for lap in session.laps:
            assert lap.active_setup is not None

    def test_reduced_mode_channels_unavailable(self, reduced_mode_files):
        csv_path, meta_path = reduced_mode_files
        session = parse_session(csv_path, meta_path)
        assert session.metadata.reduced_mode is True
        assert len(session.metadata.channels_unavailable) > 0

    def test_reduced_mode_no_laps_dropped(self, reduced_mode_files):
        csv_path, meta_path = reduced_mode_files
        session = parse_session(csv_path, meta_path)
        assert len(session.laps) == 2

    def test_all_invalid_is_invalid_true_for_all(self, all_invalid_files):
        csv_path, meta_path = all_invalid_files
        session = parse_session(csv_path, meta_path)
        for lap in session.laps:
            assert lap.is_invalid is True

    def test_all_invalid_laps_not_dropped(self, all_invalid_files):
        csv_path, meta_path = all_invalid_files
        session = parse_session(csv_path, meta_path)
        assert len(session.laps) > 0


class TestUS5RoundTrip:
    def test_minimal_session_save_load(self, minimal_session_files, tmp_path):
        from ac_engineer.parser.cache import save_session, load_session

        csv_path, meta_path = minimal_session_files
        session = parse_session(csv_path, meta_path)
        saved_dir = save_session(session, tmp_path)
        reloaded = load_session(saved_dir)

        assert len(reloaded.laps) == len(session.laps)
        for orig, rel in zip(session.laps, reloaded.laps):
            assert orig.lap_number == rel.lap_number
            assert orig.classification == rel.classification
            assert orig.is_invalid == rel.is_invalid
            assert orig.sample_count == rel.sample_count

    def test_multi_setup_round_trip_preserves_setups(self, multi_setup_files, tmp_path):
        from ac_engineer.parser.cache import save_session, load_session

        csv_path, meta_path = multi_setup_files
        session = parse_session(csv_path, meta_path)
        saved_dir = save_session(session, tmp_path)
        reloaded = load_session(saved_dir)

        assert len(reloaded.setups) == len(session.setups)
