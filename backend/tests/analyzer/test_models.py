"""Tests for analyzer Pydantic v2 models."""

from __future__ import annotations

import pytest

from ac_engineer.analyzer.models import (
    AggregatedStintMetrics,
    AnalyzedLap,
    AnalyzedSession,
    ConsistencyMetrics,
    CornerConsistency,
    CornerGrip,
    CornerLoading,
    CornerMetrics,
    CornerPerformance,
    CornerTechnique,
    DriverInputMetrics,
    FuelMetrics,
    GripMetrics,
    LapMetrics,
    MetricDeltas,
    SetupParameterDelta,
    SpeedMetrics,
    StintComparison,
    StintMetrics,
    StintTrends,
    SuspensionMetrics,
    TimingMetrics,
    TyreMetrics,
    WheelTempZones,
)
from ac_engineer.parser.models import SessionMetadata


WHEEL_DICT = {"fl": 1.0, "fr": 1.0, "rl": 1.0, "rr": 1.0}
WHEEL_TEMPS = {
    w: WheelTempZones(core=80.0, inner=85.0, mid=82.0, outer=79.0)
    for w in ("fl", "fr", "rl", "rr")
}


class TestWheelTempZones:
    def test_construction(self):
        z = WheelTempZones(core=80.0, inner=85.0, mid=82.0, outer=79.0)
        assert z.core == 80.0
        assert z.outer == 79.0


class TestTimingMetrics:
    def test_with_sectors(self):
        t = TimingMetrics(lap_time_s=90.5, sector_times_s=[30.0, 30.5, 30.0])
        assert t.lap_time_s == 90.5
        assert len(t.sector_times_s) == 3

    def test_without_sectors(self):
        t = TimingMetrics(lap_time_s=90.5)
        assert t.sector_times_s is None


class TestTyreMetrics:
    def test_construction(self):
        t = TyreMetrics(
            temps_avg=WHEEL_TEMPS,
            temps_peak=WHEEL_TEMPS,
            pressure_avg=WHEEL_DICT,
            temp_spread=WHEEL_DICT,
            front_rear_balance=1.02,
        )
        assert t.front_rear_balance == 1.02
        assert t.wear_rate is None

    def test_with_wear(self):
        t = TyreMetrics(
            temps_avg=WHEEL_TEMPS,
            temps_peak=WHEEL_TEMPS,
            pressure_avg=WHEEL_DICT,
            temp_spread=WHEEL_DICT,
            front_rear_balance=1.0,
            wear_rate=WHEEL_DICT,
        )
        assert t.wear_rate is not None


class TestGripMetrics:
    def test_construction(self):
        g = GripMetrics(
            slip_angle_avg=WHEEL_DICT,
            slip_angle_peak=WHEEL_DICT,
            slip_ratio_avg=WHEEL_DICT,
            slip_ratio_peak=WHEEL_DICT,
            peak_lat_g=1.5,
            peak_lon_g=1.2,
        )
        assert g.peak_lat_g == 1.5


class TestDriverInputMetrics:
    def test_construction(self):
        d = DriverInputMetrics(
            full_throttle_pct=45.0,
            partial_throttle_pct=30.0,
            off_throttle_pct=25.0,
            braking_pct=20.0,
            avg_steering_angle=15.0,
            gear_distribution={3: 40.0, 4: 35.0, 5: 25.0},
        )
        assert d.full_throttle_pct == 45.0
        assert sum(d.gear_distribution.values()) == pytest.approx(100.0)


class TestSpeedMetrics:
    def test_construction(self):
        s = SpeedMetrics(max_speed=250.0, min_speed=50.0, avg_speed=150.0)
        assert s.max_speed == 250.0


class TestFuelMetrics:
    def test_construction(self):
        f = FuelMetrics(fuel_start=50.0, fuel_end=48.0, consumption=2.0)
        assert f.consumption == 2.0


class TestSuspensionMetrics:
    def test_construction(self):
        s = SuspensionMetrics(
            travel_avg=WHEEL_DICT,
            travel_peak=WHEEL_DICT,
            travel_range=WHEEL_DICT,
        )
        assert s.travel_avg["fl"] == 1.0


class TestLapMetrics:
    def test_with_fuel(self):
        lm = _make_lap_metrics(with_fuel=True)
        assert lm.fuel is not None

    def test_without_fuel(self):
        lm = _make_lap_metrics(with_fuel=False)
        assert lm.fuel is None


