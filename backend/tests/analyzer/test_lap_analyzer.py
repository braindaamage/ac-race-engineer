"""Tests for lap analyzer — per-lap metric computation."""

from __future__ import annotations

import numpy as np
import pytest

from ac_engineer.analyzer.lap_analyzer import analyze_lap
from ac_engineer.analyzer.models import FuelMetrics, LapMetrics

from .conftest import (
    BASE_TIMESTAMP,
    SAMPLE_INTERVAL,
    make_lap_data,
    make_lap_segment,
    make_parsed_session,
    SETUP_A,
)


class TestAnalyzeLapFlying:
    """Test analyze_lap with a flying lap (all metrics computed)."""

    def test_returns_lap_metrics(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        assert isinstance(result, LapMetrics)

    def test_timing_lap_time(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        expected = lap.end_timestamp - lap.start_timestamp
        assert result.timing.lap_time_s == pytest.approx(expected, abs=0.01)

    def test_timing_sector_times(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        if result.timing.sector_times_s is not None:
            assert len(result.timing.sector_times_s) == 3
            assert sum(result.timing.sector_times_s) == pytest.approx(
                result.timing.lap_time_s, abs=0.1
            )

    def test_tyre_temps_populated(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        for w in ("fl", "fr", "rl", "rr"):
            assert w in result.tyres.temps_avg
            assert result.tyres.temps_avg[w].core > 0
            assert w in result.tyres.temps_peak

    def test_tyre_pressure(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        assert result.tyres.pressure_avg["fl"] == pytest.approx(27.5)

    def test_tyre_temp_spread(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        # inner=85, outer=79 → spread=6.0 for fl
        assert result.tyres.temp_spread["fl"] == pytest.approx(6.0)

    def test_front_rear_balance(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        # fl/fr core=80, rl/rr core=78 → 80/78 ≈ 1.026
        assert result.tyres.front_rear_balance == pytest.approx(80.0 / 78.0, abs=0.01)

    def test_grip_slip_angles(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        for w in ("fl", "fr", "rl", "rr"):
            assert w in result.grip.slip_angle_avg
            assert result.grip.slip_angle_avg[w] >= 0

    def test_grip_g_forces(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        assert result.grip.peak_lat_g == pytest.approx(0.5)
        assert result.grip.peak_lon_g == pytest.approx(0.3)

    def test_driver_inputs_throttle(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        # throttle=0.7 (partial: >0.05 and <0.95)
        assert result.driver_inputs.full_throttle_pct == pytest.approx(0.0)
        assert result.driver_inputs.partial_throttle_pct == pytest.approx(100.0)
        assert result.driver_inputs.off_throttle_pct == pytest.approx(0.0)

    def test_driver_inputs_braking(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        # brake=0.0 → no braking
        assert result.driver_inputs.braking_pct == pytest.approx(0.0)

    def test_driver_inputs_gear_distribution(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        total = sum(result.driver_inputs.gear_distribution.values())
        assert total == pytest.approx(100.0, abs=0.1)

    def test_speed_metrics(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        assert result.speed.max_speed == pytest.approx(120.0)
        assert result.speed.avg_speed == pytest.approx(120.0)

    def test_fuel_metrics(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        assert result.fuel is not None
        assert result.fuel.fuel_start == pytest.approx(50.0)
        assert result.fuel.fuel_end == pytest.approx(48.0)
        assert result.fuel.consumption == pytest.approx(2.0)

    def test_suspension_metrics(self, flying_lap_session):
        lap = flying_lap_session.laps[0]
        result = analyze_lap(lap, flying_lap_session.metadata)
        for w in ("fl", "fr", "rl", "rr"):
            assert w in result.suspension.travel_avg
            assert w in result.suspension.travel_peak
            assert w in result.suspension.travel_range


class TestAnalyzeLapReducedMode:
    """Test with reduced-mode lap (fuel=None, wear=None)."""

    def test_fuel_is_none(self, reduced_mode_session):
        lap = reduced_mode_session.laps[0]
        result = analyze_lap(lap, reduced_mode_session.metadata)
        assert result.fuel is None

    def test_wear_is_none(self, reduced_mode_session):
        lap = reduced_mode_session.laps[0]
        result = analyze_lap(lap, reduced_mode_session.metadata)
        assert result.tyres.wear_rate is None

    def test_timing_still_works(self, reduced_mode_session):
        lap = reduced_mode_session.laps[0]
        result = analyze_lap(lap, reduced_mode_session.metadata)
        assert result.timing.lap_time_s > 0

    def test_speed_still_works(self, reduced_mode_session):
        lap = reduced_mode_session.laps[0]
        result = analyze_lap(lap, reduced_mode_session.metadata)
        assert result.speed.max_speed > 0

    def test_core_temps_available(self, reduced_mode_session):
        lap = reduced_mode_session.laps[0]
        result = analyze_lap(lap, reduced_mode_session.metadata)
        # Core temps are always available even in reduced mode
        assert result.tyres.temps_avg["fl"].core > 0


class TestAnalyzeLapInvalid:
    """Test with invalid lap — metrics should still compute."""

    def test_invalid_lap_computes(self):
        lap = make_lap_segment(
            lap_number=1, classification="flying",
            is_invalid=True, n_samples=100,
        )
        session = make_parsed_session(laps=[lap])
        result = analyze_lap(lap, session.metadata)
        assert isinstance(result, LapMetrics)
        assert result.timing.lap_time_s > 0


class TestAnalyzeLapMultiLap:
    """Test with multi_lap_session fixture."""

    def test_each_lap_analyzed(self, multi_lap_session):
        for lap in multi_lap_session.laps:
            result = analyze_lap(lap, multi_lap_session.metadata)
            assert result.timing.lap_time_s > 0

    def test_flying_laps_have_full_metrics(self, multi_lap_session):
        for lap in multi_lap_session.laps:
            if lap.classification == "flying":
                result = analyze_lap(lap, multi_lap_session.metadata)
                assert result.fuel is not None
                assert result.speed.max_speed > 0


class TestAnalyzeLapEdgeCases:
    """Edge cases for lap analysis."""

    def test_all_throttle_full(self):
        """All samples at full throttle."""
        lap = make_lap_segment(n_samples=100, throttle=1.0)
        session = make_parsed_session(laps=[lap])
        result = analyze_lap(lap, session.metadata)
        assert result.driver_inputs.full_throttle_pct == pytest.approx(100.0)

    def test_all_throttle_off(self):
        """All samples at zero throttle."""
        lap = make_lap_segment(n_samples=100, throttle=0.0)
        session = make_parsed_session(laps=[lap])
        result = analyze_lap(lap, session.metadata)
        assert result.driver_inputs.off_throttle_pct == pytest.approx(100.0)

    def test_speed_min_filters_pit_speeds(self):
        """min_speed should exclude speeds < 10 km/h."""
        data = make_lap_data(n_samples=100, speed=120.0)
        # Set a few samples to very low speed
        data["speed_kmh"][0] = 2.0
        data["speed_kmh"][1] = 5.0
        lap = make_lap_segment(data=data)
        session = make_parsed_session(laps=[lap])
        result = analyze_lap(lap, session.metadata)
        assert result.speed.min_speed >= 10.0
