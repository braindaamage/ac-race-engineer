"""Shared fixtures for knowledge base tests.

Builder functions create minimal AnalyzedSession objects with controllable
fields for signal detection testing.  Named fixtures provide ready-made
sessions that trigger specific signals.
"""

from __future__ import annotations

import pytest

from ac_engineer.analyzer.models import (
    AnalyzedLap,
    AnalyzedSession,
    AggregatedStintMetrics,
    ConsistencyMetrics,
    CornerGrip,
    CornerLoading,
    CornerMetrics,
    CornerPerformance,
    CornerTechnique,
    DriverInputMetrics,
    FuelMetrics,
    GripMetrics,
    LapMetrics,
    SpeedMetrics,
    StintMetrics,
    StintTrends,
    SuspensionMetrics,
    TimingMetrics,
    TyreMetrics,
    WheelTempZones,
)
from ac_engineer.parser.models import SessionMetadata


# ---------------------------------------------------------------------------
# Default wheel keys
# ---------------------------------------------------------------------------

WHEELS = ["fl", "fr", "rl", "rr"]


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _default_metadata(**overrides) -> SessionMetadata:
    defaults = dict(
        car_name="test_car",
        track_name="test_track",
        track_config="",
        track_length_m=5000.0,
        session_type="practice",
        tyre_compound="SM",
        driver_name="Test Driver",
        air_temp_c=22.0,
        road_temp_c=30.0,
        session_start="2026-03-02T14:00:00",
        session_end="2026-03-02T15:00:00",
        laps_completed=1,
        total_samples=200,
        sample_rate_hz=22.0,
        channels_available=["speed_kmh"],
        channels_unavailable=[],
        sim_info_available=True,
        reduced_mode=False,
        csv_filename="test.csv",
        app_version="0.2.0",
    )
    defaults.update(overrides)
    return SessionMetadata(**defaults)


def _default_tyre_metrics(**overrides) -> TyreMetrics:
    zones = WheelTempZones(core=80.0, inner=83.0, mid=80.0, outer=78.0)
    defaults = dict(
        temps_avg={w: zones for w in WHEELS},
        temps_peak={w: zones for w in WHEELS},
        pressure_avg={w: 27.0 for w in WHEELS},
        temp_spread={w: 5.0 for w in WHEELS},
        front_rear_balance=0.0,
    )
    defaults.update(overrides)
    return TyreMetrics(**defaults)


def _default_grip_metrics(**overrides) -> GripMetrics:
    defaults = dict(
        slip_angle_avg={w: 0.03 for w in WHEELS},
        slip_angle_peak={w: 0.06 for w in WHEELS},
        slip_ratio_avg={w: 0.01 for w in WHEELS},
        slip_ratio_peak={w: 0.03 for w in WHEELS},
        peak_lat_g=1.0,
        peak_lon_g=0.8,
    )
    defaults.update(overrides)
    return GripMetrics(**defaults)


def _default_lap_metrics(**overrides) -> LapMetrics:
    defaults = dict(
        timing=TimingMetrics(lap_time_s=90.0),
        tyres=overrides.pop("tyres", _default_tyre_metrics()),
        grip=overrides.pop("grip", _default_grip_metrics()),
        driver_inputs=DriverInputMetrics(
            full_throttle_pct=40.0,
            partial_throttle_pct=30.0,
            off_throttle_pct=15.0,
            braking_pct=15.0,
            avg_steering_angle=10.0,
            gear_distribution={3: 0.3, 4: 0.4, 5: 0.3},
        ),
        speed=SpeedMetrics(max_speed=220.0, min_speed=60.0, avg_speed=140.0),
        fuel=FuelMetrics(fuel_start=50.0, fuel_end=48.0, consumption=2.0),
        suspension=SuspensionMetrics(
            travel_avg={w: 0.05 for w in WHEELS},
            travel_peak={w: 0.08 for w in WHEELS},
            travel_range={w: 0.06 for w in WHEELS},
        ),
    )
    defaults.update(overrides)
    return LapMetrics(**defaults)


