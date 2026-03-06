"""Serializers to transform AnalyzedSession into API response shapes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ac_engineer.analyzer.models import AnalyzedSession, AnalyzedLap
from api.analysis.models import (
    AggregatedCorner,
    CornerLapEntry,
    LapSummary,
    LapTelemetryChannels,
    LapTelemetryResponse,
)


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
        max_speed=lap.metrics.speed.max_speed,
        sector_times_s=lap.metrics.timing.sector_times_s,
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


TELEMETRY_CHANNELS = [
    "normalized_position", "throttle", "brake", "steering", "speed_kmh", "gear",
]


def telemetry_for_lap(
    parquet_path: Path,
    session_id: str,
    lap_number: int,
    max_samples: int = 500,
) -> LapTelemetryResponse:
    """Read telemetry from Parquet, filter to one lap, downsample, return response.

    Raises:
        FileNotFoundError: If the parquet file does not exist.
        ValueError: If the lap number is not found in the data.
    """
    df = pd.read_parquet(parquet_path, columns=["lap_number"] + TELEMETRY_CHANNELS)
    lap_df = df[df["lap_number"] == lap_number].drop(columns=["lap_number"])

    if lap_df.empty:
        raise ValueError(f"Lap {lap_number} not found in telemetry data")

    # Downsample if needed
    if max_samples > 0 and len(lap_df) > max_samples:
        indices = np.linspace(0, len(lap_df) - 1, max_samples, dtype=int)
        lap_df = lap_df.iloc[indices]

    channels = LapTelemetryChannels(
        normalized_position=lap_df["normalized_position"].tolist(),
        throttle=lap_df["throttle"].tolist(),
        brake=lap_df["brake"].tolist(),
        steering=lap_df["steering"].tolist(),
        speed_kmh=lap_df["speed_kmh"].tolist(),
        gear=lap_df["gear"].tolist(),
    )

    return LapTelemetryResponse(
        session_id=session_id,
        lap_number=lap_number,
        sample_count=len(lap_df),
        channels=channels,
    )
