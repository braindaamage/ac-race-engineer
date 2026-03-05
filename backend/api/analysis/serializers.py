"""Serializers to transform AnalyzedSession into API response shapes."""

from __future__ import annotations

from ac_engineer.analyzer.models import AnalyzedSession, AnalyzedLap
from api.analysis.models import AggregatedCorner, CornerLapEntry, LapSummary


def summarize_lap(lap: AnalyzedLap) -> LapSummary:
    """Extract a LapSummary from an AnalyzedLap."""
    tyre_temps_avg: dict[str, float] = {}
    for wheel, zones in lap.metrics.tyres.temps_avg.items():
        tyre_temps_avg[wheel] = zones.core

    return LapSummary(
        lap_number=lap.lap_number,
        classification=lap.classification,
        is_invalid=lap.is_invalid,
        lap_time_s=lap.metrics.timing.lap_time_s,
        tyre_temps_avg=tyre_temps_avg,
        peak_lat_g=lap.metrics.grip.peak_lat_g,
        peak_lon_g=lap.metrics.grip.peak_lon_g,
        full_throttle_pct=lap.metrics.driver_inputs.full_throttle_pct,
        braking_pct=lap.metrics.driver_inputs.braking_pct,
    )


def summarize_all_laps(analyzed: AnalyzedSession) -> list[LapSummary]:
    """Summarize all laps in an AnalyzedSession."""
    return [summarize_lap(lap) for lap in analyzed.laps]


def aggregate_corners(analyzed: AnalyzedSession) -> list[AggregatedCorner]:
    """Aggregate corner metrics across flying laps."""
    from collections import defaultdict

    corner_data: dict[int, list] = defaultdict(list)

    for lap in analyzed.laps:
        if lap.classification != "flying":
            continue
        for corner in lap.corners:
            corner_data[corner.corner_number].append(corner)

    result: list[AggregatedCorner] = []
    for corner_number in sorted(corner_data.keys()):
        corners = corner_data[corner_number]
        sample_count = len(corners)

        apex_speeds = [c.performance.apex_speed_kmh for c in corners]
        entry_speeds = [c.performance.entry_speed_kmh for c in corners]
        exit_speeds = [c.performance.exit_speed_kmh for c in corners]
        durations = [c.performance.duration_s for c in corners]
        peak_lat_gs = [c.grip.peak_lat_g for c in corners]
        trail_braking = [c.technique.trail_braking_intensity for c in corners]

        understeer_vals = [c.grip.understeer_ratio for c in corners if c.grip.understeer_ratio is not None]
        avg_understeer = sum(understeer_vals) / len(understeer_vals) if understeer_vals else None

        result.append(AggregatedCorner(
            corner_number=corner_number,
            sample_count=sample_count,
            avg_apex_speed_kmh=sum(apex_speeds) / sample_count,
            avg_entry_speed_kmh=sum(entry_speeds) / sample_count,
            avg_exit_speed_kmh=sum(exit_speeds) / sample_count,
            avg_duration_s=sum(durations) / sample_count,
            avg_understeer_ratio=avg_understeer,
            avg_trail_braking_intensity=sum(trail_braking) / sample_count,
            avg_peak_lat_g=sum(peak_lat_gs) / sample_count,
        ))

    return result


def get_corner_by_lap(analyzed: AnalyzedSession, corner_number: int) -> list[CornerLapEntry]:
    """Return per-lap metrics for a specific corner across all laps that have it."""
    entries: list[CornerLapEntry] = []
    for lap in analyzed.laps:
        for corner in lap.corners:
            if corner.corner_number == corner_number:
                entries.append(CornerLapEntry(
                    lap_number=lap.lap_number,
                    metrics=corner,
                ))
    return entries
