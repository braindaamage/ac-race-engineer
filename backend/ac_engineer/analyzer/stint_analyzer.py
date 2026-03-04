"""Stint grouping, aggregation, trends, and cross-stint comparison."""

from __future__ import annotations

import numpy as np

from ac_engineer.parser.models import LapSegment, SetupEntry

from .models import (
    AggregatedStintMetrics,
    AnalyzedLap,
    MetricDeltas,
    SetupParameterDelta,
    StintComparison,
    StintMetrics,
    StintTrends,
)
from ._utils import compute_trend_slope

WHEELS = ["fl", "fr", "rl", "rr"]


def _setup_key(lap: LapSegment) -> str | None:
    """Identity key for a setup: lap_start + filename, or None."""
    if lap.active_setup is None:
        return None
    return f"{lap.active_setup.lap_start}:{lap.active_setup.filename}"


def group_stints(
    analyzed_laps: list[AnalyzedLap],
    session_laps: list[LapSegment],
) -> list[StintMetrics]:
    """Group laps by consecutive active_setup identity.

    Args:
        analyzed_laps: Analyzed laps with computed metrics.
        session_laps: Original LapSegments from the parser (for setup info).

    Returns:
        List of StintMetrics, one per consecutive setup group.
    """
    if not analyzed_laps:
        return []

    stints: list[StintMetrics] = []
    current_key = _setup_key(session_laps[0])
    current_laps: list[int] = []  # indices into analyzed_laps
    current_setup_filename = (
        session_laps[0].active_setup.filename
        if session_laps[0].active_setup else None
    )

    for i, (alap, slap) in enumerate(zip(analyzed_laps, session_laps)):
        key = _setup_key(slap)
        if key != current_key and current_laps:
            # Finish current stint
            stints.append(_build_stint(
                stint_index=len(stints),
                lap_indices=current_laps,
                analyzed_laps=analyzed_laps,
                setup_filename=current_setup_filename,
            ))
            current_laps = []
            current_key = key
            current_setup_filename = (
                slap.active_setup.filename if slap.active_setup else None
            )
        current_laps.append(i)

    # Final stint
    if current_laps:
        stints.append(_build_stint(
            stint_index=len(stints),
            lap_indices=current_laps,
            analyzed_laps=analyzed_laps,
            setup_filename=current_setup_filename,
        ))

    return stints


def _build_stint(
    stint_index: int,
    lap_indices: list[int],
    analyzed_laps: list[AnalyzedLap],
    setup_filename: str | None,
) -> StintMetrics:
    """Build a StintMetrics from a group of lap indices."""
    laps = [analyzed_laps[i] for i in lap_indices]
    flying = [l for l in laps if l.classification == "flying"]

    lap_numbers = [l.lap_number for l in laps]
    aggregated = _aggregate(flying)

    return StintMetrics(
        stint_index=stint_index,
        setup_filename=setup_filename,
        lap_numbers=lap_numbers,
        flying_lap_count=len(flying),
        aggregated=aggregated,
    )


def _aggregate(flying_laps: list[AnalyzedLap]) -> AggregatedStintMetrics:
    """Compute aggregated metrics across flying laps."""
    if not flying_laps:
        return AggregatedStintMetrics()

    times = [l.metrics.timing.lap_time_s for l in flying_laps]
    mean_time = float(np.mean(times))
    stddev_time = float(np.std(times)) if len(times) >= 2 else None

    # Per-wheel averages
    tyre_temp_avg: dict[str, float] = {}
    slip_angle_avg: dict[str, float] = {}
    slip_ratio_avg: dict[str, float] = {}
    for w in WHEELS:
        temps = [l.metrics.tyres.temps_avg[w].core for l in flying_laps]
        tyre_temp_avg[w] = float(np.mean(temps))
        angles = [l.metrics.grip.slip_angle_avg[w] for l in flying_laps]
        slip_angle_avg[w] = float(np.mean(angles))
        ratios = [l.metrics.grip.slip_ratio_avg[w] for l in flying_laps]
        slip_ratio_avg[w] = float(np.mean(ratios))

    lat_gs = [l.metrics.grip.peak_lat_g for l in flying_laps]
    peak_lat_g_avg = float(np.mean(lat_gs))

    return AggregatedStintMetrics(
        lap_time_mean_s=mean_time,
        lap_time_stddev_s=stddev_time,
        tyre_temp_avg=tyre_temp_avg,
        slip_angle_avg=slip_angle_avg,
        slip_ratio_avg=slip_ratio_avg,
        peak_lat_g_avg=peak_lat_g_avg,
    )


