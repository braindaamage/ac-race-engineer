"""Tests for corner analyzer — per-corner metric computation."""

from __future__ import annotations

import numpy as np
import pytest

from ac_engineer.analyzer.corner_analyzer import analyze_corner
from ac_engineer.analyzer.models import CornerMetrics

from .conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    WHEELS,
    make_corner,
    make_lap_data,
    make_lap_segment,
)


def _make_corner_lap_data(
    n_samples: int = 200,
    *,
    corner_speed_profile: list[float] | None = None,
    corner_brake_profile: list[float] | None = None,
    corner_g_lat_profile: list[float] | None = None,
) -> dict[str, list]:
    """Build lap data with varied profiles in the corner region."""
    data = make_lap_data(n_samples=n_samples, speed=120.0, g_lat=0.3)

    # Apply speed profile in corner region (0.10 to 0.20 of the lap)
    if corner_speed_profile:
        positions = data["normalized_position"]
        for i, pos in enumerate(positions):
            if 0.10 <= pos <= 0.20:
                # Map position within corner to profile index
                frac = (pos - 0.10) / 0.10
                idx = min(int(frac * len(corner_speed_profile)), len(corner_speed_profile) - 1)
                data["speed_kmh"][i] = corner_speed_profile[idx]

    if corner_brake_profile:
        positions = data["normalized_position"]
        for i, pos in enumerate(positions):
            if 0.10 <= pos <= 0.20:
                frac = (pos - 0.10) / 0.10
                idx = min(int(frac * len(corner_brake_profile)), len(corner_brake_profile) - 1)
                data["brake"][i] = corner_brake_profile[idx]

    if corner_g_lat_profile:
        positions = data["normalized_position"]
        for i, pos in enumerate(positions):
            if 0.10 <= pos <= 0.20:
                frac = (pos - 0.10) / 0.10
                idx = min(int(frac * len(corner_g_lat_profile)), len(corner_g_lat_profile) - 1)
                data["g_lat"][i] = corner_g_lat_profile[idx]

    return data


class TestAnalyzeCornerNormal:
    """Test analyze_corner with a normal braked corner."""

    def test_returns_corner_metrics(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_speed_profile=[150, 130, 100, 80, 90, 110],
            corner_brake_profile=[0.8, 0.6, 0.3, 0.0, 0.0, 0.0],
            corner_g_lat_profile=[0.5, 1.0, 1.5, 1.2, 0.8, 0.3],
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert isinstance(result, CornerMetrics)
        assert result.corner_number == 1

    def test_performance_speeds(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_speed_profile=[150, 130, 100, 80, 90, 110],
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.performance.duration_s > 0

    def test_performance_entry_exit_speeds(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_speed_profile=[150, 130, 100, 80, 90, 110],
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        # Entry speed should be close to 150, exit close to 110
        assert result.performance.entry_speed_kmh > 0
        assert result.performance.exit_speed_kmh > 0

    def test_grip_peak_lat_g(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_g_lat_profile=[0.5, 1.0, 1.5, 1.2, 0.8, 0.3],
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.grip.peak_lat_g >= 1.0

    def test_grip_understeer_ratio(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = make_lap_data(
            n_samples=200,
            slip_angle={"fl": 0.06, "fr": 0.06, "rl": 0.04, "rr": 0.04},
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        # front avg (0.06) / rear avg (0.04) = 1.5 → understeer
        assert result.grip.understeer_ratio is not None
        assert result.grip.understeer_ratio > 1.0

    def test_technique_brake_point(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_brake_profile=[0.8, 0.6, 0.3, 0.0, 0.0, 0.0],
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.technique.brake_point_norm is not None
        assert 0.10 <= result.technique.brake_point_norm <= 0.20

    def test_technique_throttle_on(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = _make_corner_lap_data(
            corner_brake_profile=[0.8, 0.6, 0.0, 0.0, 0.0, 0.0],
        )
        # Set throttle in corner region: off before apex, on after
        positions = data["normalized_position"]
        for i, pos in enumerate(positions):
            if 0.10 <= pos < 0.15:
                data["throttle"][i] = 0.0
            elif 0.15 <= pos <= 0.20:
                data["throttle"][i] = 0.5
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.technique.throttle_on_norm is not None
        assert result.technique.throttle_on_norm >= 0.15

    def test_loading_present(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = make_lap_data(n_samples=200)
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.loading is not None
        for w in WHEELS:
            assert w in result.loading.peak_wheel_load


class TestAnalyzeCornerFlatOut:
    """Test with a flat-out kink (no braking)."""

    def test_no_brake_point(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = make_lap_data(n_samples=200, throttle=1.0, brake=0.0, speed=200.0)
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.technique.brake_point_norm is None
        assert result.technique.trail_braking_intensity == pytest.approx(0.0)


class TestAnalyzeCornerReducedMode:
    """Test with wheel_load channels NaN."""

    def test_loading_none(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = make_lap_data(n_samples=200, reduced_mode=True)
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.loading is None


class TestAnalyzeCornerWrapAround:
    """Test corner spanning start/finish line."""

    def test_wrap_around_corner(self):
        corner = make_corner(1, entry_norm_pos=0.95, apex_norm_pos=0.98, exit_norm_pos=0.05)
        data = make_lap_data(n_samples=200)
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        assert result.performance.duration_s > 0


class TestAnalyzeCornerUndersteerEdge:
    """Test understeer ratio edge case: rear slip near zero."""

    def test_understeer_ratio_none_when_no_rear_slip(self):
        corner = make_corner(1, 0.10, 0.15, 0.20)
        data = make_lap_data(
            n_samples=200,
            slip_angle={"fl": 0.05, "fr": 0.05, "rl": 0.001, "rr": 0.001},
        )
        lap = make_lap_segment(data=data)
        df = lap.to_dataframe()
        result = analyze_corner(corner, df)
        # Rear slip avg < epsilon → None
        assert result.grip.understeer_ratio is None
