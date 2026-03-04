"""Per-lap metric computation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ac_engineer.parser.models import LapSegment, SessionMetadata

from .models import (
    DriverInputMetrics,
    FuelMetrics,
    GripMetrics,
    LapMetrics,
    SpeedMetrics,
    SuspensionMetrics,
    TimingMetrics,
    TyreMetrics,
    WheelTempZones,
)
from ._utils import (
    BRAKE_ON,
    SPEED_PIT_FILTER,
    THROTTLE_FULL,
    THROTTLE_ON,
    channel_available,
    safe_max,
    safe_mean,
    safe_min,
)

WHEELS = ["fl", "fr", "rl", "rr"]


def analyze_lap(lap: LapSegment, metadata: SessionMetadata) -> LapMetrics:
    """Compute all metric groups for a single lap.

    Args:
        lap: A LapSegment from the parser containing time series data.
        metadata: Session metadata for context (car, track, etc.).

    Returns:
        LapMetrics with timing, tyres, grip, driver inputs, speed,
        fuel (or None), and suspension metrics.
    """
    df = lap.to_dataframe()
    n = len(df)

    return LapMetrics(
        timing=_compute_timing(df, lap),
        tyres=_compute_tyres(df),
        grip=_compute_grip(df),
        driver_inputs=_compute_driver_inputs(df, n),
        speed=_compute_speed(df),
        fuel=_compute_fuel(df),
        suspension=_compute_suspension(df),
    )


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


def _compute_timing(df: pd.DataFrame, lap: LapSegment) -> TimingMetrics:
    lap_time_s = lap.end_timestamp - lap.start_timestamp

    sector_times_s = _compute_sector_times(df, lap_time_s)

    return TimingMetrics(lap_time_s=lap_time_s, sector_times_s=sector_times_s)


def _compute_sector_times(df: pd.DataFrame, lap_time_s: float) -> list[float] | None:
    """Compute 3 equal-thirds sector times by interpolating timestamps at position boundaries."""
    if not channel_available(df, "normalized_position") or not channel_available(df, "timestamp"):
        return None

    pos = df["normalized_position"].values
    ts = df["timestamp"].values

    if len(pos) < 4:
        return None

    boundaries = [1 / 3, 2 / 3]
    boundary_times = []

    for b in boundaries:
        # Find interpolated timestamp at this position
        idx = np.searchsorted(pos, b)
        if idx == 0:
            boundary_times.append(ts[0])
        elif idx >= len(pos):
            boundary_times.append(ts[-1])
        else:
            # Linear interpolation
            p0, p1 = pos[idx - 1], pos[idx]
            t0, t1 = ts[idx - 1], ts[idx]
            if p1 == p0:
                boundary_times.append(t0)
            else:
                frac = (b - p0) / (p1 - p0)
                boundary_times.append(t0 + frac * (t1 - t0))

    t_start = ts[0]
    t_end = ts[-1]

    sectors = [
        boundary_times[0] - t_start,
        boundary_times[1] - boundary_times[0],
        t_end - boundary_times[1],
    ]

    return sectors


# ---------------------------------------------------------------------------
# Tyres
# ---------------------------------------------------------------------------


def _compute_tyres(df: pd.DataFrame) -> TyreMetrics:
    temps_avg: dict[str, WheelTempZones] = {}
    temps_peak: dict[str, WheelTempZones] = {}
    pressure_avg: dict[str, float] = {}
    temp_spread: dict[str, float] = {}

    for w in WHEELS:
        zones_avg = {}
        zones_peak = {}
        for zone in ("core", "inner", "mid", "outer"):
            col = f"tyre_temp_{zone}_{w}"
            avg = safe_mean(df[col]) if channel_available(df, col) else 0.0
            peak = safe_max(df[col]) if channel_available(df, col) else 0.0
            zones_avg[zone] = avg if avg is not None else 0.0
            zones_peak[zone] = peak if peak is not None else 0.0

        temps_avg[w] = WheelTempZones(**zones_avg)
        temps_peak[w] = WheelTempZones(**zones_peak)

        pcol = f"tyre_pressure_{w}"
        p = safe_mean(df[pcol]) if channel_available(df, pcol) else 0.0
        pressure_avg[w] = p if p is not None else 0.0

        # Temp spread = inner_avg - outer_avg
        temp_spread[w] = zones_avg["inner"] - zones_avg["outer"]

    # Front-rear balance = mean(fl_core, fr_core) / mean(rl_core, rr_core)
    front_mean = (temps_avg["fl"].core + temps_avg["fr"].core) / 2
    rear_mean = (temps_avg["rl"].core + temps_avg["rr"].core) / 2
    front_rear_balance = front_mean / rear_mean if rear_mean > 0 else 1.0

    # Wear rate
    wear_rate: dict[str, float] | None = None
    if all(channel_available(df, f"tyre_wear_{w}") for w in WHEELS):
        wear_rate = {}
        for w in WHEELS:
            col = f"tyre_wear_{w}"
            first = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            last = df[col].dropna().iloc[-1] if len(df[col].dropna()) > 0 else None
            if first is not None and last is not None:
                wear_rate[w] = float(first - last)
            else:
                wear_rate[w] = 0.0

    return TyreMetrics(
        temps_avg=temps_avg,
        temps_peak=temps_peak,
        pressure_avg=pressure_avg,
        temp_spread=temp_spread,
        front_rear_balance=front_rear_balance,
        wear_rate=wear_rate,
    )


# ---------------------------------------------------------------------------
# Grip
# ---------------------------------------------------------------------------


def _compute_grip(df: pd.DataFrame) -> GripMetrics:
    slip_angle_avg: dict[str, float] = {}
    slip_angle_peak: dict[str, float] = {}
    slip_ratio_avg: dict[str, float] = {}
    slip_ratio_peak: dict[str, float] = {}

    for w in WHEELS:
        sa_col = f"slip_angle_{w}"
        sr_col = f"slip_ratio_{w}"

        if channel_available(df, sa_col):
            sa_abs = df[sa_col].abs()
            slip_angle_avg[w] = safe_mean(sa_abs) or 0.0
            slip_angle_peak[w] = safe_max(sa_abs) or 0.0
        else:
            slip_angle_avg[w] = 0.0
            slip_angle_peak[w] = 0.0

        if channel_available(df, sr_col):
            sr_abs = df[sr_col].abs()
            slip_ratio_avg[w] = safe_mean(sr_abs) or 0.0
            slip_ratio_peak[w] = safe_max(sr_abs) or 0.0
        else:
            slip_ratio_avg[w] = 0.0
            slip_ratio_peak[w] = 0.0

    peak_lat_g = safe_max(df["g_lat"].abs()) if channel_available(df, "g_lat") else 0.0
    peak_lon_g = safe_max(df["g_lon"].abs()) if channel_available(df, "g_lon") else 0.0

    return GripMetrics(
        slip_angle_avg=slip_angle_avg,
        slip_angle_peak=slip_angle_peak,
        slip_ratio_avg=slip_ratio_avg,
        slip_ratio_peak=slip_ratio_peak,
        peak_lat_g=peak_lat_g or 0.0,
        peak_lon_g=peak_lon_g or 0.0,
    )


# ---------------------------------------------------------------------------
# Driver inputs
# ---------------------------------------------------------------------------


def _compute_driver_inputs(df: pd.DataFrame, n: int) -> DriverInputMetrics:
    throttle = df["throttle"]
    brake = df["brake"]

    full_throttle = (throttle >= THROTTLE_FULL).sum()
    off_throttle = (throttle <= THROTTLE_ON).sum()
    partial_throttle = n - full_throttle - off_throttle

    braking = (brake > BRAKE_ON).sum()

    avg_steering = safe_mean(df["steering"].abs()) if channel_available(df, "steering") else 0.0

    # Gear distribution
    gear_counts = df["gear"].value_counts()
    gear_dist = {int(g): float(c / n * 100) for g, c in gear_counts.items()}

    return DriverInputMetrics(
        full_throttle_pct=float(full_throttle / n * 100),
        partial_throttle_pct=float(partial_throttle / n * 100),
        off_throttle_pct=float(off_throttle / n * 100),
        braking_pct=float(braking / n * 100),
        avg_steering_angle=avg_steering or 0.0,
        gear_distribution=gear_dist,
    )


# ---------------------------------------------------------------------------
# Speed
# ---------------------------------------------------------------------------


def _compute_speed(df: pd.DataFrame) -> SpeedMetrics:
    speed = df["speed_kmh"]
    max_speed = safe_max(speed) or 0.0
    avg_speed = safe_mean(speed) or 0.0

    # Min speed excluding pit speeds (< 10 km/h)
    filtered = speed[speed >= SPEED_PIT_FILTER]
    min_speed = safe_min(filtered) if len(filtered) > 0 else (safe_min(speed) or 0.0)

    return SpeedMetrics(
        max_speed=max_speed,
        min_speed=min_speed or 0.0,
        avg_speed=avg_speed,
    )


# ---------------------------------------------------------------------------
# Fuel
# ---------------------------------------------------------------------------


def _compute_fuel(df: pd.DataFrame) -> FuelMetrics | None:
    if not channel_available(df, "fuel"):
        return None

    fuel = df["fuel"].dropna()
    if len(fuel) < 2:
        return None

    fuel_start = float(fuel.iloc[0])
    fuel_end = float(fuel.iloc[-1])
    return FuelMetrics(
        fuel_start=fuel_start,
        fuel_end=fuel_end,
        consumption=fuel_start - fuel_end,
    )


# ---------------------------------------------------------------------------
# Suspension
# ---------------------------------------------------------------------------


def _compute_suspension(df: pd.DataFrame) -> SuspensionMetrics:
    travel_avg: dict[str, float] = {}
    travel_peak: dict[str, float] = {}
    travel_range: dict[str, float] = {}

    for w in WHEELS:
        col = f"susp_travel_{w}"
        if channel_available(df, col):
            travel_avg[w] = safe_mean(df[col]) or 0.0
            travel_peak[w] = safe_max(df[col]) or 0.0
            mn = safe_min(df[col]) or 0.0
            mx = safe_max(df[col]) or 0.0
            travel_range[w] = mx - mn
        else:
            travel_avg[w] = 0.0
            travel_peak[w] = 0.0
            travel_range[w] = 0.0

    return SuspensionMetrics(
        travel_avg=travel_avg,
        travel_peak=travel_peak,
        travel_range=travel_range,
    )
