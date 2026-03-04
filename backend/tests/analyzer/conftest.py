"""Shared fixtures for analyzer tests.

All fixture data is generated programmatically — no game installation required.
Builds ParsedSession objects directly with controlled data for precise assertions.
"""

from __future__ import annotations

import numpy as np
import pytest

from ac_engineer.parser.models import (
    CornerSegment,
    LapClassification,
    LapSegment,
    ParsedSession,
    SessionMetadata,
    SetupEntry,
    SetupParameter,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE = 22.0
SAMPLE_INTERVAL = 1.0 / SAMPLE_RATE
BASE_TIMESTAMP = 1_740_000_000.0

WHEELS = ["fl", "fr", "rl", "rr"]

# ---------------------------------------------------------------------------
# Channel list (82 columns)
# ---------------------------------------------------------------------------

CHANNELS = [
    "timestamp", "session_time_ms", "normalized_position", "lap_count",
    "lap_time_ms", "throttle", "brake", "steering", "gear", "clutch",
    "handbrake", "speed_kmh", "rpm", "g_lat", "g_lon", "g_vert",
    "yaw_rate", "local_vel_x", "local_vel_y", "local_vel_z",
    "tyre_temp_core_fl", "tyre_temp_core_fr", "tyre_temp_core_rl", "tyre_temp_core_rr",
    "tyre_temp_inner_fl", "tyre_temp_inner_fr", "tyre_temp_inner_rl", "tyre_temp_inner_rr",
    "tyre_temp_mid_fl", "tyre_temp_mid_fr", "tyre_temp_mid_rl", "tyre_temp_mid_rr",
    "tyre_temp_outer_fl", "tyre_temp_outer_fr", "tyre_temp_outer_rl", "tyre_temp_outer_rr",
    "tyre_pressure_fl", "tyre_pressure_fr", "tyre_pressure_rl", "tyre_pressure_rr",
    "slip_angle_fl", "slip_angle_fr", "slip_angle_rl", "slip_angle_rr",
    "slip_ratio_fl", "slip_ratio_fr", "slip_ratio_rl", "slip_ratio_rr",
    "tyre_wear_fl", "tyre_wear_fr", "tyre_wear_rl", "tyre_wear_rr",
    "tyre_dirty_fl", "tyre_dirty_fr", "tyre_dirty_rl", "tyre_dirty_rr",
    "wheel_speed_fl", "wheel_speed_fr", "wheel_speed_rl", "wheel_speed_rr",
    "susp_travel_fl", "susp_travel_fr", "susp_travel_rl", "susp_travel_rr",
    "wheel_load_fl", "wheel_load_fr", "wheel_load_rl", "wheel_load_rr",
    "world_pos_x", "world_pos_y", "world_pos_z",
    "turbo_boost", "drs", "ers_charge", "fuel",
    "damage_front", "damage_rear", "damage_left", "damage_right", "damage_center",
    "in_pit_lane", "lap_invalid",
]


# ---------------------------------------------------------------------------
# Helper: build lap data dict
# ---------------------------------------------------------------------------


def make_lap_data(
    n_samples: int = 100,
    *,
    start_norm_pos: float = 0.0,
    end_norm_pos: float = 0.99,
    base_ts: float = BASE_TIMESTAMP,
    speed: float = 120.0,
    throttle: float = 0.5,
    brake: float = 0.0,
    steering: float = 0.0,
    gear: float = 3.0,
    g_lat: float = 0.0,
    g_lon: float = 0.0,
    tyre_temp_core: dict[str, float] | None = None,
    tyre_temp_inner: dict[str, float] | None = None,
    tyre_temp_mid: dict[str, float] | None = None,
    tyre_temp_outer: dict[str, float] | None = None,
    tyre_pressure: dict[str, float] | None = None,
    slip_angle: dict[str, float] | None = None,
    slip_ratio: dict[str, float] | None = None,
    susp_travel: dict[str, float] | None = None,
    wheel_load: dict[str, float] | None = None,
    fuel_start: float | None = 50.0,
    fuel_end: float | None = 48.0,
    tyre_wear: dict[str, float] | None = None,
    reduced_mode: bool = False,
) -> dict[str, list]:
    """Generate a data dict with specified channel values for a lap."""
    n = n_samples
    ts = (base_ts + np.arange(n) * SAMPLE_INTERVAL).tolist()
    norm_pos = np.linspace(start_norm_pos, end_norm_pos, n).tolist()

    nan = float("nan")

    # Defaults per-wheel
    tc = tyre_temp_core or {"fl": 80.0, "fr": 80.0, "rl": 78.0, "rr": 78.0}
    ti = tyre_temp_inner or {"fl": 85.0, "fr": 85.0, "rl": 83.0, "rr": 83.0}
    tm = tyre_temp_mid or {"fl": 82.0, "fr": 82.0, "rl": 80.0, "rr": 80.0}
    to_ = tyre_temp_outer or {"fl": 79.0, "fr": 79.0, "rl": 77.0, "rr": 77.0}
    tp = tyre_pressure or {"fl": 27.5, "fr": 27.5, "rl": 26.0, "rr": 26.0}
    sa = slip_angle or {"fl": 0.02, "fr": 0.02, "rl": 0.03, "rr": 0.03}
    sr = slip_ratio or {"fl": 0.01, "fr": 0.01, "rl": 0.015, "rr": 0.015}
    st = susp_travel or {"fl": 0.05, "fr": 0.05, "rl": 0.04, "rr": 0.04}
    wl = wheel_load or {"fl": 3000.0, "fr": 3000.0, "rl": 3200.0, "rr": 3200.0}
    tw = tyre_wear or {"fl": 0.95, "fr": 0.95, "rl": 0.95, "rr": 0.95}

    # Fuel: linear from fuel_start to fuel_end
    if fuel_start is not None and fuel_end is not None and not reduced_mode:
        fuel_vals = np.linspace(fuel_start, fuel_end, n).tolist()
    else:
        fuel_vals = [nan] * n

    data: dict[str, list] = {
        "timestamp": ts,
        "session_time_ms": [(t - BASE_TIMESTAMP) * 1000 for t in ts],
        "normalized_position": norm_pos,
        "lap_count": [0.0] * n,
        "lap_time_ms": [i * SAMPLE_INTERVAL * 1000 for i in range(n)],
        "throttle": [throttle] * n,
        "brake": [brake] * n,
        "steering": [steering] * n,
        "gear": [gear] * n,
        "clutch": [0.0] * n,
        "handbrake": [nan] * n,
        "speed_kmh": [speed] * n,
        "rpm": [6000.0] * n,
        "g_lat": [g_lat] * n,
        "g_lon": [g_lon] * n,
        "g_vert": [1.0] * n,
        "yaw_rate": [0.0] * n,
        "local_vel_x": [0.0] * n,
        "local_vel_y": [33.0] * n,
        "local_vel_z": [0.0] * n,
    }

    # Per-wheel channels
    for zone_name, zone_vals in [("core", tc), ("inner", ti), ("mid", tm), ("outer", to_)]:
        for w in WHEELS:
            v = nan if reduced_mode and zone_name != "core" else zone_vals[w]
            data[f"tyre_temp_{zone_name}_{w}"] = [v] * n

    for w in WHEELS:
        data[f"tyre_pressure_{w}"] = [tp[w]] * n
        data[f"slip_angle_{w}"] = [sa[w]] * n
        data[f"slip_ratio_{w}"] = [sr[w]] * n
        data[f"tyre_wear_{w}"] = [nan if reduced_mode else tw[w]] * n
        data[f"tyre_dirty_{w}"] = [0.0] * n
        data[f"wheel_speed_{w}"] = [200.0] * n
        data[f"susp_travel_{w}"] = [st[w]] * n
        data[f"wheel_load_{w}"] = [nan if reduced_mode else wl[w]] * n

    data["world_pos_x"] = np.linspace(0, 100, n).tolist()
    data["world_pos_y"] = [0.0] * n
    data["world_pos_z"] = np.linspace(0, 100, n).tolist()
    data["turbo_boost"] = [0.0] * n
    data["drs"] = [nan if reduced_mode else 0.0] * n
    data["ers_charge"] = [nan if reduced_mode else 0.0] * n
    data["fuel"] = fuel_vals
    for d in ["front", "rear", "left", "right", "center"]:
        data[f"damage_{d}"] = [nan if reduced_mode else 0.0] * n
    data["in_pit_lane"] = [0.0] * n
    data["lap_invalid"] = [0.0] * n

    return data


def make_lap_segment(
    lap_number: int = 1,
    classification: LapClassification = "flying",
    *,
    n_samples: int = 100,
    is_invalid: bool = False,
    data: dict[str, list] | None = None,
    corners: list[CornerSegment] | None = None,
    active_setup: SetupEntry | None = None,
    **data_kwargs,
) -> LapSegment:
    """Build a LapSegment with controlled data."""
    if data is None:
        data = make_lap_data(n_samples=n_samples, **data_kwargs)

    timestamps = data["timestamp"]
    positions = data["normalized_position"]

    return LapSegment(
        lap_number=lap_number,
        classification=classification,
        is_invalid=is_invalid,
        start_timestamp=timestamps[0],
        end_timestamp=timestamps[-1],
        start_norm_pos=positions[0],
        end_norm_pos=positions[-1],
        sample_count=len(timestamps),
        data=data,
        corners=corners or [],
        active_setup=active_setup,
    )


def make_parsed_session(
    laps: list[LapSegment] | None = None,
    setups: list[SetupEntry] | None = None,
    metadata_overrides: dict | None = None,
) -> ParsedSession:
    """Build a ParsedSession with sensible defaults."""
    meta_kwargs: dict = {
        "car_name": "bmw_m235i_racing",
        "track_name": "mugello",
        "track_config": "",
        "track_length_m": 5245.0,
        "session_type": "practice",
        "tyre_compound": "SM",
        "driver_name": "Test Driver",
        "air_temp_c": 22.0,
        "road_temp_c": 30.5,
        "session_start": "2026-03-02T14:30:00",
        "session_end": "2026-03-02T15:00:00",
        "laps_completed": len(laps) if laps else 0,
        "total_samples": sum(l.sample_count for l in laps) if laps else 0,
        "sample_rate_hz": SAMPLE_RATE,
        "channels_available": [c for c in CHANNELS if c != "handbrake"],
        "channels_unavailable": ["handbrake"],
        "sim_info_available": True,
        "reduced_mode": False,
        "csv_filename": "test_session.csv",
        "app_version": "0.2.0",
    }
    if metadata_overrides:
        meta_kwargs.update(metadata_overrides)

    return ParsedSession(
        metadata=SessionMetadata(**meta_kwargs),
        setups=setups or [],
        laps=laps or [],
    )


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

SETUP_A = SetupEntry(
    lap_start=0,
    trigger="session_start",
    confidence="high",
    filename="setup_a.ini",
    timestamp="2026-03-02T14:30:00",
    parameters=[
        SetupParameter(section="FRONT", name="CAMBER", value=-2.5),
        SetupParameter(section="FRONT", name="TOE", value=0.1),
        SetupParameter(section="REAR", name="CAMBER", value=-1.8),
        SetupParameter(section="REAR", name="TOE", value=0.05),
    ],
)

SETUP_B = SetupEntry(
    lap_start=2,
    trigger="pit_exit",
    confidence="high",
    filename="setup_b.ini",
    timestamp="2026-03-02T14:40:00",
    parameters=[
        SetupParameter(section="FRONT", name="CAMBER", value=-3.0),
        SetupParameter(section="FRONT", name="TOE", value=0.1),
        SetupParameter(section="REAR", name="CAMBER", value=-2.0),
        SetupParameter(section="REAR", name="TOE", value=0.05),
    ],
)


# ---------------------------------------------------------------------------
# Corner helpers
# ---------------------------------------------------------------------------

def make_corner(
    corner_number: int = 1,
    entry_norm_pos: float = 0.10,
    apex_norm_pos: float = 0.15,
    exit_norm_pos: float = 0.20,
    apex_speed_kmh: float = 80.0,
    entry_speed_kmh: float = 120.0,
    exit_speed_kmh: float = 100.0,
    max_lat_g: float = 1.2,
) -> CornerSegment:
    """Build a CornerSegment."""
    return CornerSegment(
        corner_number=corner_number,
        entry_norm_pos=entry_norm_pos,
        apex_norm_pos=apex_norm_pos,
        exit_norm_pos=exit_norm_pos,
        apex_speed_kmh=apex_speed_kmh,
        max_lat_g=max_lat_g,
        entry_speed_kmh=entry_speed_kmh,
        exit_speed_kmh=exit_speed_kmh,
    )


# ---------------------------------------------------------------------------
# Named pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def flying_lap_session() -> ParsedSession:
    """1 flying lap with full data and 2 corners."""
    corners = [
        make_corner(corner_number=1, entry_norm_pos=0.10, apex_norm_pos=0.15, exit_norm_pos=0.20),
        make_corner(corner_number=2, entry_norm_pos=0.50, apex_norm_pos=0.55, exit_norm_pos=0.60),
    ]
    lap = make_lap_segment(
        lap_number=1,
        classification="flying",
        n_samples=200,
        corners=corners,
        active_setup=SETUP_A,
        throttle=0.7,
        brake=0.0,
        g_lat=0.5,
        g_lon=0.3,
        slip_angle={"fl": 0.04, "fr": 0.04, "rl": 0.05, "rr": 0.05},
        slip_ratio={"fl": 0.02, "fr": 0.02, "rl": 0.025, "rr": 0.025},
        susp_travel={"fl": 0.06, "fr": 0.06, "rl": 0.05, "rr": 0.05},
    )
    return make_parsed_session(laps=[lap], setups=[SETUP_A])


@pytest.fixture
def multi_lap_session() -> ParsedSession:
    """Outlap + 2 flying + inlap — all with same setup."""
    base_ts = BASE_TIMESTAMP
    outlap = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL

    flying1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[
            make_corner(1, 0.10, 0.15, 0.20),
            make_corner(2, 0.50, 0.55, 0.60),
        ],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
        slip_angle={"fl": 0.04, "fr": 0.04, "rl": 0.05, "rr": 0.05},
    )
    base_ts += 200 * SAMPLE_INTERVAL

    flying2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        corners=[
            make_corner(1, 0.10, 0.15, 0.20),
            make_corner(2, 0.50, 0.55, 0.60),
        ],
        throttle=0.8, g_lat=0.6, g_lon=0.4,
        slip_angle={"fl": 0.04, "fr": 0.04, "rl": 0.05, "rr": 0.05},
    )
    base_ts += 200 * SAMPLE_INTERVAL

    inlap = make_lap_segment(
        lap_number=3, classification="inlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )

    return make_parsed_session(
        laps=[outlap, flying1, flying2, inlap],
        setups=[SETUP_A],
    )


@pytest.fixture
def reduced_mode_session() -> ParsedSession:
    """Session with NaN for tyre_wear, fuel, wheel_load channels."""
    lap = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        active_setup=SETUP_A, reduced_mode=True,
    )
    return make_parsed_session(
        laps=[lap],
        setups=[SETUP_A],
        metadata_overrides={"reduced_mode": True, "sim_info_available": False},
    )


