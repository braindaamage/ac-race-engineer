"""Unit tests for quality_validator.validate_lap."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import ac_engineer.parser.quality_validator as qv
from ac_engineer.parser.quality_validator import validate_lap

SAMPLE_RATE = 22.0
SAMPLE_INTERVAL = 1.0 / SAMPLE_RATE


def _make_clean_lap(n: int = 500) -> pd.DataFrame:
    """Build a clean lap DataFrame with no anomalies."""
    ts = 1_740_000_000.0 + np.arange(n) * SAMPLE_INTERVAL
    norm_pos = np.linspace(0.15, 0.85, n)  # mid-track positions
    speed = np.full(n, 120.0)
    return pd.DataFrame({
        "timestamp": ts,
        "normalized_position": norm_pos,
        "speed_kmh": speed,
    })


class TestValidateLapClean:
    def test_clean_lap_no_warnings(self):
        df = _make_clean_lap()
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        assert warnings == []

    def test_empty_lap_no_crash(self):
        df = pd.DataFrame(columns=["timestamp", "normalized_position", "speed_kmh"])
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        assert isinstance(warnings, list)


class TestTimeSeriesGap:
    def test_gap_above_threshold_triggers_warning(self):
        df = _make_clean_lap()
        # Inject 1.2s gap at index 100
        df.loc[100, "timestamp"] = df.loc[99, "timestamp"] + 1.2
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "time_series_gap" in types

    def test_gap_below_threshold_no_warning(self):
        df = _make_clean_lap()
        # Gap just below threshold (0.49s < 0.5s threshold)
        df.loc[100, "timestamp"] = df.loc[99, "timestamp"] + 0.49
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "time_series_gap" not in types

    def test_gap_exactly_at_threshold_no_warning(self):
        """Gap equal to threshold (not strictly greater) should not trigger."""
        df = _make_clean_lap()
        df.loc[100, "timestamp"] = df.loc[99, "timestamp"] + qv.TIME_GAP_THRESHOLD
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "time_series_gap" not in types

    def test_gap_just_above_threshold_triggers(self):
        df = _make_clean_lap()
        df.loc[100, "timestamp"] = df.loc[99, "timestamp"] + qv.TIME_GAP_THRESHOLD + 0.01
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "time_series_gap" in types


class TestPositionJump:
    def test_position_jump_triggers_warning(self):
        df = _make_clean_lap()
        # Jump of 0.10 (above 0.05 threshold)
        df.loc[200, "normalized_position"] = df.loc[199, "normalized_position"] + 0.10
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "position_jump" in types

    def test_small_jump_no_warning(self):
        df = _make_clean_lap()
        # Jump of 0.04 (below 0.05 threshold)
        df.loc[200, "normalized_position"] = df.loc[199, "normalized_position"] + 0.04
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "position_jump" not in types

    def test_sf_wrap_around_no_false_positive(self):
        """S/F crossing (0.9998 → 0.0003) must NOT trigger position_jump.

        This is a regression test for real-session data where the last
        sample(s) of a lap group show the car crossing the start/finish
        line, producing a raw diff of ~-0.9995 which should be ignored.
        """
        n = 100
        ts = 1_740_000_000.0 + np.arange(n) * SAMPLE_INTERVAL
        # Build a lap that ends near the S/F line
        norm_pos = np.linspace(0.90, 0.9995, n)
        # Last sample wraps to just past S/F
        norm_pos[-1] = 0.0003
        speed = np.full(n, 100.0)
        df = pd.DataFrame({
            "timestamp": ts,
            "normalized_position": norm_pos,
            "speed_kmh": speed,
        })
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "position_jump" not in types

    def test_genuine_backward_jump_triggers_warning(self):
        """A genuine large backward teleport should still be flagged."""
        n = 200
        ts = 1_740_000_000.0 + np.arange(n) * SAMPLE_INTERVAL
        norm_pos = np.linspace(0.15, 0.85, n)
        # Backward jump at sample 100: position goes from ~0.50 back to 0.10
        norm_pos[100] = 0.10
        speed = np.full(n, 100.0)
        df = pd.DataFrame({
            "timestamp": ts,
            "normalized_position": norm_pos,
            "speed_kmh": speed,
        })
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "position_jump" in types


class TestZeroSpeedMidLap:
    def test_zero_speed_mid_lap_triggers_warning(self):
        df = _make_clean_lap(n=500)
        # Stop for 4 seconds (88 samples at 22 Hz) at position 0.5
        n_stopped = int(SAMPLE_RATE * 4)
        start = 200
        df.loc[start: start + n_stopped, "speed_kmh"] = 0.0
        # Ensure within ZERO_SPEED_MIN/MAX window
        df.loc[start: start + n_stopped, "normalized_position"] = 0.5
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "zero_speed_mid_lap" in types

    def test_zero_speed_too_short_no_warning(self):
        df = _make_clean_lap()
        # Stop for only 1 second (22 samples) — below 3s threshold
        n_stopped = int(SAMPLE_RATE * 1)
        start = 200
        df.loc[start: start + n_stopped, "speed_kmh"] = 0.0
        df.loc[start: start + n_stopped, "normalized_position"] = 0.5
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "zero_speed_mid_lap" not in types

    def test_zero_speed_outside_window_no_warning(self):
        """Zero speed near pit entry (position 0.05) should not trigger."""
        df = _make_clean_lap()
        n_stopped = int(SAMPLE_RATE * 4)
        start = 10
        df.loc[start: start + n_stopped, "speed_kmh"] = 0.0
        df.loc[start: start + n_stopped, "normalized_position"] = 0.05  # < ZERO_SPEED_MIN
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "zero_speed_mid_lap" not in types


class TestIncomplete:
    def test_is_last_triggers_incomplete(self):
        df = _make_clean_lap()
        warnings = validate_lap(df, SAMPLE_RATE, is_last=True)
        types = [w.warning_type for w in warnings]
        assert "incomplete" in types

    def test_not_last_no_incomplete(self):
        df = _make_clean_lap()
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "incomplete" not in types


class TestDuplicateTimestamp:
    def test_duplicate_timestamp_triggers_warning(self):
        df = _make_clean_lap()
        # Make sample 150 have the same timestamp as sample 149
        df.loc[150, "timestamp"] = df.loc[149, "timestamp"]
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "duplicate_timestamp" in types

    def test_unique_timestamps_no_warning(self):
        df = _make_clean_lap()
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "duplicate_timestamp" not in types


class TestMultipleWarnings:
    def test_gap_and_jump_both_detected(self):
        df = _make_clean_lap()
        df.loc[100, "timestamp"] = df.loc[99, "timestamp"] + 1.0
        df.loc[200, "normalized_position"] = df.loc[199, "normalized_position"] + 0.10
        warnings = validate_lap(df, SAMPLE_RATE, is_last=False)
        types = [w.warning_type for w in warnings]
        assert "time_series_gap" in types
        assert "position_jump" in types
