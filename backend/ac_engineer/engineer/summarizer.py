"""Compress AnalyzedSession into a compact SessionSummary for LLM consumption."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ac_engineer.knowledge.signals import detect_signals

from .models import (
    CornerIssue,
    LapSummary,
    SessionSummary,
    StintSummary,
)

if TYPE_CHECKING:
    from ac_engineer.analyzer.models import AnalyzedLap, AnalyzedSession
    from ac_engineer.config import ACConfig

logger = logging.getLogger(__name__)

WHEELS = ["fl", "fr", "rl", "rr"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def summarize_session(
    session: AnalyzedSession,
    config: ACConfig,
    *,
    max_corner_issues: int = 5,
) -> SessionSummary:
    """Compress an analyzed session into a compact, token-efficient summary.

    Pure function — does not mutate the input session. Deterministic: same
    input always produces identical output.
    """
    flying_laps = _extract_flying_laps(session)
    best_time = min((l.metrics.timing.lap_time_s for l in flying_laps), default=None)

    lap_summaries = [_build_lap_summary(lap, best_time) for lap in flying_laps]

    # Signals
    try:
        signals = detect_signals(session)
    except Exception:
        signals = []

    # Corner issues
    corner_issues = _extract_corner_issues(flying_laps, max_corner_issues)

    # Stint summaries
    stint_summaries = _build_stint_summaries(session)

    # Session-wide averages
    tyre_temps, tyre_pressures, slip_angles = _compute_session_averages(flying_laps)

    # Consistency stats
    consistency = session.consistency
    best_lap_time_s = consistency.best_lap_time_s if consistency else None
    worst_lap_time_s = consistency.worst_lap_time_s if consistency else None
    lap_time_stddev_s = consistency.lap_time_stddev_s if consistency else None

    # Active setup from last stint
    active_setup_filename = None
    active_setup_parameters = None
    if session.stints:
        last_stint = session.stints[-1]
        active_setup_filename = last_stint.setup_filename

    # Average understeer ratio across all flying lap corners
    avg_understeer = _compute_avg_understeer(flying_laps)

    # Session ID
    meta = session.metadata
    session_id = meta.csv_filename.replace(".csv", "") if meta.csv_filename else "unknown"

    return SessionSummary(
        session_id=session_id,
        car_name=meta.car_name,
        track_name=meta.track_name,
        track_config=meta.track_config or None,
        recorded_at=meta.session_start,
        total_lap_count=len(session.laps),
        flying_lap_count=len(flying_laps),
        best_lap_time_s=best_lap_time_s,
        worst_lap_time_s=worst_lap_time_s,
        lap_time_stddev_s=lap_time_stddev_s,
        avg_understeer_ratio=avg_understeer,
        active_setup_filename=active_setup_filename,
        active_setup_parameters=active_setup_parameters,
        laps=lap_summaries,
        signals=signals,
        corner_issues=corner_issues,
        stints=stint_summaries,
        tyre_temp_averages=tyre_temps,
        tyre_pressure_averages=tyre_pressures,
        slip_angle_averages=slip_angles,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_flying_laps(session: AnalyzedSession) -> list[AnalyzedLap]:
    """Filter to only flying laps."""
    return [lap for lap in session.laps if lap.classification == "flying"]


def _build_lap_summary(lap: AnalyzedLap, best_time: float | None) -> LapSummary:
    """Build a compact LapSummary from an AnalyzedLap."""
    t = lap.metrics.timing.lap_time_s
    gap = round(t - best_time, 4) if best_time is not None else 0.0
    is_best = gap == 0.0

    # Tyre temp average: mean of 4 wheel core temps
    tyre_temp_avg = _mean_tyre_temp(lap)

    # Understeer ratio average across corners
    understeer_avg = _mean_understeer(lap)

    return LapSummary(
        lap_number=lap.lap_number,
        lap_time_s=t,
        gap_to_best_s=gap,
        is_best=is_best,
        tyre_temp_avg_c=tyre_temp_avg,
        understeer_ratio_avg=understeer_avg,
        peak_lat_g=lap.metrics.grip.peak_lat_g if lap.metrics.grip else None,
        peak_speed_kmh=lap.metrics.speed.max_speed if lap.metrics.speed else None,
    )


def _mean_tyre_temp(lap: AnalyzedLap) -> float | None:
    """Mean of 4 wheel core temps, or None if no data."""
    try:
        temps = lap.metrics.tyres.temps_avg
        if not temps:
            return None
        values = [temps[w].core for w in WHEELS if w in temps]
        return round(sum(values) / len(values), 2) if values else None
    except (AttributeError, TypeError, KeyError):
        return None


def _mean_understeer(lap: AnalyzedLap) -> float | None:
    """Mean understeer_ratio across corners."""
    if not lap.corners:
        return None
    ratios = []
    for c in lap.corners:
        try:
            ratios.append(c.grip.understeer_ratio)
        except (AttributeError, TypeError):
            pass
    return round(sum(ratios) / len(ratios), 4) if ratios else None


def _compute_avg_understeer(flying_laps: list[AnalyzedLap]) -> float | None:
    """Session-wide average understeer ratio from all corners in flying laps."""
    ratios = []
    for lap in flying_laps:
        for c in lap.corners:
            try:
                ratios.append(c.grip.understeer_ratio)
            except (AttributeError, TypeError):
                pass
    return round(sum(ratios) / len(ratios), 4) if ratios else None


def _extract_corner_issues(
    flying_laps: list[AnalyzedLap],
    max_issues: int,
) -> list[CornerIssue]:
    """Extract corner issues sorted by severity, truncated to max_issues."""
    issues: list[CornerIssue] = []

    for lap in flying_laps:
        for corner in lap.corners:
            try:
                ur = corner.grip.understeer_ratio
            except (AttributeError, TypeError):
                continue

            deviation = abs(ur - 1.0)
            if deviation < 0.1:
                continue  # Not significant enough

            # Determine issue type and severity
            if ur > 1.0:
                issue_type = "understeer"
            else:
                issue_type = "oversteer"

            if deviation > 0.3:
                severity = "high"
            elif deviation > 0.15:
                severity = "medium"
            else:
                severity = "low"

            # Apex speed loss estimate
            try:
                perf = corner.performance
                apex_loss = None
                if perf.entry_speed_kmh and perf.apex_speed_kmh:
                    apex_loss = round(
                        (1 - perf.apex_speed_kmh / perf.entry_speed_kmh) * 100, 1
                    )
            except (AttributeError, TypeError):
                apex_loss = None

            avg_lat_g = None
            try:
                avg_lat_g = corner.grip.avg_lat_g
            except (AttributeError, TypeError):
                pass

            desc = (
                f"Corner {corner.corner_number}: {issue_type} "
                f"(ratio={ur:.2f}, deviation={deviation:.2f})"
            )

            issues.append(CornerIssue(
                corner_number=corner.corner_number,
                issue_type=issue_type,
                severity=severity,
                understeer_ratio=ur,
                apex_speed_loss_pct=apex_loss,
                avg_lat_g=avg_lat_g,
                description=desc,
            ))

    # Sort by severity (high > medium > low), then by deviation magnitude desc
    severity_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda ci: (
        severity_order.get(ci.severity, 3),
        -(abs((ci.understeer_ratio or 1.0) - 1.0)),
    ))

    return issues[:max_issues]


def _build_stint_summaries(session: AnalyzedSession) -> list[StintSummary]:
    """Build stint summaries from session stints and comparisons."""
    # Build lookup for comparisons keyed by stint_b_index
    comparison_map: dict[int, list[str]] = {}
    for comp in session.stint_comparisons:
        changes = []
        for delta in comp.setup_changes:
            changes.append(f"{delta.section}.{delta.name}: {delta.value_a} -> {delta.value_b}")
        comparison_map[comp.stint_b_index] = changes

    summaries = []
    for stint in session.stints:
        # Derive trend from slope
        slope = None
        tyre_slope = None
        if stint.trends:
            slope = stint.trends.lap_time_slope
            # Average tyre temp slope across wheels
            if stint.trends.tyre_temp_slope:
                slopes = list(stint.trends.tyre_temp_slope.values())
                tyre_slope = round(sum(slopes) / len(slopes), 4) if slopes else None

        trend = _slope_to_trend(slope)

        summaries.append(StintSummary(
            stint_index=stint.stint_index,
            flying_lap_count=stint.flying_lap_count,
            lap_time_mean_s=stint.aggregated.lap_time_mean_s if stint.aggregated else None,
            lap_time_stddev_s=stint.aggregated.lap_time_stddev_s if stint.aggregated else None,
            lap_time_trend=trend,
            lap_time_slope_s_per_lap=slope,
            tyre_temp_slope_c_per_lap=tyre_slope,
            setup_filename=stint.setup_filename,
            setup_changes_from_prev=comparison_map.get(stint.stint_index, []),
        ))

    return summaries


def _slope_to_trend(slope: float | None) -> str:
    """Convert a lap time slope to a trend label."""
    if slope is None:
        return "stable"
    if slope < 0:
        return "improving"
    if slope > 0.05:
        return "degrading"
    return "stable"


def _compute_session_averages(
    flying_laps: list[AnalyzedLap],
) -> tuple[dict[str, float] | None, dict[str, float] | None, dict[str, float] | None]:
    """Compute session-wide per-wheel averages for temps, pressures, slip angles."""
    if not flying_laps:
        return None, None, None

    temp_sums: dict[str, list[float]] = {w: [] for w in WHEELS}
    pressure_sums: dict[str, list[float]] = {w: [] for w in WHEELS}
    slip_sums: dict[str, list[float]] = {w: [] for w in WHEELS}

    for lap in flying_laps:
        try:
            temps = lap.metrics.tyres.temps_avg
            for w in WHEELS:
                if w in temps:
                    temp_sums[w].append(temps[w].core)
        except (AttributeError, TypeError, KeyError):
            pass

        try:
            pressures = lap.metrics.tyres.pressure_avg
            for w in WHEELS:
                if w in pressures:
                    pressure_sums[w].append(pressures[w])
        except (AttributeError, TypeError, KeyError):
            pass

        try:
            slips = lap.metrics.grip.slip_angle_avg
            for w in WHEELS:
                if w in slips:
                    slip_sums[w].append(slips[w])
        except (AttributeError, TypeError, KeyError):
            pass

    def _avg(d: dict[str, list[float]]) -> dict[str, float] | None:
        result = {}
        for w, vals in d.items():
            if vals:
                result[w] = round(sum(vals) / len(vals), 2)
        return result if result else None

    return _avg(temp_sums), _avg(pressure_sums), _avg(slip_sums)
