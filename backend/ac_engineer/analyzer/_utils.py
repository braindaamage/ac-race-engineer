"""Shared helpers: NaN-safe stats, channel extraction, threshold constants."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------

THROTTLE_FULL = 0.95
THROTTLE_ON = 0.05
BRAKE_ON = 0.05
SPEED_PIT_FILTER = 10.0


# ---------------------------------------------------------------------------
# NaN-safe statistics
# ---------------------------------------------------------------------------


def safe_mean(series: pd.Series | np.ndarray) -> float | None:
    """Return nanmean or None if all NaN."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return None
    return float(np.nanmean(arr))


def safe_max(series: pd.Series | np.ndarray) -> float | None:
    """Return nanmax or None if all NaN."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return None
    return float(np.nanmax(arr))


def safe_min(series: pd.Series | np.ndarray) -> float | None:
    """Return nanmin or None if all NaN."""
    arr = np.asarray(series, dtype=float)
    if arr.size == 0 or np.all(np.isnan(arr)):
        return None
    return float(np.nanmin(arr))


# ---------------------------------------------------------------------------
# Channel helpers
# ---------------------------------------------------------------------------


def channel_available(df: pd.DataFrame, column: str) -> bool:
    """True if column exists and has at least one non-NaN value."""
    if column not in df.columns:
        return False
    return bool(df[column].notna().any())


def extract_corner_data(
    df: pd.DataFrame,
    entry_pos: float,
    exit_pos: float,
) -> pd.DataFrame:
    """Filter DataFrame by normalized_position range, handling wrap-around."""
    pos = df["normalized_position"]
    if entry_pos <= exit_pos:
        mask = (pos >= entry_pos) & (pos <= exit_pos)
    else:
        # Wrap-around: corner spans the start/finish line
        mask = (pos >= entry_pos) | (pos <= exit_pos)
    return df.loc[mask].copy()


# ---------------------------------------------------------------------------
# Trend computation
# ---------------------------------------------------------------------------


def compute_trend_slope(values: list[float]) -> float | None:
    """Linear regression slope via scipy.stats.linregress. None if < 2 values."""
    if len(values) < 2:
        return None
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    result = stats.linregress(x, y)
    return float(result.slope)