def compute_stint_trends(
    stint: StintMetrics,
    analyzed_laps: list[AnalyzedLap],
) -> StintTrends | None:
    """Compute linear trends within a stint.

    Args:
        stint: The stint to compute trends for.
        analyzed_laps: All analyzed laps (filtered to this stint internally).

    Returns:
        StintTrends with slope values, or None if < 2 flying laps.
    """
    flying = [
        l for l in analyzed_laps
        if l.lap_number in stint.lap_numbers and l.classification == "flying"
    ]
    if len(flying) < 2:
        return None

    times = [l.metrics.timing.lap_time_s for l in flying]
    lap_time_slope = compute_trend_slope(times)
    if lap_time_slope is None:
        return None

    tyre_temp_slope: dict[str, float] = {}
    for w in WHEELS:
        temps = [l.metrics.tyres.temps_avg[w].core for l in flying]
        slope = compute_trend_slope(temps)
        tyre_temp_slope[w] = slope if slope is not None else 0.0

    # Fuel consumption trend
    fuel_consumptions = []
    for l in flying:
        if l.metrics.fuel is not None:
            fuel_consumptions.append(l.metrics.fuel.consumption)
    fuel_slope = compute_trend_slope(fuel_consumptions)

    return StintTrends(
        lap_time_slope=lap_time_slope,
        tyre_temp_slope=tyre_temp_slope,
        fuel_consumption_slope=fuel_slope,
    )


def compare_stints(
    stint_a: StintMetrics,
    stint_b: StintMetrics,
    setup_a: SetupEntry | None,
    setup_b: SetupEntry | None,
) -> StintComparison:
    """Compare two stints: metric deltas and setup parameter diffs.

    Args:
        stint_a: First stint (baseline).
        stint_b: Second stint (comparison).
        setup_a: Setup for stint A, or None.
        setup_b: Setup for stint B, or None.

    Returns:
        StintComparison with metric deltas (B - A) and setup changes.
    """
    metric_deltas = _compute_deltas(stint_a.aggregated, stint_b.aggregated)
    setup_changes = _diff_setups(setup_a, setup_b)

    return StintComparison(
        stint_a_index=stint_a.stint_index,
        stint_b_index=stint_b.stint_index,
        setup_changes=setup_changes,
        metric_deltas=metric_deltas,
    )


def _compute_deltas(a: AggregatedStintMetrics, b: AggregatedStintMetrics) -> MetricDeltas:
    """Compute B - A for aggregated metrics."""
    lap_time_delta = None
    if a.lap_time_mean_s is not None and b.lap_time_mean_s is not None:
        lap_time_delta = b.lap_time_mean_s - a.lap_time_mean_s

    tyre_temp_delta: dict[str, float] = {}
    slip_angle_delta: dict[str, float] = {}
    slip_ratio_delta: dict[str, float] = {}
    for w in WHEELS:
        if w in a.tyre_temp_avg and w in b.tyre_temp_avg:
            tyre_temp_delta[w] = b.tyre_temp_avg[w] - a.tyre_temp_avg[w]
        if w in a.slip_angle_avg and w in b.slip_angle_avg:
            slip_angle_delta[w] = b.slip_angle_avg[w] - a.slip_angle_avg[w]
        if w in a.slip_ratio_avg and w in b.slip_ratio_avg:
            slip_ratio_delta[w] = b.slip_ratio_avg[w] - a.slip_ratio_avg[w]

    peak_lat_g_delta = None
    if a.peak_lat_g_avg is not None and b.peak_lat_g_avg is not None:
        peak_lat_g_delta = b.peak_lat_g_avg - a.peak_lat_g_avg

    return MetricDeltas(
        lap_time_delta_s=lap_time_delta,
        tyre_temp_delta=tyre_temp_delta,
        slip_angle_delta=slip_angle_delta,
        slip_ratio_delta=slip_ratio_delta,
        peak_lat_g_delta=peak_lat_g_delta,
    )


def _diff_setups(
    setup_a: SetupEntry | None,
    setup_b: SetupEntry | None,
) -> list[SetupParameterDelta]:
    """Diff setup parameters between two stints."""
    if setup_a is None or setup_b is None:
        return []

    # Build lookup for setup_a parameters
    a_params = {(p.section, p.name): p.value for p in setup_a.parameters}
    b_params = {(p.section, p.name): p.value for p in setup_b.parameters}

    changes: list[SetupParameterDelta] = []
    all_keys = set(a_params.keys()) | set(b_params.keys())
    for key in sorted(all_keys):
        val_a = a_params.get(key)
        val_b = b_params.get(key)
        if val_a != val_b and val_a is not None and val_b is not None:
            changes.append(SetupParameterDelta(
                section=key[0], name=key[1],
                value_a=val_a, value_b=val_b,
            ))

    return changes