class TestCornerModels:
    def test_corner_metrics_with_loading(self):
        cm = CornerMetrics(
            corner_number=1,
            performance=CornerPerformance(
                entry_speed_kmh=120.0, apex_speed_kmh=80.0,
                exit_speed_kmh=100.0, duration_s=3.5,
            ),
            grip=CornerGrip(peak_lat_g=1.5, avg_lat_g=1.2, understeer_ratio=1.1),
            technique=CornerTechnique(
                brake_point_norm=0.08, throttle_on_norm=0.16,
                trail_braking_intensity=0.3,
            ),
            loading=CornerLoading(peak_wheel_load=WHEEL_DICT),
        )
        assert cm.loading is not None

    def test_corner_metrics_without_loading(self):
        cm = CornerMetrics(
            corner_number=1,
            performance=CornerPerformance(
                entry_speed_kmh=120.0, apex_speed_kmh=80.0,
                exit_speed_kmh=100.0, duration_s=3.5,
            ),
            grip=CornerGrip(peak_lat_g=1.5, avg_lat_g=1.2),
            technique=CornerTechnique(),
        )
        assert cm.loading is None
        assert cm.grip.understeer_ratio is None

    def test_corner_technique_defaults(self):
        ct = CornerTechnique()
        assert ct.brake_point_norm is None
        assert ct.throttle_on_norm is None
        assert ct.trail_braking_intensity == 0.0


class TestAnalyzedLap:
    def test_construction(self):
        al = AnalyzedLap(
            lap_number=1,
            classification="flying",
            is_invalid=False,
            metrics=_make_lap_metrics(),
        )
        assert al.lap_number == 1
        assert al.corners == []


class TestStintModels:
    def test_stint_metrics(self):
        sm = StintMetrics(
            stint_index=0,
            setup_filename="setup.ini",
            lap_numbers=[1, 2, 3],
            flying_lap_count=2,
            aggregated=AggregatedStintMetrics(),
        )
        assert sm.trends is None

    def test_stint_comparison(self):
        sc = StintComparison(
            stint_a_index=0,
            stint_b_index=1,
            metric_deltas=MetricDeltas(),
        )
        assert sc.setup_changes == []

    def test_setup_parameter_delta(self):
        d = SetupParameterDelta(
            section="FRONT", name="CAMBER", value_a=-2.5, value_b=-3.0,
        )
        assert d.value_a == -2.5


class TestConsistencyModels:
    def test_consistency_metrics(self):
        cm = ConsistencyMetrics(
            flying_lap_count=5,
            lap_time_stddev_s=0.8,
            best_lap_time_s=89.5,
            worst_lap_time_s=91.2,
        )
        assert cm.lap_time_trend_slope is None

    def test_corner_consistency(self):
        cc = CornerConsistency(
            corner_number=1,
            apex_speed_variance=4.5,
            apex_speed_stddev=2.12,
            sample_count=5,
        )
        assert cc.brake_point_variance is None


class TestAnalyzedSession:
    def test_minimal(self):
        meta = SessionMetadata(
            car_name="test", track_name="test", track_config="",
            session_type="practice", tyre_compound="SM",
            driver_name="Test", session_start="2026-01-01T00:00:00",
            csv_filename="test.csv", app_version="0.2.0",
        )
        s = AnalyzedSession(metadata=meta)
        assert s.laps == []
        assert s.consistency is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_lap_metrics(with_fuel: bool = False) -> LapMetrics:
    return LapMetrics(
        timing=TimingMetrics(lap_time_s=90.0),
        tyres=TyreMetrics(
            temps_avg=WHEEL_TEMPS, temps_peak=WHEEL_TEMPS,
            pressure_avg=WHEEL_DICT, temp_spread=WHEEL_DICT,
            front_rear_balance=1.0,
        ),
        grip=GripMetrics(
            slip_angle_avg=WHEEL_DICT, slip_angle_peak=WHEEL_DICT,
            slip_ratio_avg=WHEEL_DICT, slip_ratio_peak=WHEEL_DICT,
            peak_lat_g=1.5, peak_lon_g=1.2,
        ),
        driver_inputs=DriverInputMetrics(
            full_throttle_pct=45.0, partial_throttle_pct=30.0,
            off_throttle_pct=25.0, braking_pct=20.0,
            avg_steering_angle=15.0, gear_distribution={3: 100.0},
        ),
        speed=SpeedMetrics(max_speed=250.0, min_speed=50.0, avg_speed=150.0),
        fuel=FuelMetrics(fuel_start=50.0, fuel_end=48.0, consumption=2.0) if with_fuel else None,
        suspension=SuspensionMetrics(
            travel_avg=WHEEL_DICT, travel_peak=WHEEL_DICT, travel_range=WHEEL_DICT,
        ),
    )
