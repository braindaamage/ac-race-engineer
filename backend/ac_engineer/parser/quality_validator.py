"""Data quality validation for lap segments.

Detects time-series gaps, position jumps, prolonged zero-speed events,
incomplete laps, and duplicate timestamps. All thresholds are module-level
constants configurable at import time for testing.
"""

from __future__ import annotations

import pandas as pd

from ac_engineer.parser.models import QualityWarning

# ---------------------------------------------------------------------------
# Configurable threshold constants
# ---------------------------------------------------------------------------

TIME_GAP_THRESHOLD: float = 0.5        # seconds between consecutive samples
POSITION_JUMP_THRESHOLD: float = 0.05  # normalized position units in one sample
ZERO_SPEED_THRESHOLD: float = 1.0      # km/h below which car is considered stopped
ZERO_SPEED_DURATION: float = 3.0       # seconds of zero-speed to trigger warning
ZERO_SPEED_MIN: float = 0.10           # minimum normalized_position for zero-speed check
ZERO_SPEED_MAX: float = 0.90           # maximum normalized_position for zero-speed check


def validate_lap(
    lap_df: pd.DataFrame,
    sample_rate: float,
    is_last: bool = False,
) -> list[QualityWarning]:
    """Detect all data quality issues in a single lap DataFrame.

    Checks all 5 quality conditions using module-level threshold constants.
    Does not modify the DataFrame or drop samples.

    Args:
        lap_df: DataFrame for one lap (rows for a single lap_count value).
        sample_rate: Session sample rate in Hz (used for zero-speed duration).
        is_last: If True, automatically adds an ``incomplete`` warning.

    Returns:
        List of QualityWarning objects. Returns empty list for a clean lap.
    """
    warnings: list[QualityWarning] = []

    if lap_df.empty:
        if is_last:
            warnings.append(QualityWarning(
                warning_type="incomplete",
                normalized_position=0.0,
                description="Lap segment has no closing lap count transition (empty segment).",
            ))
        return warnings

    # -----------------------------------------------------------------------
    # 1. Time-series gap: consecutive samples more than TIME_GAP_THRESHOLD apart
    # -----------------------------------------------------------------------
    if "timestamp" in lap_df.columns:
        ts = lap_df["timestamp"]
        diffs = ts.diff()
        gap_mask = diffs > TIME_GAP_THRESHOLD
        if gap_mask.any():
            first_gap_idx = int(gap_mask.idxmax())
            norm_pos = _norm_at(lap_df, first_gap_idx)
            gap_seconds = float(diffs.loc[first_gap_idx])
            warnings.append(QualityWarning(
                warning_type="time_series_gap",
                normalized_position=norm_pos,
                description=f"Time gap of {gap_seconds:.2f}s detected between consecutive samples "
                            f"(threshold: {TIME_GAP_THRESHOLD}s).",
            ))

    # -----------------------------------------------------------------------
    # 2. Position jump: normalized_position changed > POSITION_JUMP_THRESHOLD
    #    Wrap-corrected: S/F crossing (0.999 → 0.001) produces a raw diff of
    #    ~-0.999. Any diff < -0.5 is a forward S/F wrap-around, not a real
    #    jump — correct it to diff + 1.0 (actual movement ≈ +0.001).
    # -----------------------------------------------------------------------
    if "normalized_position" in lap_df.columns:
        pos = lap_df["normalized_position"]
        raw_diffs = pos.diff()
        # Apply wrap correction: forward S/F crossing has diff < -0.5
        corrected_diffs = raw_diffs.copy()
        corrected_diffs[raw_diffs < -0.5] = raw_diffs[raw_diffs < -0.5] + 1.0
        jumps = corrected_diffs.abs()
        jump_mask = jumps > POSITION_JUMP_THRESHOLD
        if jump_mask.any():
            first_jump_idx = int(jump_mask.idxmax())
            norm_pos = _norm_at(lap_df, first_jump_idx)
            jump_size = float(jumps.loc[first_jump_idx])
            warnings.append(QualityWarning(
                warning_type="position_jump",
                normalized_position=norm_pos,
                description=f"Normalized position jumped {jump_size:.3f} in one sample "
                            f"(threshold: {POSITION_JUMP_THRESHOLD}).",
            ))

    # -----------------------------------------------------------------------
    # 3. Zero-speed mid-lap: speed ≤ ZERO_SPEED_THRESHOLD for > ZERO_SPEED_DURATION
    #    only between ZERO_SPEED_MIN and ZERO_SPEED_MAX track positions
    # -----------------------------------------------------------------------
    if "speed_kmh" in lap_df.columns and "normalized_position" in lap_df.columns:
        pos = lap_df["normalized_position"]
        speed = lap_df["speed_kmh"]
        in_window = (pos >= ZERO_SPEED_MIN) & (pos <= ZERO_SPEED_MAX)
        stopped = (speed <= ZERO_SPEED_THRESHOLD) & in_window

        if stopped.any():
            min_samples = max(1, int(sample_rate * ZERO_SPEED_DURATION))
            # Find contiguous stopped runs
            run_len = 0
            run_start_idx = None
            for i in range(len(lap_df)):
                idx = lap_df.index[i]
                if stopped.loc[idx]:
                    if run_start_idx is None:
                        run_start_idx = idx
                    run_len += 1
                    if run_len >= min_samples:
                        norm_pos = _norm_at(lap_df, run_start_idx)
                        duration = run_len / sample_rate
                        warnings.append(QualityWarning(
                            warning_type="zero_speed_mid_lap",
                            normalized_position=norm_pos,
                            description=f"Speed ≤ {ZERO_SPEED_THRESHOLD} km/h for {duration:.1f}s "
                                        f"between {ZERO_SPEED_MIN}–{ZERO_SPEED_MAX} track position "
                                        f"(threshold: {ZERO_SPEED_DURATION}s).",
                        ))
                        break
                else:
                    run_len = 0
                    run_start_idx = None

    # -----------------------------------------------------------------------
    # 4. Duplicate timestamp: consecutive samples share the same timestamp
    # -----------------------------------------------------------------------
    if "timestamp" in lap_df.columns:
        ts = lap_df["timestamp"]
        dup_mask = ts.diff() == 0
        if dup_mask.any():
            first_dup_idx = int(dup_mask.idxmax())
            norm_pos = _norm_at(lap_df, first_dup_idx)
            warnings.append(QualityWarning(
                warning_type="duplicate_timestamp",
                normalized_position=norm_pos,
                description="Consecutive samples share the same timestamp (buffer flush artifact).",
            ))

    # -----------------------------------------------------------------------
    # 5. Incomplete: no closing lap_count transition (is_last=True)
    # -----------------------------------------------------------------------
    if is_last:
        norm_pos = _norm_at(lap_df, lap_df.index[-1])
        warnings.append(QualityWarning(
            warning_type="incomplete",
            normalized_position=norm_pos,
            description="Lap segment has no closing lap count transition (session ended mid-lap).",
        ))

    return warnings


def _norm_at(lap_df: pd.DataFrame, idx) -> float:
    """Return the normalized_position value at the given index, or 0.0."""
    if "normalized_position" in lap_df.columns:
        try:
            return float(lap_df.loc[idx, "normalized_position"])
        except (KeyError, TypeError):
            pass
    return 0.0
