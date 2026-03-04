"""Shared fixtures for engineer core tests.

Builder functions and named fixtures for creating AnalyzedSession, ACConfig,
and setup .ini file objects used across all engineer test modules.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from ac_engineer.analyzer.models import (
    AggregatedStintMetrics,
    AnalyzedLap,
    AnalyzedSession,
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
    StintComparison,
    StintMetrics,
    StintTrends,
    SuspensionMetrics,
    TimingMetrics,
    TyreMetrics,
    WheelTempZones,
    MetricDeltas,
    SetupParameterDelta,
)
from ac_engineer.config import ACConfig
from ac_engineer.parser.models import SessionMetadata


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WHEELS = ["fl", "fr", "rl", "rr"]


# ---------------------------------------------------------------------------
# Builders — SessionMetadata
# ---------------------------------------------------------------------------


def _default_metadata(**overrides) -> SessionMetadata:
    defaults = dict(
        car_name="test_car",
        track_name="test_track",
        track_config="default",
        track_length_m=5000.0,
        session_type="practice",
        tyre_compound="SM",
        driver_name="Test Driver",
        air_temp_c=22.0,
        road_temp_c=30.0,
        session_start="2026-03-02T14:00:00",
        session_end="2026-03-02T15:00:00",
        laps_completed=10,
        total_samples=2000,
        sample_rate_hz=22.0,
        channels_available=["speed_kmh"],
        channels_unavailable=[],
        sim_info_available=True,
        reduced_mode=False,
        csv_filename="test_session.csv",
        app_version="0.2.0",
    )
    defaults.update(overrides)
    return SessionMetadata(**defaults)


# ---------------------------------------------------------------------------
# Builders — Lap / Corner metrics
# ---------------------------------------------------------------------------


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
        peak_lat_g=1.2,
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
    corner_number = overrides.pop("corner_number", 1)
    understeer_ratio = overrides.pop("understeer_ratio", 1.0)
    avg_lat_g = overrides.pop("avg_lat_g", 0.9)
    entry_speed = overrides.pop("entry_speed_kmh", 120.0)
    apex_speed = overrides.pop("apex_speed_kmh", 80.0)
    exit_speed = overrides.pop("exit_speed_kmh", 100.0)

    defaults = dict(
        corner_number=corner_number,
        performance=CornerPerformance(
            entry_speed_kmh=entry_speed,
            apex_speed_kmh=apex_speed,
            exit_speed_kmh=exit_speed,
            duration_s=3.0,
        ),
        grip=CornerGrip(
            peak_lat_g=1.2,
            avg_lat_g=avg_lat_g,
            understeer_ratio=understeer_ratio,
        ),
        technique=CornerTechnique(),
        loading=None,
    )
    defaults.update(overrides)
    return CornerMetrics(**defaults)


def make_analyzed_lap(
    lap_number: int = 1,
    classification: str = "flying",
    lap_time_s: float = 90.0,
    corners: list[CornerMetrics] | None = None,
    **overrides,
) -> AnalyzedLap:
    """Build an AnalyzedLap with configurable classification and metrics."""
    metrics = _default_lap_metrics(
        timing=TimingMetrics(lap_time_s=lap_time_s),
        **{k: v for k, v in overrides.items() if k in ("tyres", "grip", "speed", "fuel", "suspension")},
    )
    return AnalyzedLap(
        lap_number=lap_number,
        classification=classification,
        is_invalid=(classification == "invalid"),
        metrics=metrics,
        corners=corners if corners is not None else [make_corner_metrics()],
    )


def make_stint_metrics(
    stint_index: int = 0,
    lap_numbers: list[int] | None = None,
    flying_lap_count: int = 2,
    lap_time_mean_s: float = 90.0,
    lap_time_stddev_s: float = 0.3,
    lap_time_slope: float = 0.0,
    tyre_temp_slope: float = 0.0,
    setup_filename: str | None = "race_setup.ini",
    **overrides,
) -> StintMetrics:
    """Build a minimal StintMetrics with configurable trends."""
    defaults = dict(
        stint_index=stint_index,
        setup_filename=setup_filename,
        lap_numbers=lap_numbers or [1, 2],
        flying_lap_count=flying_lap_count,
        aggregated=AggregatedStintMetrics(
            lap_time_mean_s=lap_time_mean_s,
            lap_time_stddev_s=lap_time_stddev_s,
            tyre_temp_avg={w: 80.0 for w in WHEELS},
        ),
        trends=StintTrends(
            lap_time_slope=lap_time_slope,
            tyre_temp_slope={w: tyre_temp_slope for w in WHEELS},
        ),
    )
    defaults.update(overrides)
    return StintMetrics(**defaults)


def make_analyzed_session(
    laps: list[AnalyzedLap] | None = None,
    stints: list[StintMetrics] | None = None,
    stint_comparisons: list[StintComparison] | None = None,
    consistency: ConsistencyMetrics | None = None,
    **metadata_overrides,
) -> AnalyzedSession:
    """Build a minimal AnalyzedSession with controllable fields."""
    if laps is None:
        laps = [make_analyzed_lap()]
    if stints is None:
        stints = [make_stint_metrics()]
    if consistency is None:
        consistency = ConsistencyMetrics(
            flying_lap_count=len([l for l in laps if l.classification == "flying"]),
            lap_time_stddev_s=0.3,
            best_lap_time_s=89.5,
            worst_lap_time_s=90.5,
        )
    return AnalyzedSession(
        metadata=_default_metadata(**metadata_overrides),
        laps=laps,
        stints=stints,
        stint_comparisons=stint_comparisons or [],
        consistency=consistency,
    )


# ---------------------------------------------------------------------------
# Named fixtures — SessionMetadata
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_metadata() -> SessionMetadata:
    """A basic SessionMetadata for testing."""
    return _default_metadata()


# ---------------------------------------------------------------------------
# Named fixtures — ACConfig
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_config(tmp_path: Path) -> ACConfig:
    """ACConfig with tmp_path as ac_install_path."""
    return ACConfig(ac_install_path=tmp_path)


# ---------------------------------------------------------------------------
# Named fixtures — Setup .ini files
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_setup_ini(tmp_path: Path) -> Path:
    """Write a multi-section setup .ini file to tmp_path and return its path."""
    setup_path = tmp_path / "race_setup.ini"
    setup_path.write_text(
        textwrap.dedent("""\
            [CAMBER_LF]
            VALUE=-2.0

            [CAMBER_RF]
            VALUE=-2.0

            [TOE_OUT_LF]
            VALUE=0.10

            [TOE_OUT_RF]
            VALUE=0.10

            [PRESSURE_LF]
            VALUE=26.5

            [PRESSURE_RF]
            VALUE=26.5

            [PRESSURE_RL]
            VALUE=25.0

            [PRESSURE_RR]
            VALUE=25.0

            [WING_1]
            VALUE=5

            [WING_2]
            VALUE=7

            [ARB_FRONT]
            VALUE=3

            [ARB_REAR]
            VALUE=4

            [SPRING_RATE_LF]
            VALUE=80000

            [SPRING_RATE_RF]
            VALUE=80000

            [SPRING_RATE_RL]
            VALUE=65000

            [SPRING_RATE_RR]
            VALUE=65000

            [DAMP_BUMP_LF]
            VALUE=5

            [DAMP_BUMP_RF]
            VALUE=5

            [DAMP_BUMP_RL]
            VALUE=4

            [DAMP_BUMP_RR]
            VALUE=4
        """),
        encoding="utf-8",
    )
    return setup_path


@pytest.fixture
def sample_car_data_dir(tmp_path: Path) -> Path:
    """Create a car's data/setup.ini with parameter ranges in tmp_path.

    Directory structure: tmp_path/content/cars/test_car/data/setup.ini
    Returns tmp_path (the AC install path).
    """
    data_dir = tmp_path / "content" / "cars" / "test_car" / "data"
    data_dir.mkdir(parents=True)

    setup_ini = data_dir / "setup.ini"
    setup_ini.write_text(
        textwrap.dedent("""\
            [CAMBER_LF]
            SHOW_CLICKS=0
            TAB=ALIGNMENT
            NAME=Camber LF
            MIN=-5.0
            MAX=0.0
            STEP=0.1
            POS_X=0
            POS_Y=0
            HELP=HELP_CAMBER

            [CAMBER_RF]
            SHOW_CLICKS=0
            TAB=ALIGNMENT
            NAME=Camber RF
            MIN=-5.0
            MAX=0.0
            STEP=0.1
            POS_X=1
            POS_Y=0
            HELP=HELP_CAMBER

            [PRESSURE_LF]
            SHOW_CLICKS=0
            TAB=TYRES
            NAME=Pressure LF
            MIN=20.0
            MAX=35.0
            STEP=0.5
            POS_X=0
            POS_Y=0
            HELP=HELP_PRESSURE

            [PRESSURE_RF]
            SHOW_CLICKS=0
            TAB=TYRES
            NAME=Pressure RF
            MIN=20.0
            MAX=35.0
            STEP=0.5
            POS_X=1
            POS_Y=0
            HELP=HELP_PRESSURE

            [WING_1]
            SHOW_CLICKS=1
            TAB=AERO
            NAME=Front Wing
            MIN=0
            MAX=20
            STEP=1
            POS_X=0
            POS_Y=0
            HELP=HELP_WING

            [SPRING_RATE_LF]
            SHOW_CLICKS=1
            TAB=SUSPENSION
            NAME=Spring Rate LF
            MIN=50000
            MAX=120000
            STEP=5000
            DEFAULT=80000
            POS_X=0
            POS_Y=0
            HELP=HELP_SPRING
        """),
        encoding="utf-8",
    )
    return tmp_path
