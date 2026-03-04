"""Session-wide consistency analysis."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .models import AnalyzedLap, ConsistencyMetrics, CornerConsistency
from ._utils import compute_trend_slope


def compute_consistency(
    analyzed_laps: list[AnalyzedLap],
) -> ConsistencyMetrics | None:
    """Compute session-wide consistency metrics across all flying laps.

    Args:
        analyzed_laps: All analyzed laps from the session.

    Returns:
        ConsistencyMetrics with lap time stats and per-corner variance,
        or None if there are no flying laps.
    """
    flying = [l for l in analyzed_laps if l.classification == "flying"]
    if not flying:
        return None

    times = [l.metrics.timing.lap_time_s for l in flying]

    stddev = float(np.std(times))
    best = float(np.min(times))
    worst = float(np.max(times))
    trend = compute_trend_slope(times)

    # Corner consistency
    corner_data: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: {"apex_speed": [], "brake_point": []}
    )

    for lap in flying:
        for cm in lap.corners:
            corner_data[cm.corner_number]["apex_speed"].append(
                cm.performance.apex_speed_kmh
            )
            if cm.technique.brake_point_norm is not None:
                corner_data[cm.corner_number]["brake_point"].append(
                    cm.technique.brake_point_norm
                )

    corner_consistency: list[CornerConsistency] = []
    for cn in sorted(corner_data.keys()):
        speeds = corner_data[cn]["apex_speed"]
        brakes = corner_data[cn]["brake_point"]

        apex_var = float(np.var(speeds)) if len(speeds) >= 2 else None
        apex_std = float(np.std(speeds)) if len(speeds) >= 2 else None
        brake_var = float(np.var(brakes)) if len(brakes) >= 2 else None

        corner_consistency.append(CornerConsistency(
            corner_number=cn,
            apex_speed_variance=apex_var,
            apex_speed_stddev=apex_std,
            brake_point_variance=brake_var,
            sample_count=len(speeds),
        ))

    return ConsistencyMetrics(
        flying_lap_count=len(flying),
        lap_time_stddev_s=stddev,
        best_lap_time_s=best,
        worst_lap_time_s=worst,
        lap_time_trend_slope=trend,
        corner_consistency=corner_consistency,
    )
