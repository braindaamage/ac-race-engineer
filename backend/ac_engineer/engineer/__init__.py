"""Engineer core: deterministic session summarizer, setup reader/writer."""

from __future__ import annotations

from .models import (
    ChangeOutcome,
    CornerIssue,
    DriverFeedback,
    EngineerResponse,
    LapSummary,
    ParameterRange,
    SessionSummary,
    SetupChange,
    StintSummary,
    ValidationResult,
)
from .setup_reader import get_parameter_range, read_parameter_ranges
from .setup_writer import apply_changes, create_backup, validate_changes
from .summarizer import summarize_session

__all__ = [
    # Functions
    "summarize_session",
    "read_parameter_ranges",
    "get_parameter_range",
    "validate_changes",
    "apply_changes",
    "create_backup",
    # Models
    "SessionSummary",
    "LapSummary",
    "CornerIssue",
    "StintSummary",
    "ParameterRange",
    "ValidationResult",
    "ChangeOutcome",
    "SetupChange",
    "DriverFeedback",
    "EngineerResponse",
]
