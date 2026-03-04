"""Per-corner metric computation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ac_engineer.parser.models import CornerSegment

from .models import (
    CornerGrip,
    CornerLoading,
    CornerMetrics,
    CornerPerformance,
    CornerTechnique,
)
from ._utils import (
    BRAKE_ON,
    THROTTLE_ON,
    channel_available,
    extract_corner_data,
    safe_max,
    safe_mean,
)

WHEELS = ["fl", "fr", "rl", "rr"]
UNDERSTEER_EPSILON = 0.01  # rad — minimum rear slip for ratio


def analyze_corner(corner: CornerSegment, lap_df: pd.DataFrame) -> CornerMetrics:
    """Compute metrics for a single corner from the lap's time series data.

    Args:
        corner: A CornerSegment defining the corner boundaries.
        lap_df: The full lap DataFrame with all telemetry channels.

    Returns:
        CornerMetrics with performance, grip, technique, and loading data.
    """
    cdf = extract_corner_data(lap_df, corner.entry_norm_pos, corner.exit_norm_pos)

    return CornerMetrics(
        corner_number=corner.corner_number,
        performance=_compute_performance(cdf, corner),
        grip=_compute_grip(cdf),
        technique=_compute_technique(cdf, corner),
        loading=_compute_loading(cdf),
    )


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


def _speed_at_position(cdf: pd.DataFrame, target_pos: float) -> float:
    """Get speed at the sample nearest to target_pos."""
    if cdf.empty:
        return 0.0
    idx = (cdf["normalized_position"] - target_pos).abs().idxmin()
    return float(cdf.loc[idx, "speed_kmh"])


def _compute_performance(cdf: pd.DataFrame, corner: CornerSegment) -> CornerPerformance:
    if cdf.empty:
        return CornerPerformance(
            entry_speed_kmh=0.0, apex_speed_kmh=0.0,
            exit_speed_kmh=0.0, duration_s=0.0,
        )

    entry_speed = _speed_at_position(cdf, corner.entry_norm_pos)
    apex_speed = _speed_at_position(cdf, corner.apex_norm_pos)
    exit_speed = _speed_at_position(cdf, corner.exit_norm_pos)

    ts = cdf["timestamp"]
    duration = float(ts.iloc[-1] - ts.iloc[0])

    return CornerPerformance(
        entry_speed_kmh=entry_speed,
        apex_speed_kmh=apex_speed,
        exit_speed_kmh=exit_speed,
        duration_s=duration,
    )


# ---------------------------------------------------------------------------
# Grip
# ---------------------------------------------------------------------------


def _compute_grip(cdf: pd.DataFrame) -> CornerGrip:
    if cdf.empty:
        return CornerGrip(peak_lat_g=0.0, avg_lat_g=0.0)

    g_lat_abs = cdf["g_lat"].abs()
    peak_lat_g = safe_max(g_lat_abs) or 0.0
    avg_lat_g = safe_mean(g_lat_abs) or 0.0

    # Understeer ratio
    front_slip = []
    rear_slip = []
    for w in ("fl", "fr"):
        col = f"slip_angle_{w}"
        if channel_available(cdf, col):
            v = safe_mean(cdf[col].abs())
            if v is not None:
                front_slip.append(v)
    for w in ("rl", "rr"):
        col = f"slip_angle_{w}"
        if channel_available(cdf, col):
            v = safe_mean(cdf[col].abs())
            if v is not None:
                rear_slip.append(v)

    understeer_ratio: float | None = None
    if front_slip and rear_slip:
        front_avg = sum(front_slip) / len(front_slip)
        rear_avg = sum(rear_slip) / len(rear_slip)
        if rear_avg >= UNDERSTEER_EPSILON:
            understeer_ratio = front_avg / rear_avg

    return CornerGrip(
        peak_lat_g=peak_lat_g,
        avg_lat_g=avg_lat_g,
        understeer_ratio=understeer_ratio,
    )


# ---------------------------------------------------------------------------
# Technique
# ---------------------------------------------------------------------------


def _compute_technique(cdf: pd.DataFrame, corner: CornerSegment) -> CornerTechnique:
    if cdf.empty:
        return CornerTechnique()

    # Brake point: first position where brake > threshold
    brake_point_norm: float | None = None
    braking_mask = cdf["brake"] > BRAKE_ON
    if braking_mask.any():
        first_brake_idx = braking_mask.idxmax()
        brake_point_norm = float(cdf.loc[first_brake_idx, "normalized_position"])

    # Throttle on: first position after apex where throttle > threshold
    throttle_on_norm: float | None = None
    after_apex = cdf[cdf["normalized_position"] >= corner.apex_norm_pos]
    if not after_apex.empty:
        throttle_mask = after_apex["throttle"] > THROTTLE_ON
        if throttle_mask.any():
            first_throttle_idx = throttle_mask.idxmax()
            throttle_on_norm = float(cdf.loc[first_throttle_idx, "normalized_position"])

    # Trail braking intensity: mean brake where braking AND steering
    trail_braking_intensity = 0.0
    if channel_available(cdf, "steering"):
        overlap = (cdf["brake"] > BRAKE_ON) & (cdf["steering"].abs() > 0.05)
        if overlap.any():
            trail_braking_intensity = float(cdf.loc[overlap, "brake"].mean())

    return CornerTechnique(
        brake_point_norm=brake_point_norm,
        throttle_on_norm=throttle_on_norm,
        trail_braking_intensity=trail_braking_intensity,
    )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _compute_loading(cdf: pd.DataFrame) -> CornerLoading | None:
    if cdf.empty:
        return None

    # Check if any wheel load channel is available
    available = any(channel_available(cdf, f"wheel_load_{w}") for w in WHEELS)
    if not available:
        return None

    peak_loads: dict[str, float] = {}
    for w in WHEELS:
        col = f"wheel_load_{w}"
        if channel_available(cdf, col):
            peak_loads[w] = safe_max(cdf[col]) or 0.0
        else:
            peak_loads[w] = 0.0

    return CornerLoading(peak_wheel_load=peak_loads)