@pytest.fixture
def two_stint_session() -> ParsedSession:
    """2 stints with different setups, 2 flying laps each."""
    base_ts = BASE_TIMESTAMP

    # Stint 1: setup A, laps 0-1
    lap0 = make_lap_segment(
        lap_number=0, classification="outlap", n_samples=100,
        base_ts=base_ts, active_setup=SETUP_A,
    )
    base_ts += 100 * SAMPLE_INTERVAL

    lap1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_A,
        speed=130.0, fuel_start=50.0, fuel_end=48.5,
        corners=[make_corner(1, 0.10, 0.15, 0.20)],
    )
    base_ts += 200 * SAMPLE_INTERVAL

    # Stint 2: setup B, laps 2-3
    lap2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_B,
        speed=125.0, fuel_start=45.0, fuel_end=43.0,
        corners=[make_corner(1, 0.10, 0.15, 0.20)],
    )
    base_ts += 200 * SAMPLE_INTERVAL

    lap3 = make_lap_segment(
        lap_number=3, classification="flying", n_samples=200,
        base_ts=base_ts, active_setup=SETUP_B,
        speed=126.0, fuel_start=43.0, fuel_end=41.0,
        corners=[make_corner(1, 0.10, 0.15, 0.20)],
    )

    return make_parsed_session(
        laps=[lap0, lap1, lap2, lap3],
        setups=[SETUP_A, SETUP_B],
    )


@pytest.fixture
def single_flying_lap_session() -> ParsedSession:
    """1 flying lap only — tests edge cases for consistency."""
    lap = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        active_setup=SETUP_A,
        corners=[make_corner(1, 0.10, 0.15, 0.20)],
    )
    return make_parsed_session(laps=[lap], setups=[SETUP_A])


@pytest.fixture
def all_invalid_session() -> ParsedSession:
    """All laps with is_invalid=True."""
    base_ts = BASE_TIMESTAMP
    lap1 = make_lap_segment(
        lap_number=1, classification="flying", n_samples=200,
        base_ts=base_ts, is_invalid=True, active_setup=SETUP_A,
    )
    base_ts += 200 * SAMPLE_INTERVAL
    lap2 = make_lap_segment(
        lap_number=2, classification="flying", n_samples=200,
        base_ts=base_ts, is_invalid=True, active_setup=SETUP_A,
    )
    return make_parsed_session(laps=[lap1, lap2], setups=[SETUP_A])
