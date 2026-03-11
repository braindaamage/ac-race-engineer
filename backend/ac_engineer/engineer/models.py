"""Pydantic v2 models for the engineer core layer.

Four groups:
- Summary models (LapSummary, CornerIssue, StintSummary, SessionSummary)
- Setup models (ParameterRange, ValidationResult, ChangeOutcome)
- Response models (SetupChange, DriverFeedback, EngineerResponse)
- Agent models (SpecialistResult, AgentDeps)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Summary models (US1)
# ---------------------------------------------------------------------------


class LapSummary(BaseModel):
    """Compact per-lap entry for flying laps."""

    lap_number: int
    lap_time_s: float
    gap_to_best_s: float
    is_best: bool
    tyre_temp_avg_c: float | None = None
    understeer_ratio_avg: float | None = None
    peak_lat_g: float | None = None
    peak_speed_kmh: float | None = None

    @field_validator("gap_to_best_s")
    @classmethod
    def gap_non_negative(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("gap_to_best_s must be >= 0.0")
        return v


class CornerIssue(BaseModel):
    """A prioritized corner-specific problem."""

    corner_number: int
    issue_type: str
    severity: Literal["high", "medium", "low"]
    understeer_ratio: float | None = None
    apex_speed_loss_pct: float | None = None
    avg_lat_g: float | None = None
    description: str


class StintSummary(BaseModel):
    """Per-stint breakdown within the session summary."""

    stint_index: int
    flying_lap_count: int
    lap_time_mean_s: float | None = None
    lap_time_stddev_s: float | None = None
    lap_time_trend: Literal["improving", "degrading", "stable"]
    lap_time_slope_s_per_lap: float | None = None
    tyre_temp_slope_c_per_lap: float | None = None
    setup_filename: str | None = None
    setup_changes_from_prev: list[str] = []


class SessionSummary(BaseModel):
    """Complete compact summary optimized for LLM consumption."""

    session_id: str
    car_name: str
    track_name: str
    track_config: str | None = None
    recorded_at: str | None = None
    total_lap_count: int
    flying_lap_count: int
    best_lap_time_s: float | None = None
    worst_lap_time_s: float | None = None
    lap_time_stddev_s: float | None = None
    avg_understeer_ratio: float | None = None
    active_setup_filename: str | None = None
    active_setup_parameters: dict[str, dict[str, float | str]] | None = None
    laps: list[LapSummary] = []
    signals: list[str] = []
    corner_issues: list[CornerIssue] = []
    stints: list[StintSummary] = []
    tyre_temp_averages: dict[str, float] | None = None
    tyre_pressure_averages: dict[str, float] | None = None
    slip_angle_averages: dict[str, float] | None = None


# ---------------------------------------------------------------------------
# Setup models (US2/US3/US4)
# ---------------------------------------------------------------------------


class ParameterRange(BaseModel):
    """Valid range for a single adjustable setup parameter."""

    section: str
    parameter: str
    min_value: float
    max_value: float
    step: float
    default_value: float | None = None
    show_clicks: int | None = None
    storage_convention: str | None = None

    @field_validator("max_value")
    @classmethod
    def min_le_max(cls, v: float, info) -> float:
        min_val = info.data.get("min_value")
        if min_val is not None and min_val > v:
            raise ValueError(f"min_value ({min_val}) must be <= max_value ({v})")
        return v

    @field_validator("step")
    @classmethod
    def step_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"step must be > 0, got {v}")
        return v


class ValidationResult(BaseModel):
    """Outcome of validating a single proposed setup change."""

    section: str
    parameter: str
    proposed_value: float
    clamped_value: float | None = None
    is_valid: bool
    warning: str | None = None


class ChangeOutcome(BaseModel):
    """Result of applying a single validated change to a setup file."""

    section: str
    parameter: str
    old_value: str
    new_value: str
    status: Literal["applied", "skipped"] = "applied"
    reason: str = ""


# ---------------------------------------------------------------------------
# Engineer response models (Phase 5.3 data containers)
# ---------------------------------------------------------------------------


class SetupChange(BaseModel):
    """A fully described setup modification proposed by the AI engineer."""

    section: str = Field(
        description="Exact section name from the setup .ini file (e.g. 'CAMBER_RF', 'PRESSURE_LF', 'SPRING_RATE_FR'). Must match a section listed in Current Setup Parameters exactly.",
    )
    parameter: str = Field(
        description="Parameter name within the section. In AC setup files this is always 'VALUE'.",
    )
    value_before: float | None = Field(
        default=None,
        description="Previous value in physical units (after domain conversion).",
    )
    value_after: float = Field(
        description="Proposed value in physical units (after domain conversion).",
    )
    reasoning: str
    expected_effect: str
    confidence: Literal["high", "medium", "low"]


class DriverFeedback(BaseModel):
    """A driving technique observation from the engineer."""

    area: str
    observation: str
    suggestion: str
    corners_affected: list[int] = []
    severity: Literal["high", "medium", "low"]


class EngineerResponse(BaseModel):
    """Complete output of the AI engineer for a session."""

    session_id: str
    setup_changes: list[SetupChange] = []
    driver_feedback: list[DriverFeedback] = []
    signals_addressed: list[str] = []
    summary: str
    explanation: str
    confidence: Literal["high", "medium", "low"]
    resolution_tier: int | None = None
    tier_notice: str = ""


# ---------------------------------------------------------------------------
# Agent models (Phase 5.3)
# ---------------------------------------------------------------------------


class SpecialistResult(BaseModel):
    """Intermediate output from each specialist agent before combination."""

    setup_changes: list[SetupChange] = []
    driver_feedback: list[DriverFeedback] = []
    domain_summary: str

    @model_validator(mode="after")
    def at_least_one_output(self) -> SpecialistResult:
        if not self.setup_changes and not self.driver_feedback:
            raise ValueError(
                "Specialist must produce at least setup_changes or driver_feedback"
            )
        return self


class PrincipalNarrative(BaseModel):
    """Structured output from the principal agent synthesis step.

    Two distinct fields produced in a single LLM call:
    - summary: executive headline (2–4 sentences, ≤80 words)
    - explanation: detailed narrative (multi-paragraph, ≤300 words)
    """

    summary: str
    explanation: str


class AgentDeps(BaseModel):
    """Shared context passed to all specialist agents via RunContext."""

    session_summary: SessionSummary
    parameter_ranges: dict[str, ParameterRange] = {}
    domain_signals: list[str] = []
    knowledge_fragments: list[Any] = []
    resolution_tier: int | None = None
