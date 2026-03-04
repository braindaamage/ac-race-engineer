"""Telemetry analyzer — computes performance metrics from parsed sessions."""

from __future__ import annotations

from ac_engineer.parser.models import ParsedSession

from .consistency import compute_consistency
from .corner_analyzer import analyze_corner
from .lap_analyzer import analyze_lap
from .models import (
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
from .stint_analyzer import compare_stints, compute_stint_trends, group_stints

__all__ = [
    "analyze_session",
    "AggregatedStintMetrics",
    "AnalyzedLap",
    "AnalyzedSession",
    "ConsistencyMetrics",
    "CornerConsistency",
    "CornerGrip",
    "CornerLoading",
    "CornerMetrics",
    "CornerPerformance",
    "CornerTechnique",
    "DriverInputMetrics",
    "FuelMetrics",
    "GripMetrics",
    "LapMetrics",
    "MetricDeltas",
    "SetupParameterDelta",
    "SpeedMetrics",
    "StintComparison",
    "StintMetrics",
    "StintTrends",
    "SuspensionMetrics",
    "TimingMetrics",
    "TyreMetrics",
    "WheelTempZones",
]


def analyze_session(session: ParsedSession) -> AnalyzedSession:
    """Analyze a parsed session and return structured performance metrics.

    Args:
        session: A ParsedSession from the parser.

    Returns:
        AnalyzedSession with per-lap, per-corner, per-stint, and
        session-wide consistency metrics.
    """
    # 1. Analyze each lap + corners
    analyzed_laps: list[AnalyzedLap] = []
    for lap in session.laps:
        metrics = analyze_lap(lap, session.metadata)
        corners: list[CornerMetrics] = []
        if lap.corners:
            df = lap.to_dataframe()
            for c in lap.corners:
                corners.append(analyze_corner(c, df))

        analyzed_laps.append(AnalyzedLap(
            lap_number=lap.lap_number,
            classification=lap.classification,
            is_invalid=lap.is_invalid,
            metrics=metrics,
            corners=corners,
        ))

    # 2. Group into stints
    stints = group_stints(analyzed_laps, session.laps)

    # Compute trends for each stint
    for stint in stints:
        stint.trends = compute_stint_trends(stint, analyzed_laps)

    # 3. Compare adjacent stints
    stint_comparisons: list[StintComparison] = []
    for i in range(len(stints) - 1):
        sa = stints[i]
        sb = stints[i + 1]
        # Find setup for each stint
        setup_a = _find_setup(session, sa.lap_numbers[0]) if sa.lap_numbers else None
        setup_b = _find_setup(session, sb.lap_numbers[0]) if sb.lap_numbers else None
        stint_comparisons.append(compare_stints(sa, sb, setup_a, setup_b))

    # 4. Consistency
    consistency = compute_consistency(analyzed_laps)

    return AnalyzedSession(
        metadata=session.metadata,
        laps=analyzed_laps,
        stints=stints,
        stint_comparisons=stint_comparisons,
        consistency=consistency,
    )


def _find_setup(session: ParsedSession, lap_number: int):
    """Find the active setup for a given lap number."""
    lap = session.lap_by_number(lap_number)
    if lap and lap.active_setup:
        return lap.active_setup
    return None
