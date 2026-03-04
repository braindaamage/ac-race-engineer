"""Unit tests for corner_detector module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ac_engineer.parser.corner_detector import (
    build_reference_map,
    compute_session_thresholds,
    detect_corners,
)

SAMPLE_RATE = 22.0


def _make_df(
    n: int = 440,  # ~20 seconds at 22 Hz
    n_corners: int = 0,
    g_lat_scale: float = 1.0,
    steer_scale: float = 1.0,
    all_nan_g: bool = False,
    speed_base: float = 120.0,
) -> pd.DataFrame:
    """Build a synthetic lap DataFrame.

    If n_corners > 0, sinusoidal lateral G / steering patterns are injected
    at evenly-spaced normalized positions.
    """
    norm_pos = np.linspace(0.0, 0.99, n)
    speed = np.full(n, speed_base)
    g_lat = np.zeros(n)
    steering = np.zeros(n)

    if n_corners > 0:
        # Inject sinusoidal cornering peaks at evenly-spaced positions
        for k in range(n_corners):
            apex = (k + 0.5) / n_corners  # normalized apex position
            apex_idx = int(apex * n)
            half_width = int(n / (n_corners * 3))  # cornering window width
            start = max(0, apex_idx - half_width)
            end = min(n - 1, apex_idx + half_width)
            sign = 1 if k % 2 == 0 else -1  # alternating left/right

            for i in range(start, end + 1):
                t = (i - apex_idx) / max(half_width, 1)
                g_val = sign * g_lat_scale * 2.5 * max(0, 1 - t * t)
                g_lat[i] = g_val
                steering[i] = g_val * 10
                # Slow down at apex
                speed[i] = speed_base * max(0.4, 1 - 0.6 * max(0, 1 - t * t))

    if all_nan_g:
        g_lat[:] = float("nan")

    return pd.DataFrame({
        "normalized_position": norm_pos,
        "speed_kmh": speed,
        "g_lat": g_lat if not all_nan_g else np.full(n, float("nan")),
        "steering": steering,
    })


class TestComputeSessionThresholds:
    def test_returns_dict_with_required_keys(self):
        df = _make_df(n_corners=5)
        result = compute_session_thresholds(df, SAMPLE_RATE)
        assert "g_threshold" in result
        assert "steer_threshold" in result
        assert "reduced_mode" in result

    def test_thresholds_positive_for_non_trivial_data(self):
        df = _make_df(n_corners=5)
        result = compute_session_thresholds(df, SAMPLE_RATE)
        assert result["g_threshold"] >= 0
        assert result["steer_threshold"] >= 0
        assert result["reduced_mode"] is False

    def test_reduced_mode_when_g_lat_all_nan(self):
        df = _make_df(all_nan_g=True, n_corners=5)
        result = compute_session_thresholds(df, SAMPLE_RATE)
        assert result["reduced_mode"] is True
        assert result["g_threshold"] == 0.0

    def test_flat_straight_g_threshold_near_zero(self):
        df = _make_df(n_corners=0)  # no corners, all zeros
        result = compute_session_thresholds(df, SAMPLE_RATE)
        # All g_lat = 0, so 80th percentile = 0
        assert result["g_threshold"] == 0.0

    def test_empty_dataframe(self):
        df = pd.DataFrame({"g_lat": [], "steering": []})
        result = compute_session_thresholds(df, SAMPLE_RATE)
        assert isinstance(result, dict)


class TestBuildReferenceMap:
    def test_returns_list(self):
        df = _make_df(n_corners=5)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        result = build_reference_map(df, thresholds, SAMPLE_RATE)
        assert isinstance(result, list)

    def test_10_corner_track(self):
        df = _make_df(n=880, n_corners=10)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        result = build_reference_map(df, thresholds, SAMPLE_RATE)
        # Should detect approximately 10 corners
        assert 8 <= len(result) <= 12

    def test_oval_2_corners(self):
        df = _make_df(n=880, n_corners=2)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        result = build_reference_map(df, thresholds, SAMPLE_RATE)
        assert 1 <= len(result) <= 3

    def test_flat_straight_zero_corners(self):
        df = _make_df(n_corners=0)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        result = build_reference_map(df, thresholds, SAMPLE_RATE)
        assert len(result) == 0

    def test_empty_lap_returns_empty(self):
        df = pd.DataFrame(columns=["normalized_position", "speed_kmh", "g_lat", "steering"])
        thresholds = {"g_threshold": 0.5, "steer_threshold": 5.0, "reduced_mode": False}
        result = build_reference_map(df, thresholds, SAMPLE_RATE)
        assert result == []


class TestDetectCorners:
    def test_returns_list_of_corner_segments(self):
        df = _make_df(n=880, n_corners=5)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        ref = build_reference_map(df, thresholds, SAMPLE_RATE)
        corners = detect_corners(df, ref, thresholds, SAMPLE_RATE)
        assert isinstance(corners, list)

    def test_apex_positions_within_tolerance(self):
        """Detected apexes should be within ±0.05 of the reference."""
        df = _make_df(n=880, n_corners=5)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        ref = build_reference_map(df, thresholds, SAMPLE_RATE)
        corners = detect_corners(df, ref, thresholds, SAMPLE_RATE)
        for corner in corners:
            ref_pos = ref[corner.corner_number - 1]
            assert abs(corner.apex_norm_pos - ref_pos) <= 0.05

    def test_empty_reference_returns_empty(self):
        df = _make_df(n_corners=5)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        corners = detect_corners(df, [], thresholds, SAMPLE_RATE)
        assert corners == []

    def test_corner_numbers_are_ordered(self):
        df = _make_df(n=880, n_corners=5)
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        ref = build_reference_map(df, thresholds, SAMPLE_RATE)
        corners = detect_corners(df, ref, thresholds, SAMPLE_RATE)
        numbers = [c.corner_number for c in corners]
        assert numbers == sorted(numbers)

    def test_reduced_mode_fallback(self):
        """With all-NaN g_lat, steering-only fallback should detect corners."""
        n = 880
        norm_pos = np.linspace(0.0, 0.99, n)
        speed = np.full(n, 120.0)
        g_lat = np.full(n, float("nan"))
        # Inject steering-only corners
        steering = np.zeros(n)
        for k in range(3):
            apex_idx = int((k + 0.5) / 3 * n)
            half = int(n / 9)
            for i in range(max(0, apex_idx - half), min(n - 1, apex_idx + half)):
                t = (i - apex_idx) / max(half, 1)
                steering[i] = 50.0 * max(0, 1 - t * t)
                speed[i] = 120.0 * max(0.4, 1 - 0.6 * max(0, 1 - t * t))
        df = pd.DataFrame({
            "normalized_position": norm_pos,
            "speed_kmh": speed,
            "g_lat": g_lat,
            "steering": steering,
        })
        thresholds = compute_session_thresholds(df, SAMPLE_RATE)
        assert thresholds["reduced_mode"] is True
        ref = build_reference_map(df, thresholds, SAMPLE_RATE)
        corners = detect_corners(df, ref, thresholds, SAMPLE_RATE)
        # Reduced mode should detect some corners using steering
        assert len(corners) >= 1
