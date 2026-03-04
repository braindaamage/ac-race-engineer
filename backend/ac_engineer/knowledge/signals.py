"""Signal detector functions for AnalyzedSession inspection."""

from __future__ import annotations

from ac_engineer.analyzer.models import AnalyzedSession

# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------

UNDERSTEER_THRESHOLD = 1.2
OVERSTEER_THRESHOLD = 0.8
TEMP_SPREAD_THRESHOLD = 12.0  # °C
TEMP_BALANCE_THRESHOLD = 5.0  # °C
LAP_TIME_SLOPE_THRESHOLD = 0.15  # s/lap
SLIP_ANGLE_THRESHOLD = 0.08  # rad
SUSPENSION_TRAVEL_THRESHOLD = 0.95  # fraction of max travel
CONSISTENCY_THRESHOLD = 1.5  # s stddev
BRAKE_BALANCE_UNDERSTEER_THRESHOLD = 1.3
TYRE_TEMP_SLOPE_THRESHOLD = 0.5  # °C/lap


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------


def _check_understeer(session: AnalyzedSession) -> bool:
    """Mean understeer_ratio across flying lap corners > threshold."""
    ratios: list[float] = []
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for corner in lap.corners:
            if corner.grip.understeer_ratio is not None:
                ratios.append(corner.grip.understeer_ratio)
    if not ratios:
        return False
    return sum(ratios) / len(ratios) > UNDERSTEER_THRESHOLD


def _check_oversteer(session: AnalyzedSession) -> bool:
    """Mean understeer_ratio across flying lap corners < oversteer threshold."""
    ratios: list[float] = []
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for corner in lap.corners:
            if corner.grip.understeer_ratio is not None:
                ratios.append(corner.grip.understeer_ratio)
    if not ratios:
        return False
    return sum(ratios) / len(ratios) < OVERSTEER_THRESHOLD


def _check_tyre_temp_spread(session: AnalyzedSession) -> bool:
    """Any wheel's temp_spread > threshold on any flying lap."""
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for spread in lap.metrics.tyres.temp_spread.values():
            if spread > TEMP_SPREAD_THRESHOLD:
                return True
    return False


def _check_tyre_temp_imbalance(session: AnalyzedSession) -> bool:
    """Front-rear balance deviation > threshold on any flying lap."""
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        if abs(lap.metrics.tyres.front_rear_balance) > TEMP_BALANCE_THRESHOLD:
            return True
    return False


def _check_lap_time_degradation(session: AnalyzedSession) -> bool:
    """Positive lap_time_slope > threshold in any stint."""
    for stint in session.stints:
        if stint.trends is not None:
            if stint.trends.lap_time_slope > LAP_TIME_SLOPE_THRESHOLD:
                return True
    return False


def _check_high_slip_angle(session: AnalyzedSession) -> bool:
    """Any wheel's avg slip angle > threshold on any flying lap."""
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for avg in lap.metrics.grip.slip_angle_avg.values():
            if avg > SLIP_ANGLE_THRESHOLD:
                return True
    return False


def _check_suspension_bottoming(session: AnalyzedSession) -> bool:
    """Any wheel's travel_peak near max on any flying lap."""
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for peak in lap.metrics.suspension.travel_peak.values():
            if peak > SUSPENSION_TRAVEL_THRESHOLD:
                return True
    return False


def _check_low_consistency(session: AnalyzedSession) -> bool:
    """Lap time stddev > threshold."""
    if session.consistency is None:
        return False
    return session.consistency.lap_time_stddev_s > CONSISTENCY_THRESHOLD


def _check_brake_balance(session: AnalyzedSession) -> bool:
    """Consistent entry-phase understeer/oversteer indicating brake balance issue."""
    # Check if corner entry behaviour is consistently imbalanced
    entry_ratios: list[float] = []
    for lap in session.laps:
        if lap.classification != "flying" or lap.is_invalid:
            continue
        for corner in lap.corners:
            if corner.grip.understeer_ratio is not None:
                if corner.technique.trail_braking_intensity > 0.3:
                    entry_ratios.append(corner.grip.understeer_ratio)
    if not entry_ratios:
        return False
    mean = sum(entry_ratios) / len(entry_ratios)
    return mean > BRAKE_BALANCE_UNDERSTEER_THRESHOLD or mean < OVERSTEER_THRESHOLD


def _check_tyre_wear(session: AnalyzedSession) -> bool:
    """Positive tyre_temp_slope > threshold in any stint."""
    for stint in session.stints:
        if stint.trends is not None:
            for slope in stint.trends.tyre_temp_slope.values():
                if slope > TYRE_TEMP_SLOPE_THRESHOLD:
                    return True
    return False


# ---------------------------------------------------------------------------
# Signal registry
# ---------------------------------------------------------------------------

_DETECTORS: dict[str, callable] = {
    "high_understeer": _check_understeer,
    "high_oversteer": _check_oversteer,
    "tyre_temp_spread_high": _check_tyre_temp_spread,
    "tyre_temp_imbalance": _check_tyre_temp_imbalance,
    "lap_time_degradation": _check_lap_time_degradation,
    "high_slip_angle": _check_high_slip_angle,
    "suspension_bottoming": _check_suspension_bottoming,
    "low_consistency": _check_low_consistency,
    "brake_balance_issue": _check_brake_balance,
    "tyre_wear_rapid": _check_tyre_wear,
}


def detect_signals(session: AnalyzedSession) -> list[str]:
    """Run all detectors and return list of signal names that fired."""
    fired: list[str] = []
    for name, detector in _DETECTORS.items():
        try:
            if detector(session):
                fired.append(name)
        except (AttributeError, TypeError, KeyError):
            # Gracefully handle None/missing fields
            continue
    return fired
