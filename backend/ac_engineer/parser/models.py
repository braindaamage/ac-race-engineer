"""Pydantic v2 models for the telemetry parser."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

LapClassification = Literal["flying", "outlap", "inlap", "invalid", "incomplete"]

WarnType = Literal[
    "time_series_gap",
    "position_jump",
    "zero_speed_mid_lap",
    "incomplete",
    "duplicate_timestamp",
]


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class QualityWarning(BaseModel):
    """A data quality issue detected on a specific lap."""

    warning_type: WarnType
    normalized_position: float
    description: str


class SetupParameter(BaseModel):
    """One key-value parameter extracted from a setup .ini file."""

    section: str
    name: str
    value: float | str


class SetupEntry(BaseModel):
    """One setup stint read from setup_history."""

    lap_start: int
    trigger: str
    confidence: str | None = None
    filename: str | None = None
    timestamp: str
    parameters: list[SetupParameter] = []


class CornerSegment(BaseModel):
    """One detected corner within a lap."""

    corner_number: int
    entry_norm_pos: float
    apex_norm_pos: float
    exit_norm_pos: float
    apex_speed_kmh: float
    max_lat_g: float
    entry_speed_kmh: float
    exit_speed_kmh: float


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------


class LapSegment(BaseModel):
    """One lap's worth of telemetry data plus all derived structures."""

    lap_number: int
    classification: LapClassification
    is_invalid: bool = False
    start_timestamp: float
    end_timestamp: float
    start_norm_pos: float
    end_norm_pos: float
    sample_count: int
    data: dict[str, list]
    corners: list[CornerSegment] = []
    active_setup: SetupEntry | None = None
    quality_warnings: list[QualityWarning] = []

    def to_dataframe(self) -> pd.DataFrame:
        """Reconstruct a pandas DataFrame from the data dict."""
        return pd.DataFrame(self.data)


class SessionMetadata(BaseModel):
    """Session-level context from the .meta.json file."""

    car_name: str
    track_name: str
    track_config: str
    track_length_m: float | None = None
    session_type: str
    tyre_compound: str
    driver_name: str
    air_temp_c: float | None = None
    road_temp_c: float | None = None
    session_start: str
    session_end: str | None = None
    laps_completed: int | None = None
    total_samples: int | None = None
    sample_rate_hz: float | None = None
    channels_available: list[str] = []
    channels_unavailable: list[str] = []
    sim_info_available: bool = True
    reduced_mode: bool = False
    csv_filename: str
    app_version: str


class ParsedSession(BaseModel):
    """Top-level container returned by parse_session()."""

    metadata: SessionMetadata
    setups: list[SetupEntry] = []
    laps: list[LapSegment] = []

    @property
    def flying_laps(self) -> list[LapSegment]:
        """Return laps classified as 'flying'."""
        return [lap for lap in self.laps if lap.classification == "flying"]

    def lap_by_number(self, n: int) -> LapSegment | None:
        """Return the lap segment with the given lap number, or None."""
        for lap in self.laps:
            if lap.lap_number == n:
                return lap
        return None


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class ParserError(Exception):
    """Raised for unrecoverable structural errors in session data."""
    pass