def make_corner_metrics(**overrides) -> CornerMetrics:
    """Build a minimal CornerMetrics with configurable fields."""
    defaults = dict(
        corner_number=overrides.pop("corner_number", 1),
        performance=CornerPerformance(
            entry_speed_kmh=120.0,
            apex_speed_kmh=80.0,
            exit_speed_kmh=100.0,
            duration_s=3.0,
        ),
        grip=CornerGrip(
            peak_lat_g=1.2,
            avg_lat_g=0.9,
            understeer_ratio=overrides.pop("understeer_ratio", 1.0),
        ),
        technique=CornerTechnique(),
        loading=None,
    )
    defaults.update(overrides)
    return CornerMetrics(**defaults)


def make_stint_metrics(**overrides) -> StintMetrics:
    """Build a minimal StintMetrics with configurable trends."""
    lap_time_slope = overrides.pop("lap_time_slope", 0.0)
    tyre_temp_slope = overrides.pop("tyre_temp_slope", 0.0)
    defaults = dict(
        stint_index=overrides.pop("stint_index", 0),
        lap_numbers=[1, 2],
        flying_lap_count=2,
        aggregated=AggregatedStintMetrics(
            lap_time_mean_s=90.0,
            lap_time_stddev_s=0.3,
        ),
        trends=StintTrends(
            lap_time_slope=lap_time_slope,
            tyre_temp_slope={w: tyre_temp_slope for w in WHEELS},
        ),
    )
    defaults.update(overrides)
    return StintMetrics(**defaults)


def make_analyzed_session(**overrides) -> AnalyzedSession:
    """Build a minimal AnalyzedSession with controllable fields."""
    defaults = dict(
        metadata=_default_metadata(),
        laps=overrides.pop("laps", [
            AnalyzedLap(
                lap_number=1,
                classification="flying",
                is_invalid=False,
                metrics=_default_lap_metrics(),
                corners=[make_corner_metrics()],
            ),
        ]),
        stints=overrides.pop("stints", [make_stint_metrics()]),
        stint_comparisons=[],
        consistency=overrides.pop("consistency", ConsistencyMetrics(
            flying_lap_count=2,
            lap_time_stddev_s=0.3,
            best_lap_time_s=89.5,
            worst_lap_time_s=90.5,
        )),
    )
    defaults.update(overrides)
    return AnalyzedSession(**defaults)


# ---------------------------------------------------------------------------
# Named pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def understeer_session() -> AnalyzedSession:
    """Session with high understeer_ratio corners (> 1.2)."""
    corners = [
        make_corner_metrics(corner_number=1, understeer_ratio=1.5),
        make_corner_metrics(corner_number=2, understeer_ratio=1.4),
    ]
    lap = AnalyzedLap(
        lap_number=1,
        classification="flying",
        is_invalid=False,
        metrics=_default_lap_metrics(),
        corners=corners,
    )
    return make_analyzed_session(laps=[lap])


@pytest.fixture
def tyre_temp_session() -> AnalyzedSession:
    """Session with high tyre temp spread on some wheels."""
    tyres = _default_tyre_metrics(
        temp_spread={"fl": 15.0, "fr": 14.0, "rl": 5.0, "rr": 5.0},
    )
    lap = AnalyzedLap(
        lap_number=1,
        classification="flying",
        is_invalid=False,
        metrics=_default_lap_metrics(tyres=tyres),
        corners=[make_corner_metrics()],
    )
    return make_analyzed_session(laps=[lap])


@pytest.fixture
def degradation_session() -> AnalyzedSession:
    """Session with positive lap_time_slope in stint trends."""
    stint = make_stint_metrics(lap_time_slope=0.5, tyre_temp_slope=0.3)
    return make_analyzed_session(stints=[stint])


@pytest.fixture
def clean_session() -> AnalyzedSession:
    """Session with all metrics within normal ranges — no signals should fire."""
    return make_analyzed_session()
