"""Percentile-based corner detection with session-consistent numbering.

Uses lateral G-force and steering angle to detect cornering windows,
then maps detected corners to a reference lap for consistent numbering
across all laps in a session.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ac_engineer.parser.models import CornerSegment


def compute_session_thresholds(
    session_df: pd.DataFrame,
    sample_rate: float,
) -> dict:
    """Compute session-wide cornering detection thresholds.

    Computes 80th-percentile of absolute lateral G and 70th-percentile of
    absolute steering across the entire session (not per-lap) for stable,
    consistent thresholds unaffected by individual lap data quality.

    Args:
        session_df: Full session DataFrame (all laps concatenated).
        sample_rate: Session sample rate in Hz.

    Returns:
        Dict with keys ``g_threshold`` (float), ``steer_threshold`` (float),
        and ``reduced_mode`` (bool — True if g_lat is all-NaN).
    """
    reduced_mode = False
    g_threshold = 0.0
    steer_threshold = 0.0

    if "g_lat" in session_df.columns:
        abs_g = session_df["g_lat"].abs()
        if abs_g.notna().any():
            g_threshold = float(np.nanpercentile(abs_g.dropna().values, 80))
        else:
            reduced_mode = True

    if "steering" in session_df.columns:
        abs_steer = session_df["steering"].abs()
        if abs_steer.notna().any():
            steer_threshold = float(np.nanpercentile(abs_steer.dropna().values, 70))

    return {
        "g_threshold": g_threshold,
        "steer_threshold": steer_threshold,
        "reduced_mode": reduced_mode,
    }


def build_reference_map(
    lap_df: pd.DataFrame,
    thresholds: dict,
    sample_rate: float,
) -> list[float]:
    """Build the session corner reference map from a reference lap.

    Detects corners in the reference lap and returns their apex
    normalized_position values as the track corner map for the session.

    Args:
        lap_df: DataFrame for the reference lap.
        thresholds: Dict from compute_session_thresholds.
        sample_rate: Session sample rate in Hz.

    Returns:
        Ordered list of apex normalized_position values (one per corner).
    """
    corners = _detect_cornering_runs(lap_df, thresholds, sample_rate)
    return [c["apex_norm_pos"] for c in corners]


def detect_corners(
    lap_df: pd.DataFrame,
    reference_apexes: list[float],
    thresholds: dict,
    sample_rate: float,
) -> list[CornerSegment]:
    """Detect corners in a lap and align them to the session reference map.

    Runs the cornering-sample detection, merging, and filtering algorithm,
    then matches each detected corner to the nearest reference apex (within
    0.05 tolerance). Assigns session-consistent corner numbers.

    Args:
        lap_df: DataFrame for one lap.
        reference_apexes: Ordered apex positions from the reference lap.
        thresholds: Dict from compute_session_thresholds.
        sample_rate: Session sample rate in Hz.

    Returns:
        List of CornerSegment objects ordered by corner_number.
        Unmatched detections are discarded.
    """
    if not reference_apexes:
        return []

    detected_runs = _detect_cornering_runs(lap_df, thresholds, sample_rate)
    if not detected_runs:
        return []

    segments: list[CornerSegment] = []
    used_refs: set[int] = set()

    for run in detected_runs:
        apex_pos = run["apex_norm_pos"]
        # Find nearest reference apex
        best_ref_idx = -1
        best_dist = float("inf")
        for ref_idx, ref_pos in enumerate(reference_apexes):
            dist = abs(apex_pos - ref_pos)
            if dist < best_dist and ref_idx not in used_refs:
                best_dist = dist
                best_ref_idx = ref_idx

        # Only accept match within 0.05 tolerance
        if best_dist > 0.05 or best_ref_idx < 0:
            continue

        used_refs.add(best_ref_idx)
        corner_number = best_ref_idx + 1  # 1-indexed

        # Extract speed and g values at entry/apex/exit
        speed_col = "speed_kmh" if "speed_kmh" in lap_df.columns else None
        g_col = "g_lat" if "g_lat" in lap_df.columns else None

        entry_idx = run["entry_idx"]
        apex_idx = run["apex_idx"]
        exit_idx = run["exit_idx"]

        def _speed(idx: int) -> float:
            if speed_col and not lap_df[speed_col].isna().all():
                return float(lap_df[speed_col].iloc[idx])
            return 0.0

        def _norm(idx: int) -> float:
            return float(lap_df["normalized_position"].iloc[idx]) if "normalized_position" in lap_df.columns else 0.0

        max_g = 0.0
        if g_col:
            run_g = lap_df[g_col].iloc[entry_idx: exit_idx + 1].abs()
            if run_g.notna().any():
                max_g = float(run_g.max())

        segments.append(CornerSegment(
            corner_number=corner_number,
            entry_norm_pos=_norm(entry_idx),
            apex_norm_pos=_norm(apex_idx),
            exit_norm_pos=_norm(exit_idx),
            apex_speed_kmh=_speed(apex_idx),
            max_lat_g=max_g,
            entry_speed_kmh=_speed(entry_idx),
            exit_speed_kmh=_speed(exit_idx),
        ))

    return sorted(segments, key=lambda c: c.corner_number)


# ---------------------------------------------------------------------------
# Internal: cornering run detection
# ---------------------------------------------------------------------------

def _detect_cornering_runs(
    lap_df: pd.DataFrame,
    thresholds: dict,
    sample_rate: float,
) -> list[dict]:
    """Core cornering-sample detection and run-merging algorithm.

    Returns a list of dicts with keys: entry_idx, apex_idx, exit_idx,
    apex_norm_pos, g_lat_sign (for chicane detection).
    """
    if lap_df.empty or "normalized_position" not in lap_df.columns:
        return []

    n = len(lap_df)
    g_threshold = thresholds.get("g_threshold", 0.0)
    steer_threshold = thresholds.get("steer_threshold", 0.0)
    reduced_mode = thresholds.get("reduced_mode", False)

    # Mark cornering samples
    cornering = np.zeros(n, dtype=bool)

    has_g = "g_lat" in lap_df.columns and not lap_df["g_lat"].isna().all()
    has_steer = "steering" in lap_df.columns and not lap_df["steering"].isna().all()

    if not reduced_mode and has_g and g_threshold > 0:
        abs_g = lap_df["g_lat"].abs().fillna(0).values
        g_mask = abs_g > g_threshold * 0.6
        if has_steer and steer_threshold > 0:
            abs_steer = lap_df["steering"].abs().fillna(0).values
            steer_mask = abs_steer > steer_threshold * 0.4
            cornering = g_mask & steer_mask
        else:
            cornering = g_mask
    elif has_steer and steer_threshold > 0:
        # Reduced mode: steering-only fallback
        abs_steer = lap_df["steering"].abs().fillna(0).values
        cornering = abs_steer > steer_threshold * 0.4
    else:
        return []

    # Get g_lat sign for chicane separation
    g_lat_values = lap_df["g_lat"].fillna(0).values if "g_lat" in lap_df.columns else np.zeros(n)

    # Find contiguous runs of cornering samples
    runs: list[tuple[int, int]] = []
    in_run = False
    run_start = 0
    for i in range(n):
        if cornering[i] and not in_run:
            in_run = True
            run_start = i
        elif not cornering[i] and in_run:
            in_run = False
            runs.append((run_start, i - 1))
    if in_run:
        runs.append((run_start, n - 1))

    if not runs:
        return []

    # Merge runs separated by < sample_rate * 0.5 samples (same sign only).
    # 0.5s gap allows same-direction corner sections split by brief G-force dips.
    min_gap = max(1, int(sample_rate * 0.5))
    merged: list[tuple[int, int]] = [runs[0]]
    for start, end in runs[1:]:
        prev_start, prev_end = merged[-1]
        gap = start - prev_end - 1
        # Determine sign of each run
        prev_sign = np.sign(np.nanmean(g_lat_values[prev_start: prev_end + 1]))
        curr_sign = np.sign(np.nanmean(g_lat_values[start: end + 1]))
        # Only merge if same sign and within gap threshold
        if gap < min_gap and prev_sign == curr_sign:
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))

    # Discard runs shorter than sample_rate * 0.75 samples
    min_duration = max(2, int(sample_rate * 0.75))
    valid_runs = [(s, e) for s, e in merged if (e - s + 1) >= min_duration]

    # Build result dicts
    speed_col = "speed_kmh" if "speed_kmh" in lap_df.columns else None
    norm_col = "normalized_position"

    results = []
    for start, end in valid_runs:
        # Apex = index of minimum speed in the run
        if speed_col and not lap_df[speed_col].iloc[start: end + 1].isna().all():
            apex_idx = int(lap_df[speed_col].iloc[start: end + 1].idxmin())
        else:
            apex_idx = (start + end) // 2

        apex_norm = float(lap_df[norm_col].iloc[apex_idx])
        g_sign = float(np.sign(np.nanmean(g_lat_values[start: end + 1])))

        results.append({
            "entry_idx": start,
            "apex_idx": apex_idx,
            "exit_idx": end,
            "apex_norm_pos": apex_norm,
            "g_lat_sign": g_sign,
        })

    return results
