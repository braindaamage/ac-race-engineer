"""Tests for analyzer utility functions."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from ac_engineer.analyzer._utils import (
    BRAKE_ON,
    SPEED_PIT_FILTER,
    THROTTLE_FULL,
    THROTTLE_ON,
    channel_available,
    compute_trend_slope,
    extract_corner_data,
    safe_max,
    safe_mean,
    safe_min,
)


class TestSafeMean:
    def test_normal_data(self):
        assert safe_mean(pd.Series([1.0, 2.0, 3.0])) == pytest.approx(2.0)

    def test_all_nan(self):
        assert safe_mean(pd.Series([float("nan"), float("nan")])) is None

    def test_mixed_nan(self):
        assert safe_mean(pd.Series([1.0, float("nan"), 3.0])) == pytest.approx(2.0)

    def test_empty(self):
        assert safe_mean(pd.Series([], dtype=float)) is None

    def test_numpy_array(self):
        assert safe_mean(np.array([10.0, 20.0])) == pytest.approx(15.0)


class TestSafeMax:
    def test_normal_data(self):
        assert safe_max(pd.Series([1.0, 3.0, 2.0])) == pytest.approx(3.0)

    def test_all_nan(self):
        assert safe_max(pd.Series([float("nan")])) is None

    def test_mixed_nan(self):
        assert safe_max(pd.Series([1.0, float("nan"), 3.0])) == pytest.approx(3.0)

    def test_empty(self):
        assert safe_max(pd.Series([], dtype=float)) is None


class TestSafeMin:
    def test_normal_data(self):
        assert safe_min(pd.Series([1.0, 3.0, 2.0])) == pytest.approx(1.0)

    def test_all_nan(self):
        assert safe_min(pd.Series([float("nan")])) is None

    def test_mixed_nan(self):
        assert safe_min(pd.Series([1.0, float("nan"), 3.0])) == pytest.approx(1.0)

    def test_empty(self):
        assert safe_min(pd.Series([], dtype=float)) is None


class TestChannelAvailable:
    def test_existing_column_with_data(self):
        df = pd.DataFrame({"col": [1.0, 2.0]})
        assert channel_available(df, "col") is True

    def test_missing_column(self):
        df = pd.DataFrame({"col": [1.0]})
        assert channel_available(df, "other") is False

    def test_all_nan_column(self):
        df = pd.DataFrame({"col": [float("nan"), float("nan")]})
        assert channel_available(df, "col") is False

    def test_partial_nan_column(self):
        df = pd.DataFrame({"col": [1.0, float("nan")]})
        assert channel_available(df, "col") is True


class TestExtractCornerData:
    def test_normal_range(self):
        df = pd.DataFrame({
            "normalized_position": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "speed_kmh": [100, 110, 120, 130, 140, 150],
        })
        result = extract_corner_data(df, 0.1, 0.3)
        assert len(result) == 3
        assert list(result["speed_kmh"]) == [110, 120, 130]

    def test_wrap_around(self):
        df = pd.DataFrame({
            "normalized_position": [0.0, 0.05, 0.9, 0.95, 1.0],
            "speed_kmh": [100, 110, 120, 130, 140],
        })
        result = extract_corner_data(df, 0.9, 0.05)
        # 0.0, 0.05 (<=0.05) + 0.9, 0.95, 1.0 (>=0.9) = 5 rows
        assert len(result) == 5

    def test_empty_result(self):
        df = pd.DataFrame({
            "normalized_position": [0.0, 0.1, 0.2],
            "speed_kmh": [100, 110, 120],
        })
        result = extract_corner_data(df, 0.5, 0.6)
        assert len(result) == 0


class TestComputeTrendSlope:
    def test_zero_values(self):
        assert compute_trend_slope([]) is None

    def test_one_value(self):
        assert compute_trend_slope([5.0]) is None

    def test_two_values_increasing(self):
        slope = compute_trend_slope([1.0, 3.0])
        assert slope == pytest.approx(2.0)

    def test_two_values_decreasing(self):
        slope = compute_trend_slope([3.0, 1.0])
        assert slope == pytest.approx(-2.0)

    def test_flat(self):
        slope = compute_trend_slope([5.0, 5.0, 5.0])
        assert slope == pytest.approx(0.0)

    def test_multiple_values(self):
        # y = 2x + 1 → slope = 2
        slope = compute_trend_slope([1.0, 3.0, 5.0, 7.0])
        assert slope == pytest.approx(2.0)


class TestThresholdConstants:
    def test_values(self):
        assert THROTTLE_FULL == 0.95
        assert THROTTLE_ON == 0.05
        assert BRAKE_ON == 0.05
        assert SPEED_PIT_FILTER == 10.0
