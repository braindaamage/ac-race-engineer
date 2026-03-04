"""Pydantic v2 models for the telemetry analyzer."""

from __future__ import annotations

from pydantic import BaseModel

from ac_engineer.parser.models import LapClassification, SessionMetadata


# ---------------------------------------------------------------------------
# Lap-level metric groups
# ---------------------------------------------------------------------------


class WheelTempZones(BaseModel):
    """Temperature zones for one wheel."""

    core: float
    inner: float
    mid: float
    outer: float


class TimingMetrics(BaseModel):
    """Lap timing data."""

    lap_time_s: float
    sector_times_s: list[float] | None = None


class TyreMetrics(BaseModel):
    """Per-wheel tyre data."""

    temps_avg: dict[str, WheelTempZones]
    temps_peak: dict[str, WheelTempZones]
    pressure_avg: dict[str, float]
    temp_spread: dict[str, float]
    front_rear_balance: float
    wear_rate: dict[str, float] | None = None


class GripMetrics(BaseModel):
    """Slip angle/ratio and G-force data."""

    slip_angle_avg: dict[str, float]
    slip_angle_peak: dict[str, float]
    slip_ratio_avg: dict[str, float]
    slip_ratio_peak: dict[str, float]
    peak_lat_g: float
    peak_lon_g: float


class DriverInputMetrics(BaseModel):
    """Throttle/brake/steering statistics."""

    full_throttle_pct: float
    partial_throttle_pct: float
    off_throttle_pct: float
    braking_pct: float
    avg_steering_angle: float
    gear_distribution: dict[int, float]


class SpeedMetrics(BaseModel):
    """Speed statistics."""

    max_speed: float
    min_speed: float
    avg_speed: float


class FuelMetrics(BaseModel):
    """Fuel consumption data."""

    fuel_start: float
    fuel_end: float
    consumption: float


class SuspensionMetrics(BaseModel):
    """Per-wheel suspension travel data."""

    travel_avg: dict[str, float]
    travel_peak: dict[str, float]
    travel_range: dict[str, float]


class LapMetrics(BaseModel):
    """Composite of all lap-level metric groups."""

    timing: TimingMetrics
    tyres: TyreMetrics
    grip: GripMetrics
    driver_inputs: DriverInputMetrics
    speed: SpeedMetrics
    fuel: FuelMetrics | None = None
    suspension: SuspensionMetrics


# ---------------------------------------------------------------------------
# Corner-level metric groups
# ---------------------------------------------------------------------------


class CornerPerformance(BaseModel):
    """Speeds and duration for one corner."""

    entry_speed_kmh: float
    apex_speed_kmh: float
    exit_speed_kmh: float
    duration_s: float


class CornerGrip(BaseModel):
    """G-forces and balance for one corner."""

    peak_lat_g: float
    avg_lat_g: float
    understeer_ratio: float | None = None


class CornerTechnique(BaseModel):
    """Braking/throttle technique for one corner."""

    brake_point_norm: float | None = None
    throttle_on_norm: float | None = None
    trail_braking_intensity: float = 0.0


class CornerLoading(BaseModel):
    """Peak wheel loads during one corner."""

    peak_wheel_load: dict[str, float]


class CornerMetrics(BaseModel):
    """Per-corner-per-lap metrics."""

    corner_number: int
    performance: CornerPerformance
    grip: CornerGrip
    technique: CornerTechnique
    loading: CornerLoading | None = None


# ---------------------------------------------------------------------------
# Analyzed lap
# ---------------------------------------------------------------------------


class AnalyzedLap(BaseModel):
    """Per-lap wrapper linking lap identity to computed metrics."""

    lap_number: int
    classification: LapClassification
    is_invalid: bool
    metrics: LapMetrics
    corners: list[CornerMetrics] = []


# ---------------------------------------------------------------------------
# Stint-level models
# ---------------------------------------------------------------------------


class AggregatedStintMetrics(BaseModel):
    """Mean/stddev across flying laps in a stint."""

    lap_time_mean_s: float | None = None
    lap_time_stddev_s: float | None = None
    tyre_temp_avg: dict[str, float] = {}
    slip_angle_avg: dict[str, float] = {}
    slip_ratio_avg: dict[str, float] = {}
    peak_lat_g_avg: float | None = None


class StintTrends(BaseModel):
    """Linear trends within a stint."""

    lap_time_slope: float
    tyre_temp_slope: dict[str, float]
    fuel_consumption_slope: float | None = None


class StintMetrics(BaseModel):
    """One stint's metrics."""

    stint_index: int
    setup_filename: str | None = None
    lap_numbers: list[int]
    flying_lap_count: int
    aggregated: AggregatedStintMetrics
    trends: StintTrends | None = None


# ---------------------------------------------------------------------------
# Stint comparison
# ---------------------------------------------------------------------------


class SetupParameterDelta(BaseModel):
    """One parameter that changed between stints."""

    section: str
    name: str
    value_a: float | str
    value_b: float | str


class MetricDeltas(BaseModel):
    """Aggregated metric differences (B - A)."""

    lap_time_delta_s: float | None = None
    tyre_temp_delta: dict[str, float] = {}
    slip_angle_delta: dict[str, float] = {}
    slip_ratio_delta: dict[str, float] = {}
    peak_lat_g_delta: float | None = None


class StintComparison(BaseModel):
    """Comparison between two adjacent stints."""

    stint_a_index: int
    stint_b_index: int
    setup_changes: list[SetupParameterDelta] = []
    metric_deltas: MetricDeltas


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------


class CornerConsistency(BaseModel):
    """Per-corner variance data across laps."""

    corner_number: int
    apex_speed_variance: float | None = None
    apex_speed_stddev: float | None = None
    brake_point_variance: float | None = None
    sample_count: int


class ConsistencyMetrics(BaseModel):
    """Session-wide consistency metrics."""

    flying_lap_count: int
    lap_time_stddev_s: float
    best_lap_time_s: float
    worst_lap_time_s: float
    lap_time_trend_slope: float | None = None
    corner_consistency: list[CornerConsistency] = []


# ---------------------------------------------------------------------------
# Top-level output
# ---------------------------------------------------------------------------


class AnalyzedSession(BaseModel):
    """Top-level output container."""

    metadata: SessionMetadata
    laps: list[AnalyzedLap] = []
    stints: list[StintMetrics] = []
    stint_comparisons: list[StintComparison] = []
    consistency: ConsistencyMetrics | None = None
