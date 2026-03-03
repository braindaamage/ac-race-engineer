"""Lap segmentation and classification logic.

Splits a session DataFrame by lap_count transitions and classifies each
lap segment using the 5-rule priority state machine.
"""

from __future__ import annotations

import pandas as pd

from ac_engineer.parser.models import LapClassification, ParserError


def segment_laps(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Split session DataFrame into per-lap DataFrames grouped by lap_count.

    Groups rows by the value of the ``lap_count`` column in temporal order.
    The first group contains all rows with the initial lap_count value, the
    second group all rows where lap_count incremented once, and so on.

    Args:
        df: Full session DataFrame with all 82 channels. Must contain a
            ``lap_count`` column.

    Returns:
        List of DataFrames, one per unique consecutive lap_count value,
        preserving temporal order. Returns an empty list if df is empty.

    Raises:
        ParserError: If the ``lap_count`` column is missing from df.
    """
    if "lap_count" not in df.columns:
        raise ParserError("lap_count column missing from session DataFrame")

    if df.empty:
        return []

    segments: list[pd.DataFrame] = []
    current_value = df["lap_count"].iloc[0]
    start_idx = 0

    for i in range(1, len(df)):
        val = df["lap_count"].iloc[i]
        if val != current_value:
            segments.append(df.iloc[start_idx:i].reset_index(drop=True))
            current_value = val
            start_idx = i

    # Always append the final (possibly partial) group
    segments.append(df.iloc[start_idx:].reset_index(drop=True))
    return segments


def classify_lap(
    lap_df: pd.DataFrame,
    is_first: bool,
    is_last: bool,
) -> tuple[LapClassification, bool]:
    """Classify a single lap segment using the 5-rule priority state machine.

    Rules are evaluated in priority order:
    1. outlap   — first sample in_pit_lane==1 AND last sample in_pit_lane==0
    2. inlap    — in_pit_lane transitions 0→1 within the lap, or lap ends in pits
    3. incomplete — no closing lap_count transition (is_last==True)
    4. invalid  — any sample has lap_invalid==1
    5. flying   — none of the above

    The ``is_invalid`` flag is set independently: True whenever any sample has
    ``lap_invalid==1``, regardless of the classification result.

    Args:
        lap_df: DataFrame for one lap segment (rows for a single lap_count value).
        is_first: True if this is the first lap group in the session.
        is_last: True if this is the last lap group (no closing transition).

    Returns:
        Tuple of (LapClassification, is_invalid: bool).
    """
    if lap_df.empty:
        return ("incomplete", False)

    # Compute is_invalid independently
    is_invalid = False
    if "lap_invalid" in lap_df.columns:
        is_invalid = bool((lap_df["lap_invalid"] == 1).any())

    # Rule 1: outlap
    if "in_pit_lane" in lap_df.columns:
        pit_series = lap_df["in_pit_lane"]
        first_in_pit = pit_series.iloc[0] == 1
        last_in_pit = pit_series.iloc[-1] == 1

        if first_in_pit and not last_in_pit:
            return ("outlap", is_invalid)

        # Rule 2: inlap — last sample in pits, or any 0→1 transition mid-lap
        has_pit_entry = bool(((pit_series.shift(1) == 0) & (pit_series == 1)).any())
        if last_in_pit or has_pit_entry:
            return ("inlap", is_invalid)

    # Rule 3: incomplete — final partial lap
    if is_last:
        return ("incomplete", is_invalid)

    # Rule 4: invalid — AC flagged lap_invalid
    if is_invalid:
        return ("invalid", is_invalid)

    # Rule 5: flying
    return ("flying", is_invalid)
