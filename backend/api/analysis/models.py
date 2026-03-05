"""API response models for analysis endpoints."""

from __future__ import annotations

from pydantic import BaseModel

from ac_engineer.analyzer.models import (
    ConsistencyMetrics,
    CornerMetrics,
    LapMetrics,
    StintComparison,
    StintMetrics,
)


class ProcessResponse(BaseModel):
    """Response for POST /sessions/{session_id}/process."""

    job_id: str
    session_id: str


class LapSummary(BaseModel):
    """Summary of one lap for the lap list endpoint."""

    lap_number: int
    classification: str
    is_invalid: bool
    lap_time_s: float
    tyre_temps_avg: dict[str, float]
    peak_lat_g: float
    peak_lon_g: float
    full_throttle_pct: float
    braking_pct: float


class LapListResponse(BaseModel):
    """Response for GET /sessions/{session_id}/laps."""

    session_id: str
    lap_count: int
    laps: list[LapSummary]


class LapDetailResponse(BaseModel):
    """Response for GET /sessions/{session_id}/laps/{lap_number}."""

    session_id: str
    lap_number: int
    classification: str
    is_invalid: bool
    metrics: LapMetrics


class AggregatedCorner(BaseModel):
    """Aggregated metrics for one corner across flying laps."""

    corner_number: int
    sample_count: int
    avg_apex_speed_kmh: float
    avg_entry_speed_kmh: float
    avg_exit_speed_kmh: float
    avg_duration_s: float
    avg_understeer_ratio: float | None = None
    avg_trail_braking_intensity: float
    avg_peak_lat_g: float


class CornerListResponse(BaseModel):
    """Response for GET /sessions/{session_id}/corners."""

    session_id: str
    corner_count: int
    corners: list[AggregatedCorner]


class CornerLapEntry(BaseModel):
    """One lap's metrics for a specific corner."""

    lap_number: int
    metrics: CornerMetrics


class CornerDetailResponse(BaseModel):
    """Response for GET /sessions/{session_id}/corners/{corner_number}."""

    session_id: str
    corner_number: int
    laps: list[CornerLapEntry]


class StintListResponse(BaseModel):
    """Response for GET /sessions/{session_id}/stints."""

    session_id: str
    stint_count: int
    stints: list[StintMetrics]


class StintComparisonResponse(BaseModel):
    """Response for GET /sessions/{session_id}/compare."""

    session_id: str
    comparison: StintComparison


class ConsistencyResponse(BaseModel):
    """Response for GET /sessions/{session_id}/consistency."""

    session_id: str
    consistency: ConsistencyMetrics
